"""
Explanation provenance and the operators that transfer explanations between the problem-space and the feature-space.

Notation follows the manuscript: a problem-space object z has m elements (bytes), its feature-space representation x
has n features, and the provenance matrix P is nonnegative with columns that sum to one. P[i, j] is the proportion of
feature j's provenance attributable to element i.
"""

from __future__ import annotations
from collections.abc import Sequence
from functools import cached_property
from typing import Literal
from typing import NamedTuple
from typing import Optional

import numba
import numpy as np
from numpy import typing as npt

from provexp.boxmatrix import BoxMatrix
from provexp.boxmatrix import FloatArray
from provexp.boxmatrix import IntArray
from provexp.boxmatrix import Pieces
from provexp.boxmatrix import expand_ranges


__all__ = [
    "EmptyPolicy",
    "Provenance",
    "Ambiguity",
    "Overlap",
]


# NOTE (Axiom 3): a feature to which no element contributes cannot satisfy both Axiom 2 (its column sums to one) and
# Axiom 3 (only influencing elements have nonzero provenance). Examples include features that do not depend on any
# particular bytes (e.g., whether a file parsed as a PE) and features whose value is zero because the thing they count
# is absent (e.g., an empty hash bucket). Feature sets never fabricate provenance for such features, so their columns
# of the raw contributions are empty, and this policy decides how to treat them. Changing the policy does not require
# recomputing any provenance.
#   - "null" (the default): augment the problem-space with a null element, which stands for "no part of the input"
#       and is the sole source of provenance of every empty feature. P then has m + 1 rows, the last of which is the null element, and
#       satisfies all three axioms over the augmented problem-space. The null element's share of a pulled-back
#       explanation is the attribution that cannot be localized within the input.
#   - "uniform": spread the feature's provenance uniformly over all elements. Satisfies Axioms 1 and 2, but
#       contradicts Axiom 3 because every element is said to influence the feature. Equivalent to "null" followed by
#       spreading the null element's share uniformly over the real elements.
#   - "ignore": leave the column empty. Pullback and pushforward ignore the feature and the summary statistics exclude
#       it. Satisfies Axioms 1 and 3, but the column does not sum to one (Axiom 2). Equivalent to the manuscript's
#       recommendation of excluding the feature from P entirely, without changing the feature indices.
EmptyPolicy = Literal["null", "uniform", "ignore"]


################################################################################
# Provenance
################################################################################


class Ambiguity(NamedTuple):
    """
    Provenance ambiguity (manuscript, Definition 6).

    Attributes:
        per_feature: H_j for each feature, shape (n,).
        normalized: H_j / log|A_j| for each feature (0 if |A_j| <= 1), shape (n,).
        overall: The mean of the normalized ambiguity over the included features.
        support: |A_j|, the number of elements with nonzero provenance for each feature, shape (n,).
        included: Whether each feature is included in the overall statistic, shape (n,).
    """

    per_feature: FloatArray
    normalized: FloatArray
    overall: float
    support: IntArray
    included: npt.NDArray[np.bool_]


class Overlap(NamedTuple):
    """
    Provenance overlap (manuscript, Definition 7).

    Attributes:
        per_feature: O_j = sum_{k != j} I_{j,k} for each feature, shape (n,).
        normalized: O_j / (n' - 1), where n' is the number of included features, shape (n,).
        overall: The mean of the normalized overlap over the included features.
        included: Whether each feature is included in the statistics, shape (n,).
    """

    per_feature: FloatArray
    normalized: FloatArray
    overall: float
    included: npt.NDArray[np.bool_]


