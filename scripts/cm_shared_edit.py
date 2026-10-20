"""
Editing the shared fields (manuscript, Section 6.1; docs/experiments/specs.md, "Part A'"): do loader-safe changes to
the fields that both detectors rely on, found through the GBDT's pullback, weaken both detectors, while the same number
of fields chosen another way weakens only one?

For each of the malware that both detectors detect (run 68's files, scripts/cm_transfer.py):

    Phase 1 (GPU): MalConv's Integrated Gradients per byte, cached in `{outdir}/ig/{index}.npy`.
    Phase 2 (CPU): on the original file, the GBDT's interventional-TreeSHAP pullback, its occlusion over windows (the
        window baseline, no provenance), and MalConv's IG, all as evidence for malware. The candidate fields are the
        loader-safe fields of scripts/audit_evade.py (FREE and FREE_EXTRA, scrambled; CONSTRAINED, a valid benign value),
        located in the file by P. A field's evidence is a detector's evidence summed over the field's bytes (for occlusion,
        each window's score spread evenly over its bytes; only windows that hold a candidate field are occluded). Each arm
        edits the same number of fields per file and differs only in how they are chosen:
            shared_pullback   top n by min(GBDT pullback evidence, MalConv IG evidence)
            shared_windows    top n by min(GBDT occlusion evidence, MalConv IG evidence)
            malconv_only      top n by MalConv IG evidence (an attacker who explains only the raw-byte detector)
            gbdt_only         top n by GBDT pullback evidence
            random            n candidate fields drawn per file
        Every edited file must parse with its original section layout; both detectors score it.

With `--check` (step 0, the feasibility check), phase 2 stops before editing and records, per file, the number of
candidate fields and how much of each detector's evidence they carry.

Outputs, in `{outdir}/seed-{seed}/`:
    check.parquet   (--check) one row per file: candidates, evidence on them, the shared fields' evidence
    files.parquet   one row per (file, arm): the fields edited, bytes written, parse, both detectors' scores and drops
    report.json     the configuration, thresholds, per-arm summary, paired comparisons, and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py --seed 0 --device cuda:3 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
import torch
from tqdm import tqdm

from provexp.ablation import element_order
from provexp.ablation import window_edges
from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import treeshap_interventional
from provexp.explain.problem import malconv_integrated_gradients
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv

sys.path.insert(0, str(Path(__file__).parent))

import faithfulness  # noqa: E402
from audit_evade import CONSTRAINED  # noqa: E402
from audit_evade import FREE  # noqa: E402
from audit_evade import FREE_EXTRA  # noqa: E402
from audit_evade import _scramble_features  # noqa: E402
from audit_evade import benign_pools  # noqa: E402
from audit_evade import realizable_plan  # noqa: E402
from cm_shared import split_sets  # noqa: E402
from cm_transfer import thresholds  # noqa: E402
from faithfulness import Scorer  # noqa: E402
from faithfulness import load_sample  # noqa: E402
from faithfulness import occlude_range  # noqa: E402
import shortcuts_transplant as st  # noqa: E402


__all__ = [
    "ARMS",
    "choose_fields",
    "field_evidence",
    "paired",
    "summarize",
]


ROOT = Path(__file__).parent.parent
ARMS = ("shared_pullback", "shared_windows", "malconv_only", "gbdt_only", "random")
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

_STATE: dict[str, Any] = {}


################################################################################
# Fields
################################################################################


def field_evidence(e: FloatArray, runs: dict[int, list[tuple[int, int]]], fields: list[int]) -> FloatArray:
    """A detector's evidence summed over each field's bytes (its runs in P), shape (len(fields),)."""
    return np.array([sum(float(e[s:s + n].sum()) for s, n in runs.get(j, [])) for j in fields], dtype=np.float64)


def choose_fields(scores: FloatArray, n: int, tiebreak: IntArray) -> list[int]:
    """
    The positions of the top n fields by score, ties broken by a seeded permutation.

    Args:
        scores: A score per candidate field, shape (k,).
        n: The number of fields to choose (all of them if fewer).
        tiebreak: A permutation of the k fields.
    """
    if scores.shape != tiebreak.shape:
        raise ValueError(f"Expected one tie-break rank per field. Got {scores.shape} and {tiebreak.shape}.")
    return [int(i) for i in element_order(scores, 1.0, tiebreak)[:n]]


def candidate_fields(
    x: FloatArray,
    runs: dict[int, list[tuple[int, int]]],
    rng: np.random.Generator,
    max_content: int,
) -> tuple[list[int], dict[int, int]]:
    """
    The loader-safe fields an attacker could change in this file: the fields to scramble, and a valid benign value for
    each constrained field, keeping only fields located in the file by P (at most `max_content` bytes; a constrained
    field must be one run of 1, 2, 4, or 8 bytes, which `_scramble_features` writes).
    """
    index, names, pools = _STATE["index"], _STATE["names"], _STATE["pools"]
    columns = sorted(index[name] for name in FREE | CONSTRAINED)
    free, values = realizable_plan(x, index, columns, names, pools, rng)
    free += sorted(index[name] for name in FREE_EXTRA)

    def size(j: int) -> int:
        return sum(n for _, n in runs.get(j, []))

    free = [j for j in free if 0 < size(j) <= max_content]
    values = {j: v for j, v in values.items() if len(runs.get(j, [])) == 1 and runs[j][0][1] in (1, 2, 4, 8)}
    return free, values


################################################################################
# Workers
################################################################################


def _init_worker(model_file: Path, checkpoint: Path, background: FloatArray, pools: dict[tuple[int, int], Any]) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    torch.set_num_threads(1)
    extractor = PEFeatureExtractor()
    _STATE["extractor"] = extractor
    _STATE["names"] = list(extractor.feature_names)
    _STATE["index"] = {name: i for i, name in enumerate(_STATE["names"])}
    _STATE["booster"] = lgb.Booster(model_file=str(model_file))
    _STATE["gbdt"] = gbdt_function(_STATE["booster"])
    _STATE["malconv"] = load_pretrained_malconv(checkpoint).eval()
    _STATE["background"] = background
    _STATE["pools"] = pools
    faithfulness._STATE["extractor"] = extractor
    faithfulness._STATE["models"] = {"gbdt": _STATE["gbdt"]}


def _scores(data: bytes) -> tuple[float, float]:
    """The GBDT's and MalConv's malware log-odds of a file."""
    x = np.asarray(_STATE["extractor"].feature_vector(data), dtype=np.float64)
    with torch.no_grad():
        z = _STATE["malconv"](encode(data)[None])
    return float(_STATE["gbdt"](x[None])[0]), float(z[0, 1] - z[0, 0])


def process_file(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Phase 2 for one file: the evidence per candidate field and, unless checking, the edits of every arm."""
    base = {"index": task["index"], "name": task["name"]}
    t_0 = time.perf_counter()
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        original = parse(data)
        if original.status != "ok":
            return [base | {"status": "not_pe"}]
        x0, prov = _STATE["extractor"].feature_vector_with_provenance(data)
        x0 = np.asarray(x0, dtype=np.float64)
        f_g, f_m = _scores(data)
        d_g, d_m = float(np.sign(f_g)) or 1.0, float(np.sign(f_m)) or 1.0

        # Each detector's evidence for its verdict per byte: the GBDT's pullback, its occlusion density, MalConv's IG.
        a = treeshap_interventional(_STATE["booster"], x0[None], _STATE["background"])[0]
        e_g = d_g * prov.pullback(a)[:m]
        e_m = d_m * np.load(task["ig"]).astype(np.float64)[:m]

        names, index = _STATE["names"], _STATE["index"]
        pool = np.array(sorted(index[name] for name in FREE | CONSTRAINED | FREE_EXTRA), dtype=np.int64)
        runs = st.feature_runs(prov, pool)
        values_rng = np.random.default_rng([task["seed"], task["index"], 1])
        free, values = candidate_fields(x0, runs, values_rng, task["max_content"])
        fields = free + sorted(values)
        covered = np.zeros(m, dtype=np.bool_)
        for j in fields:
            for s, k in runs.get(j, []):
                covered[s:s + k] = True

        # The window baseline: the GBDT's occlusion score of each window, spread evenly over the window's bytes.
        # NOTE: only the windows that hold a candidate field are occluded; the others cannot affect any field's score.
        protection = protect(data, header="typical")
        e_w = np.zeros(m)
        windows_occluded = 0
        if not task["check"]:
            scorer = Scorer(data, protection, "zeros", task["index"])
            edges = window_edges(m, task["num_windows"])
            window = np.repeat(np.arange(edges.shape[0] - 1), np.diff(edges))
            f0, _ = scorer.scores(np.zeros(m, dtype=np.bool_))
            for k in np.unique(window[covered]).tolist():
                occlusion, _ = occlude_range(scorer, window, f0, k, k + 1)
                e_w[edges[k]:edges[k + 1]] = d_g * occlusion["gbdt"][0] / max(1, int(edges[k + 1] - edges[k]))
                windows_occluded += 1
        G, W, M = (field_evidence(e, runs, fields) for e in (e_g, e_w, e_m))
        tiebreak = np.random.default_rng([task["seed"], task["index"], 2]).permutation(len(fields)).astype(np.int64)
        n = task["num_fields"]
        chosen = {
            "shared_pullback": choose_fields(np.minimum(G, M), n, tiebreak),
            "shared_windows": choose_fields(np.minimum(W, M), n, tiebreak),
            "malconv_only": choose_fields(M, n, tiebreak),
            "gbdt_only": choose_fields(G, n, tiebreak),
            "random": [int(i) for i in np.random.default_rng([task["seed"], task["index"], 3]).permutation(len(fields))[:n]],
        }

        info = base | {"status": "ok", "size": m, "gbdt_f0": f_g, "malconv_f0": f_m, "candidates": len(fields),
                       "candidates_constrained": len(values), "windows_occluded": windows_occluded}
        if task["check"]:
            ablatable = ~protection.mask
            perm = np.random.default_rng([task["seed"], task["index"], 4]).permutation(m).astype(np.int64)
            T_g, T_m, S = split_sets(e_g, e_m, ablatable, 0.01, perm)
            top = chosen["shared_pullback"]
            return [info | {
                "candidate_bytes": int(covered.sum()),
                "gbdt_evidence_total": float(e_g.sum()), "malconv_evidence_total": float(e_m.sum()),
                "gbdt_on_candidates": float(e_g[covered].sum()), "malconv_on_candidates": float(e_m[covered].sum()),
                "shared_bytes": int(S.sum()), "shared_on_candidates": int((S & covered).sum()),
                "gbdt_shared_fields": float(G[top].sum()), "malconv_shared_fields": float(M[top].sum()),
                "min_shared_fields": float(np.minimum(G, M)[top].sum()),
                "shared_fields": ",".join(names[fields[i]] for i in top),
                "seconds": time.perf_counter() - t_0,
            }]

        rows = []
        for k, arm in enumerate(ARMS):
            picked = [fields[i] for i in chosen[arm]]
            rng = np.random.default_rng([task["seed"], task["index"], 10 + k])
            modified, written, changed = _scramble_features(data, runs, [j for j in picked if j not in values],
                                                            task["max_content"], rng,
                                                            {j: values[j] for j in picked if j in values})
            result = parse(modified)
            ok = result.status == "ok" and result.layout == original.layout
            g, mc = _scores(modified) if ok else (float("nan"), float("nan"))
            rows.append(info | {
                "arm": arm, "fields": ",".join(names[j] for j in picked), "num_fields": changed, "bytes": written,
                "parsed": ok, "gbdt_edited": g, "malconv_edited": mc,
                "gbdt_drop": d_g * (f_g - g), "malconv_drop": d_m * (f_m - mc),
                "gbdt_evidence": float(G[chosen[arm]].sum()), "malconv_evidence": float(M[chosen[arm]].sum()),
                "gbdt_window_evidence": float(W[chosen[arm]].sum()),
                "seconds": time.perf_counter() - t_0,
            })
        return rows
    except Exception as err:
        return [base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]}]


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, gbdt_threshold: float, malconv_threshold: float, delta: float) -> pl.DataFrame:
    """
    Per arm, over the files where the edit parsed: the median drop of each detector, the share of files where both
    drop by more than `delta`, MalConv's evasion rate, and the share the GBDT now scores below its threshold.
    """
    ok = files.filter((pl.col("status") == "ok") & pl.col("parsed"))
    return (
        ok.group_by("arm").agg(
            pl.len().alias("files"),
            pl.col("num_fields").mean().alias("fields"),
            pl.col("malconv_drop").median().alias("malconv_drop"),
            pl.col("gbdt_drop").median().alias("gbdt_drop"),
            ((pl.col("malconv_drop") > delta) & (pl.col("gbdt_drop") > delta)).mean().alias("both_drop"),
            (pl.col("malconv_edited") <= malconv_threshold).mean().alias("malconv_evaded"),
            (pl.col("gbdt_edited") <= gbdt_threshold).mean().alias("gbdt_crossed"),
        )
        .with_columns(pl.col("arm").replace_strict({a: i for i, a in enumerate(ARMS)}, default=len(ARMS)).alias("order"))
        .sort("order").drop("order")
    )


