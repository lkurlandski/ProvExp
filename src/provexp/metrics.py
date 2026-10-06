"""
Binary classification metrics.
"""

from __future__ import annotations

import numpy as np
from numpy import typing as npt
from sklearn import metrics as skmetrics


__all__ = [
    "compute_metrics",
]


def compute_metrics(labels: npt.NDArray[np.integer], probs: npt.NDArray[np.floating], threshold: float = 0.5) -> dict[str, float]:
    """
    Compute binary classification metrics.

    Args:
        labels: The ground truth labels, shape (N,).
        probs: The predicted probability of the positive class, shape (N,).
        threshold: The decision threshold.

    Returns:
        A dictionary of metric names and values.
    """
    preds = (probs >= threshold).astype(np.int64)
    return {
        "acc": float(skmetrics.accuracy_score(labels, preds)),
        "pre": float(skmetrics.precision_score(labels, preds)),
        "rec": float(skmetrics.recall_score(labels, preds)),
        "f-1": float(skmetrics.f1_score(labels, preds)),
        "roc": float(skmetrics.roc_auc_score(labels, probs)),
        "prc": float(skmetrics.average_precision_score(labels, probs)),
        "nll": float(skmetrics.log_loss(labels, np.clip(probs, 1e-7, 1 - 1e-7))),
    }