class Provenance:
    """
    The explanation provenance of one problem-space object under a feature mapping function.

    The raw contributions C (m, n) are stored and P is computed lazily by normalizing the columns of C, i.e.,
    P = C diag(1 / colsum(C)), with empty columns handled according to `empty`. Feature sets record contributions in
    whatever units are natural (e.g., one per counted byte) and never need to normalize anything themselves.

    With `empty="null"`, P has `num_rows = num_elements + 1` rows, the last of which is the null element. Vectors in
    the problem-space then have `num_rows` entries, although `pushforward` also accepts `num_elements` entries, in
    which case the null element's entry is taken to be zero.

    Args:
        contributions: The raw contributions C as a BoxMatrix of shape (m, n).
        feature_names: Optionally, the name of each feature.
        empty: How to treat features with no contributions. See `EmptyPolicy`.
    """

    def __init__(
        self,
        contributions: BoxMatrix,
        feature_names: Optional[Sequence[str]] = None,
        empty: EmptyPolicy = "null",
    ) -> None:
        if empty not in ("null", "uniform", "ignore"):
            raise ValueError(f"Invalid empty policy: {empty}")
        if feature_names is not None and len(feature_names) != contributions.shape[1]:
            raise ValueError(f"Expected {contributions.shape[1]} feature names. Got {len(feature_names)}.")

        self.contributions = contributions
        self.feature_names = list(feature_names) if feature_names is not None else None
        self.empty = empty

        if np.any(contributions.boxes[4] < 0) or np.any(contributions.keyed_boxes[4] < 0):
            raise ValueError("Contributions must be nonnegative (Axiom 1).")
        # Clamp the floating-point residue of the prefix sums used by rmatvec.
        colsum = np.maximum(contributions.rmatvec(np.ones(self.num_elements)), 0.0)
        # A column whose sum is at most a tiny fraction of the largest column is numerically empty.
        tol = 1e-12 * colsum.max(initial=0.0)
        self.colsum: FloatArray = colsum
        self.is_empty: npt.NDArray[np.bool_] = colsum <= tol
        self.scale: FloatArray = np.where(self.is_empty, 0.0, 1.0 / np.where(self.is_empty, 1.0, colsum))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"num_elements={self.num_elements}, "
            f"num_features={self.num_features}, "
            f"num_empty={int(self.is_empty.sum())}, "
            f"empty={self.empty!r}"
            f")"
        )

    @property
    def num_elements(self) -> int:
        """The number of real elements, m."""
        return self.contributions.shape[0]

    @property
    def num_features(self) -> int:
        """The number of features, n."""
        return self.contributions.shape[1]

    @property
    def has_null(self) -> bool:
        """Whether P has a null element (see `EmptyPolicy`)."""
        return self.empty == "null"

    @property
    def num_rows(self) -> int:
        """The number of rows of P, i.e., the number of elements plus the null element, if any."""
        return self.num_elements + int(self.has_null)

    @property
    def shape(self) -> tuple[int, int]:
        """The shape of P."""
        return self.num_rows, self.num_features

    @property
    def _uniform(self) -> bool:
        return self.empty == "uniform" and self.num_elements > 0

    # ---------- Products with P ----------

    def matvec(self, a: npt.ArrayLike) -> FloatArray:
        """Compute P @ a for a vector of shape (n,). Returns a vector of shape (num_rows,)."""
        a_ = np.asarray(a, dtype=np.float64)
        b = self.contributions.matvec(a_ * self.scale)
        if self._uniform:
            b += a_[self.is_empty].sum() / self.num_elements
        if self.has_null:
            b = np.append(b, a_[self.is_empty].sum())
        return b

    def rmatvec(self, b: npt.ArrayLike) -> FloatArray:
        """Compute P.T @ b for a vector of shape (num_rows,)."""
        b_ = np.asarray(b, dtype=np.float64)
        a = self.contributions.rmatvec(b_[:self.num_elements]) * self.scale
        if self._uniform:
            a[self.is_empty] = b_.sum() / self.num_elements
        if self.has_null:
            a[self.is_empty] = b_[self.num_elements]
        return a

    def rowsum(self) -> FloatArray:
        """Compute D, the row sums of P, shape (num_rows,)."""
        return self.matvec(np.ones(self.num_features))

    def to_dense(self, max_elements: int = 2 ** 26) -> FloatArray:
        """Materialize P as a dense array (only sensible for small objects)."""
        P = self.contributions.to_dense(max_elements) * self.scale
        if self._uniform:
            P[:, self.is_empty] = 1.0 / self.num_elements
        if self.has_null:
            P = np.vstack([P, self.is_empty.astype(np.float64)])
        return P

    def pieces(self) -> Pieces:
        """The canonical form of P (see `BoxMatrix.pieces`), including uniform columns and the null element."""
        pieces = self.contributions.pieces(colscale=self.scale)
        if not (self._uniform or self.has_null) or not np.any(self.is_empty):
            return pieces
        cols = np.flatnonzero(self.is_empty).astype(np.int64)
        if self._uniform:
            lo, hi, val = np.zeros_like(cols), np.full_like(cols, self.num_elements), 1.0 / self.num_elements
        else:
            lo, hi, val = np.full_like(cols, self.num_elements), np.full_like(cols, self.num_elements + 1), 1.0
        col = np.concatenate([pieces.col, cols])
        lo = np.concatenate([pieces.lo, lo])
        hi = np.concatenate([pieces.hi, hi])
        val = np.concatenate([pieces.val, np.full(cols.shape, val)])
        order = np.lexsort((lo, col))
        return Pieces(col[order], lo[order], hi[order], val[order])

    # ---------- Feature Subsets ----------

    def select(self, features: npt.ArrayLike | Sequence[str]) -> Provenance:
        """
        The provenance of a subset S of the features alone, as if the feature mapping function computed only S.

        Every column of P is normalized on its own, so the result is exactly the selected columns, P_S = P[:, S], with
        the same empty policy. Its statistics therefore describe the subset in isolation, e.g., its overlap counts only
        the mass that the features of S share with each other.

        Args:
            features: The features of S, as indices, a boolean mask of shape (n,), or names (see `feature_names`).
                The selected features keep their original order.

        Returns:
            The provenance of S, with |S| features.
        """
        n = self.num_features
        f = np.asarray(features)
        if f.size == 0:
            idx = np.zeros(0, dtype=np.int64)
        elif f.dtype == np.bool_:
            if f.shape != (n,):
                raise ValueError(f"Expected a boolean mask of shape ({n},). Got {f.shape}.")
            idx = np.flatnonzero(f)
        elif f.dtype.kind in ("U", "S", "O"):
            if self.feature_names is None:
                raise ValueError("Cannot select features by name without feature names.")
            index = {name: i for i, name in enumerate(self.feature_names)}
            unknown = [name for name in f.tolist() if name not in index]
            if unknown:
                raise ValueError(f"Unknown feature names: {unknown[:5]}{'...' if len(unknown) > 5 else ''}")
            idx = np.array([index[name] for name in f.tolist()], dtype=np.int64)
        elif np.issubdtype(f.dtype, np.integer):
            idx = f.astype(np.int64)
        else:
            raise TypeError(f"Expected indices, a boolean mask, or names. Got an array of {f.dtype}.")
        if idx.ndim != 1:
            raise ValueError(f"Expected a one-dimensional selection. Got shape {idx.shape}.")
        if np.any(idx < 0) or np.any(idx >= n):
            raise IndexError(f"Feature indices are out of bounds for {n} features.")
        idx = np.sort(idx)
        if np.any(np.diff(idx) == 0):
            raise ValueError("Expected each feature to be selected at most once.")

        names = [self.feature_names[i] for i in idx] if self.feature_names is not None else None
        sub = Provenance(self.contributions.select_columns(idx), names, self.empty)
        # NOTE: Which columns count as numerically empty depends on the largest column sum, which can differ within S.
        # Inheriting the normalization keeps P_S identical to P[:, S].
        sub.colsum, sub.is_empty, sub.scale = self.colsum[idx], self.is_empty[idx], self.scale[idx]
        return sub

    # ---------- Explanation Transfers ----------

    def pullback(self, a: npt.ArrayLike) -> FloatArray:
        """
        Pull a feature-space explanation back into the problem-space, i.e., tau(a) = P a (manuscript, Definition 4).

        Args:
            a: A feature-space explanation, shape (n,).

        Returns:
            A problem-space explanation, shape (num_rows,). With a null element, the last entry is its share.
        """
        a_ = np.asarray(a, dtype=np.float64)
        if a_.shape != (self.num_features,):
            raise ValueError(f"Expected an explanation of shape ({self.num_features},). Got {a_.shape}.")
        return self.matvec(a_)

    def pushforward(self, b: npt.ArrayLike) -> FloatArray:
        """
        Push a problem-space explanation forward into the feature-space, i.e., psi(b) = P^T D^+ b
        (manuscript, Definition 5).

        Args:
            b: A problem-space explanation, shape (num_rows,), or shape (num_elements,) if the null element's entry
                is zero.

        Returns:
            A feature-space explanation, shape (n,).
        """
        b_ = np.asarray(b, dtype=np.float64)
        if self.has_null and b_.shape == (self.num_elements,):
            b_ = np.append(b_, 0.0)
        if b_.shape != (self.num_rows,):
            raise ValueError(f"Expected an explanation of shape ({self.num_rows},). Got {b_.shape}.")
        D = self.rowsum()
        Dinv = np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0)
        return self.rmatvec(Dinv * b_)

    def pull_push(self, a: npt.ArrayLike) -> FloatArray:
        """The pull-push cyclic operator, psi(tau(a)) (manuscript, Definition 8)."""
        return self.pushforward(self.pullback(a))

    def push_pull(self, b: npt.ArrayLike) -> FloatArray:
        """The push-pull cyclic operator, tau(psi(b)) (manuscript, Definition 8)."""
        return self.pullback(self.pushforward(b))

    def pull_push_error(self, a: npt.ArrayLike) -> float:
        """The pull-push reconstruction error, ||psi(tau(a)) - a||_2 (manuscript, Definition 9)."""
        return float(np.linalg.norm(self.pull_push(a) - np.asarray(a, dtype=np.float64)))

    def push_pull_error(self, b: npt.ArrayLike) -> float:
        """The push-pull reconstruction error, ||tau(psi(b)) - b||_2 (manuscript, Definition 9)."""
        b_ = np.asarray(b, dtype=np.float64)
        if self.has_null and b_.shape == (self.num_elements,):
            b_ = np.append(b_, 0.0)
        return float(np.linalg.norm(self.push_pull(b_) - b_))

    # ---------- Summary Statistics ----------

    @property
    def included(self) -> npt.NDArray[np.bool_]:
        """Whether each feature participates in the summary statistics (see `EmptyPolicy`)."""
        if self.empty == "ignore":
            return ~self.is_empty
        return np.ones(self.num_features, dtype=np.bool_)

    @cached_property
    def _statistics(self) -> tuple[FloatArray, FloatArray, IntArray]:
        """
        The per-feature overlap, entropy, and support of P, computed in a single sweep over its rows.
        """
        m, n = self.num_elements, self.num_features

        # Constant intervals: every constant box split into one interval per column.
        r0, r1, c0, c1, w = self.contributions.boxes
        which, c_col = expand_ranges(c0, c1)
        c_lo, c_hi, c_val = r0[which], r1[which], w[which] * self.scale[c_col]

        # Empty columns, according to the policy. Under "uniform", every empty column has the same value in every row,
        # so they are represented by a single extra column (index n) with a multiplicity of one per empty column.
        cols = np.flatnonzero(self.is_empty).astype(np.int64)
        mult = np.ones(n + 1, dtype=np.int64)
        if self._uniform and cols.size > 0:
            mult[n] = cols.size
            c_col = np.append(c_col, n)
            c_lo = np.append(c_lo, 0)
            c_hi = np.append(c_hi, m)
            c_val = np.append(c_val, 1.0 / m)
        if self.has_null:
            c_col = np.concatenate([c_col, cols])
            c_lo = np.concatenate([c_lo, np.full_like(cols, m)])
            c_hi = np.concatenate([c_hi, np.full_like(cols, m + 1)])
            c_val = np.concatenate([c_val, np.ones(cols.shape)])

        # Keyed entries: every keyed box split into one entry per row.
        k_row, k_col, k_w = self.contributions._expand_keyed_with_weights()
        k_val = k_w * self.scale[k_col]

        keep_c = c_val > 0
        keep_k = k_val > 0
        O, H, support = _sweep_statistics(
            self.num_rows,
            mult,
            c_col[keep_c], c_lo[keep_c], c_hi[keep_c], c_val[keep_c],
            k_row[keep_k], k_col[keep_k], k_val[keep_k],
        )

        # Every empty column shares the statistics of the extra column.
        if self._uniform:
            O[cols], H[cols], support[cols] = O[n], H[n], support[n]
        return O[:n], H[:n], support[:n]

    @property
    def coverage(self) -> float:
        """
        The provenance coverage, i.e., the fraction of features attributable to some element (manuscript, Definition
        Explanation Localizability).
        """
        return float((~self.is_empty).mean()) if self.num_features > 0 else 0.0

    def localizability(self, a: npt.ArrayLike) -> float:
        """
        The localizability of a feature-space explanation, i.e., the fraction of its attribution magnitude on
        attributable features, which the pullback places on elements rather than the null element (manuscript,
        Definition Explanation Localizability).
        """
        a_ = np.abs(np.asarray(a, dtype=np.float64))
        if a_.shape != (self.num_features,):
            raise ValueError(f"Expected an explanation of shape ({self.num_features},). Got {a_.shape}.")
        total = a_.sum()
        return float(a_[~self.is_empty].sum() / total) if total > 0 else 1.0

    def ambiguity(self) -> Ambiguity:
        """
        Compute the provenance ambiguity exactly.
        """
        n = self.num_features
        _, H, support = self._statistics
        H = np.maximum(H, 0.0)

        normalized = np.zeros(n, dtype=np.float64)
        many = support > 1
        normalized[many] = H[many] / np.log(support[many])
        normalized = np.clip(normalized, 0.0, 1.0)

        included = self.included
        overall = float(normalized[included].mean()) if np.any(included) else 0.0
        return Ambiguity(H, normalized, overall, support, included)

    def overlap(self) -> Overlap:
        """
        Compute the provenance overlap exactly.

        Within a run of rows in which t features have nonzero values sorted q_1 <= ... <= q_t, the feature of rank r
        shares sum_{s < r} q_s + q_r * (t - r) mass with the other features, per row. Summing this over the rows gives
        O_j without enumerating the O(n^2) pairs of features.
        """
        n = self.num_features
        O, _, _ = self._statistics
        included = self.included
        nincluded = int(included.sum())
        normalized = O / (nincluded - 1) if nincluded > 1 else np.zeros(n, dtype=np.float64)
        overall = float(normalized[included].mean()) if nincluded > 0 else 0.0
        return Overlap(O, normalized, overall, included)

    # ---------- Validation ----------

    def check_axioms(self, atol: float = 1e-9) -> None:
        """
        Check the axioms of explanation provenance that can be checked numerically (manuscript, Definition 3).

        Axiom 3 (Influence) is a statement about the feature mapping function, so it cannot be verified from P alone.

        Raises:
            ValueError: If an axiom is violated.
        """
        if np.any(self.contributions.boxes[4] < 0) or np.any(self.contributions.keyed_boxes[4] < 0):
            raise ValueError("Axiom 1 (Nonnegativity) is violated.")
        if self.num_rows == 0:
            return
        colsum = self.rmatvec(np.ones(self.num_rows))
        expected = np.where(self.is_empty & (self.empty == "ignore"), 0.0, 1.0)
        if not np.allclose(colsum, expected, atol=atol, rtol=0.0):
            bad = np.flatnonzero(~np.isclose(colsum, expected, atol=atol, rtol=0.0))
            raise ValueError(f"Axiom 2 (Normalization) is violated for features {bad[:10].tolist()}.")


