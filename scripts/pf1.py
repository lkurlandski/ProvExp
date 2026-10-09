"""
PF1 (docs/pf1_plan.md): the faithfulness of the pushforward, by a feature-space deletion test of the GBDT.

Every method ranks the file's features; deleting the top-ranked features up to log-spaced budgets and re-scoring the
model gives a deletion curve. The methods:
    treeshap_path, treeshap_interventional, kernelshap_gbdt
                            the native feature-space explainers (they see the model directly)
    push:{source}           the pushforward a = P^T D^+ b of a direct problem-space explanation b over windows, through
                            the provenance coarsened to the same windows; sources: occlusion (K windows), occlusion_k{J}
                            (the sweep), kernelshap_windows (KernelSHAP over the K windows)
    naive:{source}          the incidence sum a_j = sum over the windows w that feature j reads of b_w (no D^+ split, so
                            a window feeding many features is counted many times): the naive baseline
    roundtrip:{explainer}   the pull-push round trip M a of a native explanation, at the byte level (a secondary
                            reference; CP bounds its L1 error)
    random:{seed}           a random order

Two references for a deleted feature (decision 1):
    ablated                 x_j := x~_j, the features of the fully ablated file under the PB1 operator: matched to the
                            problem-space explanations, and deleting every feature gives exactly PB1's end point
    background              the interventional expectation, mean over the background B of f(x with the deleted
                            features taken from B): matched to interventional TreeSHAP
and two candidate sets (decision 2): every feature (`all`), or only the attributable ones (`attributable`, the features
with nonempty provenance in this file), so that PF1 measures the translation and App-L the coverage gap.

Ties in a ranking (a pushforward is exactly zero on every feature its windows do not touch) are broken by a seeded
random permutation, the same for every method of a file, never by feature index.

Per file and method, with s the sign of f(x): removed(budget) = s (f(x) - f(deleted)); the area is the mean of
removed() over the budgets below 100%, as in PB1. The criterion fixed in advance (decision 5): the pushforward is
significantly above random and the naive baseline (Wilcoxon signed-rank over files), then R = mean area(pushforward) /
mean area(TreeSHAP) under the matched reference: >= 0.8 faithful, 0.5-0.8 partial, < 0.5 weakened.

Inputs: a faithfulness.py run (its files.parquet and window_scores.npz) and the saved explanations.
Outputs, in `{outdir}/seed-{seed}/{run name}/`:
    curves.parquet          one row per (file, method, candidates, reference, budget): the log-odds
    files.parquet           one row per file: log-odds, checks, and the gap diagnostics (the share of each native
                            explanation on unattributable features, and its |a|-weighted overlap at K windows)

Usage:
    PYTHONHASHSEED=0 python scripts/pf1.py --run artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
    python scripts/pf1.py --run ... --tables_only
"""

from argparse import ArgumentParser
from collections.abc import Callable
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any
from typing import Optional
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy.stats import wilcoxon
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import budget_masks
from provexp.ablation import coarsen
from provexp.ablation import coarsen_provenance
from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from faithfulness import load_window_scores  # noqa: E402


ROOT = Path(__file__).parent.parent
NATIVE = ["treeshap_path", "treeshap_interventional", "kernelshap_gbdt"]
NUM_RANDOM = 3
REFERENCES = ("ablated", "background")
CANDIDATES = ("all", "attributable")

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]

_STATE: dict[str, Any] = {}


################################################################################
# Rankings
################################################################################


