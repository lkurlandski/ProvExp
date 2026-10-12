"""
3-A first check (PLAN.md, "Paper structure", 3-A): do the GBDT on EMBER v3 and MalConv rely on the same bytes, and
does the answer depend on comparing them at byte level, which only the pullback makes affordable for the GBDT?

The files, operator, and GBDT occlusion scores are PB1's (run 21: 100 pilot files, level 3, zeros fill). For each file:

Agreement. The GBDT's byte explanation is the pullback of interventional TreeSHAP; its P-free alternative is PB1's
occlusion at 64, 256, 1,024, and 4,096 windows. MalConv's is Integrated Gradients (per byte) and its exact occlusion
of its own 512-byte convolution windows. Each pair is compared at each window count (scores summed per window) and at
byte level by Spearman's rho and by the overlap of their top 5% of windows (top 1% of bytes) of evidence for malware,
whose chance level is the fraction itself. Every score attributes the malware log-odds, so they are compared signed.

Cross-deletion. Each ranking (evidence for its own model's predicted class, PB1's convention) deletes its top bytes
at PB1's budgets with PB1's operator, and both models score every deleted file: does one model's evidence remove the
other's? Random window orders are the control.

Outputs, in `{outdir}/seed-{seed}/`:
    agreement.parquet   one row per (file, pair, resolution): rho, top overlap, its chance level
    curves.parquet      one row per (file, ranking, budget): both models' log-odds, and whether the file verified
    files.parquet       one row per file: size, both models' log-odds, status, timing
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_check.py --seed 0 --num_workers 16
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
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
import torch
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import ablate
from provexp.ablation import budget_masks
from provexp.ablation import element_order
from provexp.ablation import window_edges
from provexp.ablation import window_order
from provexp.explain.feature import gbdt_function
from provexp.explain.problem import malconv_integrated_gradients
from provexp.explain.problem import malconv_occlusion
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import MalConv
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from faithfulness import load_window_scores  # noqa: E402


__all__ = [
    "agreement",
    "malconv_explanations",
    "top_overlap",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
EXPLAINER = "treeshap_interventional"
RESOLUTIONS = (64, 256, 1024, 4096)
TOP_WINDOWS = 0.05
TOP_BYTES = 0.01
NUM_RANDOM = 3

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

_STATE: dict[str, Any] = {}


################################################################################
# Agreement
################################################################################


def top_overlap(a: FloatArray, b: FloatArray, q: float, perm: IntArray) -> float:
    """The fraction of `a`'s top ⌈q·n⌉ elements (largest first, ties by `perm`) that are also among `b`'s."""
    k = max(1, int(np.ceil(q * a.shape[0])))
    ta = element_order(a, 1.0, perm)[:k]
    tb = element_order(b, 1.0, perm)[:k]
    return float(np.intersect1d(ta, tb).shape[0] / k)


def agreement(scores: dict[str, FloatArray], pairs: list[tuple[str, str]], resolution: str, q: float, perm: IntArray) -> list[dict[str, Any]]:
    """Spearman's rho and the top-q overlap of each pair of score vectors at one resolution."""
    rows = []
    for a, b in pairs:
        if a not in scores or b not in scores:
            continue
        x, y = scores[a], scores[b]
        rho = float(stats.spearmanr(x, y).statistic) if np.ptp(x) > 0 and np.ptp(y) > 0 else float("nan")
        rows.append({"pair": f"{a}~{b}", "resolution": resolution, "rho": rho, "top": top_overlap(x, y, q, perm),
                     "chance": max(1, int(np.ceil(q * x.shape[0]))) / x.shape[0]})
    return rows


################################################################################
# Per File
################################################################################


def _init_worker(gbdt_file: Path, malconv_file: Path) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    torch.set_num_threads(1)
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["gbdt"] = gbdt_function(lgb.Booster(model_file=str(gbdt_file)))
    _STATE["malconv"] = load_pretrained_malconv(malconv_file)