################################################################################
# Statistics Kernel
################################################################################


@numba.njit(cache=True)
def _accumulate(
    vals: FloatArray,
    cols: IntArray,
    t: int,
    mult: IntArray,
    weight: float,
    O: FloatArray,
    H: FloatArray,
    support: IntArray,
) -> None:
    """
    Accumulate the overlap, entropy, and support of t nonzero values sorted in ascending order, over `weight` rows.

    Column c stands for `mult[c]` identical columns. Each of them shares the sum of the values ranked below the group
    plus its own value with every column ranked at or above it, other than itself.
    """
    total = 0
    for r in range(t):
        total += mult[cols[r]]
    smaller = 0.0
    before = 0
    for r in range(t):
        v = vals[r]
        c = cols[r]
        O[c] += weight * (smaller + v * (total - 1 - before))
        H[c] -= weight * v * np.log(v)
        support[c] += int(weight)
        smaller += mult[c] * v
        before += mult[c]


@numba.njit(cache=True)
def _sweep_statistics(
    num_rows: int,
    mult: IntArray,
    c_col: IntArray,
    c_lo: IntArray,
    c_hi: IntArray,
    c_val: FloatArray,
    k_row: IntArray,
    k_col: IntArray,
    k_val: FloatArray,
) -> tuple[FloatArray, FloatArray, IntArray]:
    """
    Compute the per-feature overlap, entropy, and support of a matrix given as positive constant intervals
    `(c_col, [c_lo, c_hi), c_val)` and positive single entries `(k_row, k_col, k_val)`, all of which add. Column c
    stands for `mult[c]` identical columns (see `_accumulate`); single entries must only land on columns with a
    multiplicity of one.

    The rows are swept in order. The columns covered by constant intervals form a "base" that only changes where
    an interval starts or ends, so runs of rows without single entries are accumulated at once. Rows with single
    entries merge their (few) values into the sorted base.
    """
    n = mult.size
    O = np.zeros(n)
    H = np.zeros(n)
    support = np.zeros(n, dtype=np.int64)

    # Group the single entries by row (counting sort).
    ptr = np.zeros(num_rows + 1, dtype=np.int64)
    for i in range(k_row.size):
        ptr[k_row[i] + 1] += 1
    maxk = 0
    for r in range(num_rows):
        maxk = max(maxk, ptr[r + 1])
        ptr[r + 1] += ptr[r]
    fill = ptr[:-1].copy()
    g_col = np.empty(k_row.size, dtype=np.int64)
    g_val = np.empty(k_row.size, dtype=np.float64)
    for i in range(k_row.size):
        r = k_row[i]
        g_col[fill[r]] = k_col[i]
        g_val[fill[r]] = k_val[i]
        fill[r] += 1

    # The start and end of every constant interval, in order of position.
    E = c_col.size
    epos = np.empty(2 * E, dtype=np.int64)
    for i in range(E):
        epos[2 * i] = c_lo[i]
        epos[2 * i + 1] = c_hi[i]
    order = np.argsort(epos, kind="mergesort")

    # The base: the value and number of active intervals of each column, and the active columns sorted by value.
    bval = np.zeros(n)
    bcnt = np.zeros(n, dtype=np.int64)
    active = np.empty(n, dtype=np.int64)
    where = np.full(n, -1, dtype=np.int64)
    t = 0
    s_col = np.empty(n, dtype=np.int64)
    s_val = np.empty(n, dtype=np.float64)

    # Workspace for rows with single entries.
    w_col = np.empty(n + maxk, dtype=np.int64)
    w_val = np.empty(n + maxk, dtype=np.float64)
    r_col = np.empty(maxk, dtype=np.int64)
    r_val = np.empty(maxk, dtype=np.float64)

    e = 0
    cur = 0
    while cur < num_rows:

        # Apply the intervals that start or end here, then re-sort the base.
        changed = False
        while e < 2 * E and epos[order[e]] == cur:
            i = order[e] // 2
            c = c_col[i]
            if order[e] % 2 == 0:
                if bcnt[c] == 0:
                    where[c] = t
                    active[t] = c
                    t += 1
                bcnt[c] += 1
                bval[c] += c_val[i]
            else:
                bcnt[c] -= 1
                bval[c] -= c_val[i]
                if bcnt[c] == 0:
                    bval[c] = 0.0
                    last = active[t - 1]
                    active[where[c]] = last
                    where[last] = where[c]
                    where[c] = -1
                    t -= 1
            changed = True
            e += 1
        if changed:
            for j in range(t):
                s_val[j] = bval[active[j]]
            idx = np.argsort(s_val[:t])
            for j in range(t):
                s_col[j] = active[idx[j]]
            for j in range(t):
                s_val[j] = bval[s_col[j]]

        nxt = epos[order[e]] if e < 2 * E else num_rows
        r = cur
        while r < nxt:

            # A run of rows without single entries.
            if ptr[r + 1] == ptr[r]:
                start = r
                while r < nxt and ptr[r + 1] == ptr[r]:
                    r += 1
                if t > 0:
                    _accumulate(s_val, s_col, t, mult, float(r - start), O, H, support)
                continue

            # A row with single entries: combine duplicates, then merge them into the base.
            K = 0
            for i in range(ptr[r], ptr[r + 1]):
                c = g_col[i]
                found = False
                for q in range(K):
                    if r_col[q] == c:
                        r_val[q] += g_val[i]
                        found = True
                        break
                if not found:
                    r_col[K] = c
                    r_val[K] = g_val[i]
                    K += 1

            collision = False
            for q in range(K):
                if bcnt[r_col[q]] > 0:
                    collision = True
                    break

            if collision:
                # Rare: a single entry lands on a column of the base, so values change. Re-sort everything.
                T = 0
                for j in range(t):
                    w_col[T] = s_col[j]
                    w_val[T] = s_val[j]
                    T += 1
                for q in range(K):
                    c = r_col[q]
                    merged = False
                    for j in range(t):
                        if w_col[j] == c:
                            w_val[j] += r_val[q]
                            merged = True
                            break
                    if not merged:
                        w_col[T] = c
                        w_val[T] = r_val[q]
                        T += 1
                idx = np.argsort(w_val[:T])
                tmp_col = w_col[:T][idx].copy()
                tmp_val = w_val[:T][idx].copy()
                _accumulate(tmp_val, tmp_col, T, mult, 1.0, O, H, support)
            else:
                # Common: sort the single entries (insertion sort, K is small) and merge them with the base.
                for a in range(1, K):
                    vc, vv = r_col[a], r_val[a]
                    b = a - 1
                    while b >= 0 and r_val[b] > vv:
                        r_col[b + 1] = r_col[b]
                        r_val[b + 1] = r_val[b]
                        b -= 1
                    r_col[b + 1] = vc
                    r_val[b + 1] = vv
                T = 0
                x = 0
                y = 0
                while x < t or y < K:
                    if y >= K or (x < t and s_val[x] <= r_val[y]):
                        w_col[T] = s_col[x]
                        w_val[T] = s_val[x]
                        x += 1
                    else:
                        w_col[T] = r_col[y]
                        w_val[T] = r_val[y]
                        y += 1
                    T += 1
                _accumulate(w_val, w_col, T, mult, 1.0, O, H, support)
            r += 1

        cur = nxt

    return O, H, support
