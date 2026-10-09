"""
CP.3 (docs/cp_plan.md): do the statistics of P track P? The instrumented and the black-box provenance, both coarsened
to the K windows of a faithfulness.py run, compared per subset through their statistics.

T1 says the two agree for features additive in their elements and differ for non-additive ones; the total variation
between the columns (already reported in docs/pb1_pilot.md) measures that directly. This compares what the statistics
say about each:
    ambiguity           a property of one column, so where the columns agree (total variation 0) it must agree too
    overlap             1 - M_jj depends on the row sums D, i.e., on every other feature reading the same windows, so
                        it can differ even for a feature whose own column agrees, when the features around it differ

Per subset, over the features attributable under both and over files: the median total variation, the median
effective support exp(H_j) (in windows) and overlap O_j under each, and the share of (file, feature) pairs whose
statistic agrees (to 1e-4; they are saved as float32).

Input: `provenance.npz` of a faithfulness.py run made after 2026-10-08, which saves `overlap_{instrumented,blackbox}`
and `ambiguity_{instrumented,blackbox}` (earlier runs saved only `tv`, `attributable`, `estimated`).

Usage:
    python scripts/cp_blackbox.py --run artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
"""

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
from numpy import typing as npt
import polars as pl

from provexp.featuresets.ember2024.features import PEFeatureExtractor


TOLERANCE = 1e-4  # NOTE: the statistics are saved as float32, so agreement is judged to 1e-4, not to round-off.


def markdown(df: pl.DataFrame, digits: int = 3) -> str:
    def fmt(v: object) -> str:
        return f"{v:.{digits}g}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def compare(stats: dict[str, npt.NDArray[np.floating]], subsets: npt.NDArray[np.str_]) -> pl.DataFrame:
    """
    The comparison table, one row per subset and one for all features.

    Args:
        stats: The arrays of provenance.npz, each of shape (files, features).
        subsets: The subset of each feature, shape (features,).
    """
    for key in ("overlap_instrumented", "overlap_blackbox", "ambiguity_instrumented", "ambiguity_blackbox"):
        if key not in stats:
            raise ValueError(f"provenance.npz has no {key}: the run predates the window-level statistics.")
    both = stats["attributable"].astype(np.bool_) & stats["estimated"].astype(np.bool_)
    rows = []
    for subset in ["all", *dict.fromkeys(subsets.tolist())]:
        cols = np.ones(subsets.shape[0], dtype=np.bool_) if subset == "all" else subsets == subset
        sel = both & cols[None, :]
        if not sel.any():
            continue
        tv = stats["tv"][sel]
        Hi, Hb = stats["ambiguity_instrumented"][sel], stats["ambiguity_blackbox"][sel]
        Oi, Ob = stats["overlap_instrumented"][sel], stats["overlap_blackbox"][sel]
        rows.append({
            "subset": subset,
            "pairs": int(sel.sum()),
            "median tv": float(np.nanmedian(tv)),
            "support: instrumented": float(np.median(np.exp(Hi))),
            "support: black-box": float(np.median(np.exp(Hb))),
            "ambiguity agrees": float(np.mean(np.abs(Hi - Hb) <= TOLERANCE)),
            "overlap: instrumented": float(np.median(Oi)),
            "overlap: black-box": float(np.median(Ob)),
            "overlap agrees": float(np.mean(np.abs(Oi - Ob) <= TOLERANCE)),
            "overlap agrees where tv = 0": float(np.mean(np.abs(Oi - Ob)[tv <= TOLERANCE] <= TOLERANCE)) if np.any(tv <= TOLERANCE) else float("nan"),
        })
    return pl.DataFrame(rows)


def main() -> None:
    parser = ArgumentParser(description="CP.3: instrumented vs. black-box provenance through their statistics.")
    parser.add_argument("--run", type=Path, required=True, help="A faithfulness.py output directory.")
    args = parser.parse_args()

    with np.load(args.run / "provenance.npz") as archive:
        stats = {key: archive[key] for key in archive.files}
    names = PEFeatureExtractor().feature_names
    subsets = np.array([n.split(":", 1)[0] for n in names])
    if stats["tv"].shape[1] != subsets.shape[0]:
        raise RuntimeError(f"provenance.npz has {stats['tv'].shape[1]} features, the extractor {subsets.shape[0]}.")
    print(f"CP.3 on {args.run.as_posix()}: {stats['tv'].shape[0]} files, window level.\n")
    print(markdown(compare(stats, subsets)))


if __name__ == "__main__":
    main()
