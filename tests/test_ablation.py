"""
Tests for ablation.py.
"""

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import pytest

from provexp.ablation import ablate
from provexp.ablation import budget_masks
from provexp.ablation import element_order
from provexp.ablation import estimate_provenance
from provexp.ablation import window_edges
from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance


def random_bytes(m: int, seed: int = 0) -> bytes:
    return np.random.default_rng(seed).integers(1, 256, size=m, dtype=np.uint8).tobytes()


################################################################################
# Ablation
################################################################################


class TestAblate:

    def test_zeros_respect_protection(self) -> None:
        data = random_bytes(100)
        which = np.zeros(100, dtype=np.bool_)
        which[10:60] = True
        protected = np.zeros(100, dtype=np.bool_)
        protected[20:30] = True
        out = np.frombuffer(ablate(data, which, protected), dtype=np.uint8)
        original = np.frombuffer(data, dtype=np.uint8)
        assert (out[10:20] == 0).all() and (out[30:60] == 0).all()
        assert (out[20:30] == original[20:30]).all()
        assert (out[:10] == original[:10]).all() and (out[60:] == original[60:]).all()

    def test_random_fill(self) -> None:
        data = bytes(1000)
        which = np.ones(1000, dtype=np.bool_)
        protected = np.zeros(1000, dtype=np.bool_)
        zero_only = np.zeros(1000, dtype=np.bool_)
        zero_only[:100] = True
        a = ablate(data, which, protected, "random", np.random.default_rng(0), zero_only)
        b = ablate(data, which, protected, "random", np.random.default_rng(0), zero_only)
        out = np.frombuffer(a, dtype=np.uint8)
        assert a == b
        assert (out[:100] == 0).all()
        assert (out[100:] != 0).mean() > 0.9

    def test_invalid(self) -> None:
        mask = np.zeros(4, dtype=np.bool_)
        with pytest.raises(ValueError):
            ablate(bytes(5), mask, mask)
        with pytest.raises(ValueError):
            ablate(bytes(4), mask, mask, "random")
        with pytest.raises(ValueError):
            ablate(bytes(4), mask, mask, "ones")  # type: ignore[arg-type]


################################################################################
# Orders and Budgets
################################################################################


def test_element_order() -> None:
    scores = np.array([0.0, 2.0, -1.0, 2.0, 1.0])
    assert element_order(scores).tolist() == [1, 3, 4, 0, 2]
    assert element_order(scores, direction=-3.0).tolist() == [2, 0, 4, 1, 3]


@given(st.integers(1, 200), st.integers(0, 2 ** 16))
@settings(max_examples=100, deadline=None)
def test_budget_masks(m: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    order = rng.permutation(m).astype(np.int64)
    protected = rng.random(m) < 0.2
    masks = budget_masks(order, protected, (0.0, 0.1, 0.5, 1.0))
    n = int((~protected).sum())
    assert [int(mask.sum()) for mask in masks] == [int(np.ceil(f * n)) for f in (0.0, 0.1, 0.5, 1.0)]
    for mask in masks:
        assert not (mask & protected).any()
    for small, large in zip(masks, masks[1:]):
        assert not (small & ~large).any()
    # The ablated elements are the first unprotected elements of the order.
    ablatable = order[~protected[order]]
    k = int(masks[2].sum())
    assert set(np.flatnonzero(masks[2]).tolist()) == set(ablatable[:k].tolist())


def test_budget_masks_invalid() -> None:
    with pytest.raises(ValueError):
        budget_masks(np.arange(3), np.zeros(3, dtype=np.bool_), (1.5,))


@pytest.mark.parametrize("m,k", [(1000, 256), (10, 256), (256, 256), (1, 4), (0, 4)])
def test_window_edges(m: int, k: int) -> None:
    edges = window_edges(m, k)
    assert edges[0] == 0 and edges[-1] == m
    assert np.all(np.diff(edges) > 0) or m == 0
    assert len(edges) - 1 == min(k, max(m, 1)) or m == 0
    if m >= k:
        assert np.diff(edges).max() - np.diff(edges).min() <= 1


################################################################################
# Black-Box Provenance
################################################################################


def histogram(data: np.ndarray) -> np.ndarray:
    return np.bincount(data, minlength=256).astype(np.float64)


def test_estimate_provenance_is_exact_for_counts() -> None:
    """
    For a byte histogram, zero-occluding window k lowers bin v by the number of v-bytes in the window (v > 0), so the
    estimate coarsened to windows equals the instrumented provenance coarsened to windows, except in the bin of the
    fill value.
    """
    rng = np.random.default_rng(0)
    data = rng.integers(0, 16, size=1000).astype(np.uint8)
    edges = window_edges(1000, 10)
    x = histogram(data)
    X = np.stack([histogram(np.concatenate([data[:lo], np.zeros(hi - lo, dtype=np.uint8), data[hi:]])) for lo, hi in zip(edges[:-1], edges[1:])])
    estimated = estimate_provenance(x, X, edges)

    C = BoxMatrix((1000, 256))
    C.add_keyed_boxes(0, 1000, 0, C.add_key(data))
    instrumented = Provenance(C)

    a = rng.normal(size=256)
    a[0] = 0.0
    window = np.repeat(np.arange(10), np.diff(edges))

    def coarse(b: np.ndarray) -> np.ndarray:
        return np.bincount(window, weights=b[:1000], minlength=10)

    assert np.allclose(coarse(estimated.pullback(a)), coarse(instrumented.pullback(a)))
    assert estimated.is_empty[16:].all() and not estimated.is_empty[1:16].any()


def test_estimate_provenance_shape() -> None:
    with pytest.raises(ValueError):
        estimate_provenance(np.zeros(3), np.zeros((2, 3)), np.array([0, 5, 10, 20]))