def feature_order(scores: npt.ArrayLike, direction: float, tiebreak: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """
    The features ordered by decreasing `direction * scores`, ties broken by the permutation `tiebreak` (a feature
    earlier in it comes first), never by feature index.
    """
    s = np.asarray(scores, dtype=np.float64)
    if s.ndim != 1 or tiebreak.shape != s.shape:
        raise ValueError(f"Expected scores and a tie-break permutation of the same length. Got {s.shape} and {tiebreak.shape}.")
    return tiebreak[np.argsort(-np.sign(direction) * s[tiebreak], kind="stable")].astype(np.int64)


def incidence_pushforward(coarse: FloatArray, b: npt.ArrayLike) -> FloatArray:
    """
    The naive baseline: each feature gets the plain sum of the scores of the windows it reads, a_j = sum_w 1[P_wj > 0]
    b_w, with no D^+ split.

    Args:
        coarse: The provenance coarsened to K windows, shape (K + 1, n), as returned by `coarsen` (the last row, the
            null element, is ignored).
        b: A score per window, shape (K,).
    """
    b_ = np.asarray(b, dtype=np.float64)
    K = coarse.shape[0] - 1
    if b_.shape != (K,):
        raise ValueError(f"Expected one score per window ({K}). Got {b_.shape}.")
    return np.asarray((coarse[:K] > 0).T.astype(np.float64) @ b_, dtype=np.float64)


def window_pushforward(prov: Provenance, edges: npt.NDArray[np.int64], b: npt.ArrayLike) -> tuple[FloatArray, FloatArray]:
    """
    The pushforward of a score per window through the provenance coarsened to the same windows, and that naive baseline.

    Returns:
        psi(b) = P_w^T D_w^+ b, and the incidence sum, both of shape (n,).
    """
    coarse = coarsen(prov, edges)
    return coarsen_provenance(prov, edges).pushforward(np.asarray(b, dtype=np.float64)), incidence_pushforward(coarse, b)


################################################################################
# Feature-Space Deletion
################################################################################


def delete_to_reference(f: Callable[[FloatArray], FloatArray], x: FloatArray, reference: FloatArray, masks: list[BoolArray]) -> FloatArray:
    """The log-odds of x with each mask's features set to the reference's values, shape (len(masks),)."""
    X = np.where(np.stack(masks), reference[None, :], x[None, :])
    return f(X)


def delete_to_background(f: Callable[[FloatArray], FloatArray], x: FloatArray, background: FloatArray, masks: list[BoolArray]) -> FloatArray:
    """
    The interventional expectation of each deletion: the mean over the background rows of f with the mask's features
    taken from the row and the others from x, shape (len(masks),).
    """
    out = np.zeros(len(masks))
    for k, mask in enumerate(masks):
        Z = background.copy()
        Z[:, ~mask] = x[~mask]
        out[k] = float(f(Z).mean())
    return out


################################################################################
# Per File
################################################################################


def _init_worker(model_file: Path, background: FloatArray) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["f"] = gbdt_function(lgb.Booster(model_file=str(model_file)))
    _STATE["background"] = background


def methods_of(prov: Provenance, saved: dict[str, npt.NDArray[Any]], native: dict[str, FloatArray], rng: np.random.Generator) -> dict[str, FloatArray]:
    """Every method's feature attribution for one file (see the module docstring)."""
    out: dict[str, FloatArray] = dict(native)
    sources: list[tuple[str, npt.NDArray[np.int64], FloatArray]] = []
    for key, values in saved.items():
        if not key.endswith(":gbdt"):
            continue
        source = key.split(":", 1)[0]
        if source.startswith("occlusion_k"):
            edges = saved[f"edges_k{source.removeprefix('occlusion_k')}"]
        else:
            edges = saved["edges"]
        sources.append((source, edges, values))
    for source, edges, values in sorted(sources, key=lambda t: t[0]):
        out[f"push:{source}"], out[f"naive:{source}"] = window_pushforward(prov, edges, values)
    for name, a in native.items():
        out[f"roundtrip:{name}"] = prov.pull_push(a)
    for r in range(NUM_RANDOM):
        out[f"random:{r}"] = rng.normal(size=prov.num_features)
    return out


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The deletion curves of every method, candidate set, and reference for one file."""
    f: Callable[[FloatArray], FloatArray] = _STATE["f"]
    background: FloatArray = _STATE["background"]
    saved: dict[str, npt.NDArray[Any]] = task["saved"]
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    x, prov = _STATE["extractor"].feature_vector_with_provenance(data)
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    f0 = float(f(x[None, :])[0])
    direction = float(np.sign(f0)) or 1.0
    rng = np.random.default_rng(task["seed"])
    tiebreak = rng.permutation(n).astype(np.int64)
    methods = methods_of(prov, saved, task["native"], rng)

    attributable = ~prov.is_empty
    x_ablated = saved["x_ablated"]
    has_ablated = bool(np.all(np.isfinite(x_ablated)))
    records: list[dict[str, Any]] = []
    base = {"index": task["index"], "label": task["label"]}
    for candidates in CANDIDATES:
        protected = np.zeros(n, dtype=np.bool_) if candidates == "all" else ~attributable
        for method, a in methods.items():
            masks = budget_masks(feature_order(a, direction, tiebreak), protected, BUDGETS)
            curves = {"background": delete_to_background(f, x, background, masks)}
            if has_ablated:
                curves["ablated"] = delete_to_reference(f, x, x_ablated, masks)
            for reference, log_odds in curves.items():
                for budget, value in zip(BUDGETS, log_odds):
                    records.append(base | {"method": method, "candidates": candidates, "reference": reference,
                                           "budget": budget, "log_odds": float(value)})

    # The gap diagnostics (decision 5): what a pushforward cannot credit (unattributable features) and how much the
    # windows' provenance is shared (overlap at the K windows), each weighted by a native explanation.
    overlap = coarsen_provenance(prov, saved["edges"]).overlap().per_feature
    info: dict[str, Any] = base | {
        "name": task["name"], "num_elements": prov.num_elements, "num_attributable": int(attributable.sum()),
        "log_odds": f0, "log_odds_ablated": float(f(x_ablated[None, :])[0]) if has_ablated else float("nan"),
        "log_odds_background": float(f(background).mean()), "has_ablated": has_ablated,
        "max_x_difference": float(np.abs(x - saved["x"]).max()),
    }
    for name, a in task["native"].items():
        w = np.abs(a)
        total = float(w.sum())
        info[f"unattributable_share:{name}"] = float(w[~attributable].sum() / total) if total > 0 else float("nan")
        info[f"weighted_overlap:{name}"] = float((w[attributable] * overlap[attributable]).sum() / w[attributable].sum()) if w[attributable].sum() > 0 else float("nan")
    return records, info


################################################################################
# Tables
################################################################################


def markdown(df: pl.DataFrame, digits: int = 3) -> str:
    def fmt(v: object) -> str:
        return f"{v:.{digits}g}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def areas_of(curves: pl.DataFrame, files: pl.DataFrame) -> pl.DataFrame:
    """The deletion area per (file, method, candidates, reference), random averaged over its seeds."""
    return (
        curves
        .with_columns(pl.when(pl.col("method").str.starts_with("random:")).then(pl.lit("random")).otherwise(pl.col("method")).alias("method"))
        .group_by("index", "method", "candidates", "reference", "budget").agg(pl.col("log_odds").mean())
        .join(files.select("index", "log_odds").rename({"log_odds": "f0"}), on="index")
        .with_columns((pl.col("f0").sign().replace(0, 1) * (pl.col("f0") - pl.col("log_odds"))).alias("removed"))
        .filter(pl.col("budget") < 1.0)
        .group_by("index", "method", "candidates", "reference").agg(pl.col("removed").mean().alias("area"))
    )


def band(R: float) -> str:
    """The reading of the area ratio fixed in advance (docs/pf1_plan.md, decision 5)."""
    return "faithful" if R >= 0.8 else "partial" if R >= 0.5 else "weakened"


def tables(curves: pl.DataFrame, files: pl.DataFrame) -> None:
    """Print the PF1 tables: areas per method, the paired tests, and the criterion fixed in advance."""
    areas = areas_of(curves, files)
    print(f"{files.height} files; {int(files['has_ablated'].sum())} with a valid fully ablated file.\n")
    print(f"Checks: max |x - saved x| {float(files['max_x_difference'].to_numpy().max()):.3g}.\n")
    for reference in REFERENCES:
        for candidates in CANDIDATES:
            a = areas.filter((pl.col("reference") == reference) & (pl.col("candidates") == candidates))
            wide = a.pivot(on="method", index="index", values="area").drop_nulls()
            if wide.height == 0:
                continue
            ref_path, ref_int = float(wide["treeshap_path"].to_numpy().mean()), float(wide["treeshap_interventional"].to_numpy().mean())
            rows = []
            for method in sorted(c for c in wide.columns if c != "index"):
                x = wide[method].to_numpy()
                row: dict[str, object] = {"method": method, "mean area": float(x.mean()), "median area": float(np.median(x)),
                                          "R vs path": float(x.mean()) / ref_path, "R vs interventional": float(x.mean()) / ref_int}
                naive = method.replace("push:", "naive:") if method.startswith("push:") else ""
                for label, other in (("random", "random"), ("naive", naive)):
                    if other in ("", method) or other not in wide.columns:
                        row[f"wins vs {label}"], row[f"p vs {label}"] = "", ""
                        continue
                    y = wide[other].to_numpy()
                    row[f"wins vs {label}"] = f"{int((x > y).sum())}/{len(x)}"
                    row[f"p vs {label}"] = float(wilcoxon(x, y).pvalue) if np.any(x != y) else 1.0
                rows.append(row)
            print(f"## Reference {reference}, candidates {candidates} ({wide.height} files)\n")
            print(markdown(pl.DataFrame(rows).select("method", "mean area", "median area", "R vs path", "R vs interventional",
                                                     "wins vs random", "p vs random", "wins vs naive", "p vs naive")), "\n")

    print("## The criterion fixed in advance (matched reference: ablated, all features)\n")
    a = areas.filter((pl.col("reference") == "ablated") & (pl.col("candidates") == "all"))
    wide = a.pivot(on="method", index="index", values="area").drop_nulls()
    if wide.height:
        for method in sorted(c for c in wide.columns if c.startswith("push:")):
            x, rnd, naive = wide[method].to_numpy(), wide["random"].to_numpy(), wide[method.replace("push:", "naive:")].to_numpy()
            p_random = float(wilcoxon(x, rnd, alternative="greater").pvalue)
            p_naive = float(wilcoxon(x, naive, alternative="greater").pvalue)
            required = p_random < 0.05 and p_naive < 0.05
            for ref in ("treeshap_path", "treeshap_interventional"):
                R = float(x.mean() / wide[ref].to_numpy().mean())
                print(f"- {method} vs {ref}: above random p = {p_random:.2g}, above naive p = {p_naive:.2g} "
                      f"({'passes' if required else 'FAILS'} the requirement); R = {R:.2f} ({band(R)})")
        print()

    print("## Gap diagnostics (median over files)\n")
    rows = [{"explainer": name,
             "share on unattributable features": float(files[f"unattributable_share:{name}"].median()),  # type: ignore[arg-type]
             "|a|-weighted overlap at K windows": float(files[f"weighted_overlap:{name}"].median())}  # type: ignore[arg-type]
            for name in NATIVE if f"unattributable_share:{name}" in files.columns]
    print(markdown(pl.DataFrame(rows)), "\n")


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="PF1: the pushforward's faithfulness by feature-space deletion.")
    parser.add_argument("--run", type=Path, required=True, help="A faithfulness.py output directory with window_scores.npz.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained model.")
    parser.add_argument("--background_size", type=int, default=1000, help="Background rows for the interventional reference (a seeded subsample of the explainers' background).")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "pf1")
    parser.add_argument("--num_files", type=int, default=None, help="Only the first files (a smoke test).")
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--tables_only", action="store_true", help="Print the tables of an earlier run.")
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}" / args.run.name
    if args.tables_only:
        tables(pl.read_parquet(outdir / "curves.parquet"), pl.read_parquet(outdir / "files.parquet"))
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

    meta = pl.read_parquet(args.explanations / "background.parquet")
    rows = meta["row"].to_numpy()
    if args.background_size < rows.shape[0]:
        rows = np.sort(np.random.default_rng(0).choice(rows, args.background_size, replace=False))
    X_tr, _ = load_features(args.features, "tr")
    background = np.asarray(X_tr[rows], dtype=np.float64)
    del X_tr

    tasks = [{"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
              "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]),
              "native": {e: A[int(r["index"])] for e, A in native.items()}, "saved": saved[int(r["index"])]}
             for r in run_files.to_dicts()]
    print(f"PF1: {len(tasks)} files from {args.run.as_posix()}, background {background.shape[0]} rows, "
          f"{args.num_workers} workers.", flush=True)
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file, background)) as pool:
        for recs, info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=30):
            records.extend(recs)
            infos.append(info)
    curves = pl.DataFrame(records)
    files = pl.DataFrame(infos, infer_schema_length=None).sort("index")
    curves.write_parquet(outdir / "curves.parquet")
    files.write_parquet(outdir / "files.parquet")

    # The matched reference's end point is PB1's: deleting every feature gives the fully ablated file.
    pb1 = pl.read_parquet(args.run / "files.parquet").select("index", "log_odds_ablated:gbdt")
    end = files.filter(pl.col("has_ablated")).join(pb1, on="index")
    if end.height:
        print(f"End point vs. PB1's fully ablated file: max |difference| "
              f"{float((end['log_odds_ablated'] - end['log_odds_ablated:gbdt']).abs().max()):.3g}.\n")  # type: ignore[arg-type]
    tables(curves, files)
    print(f"Wrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