def paired(files: pl.DataFrame, delta: float, reference: str = "shared_pullback") -> pl.DataFrame:
    """
    The reference arm against every other arm, per file: wins and the Wilcoxon p on the smaller of the two detectors'
    drops, and the exact (McNemar) p on "both drop by more than delta".
    """
    ok = files.filter((pl.col("status") == "ok") & pl.col("parsed")).with_columns(
        pl.min_horizontal("malconv_drop", "gbdt_drop").alias("weaker"),
        ((pl.col("malconv_drop") > delta) & (pl.col("gbdt_drop") > delta)).alias("both"),
    )
    wide = ok.pivot(on="arm", index="index", values=["weaker", "both"]).drop_nulls()
    rows = []
    for arm in ARMS:
        if arm == reference or f"weaker_{arm}" not in wide.columns:
            continue
        d = wide[f"weaker_{reference}"].to_numpy() - wide[f"weaker_{arm}"].to_numpy()
        b_ref, b_arm = wide[f"both_{reference}"].to_numpy(), wide[f"both_{arm}"].to_numpy()
        only_ref, only_arm = int((b_ref & ~b_arm).sum()), int((~b_ref & b_arm).sum())
        rows.append({
            "against": arm, "files": wide.height, "wins": int((d > 0).sum()),
            "p_weaker": float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0,
            "both_only_reference": only_ref, "both_only_other": only_arm,
            "p_both": float(stats.binomtest(only_ref, only_ref + only_arm).pvalue) if only_ref + only_arm else 1.0,
        })
    return pl.DataFrame(rows)


