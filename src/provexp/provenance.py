"""
Explanation provenance and the operators that transfer explanations between the problem-space and the feature-space.

Notation follows the manuscript: a problem-space object z has m elements (bytes), its feature-space representation x
has n features, and the provenance matrix P (m, n) is nonnegative with columns that sum to one. P[i, j] is the
proportion of feature j's provenance attributable to element i.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import Literal
from typing import NamedTuple
from typing import Optional

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


# NOTE (Axiom 3): what to do with a feature to which no element contributes is an open question. Examples include
# features that do not depend on any particular bytes (e.g., whether a file parsed as a PE) and features whose value is
# zero because the thing they count is absent (e.g., an empty hash bucket). Feature sets never fabricate provenance for
# such features, so their columns of the raw contributions are empty, and this policy decides how to treat them when
# normalizing. Changing the policy does not require recomputing any provenance.
#   - "uniform": spread the feature's provenance uniformly over all elements. Satisfies Axioms 1 and 2, but
#       contradicts Axiom 3 because every element is said to influence the feature.
#   - "ignore": leave the column empty. Pullback and pushforward ignore the feature and the summary statistics exclude
#       it. Satisfies Axioms 1 and 3, but the column does not sum to one (Axiom 2). This is equivalent to the
#       manuscript's recommendation of excluding the feature from P entirely, without changing the feature indices.
EmptyPolicy = Literal["uniform", "ignore"]


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

    Args:
        contributions: The raw contributions C as a BoxMatrix of shape (m, n).
        feature_names: Optionally, the name of each feature.
        empty: How to treat features with no contributions. See `EmptyPolicy`.
    """

    def __init__(
        self,
        contributions: BoxMatrix,
        feature_names: Optional[Sequence[str]] = None,
        empty: EmptyPolicy = "uniform",
    ) -> None:
        if empty not in ("uniform", "ignore"):
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
    def shape(self) -> tuple[int, int]:
        return self.contributions.shape

    @property
    def num_elements(self) -> int:
        return self.contributions.shape[0]

    @property
    def num_features(self) -> int:
        return self.contributions.shape[1]

    @property
    def _uniform(self) -> bool:
        return self.empty == "uniform" and self.num_elements > 0

    # ---------- Products with P ----------

    def matvec(self, a: npt.ArrayLike) -> FloatArray:
        """Compute P @ a for a vector of shape (n,)."""
        a_ = np.asarray(a, dtype=np.float64)
        b = self.contributions.matvec(a_ * self.scale)
        if self._uniform:
            b += a_[self.is_empty].sum() / self.num_elements
        return b

    def rmatvec(self, b: npt.ArrayLike) -> FloatArray:
        """Compute P.T @ b for a vector of shape (m,)."""
        b_ = np.asarray(b, dtype=np.float64)
        a = self.contributions.rmatvec(b_) * self.scale
        if self._uniform:
            a[self.is_empty] = b_.sum() / self.num_elements
        return a

    def rowsum(self) -> FloatArray:
        """Compute D, the row sums of P, shape (m,)."""
        return self.matvec(np.ones(self.num_features))

    def to_dense(self, max_elements: int = 2 ** 26) -> FloatArray:
        """Materialize P as a dense array (only sensible for small objects)."""
        P = self.contributions.to_dense(max_elements) * self.scale
        if self._uniform:
            P[:, self.is_empty] = 1.0 / self.num_elements
        return P

    def pieces(self) -> Pieces:
        """The canonical form of P (see `BoxMatrix.pieces`), including uniform columns if applicable."""
        pieces = self.contributions.pieces(colscale=self.scale)
        if not self._uniform or not np.any(self.is_empty):
            return pieces
        cols = np.flatnonzero(self.is_empty).astype(np.int64)
        col = np.concatenate([pieces.col, cols])
        lo = np.concatenate([pieces.lo, np.zeros_like(cols)])
        hi = np.concatenate([pieces.hi, np.full_like(cols, self.num_elements)])
        val = np.concatenate([pieces.val, np.full(cols.shape, 1.0 / self.num_elements)])
        order = np.lexsort((lo, col))
        return Pieces(col[order], lo[order], hi[order], val[order])

    # ---------- Explanation Transfers ----------

    def pullback(self, a: npt.ArrayLike) -> FloatArray:
        """
        Pull a feature-space explanation back into the problem-space, i.e., tau(a) = P a (manuscript, Definition 4).

        Args:
            a: A feature-space explanation, shape (n,).

        Returns:
            A problem-space explanation, shape (m,).
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
            b: A problem-space explanation, shape (m,).

        Returns:
            A feature-space explanation, shape (n,).
        """
        b_ = np.asarray(b, dtype=np.float64)
        if b_.shape != (self.num_elements,):
            raise ValueError(f"Expected an explanation of shape ({self.num_elements},). Got {b_.shape}.")
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
        return float(np.linalg.norm(self.push_pull(b) - np.asarray(b, dtype=np.float64)))

    # ---------- Summary Statistics ----------

    @property
    def included(self) -> npt.NDArray[np.bool_]:
        """Whether each feature participates in the summary statistics (see `EmptyPolicy`)."""
        if self.empty == "ignore":
            return ~self.is_empty
        return np.ones(self.num_features, dtype=np.bool_)

    def ambiguity(self) -> Ambiguity:
        """
        Compute the provenance ambiguity exactly from the canonical form of P.
        """
        n = self.num_features
        pieces = self.pieces()
        length = (pieces.hi - pieces.lo).astype(np.float64)

        support = np.bincount(pieces.col, weights=length, minlength=n).astype(np.int64)
        H = np.bincount(pieces.col, weights=-length * pieces.val * np.log(pieces.val), minlength=n)
        H = np.maximum(H, 0.0)

        normalized = np.zeros(n, dtype=np.float64)
        many = support > 1
        normalized[many] = H[many] / np.log(support[many])
        normalized = np.clip(normalized, 0.0, 1.0)

        included = self.included
        overall = float(normalized[included].mean()) if np.any(included) else 0.0
        return Ambiguity(H, normalized, overall, support, included)

    def overlap(self, budget: int = 2 ** 24) -> Overlap:
        """
        Compute the provenance overlap exactly from the canonical form of P.

        The rows are partitioned into elementary segments, within which every column of P is constant. Within a
        segment where t features have nonzero values sorted q_1 <= ... <= q_t, the feature of rank r shares
        sum_{s < r} q_s + q_r * (t - r) mass with the other features, per row. Summing this over the segments gives
        O_j without enumerating the O(n^2) pairs of features.

        Args:
            budget: The approximate number of (segment, feature) pairs to process at a time, which bounds memory.
        """
        n = self.num_features
        included = self.included
        pieces = self.pieces()
        keep = included[pieces.col]
        col, lo, hi, val = pieces.col[keep], pieces.lo[keep], pieces.hi[keep], pieces.val[keep]

        O = np.zeros(n, dtype=np.float64)
        if col.size > 0:
            bounds = np.unique(np.concatenate([lo, hi]))
            seglen = np.diff(bounds).astype(np.float64)
            slo = np.searchsorted(bounds, lo)
            shi = np.searchsorted(bounds, hi)
            for a, b in _segment_chunks(slo, shi, bounds.size - 1, budget):
                mask = (slo < b) & (shi > a)
                which, seg = expand_ranges(np.maximum(slo[mask], a), np.minimum(shi[mask], b))
                O += _overlap_within_segments(seg, col[mask][which], val[mask][which], seglen, n)

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
        pieces = self.pieces()
        if np.any(pieces.val < 0):
            raise ValueError("Axiom 1 (Nonnegativity) is violated.")
        colsum = np.bincount(pieces.col, weights=(pieces.hi - pieces.lo) * pieces.val, minlength=self.num_features)
        expected = np.where(self.is_empty & (self.empty == "ignore"), 0.0, 1.0)
        if self.num_elements > 0 and not np.allclose(colsum, expected, atol=atol, rtol=0.0):
            bad = np.flatnonzero(~np.isclose(colsum, expected, atol=atol, rtol=0.0))
            raise ValueError(f"Axiom 2 (Normalization) is violated for features {bad[:10].tolist()}.")


