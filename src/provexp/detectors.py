"""
Loading and calibrating detectors: the extractor of a feature store, thresholds at a false-positive rate, the
precondition, evasion by group, and detector specs on the command line.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.expert import ExpertFeatureExtractor
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

__all__ = ["MAX_LENGTH", "calibrate_threshold", "group_evasion", "make_extractor", "parse_defenses",
           "precondition_holds"]


MAX_LENGTH = 4_000_000


def make_extractor(features: Path) -> PEFeatureExtractor:
    """The extractor a feature store was built with (quirk-fixed in every case), checked against its manifest."""
    manifest = load_manifest(features)
    extractor: PEFeatureExtractor
    if manifest["feature_set"] == "ember2024-sums":
        extractor = SumsFeatureExtractor()
    elif manifest["feature_set"] == "ember2024-expert":
        extractor = ExpertFeatureExtractor()
    else:
        extractor = merge_import_descriptors(PEFeatureExtractor())
    if extractor.feature_names != manifest["feature_names"]:
        raise RuntimeError(f"The extractor does not match the feature names of {features.as_posix()}.")
    return extractor


def calibrate_threshold(probs: np.ndarray, labels: np.ndarray, fpr: float) -> float:
    """
    The threshold tau at which p > tau flags at most `fpr` of the goodware.

    Args:
        probs: Predicted malware probabilities on the test split.
        labels: Their labels (0 goodware, 1 malware).
        fpr: The target false-positive rate.

    Returns:
        tau, the (1 - fpr) order statistic of the goodware probabilities.
    """
    good = np.sort(probs[labels == 0])[::-1]
    if good.size == 0:
        raise ValueError("No goodware to calibrate on.")
    return float(good[min(int(fpr * good.size), good.size - 1)])


def group_evasion(rows: pl.DataFrame, attacks: list[str]) -> dict[str, Any]:
    """The fraction of attacked (detected) files that at least one attack of `attacks` evaded, within budget."""
    g = rows.filter(pl.col("attack").is_in(attacks))
    if g.height == 0:
        return {"files": 0, "evaded": 0, "rate": None}
    per_file = g.group_by("name").agg(pl.col("evaded").any())
    n, e = per_file.height, int(per_file["evaded"].sum())
    return {"files": n, "evaded": e, "rate": e / n}


_PRECONDITION_EXTRACTOR = merge_import_descriptors(PEFeatureExtractor())


def precondition_holds(bytez: bytes) -> bool:
    """The precondition row's check on a file (with the thrember extractor's item table)."""
    return passes_precondition(_PRECONDITION_EXTRACTOR, bytez)


def parse_defenses(specs: list[str]) -> dict[str, Path]:
    """`name=model_dir` pairs, in order."""
    out: dict[str, Path] = {}
    for spec in specs:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise ValueError(f"Expected name=model_dir, got {spec!r}.")
        out[name] = Path(path)
    return out
