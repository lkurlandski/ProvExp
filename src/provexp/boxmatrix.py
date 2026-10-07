"""
Sparse matrices whose nonzero entries are stored as constant-valued rectangles ("boxes").

Explanation provenance matrices are enormous when elements are bytes, e.g., a 4 MiB file and a few thousand
features is roughly 40 GiB as a dense float32 matrix, but their nonzero entries are highly structured. Most features
draw upon a handful of contiguous byte ranges, which a rectangle represents exactly in constant space. A minority of
features scatter each byte into a column determined by the byte's value, e.g., a byte histogram, which a "keyed box"
represents in constant space as well.

The value of a BoxMatrix is the sum of its boxes, i.e., overlapping boxes add. The core linear algebra (`matvec` and
`rmatvec`) operates directly on the boxes, so the matrix never needs to be materialized.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import NamedTuple
from typing import Optional

import numpy as np
from numpy import typing as npt
from scipy import sparse


__all__ = [
    "BoxMatrix",
    "Pieces",
]


IntArray = npt.NDArray[np.int64]
FloatArray = npt.NDArray[np.float64]


################################################################################
# Utilities
################################################################################


def _as_int_array(x: npt.ArrayLike, size: int) -> IntArray:
    a = np.asarray(x)
    if a.ndim == 0:
        a = np.full(size, a)
    if a.ndim != 1 or a.shape[0] != size:
        raise ValueError(f"Expected a scalar or an array of shape ({size},). Got shape {a.shape}.")
    if a.size > 0 and not np.issubdtype(a.dtype, np.integer):
        raise TypeError(f"Expected an integer array. Got {a.dtype}.")
    return a.astype(np.int64, copy=False)


def _as_float_array(x: npt.ArrayLike, size: int) -> FloatArray:
    a = np.asarray(x, dtype=np.float64)
    if a.ndim == 0:
        a = np.full(size, a)
    if a.ndim != 1 or a.shape[0] != size:
        raise ValueError(f"Expected a scalar or an array of shape ({size},). Got shape {a.shape}.")
    if not np.all(np.isfinite(a)):
        raise ValueError("Expected finite values.")
    return a


def _broadcast_size(*xs: npt.ArrayLike) -> int:
    sizes = {np.asarray(x).shape[0] for x in xs if np.asarray(x).ndim > 0}
    if len(sizes) > 1:
        raise ValueError(f"Expected arrays of the same length. Got lengths {sorted(sizes)}.")
    return sizes.pop() if sizes else 1


def _covered(lo: IntArray, hi: IntArray, size: int) -> npt.NDArray[np.bool_]:
    """
    Determine which positions in [0, size) are covered by at least one of the half-open ranges [lo, hi).

    The prefix sums used by `BoxMatrix.matvec` and `BoxMatrix.rmatvec` leave floating-point residue (e.g., 1e-18)
    where ranges end. Counting coverage with integers lets us restore exact zeros wherever no range contributes, which
    matters, e.g., for the soundness of the pullback and for dividing by row sums in the pushforward.
    """
    d = np.bincount(lo, minlength=size + 1) - np.bincount(hi, minlength=size + 1)
    return np.cumsum(d)[:size] > 0


def expand_ranges(lo: IntArray, hi: IntArray) -> tuple[IntArray, IntArray]:
    """
    Expand half-open ranges into the integers they contain.

    Args:
        lo: The inclusive lower bound of each range, shape (B,).
        hi: The exclusive upper bound of each range, shape (B,).

    Returns:
        which: For each integer, the index of the range it came from, shape (T,).
        value: The integers themselves, shape (T,), where T is the total length of the ranges.
    """
    lengths = hi - lo
    if np.any(lengths < 0):
        raise ValueError("Expected hi >= lo for every range.")
    total = int(lengths.sum())
    which = np.repeat(np.arange(lo.shape[0], dtype=np.int64), lengths)
    offsets = np.repeat(np.cumsum(lengths) - lengths, lengths)
    value = np.arange(total, dtype=np.int64) - offsets + np.repeat(lo, lengths)
    return which, value


################################################################################
# BoxMatrix
################################################################################


class Pieces(NamedTuple):
    """
    A canonical representation of a matrix as disjoint, constant-valued row intervals within each column.

    The pieces are sorted by column, then by row. Within a column, pieces never overlap, adjacent pieces never share
    the same value, and every piece has a nonzero value.

    Attributes:
        col: The column of each piece, shape (P,).
        lo: The first row of each piece (inclusive), shape (P,).
        hi: The last row of each piece (exclusive), shape (P,).
        val: The value of every entry within each piece, shape (P,).
    """

    col: IntArray
    lo: IntArray
    hi: IntArray
    val: FloatArray


class BoxMatrix:
    """
    A sparse (m, n) matrix stored as a sum of boxes.

    Two kinds of boxes are supported:
      - A constant box `(r0, r1, c0, c1, w)` adds `w` to every entry in rows [r0, r1) and columns [c0, c1).
      - A keyed box `(r0, r1, c, k, w)` adds `w` to entry `(i, c + key_k[i])` for every row i in [r0, r1), where
        `key_k` is a registered integer array of length m. For example, a byte histogram is a single keyed box
        whose key is the file's bytes.

    Keys are stored by reference, not copied, so many keyed boxes can share a single array (e.g., the file's bytes).
    """

    def __init__(self, shape: tuple[int, int]) -> None:
        m, n = shape
        if m < 0 or n < 0:
            raise ValueError(f"Expected a nonnegative shape. Got {shape}.")
        self.shape = (int(m), int(n))
        self.keys: list[npt.NDArray[np.integer]] = []
        # Constant boxes, accumulated in chunks and concatenated lazily.
        self._boxes: list[tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]] = []
        # Keyed boxes, accumulated in chunks and concatenated lazily.
        self._keyed: list[tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]] = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"shape={self.shape}, "
            f"num_boxes={self.num_boxes}, "
            f"num_keyed_boxes={self.num_keyed_boxes}, "
            f"num_keys={len(self.keys)}"
            f")"
        )

    @property
    def num_boxes(self) -> int:
        return int(self.boxes[0].shape[0])

    @property
    def num_keyed_boxes(self) -> int:
        return int(self.keyed_boxes[0].shape[0])

    @property
    def boxes(self) -> tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]:
        """The constant boxes as arrays `(r0, r1, c0, c1, w)`."""
        if len(self._boxes) != 1:
            self._boxes = [self._concatenate(self._boxes)]
        return self._boxes[0]

    @property
    def keyed_boxes(self) -> tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]:
        """The keyed boxes as arrays `(r0, r1, c, k, w)`."""
        if len(self._keyed) != 1:
            self._keyed = [self._concatenate(self._keyed)]
        return self._keyed[0]

    @staticmethod
    def _concatenate(
        chunks: list[tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]],
    ) -> tuple[IntArray, IntArray, IntArray, IntArray, FloatArray]:
        if len(chunks) == 0:
            i = np.zeros(0, dtype=np.int64)
            return i, i.copy(), i.copy(), i.copy(), np.zeros(0, dtype=np.float64)
        return (
            np.concatenate([c[0] for c in chunks]),
            np.concatenate([c[1] for c in chunks]),
            np.concatenate([c[2] for c in chunks]),
            np.concatenate([c[3] for c in chunks]),
            np.concatenate([c[4] for c in chunks]),
        )

    # ---------- Construction ----------

    def add_boxes(
        self,
        r0: npt.ArrayLike,
        r1: npt.ArrayLike,
        c0: npt.ArrayLike,
        c1: npt.ArrayLike,
        w: npt.ArrayLike = 1.0,
    ) -> None:
        """
        Add constant boxes. Each argument is either a scalar or an array of shape (B,).

        Boxes are clipped to the matrix and empty boxes are dropped. Clipping is deliberate: feature extractors
        routinely compute ranges that run past the end of a (possibly truncated) file.
        """
        m, n = self.shape
        B = _broadcast_size(r0, r1, c0, c1, w)
        r0_ = np.clip(_as_int_array(r0, B), 0, m)
        r1_ = np.clip(_as_int_array(r1, B), 0, m)
        c0_ = _as_int_array(c0, B)
        c1_ = _as_int_array(c1, B)
        w_ = _as_float_array(w, B)
        if np.any(c0_ < 0) or np.any(c1_ > n) or np.any(c1_ < c0_):
            raise IndexError(f"Columns are out of bounds for a matrix with {n} columns.")
        keep = (r1_ > r0_) & (c1_ > c0_)
        self._boxes.append((r0_[keep], r1_[keep], c0_[keep], c1_[keep], w_[keep]))

    def add_key(self, key: npt.NDArray[np.integer]) -> int:
        """
        Register an integer array of length m for use by keyed boxes and return its identifier.

        Registering the same array object twice returns the same identifier.
        """
        if key.ndim != 1 or key.shape[0] != self.shape[0]:
            raise ValueError(f"Expected a key of shape ({self.shape[0]},). Got shape {key.shape}.")
        if not np.issubdtype(key.dtype, np.integer):
            raise TypeError(f"Expected an integer key. Got {key.dtype}.")
        for i, k in enumerate(self.keys):
            if k is key:
                return i
        self.keys.append(key)
        return len(self.keys) - 1

    def add_keyed_boxes(
        self,
        r0: npt.ArrayLike,
        r1: npt.ArrayLike,
        c: npt.ArrayLike,
        k: npt.ArrayLike,
        w: npt.ArrayLike = 1.0,
    ) -> None:
        """
        Add keyed boxes. Each argument is either a scalar or an array of shape (B,).

        Boxes are clipped to the matrix and empty boxes are dropped.
        """
        m, n = self.shape
        B = _broadcast_size(r0, r1, c, k, w)
        r0_ = np.clip(_as_int_array(r0, B), 0, m)
        r1_ = np.clip(_as_int_array(r1, B), 0, m)
        c_ = _as_int_array(c, B)
        k_ = _as_int_array(k, B)
        w_ = _as_float_array(w, B)
        if np.any(k_ < 0) or np.any(k_ >= len(self.keys)):
            raise IndexError(f"Unknown key identifier. There are {len(self.keys)} registered keys.")
        keep = r1_ > r0_
        r0_, r1_, c_, k_, w_ = r0_[keep], r1_[keep], c_[keep], k_[keep], w_[keep]
        _, cols = self._expand_keyed(r0_, r1_, c_, k_)
        if cols.size > 0 and (cols.min() < 0 or cols.max() >= n):
            raise IndexError(f"Keyed boxes address columns out of bounds for a matrix with {n} columns.")
        self._keyed.append((r0_, r1_, c_, k_, w_))

    @classmethod
    def hstack(cls, matrices: Sequence[BoxMatrix]) -> BoxMatrix:
        """
        Concatenate matrices with the same number of rows along the columns.
        """
        if len(matrices) == 0:
            raise ValueError("Cannot stack an empty sequence of matrices.")
        m = matrices[0].shape[0]
        if any(x.shape[0] != m for x in matrices):
            raise ValueError(f"Expected matrices with the same number of rows. Got {[x.shape for x in matrices]}.")

        out = cls((m, sum(x.shape[1] for x in matrices)))
        offset = 0
        for x in matrices:
            r0, r1, c0, c1, w = x.boxes
            out._boxes.append((r0, r1, c0 + offset, c1 + offset, w))
            remap = np.array([out.add_key(key) for key in x.keys], dtype=np.int64)
            r0, r1, c, k, w = x.keyed_boxes
            out._keyed.append((r0, r1, c + offset, remap[k] if k.size > 0 else k, w))
            offset += x.shape[1]
        return out

    def select_columns(self, columns: npt.ArrayLike) -> BoxMatrix:
        """
        The submatrix of the selected columns, i.e., `A[:, columns]`, computed without expanding the boxes.

        Because the columns keep their order, the selected columns of a constant box are contiguous in the submatrix,
        so it stays one box. A keyed box whose columns are all selected is shifted, and one with no selected columns is
        dropped. A keyed box whose columns are only partly selected is rewritten over a derived key, restricted to the
        runs of rows whose column is selected.

        Args:
            columns: Strictly increasing column indices, shape (n',).

        Returns:
            The submatrix, shape (m, n'). It shares the keys of this matrix by reference.
        """
        m, n = self.shape
        cols = np.asarray(columns)
        if cols.ndim != 1 or (cols.size > 0 and not np.issubdtype(cols.dtype, np.integer)):
            raise TypeError(f"Expected a one-dimensional integer array of columns. Got shape {cols.shape} and {cols.dtype}.")
        cols = cols.astype(np.int64, copy=False)
        if np.any(cols < 0) or np.any(cols >= n):
            raise IndexError(f"Columns are out of bounds for a matrix with {n} columns.")
        if np.any(np.diff(cols) <= 0):
            raise ValueError("Expected strictly increasing columns.")

        out = BoxMatrix((m, cols.size))
        new = np.full(n, -1, dtype=np.int64)
        new[cols] = np.arange(cols.size, dtype=np.int64)

        # Constant boxes: the selected columns in [c0, c1) are [lo, hi) in the submatrix.
        r0, r1, c0, c1, w = self.boxes
        lo, hi = np.searchsorted(cols, c0), np.searchsorted(cols, c1)
        keep = hi > lo
        out._boxes.append((r0[keep], r1[keep], lo[keep], hi[keep], w[keep]))

        # Keyed boxes: classify each box by how many of the columns it can address, [c, c + max(key)], are selected.
        r0, r1, c, k, w = self.keyed_boxes
        remap = np.array([out.add_key(key) for key in self.keys], dtype=np.int64)
        kmax = np.array([int(key.max(initial=0)) for key in self.keys], dtype=np.int64)
        prefix = np.concatenate([[0], np.cumsum(new >= 0)])
        end = np.minimum(c + kmax[k] + 1, n) if k.size > 0 else c
        count = prefix[end] - prefix[c]
        full = count == end - c
        out._keyed.append((r0[full], r1[full], new[c[full]], remap[k[full]] if full.any() else k[full], w[full]))

        # Partly selected keyed boxes. The derived key holds each row's column relative to the box's first selected
        # column, so boxes over the same key with the same selection pattern share it (e.g., the bins of a 2D histogram).
        partial = (count > 0) & ~full
        derived: dict[tuple[int, bytes], tuple[int, IntArray, IntArray]] = {}
        for i in np.flatnonzero(partial):
            key, start = int(k[i]), int(c[i])
            span = start + np.arange(kmax[key] + 1)
            table = np.where(span < n, new[np.minimum(span, n - 1)], -1)
            base = int(table[table >= 0].min())
            relative = np.where(table >= 0, table - base, -1)
            pattern = (key, relative.tobytes())
            if pattern not in derived:
                mapped = relative[self.keys[key]]
                valid = np.concatenate([[False], mapped >= 0, [False]])
                edges = np.flatnonzero(np.diff(valid.astype(np.int8)))
                dtype = np.min_scalar_type(int(relative.max()))
                kid = out.add_key(np.where(mapped >= 0, mapped, 0).astype(dtype))
                derived[pattern] = (kid, edges[0::2], edges[1::2])
            kid, starts, ends = derived[pattern]
            # The runs of selected rows that intersect [r0, r1).
            i0 = np.searchsorted(ends, r0[i], side="right")
            i1 = np.searchsorted(starts, r1[i], side="left")
            runs = np.arange(i0, i1)
            lo_k = np.maximum(starts[runs], r0[i])
            hi_k = np.minimum(ends[runs], r1[i])
            ones = np.ones(runs.size, dtype=np.int64)
            out._keyed.append((lo_k, hi_k, ones * base, ones * kid, np.full(runs.size, w[i])))

        return out

    # ---------- Linear Algebra ----------

    def _expand_keyed(self, r0: IntArray, r1: IntArray, c: IntArray, k: IntArray) -> tuple[IntArray, IntArray]:
        """
        Expand keyed boxes into the (row, column) of every entry they touch.

        Returns:
            rows: The row of each entry, shape (T,).
            cols: The column of each entry, shape (T,).
        """
        which, rows = expand_ranges(r0, r1)
        cols = c[which]
        for i in np.unique(k):
            mask = k[which] == i
            cols[mask] += self.keys[i][rows[mask]].astype(np.int64)
        return rows, cols

    def _expand_keyed_with_weights(self) -> tuple[IntArray, IntArray, FloatArray]:
        r0, r1, c, k, w = self.keyed_boxes
        rows, cols = self._expand_keyed(r0, r1, c, k)
        weights = np.repeat(w, r1 - r0)
        return rows, cols, weights

    def matvec(self, x: npt.ArrayLike) -> FloatArray:
        """
        Compute `A @ x` for a vector x of shape (n,).
        """
        m, n = self.shape
        x_ = np.asarray(x, dtype=np.float64)
        if x_.shape != (n,):
            raise ValueError(f"Expected a vector of shape ({n},). Got {x_.shape}.")

        # Constant boxes: each box adds w * sum(x[c0:c1]) to the rows [r0, r1).
        r0, r1, c0, c1, w = self.boxes
        X = np.concatenate([[0.0], np.cumsum(x_)])
        v = w * (X[c1] - X[c0])
        d = np.bincount(r0, weights=v, minlength=m + 1) - np.bincount(r1, weights=v, minlength=m + 1)
        y: FloatArray = np.cumsum(d, dtype=np.float64)[:m]
        y[~_covered(r0[v != 0], r1[v != 0], m)] = 0.0

        # Keyed boxes: each entry (i, j) adds w * x[j] to row i.
        rows, cols, weights = self._expand_keyed_with_weights()
        y += np.bincount(rows, weights=weights * x_[cols], minlength=m)

        return y

    def rmatvec(self, y: npt.ArrayLike) -> FloatArray:
        """
        Compute `A.T @ y` for a vector y of shape (m,).
        """
        m, n = self.shape
        y_ = np.asarray(y, dtype=np.float64)
        if y_.shape != (m,):
            raise ValueError(f"Expected a vector of shape ({m},). Got {y_.shape}.")

        # Constant boxes: each box adds w * sum(y[r0:r1]) to the columns [c0, c1).
        r0, r1, c0, c1, w = self.boxes
        Y = np.concatenate([[0.0], np.cumsum(y_)])
        v = w * (Y[r1] - Y[r0])
        d = np.bincount(c0, weights=v, minlength=n + 1) - np.bincount(c1, weights=v, minlength=n + 1)
        x: FloatArray = np.cumsum(d, dtype=np.float64)[:n]
        x[~_covered(c0[v != 0], c1[v != 0], n)] = 0.0

        # Keyed boxes: each entry (i, j) adds w * y[i] to column j.
        rows, cols, weights = self._expand_keyed_with_weights()
        x += np.bincount(cols, weights=weights * y_[rows], minlength=n)

        return x

    # ---------- Canonical Form ----------

    def pieces(self, colscale: Optional[npt.ArrayLike] = None, rtol: float = 1e-12) -> Pieces:
        """
        Compute the canonical form of the matrix: disjoint, constant-valued row intervals within each column.

        Args:
            colscale: Optionally, scale each column by this factor, shape (n,).
            rtol: Values whose magnitude is at most `rtol` times the total magnitude of the boxes that cover that
                column are considered zero. This cleans up the floating-point residue left by overlapping boxes.

        Returns:
            The pieces of the matrix.
        """
        m, n = self.shape
        scale = np.ones(n, dtype=np.float64) if colscale is None else np.asarray(colscale, dtype=np.float64)
        if scale.shape != (n,):
            raise ValueError(f"Expected colscale of shape ({n},). Got {scale.shape}.")

        # Split constant boxes into single-column intervals.
        r0, r1, c0, c1, w = self.boxes
        which, cols_b = expand_ranges(c0, c1)
        lo_b, hi_b, val_b = r0[which], r1[which], w[which]

        # Split keyed boxes into single-entry intervals.
        rows_k, cols_k, val_k = self._expand_keyed_with_weights()

        col = np.concatenate([cols_b, cols_k])
        lo = np.concatenate([lo_b, rows_k])
        hi = np.concatenate([hi_b, rows_k + 1])
        val = np.concatenate([val_b, val_k]) * scale[col]

        return _canonicalize(col, lo, hi, val, m, n, rtol)

    # ---------- Conversion ----------

    def to_dense(self, max_elements: int = 2 ** 26) -> FloatArray:
        """
        Materialize the matrix as a dense float64 array. Raises if the matrix has more than `max_elements` entries.
        """
        m, n = self.shape
        if m * n > max_elements:
            raise ValueError(f"Refusing to materialize a {m}x{n} matrix ({m * n} > {max_elements} entries).")
        out = np.zeros((m, n), dtype=np.float64)
        for r0, r1, c0, c1, w in zip(*self.boxes, strict=True):
            out[r0:r1, c0:c1] += w
        rows, cols, weights = self._expand_keyed_with_weights()
        np.add.at(out, (rows, cols), weights)
        return out

    def to_scipy(self, max_nnz: int = 2 ** 28) -> sparse.csr_array:
        """
        Convert the matrix to a scipy CSR array. Raises if it would store more than `max_nnz` entries.
        """
        m, n = self.shape
        r0, r1, c0, c1, w = self.boxes
        nnz = int(((r1 - r0) * (c1 - c0)).sum()) + int((self.keyed_boxes[1] - self.keyed_boxes[0]).sum())
        if nnz > max_nnz:
            raise ValueError(f"Refusing to expand {nnz} > {max_nnz} entries.")
        pieces = self.pieces(rtol=0.0)
        which, rows = expand_ranges(pieces.lo, pieces.hi)
        return sparse.csr_array((pieces.val[which], (rows, pieces.col[which])), shape=(m, n))


def _canonicalize(col: IntArray, lo: IntArray, hi: IntArray, val: FloatArray, m: int, n: int, rtol: float) -> Pieces:
    """
    Sum possibly overlapping single-column intervals into disjoint pieces (see `BoxMatrix.pieces`).
    """
    if col.size == 0:
        z = np.zeros(0, dtype=np.int64)
        return Pieces(z, z.copy(), z.copy(), np.zeros(0, dtype=np.float64))

    # Each interval starts (+val) and ends (-val) at a position within its column.
    ecol = np.concatenate([col, col])
    epos = np.concatenate([lo, hi])
    edel = np.concatenate([val, -val])

    # Merge events at the same (column, position).
    key = ecol * (m + 1) + epos
    order = np.argsort(key, kind="stable")
    key, edel = key[order], edel[order]
    starts = np.flatnonzero(np.concatenate([[True], key[1:] != key[:-1]]))
    key = key[starts]
    edel = np.add.reduceat(edel, starts)
    ecol, epos = key // (m + 1), key % (m + 1)

    # Running value within each column. Subtracting the running value at the start of each column keeps the
    # floating-point residue of one column from leaking into the next.
    csum = np.cumsum(edel)
    first = np.concatenate([[True], ecol[1:] != ecol[:-1]])
    base = np.maximum.accumulate(np.where(first, np.arange(first.size), 0))
    running = csum - csum[base] + edel[base]

    # A piece spans from one event to the next event in the same column.
    same = ecol[:-1] == ecol[1:]
    pcol, plo, phi, pval = ecol[:-1][same], epos[:-1][same], epos[1:][same], running[:-1][same]

    # Drop (numerically) zero pieces.
    magnitude = np.bincount(col, weights=np.abs(val), minlength=n)
    keep = np.abs(pval) > rtol * magnitude[pcol]
    pcol, plo, phi, pval = pcol[keep], plo[keep], phi[keep], pval[keep]

    # Merge adjacent pieces with identical values, e.g., runs of identical bytes in a keyed box.
    if pcol.size > 0:
        brk = np.concatenate([[True], (pcol[1:] != pcol[:-1]) | (plo[1:] != phi[:-1]) | (pval[1:] != pval[:-1])])
        starts = np.flatnonzero(brk)
        ends = np.concatenate([starts[1:], [pcol.size]]) - 1
        pcol, plo, phi, pval = pcol[starts], plo[starts], phi[ends], pval[starts]

    return Pieces(pcol, plo, phi, pval)
