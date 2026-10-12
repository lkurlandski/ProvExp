"""
3-A, disagreement triage (PLAN.md, 3-A): when one detector flags a file and the other does not, is the flagging model's
evidence content the other one does not read (a blind spot) or reads the other way (a disagreement on meaning)?

The files come from scripts/cm_disagreement_select.py (25 per cell: malware or benign, flagged only by the GBDT or only
by MalConv, at each model's 1%-FPR threshold). A is the model that flags the file, B the other. Both explain the
malware log-odds per byte (the GBDT: the pullback of interventional TreeSHAP; MalConv: Integrated Gradients), so they
can be compared byte by byte. A's top fraction q_A of the ablatable bytes by evidence for malware (positive evidence
only) is split by how B reads each byte:

    blind   outside B's attended bytes (its top fraction q_B of all bytes by |evidence|, nonzero)
    oppose  attended by B, as evidence against malware
    agree   attended by B, as evidence for malware

Validation by deletion (PB1's operator, level 3, zeros; both models scored): A's top set, each category, and for each
category a random subset of A's top set of the same size. Expected: deleting blind bytes lowers A and leaves B as it
was; deleting oppose bytes also raises B (they carry B's verdict); random subsets of A's top set fall in between.

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per file: cell, A, both log-odds, the category sizes and A's evidence in each (per q_B),
                        and both models' log-odds after each deletion
    report.json         the configuration, thresholds, and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_triage.py --seed 0 --num_workers 16
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

sys.path.insert(0, str(Path(__file__).parent))

import cm_check  # noqa: E402
from cm_check import malconv_explanations  # noqa: E402
from cm_check import malconv_log_odds  # noqa: E402
from faithfulness import load_sample  # noqa: E402


__all__ = [
    "categories",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
EXPLAINER = "treeshap_interventional"
Q_A = 0.01
Q_B = (0.01, 0.05)
Q_B_DELETE = 0.05  # The attended fraction whose categories are deleted.
CATEGORIES = ("blind", "oppose", "agree")

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]


################################################################################
# Categories
################################################################################


def top_mask(scores: FloatArray, allowed: BoolArray, q: float, perm: IntArray) -> BoolArray:
    """The top ⌈q · |allowed|⌉ allowed elements by score (ties by `perm`), keeping only positive scores."""
    k = max(1, int(np.ceil(q * int(allowed.sum()))))
    order = element_order(scores, 1.0, perm)
    order = order[allowed[order]][:k]
    mask = np.zeros(scores.shape[0], dtype=np.bool_)
    mask[order[scores[order] > 0]] = True
    return mask


def categories(e_a: FloatArray, e_b: FloatArray, ablatable: BoolArray, q_a: float, q_b: float, perm: IntArray) -> tuple[BoolArray, dict[str, BoolArray]]:
    """A's top set and its split by how B reads each byte (see the module docstring)."""
    top = top_mask(e_a, ablatable, q_a, perm)
    attended = top_mask(np.abs(e_b), np.ones(e_b.shape[0], dtype=np.bool_), q_b, perm)
    return top, {"blind": top & ~attended, "oppose": top & attended & (e_b < 0), "agree": top & attended & (e_b > 0)}


################################################################################
# Per File
################################################################################