################################################################################
# Main
################################################################################


def run_ig(files: pl.DataFrame, checkpoint: Path, db: Path, steps: int, device: str, igdir: Path) -> None:
    """MalConv's IG per byte for each file, saved to `igdir`; files already done are skipped."""
    igdir.mkdir(parents=True, exist_ok=True)
    model = load_pretrained_malconv(checkpoint).to(device).eval()
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="MalConv IG", mininterval=10):
        path = igdir / f"{r['index']}.npy"
        if path.exists():
            continue
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], db)
        ig = malconv_integrated_gradients(model, encode(data).to(device), steps=steps, batch_size=16)
        np.save(path, ig.float().cpu().numpy())
    del model


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv and of the GBDT.")
    parser.add_argument("--selection", type=Path, default=None, help="Both-detect malware (default: run 68's, artifacts/explanation_set/ts-both-detect-seed{seed}.parquet).")
    parser.add_argument("--num_files", type=int, default=100, help="The first files of the selection by row, as run 68 (0: all).")
    parser.add_argument("--num_fields", type=int, default=3, help="The fields every arm edits per file.")
    parser.add_argument("--num_windows", type=int, default=4096, help="Windows for the GBDT's occlusion (the window baseline).")
    parser.add_argument("--max_content", type=int, default=256, help="The largest field, in bytes, that counts as a candidate.")
    parser.add_argument("--delta", type=float, default=1.0, help="The drop in log-odds that counts, for 'both drop'.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--background_size", type=int, default=1000)
    parser.add_argument("--benign_rows", type=int, default=20000, help="Benign training files for the constrained fields' values.")
    parser.add_argument("--check", action="store_true", help="Step 0: candidates and evidence only, no edits.")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--predictions", type=Path, default=ROOT / "artifacts" / "checkpoints-predictions")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--transfer", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_transfer", help="Run 68's output, for the context row.")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_shared_edit")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--tables_only", action="store_true")
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    gbdt_threshold, malconv_threshold = thresholds(args.models, args.features, args.predictions, args.seed, args.fpr)

    if not args.tables_only:
        selection = args.selection or ROOT / "artifacts" / "explanation_set" / f"ts-both-detect-seed{args.seed}.parquet"
        files = pl.read_parquet(selection)
        if args.num_files > 0:
            files = files.sort("row").head(args.num_files)
        files = files.select(pl.col("row").alias("index"), "name", "shard", "position").sort("index")
        print(f"Shared-field edits: {files.height} both-detected malware, seed {args.seed}, {args.num_fields} fields per "
              f"file, GBDT occlusion over {args.num_windows} windows{' (check only)' if args.check else ''}.", flush=True)
        print(f"Thresholds (1% FPR): GBDT {gbdt_threshold:.3f}, MalConv {malconv_threshold:.3f}.", flush=True)

        t_0 = time.time()
        checkpoint = args.checkpoints / f"malconv-seed{args.seed}.pt"
        run_ig(files, checkpoint, args.db, args.ig_steps, args.device, outdir / "ig")
        seconds_ig = time.time() - t_0
        print(f"Phase 1 (IG on {args.device}): {seconds_ig:.0f} s.", flush=True)

        names = list(PEFeatureExtractor().feature_names)
        index = {name: i for i, name in enumerate(names)}
        pools = benign_pools(args.features, names, sorted(index[n] for n in CONSTRAINED), args.benign_rows, args.seed)
        background = np.asarray(load_features(args.features, "tr")[0][pl.read_parquet(ROOT / "artifacts" / "explanations" / "ember2024" / "background.parquet")["row"].to_numpy()[:args.background_size]], dtype=np.float64)
        tasks = [{"index": int(r["index"]), "name": r["name"], "shard": int(r["shard"]), "position": int(r["position"]),
                  "dbdir": args.db, "ig": outdir / "ig" / f"{r['index']}.npy", "num_windows": args.num_windows,
                  "num_fields": args.num_fields, "max_content": args.max_content, "seed": args.seed,
                  "check": args.check} for r in files.iter_rows(named=True)]
        t_0 = time.time()
        rows: list[dict[str, Any]] = []
        model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
        # Spawn, not fork: phase 1 initialized a CUDA context in this process, which a forked worker cannot use.
        with mp.get_context("spawn").Pool(args.num_workers, initializer=_init_worker,
                                          initargs=(model_file, checkpoint, background, pools)) as pool:
            for out in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
                rows += out
                if out[0]["status"] != "ok":
                    print(f"File {out[0]['index']}: {out[0]['status']} {out[0].get('error', '')}", flush=True)
        seconds_files = time.time() - t_0
        print(f"Phase 2 (files on {args.num_workers} workers): {seconds_files:.0f} s.", flush=True)
        table = pl.DataFrame(rows, infer_schema_length=None).sort("index")
        table.write_parquet(outdir / ("check.parquet" if args.check else "files.parquet"))
        if args.check:
            check_summary(table, args.num_fields)
            return
    else:
        seconds_ig = seconds_files = float("nan")

    table = pl.read_parquet(outdir / "files.parquet")
    summary = summarize(table, gbdt_threshold, malconv_threshold, args.delta)
    comparisons = paired(table, args.delta)
    context = context_row(args.transfer / f"seed-{args.seed}" / "files.parquet", table, gbdt_threshold, args.delta)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=200):
        print(f"\nPer arm (median drops in log-odds; both = both drop by more than {args.delta}):\n{summary}")
        print(f"\nRun 68's attack on the same files (context):\n{context}")
        print(f"\nShared (pullback) against each arm, paired per file:\n{comparisons}")
    report = {"config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
              "gbdt_threshold": gbdt_threshold, "malconv_threshold": malconv_threshold,
              "status": table.group_by("status").len().to_dicts(),
              "unparsed": int((table.filter(pl.col("status") == "ok")["parsed"] == False).sum()),  # noqa: E712
              "summary": summary.to_dicts(), "context": context.to_dicts(), "paired": comparisons.to_dicts(),
              "seconds_ig": seconds_ig, "seconds_files": seconds_files}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"Wrote {outdir.as_posix()}.", flush=True)


