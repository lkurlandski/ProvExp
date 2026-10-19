"""
Appendix C, "Checking the Exact Pullback": verify Proposition Exact Pullback in the setting it covers, a linear model
over the additive features.

For such a model the whole pipeline's Shapley value for a byte has a closed form (the model's score is a weighted sum
of per-feature games that are each additive over the feature's items): byte z_i receives sum_j beta_j times its
recorded contribution to feature x_j, i.e., (C beta)_i, where C is the raw-contributions matrix P is built from. We
check that this equals the pullback of the model's feature-space Shapley values a_j = beta_j * Delta_j (Delta_j the
feature's change from the no-items baseline, which the provenance stores as its column sum). The two are computed by
different code paths (the raw BoxMatrix versus Provenance.pullback, which normalizes the columns and then applies
them), so agreeing to numerical precision confirms the construction realizes the proposition: a correct normalization,
the null element, and the item-to-byte mapping. It needs no sampling and runs on every file.

Also reported, as the Shapley efficiency of the whole pipeline: the pulled-back attribution sums to the model's score
change from the all-empty feature vector, sum_i b_i = beta . Delta.

NOTE: the data-flow cost of Appendix C's second paragraph (how far the data-flow convention for the non-additive
features departs from their true Shapley provenance) is NOT computed here. It needs a faithful recomputation of each
non-additive feature (byte entropy, string statistics) from subsets of its items, which the extractor does not expose
per-subset; it is a separate, sampling-based measurement (see docs/plan-2026-10-19.md, Phase 4).

Outputs, in `{outdir}/`:
    files.parquet   one row per file: the max and l1 pullback-vs-direct difference, the attribution scale, the
                    efficiency residual
    report.json     the configuration, the number of additive features, and the aggregate errors

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=2 python scripts/exact_pullback_check.py --num_files 0
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm

from provexp.data.tabular import load_features
from provexp.featuresets.ember2024.features import PEFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from theory_coverage import is_data_flow  # noqa: E402


__all__ = [
    "train_additive_model",
]


ROOT = Path(__file__).parent.parent
FloatArray = npt.NDArray[np.float64]


def train_additive_model(features: Path, additive: npt.NDArray[np.bool_], C: float, max_iter: int, seed: int, sample: int) -> FloatArray:
    """
    A logistic regression on the additive feature columns of the training split. The malware log-odds it predicts is
    linear in those features; its coefficient vector, zero on the non-additive columns, is returned over all features.
    The check holds for any linear model, so training on a random subsample of rows (sample > 0) is enough and keeps
    this light.

    Returns:
        The coefficient vector beta, shape (num_features,), with beta_j = 0 for non-additive j.
    """
    X, meta = load_features(features, "tr")
    y = meta["label"].to_numpy()
    if 0 < sample < X.shape[0]:
        idx = np.sort(np.random.default_rng(seed).choice(X.shape[0], sample, replace=False))
        Xa, y = np.asarray(X[idx][:, additive], dtype=np.float64), y[idx]
    else:
        Xa = np.asarray(X[:, additive], dtype=np.float64)
    # Standardize for a well-conditioned fit (EMBER features span many scales), then fold the scaling back so the model
    # is linear in the raw features: log-odds = sum_j (coef_j / std_j) * x_j + const. The constant does not affect the
    # Shapley attributions. The provenance is unchanged; only beta matters for the check.
    mean, std = Xa.mean(axis=0), Xa.std(axis=0)
    std_safe = np.where(std > 0, std, 1.0)
    model = LogisticRegression(C=C, max_iter=max_iter, random_state=seed)
    model.fit((Xa - mean) / std_safe, y)
    beta = np.zeros(X.shape[1], dtype=np.float64)
    beta[additive] = np.where(std > 0, model.coef_[0] / std_safe, 0.0)  # coefficients on the raw features.
    return beta


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--num_files", type=int, default=0, help="Files from the explanation set (0: all).")
    parser.add_argument("--C", type=float, default=1.0, help="Inverse regularization of the logistic regression.")
    parser.add_argument("--max_iter", type=int, default=1000)
    parser.add_argument("--train_sample", type=int, default=50000, help="Random training rows for the logistic regression (0: all); the check holds for any linear model.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "exact_pullback")
    args = parser.parse_args()
    if "PYTHONHASHSEED" not in __import__("os").environ:
        print("WARNING: run with PYTHONHASHSEED=0 so the features match the feature store.", flush=True)

    extractor = PEFeatureExtractor()
    names = extractor.feature_names
    additive = ~is_data_flow(names)
    beta = train_additive_model(args.features, additive, args.C, args.max_iter, args.seed, args.train_sample)
    print(f"Linear model over {int(additive.sum())} additive features (of {len(names)}); "
          f"||beta|| = {np.linalg.norm(beta):.3f}.", flush=True)

    files = pl.read_parquet(args.explanation_set).filter(pl.col("status") == "ok").sort("name")
    if args.num_files > 0:
        files = files.head(args.num_files)

    rows: list[dict[str, Any]] = []
    t_0 = time.time()
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="files", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        m = len(data)
        _, prov = extractor.feature_vector_with_provenance(data)
        delta = prov.colsum  # Delta_j = v_j(z) - v_j(empty), which the provenance stores as the column sum.
        a = beta * delta
        b_pullback = prov.pullback(a)
        b_direct = prov.contributions.matvec(beta)  # (C beta)_i over the m bytes; the closed-form pipeline Shapley.
        diff = np.abs(b_pullback[:m] - b_direct)
        scale = float(np.abs(b_direct).sum())
        # Efficiency: the pulled-back attribution (bytes + null) sums to the model's score change from the empty vector.
        efficiency_residual = float(abs(b_pullback.sum() - a.sum()))
        rows.append({"name": r["name"], "size": m, "max_diff": float(diff.max(initial=0.0)),
                     "l1_diff": float(diff.sum()), "scale": scale,
                     "rel_l1": float(diff.sum() / scale) if scale > 0 else 0.0,
                     "efficiency_residual": efficiency_residual})
    seconds = time.time() - t_0

    df = pl.DataFrame(rows)
    args.outdir.mkdir(parents=True, exist_ok=True)
    df.write_parquet(args.outdir / "files.parquet")
    report = {
        "num_files": df.height, "num_additive": int(additive.sum()), "num_features": len(names),
        "C": args.C, "max_iter": args.max_iter, "seed": args.seed, "seconds": seconds,
        "max_diff": float(df["max_diff"].max() if df.height else 0.0),  # type: ignore[arg-type]
        "median_rel_l1": float(df["rel_l1"].median() if df.height else 0.0),  # type: ignore[arg-type]
        "max_efficiency_residual": float(df["efficiency_residual"].max() if df.height else 0.0),  # type: ignore[arg-type]
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    verdict = "exact (<=1e-9)" if report["max_diff"] <= 1e-9 else f"NONZERO: max {report['max_diff']:.2e}"
    print(f"Pullback vs. closed-form pipeline Shapley: {verdict} over {df.height} files.", flush=True)


if __name__ == "__main__":
    main()