def process_file(task: dict[str, Any]) -> dict[str, Any]:
    """The categories and deletions of one file."""
    t_0 = time.perf_counter()
    base = {"index": task["index"], "name": task["name"], "label": task["label"], "cell": task["cell"], "A": task["A"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = cm_check._STATE["extractor"]
        gbdt, malconv = cm_check._STATE["gbdt"], cm_check._STATE["malconv"]
        x0, prov = extractor.feature_vector_with_provenance(data)
        b = prov.pullback(task["explanation"])
        evidence = {"gbdt": b[:m], "malconv": task["ig"].astype(np.float64)}
        A, B = task["A"], "malconv" if task["A"] == "gbdt" else "gbdt"
        e_a, e_b = evidence[A], evidence[B]
        protection = protect(data, header="typical")
        ablatable = ~protection.mask
        perm = np.random.default_rng([task["seed"], 1]).permutation(m).astype(np.int64)
        rng = np.random.default_rng([task["seed"], 2])
        f0 = {"gbdt": float(gbdt(np.asarray(x0, dtype=np.float64)[None, :])[0]), "malconv": task["malconv_log_odds"]}

        row: dict[str, Any] = {"size": m, "gbdt_log_odds": f0["gbdt"], "malconv_log_odds": f0["malconv"],
                               # The GBDT's attribution on features without provenance (not localizable; App-L).
                               "gbdt_null": float(b[m]) if prov.has_null else 0.0}
        sets: dict[str, BoolArray] = {}
        for q_b in Q_B:
            top, cats = categories(e_a, e_b, ablatable, Q_A, q_b, perm)
            row["top_size"], row["top_evidence"] = int(top.sum()), float(e_a[top].sum())
            for c, mask in cats.items():
                row[f"size:{c}:{q_b}"] = int(mask.sum())
                row[f"evidence_A:{c}:{q_b}"] = float(e_a[mask].sum())
                row[f"evidence_B:{c}:{q_b}"] = float(e_b[mask].sum())
            if q_b == Q_B_DELETE:
                sets["top"] = top
                for c, mask in cats.items():
                    if mask.any():
                        sets[c] = mask
                        idx = np.flatnonzero(top)
                        r = np.zeros(m, dtype=np.bool_)
                        r[rng.choice(idx, size=int(mask.sum()), replace=False)] = True
                        sets[f"random_{c}"] = r

        for name, mask in sets.items():
            z = ablate(data, mask, protection.mask, "zeros", None, protection.header, protection.header_values)
            try:
                x = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
                ok = verify(protection, data, z, float(x[IS_PE])) is None
                g = float(gbdt(x[None, :])[0]) if ok else float("nan")
            except Exception:
                ok, g = False, float("nan")
            row[f"gbdt:{name}"], row[f"malconv:{name}"], row[f"valid:{name}"] = g, malconv_log_odds(malconv, z), ok
        return base | row | {"status": "ok", "error": "", "seconds": time.perf_counter() - t_0}
    except Exception as err:
        return base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300], "seconds": time.perf_counter() - t_0}


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, thresholds: dict[str, float]) -> None:
    """Print, per cell, how A's evidence splits and what deleting each part does to both models."""
    ok = files.filter(pl.col("status") == "ok")
    print(f"\n{ok.height} of {files.height} files ok. A's top {Q_A:.0%} of bytes by evidence for malware, split by how B")
    print("reads them; shares of A's evidence in its top set (mean over files).\n")
    print("| cell | q_B | blind | oppose | agree | B's evidence on oppose (median) |")
    print("|---|---|---|---|---|---|")
    for cell in sorted(ok["cell"].unique()):
        f = ok.filter(pl.col("cell") == cell)
        for q_b in Q_B:
            shares = [float((f[f"evidence_A:{c}:{q_b}"] / f["top_evidence"]).mean()) for c in CATEGORIES]  # type: ignore[arg-type]
            opp = float(f[f"evidence_B:oppose:{q_b}"].median())  # type: ignore[arg-type]
            print(f"| {cell} | {q_b:.0%} | " + " | ".join(f"{s:.2f}" for s in shares) + f" | {opp:.2f} |")
    print(f"\nDeletion (q_B = {Q_B_DELETE:.0%}): median change in A's and B's log-odds (deleted − original), and the files on")
    print("which A stops flagging / B starts flagging, over files where the deletion verified.\n")
    print("| cell | deleted | files | ΔA | ΔB | A stops | B starts |")
    print("|---|---|---|---|---|---|---|")
    for cell in sorted(ok["cell"].unique()):
        f = ok.filter(pl.col("cell") == cell)
        A = f["A"][0]
        B = "malconv" if A == "gbdt" else "gbdt"
        for name in ["top", *[n for c in CATEGORIES for n in (c, f"random_{c}")]]:
            if f"valid:{name}" not in f.columns:
                continue
            g = f.filter(pl.col(f"valid:{name}").fill_null(False))
            if g.height == 0:
                continue
            dA = g[f"{A}:{name}"] - g[f"{A}_log_odds"]
            dB = g[f"{B}:{name}"] - g[f"{B}_log_odds"]
            stops = int((g[f"{A}:{name}"] <= thresholds[A]).sum())
            starts = int((g[f"{B}:{name}"] > thresholds[B]).sum())
            print(f"| {cell} | {name} | {g.height} | {float(dA.median()):.2f} | {float(dB.median()):.2f} | {stops} | {starts} |")  # type: ignore[arg-type]


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT and of MalConv.")
    parser.add_argument("--selection", type=Path, default=None, help="Default: artifacts/explanation_set/ts-disagreement-seed{seed}.parquet")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024-disagreement")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files per cell (0: all), for smoke tests.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_triage")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    selection = args.selection or ROOT / "artifacts" / "explanation_set" / f"ts-disagreement-seed{args.seed}.parquet"
    thresholds: dict[str, float] = json.loads(selection.with_suffix(".json").read_text())["thresholds"]
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    expdir = args.explanations / f"seed-{args.seed}"
    explanations = np.load(expdir / f"{EXPLAINER}.npy")
    samples = pl.read_parquet(expdir / "samples.parquet").with_row_index("index")
    files = pl.read_parquet(selection)
    files = samples.select("index", "name").join(files, on="name", how="inner").sort("index")
    if files.height != samples.height:
        raise RuntimeError(f"{expdir.as_posix()} does not explain {selection.as_posix()}.")
    if args.num_files > 0:
        files = pl.concat([g.head(args.num_files) for _, g in files.group_by("cell", maintain_order=True)])
    gbdt_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    malconv_file = args.checkpoints / f"malconv-seed{args.seed}.pt"
    print(f"3-A triage: {files.height} files from {selection.as_posix()}; thresholds {thresholds}.", flush=True)

    # Phase 1, on the GPU: MalConv's log-odds and Integrated Gradients.
    t_0 = time.time()
    model = load_pretrained_malconv(malconv_file).to(args.device)
    tasks: list[dict[str, Any]] = []
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="MalConv", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        log_odds, ig, _ = malconv_explanations(model, data, args.ig_steps, args.device)
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "cell": r["cell"],
                      "A": "gbdt" if r["cell"].endswith("gbdt_only") else "malconv",
                      "shard": int(r["shard"]), "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]),
                      "explanation": explanations[int(r["index"])].astype(np.float64), "malconv_log_odds": log_odds, "ig": ig})
    seconds_malconv = time.time() - t_0
    del model
    print(f"Phase 1 (MalConv on {args.device}): {seconds_malconv:.0f} s.", flush=True)

    # Phase 2, on the CPU: provenance, categories, deletions.
    t_0 = time.time()
    rows: list[dict[str, Any]] = []
    tasks.sort(key=lambda t: -t["ig"].shape[0])
    with mp.get_context("fork").Pool(args.num_workers, initializer=cm_check._init_worker, initargs=(gbdt_file, malconv_file)) as pool:
        for row in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            rows.append(row)
            if row["status"] != "ok":
                print(f"File {row['index']}: {row['error']}", flush=True)
    seconds_files = time.time() - t_0
    print(f"Phase 2 (files on {args.num_workers} workers): {seconds_files:.0f} s.", flush=True)

    df = pl.DataFrame(rows, infer_schema_length=None).sort("index")
    df.write_parquet(outdir / "files.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "explainer": EXPLAINER, "q_a": Q_A, "q_b": list(Q_B), "q_b_delete": Q_B_DELETE, "thresholds": thresholds,
              "seconds_malconv": seconds_malconv, "seconds_files": seconds_files, "failed": int((df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(df, thresholds)


if __name__ == "__main__":
    main()
