"""
PF1's resolution trend (docs/pf1_plan.md, "Decision: claim 3, option A"): how much of a feature-space explanation's
faithfulness survives being expressed at K windows, from 64 windows to the bytes, and whether P predicts it.

For each file, native explainer a (path and interventional TreeSHAP, KernelSHAP), and resolution K, the window round
trip a_K = psi_K(W_K P a_att) pulls back the attributable part of a, sums it over K windows, and pushes it forward
through P coarsened to the same windows; this is exactly the pull-push round trip M_K a_att of the coarsened P. Its
feature-space deletion curve, against the native explainer's own, gives R(K) = area(a_K) / area(a): what a K-window
explanation carrying the explainer's information can reach. Alongside, from P alone or P and a:
    mean overlap        the mean O_j(K) over the attributable features: P only, measurable before any explanation
    weighted overlap    the same weighted by |a_j|
    loss, bound         ||a_att - M_K a_att||_1 and CP's bound 2 sum_j |a_j| O_j(K), both relative to ||a_att||_1

Resolutions: 64, 256, 1,024, 4,096 (PF1's sweep), 16,384, 65,536, 262,144 windows (beyond any affordable occlusion),
and the bytes themselves (0). A file with fewer bytes than K windows is at byte resolution there.

The coarsened P is built sparse (`coarsen_sparse`): a dense (K, n) matrix at 262,144 windows would take gigabytes.

Inputs: a faithfulness.py run (its files and window_scores.npz, for x and the fully ablated file's features), the
saved explanations, and the background, as in scripts/pf1.py (same deletion test, ties, and seeds).
Outputs, in `{outdir}/seed-{seed}/{run name}/resolution/`:
    curves.parquet      one row per (file, method, reference, budget): the log-odds (candidates: all features)
    resolution.parquet  one row per (file, explainer, resolution): windows, overlap, loss, bound

Usage:
    PYTHONHASHSEED=0 python scripts/pf1_resolution.py --run artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
    python scripts/pf1_resolution.py --run ... --tables_only
"""

from argparse import ArgumentParser
from collections.abc import Callable
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import sparse
from scipy.stats import spearmanr
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import budget_masks
from provexp.ablation import window_edges
from provexp.boxmatrix import expand_ranges
from provexp.data.tabular import load_features
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from faithfulness import load_window_scores  # noqa: E402
from pf1 import _STATE  # noqa: E402
from pf1 import NATIVE  # noqa: E402
from pf1 import _init_worker  # noqa: E402
from pf1 import delete_to_background  # noqa: E402
from pf1 import delete_to_reference  # noqa: E402
from pf1 import feature_order  # noqa: E402
from pf1 import markdown  # noqa: E402


ROOT = Path(__file__).parent.parent
BYTES = 0  # The resolution of the elements themselves.
RESOLUTIONS = (64, 256, 1024, 4096, 16384, 65536, 262144, BYTES)

FloatArray = npt.NDArray[np.float64]


################################################################################
# The Coarsened Provenance, Sparse
################################################################################


def coarsen_sparse(prov: Provenance, edges: npt.NDArray[np.int64]) -> sparse.csr_matrix:
    """
    P coarsened to K windows as a sparse matrix of shape (K, n), without the null element: entry (w, j) is the share
    of feature j's provenance in window w. The same values as `provexp.ablation.coarsen` (which is dense).
    """
    m, n = prov.num_elements, prov.num_features
    if edges[0] != 0 or edges[-1] != m:
        raise ValueError(f"Expected window edges from 0 to {m}. Got {edges[0]} to {edges[-1]}.")
    K = edges.shape[0] - 1
    pieces = prov.pieces()
    real = pieces.lo < m
    col, lo, hi, val = pieces.col[real], pieces.lo[real], np.minimum(pieces.hi[real], m), pieces.val[real]
    first = np.searchsorted(edges, lo, side="right") - 1
    last = np.searchsorted(edges, hi - 1, side="right") - 1
    which, window = expand_ranges(first, last + 1)
    overlap = np.minimum(hi[which], edges[window + 1]) - np.maximum(lo[which], edges[window])
    return sparse.csr_matrix((val[which] * overlap, (window, col[which])), shape=(K, n))


