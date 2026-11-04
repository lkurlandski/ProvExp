"""
3-A, the shared attack surface (PLAN.md, 3-A): the bytes both detectors rely on, what deleting them does to each, and
where they lie.

For each of PB1's pilot files (run 21), each model's top fraction q of the ablatable bytes by evidence for its own
predicted class (the GBDT: the pullback of interventional TreeSHAP; MalConv: Integrated Gradients) gives T_g and T_m;
the shared set is S = T_g ∩ T_m, the exclusive sets T_g \\ S and T_m \\ S. Deletion with PB1's operator (level 3,
zeros), both models scored:

    shared        S
    gbdt_only     |S| bytes drawn at random from T_g \\ S (the GBDT's evidence that MalConv does not share)
    malconv_only  |S| bytes drawn at random from T_m \\ S
    random        |S| ablatable bytes drawn at random
    gbdt_top      T_g, and malconv_top, T_m (for scale)

If S is the shared attack surface, deleting it should remove evidence from both models, while each exclusive set of
the same size removes mostly its own model's. Description: the offsets of S (absolute, binned), its runs of contiguous
bytes, and the GBDT features whose credit S carries (a_j times the share of feature j's provenance in S, P^T 1_S).

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per (file, q): set sizes, runs, offsets, and both models' log-odds per deletion
    features.parquet    one row per (file, q, feature) with nonzero credit in S: the credit in S and in T_g
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_shared.py --seed 0 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl
import torch
from tqdm import tqdm

from provexp.ablation import ablate
from provexp.ablation import element_order
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import load_pretrained_malconv
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))

import cm_check  # noqa: E402
from cm_check import malconv_explanations  # noqa: E402
from cm_check import malconv_log_odds  # noqa: E402
from faithfulness import load_sample  # noqa: E402


__all__ = [
    "runs",
    "split_sets",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
EXPLAINER = "treeshap_interventional"
FRACTIONS = (0.01, 0.05)
# Offset bins (bytes from the start of the file) for describing where the sets lie.
OFFSET_BINS = (0, 1024, 4096, 65536)

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]


################################################################################
# Sets
################################################################################


def split_sets(e_g: FloatArray, e_m: FloatArray, ablatable: BoolArray, q: float, perm: IntArray) -> tuple[BoolArray, BoolArray, BoolArray]:
    """Each model's top q of the ablatable bytes by evidence (ties by `perm`): the masks of T_g, T_m, and S = T_g ∩ T_m."""
    m = e_g.shape[0]
    k = max(1, int(np.ceil(q * int(ablatable.sum()))))
    masks = []
    for e in (e_g, e_m):
        order = element_order(e, 1.0, perm)
        order = order[ablatable[order]][:k]
        mask = np.zeros(m, dtype=np.bool_)
        mask[order] = True
        masks.append(mask)
    return masks[0], masks[1], masks[0] & masks[1]


def runs(mask: BoolArray) -> int:
    """The number of maximal runs of contiguous selected elements."""
    x = mask.astype(np.int8)
    return int(x[0]) + int((np.diff(x) == 1).sum()) if x.shape[0] else 0


def sample(mask: BoolArray, n: int, rng: np.random.Generator) -> BoolArray:
    """A random subset of n of the selected elements (all of them if fewer)."""
    idx = np.flatnonzero(mask)
    out = np.zeros(mask.shape[0], dtype=np.bool_)
    out[rng.choice(idx, size=min(n, idx.shape[0]), replace=False)] = True
    return out


