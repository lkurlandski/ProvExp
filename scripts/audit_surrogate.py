"""
3-C revised (docs/experiments/audit.md), the realistic alternative to the pushforward: a surrogate of MalConv in the EMBER
feature space, explained there directly.

A LightGBM regressor on the EMBER v3 features predicts MalConv's log-odds (its saved test predictions). It is trained
on the test files outside the explanation set (90%, with 10% held out for early stopping and fidelity), so the
explanation set is never seen in training. The surrogate is then explained on the explanation set with interventional
TreeSHAP against the shared background, in the same order as the other explanations (`samples.parquet`), so that
scripts/audit_discover.py can treat it exactly like MalConv's pushed-forward explanation.

Outputs, in `{outdir}/seed-{seed}/`:
    model.txt               the surrogate
    shap.npy                interventional TreeSHAP of the surrogate on the explanation set, shape (2000, d)
    predictions.parquet     the explanation set: name, label, MalConv's and the surrogate's log-odds
    report.json             the configuration, the fidelity (R^2, Spearman, sign agreement), and timing

Usage:
    python scripts/audit_surrogate.py --seed 0 --num_threads 32
"""

from __future__ import annotations

from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats

from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import treeshap_interventional
from provexp.models.gbdt import train_gbdt

sys.path.insert(0, str(Path(__file__).parent))
from cm_disagreement_select import load_malconv_predictions  # noqa: E402


__all__ = [
    "fidelity",
]


ROOT = Path(__file__).parent.parent

# The EMBER parameters, as a regressor of MalConv's log-odds (early stopping on the held-out squared error).
REGRESSION: dict[str, Any] = {"objective": "regression", "metric": ["l2"], "is_unbalance": False, "boost_from_average": True}


################################################################################
# Fidelity
################################################################################


def fidelity(target: npt.NDArray[np.float64], predicted: npt.NDArray[np.float64]) -> dict[str, float]:
    """How well the surrogate mimics MalConv: R^2, Spearman's rho, and the share of files with the same sign."""
    if target.shape != predicted.shape or target.ndim != 1:
        raise ValueError(f"Expected two vectors of the same shape. Got {target.shape} and {predicted.shape}.")
    residual = float(np.sum((target - predicted) ** 2))
    total = float(np.sum((target - target.mean()) ** 2))
    return {"r2": 1.0 - residual / total if total > 0 else float("nan"),
            "spearman": float(stats.spearmanr(target, predicted).statistic),
            "sign_agreement": float(np.mean(np.sign(target) == np.sign(predicted)))}


################################################################################
# Driver
################################################################################


def _shap_chunk(model_file: str, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return treeshap_interventional(lgb.Booster(model_file=model_file), X, background)


def main() -> None:
    parser = ArgumentParser(description="Train a surrogate of MalConv on EMBER features and explain it (3-C revised).")
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv's predictions and of the surrogate.")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--predictions", type=Path, default=ROOT / "artifacts" / "checkpoints-predictions")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_surrogate")
    parser.add_argument("--holdout", type=float, default=0.1, help="The share of the training files held out.")
    parser.add_argument("--limit", type=int, default=None, help="Train on at most this many files (for testing).")
    parser.add_argument("--num_explained", type=int, default=None, help="Explain only the first files (for testing).")
    parser.add_argument("--num_threads", type=int, default=os.cpu_count())
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    t_0 = time.time()

    # The test split with MalConv's log-odds; the explanation set (in its saved order) is never trained on.
    X, meta = load_features(args.features, "ts")
    malconv = load_malconv_predictions(args.predictions / f"malconv-seed{args.seed}")
    meta = meta.filter(pl.col("status") == "ok").select("row", "name", "label").join(malconv, on="name", how="inner")
    explained = pl.read_parquet(args.explanations / f"seed-{args.seed}" / "samples.parquet").select("row", "name", "label")
    explained = explained.join(malconv.select("name", "malconv_log_odds"), on="name", how="left", maintain_order="left")
    if explained["malconv_log_odds"].null_count() > 0:
        raise RuntimeError("Some explanation-set files have no MalConv prediction.")
    if args.num_explained is not None:
        explained = explained.head(args.num_explained)
    pool = meta.join(explained.select("name"), on="name", how="anti").sample(fraction=1.0, shuffle=True, seed=args.seed)
    if args.limit is not None:
        pool = pool.head(args.limit)
    n_vl = max(1, int(round(args.holdout * pool.height)))
    vl, tr = pool.head(n_vl), pool.tail(pool.height - n_vl)
    print(f"Surrogate of MalConv (seed {args.seed}): {tr.height} training files, {vl.height} held out, "
          f"{explained.height} explained.", flush=True)

    def rows(df: pl.DataFrame) -> npt.NDArray[np.float32]:
        return np.ascontiguousarray(X[np.sort(df["row"].to_numpy())])

    tr, vl = tr.sort("row"), vl.sort("row")
    booster = train_gbdt(rows(tr), tr["malconv_log_odds"].to_numpy(), rows(vl), vl["malconv_log_odds"].to_numpy(),
                         seed=args.seed, stopper_metric="l2", stopper_mode="min", num_threads=args.num_threads,
                         **REGRESSION)
    model_file = outdir / "model.txt"
    booster.save_model(model_file, num_iteration=booster.best_iteration)
    booster = lgb.Booster(model_file=str(model_file))
    f = gbdt_function(booster)
    seconds_train = time.time() - t_0

    # Fidelity on the held-out files and on the explanation set.
    X_ex = np.asarray(X[explained["row"].to_numpy()], dtype=np.float64)
    surrogate_vl = f(np.asarray(rows(vl), dtype=np.float64))
    surrogate_ex = f(X_ex)
    report: dict[str, object] = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "best_iteration": booster.current_iteration(),
        "num_train": tr.height, "num_holdout": vl.height, "num_explained": explained.height,
        "fidelity_holdout": fidelity(vl["malconv_log_odds"].to_numpy(), surrogate_vl),
        "fidelity_explained": fidelity(explained["malconv_log_odds"].to_numpy(), surrogate_ex),
        "seconds_train": seconds_train,
    }
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2), flush=True)

    # Interventional TreeSHAP on the explanation set, against the shared background (rows of the training split).
    t_1 = time.time()
    background_rows = pl.read_parquet(args.explanations / "background.parquet")["row"].to_numpy()
    X_tr_split, _ = load_features(args.features, "tr")
    background = np.asarray(X_tr_split[np.sort(background_rows)], dtype=np.float64)
    chunks = np.array_split(np.arange(X_ex.shape[0]), max(1, min(args.num_threads, X_ex.shape[0])))
    # NOTE: not forked: LightGBM's OpenMP threads are already running here, and a forked child deadlocks on them.
    with ProcessPoolExecutor(len(chunks)) as pool_:
        parts = list(pool_.map(_shap_chunk, [str(model_file)] * len(chunks), [X_ex[c] for c in chunks],
                               [background] * len(chunks)))
    A = np.concatenate(parts).astype(np.float64)
    completeness = float(np.max(np.abs(A.sum(axis=1) - (surrogate_ex - f(background).mean()))))
    np.save(outdir / "shap.npy", A)
    explained.select("name", "label", "malconv_log_odds").with_columns(
        pl.Series("surrogate_log_odds", surrogate_ex)).write_parquet(outdir / "predictions.parquet")
    report |= {"shap_completeness": completeness, "seconds_shap": time.time() - t_1}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"TreeSHAP: {A.shape}, completeness {completeness:.2e}, {time.time() - t_1:.0f} s. Wrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
