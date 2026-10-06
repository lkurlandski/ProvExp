"""
Tests for boxmatrix.py.
"""

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import pytest

from provexp.boxmatrix import BoxMatrix
from provexp.boxmatrix import expand_ranges

from tests.strategies import boxmatrices


################################################################################
# Utilities
################################################################################


@pytest.mark.parametrize(
    "lo, hi, which, value",
    [
        ([], [], [], []),
        ([3], [3], [], []),
        ([0], [3], [0, 0, 0], [0, 1, 2]),
        ([5, 0, 2], [7, 1, 2], [0, 0, 1], [5, 6, 0]),
    ],
)
def test_expand_ranges(lo: list[int], hi: list[int], which: list[int], value: list[int]) -> None:
    which_, value_ = expand_ranges(np.array(lo, dtype=np.int64), np.array(hi, dtype=np.int64))
    assert which_.tolist() == which
    assert value_.tolist() == value


def test_expand_ranges_invalid() -> None:
    with pytest.raises(ValueError):
        expand_ranges(np.array([3], dtype=np.int64), np.array([2], dtype=np.int64))


################################################################################
# Construction
################################################################################


class TestConstruction:

    def test_constant_boxes(self) -> None:
        A = BoxMatrix((4, 3))
        A.add_boxes(0, 2, 0, 1, 1.0)
        A.add_boxes([1, 3], [3, 4], [1, 0], [3, 3], [2.0, 0.5])
        expected = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 2.0, 2.0],
            [0.0, 2.0, 2.0],
            [0.5, 0.5, 0.5],
        ])
        assert np.array_equal(A.to_dense(), expected)
        assert A.num_boxes == 3

    def test_overlapping_boxes_add(self) -> None:
        A = BoxMatrix((3, 2))
        A.add_boxes(0, 3, 0, 2, 1.0)
        A.add_boxes(1, 2, 1, 2, 2.0)
        assert np.array_equal(A.to_dense(), np.array([[1.0, 1.0], [1.0, 3.0], [1.0, 1.0]]))

    def test_rows_are_clipped(self) -> None:
        A = BoxMatrix((3, 1))
        A.add_boxes(-5, 2, 0, 1, 1.0)
        A.add_boxes(2, 100, 0, 1, 2.0)
        A.add_boxes(50, 100, 0, 1, 3.0)
        assert A.to_dense()[:, 0].tolist() == [1.0, 1.0, 2.0]
        assert A.num_boxes == 2

    def test_columns_out_of_bounds(self) -> None:
        A = BoxMatrix((3, 2))
        with pytest.raises(IndexError):
            A.add_boxes(0, 1, 0, 3, 1.0)
        with pytest.raises(IndexError):
            A.add_boxes(0, 1, -1, 1, 1.0)

    def test_mismatched_lengths(self) -> None:
        A = BoxMatrix((3, 2))
        with pytest.raises(ValueError):
            A.add_boxes([0, 1], [1, 2, 3], 0, 1, 1.0)

    def test_nonfinite_weights(self) -> None:
        A = BoxMatrix((3, 2))
        with pytest.raises(ValueError):
            A.add_boxes(0, 1, 0, 1, np.nan)

    def test_keyed_boxes(self) -> None:
        A = BoxMatrix((5, 6))
        k = A.add_key(np.array([0, 1, 1, 3, 2], dtype=np.uint8))
        A.add_keyed_boxes(0, 5, 0, k, 1.0)
        A.add_keyed_boxes(1, 3, 2, k, 0.5)
        expected = np.zeros((5, 6))
        expected[[0, 1, 2, 3, 4], [0, 1, 1, 3, 2]] += 1.0
        expected[[1, 2], [3, 3]] += 0.5
        assert np.array_equal(A.to_dense(), expected)

    def test_keyed_boxes_out_of_bounds(self) -> None:
        A = BoxMatrix((3, 4))
        k = A.add_key(np.array([0, 3, 1], dtype=np.uint8))
        A.add_keyed_boxes(0, 3, 0, k)
        with pytest.raises(IndexError):
            A.add_keyed_boxes(0, 3, 1, k)
        # Fine as long as the offending row is excluded.
        A.add_keyed_boxes(2, 3, 1, k)

    def test_unknown_key(self) -> None:
        A = BoxMatrix((3, 4))
        with pytest.raises(IndexError):
            A.add_keyed_boxes(0, 3, 0, 0)

    def test_key_validation(self) -> None:
        A = BoxMatrix((3, 4))
        with pytest.raises(ValueError):
            A.add_key(np.zeros(4, dtype=np.uint8))
        with pytest.raises(TypeError):
            A.add_key(np.zeros(3, dtype=np.float32))

    def test_add_key_deduplicates(self) -> None:
        A = BoxMatrix((3, 4))
        key = np.zeros(3, dtype=np.uint8)
        assert A.add_key(key) == A.add_key(key) == 0
        assert A.add_key(key.copy()) == 1

    def test_empty(self) -> None:
        A = BoxMatrix((0, 3))
        assert A.to_dense().shape == (0, 3)
        assert A.matvec(np.ones(3)).shape == (0,)
        assert np.array_equal(A.rmatvec(np.ones(0)), np.zeros(3))
        assert A.pieces().col.size == 0