################################################################################
# Overlap Helpers
################################################################################


def _segment_chunks(slo: IntArray, shi: IntArray, nseg: int, budget: int) -> list[tuple[int, int]]:
    """
    Partition the segments [0, nseg) into contiguous chunks that each contain roughly `budget` (segment, feature)
    pairs, where each piece covers the segments [slo, shi).
    """
    # Number of pieces covering each segment, via a difference array.
    d = np.bincount(slo, minlength=nseg + 1) - np.bincount(shi, minlength=nseg + 1)
    active = np.cumsum(d)[:nseg]
    cumulative = np.cumsum(active)
    chunks = []
    a = 0
    while a < nseg:
        consumed = cumulative[a - 1] if a > 0 else 0
        b = int(np.searchsorted(cumulative, consumed + budget, side="right"))
        b = min(max(b, a + 1), nseg)
        chunks.append((a, b))
        a = b
    return chunks


def _overlap_within_segments(seg: IntArray, col: IntArray, val: FloatArray, seglen: FloatArray, n: int) -> FloatArray:
    """
    Accumulate each feature's shared provenance mass within the given (segment, feature, value) triples.
    """
    if seg.size == 0:
        return np.zeros(n, dtype=np.float64)

    order = np.lexsort((val, seg))
    seg, col, val = seg[order], col[order], val[order]

    first = np.concatenate([[True], seg[1:] != seg[:-1]])
    start = np.maximum.accumulate(np.where(first, np.arange(first.size), 0))
    count = np.bincount(np.cumsum(first) - 1)[np.cumsum(first) - 1]
    rank = np.arange(seg.size) - start

    csum = np.cumsum(val)
    smaller = csum - val - (csum[start] - val[start])  # Sum of the values ranked below within the segment.
    shared = smaller + val * (count - 1 - rank)

    return np.bincount(col, weights=shared * seglen[seg], minlength=n)