def context_row(transfer: Path, table: pl.DataFrame, gbdt_threshold: float, delta: float) -> pl.DataFrame:
    """Run 68's attack on the files of this run: the same columns as `summarize` (MalConv-evaded by its own record)."""
    if not transfer.exists():
        return pl.DataFrame()
    t = pl.read_parquet(transfer).filter(pl.col("status") == "ok").join(table.select("index").unique(), on="index")
    t = t.with_columns((pl.col("malconv_f0") - pl.col("malconv_perturbed")).alias("malconv_drop"))
    return t.select(
        pl.len().alias("files"),
        pl.col("malconv_drop").median(),
        pl.col("gbdt_drop").median(),
        ((pl.col("malconv_drop") > delta) & (pl.col("gbdt_drop") > delta)).mean().alias("both_drop"),
        pl.col("malconv_evaded").mean(),
        (pl.col("gbdt_perturbed") <= gbdt_threshold).mean().alias("gbdt_crossed"),
    )


def check_summary(check: pl.DataFrame, num_fields: int) -> None:
    """Step 0: candidates per file and the evidence they carry (shares of each detector's total evidence)."""
    ok = check.filter(pl.col("status") == "ok").with_columns(
        (pl.col("gbdt_on_candidates") / pl.col("gbdt_evidence_total")).alias("gbdt_share_candidates"),
        (pl.col("malconv_on_candidates") / pl.col("malconv_evidence_total")).alias("malconv_share_candidates"),
        (pl.col("shared_on_candidates") / pl.col("shared_bytes")).alias("shared_bytes_on_candidates"),
    )
    cols = ["candidates", "candidates_constrained", "candidate_bytes", "gbdt_share_candidates", "malconv_share_candidates",
            "shared_bytes", "shared_bytes_on_candidates", "gbdt_shared_fields", "malconv_shared_fields", "min_shared_fields"]
    q = ok.select([pl.col(c).quantile(p).alias(f"{c}@{p}") for c in cols for p in (0.1, 0.5, 0.9)])
    print(f"\nStep 0 over {ok.height} files ({check.height - ok.height} not ok):")
    for c in cols:
        print(f"  {c:30s} " + "  ".join(f"q{int(p * 100):02d} {q[f'{c}@{p}'][0]:9.3f}" for p in (0.1, 0.5, 0.9)))
    enough = float(np.mean(ok["candidates"].to_numpy() >= num_fields))
    both = float(np.mean((ok["gbdt_shared_fields"].to_numpy() > 0.5) & (ok["malconv_shared_fields"].to_numpy() > 0.5)))
    print(f"  files with >= {num_fields} candidates: {enough:.2f}")
    print(f"  files whose shared fields carry > 0.5 log-odds of each detector: {both:.2f}")
    common = ok.select(pl.col("shared_fields").str.split(",")).explode("shared_fields")["shared_fields"].value_counts(sort=True)
    print(f"  most common shared fields:\n{common.head(12)}")


if __name__ == "__main__":
    main()
