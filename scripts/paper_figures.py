"""
Data files for the manuscript's pgfplots figures, written to `manuscript/assets/data/`.

    pf_malconv.dat   the pushforward on MalConv (Section 5.1; run 58): per deletion budget, the median MalConv
                     evidence removed by each ranking, over the files with every deletion verified

Usage:
    python scripts/paper_figures.py
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import polars as pl


__all__ = [
    "pf_malconv_curves",
]


ROOT = Path(__file__).parent.parent
METHODS = ("pushforward", "surrogate", "ig_k256", "random_feat", "random")


################################################################################
# Pushforward on MalConv
################################################################################


def pf_malconv_curves(run: Path) -> pl.DataFrame:
    """
    The median MalConv evidence removed per (budget, ranking), as `summarize` in scripts/pf_malconv.py prints it.

    Args:
        run: A scripts/pf_malconv.py output directory.

    Returns:
        One row per budget (budgets up to 50%), one column per ranking in METHODS.
    """
    curves = pl.read_parquet(run / "curves.parquet")
    files = pl.read_parquet(run / "files.parquet").filter(pl.col("status") == "ok")
    c = curves.join(files.select("index", pl.col("malconv_log_odds").alias("m0")), on="index").filter(pl.col("budget") <= 0.5)
    c = c.with_columns((pl.col("m0").sign() * (pl.col("m0") - pl.col("malconv"))).alias("removed"),
                       pl.col("method").str.replace(r":\d+$", "").alias("method"))
    valid = c.group_by("index").agg(pl.col("valid").all()).filter(pl.col("valid"))["index"]
    c = c.filter(pl.col("index").is_in(valid.implode()))
    per_file = c.group_by("index", "method", "budget").agg(pl.col("removed").mean())
    table = per_file.group_by("method", "budget").agg(pl.col("removed").median())
    wide = table.pivot(on="method", index="budget", values="removed").sort("budget")
    missing = [m for m in METHODS if m not in wide.columns]
    if missing:
        raise RuntimeError(f"The run has no rankings {missing}.")
    return wide.select("budget", *METHODS).with_columns(pl.col("budget") * 100)


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Write the data files of the manuscript's figures.")
    parser.add_argument("--pf_malconv", type=Path, default=ROOT / "artifacts" / "experiments" / "pf_malconv" / "seed-0")
    parser.add_argument("--outdir", type=Path, default=ROOT / "manuscript" / "assets" / "data")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    pf = pf_malconv_curves(args.pf_malconv)
    pf.write_csv(args.outdir / "pf_malconv.dat", separator=" ", float_precision=4)
    print(pf)


if __name__ == "__main__":
    main()
