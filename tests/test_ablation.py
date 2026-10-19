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
from provexp.ablation import coarsen
from provexp.ablation import coarsen_provenance
from provexp.ablation import coarsen_sparse
from provexp.ablation import element_order
from provexp.ablation import window_order
from provexp.ablation import estimate_provenance
from provexp.ablation import window_edges
from provexp.ablation import window_pushforward
from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

from tests.strategies import boxmatrices


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
        fixed = np.zeros(1000, dtype=np.bool_)
        fixed[:100] = True
        a = ablate(data, which, protected, "random", np.random.default_rng(0), fixed)
        b = ablate(data, which, protected, "random", np.random.default_rng(0), fixed)
        out = np.frombuffer(a, dtype=np.uint8)
        assert a == b
        assert (out[:100] == 0).all()
        assert (out[100:] != 0).mean() > 0.9

    @pytest.mark.parametrize("fill", ["zeros", "random"])
    def test_fixed_values(self, fill: str) -> None:
        data = random_bytes(100)
        which = np.zeros(100, dtype=np.bool_)
        which[:50] = True
        protected = np.zeros(100, dtype=np.bool_)
        protected[0] = True
        fixed = np.zeros(100, dtype=np.bool_)
        fixed[:20] = True
        values = np.full(100, 7, dtype=np.uint8)
        out = np.frombuffer(ablate(data, which, protected, fill, np.random.default_rng(0), fixed, values), dtype=np.uint8)  # type: ignore[arg-type]
        assert out[0] == data[0]
        assert (out[1:20] == 7).all()
        assert (out[50:] == np.frombuffer(data, dtype=np.uint8)[50:]).all()

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


