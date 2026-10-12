"""
3-A tables from scripts/cm_check.py: per-budget cross-deletion with paired tests, byte rankings vs. window rankings.

For each scored model and budget, the evidence removed (s · (f(x) − f(deleted)), s the sign of the original log-odds) by
the other model's byte ranking is compared, file by file, with each window ranking of the same model and with random
windows: the median difference, the files on which the byte ranking removes more, and the paired Wilcoxon p-value.

Usage:
    python scripts/cm_tables.py --run artifacts/experiments/cm_check/seed-0
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats


__all__ = [
    "paired",
]


ROOT = Path(__file__).parent.parent
# Per scored model: the other model's byte ranking and the alternatives it is compared with.
COMPARISONS = {
    "malconv": ("gbdt_pullback", ["gbdt_pullback_k256", "gbdt_occlusion_k256", "random"]),
    "gbdt": ("malconv_ig", ["malconv_ig_k256", "malconv_occlusion", "random"]),
}
SHOWN_BUDGETS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05)


def paired(removed: pl.DataFrame, method: str, other: str, budget: float) -> dict[str, float]:
    """The paired comparison of two rankings' evidence removed at one budget, over the files that have both."""
    a = removed.filter((pl.col("method") == method) & (pl.col("budget") == budget)).select("index", pl.col("removed").alias("a"))
    b = removed.filter((pl.col("method") == other) & (pl.col("budget") == budget)).select("index", pl.col("removed").alias("b"))
    j = a.join(b, on="index").drop_nulls().filter(pl.col("a").is_finite() & pl.col("b").is_finite())
    diff = (j["a"] - j["b"]).to_numpy()
    p = float(stats.wilcoxon(diff).pvalue) if np.any(diff != 0) else float("nan")
    return {"n": j.height, "median_a": float(j["a"].median()), "median_b": float(j["b"].median()),  # type: ignore[arg-type]
            "median_diff": float(np.median(diff)), "wins": int((diff > 0).sum()), "p": p}


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--run", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_check" / "seed-0")
    args = parser.parse_args()

    curves = pl.read_parquet(args.run / "curves.parquet").filter(pl.col("valid"))
    files = pl.read_parquet(args.run / "files.parquet").filter(pl.col("status") == "ok")
    curves = curves.join(files.select("index", "gbdt_log_odds", "malconv_log_odds"), on="index")
    # The random orders are averaged per file, so that each file counts once.
    curves = curves.with_columns(pl.when(pl.col("method").str.starts_with("random:")).then(pl.lit("random")).otherwise(pl.col("method")).alias("method"))

    print(f"# 3-A cross-deletion, paired by file ({args.run.as_posix()})\n")
    print("Evidence removed from the scored model by the other model's byte ranking (a) vs. an alternative (b): medians,")
    print("the median paired difference, the files on which a removes more, and the Wilcoxon p-value.\n")
    for scored, (method, others) in COMPARISONS.items():
        log_odds = pl.col(f"{scored}_log_odds")
        removed = curves.with_columns((log_odds.sign() * (log_odds - pl.col(scored))).alias("removed")) \
            .group_by("index", "method", "budget").agg(pl.col("removed").mean())
        print(f"## Scored: {scored}; ranking: {method}\n")
        print("| budget | alternative | n | median a | median b | median a − b | a > b | p |")
        print("|---|---|---|---|---|---|---|---|")
        for budget in SHOWN_BUDGETS:
            for other in others:
                r = paired(removed, method, other, budget)
                print(f"| {budget:.1%} | {other} | {r['n']} | {r['median_a']:.2f} | {r['median_b']:.2f} | {r['median_diff']:.2f} | {r['wins']} | {r['p']:.1e} |")
        print()


if __name__ == "__main__":
    main()