def malconv_explanations(model: MalConv, data: bytes, steps: int, device: str) -> tuple[float, npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """MalConv's log-odds, Integrated Gradients (per byte), and occlusion of its windows (per byte) for one file."""
    x = encode(data).to(device)
    with torch.no_grad():
        z = model(x[None])
    ig = malconv_integrated_gradients(model, x, steps=steps, batch_size=16)
    occ = malconv_occlusion(model, x)
    return float(z[0, 1] - z[0, 0]), ig.float().cpu().numpy(), occ.float().cpu().numpy()


def malconv_log_odds(model: MalConv, data: bytes) -> float:
    with torch.no_grad():
        z = model(encode(data)[None])
    return float(z[0, 1] - z[0, 0])


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Agreement and cross-deletion for one file."""
    t_0 = time.perf_counter()
    base = {"index": task["index"], "name": task["name"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = _STATE["extractor"]
        _, prov = extractor.feature_vector_with_provenance(data)
        pullback = prov.pullback(task["explanation"])[:m]
        ig = task["ig"].astype(np.float64)
        windows = task["windows"]
        ties = np.random.default_rng([task["seed"], 1])
        byte_perm = ties.permutation(m).astype(np.int64)

        # MalConv's occlusion, per 512-byte window, spread over the window's bytes (exact; see malconv_occlusion).
        mc_occ = task["mc_occlusion"].astype(np.float64)

        # Agreement at each window count and at byte level.
        pairs = [("gbdt_pullback", "malconv_ig"), ("gbdt_occlusion", "malconv_ig"), ("gbdt_pullback", "malconv_occlusion"),
                 ("gbdt_occlusion", "malconv_occlusion"), ("gbdt_pullback", "gbdt_occlusion"), ("malconv_ig", "malconv_occlusion")]
        rows: list[dict[str, Any]] = []
        for J in RESOLUTIONS:
            key = "" if J == 256 else f"_k{J}"
            if f"edges{key}" not in windows:
                continue
            edges = windows[f"edges{key}"]
            K = edges.shape[0] - 1
            w = np.repeat(np.arange(K), np.diff(edges))
            per = {"gbdt_pullback": np.bincount(w, weights=pullback, minlength=K),
                   "gbdt_occlusion": np.asarray(windows[f"occlusion{key}:gbdt"], dtype=np.float64)[:K],
                   "malconv_ig": np.bincount(w, weights=ig, minlength=K),
                   "malconv_occlusion": np.bincount(w, weights=mc_occ, minlength=K)}
            rows += agreement(per, pairs, str(J), TOP_WINDOWS, ties.permutation(K).astype(np.int64))
        rows += agreement({"gbdt_pullback": pullback, "malconv_ig": ig}, pairs, "bytes", TOP_BYTES, byte_perm)

        # Cross-deletion: each ranking deletes its top bytes; both models score every deleted file.
        protection = protect(data, header="typical")
        gbdt, malconv = _STATE["gbdt"], _STATE["malconv"]
        f0 = {"gbdt": task["gbdt_log_odds"], "malconv": task["malconv_log_odds"]}
        d = {name: float(np.sign(v)) or 1.0 for name, v in f0.items()}
        edges = windows["edges"]
        K = edges.shape[0] - 1
        w = np.repeat(np.arange(K), np.diff(edges))
        stride = task["stride"]
        mc_edges = np.unique(np.minimum(np.append(np.arange(0, m, stride), m), m)).astype(np.int64)
        orders = {
            "gbdt_pullback": element_order(pullback, d["gbdt"], byte_perm),
            "gbdt_pullback_k256": window_order(np.bincount(w, weights=pullback, minlength=K), edges, d["gbdt"], ties.permutation(K).astype(np.int64)),
            "gbdt_occlusion_k256": window_order(windows["occlusion:gbdt"], edges, d["gbdt"], ties.permutation(K).astype(np.int64)),
            "malconv_ig": element_order(ig, d["malconv"], byte_perm),
            "malconv_ig_k256": window_order(np.bincount(w, weights=ig, minlength=K), edges, d["malconv"], ties.permutation(K).astype(np.int64)),
            "malconv_occlusion": window_order(mc_occ[mc_edges[:-1]], mc_edges, d["malconv"], ties.permutation(mc_edges.shape[0] - 1).astype(np.int64)),
        }
        rng = np.random.default_rng(task["seed"])
        for r in range(NUM_RANDOM):
            orders[f"random:{r}"] = window_order(rng.permutation(K).astype(np.float64), edges)
        cache: dict[bytes, dict[str, Any]] = {}
        curves: list[dict[str, Any]] = []
        for method, order in orders.items():
            for budget, mask in zip(BUDGETS, budget_masks(order, protection.mask, BUDGETS)):
                key = np.packbits(mask).tobytes()
                if key not in cache:
                    z = ablate(data, mask, protection.mask, "zeros", None, protection.header, protection.header_values)
                    try:
                        x = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
                        problem = verify(protection, data, z, float(x[IS_PE]))
                        g = float(gbdt(x[None, :])[0]) if problem is None else float("nan")
                    except Exception as err:
                        problem, g = f"extraction failed: {type(err).__name__}", float("nan")
                    cache[key] = {"gbdt": g, "malconv": malconv_log_odds(malconv, z), "valid": problem is None}
                curves.append({"method": method, "budget": budget} | cache[key])
        info = {"status": "ok", "error": "", "size": m, "gbdt_log_odds": f0["gbdt"], "malconv_log_odds": f0["malconv"],
                "extractions": len(cache), "seconds": time.perf_counter() - t_0}
        return [base | r for r in rows], [base | c for c in curves], base | info
    except Exception as err:
        return [], [], base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300], "seconds": time.perf_counter() - t_0}


################################################################################
# Summary
################################################################################


def summarize(agree: pl.DataFrame, curves: pl.DataFrame, files: pl.DataFrame) -> None:
    """Print the agreement medians and the cross-deletion areas (PB1's area: mean evidence removed, budgets 0.1%-50%)."""
    order = {r: i for i, r in enumerate([*map(str, RESOLUTIONS), "bytes"])}
    table = (agree.group_by("pair", "resolution")
             .agg(pl.len().alias("n"), pl.col("rho").median().alias("rho_median"), pl.col("top").mean().alias("top_mean"), pl.col("chance").mean().alias("chance_mean"))
             .with_columns(pl.col("resolution").replace_strict(order).alias("_r")).sort("pair", "_r").drop("_r"))
    with pl.Config(tbl_rows=100, tbl_width_chars=200, float_precision=3):
        print("Agreement (median Spearman rho over files; mean top overlap vs. chance):")
        print(table)
    f0 = files.select("index", pl.col("gbdt_log_odds").alias("g0"), pl.col("malconv_log_odds").alias("m0"))
    c = curves.join(f0, on="index").filter(pl.col("budget") <= 0.5)
    c = c.with_columns(
        (pl.col("g0").sign() * (pl.col("g0") - pl.col("gbdt"))).alias("removed_gbdt"),
        (pl.col("m0").sign() * (pl.col("m0") - pl.col("malconv"))).alias("removed_malconv"),
    )
    valid = c.group_by("index").agg(pl.col("valid").all()).filter(pl.col("valid"))["index"]
    c = c.filter(pl.col("index").is_in(valid.implode()))
    per_file = c.with_columns(pl.when(pl.col("method").str.starts_with("random")).then(pl.lit("random")).otherwise(pl.col("method")).alias("method")) \
        .group_by("index", "method").agg(pl.col("removed_gbdt").mean(), pl.col("removed_malconv").mean())
    table = per_file.group_by("method").agg(pl.len().alias("n"), pl.col("removed_gbdt").mean().alias("area_gbdt"),
                                           pl.col("removed_malconv").mean().alias("area_malconv")).sort("method")
    with pl.Config(tbl_rows=100, float_precision=3):
        print(f"\nCross-deletion area (mean evidence removed, budgets <= 50%), {valid.len()} files with every deletion verified:")
        print(table)


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT and of MalConv.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files and GBDT occlusion scores to reuse.")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files per label (0: all), for smoke tests.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_check")
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
    windows = load_window_scores(args.pb1_run / "window_scores.npz")
    gbdt_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    malconv_file = args.checkpoints / f"malconv-seed{args.seed}.pt"
    print(f"3-A check: {files.height} files from {args.pb1_run.as_posix()}, {EXPLAINER} pulled back, MalConv seed {args.seed}.", flush=True)

    # Phase 1, on the GPU: MalConv's log-odds, Integrated Gradients, and occlusion, file by file.
    t_0 = time.time()
    model = load_pretrained_malconv(malconv_file).to(args.device)
    stride = int(model.conv_1.stride[0])
    tasks: list[dict[str, Any]] = []
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="MalConv", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        log_odds, ig, occ = malconv_explanations(model, data, args.ig_steps, args.device)
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
                      "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]), "stride": stride,
                      "explanation": np.asarray(explanations[int(r["index"])], dtype=np.float64),
                      "windows": windows[int(r["index"])], "gbdt_log_odds": float(r["log_odds:gbdt"]),
                      "malconv_log_odds": log_odds, "ig": ig, "mc_occlusion": occ})
    seconds_malconv = time.time() - t_0
    del model
    print(f"Phase 1 (MalConv on {args.device}): {seconds_malconv:.0f} s.", flush=True)

    # Phase 2, on the CPU: provenance, agreement, and the deletions, which need feature extraction.
    t_0 = time.time()
    agree: list[dict[str, Any]] = []
    curves: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    tasks.sort(key=lambda t: -t["ig"].shape[0])
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(gbdt_file, malconv_file)) as pool:
        for a, c, info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            agree += a
            curves += c
            infos.append(info)
            if info["status"] != "ok":
                print(f"File {info['index']}: {info['error']}", flush=True)
    seconds_files = time.time() - t_0
    print(f"Phase 2 (files on {args.num_workers} workers): {seconds_files:.0f} s.", flush=True)

    agree_df, curves_df, files_df = pl.DataFrame(agree), pl.DataFrame(curves), pl.DataFrame(infos).sort("index")
    agree_df.write_parquet(outdir / "agreement.parquet")
    curves_df.write_parquet(outdir / "curves.parquet")
    files_df.write_parquet(outdir / "files.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "explainer": EXPLAINER, "budgets": list(BUDGETS), "seconds_malconv": seconds_malconv,
              "seconds_files": seconds_files, "failed": int((files_df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(agree_df, curves_df, files_df.filter(pl.col("status") == "ok"))


if __name__ == "__main__":
    main()
