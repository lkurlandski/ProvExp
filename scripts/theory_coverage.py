"""
How much of the GBDT's attribution lies on features whose provenance is exactly their Shapley provenance?

Proposition Additive Features (manuscript, Section 3.3) makes instrumentation exact for features additive over their
items: fields, counts, histograms, and hashed counts. Entropies, averages, ratios, minima, and maxima follow the
data-flow convention instead (Table 1). This script splits each explained file's attribution |a_j| into three parts:

    additive      attributable features of an additive kind (provenance = Shapley provenance)
    data-flow     attributable features of a non-additive kind (provenance = the data-flow convention)
    null          unattributable features, which the pullback hands to the null element

The kind of each feature follows the manuscript's Table 1 and is set by its name (`DATA_FLOW` below); whether a
feature is attributable in a file comes from the provenance census (`attributable.npy`, scripts/provenance_census.py).

Usage:
    python scripts/theory_coverage.py --seed 0
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import re

import numpy as np
from numpy import typing as npt
import polars as pl

from provexp.featuresets.ember2024.features import PEFeatureExtractor


__all__ = [
    "DATA_FLOW",
    "is_data_flow",
]


ROOT = Path(__file__).parent.parent
EXPLAINERS = ("treeshap_interventional", "treeshap_path", "kernelshap_gbdt")
# The non-additive features of EMBER v3 (manuscript, Table 1): entropies, averages, ratios of item-dependent quantities,
# minima, and maxima. Everything else is a field, a count, a histogram, or a hashed count.
DATA_FLOW = (
    r"^general:entropy$",
    r"^byteentropy:",
    r"^strings:(avlength|entropy)$",
    r"^section:(max|min)_(entropy|size_ratio|vsize_ratio)$",
    r"^section:entropy_hash_\d+$",
    r"^section:overlay_(entropy|size_ratio)$",
    r"^authenticode:chain_max_depth$",
)


def is_data_flow(names: list[str]) -> npt.NDArray[np.bool_]:
    """Whether each feature follows the data-flow convention rather than its Shapley provenance."""
    pattern = re.compile("|".join(DATA_FLOW))
    return np.array([pattern.search(n) is not None for n in names])


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    args = parser.parse_args()

    names = PEFeatureExtractor().feature_names
    flow = is_data_flow(names)
    rundir = args.explanations / f"seed-{args.seed}"
    attributable = np.load(rundir / "census" / "attributable.npy")
    ok = attributable.any(axis=1)

    print(f"# Attribution by provenance kind (seed {args.seed}, {int(ok.sum())} files)\n")
    print(f"Data-flow features: {int(flow.sum())} of {len(names)}.\n")
    print("Share of |attribution|: pooled over files, and the median per file.\n")
    print("| explainer | additive | data-flow | null | additive (median) | data-flow (median) | null (median) |")
    print("|---|---|---|---|---|---|---|")
    for explainer in EXPLAINERS:
        a = np.abs(np.load(rundir / f"{explainer}.npy"))
        rows = ok & np.isfinite(a).all(axis=1)
        a, att = a[rows], attributable[rows]
        parts = np.stack([
            (a * (att & ~flow)).sum(axis=1),
            (a * (att & flow)).sum(axis=1),
            (a * ~att).sum(axis=1),
        ], axis=1)
        total = parts.sum(axis=1, keepdims=True)
        pooled = parts.sum(axis=0) / total.sum()
        median = np.median(parts / np.where(total > 0, total, 1.0), axis=0)
        print(f"| {explainer} ({int(rows.sum())}) | " + " | ".join(f"{v:.1%}" for v in pooled) + " | "
              + " | ".join(f"{v:.1%}" for v in median) + " |")

    # Which data-flow groups carry the attribution, for the text.
    a = np.abs(np.load(rundir / "treeshap_interventional.npy"))
    rows = ok & np.isfinite(a).all(axis=1)
    by_feature = pl.DataFrame({"name": names, "share": (a[rows] * attributable[rows]).sum(axis=0) / a[rows].sum(), "flow": flow})
    by_group = by_feature.filter(pl.col("flow")).with_columns(pl.col("name").str.replace(r"_\d+$", "_#").str.replace(r"_nibble_.*$", "")) \
        .group_by("name").agg(pl.col("share").sum()).sort("share", descending=True)
    print("\nData-flow groups by their share of interventional TreeSHAP's |attribution| (pooled):\n")
    for r in by_group.head(10).iter_rows(named=True):
        print(f"- {r['name']}: {r['share']:.1%}")


if __name__ == "__main__":
    main()
