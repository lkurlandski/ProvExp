"""
Tests for provenance.py.

The reference implementations below follow the definitions in the manuscript literally, using dense matrices.
"""

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import pytest

from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

from tests.strategies import boxmatrices
from tests.strategies import full_boxmatrices
from tests.strategies import nonoverlapping_boxmatrices
from tests.strategies import unambiguous_boxmatrices


SETTINGS = settings(max_examples=150, deadline=None)
POLICIES = st.sampled_from(["null", "uniform", "ignore"])


################################################################################
# Dense Reference Implementations
################################################################################


def reference_P(C: np.ndarray, empty: str) -> np.ndarray:
    m, n = C.shape
    s = C.sum(axis=0)
    P: np.ndarray = np.zeros((m + int(empty == "null"), n))
    for j in range(n):
        if s[j] > 1e-12 * max(s.max(), 0.0):
            P[:m, j] = C[:, j] / s[j]
        elif empty == "uniform":
            P[:, j] = 1.0 / m
        elif empty == "null":
            P[m, j] = 1.0
    return P


def reference_pushforward(P: np.ndarray, b: np.ndarray) -> np.ndarray:
    D = P.sum(axis=1)
    Dinv = np.diag(np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0))
    a: np.ndarray = P.T @ Dinv @ b
    return a


def reference_ambiguity(P: np.ndarray, included: np.ndarray) -> tuple[np.ndarray, float]:
    """H_j = -sum_i P_ij log P_ij and H, the mean of H_j over the included features."""
    m, n = P.shape
    H = np.zeros(n)
    for j in range(n):
        p = P[:, j][P[:, j] > 0]
        H[j] = -(p * np.log(p)).sum()
    return H, float(H[included].mean()) if included.any() else 0.0


def reference_M(P: np.ndarray) -> np.ndarray:
    """The pull-push matrix M = P^T D^+ P."""
    D = P.sum(axis=1)
    Dinv = np.diag(np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0))
    M: np.ndarray = P.T @ Dinv @ P
    return M


def reference_N(P: np.ndarray) -> np.ndarray:
    """The push-pull matrix N = P P^T D^+."""
    D = P.sum(axis=1)
    Dinv = np.diag(np.where(D > 0, 1.0 / np.where(D > 0, D, 1.0), 0.0))
    N: np.ndarray = P @ P.T @ Dinv
    return N


def reference_overlap(P: np.ndarray, included: np.ndarray) -> tuple[np.ndarray, float]:
    """O_j = 1 - M_jj and O, the mean of O_j over the included features."""
    O = 1.0 - np.diag(reference_M(P))
    return O, float(O[included].mean()) if included.any() else 0.0