@given(boxmatrices(), st.integers(1, 8), st.sampled_from(["null", "uniform", "ignore"]))
@settings(max_examples=150, deadline=None)
def test_coarsen(C: BoxMatrix, num_windows: int, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    m = prov.num_elements
    edges = window_edges(m, num_windows)
    P = prov.to_dense()
    expected = np.stack([P[lo:hi].sum(axis=0) for lo, hi in zip(edges[:-1], edges[1:])] + [P[m] if prov.has_null else np.zeros(prov.num_features)])
    assert np.allclose(coarsen(prov, edges), expected)


@given(boxmatrices(), st.integers(1, 8), st.sampled_from(["null", "uniform", "ignore"]), st.integers(0, 2 ** 16))
@settings(max_examples=150, deadline=None)
def test_coarsen_provenance(C: BoxMatrix, num_windows: int, empty: str, seed: int) -> None:
    """The provenance over windows is the summed rows, and pullback commutes with coarsening."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    m = prov.num_elements
    edges = window_edges(m, num_windows)
    K = edges.shape[0] - 1
    coarse = coarsen_provenance(prov, edges)
    assert coarse.num_elements == K and coarse.empty == prov.empty
    assert np.allclose(coarse.to_dense()[:K], coarsen(prov, edges)[:K])
    a = np.random.default_rng(seed).normal(size=prov.num_features)
    b = prov.pullback(a)
    expected = np.array([b[lo:hi].sum() for lo, hi in zip(edges[:-1], edges[1:])])
    assert np.allclose(coarse.pullback(a)[:K], expected)
    if prov.has_null:
        assert np.isclose(coarse.pullback(a)[-1], b[-1])


@given(boxmatrices(), st.integers(1, 8), st.sampled_from(["null", "uniform", "ignore"]), st.integers(0, 2 ** 16))
def test_coarsen_sparse_and_window_pushforward(C: BoxMatrix, num_windows: int, empty: str, seed: int) -> None:
    """The sparse coarsening equals the dense one, and the window pushforward is the coarsened provenance's."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    edges = window_edges(prov.num_elements, num_windows)
    K = edges.shape[0] - 1
    assert np.allclose(coarsen_sparse(prov, edges).toarray(), coarsen(prov, edges)[:K])
    b = np.random.default_rng(seed).normal(size=K)
    assert np.allclose(window_pushforward(prov, edges, b), coarsen_provenance(prov, edges).pushforward(b))
    with pytest.raises(ValueError):
        window_pushforward(prov, edges, np.zeros(K + 1))


@given(boxmatrices(), st.integers(1, 8), st.sampled_from(["null", "ignore"]))
@settings(max_examples=150, deadline=None)
def test_coarsening_raises_overlap_and_lowers_ambiguity(C: BoxMatrix, num_windows: int, empty: str) -> None:
    """Merging rows never lowers O_j and never raises H_j (manuscript, Proposition Coarsening)."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    coarse = coarsen_provenance(prov, window_edges(prov.num_elements, num_windows))
    att = prov.included
    assert np.array_equal(coarse.included, att)
    assert np.all(coarse.overlap().per_feature[att] >= prov.overlap().per_feature[att] - 1e-9)
    assert np.all(coarse.ambiguity().per_feature[att] <= prov.ambiguity().per_feature[att] + 1e-9)


def test_coarsen_provenance_to_single_elements() -> None:
    """Windows of one element each leave the provenance unchanged."""
    C = BoxMatrix((5, 3))
    C.add_boxes(0, 3, 0, 1, 1.0)
    C.add_boxes(2, 5, 1, 2, 2.0)
    prov = Provenance(C)
    coarse = coarsen_provenance(prov, window_edges(5, 5))
    assert np.allclose(coarse.to_dense(), prov.to_dense())
    assert np.allclose(coarse.overlap().per_feature, prov.overlap().per_feature)


def test_estimate_provenance_with_heterogeneous_scales() -> None:
    """A feature with tiny changes is not mistaken for an empty one next to a feature with huge changes."""
    edges = window_edges(100, 4)
    x = np.array([1e9, 1e-3, 5.0])
    X = np.array([[0.0, 1e-3 - 1e-6, 5.0], [1e9, 1e-3, 5.0], [1e9, 1e-3 - 3e-6, 5.0], [1e9, 1e-3, 5.0]])
    prov = estimate_provenance(x, X, edges)
    assert prov.is_empty.tolist() == [False, False, True]
    assert np.allclose(coarsen(prov, edges)[:4, 1], [0.25, 0.0, 0.75, 0.0])


class TestTieBreaks:

    def test_a_tiebreak_decides_ties_and_near_ties(self) -> None:
        scores = np.array([0.0, 2.0, 0.0, 2.0 + 1e-15, 1.0])
        assert element_order(scores, tiebreak=np.array([3, 1, 4, 2, 0])).tolist() == [3, 1, 4, 2, 0]
        assert element_order(scores, tiebreak=np.array([1, 3, 0, 2, 4])).tolist() == [1, 3, 4, 0, 2]

    def test_without_a_tiebreak_nothing_changes(self) -> None:
        scores = np.array([0.0, 2.0, -1.0, 2.0, 1.0])
        assert element_order(scores, tiebreak=np.arange(5)).tolist() == element_order(scores).tolist()

    @given(st.integers(1, 60), st.integers(1, 20), st.integers(0, 2 ** 16))
    @settings(max_examples=100, deadline=None)
    def test_window_order_equals_the_repeated_element_order(self, m: int, K: int, seed: int) -> None:
        rng = np.random.default_rng(seed)
        edges = window_edges(m, K)
        scores = rng.integers(-2, 3, size=edges.shape[0] - 1).astype(np.float64)
        window = np.repeat(np.arange(edges.shape[0] - 1), np.diff(edges))
        assert window_order(scores, edges, -1.0).tolist() == element_order(scores[window], -1.0).tolist()

    @given(st.integers(1, 60), st.integers(1, 20), st.integers(0, 2 ** 16))
    @settings(max_examples=100, deadline=None)
    def test_window_order_keeps_windows_whole(self, m: int, K: int, seed: int) -> None:
        rng = np.random.default_rng(seed)
        edges = window_edges(m, K)
        Kw = edges.shape[0] - 1
        order = window_order(np.zeros(Kw), edges, tiebreak=rng.permutation(Kw).astype(np.int64))
        assert sorted(order.tolist()) == list(range(m))
        window = np.repeat(np.arange(Kw), np.diff(edges))[order]
        assert np.count_nonzero(np.diff(window)) == Kw - 1  # each window's elements are contiguous
