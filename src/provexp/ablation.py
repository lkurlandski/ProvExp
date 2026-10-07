"""
Problem-space ablation for faithfulness experiments: ablate elements, order elements by an explanation, and estimate
provenance from window occlusion (black-box provenance).

Everything here is domain-agnostic: elements are bytes, and which of them must not be ablated (`protected`) or are
replaced by fixed values instead of the fill (`fixed`) is decided by the caller, e.g.,
provexp.featuresets.ember2024.ablation for PE files.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import Literal
from typing import Optional

import numpy as np
from numpy import typing as npt

from provexp.boxmatrix import BoxMatrix
from provexp.boxmatrix import expand_ranges
from provexp.provenance import Provenance


__all__ = [
    "BUDGETS",
    "Fill",
    "ablate",
    "budget_masks",
    "coarsen",
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
    fixed: Optional[BoolArray] = None,
    fixed_values: Optional[npt.NDArray[np.uint8]] = None,
) -> bytes:
    """
    Replace the selected elements of an input, except the protected ones.

    Args:
        data: The input, m bytes.
        which: The elements to ablate, shape (m,).
        protected: The elements that must never change, shape (m,).
        fill: Replace with zeros or with uniformly random bytes.
        rng: The random generator (required for random fill).
        fixed: Elements that are replaced with `fixed_values` instead of the fill, shape (m,).
        fixed_values: The replacement value of each element, shape (m,); zeros if not given.

    Returns:
        The ablated input.
    """
    m = len(data)
    for mask in (which, protected, fixed, fixed_values):
        if mask is not None and mask.shape != (m,):
            raise ValueError(f"Expected masks and values of shape ({m},).")
    buffer = np.frombuffer(data, dtype=np.uint8).copy()
    target = which & ~protected
    if fill == "zeros":
        buffer[target] = 0
    elif fill == "random":
        if rng is None:
            raise ValueError("Random fill needs a random generator.")
        buffer[target] = rng.integers(0, 256, size=int(target.sum()), dtype=np.uint8)
    else:
        raise ValueError(f"Unknown fill: {fill}")
    if fixed is not None:
        target_fixed = target & fixed
        buffer[target_fixed] = 0 if fixed_values is None else fixed_values[target_fixed]
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
    # NOTE: Features differ in scale by many orders of magnitude, and Provenance treats a column as empty if its sum is
    # tiny relative to the largest column. Each column is normalized here, which does not change P.
    total = delta.sum(axis=0)
    delta = np.divide(delta, total, out=np.zeros_like(delta), where=total > 0)
    lengths = np.diff(edges)
    k, j = np.nonzero(delta)
    C = BoxMatrix((int(edges[-1]), x_.shape[0]))
    C.add_boxes(edges[k], edges[k + 1], j, j + 1, delta[k, j] / lengths[k])
    return Provenance(C, feature_names)


def coarsen(prov: Provenance, edges: IntArray) -> FloatArray:
    """
    The provenance of each feature summed over windows of elements (coarsening, which commutes with pullback).

    Args:
        prov: The provenance over m = edges[-1] elements.
        edges: The window edges, shape (K + 1,).

    Returns:
        The coarsened provenance, shape (K + 1, n): one row per window, then the null element (zero without one).
    """
    m, n = prov.num_elements, prov.num_features
    if edges[0] != 0 or edges[-1] != m:
        raise ValueError(f"Expected window edges from 0 to {m}. Got {edges[0]} to {edges[-1]}.")
    K = edges.shape[0] - 1
    out = np.zeros((K + 1, n), dtype=np.float64)
    pieces = prov.pieces()
    real = pieces.lo < m
    null = ~real
    np.add.at(out[K], pieces.col[null], pieces.val[null])
    col, lo, hi, val = pieces.col[real], pieces.lo[real], np.minimum(pieces.hi[real], m), pieces.val[real]
    first = np.searchsorted(edges, lo, side="right") - 1
    last = np.searchsorted(edges, hi - 1, side="right") - 1
    which, window = expand_ranges(first, last + 1)
    overlap = np.minimum(hi[which], edges[window + 1]) - np.maximum(lo[which], edges[window])
    np.add.at(out, (window, col[which]), val[which] * overlap)
    return out