################################################################################
# Per File
################################################################################


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The sets, deletions, and description of one file, at every fraction."""
    t_0 = time.perf_counter()
    base = {"index": task["index"], "name": task["name"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = cm_check._STATE["extractor"]
        gbdt, malconv = cm_check._STATE["gbdt"], cm_check._STATE["malconv"]
        _, prov = extractor.feature_vector_with_provenance(data)
        a = task["explanation"]
        f0 = {"gbdt": task["gbdt_log_odds"], "malconv": task["malconv_log_odds"]}
        d = {name: float(np.sign(v)) or 1.0 for name, v in f0.items()}
        e_g = d["gbdt"] * prov.pullback(a)[:m]
        e_m = d["malconv"] * task["ig"].astype(np.float64)
        protection = protect(data, header="typical")
        ablatable = ~protection.mask
        perm = np.random.default_rng([task["seed"], 1]).permutation(m).astype(np.int64)
        rng = np.random.default_rng([task["seed"], 2])

        def score(mask: BoolArray) -> tuple[float, float, bool]:
            z = ablate(data, mask, protection.mask, "zeros", None, protection.header, protection.header_values)
            try:
                x = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
                ok = verify(protection, data, z, float(x[IS_PE])) is None
                g = float(gbdt(x[None, :])[0]) if ok else float("nan")
            except Exception:
                ok, g = False, float("nan")
            return g, malconv_log_odds(malconv, z), ok

        rows: list[dict[str, Any]] = []
        features: list[dict[str, Any]] = []
        for q in FRACTIONS:
            T_g, T_m, S = split_sets(e_g, e_m, ablatable, q, perm)
            n = int(S.sum())
            row: dict[str, Any] = {"q": q, "size": m, "top": int(T_g.sum()), "shared": n, "runs_shared": runs(S),
                                   "gbdt_log_odds": f0["gbdt"], "malconv_log_odds": f0["malconv"]}
            # Where each set lies: each model's evidence in the set, by absolute offset (bytes would let the bulk of
            # large files dominate, while the evidence concentrates in few bytes).
            edges = np.searchsorted(np.arange(m), [*OFFSET_BINS, m])
            for name, mask in (("shared", S), ("gbdt_top", T_g), ("malconv_top", T_m)):
                for model, e in (("gbdt", e_g), ("malconv", e_m)):
                    for lo, hi, start in zip(edges[:-1], edges[1:], OFFSET_BINS):
                        row[f"offset_{start}:{model}:{name}"] = float(e[lo:hi][mask[lo:hi]].sum())
            # Each model's evidence that the sets hold (in log-odds; the pullback sums to the GBDT's explained log-odds).
            for name, mask in (("shared", S), ("gbdt_top", T_g), ("malconv_top", T_m)):
                row[f"evidence_gbdt:{name}"] = float(e_g[mask].sum())
                row[f"evidence_malconv:{name}"] = float(e_m[mask].sum())
            deletions = {"gbdt_top": T_g, "malconv_top": T_m}
            if n > 0:
                deletions |= {"shared": S, "gbdt_only": sample(T_g & ~S, n, rng), "malconv_only": sample(T_m & ~S, n, rng),
                              "random": sample(ablatable, n, rng)}
            for name, mask in deletions.items():
                g, mc, ok = score(mask)
                row[f"gbdt:{name}"], row[f"malconv:{name}"], row[f"valid:{name}"] = g, mc, ok
            rows.append(base | row)
            # The GBDT features whose credit the shared set carries, and the top set for comparison.
            if n > 0:
                in_s = prov.rmatvec(np.append(S, False).astype(np.float64) if prov.has_null else S.astype(np.float64))
                in_t = prov.rmatvec(np.append(T_g, False).astype(np.float64) if prov.has_null else T_g.astype(np.float64))
                credit_s, credit_t = d["gbdt"] * a * in_s, d["gbdt"] * a * in_t
                for j in np.flatnonzero(credit_s != 0):
                    features.append(base | {"q": q, "feature": int(j), "credit_shared": float(credit_s[j]), "credit_top": float(credit_t[j])})
        rows = [r | {"status": "ok", "error": "", "seconds": time.perf_counter() - t_0} for r in rows]
        return rows, features
    except Exception as err:
        return [base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]}], []


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, features: pl.DataFrame, names: list[str]) -> None:
    """Print the deletions (median evidence removed), where the sets lie, and the features S carries."""
    ok = files.filter(pl.col("status") == "ok")
    for q in FRACTIONS:
        f = ok.filter(pl.col("q") == q)
        print(f"\n## q = {q:.0%}: |S| / |T| median {float((f['shared'] / f['top']).median()):.3f} (chance {q:.3f}); "  # type: ignore[arg-type]
              f"files with S empty: {int((f['shared'] == 0).sum())} of {f.height}; runs per shared byte, median "
              f"{float((f['runs_shared'] / f['shared']).filter(f['shared'] > 0).median()):.2f}")  # type: ignore[arg-type]
        print("\nDeletion (median evidence removed over files where every deletion verified; shared, exclusive, and random")
        print("sets have the same size |S|):\n")
        print("| deleted | GBDT | MalConv | files |")
        print("|---|---|---|---|")
        names_del = ["shared", "gbdt_only", "malconv_only", "random", "gbdt_top", "malconv_top"]
        valid = f.filter(pl.all_horizontal([pl.col(f"valid:{k}").fill_null(False) for k in names_del]))
        for k in names_del:
            g = float((valid["gbdt_log_odds"].sign() * (valid["gbdt_log_odds"] - valid[f"gbdt:{k}"])).median())  # type: ignore[arg-type]
            mc = float((valid["malconv_log_odds"].sign() * (valid["malconv_log_odds"] - valid[f"malconv:{k}"])).median())  # type: ignore[arg-type]
            print(f"| {k} | {g:.2f} | {mc:.2f} | {valid.height} |")
        print("\nWhere each set's evidence lies, by offset from the start (each model's evidence in the set, as a share of")
        print("its total in the set, averaged over files):\n")
        bins = [f"[{lo}, {hi})" for lo, hi in zip(map(str, OFFSET_BINS), [*map(str, OFFSET_BINS[1:]), "end"])]
        print("| set | model | " + " | ".join(bins) + " |")
        print("|---|---|" + "---|" * len(bins))
        for name in ("shared", "gbdt_top", "malconv_top"):
            for model in ("gbdt", "malconv"):
                cols = [f"offset_{lo}:{model}:{name}" for lo in OFFSET_BINS]
                share = f.filter(f["shared"] > 0).select(cols).to_numpy()
                total = share.sum(axis=1, keepdims=True)
                share = np.divide(share, total, out=np.full_like(share, np.nan), where=total > 0)
                print(f"| {name} | {model} | " + " | ".join(f"{v:.2f}" for v in np.nanmean(share, axis=0)) + " |")
        print("\nThe shared set's evidence as a share of each model's top set's evidence (median over files):")
        for model in ("gbdt", "malconv"):
            share = (f[f"evidence_{model}:shared"] / f[f"evidence_{model}:{model}_top"]).filter(f["shared"] > 0)
            print(f"  {model}: {float(share.median()):.3f}")  # type: ignore[arg-type]
        feats = features.filter(pl.col("q") == q).group_by("feature").agg(
            pl.len().alias("files"), pl.col("credit_shared").sum(), pl.col("credit_top").sum())
        total = float(feats["credit_shared"].abs().sum())
        feats = feats.with_columns((pl.col("credit_shared") / total).alias("share"),
                                   pl.col("feature").map_elements(lambda j: names[j], return_dtype=pl.String).alias("name"))
        with pl.Config(tbl_rows=25, fmt_str_lengths=60, float_precision=3):
            print("\nGBDT features whose credit S carries (top 20 by total credit in S, as a share of |credit in S|):")
            print(feats.sort("credit_shared", descending=True).head(20).select("name", "files", "credit_shared", "share", "credit_top"))


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT and of MalConv.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files to reuse.")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files per label (0: all), for smoke tests.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_shared")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    files = pl.read_parquet(args.pb1_run / "files.parquet").filter(pl.col("status") == "ok")
    if args.num_files > 0:
        files = pl.concat([files.filter(pl.col("label") == lab).sort("index").head(args.num_files) for lab in (0, 1)])
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    files = files.select("index", "name", "label", "log_odds:gbdt").join(location, on="name", how="left").sort("index")
    explanations = np.load(args.explanations / f"seed-{args.seed}" / f"{EXPLAINER}.npy", mmap_mode="r")
    gbdt_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    malconv_file = args.checkpoints / f"malconv-seed{args.seed}.pt"
    print(f"3-A shared bytes: {files.height} files, fractions {list(FRACTIONS)}.", flush=True)

    # Phase 1, on the GPU: MalConv's log-odds and Integrated Gradients.
    t_0 = time.time()
    model = load_pretrained_malconv(malconv_file).to(args.device)
    tasks: list[dict[str, Any]] = []
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="MalConv", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        log_odds, ig, _ = malconv_explanations(model, data, args.ig_steps, args.device)
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
                      "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]),
                      "explanation": np.asarray(explanations[int(r["index"])], dtype=np.float64),
                      "gbdt_log_odds": float(r["log_odds:gbdt"]), "malconv_log_odds": log_odds, "ig": ig})
    seconds_malconv = time.time() - t_0
    del model
    print(f"Phase 1 (MalConv on {args.device}): {seconds_malconv:.0f} s.", flush=True)

    # Phase 2, on the CPU: provenance, sets, deletions.
    t_0 = time.time()
    rows: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    tasks.sort(key=lambda t: -t["ig"].shape[0])
    with mp.get_context("fork").Pool(args.num_workers, initializer=cm_check._init_worker, initargs=(gbdt_file, malconv_file)) as pool:
        for r_, f_ in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            rows += r_
            features += f_
            if r_ and r_[0]["status"] != "ok":
                print(f"File {r_[0]['index']}: {r_[0]['error']}", flush=True)
    seconds_files = time.time() - t_0
    print(f"Phase 2 (files on {args.num_workers} workers): {seconds_files:.0f} s.", flush=True)

    files_df = pl.DataFrame(rows, infer_schema_length=None).sort("index", "q")
    features_df = pl.DataFrame(features)
    files_df.write_parquet(outdir / "files.parquet")
    features_df.write_parquet(outdir / "features.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "explainer": EXPLAINER, "fractions": list(FRACTIONS), "seconds_malconv": seconds_malconv,
              "seconds_files": seconds_files, "failed": int((files_df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(files_df, features_df, PEFeatureExtractor().feature_names)


if __name__ == "__main__":
    main()
