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

import numpy as np
from numpy import typing as npt
from scipy import sparse

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
#       explanation is the attribution that cannot be localized within the input. The summary statistics exclude empty
#       features: their provenance is one-hot on the null element, so they are trivially unambiguous and overlap each
#       other completely, which says nothing about localization within the input and only drags the averages.
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
    Provenance ambiguity (manuscript, Definition Provenance Ambiguity): how widely each feature's provenance is spread.

    Attributes:
        per_feature: H_j, the entropy of column j of P (in nats), for each feature, shape (n,).
        effective_support: exp(H_j), the number of elements over which feature j's provenance is effectively spread
            (between 1 and |A_j|), shape (n,).
        overall: H, the mean of H_j over the included features.
        support: |A_j|, the number of elements with nonzero provenance for each feature, shape (n,).
        included: Whether each feature is included in the overall statistic, shape (n,).
    """

    per_feature: FloatArray
    effective_support: FloatArray
    overall: float
    support: IntArray
    included: npt.NDArray[np.bool_]


class Overlap(NamedTuple):
    """
    Provenance overlap (manuscript, Definition Provenance Overlap): how much each feature shares its elements with
    other features.

    O_j = 1 - sum_i P_ij^2 / D_ii is the share of feature j's attribution that the pull-push round trip moves to other
    features, i.e., one minus the j-th diagonal entry of the pull-push matrix (see `Provenance.pull_push_matrix`).
    O_j = 0 if and only if no element of feature j's provenance contributes to another feature. A feature without
    provenance has O_j = 1 under "ignore" (nothing comes back) and O_j = 1 - 1/|U| under "null".

    Attributes:
        per_feature: O_j for each feature, shape (n,).
        overall: O, the mean of O_j over the included features.
        included: Whether each feature is included in the overall statistic, shape (n,).
    """

    per_feature: FloatArray
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
        Pull a feature-space explanation back into the problem-space, i.e., tau(a) = P a (manuscript, Definition
        Pullback).

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
        Push a problem-space explanation forward into the feature-space, i.e., psi(b) = P^T D^+ b (manuscript,
        Definition Pushforward). This is the Bayesian inverse of the pullback under a uniform prior over the features:
        element i passes its attribution to feature j in proportion to P_ij / D_ii.

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
        """The pull-push cyclic operator, psi(tau(a)) (manuscript, Definition Cyclic Explanation Transfers)."""
        return self.pushforward(self.pullback(a))

    def push_pull(self, b: npt.ArrayLike) -> FloatArray:
        """The push-pull cyclic operator, tau(psi(b)) (manuscript, Definition Cyclic Explanation Transfers)."""
        return self.pullback(self.pushforward(b))

    def pull_push_error(self, a: npt.ArrayLike) -> float:
        """The pull-push reconstruction error, ||psi(tau(a)) - a||_1 (manuscript, Definition Cyclic Reconstruction Error)."""
        return float(np.abs(self.pull_push(a) - np.asarray(a, dtype=np.float64)).sum())

    def push_pull_error(self, b: npt.ArrayLike) -> float:
        """The push-pull reconstruction error, ||tau(psi(b)) - b||_1 (manuscript, Definition Cyclic Reconstruction Error)."""
        b_ = np.asarray(b, dtype=np.float64)
        if self.has_null and b_.shape == (self.num_elements,):
            b_ = np.append(b_, 0.0)
        return float(np.abs(self.push_pull(b_) - b_).sum())

    # ---------- Summary Statistics ----------

    @property
    def included(self) -> npt.NDArray[np.bool_]:
        """Whether each feature participates in the summary statistics, i.e., is attributable (see `EmptyPolicy`)."""
        if self.empty in ("null", "ignore"):
            return ~self.is_empty
        return np.ones(self.num_features, dtype=np.bool_)

    @cached_property
    def _pieces(self) -> Pieces:
        """The canonical form of P, shared by the statistics."""
        return self.pieces()

    @cached_property
    def _rows(self) -> tuple[FloatArray, FloatArray, npt.NDArray[np.bool_], FloatArray]:
        """
        Row quantities of P from its canonical pieces: D (the row sums), sum_j P_ij^2, whether each row is live
        (D_ii > 0), and D^+.
        """
        pieces = self._pieces
        R = self.num_rows

        def per_row(weights: FloatArray) -> FloatArray:
            diff = np.bincount(pieces.lo, weights, minlength=R + 1) - np.bincount(pieces.hi, weights, minlength=R + 1)
            return np.cumsum(diff)[:R]

        # Counting the pieces that cover each row is exact in floating point, so liveness has no rounding residue.
        live = per_row(np.ones(pieces.col.shape)) > 0.5
        D = np.where(live, per_row(pieces.val), 0.0)
        squares = np.where(live, per_row(pieces.val ** 2), 0.0)
        Dinv = np.where(live, 1.0 / np.where(live, D, 1.0), 0.0)
        return D, squares, live, Dinv

    @cached_property
    def _columns(self) -> tuple[FloatArray, IntArray, FloatArray]:
        """The entropy H_j, the support |A_j|, and the pull-push diagonal sum_i P_ij^2 / D_ii of every column."""
        pieces = self._pieces
        n = self.num_features
        length = (pieces.hi - pieces.lo).astype(np.float64)
        H = np.bincount(pieces.col, weights=-length * pieces.val * np.log(pieces.val), minlength=n)
        support = np.bincount(pieces.col, weights=length, minlength=n).round().astype(np.int64)
        # The sum of D^+ over each piece, summed directly: differences of a prefix sum lose precision on long inputs.
        Dinv = np.append(self._rows[3], 0.0)
        bounds = np.stack([pieces.lo, pieces.hi], axis=1).ravel()
        per_piece = np.add.reduceat(Dinv, bounds)[::2] if bounds.size else np.zeros(0)
        diagonal = np.bincount(pieces.col, weights=pieces.val ** 2 * per_piece, minlength=n)
        return np.maximum(H, 0.0), support, np.clip(diagonal, 0.0, 1.0)

    @property
    def coverage(self) -> float:
        """
        The provenance coverage, i.e., the fraction of features attributable to some element (manuscript, Definition
        Provenance Coverage).
        """
        return float((~self.is_empty).mean()) if self.num_features > 0 else 0.0

    def localizability(self, a: npt.ArrayLike) -> float:
        """
        The localizability of a feature-space explanation, i.e., the fraction of its attribution magnitude on
        attributable features, which the pullback places on elements rather than the null element.

        This is an evaluation quantity, not part of the framework: it depends on the explanation, not only on P. The
        framework's counterpart is the null element's entry of the pullback (manuscript, Definition Pullback).
        """
        a_ = np.abs(np.asarray(a, dtype=np.float64))
        if a_.shape != (self.num_features,):
            raise ValueError(f"Expected an explanation of shape ({self.num_features},). Got {a_.shape}.")
        total = a_.sum()
        return float(a_[~self.is_empty].sum() / total) if total > 0 else 1.0

    def ambiguity(self) -> Ambiguity:
        """
        Compute the provenance ambiguity exactly: H_j = -sum_i P_ij log P_ij, its effective support exp(H_j), and the
        mean H over the included features.
        """
        H, support, _ = self._columns
        included = self.included
        overall = float(H[included].mean()) if np.any(included) else 0.0
        return Ambiguity(H, np.exp(H), overall, support, included)

    def overlap(self) -> Overlap:
        """
        Compute the provenance overlap exactly: O_j = 1 - sum_i P_ij^2 / D_ii, and the mean O over the included
        features. The diagonal needs only the sum of D^+ over each constant piece of a column.
        """
        O = 1.0 - self._columns[2]
        included = self.included
        overall = float(O[included].mean()) if np.any(included) else 0.0
        return Overlap(O, overall, included)

    def push_pull_diagonal(self) -> FloatArray:
        """
        The diagonal of the push-pull matrix N = P P^T D^+, N_ii = sum_j P_ij^2 / D_ii, shape (num_rows,): the share of
        element i's attribution that the push-pull round trip returns to it (0 for elements that influence no
        feature). N_ii = 1 if and only if every feature that element i influences comes from element i alone.
        """
        D, squares, live, _ = self._rows
        return np.where(live, np.clip(squares / np.where(live, D, 1.0), 0.0, 1.0), 0.0)

    def pull_push_matrix(self, max_nnz: int = 2 ** 28) -> FloatArray:
        """
        The pull-push matrix M = P^T D^+ P, shape (n, n), so that pull_push(a) = M a. M_kj is the share of feature j's
        attribution that the round trip lands on feature k, and M_jj = 1 - O_j. M is symmetric and, unless a feature
        is ignored, doubly stochastic (manuscript, Proposition Round Trips).

        Args:
            max_nnz: Refuse to expand P into more than this many nonzero entries.
        """
        pieces = self._pieces
        nnz = int((pieces.hi - pieces.lo).sum())
        if nnz > max_nnz:
            raise ValueError(f"Refusing to expand {nnz} > {max_nnz} entries.")
        Dinv = self._rows[3]
        which, rows = expand_ranges(pieces.lo, pieces.hi)
        P = sparse.csr_array((pieces.val[which], (rows, pieces.col[which])), shape=self.shape)
        M = (P.T @ (P * Dinv[:, None])).toarray()
        return np.asarray(0.5 * (M + M.T), dtype=np.float64)

    # ---------- Validation ----------

    def check_axioms(self, atol: float = 1e-9) -> None:
        """
        Check the axioms of explanation provenance that can be checked numerically (manuscript, Definition Explanation Provenance).

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
