"""
Problem-space ablation for faithfulness experiments: ablate elements, order elements by an explanation, and estimate
provenance from window occlusion (black-box provenance).

Everything here is domain-agnostic: elements are bytes, and which of them must not be ablated (`protected`) or may only
be zeroed (`zero_only`) is decided by the caller, e.g., provexp.featuresets.ember2024.ablation for PE files.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import Literal
from typing import Optional

import numpy as np
from numpy import typing as npt

from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance


__all__ = [
    "BUDGETS",
    "Fill",
    "ablate",
    "budget_masks",
    "element_order",
    "estimate_provenance",
    "window_edges",
]


Fill = Literal["zeros", "random"]

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

# Fractions of the ablatable elements, log-spaced because evidence is concentrated in small parts of the input.
BUDGETS: tuple[float, ...] = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0)


################################################################################
# Ablation
################################################################################


def ablate(
    data: bytes,
    which: BoolArray,
    protected: BoolArray,
    fill: Fill = "zeros",
    rng: Optional[np.random.Generator] = None,
    zero_only: Optional[BoolArray] = None,
) -> bytes:
    """
    Replace the selected elements of an input, except the protected ones.

    Args:
        data: The input, m bytes.
        which: The elements to ablate, shape (m,).
        protected: The elements that must never change, shape (m,).
        fill: Replace with zeros or with uniformly random bytes.
        rng: The random generator (required for random fill).
        zero_only: Elements that are always replaced with zeros, even with random fill, shape (m,).

    Returns:
        The ablated input.
    """
    m = len(data)
    if which.shape != (m,) or protected.shape != (m,) or (zero_only is not None and zero_only.shape != (m,)):
        raise ValueError(f"Expected masks of shape ({m},).")
    buffer = np.frombuffer(data, dtype=np.uint8).copy()
    target = which & ~protected
    if fill == "zeros":
        buffer[target] = 0
    elif fill == "random":
        if rng is None:
            raise ValueError("Random fill needs a random generator.")
        values = rng.integers(0, 256, size=int(target.sum()), dtype=np.uint8)
        if zero_only is not None:
            values[zero_only[target]] = 0
        buffer[target] = values
    else:
        raise ValueError(f"Unknown fill: {fill}")
    return buffer.tobytes()


################################################################################
# Orders and Budgets
################################################################################


def element_order(scores: npt.ArrayLike, direction: float = 1.0) -> IntArray:
    """
    The elements ordered by decreasing `direction * scores`; ties keep their input order.

    Args:
        scores: A score per element, shape (m,), e.g., a pulled-back explanation without its null element.
        direction: The sign of the evidence to rank first, e.g., the sign of the model's log-odds.
    """
    s = np.asarray(scores, dtype=np.float64)
    if s.ndim != 1:
        raise ValueError(f"Expected one score per element. Got shape {s.shape}.")
    return np.argsort(-np.sign(direction) * s, kind="stable").astype(np.int64)


def budget_masks(order: IntArray, protected: BoolArray, budgets: Sequence[float] = BUDGETS) -> list[BoolArray]:
    """
    The elements to ablate at each budget: the first ⌈f · n⌉ unprotected elements of `order`, where n is the number of
    unprotected elements. The masks are nested.
    """
    if any(not 0 <= f <= 1 for f in budgets):
        raise ValueError(f"Budgets must be fractions in [0, 1]. Got {list(budgets)}.")
    ablatable = order[~protected[order]]
    n = ablatable.shape[0]
    masks = []
    for f in budgets:
        mask = np.zeros(protected.shape[0], dtype=np.bool_)
        mask[ablatable[:int(np.ceil(f * n))]] = True
        masks.append(mask)
    return masks


def window_edges(m: int, num_windows: int) -> IntArray:
    """The edges of `num_windows` (or m, if fewer elements) contiguous windows of nearly equal size, shape (K + 1,)."""
    if m < 0 or num_windows < 1:
        raise ValueError(f"Invalid number of elements ({m}) or windows ({num_windows}).")
    return np.unique(np.linspace(0, m, min(num_windows, max(m, 1)) + 1).round().astype(np.int64))


################################################################################
# Black-Box Provenance
################################################################################


def estimate_provenance(
    x: npt.ArrayLike,
    X_occluded: npt.ArrayLike,
    edges: IntArray,
    feature_names: Optional[Sequence[str]] = None,
) -> Provenance:
    """
    Estimate provenance from window occlusion: the provenance of feature j on window k is proportional to how much
    occluding the window changes the feature, |x_j - x_j^(k)|, spread evenly over the window's elements.

    This treats the feature mapping as a black box, needs one evaluation per window, and is exact at the window level
    for features that are additive in their elements' contributions (e.g., counts), up to the fill value's own
    contribution. Features that no occlusion changes are empty (the null element).

    Args:
        x: The features of the input, shape (d,).
        X_occluded: The features with each window occluded, shape (K, d).
        edges: The window edges, shape (K + 1,).
        feature_names: Optionally, the name of each feature.

    Returns:
        The estimated provenance over the m = edges[-1] elements.
    """
    x_ = np.asarray(x, dtype=np.float64)
    X = np.asarray(X_occluded, dtype=np.float64)
    K = edges.shape[0] - 1
    if X.shape != (K, x_.shape[0]):
        raise ValueError(f"Expected occluded features of shape ({K}, {x_.shape[0]}). Got {X.shape}.")
    delta = np.abs(X - x_[None, :])
    delta[~np.isfinite(delta)] = 0.0
    lengths = np.diff(edges)
    k, j = np.nonzero(delta)
    C = BoxMatrix((int(edges[-1]), x_.shape[0]))
    C.add_boxes(edges[k], edges[k + 1], j, j + 1, delta[k, j] / lengths[k])
    return Provenance(C, feature_names)