def is_sigma_consistent(P: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Zero out the elements of b that influence no feature (manuscript, Definition 2)."""
    return np.where(P.sum(axis=1) > 0, b, 0.0)


################################################################################
# Normalization
################################################################################


@given(boxmatrices(), POLICIES)
@SETTINGS
def test_normalization(C: BoxMatrix, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    assert np.allclose(prov.to_dense(), reference_P(C.to_dense(), empty))
    prov.check_axioms()


def test_empty_policies() -> None:
    C = BoxMatrix((4, 3))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(1, 4, 2, 3, 2.0)

    uniform = Provenance(C, empty="uniform")
    assert uniform.is_empty.tolist() == [False, True, False]
    assert np.allclose(uniform.to_dense()[:, 1], 0.25)
    assert np.allclose(uniform.to_dense().sum(axis=0), 1.0)

    ignore = Provenance(C, empty="ignore")
    assert np.allclose(ignore.to_dense()[:, 1], 0.0)
    assert ignore.included.tolist() == [True, False, True]


def test_null_policy() -> None:
    C = BoxMatrix((4, 3))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(1, 4, 2, 3, 2.0)
    prov = Provenance(C, empty="null")
    assert prov.has_null
    assert prov.shape == (5, 3)
    P = prov.to_dense()
    assert np.array_equal(P[4], [0.0, 1.0, 0.0])
    assert np.allclose(P.sum(axis=0), 1.0)
    # The null element receives exactly the attribution of the empty features.
    b = prov.pullback(np.array([1.0, 5.0, -2.0]))
    assert b[4] == 5.0
    assert np.isclose(b.sum(), 4.0)
    # A problem-space explanation without a null entry is padded with zero.
    assert np.allclose(prov.pushforward(np.ones(4)), prov.pushforward(np.append(np.ones(4), 0.0)))
    # The summary statistics exclude the empty features.
    assert prov.included.tolist() == [True, False, True]


@given(boxmatrices())
@SETTINGS
def test_null_and_ignore_statistics_agree(C: BoxMatrix) -> None:
    """The null element does not enter the summary statistics."""
    null, ignore = Provenance(C, empty="null"), Provenance(C, empty="ignore")
    assert np.isclose(null.ambiguity().overall, ignore.ambiguity().overall)
    assert np.isclose(null.overlap().overall, ignore.overlap().overall)
    assert np.allclose(null.overlap().per_feature[null.included], ignore.overlap().per_feature[ignore.included])


def test_coverage_and_localizability() -> None:
    C = BoxMatrix((4, 4))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(1, 4, 2, 3, 2.0)
    prov = Provenance(C)
    assert prov.coverage == 0.5
    a = np.array([1.0, -3.0, -2.0, 4.0])
    assert prov.localizability(a) == 0.3
    # The null element's share of the pullback is the signed attribution of the unattributable features.
    assert prov.pullback(a)[-1] == 1.0
    assert prov.localizability(np.zeros(4)) == 1.0


@given(boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_uniform_is_null_spread(C: BoxMatrix, seed: int) -> None:
    """Pulling back with "uniform" is pulling back with "null" and then spreading the null share uniformly."""
    null = Provenance(C, empty="null")
    uniform = Provenance(C, empty="uniform")
    a = np.random.default_rng(seed).normal(size=null.num_features)
    b = null.pullback(a)
    assert np.allclose(uniform.pullback(a), b[:-1] + b[-1] / null.num_elements)


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_policies_agree_without_empty_features(C: BoxMatrix, seed: int) -> None:
    a = np.random.default_rng(seed).normal(size=C.shape[1])
    b_null = Provenance(C, empty="null").pullback(a)
    assert b_null[-1] == 0.0
    for empty in ("uniform", "ignore"):
        assert np.allclose(Provenance(C, empty=empty).pullback(a), b_null[:-1])


def test_negative_contributions() -> None:
    C = BoxMatrix((2, 1))
    C.add_boxes(0, 2, 0, 1, -1.0)
    with pytest.raises(ValueError):
        Provenance(C)


def test_feature_names() -> None:
    C = BoxMatrix((2, 2))
    assert Provenance(C, feature_names=["a", "b"]).feature_names == ["a", "b"]
    with pytest.raises(ValueError):
        Provenance(C, feature_names=["a"])


def test_invalid_policy() -> None:
    with pytest.raises(ValueError):
        Provenance(BoxMatrix((2, 2)), empty="exclude")  # type: ignore[arg-type]


################################################################################
# Feature Subsets
################################################################################


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_select(C: BoxMatrix, empty: str, seed: int) -> None:
    """The provenance of a subset is the subset's columns of P, and its statistics are those of P_S in isolation."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    rng = np.random.default_rng(seed)
    S = np.flatnonzero(rng.random(prov.num_features) < rng.random())
    sub = prov.select(S)
    P = sub.to_dense()
    assert sub.shape == (prov.num_rows, S.size)
    assert np.allclose(P, prov.to_dense()[:, S])
    assert np.allclose(sub.ambiguity().per_feature, prov.ambiguity().per_feature[S])
    O, O_ = reference_overlap(P, sub.included)
    overlap = sub.overlap()
    assert np.allclose(overlap.per_feature, O)
    assert np.isclose(overlap.overall, O_)
    a = rng.normal(size=S.size)
    assert np.allclose(sub.pullback(a), P @ a)


@given(boxmatrices(), POLICIES)
@SETTINGS
def test_select_all(C: BoxMatrix, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    sub = prov.select(np.arange(prov.num_features))
    assert np.isclose(sub.ambiguity().overall, prov.ambiguity().overall)
    assert np.isclose(sub.overlap().overall, prov.overlap().overall)
    assert sub.coverage == prov.coverage


class TestSelect:

    @staticmethod
    def provenance() -> Provenance:
        C = BoxMatrix((10, 4))
        C.add_boxes([0, 2, 5], [6, 8, 10], [0, 1, 2], [1, 2, 3])
        return Provenance(C, feature_names=["a:x", "a:y", "b:x", "b:y"])

    @pytest.mark.parametrize("features", [[2, 0], np.array([True, False, True, False]), ["b:x", "a:x"]])
    def test_forms(self, features: object) -> None:
        prov = self.provenance()
        sub = prov.select(features)  # type: ignore[arg-type]
        assert sub.feature_names == ["a:x", "b:x"]
        assert np.array_equal(sub.to_dense(), prov.to_dense()[:, [0, 2]])

    def test_empty_features_go_to_the_null_element(self) -> None:
        sub = self.provenance().select([1, 3])
        assert sub.is_empty.tolist() == [False, True]
        assert np.array_equal(sub.to_dense()[-1], [0.0, 1.0])
        assert sub.coverage == 0.5

    def test_empty_selection(self) -> None:
        sub = self.provenance().select([])
        assert sub.shape == (11, 0)
        assert sub.overlap().overall == 0.0
        assert sub.ambiguity().overall == 0.0

    @pytest.mark.parametrize("features", [[0, 0], [4], [-1], ["c:z"], np.array([True, False])])
    def test_invalid(self, features: object) -> None:
        with pytest.raises((ValueError, IndexError)):
            self.provenance().select(features)  # type: ignore[arg-type]

    def test_names_require_feature_names(self) -> None:
        with pytest.raises(ValueError):
            Provenance(BoxMatrix((2, 2))).select(["a:x"])

    def test_non_integer(self) -> None:
        with pytest.raises(TypeError):
            self.provenance().select([0.0, 1.0])


################################################################################
# Explanation Transfers
################################################################################


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_pullback(C: BoxMatrix, empty: str, seed: int) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    a = np.random.default_rng(seed).normal(size=prov.num_features)
    assert np.allclose(prov.pullback(a), prov.to_dense() @ a)


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_pushforward(C: BoxMatrix, empty: str, seed: int) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    b = np.random.default_rng(seed).normal(size=prov.num_rows)
    assert np.allclose(prov.pushforward(b), reference_pushforward(prov.to_dense(), b))


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_cyclic_operators(C: BoxMatrix, empty: str, seed: int) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    rng = np.random.default_rng(seed)
    a = rng.normal(size=prov.num_features)
    b = rng.normal(size=prov.num_rows)
    P = prov.to_dense()
    assert np.allclose(prov.pull_push(a), reference_pushforward(P, P @ a))
    assert np.allclose(prov.push_pull(b), P @ reference_pushforward(P, b))
    assert np.isclose(prov.pull_push_error(a), np.abs(reference_pushforward(P, P @ a) - a).sum())
    assert np.isclose(prov.push_pull_error(b), np.abs(P @ reference_pushforward(P, b) - b).sum())


def test_transfer_shapes() -> None:
    prov = Provenance(BoxMatrix((3, 2)))
    with pytest.raises(ValueError):
        prov.pullback(np.ones(3))
    with pytest.raises(ValueError):
        prov.pushforward(np.ones(2))


################################################################################
# Summary Statistics
################################################################################


@given(boxmatrices(), POLICIES)
@SETTINGS
def test_ambiguity(C: BoxMatrix, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    P = prov.to_dense()
    H, H_ = reference_ambiguity(P, prov.included)
    ambiguity = prov.ambiguity()
    assert np.allclose(ambiguity.per_feature, H)
    assert np.allclose(ambiguity.effective_support, np.exp(H))
    assert np.isclose(ambiguity.overall, H_)
    support = (P > 0).sum(axis=0)
    assert np.array_equal(ambiguity.support, support)
    # The effective support lies between 1 and the support.
    nonempty = support > 0
    assert np.all(ambiguity.effective_support[nonempty] >= 1 - 1e-9)
    assert np.all(ambiguity.effective_support[nonempty] <= support[nonempty] * (1 + 1e-9))


@given(boxmatrices(), POLICIES)
@SETTINGS
def test_overlap(C: BoxMatrix, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    O, O_ = reference_overlap(prov.to_dense(), prov.included)
    overlap = prov.overlap()
    assert np.allclose(overlap.per_feature, O)
    assert np.isclose(overlap.overall, O_)


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_round_trip_matrices(C: BoxMatrix, empty: str, seed: int) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    P = prov.to_dense()
    M = prov.pull_push_matrix()
    assert np.allclose(M, reference_M(P))
    assert np.allclose(np.diag(M), 1.0 - prov.overlap().per_feature)
    a = np.random.default_rng(seed).normal(size=prov.num_features)
    assert np.allclose(M @ a, prov.pull_push(a))
    assert np.allclose(prov.push_pull_diagonal(), np.diag(reference_N(P)))


def test_round_trip_matrix_size_limit() -> None:
    C = BoxMatrix((100, 2))
    C.add_boxes(0, 100, 0, 2, 1.0)
    with pytest.raises(ValueError):
        Provenance(C).pull_push_matrix(max_nnz=10)


def test_statistics_with_collisions() -> None:
    """Keyed entries that land on columns covered by constant boxes."""
    C = BoxMatrix((6, 3))
    C.add_boxes(0, 6, 0, 2, 1.0)
    C.add_boxes(2, 5, 2, 3, 3.0)
    C.add_keyed_boxes(0, 6, 0, C.add_key(np.array([0, 1, 2, 2, 0, 1], dtype=np.uint8)), 0.5)
    C.add_keyed_boxes(1, 4, 1, C.add_key(np.array([0, 1, 1, 0, 0, 0], dtype=np.uint8)), 2.0)
    prov = Provenance(C)
    P = prov.to_dense()
    O, _ = reference_overlap(P, prov.included)
    H, _ = reference_ambiguity(P, prov.included)
    assert np.allclose(prov.overlap().per_feature, O)
    assert np.allclose(prov.ambiguity().per_feature, H)
    assert np.allclose(prov.push_pull_diagonal(), np.diag(reference_N(P)))


def test_overlap_example() -> None:
    # Feature 0 draws on elements {0, 1}, feature 1 on {1, 2}, feature 2 on {3}. Element 1 feeds features 0 and 1, so a
    # round trip moves half of the attribution on element 1, i.e., a quarter of feature 0's, to feature 1.
    C = BoxMatrix((4, 3))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(1, 3, 1, 2, 1.0)
    C.add_boxes(3, 4, 2, 3, 1.0)
    prov = Provenance(C)
    assert np.allclose(prov.overlap().per_feature, [0.25, 0.25, 0.0])
    assert np.allclose(prov.pull_push_matrix(), [[0.75, 0.25, 0.0], [0.25, 0.75, 0.0], [0.0, 0.0, 1.0]])
    assert np.allclose(prov.push_pull_diagonal(), [0.5, 0.5, 0.5, 1.0, 0.0])
    assert np.allclose(prov.ambiguity().effective_support, [2.0, 2.0, 1.0])


################################################################################
# Propositions (manuscript, Appendices B and C)
################################################################################


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_soundness_of_pullback(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    P = prov.to_dense()
    rng = np.random.default_rng(seed)
    a = rng.normal(size=prov.num_features) * (rng.random(prov.num_features) < 0.5)
    b = prov.pullback(a)
    for i in range(prov.num_elements):
        if np.all(P[i, a != 0] == 0):
            assert b[i] == 0


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_completeness_of_pullback(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    a = np.random.default_rng(seed).normal(size=prov.num_features)
    assert np.isclose(prov.pullback(a).sum(), a.sum())


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_independence_of_pullback(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    P = prov.to_dense()
    rng = np.random.default_rng(seed)
    a = rng.normal(size=prov.num_features) * (rng.random(prov.num_features) < 0.3)
    b = prov.pullback(a)
    for i in range(prov.num_elements):
        S = np.flatnonzero((a != 0) & (P[i] > 0))
        if S.size == 1:
            assert np.isclose(b[i], P[i, S[0]] * a[S[0]])


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_soundness_of_pushforward(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    P = prov.to_dense()
    rng = np.random.default_rng(seed)
    b = rng.normal(size=prov.num_rows) * (rng.random(prov.num_rows) < 0.5)
    a = prov.pushforward(b)
    for j in range(prov.num_features):
        if np.all(P[b != 0, j] == 0):
            assert a[j] == 0


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_completeness_of_pushforward(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    b = is_sigma_consistent(prov.to_dense(), np.random.default_rng(seed).normal(size=prov.num_rows))
    assert np.isclose(prov.pushforward(b).sum(), b.sum())


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_independence_of_pushforward(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    P = prov.to_dense()
    D = P.sum(axis=1)
    rng = np.random.default_rng(seed)
    b = rng.normal(size=prov.num_rows) * (rng.random(prov.num_rows) < 0.3)
    a = prov.pushforward(b)
    for j in range(prov.num_features):
        T = np.flatnonzero((b != 0) & (P[:, j] > 0))
        if T.size == 1:
            i = T[0]
            assert np.isclose(a[j], P[i, j] * b[i] / D[i])


################################################################################
# Round Trips (manuscript, Section 3)
################################################################################


@given(boxmatrices(), st.sampled_from(["null", "uniform"]))
@SETTINGS
def test_round_trip_structure(C: BoxMatrix, empty: str) -> None:
    """
    M is symmetric, nonnegative, doubly stochastic, with eigenvalues in [0, 1] (manuscript, Proposition Round Trips).
    It also shares its nonzero eigenvalues with N, which the manuscript does not state (docs/plan_e2.md, decision 2).
    """
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    if prov.num_features == 0:
        return
    M = prov.pull_push_matrix()
    assert np.allclose(M, M.T)
    assert np.all(M >= 0)
    assert np.allclose(M.sum(axis=0), 1.0)
    eigenvalues = np.linalg.eigvalsh(M)
    assert eigenvalues.min() >= -1e-9 and eigenvalues.max() <= 1 + 1e-9
    N = reference_N(prov.to_dense())
    nonzero_M = np.sort(eigenvalues[eigenvalues > 1e-7])
    nonzero_N = np.sort(np.linalg.eigvals(N).real)
    nonzero_N = nonzero_N[nonzero_N > 1e-7]
    assert nonzero_M.shape == nonzero_N.shape and np.allclose(nonzero_M, nonzero_N, atol=1e-6)


@given(st.one_of(full_boxmatrices(), nonoverlapping_boxmatrices(), boxmatrices()), POLICIES)
@SETTINGS
def test_overlap_vanishes_iff_exclusive(C: BoxMatrix, empty: str) -> None:
    """O_j = 0 if and only if every element of feature j's provenance contributes to no other feature."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    P = prov.to_dense()
    O = prov.overlap().per_feature
    for j in np.flatnonzero(P.sum(axis=0) > 0):
        rows = P[:, j] > 0
        exclusive = bool(np.all((P[rows] > 0).sum(axis=1) == 1))
        assert bool(np.isclose(O[j], 0.0, atol=1e-9)) == exclusive


@given(st.one_of(full_boxmatrices(), unambiguous_boxmatrices(), boxmatrices()), POLICIES)
@SETTINGS
def test_push_pull_diagonal_is_one_iff_one_hot(C: BoxMatrix, empty: str) -> None:
    """N_ii = 1 if and only if every feature that element i influences is one-hot on i."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    P = prov.to_dense()
    N = prov.push_pull_diagonal()
    for i in np.flatnonzero(P.sum(axis=1) > 0):
        cols = P[i] > 0
        one_hot = bool(np.all((P[:, cols] > 0).sum(axis=0) == 1))
        assert bool(np.isclose(N[i], 1.0, atol=1e-9)) == one_hot


@given(boxmatrices(), POLICIES, st.integers(0, 2 ** 16))
@SETTINGS
def test_round_trip_bounds(C: BoxMatrix, empty: str, seed: int) -> None:
    """||a - Ma||_1 <= 2 sum_j |a_j| O_j and ||b - Nb||_1 <= 2 sum_i |b_i| (1 - N_ii), with equality for one-hot inputs."""
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    P = prov.to_dense()
    rng = np.random.default_rng(seed)
    O = prov.overlap().per_feature
    N = prov.push_pull_diagonal()
    a = rng.normal(size=prov.num_features) * (rng.random(prov.num_features) < 0.7)
    b = is_sigma_consistent(P, rng.normal(size=prov.num_rows))
    assert prov.pull_push_error(a) <= 2 * (np.abs(a) * O).sum() + 1e-9
    assert prov.push_pull_error(b) <= 2 * (np.abs(b) * (1 - N)).sum() + 1e-9
    for j in range(prov.num_features):
        if P[:, j].sum() > 0:
            assert np.isclose(prov.pull_push_error(np.eye(prov.num_features)[j]), 2 * O[j])
    for i in np.flatnonzero(P.sum(axis=1) > 0):
        assert np.isclose(prov.push_pull_error(np.eye(prov.num_rows)[i]), 2 * (1 - N[i]))


@given(st.one_of(full_boxmatrices(), nonoverlapping_boxmatrices(), boxmatrices()))
@SETTINGS
def test_perfect_pull_push(C: BoxMatrix) -> None:
    """The pull-push reconstruction of explanations of the attributable features is perfect if and only if O = 0."""
    prov = Provenance(C)
    perfect = all(prov.pull_push_error(e) < 1e-9 for e in np.eye(prov.num_features)[prov.included])
    assert perfect == bool(np.isclose(prov.overlap().overall, 0.0, atol=1e-9))


@given(st.one_of(full_boxmatrices(), unambiguous_boxmatrices(), boxmatrices()))
@SETTINGS
def test_perfect_push_pull(C: BoxMatrix) -> None:
    """The push-pull reconstruction is perfect for all sigma-consistent b if and only if H = 0."""
    prov = Provenance(C)
    P = prov.to_dense()
    basis = [is_sigma_consistent(P, e) for e in np.eye(prov.num_rows)]
    perfect = all(prov.push_pull_error(e) < 1e-9 for e in basis)
    assert perfect == bool(np.isclose(prov.ambiguity().overall, 0.0, atol=1e-9))