@given(st.lists(boxmatrices(nonnegative=False), min_size=1, max_size=4).filter(lambda xs: len({x.shape[0] for x in xs}) == 1))
@settings(max_examples=50, deadline=None)
def test_hstack(matrices: list[BoxMatrix]) -> None:
    A = BoxMatrix.hstack(matrices)
    assert np.allclose(A.to_dense(), np.hstack([x.to_dense() for x in matrices]))


def test_hstack_mismatched_rows() -> None:
    with pytest.raises(ValueError):
        BoxMatrix.hstack([BoxMatrix((2, 1)), BoxMatrix((3, 1))])


def test_hstack_shares_keys() -> None:
    key = np.array([0, 1], dtype=np.uint8)
    A = BoxMatrix((2, 2))
    A.add_keyed_boxes(0, 2, 0, A.add_key(key))
    B = BoxMatrix((2, 2))
    B.add_keyed_boxes(0, 2, 0, B.add_key(key))
    C = BoxMatrix.hstack([A, B])
    assert len(C.keys) == 1
    assert np.array_equal(C.to_dense(), np.hstack([A.to_dense(), B.to_dense()]))


################################################################################
# Linear Algebra
################################################################################


@given(boxmatrices(nonnegative=False), st.integers(0, 2 ** 16))
@settings(max_examples=200, deadline=None)
def test_matvec(A: BoxMatrix, seed: int) -> None:
    x = np.random.default_rng(seed).normal(size=A.shape[1])
    assert np.allclose(A.matvec(x), A.to_dense() @ x)


@given(boxmatrices(nonnegative=False), st.integers(0, 2 ** 16))
@settings(max_examples=200, deadline=None)
def test_rmatvec(A: BoxMatrix, seed: int) -> None:
    y = np.random.default_rng(seed).normal(size=A.shape[0])
    assert np.allclose(A.rmatvec(y), A.to_dense().T @ y)


def test_matvec_shape() -> None:
    A = BoxMatrix((3, 2))
    with pytest.raises(ValueError):
        A.matvec(np.ones(3))
    with pytest.raises(ValueError):
        A.rmatvec(np.ones(2))


################################################################################
# Canonical Form
################################################################################


def pieces_to_dense(A: BoxMatrix, colscale: np.ndarray | None = None) -> np.ndarray:
    pieces = A.pieces(colscale)
    out = np.zeros(A.shape)
    for c, lo, hi, v in zip(*pieces, strict=True):
        out[lo:hi, c] = v
    return out


@given(boxmatrices(nonnegative=False), st.integers(0, 2 ** 16))
@settings(max_examples=200, deadline=None)
def test_pieces_match_dense(A: BoxMatrix, seed: int) -> None:
    scale = np.random.default_rng(seed).uniform(0.1, 2.0, size=A.shape[1])
    assert np.allclose(pieces_to_dense(A), A.to_dense())
    assert np.allclose(pieces_to_dense(A, scale), A.to_dense() * scale)


@given(boxmatrices(nonnegative=False))
@settings(max_examples=200, deadline=None)
def test_pieces_are_canonical(A: BoxMatrix) -> None:
    col, lo, hi, val = A.pieces()
    assert np.all(hi > lo)
    assert np.all(val != 0)
    order = np.lexsort((lo, col))
    assert np.array_equal(order, np.arange(col.size))
    same = col[1:] == col[:-1]
    # Disjoint within each column.
    assert np.all(lo[1:][same] >= hi[:-1][same])
    # Adjacent pieces with identical values are merged.
    adjacent = same & (lo[1:] == hi[:-1])
    assert np.all(val[1:][adjacent] != val[:-1][adjacent])


def test_pieces_cancellation() -> None:
    A = BoxMatrix((4, 1))
    A.add_boxes(0, 4, 0, 1, 0.1)
    A.add_boxes(1, 3, 0, 1, -0.1)
    col, lo, hi, val = A.pieces()
    assert lo.tolist() == [0, 3]
    assert hi.tolist() == [1, 4]


def test_pieces_merge_runs() -> None:
    A = BoxMatrix((6, 2))
    A.add_keyed_boxes(0, 6, 0, A.add_key(np.array([0, 0, 0, 1, 0, 0], dtype=np.uint8)))
    col, lo, hi, val = A.pieces()
    assert col.tolist() == [0, 0, 1]
    assert lo.tolist() == [0, 4, 3]
    assert hi.tolist() == [3, 6, 4]


################################################################################
# Conversion
################################################################################


@given(boxmatrices(nonnegative=False))
@settings(max_examples=100, deadline=None)
def test_to_scipy(A: BoxMatrix) -> None:
    assert np.allclose(A.to_scipy().toarray(), A.to_dense())


def test_to_dense_refuses_large() -> None:
    A = BoxMatrix((2 ** 22, 2568))
    A.add_boxes(0, 2 ** 22, 0, 2568, 1.0)
    with pytest.raises(ValueError):
        A.to_dense()
    with pytest.raises(ValueError):
        A.to_scipy()
    # But the linear algebra is cheap.
    assert np.allclose(A.matvec(np.ones(2568)), 2568.0)