def window_statistics(P: sparse.csr_matrix) -> tuple[FloatArray, FloatArray]:
    """The row sums D of a coarsened P, shape (K,), and each feature's overlap O_j = 1 - sum_w P_wj^2 / D_w, shape (n,)."""
    D = np.asarray(P.sum(axis=1)).ravel()
    Dinv = np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0)
    return D, 1.0 - np.asarray(P.multiply(P).T @ Dinv).ravel()


def window_pushforward_sparse(P: sparse.csr_matrix, D: FloatArray, b: FloatArray) -> FloatArray:
    """psi_K(b) = P^T D^+ b for a score per window b, shape (n,)."""
    Dinv = np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0)
    return np.asarray(P.T @ (Dinv * b), dtype=np.float64).ravel()


################################################################################
# Per File
################################################################################


def round_trips(prov: Provenance, a: FloatArray, resolutions: tuple[int, ...]) -> tuple[dict[int, FloatArray], list[dict[str, Any]]]:
    """
    The window round trip of `a` at each resolution, and its statistics (see the module docstring).

    Returns:
        Per resolution, a_K, shape (n,); and one record per resolution.
    """
    m = prov.num_elements
    att = prov.included
    a_att = np.where(att, a, 0.0)
    l1 = float(np.abs(a_att).sum())
    w = np.abs(a_att)
    b = prov.pullback(a_att)[:m]
    out: dict[int, FloatArray] = {}
    records: list[dict[str, Any]] = []
    byte_level: tuple[FloatArray, FloatArray] | None = None
    for K in resolutions:
        if K == BYTES or K >= m:
            if byte_level is None:
                byte_level = (prov.pull_push(a_att), prov.overlap().per_feature)
            a_K, O = byte_level
            num_windows = m
        else:
            edges = window_edges(m, K)
            P = coarsen_sparse(prov, edges)
            D, O = window_statistics(P)
            a_K = window_pushforward_sparse(P, D, np.add.reduceat(b, edges[:-1]))
            num_windows = edges.shape[0] - 1
        out[K] = a_K
        records.append({
            "resolution": K, "num_windows": num_windows,
            "mean_overlap": float(O[att].mean()) if att.any() else float("nan"),
            "weighted_overlap": float((w[att] * O[att]).sum() / w[att].sum()) if w[att].sum() > 0 else float("nan"),
            "loss": float(np.abs(a_att - a_K).sum()) / l1 if l1 > 0 else float("nan"),
            "bound": float(2 * (w * np.where(att, O, 0.0)).sum()) / l1 if l1 > 0 else float("nan"),
        })
    return out, records


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """The deletion curves of every native explainer and its round trips, and the round trips' statistics."""
    f: Callable[[FloatArray], FloatArray] = _STATE["f"]
    background: FloatArray = _STATE["background"]
    saved: dict[str, npt.NDArray[Any]] = task["saved"]
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    x, prov = _STATE["extractor"].feature_vector_with_provenance(data)
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    f0 = float(f(x[None, :])[0])
    direction = float(np.sign(f0)) or 1.0
    # The same tie-break permutation as scripts/pf1.py (its first draw from the file's seed).
    tiebreak = np.random.default_rng(task["seed"]).permutation(n).astype(np.int64)

    base = {"index": task["index"], "label": task["label"]}
    methods: dict[str, FloatArray] = {}
    stats: list[dict[str, Any]] = []
    for name, a in task["native"].items():
        methods[name] = a
        trips, records = round_trips(prov, a, task["resolutions"])
        for K, a_K in trips.items():
            methods[f"windowtrip_k{K}:{name}"] = a_K
        stats.extend(base | {"explainer": name} | r for r in records)

    curves: list[dict[str, Any]] = []
    protected = np.zeros(n, dtype=np.bool_)
    for method, a in methods.items():
        masks = budget_masks(feature_order(a, direction, tiebreak), protected, BUDGETS)
        for reference, log_odds in (("ablated", delete_to_reference(f, x, saved["x_ablated"], masks)),
                                    ("background", delete_to_background(f, x, background, masks))):
            curves.extend(base | {"method": method, "reference": reference, "budget": budget, "log_odds": float(v)}
                          for budget, v in zip(BUDGETS, log_odds))
    info = base | {"log_odds": f0, "num_elements": prov.num_elements, "max_x_difference": float(np.abs(x - saved["x"]).max())}
    return curves, stats, info


