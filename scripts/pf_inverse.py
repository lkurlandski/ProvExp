"""
Go/no-go for the iterated pushforward (docs/theory.md, Pillar B): can the pushforward recover a feature-space
explanation from its pullback better when it is iterated than in one step?

For each file and native explainer a (path and interventional TreeSHAP, KernelSHAP), the byte-level explanation is
b = P a_att, the pullback of a's attributable part. It is pushed back into the features in four ways:
    one step        psi(b) = P^T D^+ b, today's pushforward (the byte-level round trip of scripts/pf1_resolution.py)
    landweber_kN    N iterations of a_{k+1} = a_k + psi(b - P a_k), starting from a_1 = psi(b)
    cg              the solution of M a = psi(b), M = P^T D^+ P, by conjugate gradients (the limit of the iteration)
    twins           an oracle: cg, with the native explanation's split inside each group of features with identical
                    provenance columns (cg splits such "twins" evenly; their differences lie in P's null space)
Each recovered explanation is scored by the feature-space deletion test of scripts/pf1.py (same model, references,
ties, and budgets), against the native explainer's own curve: R = area(recovered) / area(a). Alongside, the relative
recovery error ||a_att - a_rec||_1 / ||a_att||_1 and the relative residual ||b - P a_rec||_1 / ||b||_1.

Hypothesis (docs/theory.md): R rises from about 0.80 (one step) toward 1, minus what features that cannot be told apart
(linearly dependent provenance columns) hold. No-go if the iteration gains little over one step.

The twins oracle measures the identifiability ceiling (run 62): by Proposition Exact Pushforward (iii), cg is already the
projection of the native explanation onto P's row space, i.e., everything the bytes determine, so no method can beat it
without outside information. The oracle asks how much of the remaining gap lies between twins (an analyst can read a
twin group as one unit) and how much in subtler linear dependences between provenance columns. Hypothesis: at bytes,
twins hold most of the gap (R near 0.95); at windows, P has at most 256 rows, so dependence goes far beyond twins.

Optionally (--resolutions), the same at K windows, through P coarsened to the windows (underdetermined there).

Inputs: as scripts/pf1_resolution.py. Outputs, in `{outdir}/seed-{seed}/{run name}/{name}/` (default name: inverse):
    curves.parquet      one row per (file, method, reference, budget): the log-odds
    recovery.parquet    one row per (file, explainer, resolution, method): recovery error and residual
    files.parquet       one row per file

Usage:
    PYTHONHASHSEED=0 python scripts/pf_inverse.py --run artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
    python scripts/pf_inverse.py --run ... --tables_only
    PYTHONHASHSEED=0 python scripts/pf_inverse.py --run ... --iterations --name ceiling   # one step, cg, twins only
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
from scipy.sparse.linalg import LinearOperator
from scipy.sparse.linalg import cg
from scipy.stats import wilcoxon
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import budget_masks
from provexp.ablation import window_edges
from provexp.data.tabular import load_features
from provexp.provenance import Provenance
from provexp.data.paths import EMBER2024_DATA

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
from pf1_resolution import coarsen_sparse  # noqa: E402


ROOT = Path(__file__).parent.parent
BYTES = 0
ITERATIONS = (2, 4, 8, 16, 32, 64, 128, 256)
CG_TOL = 1e-10
CG_MAXITER = 5000

FloatArray = npt.NDArray[np.float64]


################################################################################
# Inverse Pushforward
################################################################################


def operators(P: sparse.csr_matrix) -> tuple[Callable[[FloatArray], FloatArray], Callable[[FloatArray], FloatArray]]:
    """The pullback a -> P a and the pushforward b -> P^T D^+ b for a (rows, n) provenance matrix P."""
    D = np.asarray(P.sum(axis=1)).ravel()
    Dinv = np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0)
    PT = P.T.tocsr()

    def pull(a: FloatArray) -> FloatArray:
        return np.asarray(P @ a, dtype=np.float64).ravel()

    def push(b: FloatArray) -> FloatArray:
        return np.asarray(PT @ (Dinv * b), dtype=np.float64).ravel()

    return pull, push


def inverse_pushforwards(P: sparse.csr_matrix, b: FloatArray, iterations: tuple[int, ...]) -> dict[str, FloatArray]:
    """One step, the Landweber iterates at `iterations`, and the conjugate-gradient limit, for byte explanation b."""
    pull, push = operators(P)
    n = P.shape[1]
    a = push(b)
    out = {"onestep": a.copy()}
    last = max(iterations, default=1)
    for k in range(2, last + 1):
        a = a + push(b - pull(a))
        if k in iterations:
            out[f"landweber_k{k}"] = a.copy()
    M = LinearOperator((n, n), matvec=lambda v: push(pull(np.asarray(v, dtype=np.float64).ravel())), dtype=np.float64)
    sol, _ = cg(M, push(b), x0=out["onestep"], rtol=CG_TOL, maxiter=CG_MAXITER)
    out["cg"] = np.asarray(sol, dtype=np.float64)
    return out


def twin_groups(P: sparse.csr_matrix) -> npt.NDArray[np.int64]:
    """A group label per column of P, shape (n,): columns with identical entries (to 12 digits) share a label."""
    C = P.tocsc()
    C.sort_indices()
    keys: dict[tuple[bytes, bytes], int] = {}
    labels = np.empty(C.shape[1], dtype=np.int64)
    for j in range(C.shape[1]):
        s, e = C.indptr[j], C.indptr[j + 1]
        key = (C.indices[s:e].tobytes(), np.round(C.data[s:e], 12).tobytes())
        labels[j] = keys.setdefault(key, len(keys))
    return labels


def group_mean(a: FloatArray, labels: npt.NDArray[np.int64]) -> FloatArray:
    """Each entry of `a` replaced by the mean of its group."""
    sizes = np.bincount(labels)
    return (np.bincount(labels, weights=a) / sizes)[labels]


def provenance_matrix(prov: Provenance) -> sparse.csr_matrix:
    """The byte-level P without the null element as a sparse (m, n) matrix (the attributable part is all we push)."""
    m = prov.num_elements
    return coarsen_sparse(prov, np.arange(m + 1, dtype=np.int64))


################################################################################
# Per File
################################################################################


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """The deletion curves of every native explainer and of its recovered explanations."""
    f: Callable[[FloatArray], FloatArray] = _STATE["f"]
    background: FloatArray = _STATE["background"]
    saved: dict[str, npt.NDArray[Any]] = task["saved"]
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    x, prov = _STATE["extractor"].feature_vector_with_provenance(data)
    x = np.asarray(x, dtype=np.float64)
    n, m = x.shape[0], prov.num_elements
    f0 = float(f(x[None, :])[0])
    direction = float(np.sign(f0)) or 1.0
    tiebreak = np.random.default_rng(task["seed"]).permutation(n).astype(np.int64)
    att = prov.included

    matrices: dict[int, sparse.csr_matrix] = {}
    for K in task["resolutions"]:
        matrices[K] = provenance_matrix(prov) if (K == BYTES or K >= m) else coarsen_sparse(prov, window_edges(m, K))

    base = {"index": task["index"], "label": task["label"]}
    methods: dict[str, FloatArray] = {}
    records: list[dict[str, Any]] = []
    for name, a in task["native"].items():
        methods[name] = a
        a_att = np.where(att, a, 0.0)
        l1 = float(np.abs(a_att).sum())
        for K, P in matrices.items():
            pull, _ = operators(P)
            b = pull(a_att)
            recovered = inverse_pushforwards(P, b, task["iterations"])
            labels = twin_groups(P)
            # Inside a twin group, cg is constant; the oracle restores the native split (a null-space move, Pa unchanged).
            recovered["twins"] = recovered["cg"] + (a_att - group_mean(a_att, labels))
            # Features without provenance (all zeros here: the null element's) are not twins.
            sizes = np.where(np.diff(P.tocsc().indptr) > 0, np.bincount(labels)[labels], 0)
            twin_mass = float(np.abs(a_att[sizes > 1]).sum()) / l1 if l1 > 0 else float("nan")
            for method, a_rec in recovered.items():
                methods[f"inv_k{K}_{method}:{name}"] = a_rec
                records.append(base | {
                    "explainer": name, "resolution": K, "method": method, "rows": P.shape[0],
                    "groups": int(np.unique(labels[sizes > 0]).shape[0]), "twin_features": int((sizes > 1).sum()), "twin_mass": twin_mass,
                    "error": float(np.abs(a_att - a_rec).sum()) / l1 if l1 > 0 else float("nan"),
                    "residual": float(np.abs(b - pull(a_rec)).sum()) / float(np.abs(b).sum()) if l1 > 0 else float("nan"),
                })

    curves: list[dict[str, Any]] = []
    protected = np.zeros(n, dtype=np.bool_)
    for method, a in methods.items():
        masks = budget_masks(feature_order(a, direction, tiebreak), protected, BUDGETS)
        for reference, log_odds in (("ablated", delete_to_reference(f, x, saved["x_ablated"], masks)),
                                    ("background", delete_to_background(f, x, background, masks))):
            curves.extend(base | {"method": method, "reference": reference, "budget": budget, "log_odds": float(v)}
                          for budget, v in zip(BUDGETS, log_odds))
    info = base | {"log_odds": f0, "num_elements": m, "max_x_difference": float(np.abs(x - saved["x"]).max())}
    return curves, records, info


################################################################################
# Tables
################################################################################


METHOD_ORDER = ["onestep"] + [f"landweber_k{k}" for k in ITERATIONS] + ["cg", "twins"]


def tables(curves: pl.DataFrame, recovery: pl.DataFrame, files: pl.DataFrame) -> None:
    """R per method and resolution, the recovery error and residual, and how many files improve over one step."""
    print(f"{files.height} files; max |x - saved x| {float(files['max_x_difference'].to_numpy().max()):.3g}.\n")
    areas = (
        curves.join(files.select("index", "log_odds").rename({"log_odds": "f0"}), on="index")
        .with_columns((pl.col("f0").sign().replace(0, 1) * (pl.col("f0") - pl.col("log_odds"))).alias("removed"))
        .filter(pl.col("budget") < 1.0)
        .group_by("index", "method", "reference").agg(pl.col("removed").mean().alias("area"))
    )
    native = areas.filter(~pl.col("method").str.starts_with("inv_")).rename({"method": "explainer", "area": "native"})
    rec = (
        areas.filter(pl.col("method").str.starts_with("inv_"))
        .with_columns(
            pl.col("method").str.extract(r"^inv_k(\d+)_").cast(pl.Int64).alias("resolution"),
            pl.col("method").str.extract(r"^inv_k\d+_([a-z0-9_]+):").alias("variant"),
            pl.col("method").str.extract(r":(.+)$").alias("explainer"),
        )
        .join(native, on=["index", "explainer", "reference"])
        .join(recovery.rename({"method": "variant"}), on=["index", "explainer", "resolution", "variant"])
    )
    for K in sorted(set(rec["resolution"].to_list()), key=lambda k: (k == 0, k)):
        label = "bytes" if K == 0 else f"{K:,} windows"
        for reference in ("ablated", "background"):
            t = rec.filter((pl.col("resolution") == K) & (pl.col("reference") == reference))
            rows = []
            for v in [v for v in METHOD_ORDER if v in set(t["variant"].to_list())]:
                row: dict[str, object] = {"method": v}
                for e in NATIVE:
                    g = t.filter((pl.col("variant") == v) & (pl.col("explainer") == e))
                    row[f"R {e}"] = float(g["area"].to_numpy().sum() / g["native"].to_numpy().sum()) if g.height else float("nan")
                g = t.filter((pl.col("variant") == v) & (pl.col("explainer") == "treeshap_interventional"))
                row["error (median)"] = float(np.median(g["error"].to_numpy())) if g.height else float("nan")
                row["residual (median)"] = float(np.median(g["residual"].to_numpy())) if g.height else float("nan")
                rows.append(row)
            print(f"## {label}, reference {reference}: R = mean area / mean area of the explainer "
                  "(error, residual: interventional TreeSHAP)\n")
            print(markdown(pl.DataFrame(rows)), "\n")
        g = recovery.filter((pl.col("resolution") == K) & (pl.col("method") == "cg")
                            & (pl.col("explainer") == "treeshap_interventional"))
        if g.height and "twin_mass" in g.columns:
            print(f"{label}: median {float(np.median(g['groups'].to_numpy())):,.0f} distinct provenance columns; "
                  f"{float(np.median(g['twin_features'].to_numpy())):,.0f} features have a twin, holding "
                  f"{float(np.median(g['twin_mass'].to_numpy())):.1%} of |TreeSHAP| (medians over files).\n")
        # Paired: files where cg beats one step (ablated reference, interventional TreeSHAP).
        t = rec.filter((pl.col("resolution") == K) & (pl.col("reference") == "ablated")
                       & (pl.col("explainer") == "treeshap_interventional"))
        one = t.filter(pl.col("variant") == "onestep").select("index", pl.col("area").alias("one"))
        lim = t.filter(pl.col("variant") == "cg").select("index", pl.col("area").alias("lim"))
        j = one.join(lim, on="index")
        if j.height:
            d = (j["lim"] - j["one"]).to_numpy()
            p = float(wilcoxon(d).pvalue) if np.any(d != 0) else float("nan")
            print(f"{label}: cg vs one step, interventional TreeSHAP, ablated: larger on {int((d > 0).sum())} of "
                  f"{j.height} files, median difference {float(np.median(d)):.3f} log-odds, Wilcoxon p = {p:.2g}.\n")


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Go/no-go for the iterated pushforward: recover explanations from their pullback.")
    parser.add_argument("--run", type=Path, required=True, help="A faithfulness.py output directory with window_scores.npz.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resolutions", type=int, nargs="+", default=[BYTES], help="Window counts; 0 is the bytes.")
    parser.add_argument("--iterations", type=int, nargs="*", default=list(ITERATIONS),
                        help="Landweber iterates to keep (none: one step, cg, and twins only).")
    parser.add_argument("--name", type=str, default="inverse", help="The output subdirectory.")
    parser.add_argument("--background_size", type=int, default=1000)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "pf1")
    parser.add_argument("--num_files", type=int, default=None, help="Only the first files (a smoke test).")
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--tables_only", action="store_true")
    args = parser.parse_args()

    if any(K < 0 for K in args.resolutions):
        raise ValueError(f"Resolutions must be window counts or 0 (bytes). Got {args.resolutions}.")
    if any(k < 2 for k in args.iterations):
        raise ValueError(f"Landweber iterates start at 2 (1 is one step). Got {args.iterations}.")
    outdir = args.outdir / f"seed-{args.seed}" / args.run.name / args.name
    if args.tables_only:
        tables(pl.read_parquet(outdir / "curves.parquet"), pl.read_parquet(outdir / "recovery.parquet"),
               pl.read_parquet(outdir / "files.parquet"))
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

    rows = pl.read_parquet(args.explanations / "background.parquet")["row"].to_numpy()
    if args.background_size < rows.shape[0]:
        rows = np.sort(np.random.default_rng(0).choice(rows, args.background_size, replace=False))
    X_tr, _ = load_features(args.features, "tr")
    background = np.asarray(X_tr[rows], dtype=np.float64)
    del X_tr

    resolutions = tuple(dict.fromkeys(args.resolutions))
    tasks = [{"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
              "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]), "resolutions": resolutions,
              "iterations": tuple(args.iterations), "native": {e: A[int(r["index"])] for e, A in native.items()},
              "saved": saved[int(r["index"])]}
             for r in run_files.to_dicts()]
    print(f"Inverse pushforward: {len(tasks)} files, resolutions {list(resolutions)} (0 = bytes), "
          f"{args.num_workers} workers.", flush=True)
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    curves: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file, background)) as pool:
        for c, r, info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=30):
            curves.extend(c)
            records.extend(r)
            infos.append(info)
    curves_df = pl.DataFrame(curves)
    recovery_df = pl.DataFrame(records).sort("index", "explainer", "resolution", "method")
    files_df = pl.DataFrame(infos).sort("index")
    curves_df.write_parquet(outdir / "curves.parquet")
    recovery_df.write_parquet(outdir / "recovery.parquet")
    files_df.write_parquet(outdir / "files.parquet")
    tables(curves_df, recovery_df, files_df)
    print(f"Wrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
