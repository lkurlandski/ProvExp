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
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

__all__ = ["MAX_LENGTH", "THRESHOLD_SPLITS", "byte_room", "calibrate_threshold", "detection_at", "model_threshold", "group_evasion", "make_extractor", "parse_defenses",
           "precondition_holds"]


MAX_LENGTH = 4_000_000


def byte_room(size: int, max_size: int = MAX_LENGTH) -> int:
    """
    The bytes an attack may add to a file of `size` bytes: every attack's output may be at most `max_size` bytes.

    The study concerns PE files up to 4 MB (the data's limit; scale-up protocol item (22), user, session 105), which
    replaced the old cap max(5% of the file, 512 KiB).

    Args:
        size: The original file's size in bytes.
        max_size: The largest output that counts.

    Returns:
        max_size - size, or 0 when the file is already that large.
    """
    if max_size < 1:
        raise ValueError(f"max_size must be positive, got {max_size}.")
    return max(0, max_size - size)


def make_extractor(features: Path) -> PEFeatureExtractor:
    """The extractor a feature store was built with (quirk-fixed in every case), checked against its manifest."""
    manifest = load_manifest(features)
    extractor: PEFeatureExtractor
    if manifest["feature_set"] == "ember2024-sums":
        extractor = SumsFeatureExtractor()
    elif manifest["feature_set"] == "ember2024-expert":
        extractor = ExpertFeatureExtractor()
    else:
        extractor = fix_quirks(PEFeatureExtractor())
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


# NOTE: the pilot's models set their thresholds on the test split (ts); the scale-up's on the validation split (vl;
# session 67), whose predictions the trainers write next to the test predictions.
THRESHOLD_SPLITS = ("vl", "ts")


def model_threshold(model_dir: Path, fpr: float, split: str = "ts") -> float:
    """
    A model's threshold at `fpr`, from the goodware of its stored predictions on one split.

    Args:
        model_dir: The model directory, holding `{split}_predictions.parquet` (name, label, prob).
        fpr: The target false-positive rate.
        split: The split the threshold is set on: "vl" (the scale-up) or "ts" (the pilot).

    Returns:
        tau, as calibrate_threshold.
    """
    if split not in THRESHOLD_SPLITS:
        raise ValueError(f"split must be one of {THRESHOLD_SPLITS}, got {split!r}.")
    path = Path(model_dir) / f"{split}_predictions.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path.as_posix()} does not exist; the pilot's models have only ts predictions.")
    pred = pl.read_parquet(path)
    return calibrate_threshold(pred["prob"].to_numpy(), pred["label"].to_numpy(), fpr)


def detection_at(model_dir: Path, fpr: float, split: str = "vl") -> dict[str, float]:
    """
    A model's detection on the test split at the threshold set at `fpr` on `split` (the scale-up: vl).

    Args:
        model_dir: The model directory (ts_predictions.parquet, and `{split}_predictions.parquet`).
        fpr: The target false-positive rate.
        split: The split the threshold is set on.

    Returns:
        tau, the share of test malware with p > tau (tpr), and the share of test goodware with p > tau (fpr_ts).
    """
    tau = model_threshold(model_dir, fpr, split)
    pred = pl.read_parquet(Path(model_dir) / "ts_predictions.parquet")
    p, y = pred["prob"].to_numpy(), pred["label"].to_numpy()
    return {"tau": tau, "tpr": float(np.mean(p[y == 1] > tau)), "fpr_ts": float(np.mean(p[y == 0] > tau))}


def group_evasion(rows: pl.DataFrame, attacks: list[str]) -> dict[str, Any]:
    """The fraction of attacked (detected) files that at least one attack of `attacks` evaded, within budget."""
    g = rows.filter(pl.col("attack").is_in(attacks))
    if g.height == 0:
        return {"files": 0, "evaded": 0, "rate": None}
    per_file = g.group_by("name").agg(pl.col("evaded").any())
    n, e = per_file.height, int(per_file["evaded"].sum())
    return {"files": n, "evaded": e, "rate": e / n}


_PRECONDITION_EXTRACTOR = fix_quirks(PEFeatureExtractor())


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