################################################################################
# Tables
################################################################################


def tables(curves: pl.DataFrame, stats: pl.DataFrame, files: pl.DataFrame, pf1_curves: pl.DataFrame | None) -> None:
    """Print the trend: R per resolution, the statistics of P, the bound, and the per-file correlations."""
    print(f"{files.height} files; max |x - saved x| {float(files['max_x_difference'].to_numpy().max()):.3g}.\n")
    areas = (
        curves.join(files.select("index", "log_odds").rename({"log_odds": "f0"}), on="index")
        .with_columns((pl.col("f0").sign().replace(0, 1) * (pl.col("f0") - pl.col("log_odds"))).alias("removed"))
        .filter(pl.col("budget") < 1.0)
        .group_by("index", "method", "reference").agg(pl.col("removed").mean().alias("area"))
    )
    # The file's ratio area(a_K) / area(a) per explainer and resolution.
    native = areas.filter(~pl.col("method").str.starts_with("windowtrip_")).rename({"method": "explainer", "area": "native"})
    trips = (
        areas.filter(pl.col("method").str.starts_with("windowtrip_"))
        .with_columns(
            pl.col("method").str.extract(r"^windowtrip_k(\d+):").cast(pl.Int64).alias("resolution"),
            pl.col("method").str.extract(r":(.+)$").alias("explainer"),
        )
        .join(native, on=["index", "explainer", "reference"])
        .join(stats, on=["index", "explainer", "resolution"])
    )

    def label(K: int) -> str:
        return "bytes" if K == 0 else f"{K:,}"

    order = [K for K in RESOLUTIONS if K in set(trips["resolution"].to_list())]
    for reference in ("ablated", "background"):
        t = trips.filter(pl.col("reference") == reference)
        rows = []
        for K in order:
            row: dict[str, object] = {"resolution": label(K)}
            for e in NATIVE:
                g = t.filter((pl.col("resolution") == K) & (pl.col("explainer") == e))
                row[f"R {e}"] = float(g["area"].to_numpy().mean() / g["native"].to_numpy().mean()) if g.height else float("nan")
            g = t.filter((pl.col("resolution") == K) & (pl.col("explainer") == "treeshap_path"))
            row |= {
                "windows (median)": float(np.median(g["num_windows"].to_numpy())),
                "mean overlap (P only)": float(np.median(g["mean_overlap"].to_numpy())),
                "weighted overlap": float(np.median(g["weighted_overlap"].to_numpy())),
                "loss": float(np.median(g["loss"].to_numpy())),
                "bound": float(np.median(g["bound"].to_numpy())),
            }
            rows.append(row)
        print(f"## Reference {reference}: R(K) = mean area of the window round trip / mean area of the explainer\n")
        print("(overlap, loss, and bound: median over files, path TreeSHAP)\n")
        print(markdown(pl.DataFrame(rows)), "\n")

    print("## CP's bound holds (loss <= bound, every file, explainer, resolution)\n")
    ok = stats.filter(pl.col("loss") <= pl.col("bound") + 1e-9)
    print(f"{ok.height} of {stats.height}; largest loss / bound {float((stats['loss'] / stats['bound']).to_numpy().max()):.3f}.\n")

    print("## Per-file: does the file's overlap predict its R? (Spearman over files, path TreeSHAP, ablated)\n")
    rows = []
    t = trips.filter((pl.col("reference") == "ablated") & (pl.col("explainer") == "treeshap_path")).with_columns(
        (pl.col("area") / pl.col("native")).alias("ratio"))
    for K in order:
        g = t.filter(pl.col("resolution") == K).drop_nulls()
        r = g["ratio"].to_numpy()
        rows.append({"resolution": label(K), "files": g.height,
                     "rho(R, mean overlap)": float(spearmanr(r, g["mean_overlap"].to_numpy()).statistic),
                     "rho(R, weighted overlap)": float(spearmanr(r, g["weighted_overlap"].to_numpy()).statistic),
                     "rho(R, loss)": float(spearmanr(r, g["loss"].to_numpy()).statistic)})
    print(markdown(pl.DataFrame(rows)), "\n")

    if pf1_curves is not None:
        # The window round trips of scripts/pf1.py at 64-4,096 windows must be reproduced (dense vs. sparse P).
        old = pf1_curves.filter(pl.col("method").str.starts_with("windowtrip_") & (pl.col("candidates") == "all"))
        j = old.join(curves, on=["index", "method", "reference", "budget"], suffix="_new")
        if j.height:
            diff = (j["log_odds"] - j["log_odds_new"]).abs()
            print(f"Check against scripts/pf1.py's window round trips: {j.height} curve points, max |difference| "
                  f"{float(diff.max()):.3g}, {int((diff > 1e-9).sum())} differ.\n")  # type: ignore[arg-type]


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="PF1's resolution trend: window round trips from 64 windows to the bytes.")
    parser.add_argument("--run", type=Path, required=True, help="A faithfulness.py output directory with window_scores.npz.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resolutions", type=int, nargs="+", default=list(RESOLUTIONS), help="Window counts; 0 is the bytes.")
    parser.add_argument("--background_size", type=int, default=1000)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "pf1")
    parser.add_argument("--num_files", type=int, default=None, help="Only the first files (a smoke test).")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--tables_only", action="store_true")
    args = parser.parse_args()

    if any(K < 0 for K in args.resolutions):
        raise ValueError(f"Resolutions must be window counts or 0 (bytes). Got {args.resolutions}.")
    pf1_dir = args.outdir / f"seed-{args.seed}" / args.run.name
    outdir = pf1_dir / "resolution"
    pf1_curves = pl.read_parquet(pf1_dir / "curves.parquet") if (pf1_dir / "curves.parquet").exists() else None
    if args.tables_only:
        tables(pl.read_parquet(outdir / "curves.parquet"), pl.read_parquet(outdir / "resolution.parquet"),
               pl.read_parquet(outdir / "files.parquet"), pf1_curves)
        return
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    outdir.mkdir(parents=True, exist_ok=True)

    run_files = pl.read_parquet(args.run / "files.parquet").filter(pl.col("status") == "ok").sort("index")
    saved = load_window_scores(args.run / "window_scores.npz")
    run_files = run_files.filter(pl.col("index").is_in(list(saved)))
    if args.num_files is not None:
        run_files = run_files.head(args.num_files)
    indir = args.explanations / f"seed-{args.seed}"
    native = {e: np.load(indir / f"{e}.npy") for e in NATIVE}
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    run_files = run_files.select("index", "name", "label").join(location, on="name", how="left")

    # The same background as scripts/pf1.py.
    rows = pl.read_parquet(args.explanations / "background.parquet")["row"].to_numpy()
    if args.background_size < rows.shape[0]:
        rows = np.sort(np.random.default_rng(0).choice(rows, args.background_size, replace=False))
    X_tr, _ = load_features(args.features, "tr")
    background = np.asarray(X_tr[rows], dtype=np.float64)
    del X_tr

    resolutions = tuple(dict.fromkeys(args.resolutions))
    tasks = [{"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
              "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]), "resolutions": resolutions,
              "native": {e: A[int(r["index"])] for e, A in native.items()}, "saved": saved[int(r["index"])]}
             for r in run_files.to_dicts()]
    print(f"PF1 resolution trend: {len(tasks)} files, resolutions {list(resolutions)} (0 = bytes), "
          f"{args.num_workers} workers.", flush=True)
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    curves: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file, background)) as pool:
        for c, s, info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=30):
            curves.extend(c)
            stats.extend(s)
            infos.append(info)
    curves_df = pl.DataFrame(curves)
    stats_df = pl.DataFrame(stats).sort("index", "explainer", "resolution")
    files_df = pl.DataFrame(infos).sort("index")
    curves_df.write_parquet(outdir / "curves.parquet")
    stats_df.write_parquet(outdir / "resolution.parquet")
    files_df.write_parquet(outdir / "files.parquet")
    tables(curves_df, stats_df, files_df, pf1_curves)
    print(f"Wrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
