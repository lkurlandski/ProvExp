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


def reference_ambiguity(P: np.ndarray, included: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    m, n = P.shape
    H = np.zeros(n)
    Hn = np.zeros(n)
    for j in range(n):
        p = P[:, j][P[:, j] > 0]
        H[j] = -(p * np.log(p)).sum()
        Hn[j] = H[j] / np.log(p.size) if p.size > 1 else 0.0
    return H, Hn, float(Hn[included].mean()) if included.any() else 0.0


def reference_overlap(P: np.ndarray, included: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    m, n = P.shape
    O = np.zeros(n)
    for j in range(n):
        for k in range(n):
            if j != k and included[j] and included[k]:
                O[j] += np.minimum(P[:, j], P[:, k]).sum()
    nincluded = int(included.sum())
    On = O / (nincluded - 1) if nincluded > 1 else np.zeros(n)
    return O, On, float(On[included].mean()) if nincluded > 0 else 0.0


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
    assert np.isclose(prov.pull_push_error(a), np.linalg.norm(reference_pushforward(P, P @ a) - a))
    assert np.isclose(prov.push_pull_error(b), np.linalg.norm(P @ reference_pushforward(P, b) - b))


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
    H, Hn, H_ = reference_ambiguity(prov.to_dense(), prov.included)
    ambiguity = prov.ambiguity()
    assert np.allclose(ambiguity.per_feature, H)
    assert np.allclose(ambiguity.normalized, Hn)
    assert np.isclose(ambiguity.overall, H_)
    assert np.array_equal(ambiguity.support, (prov.to_dense() > 0).sum(axis=0))


@given(boxmatrices(), POLICIES)
@SETTINGS
def test_overlap(C: BoxMatrix, empty: str) -> None:
    prov = Provenance(C, empty=empty)  # type: ignore[arg-type]
    O, On, O_ = reference_overlap(prov.to_dense(), prov.included)
    overlap = prov.overlap()
    assert np.allclose(overlap.per_feature, O)
    assert np.allclose(overlap.normalized, On)
    assert np.isclose(overlap.overall, O_)


def test_statistics_with_collisions() -> None:
    """Keyed entries that land on columns covered by constant boxes (the kernel's slow path)."""
    C = BoxMatrix((6, 3))
    C.add_boxes(0, 6, 0, 2, 1.0)
    C.add_boxes(2, 5, 2, 3, 3.0)
    C.add_keyed_boxes(0, 6, 0, C.add_key(np.array([0, 1, 2, 2, 0, 1], dtype=np.uint8)), 0.5)
    C.add_keyed_boxes(1, 4, 1, C.add_key(np.array([0, 1, 1, 0, 0, 0], dtype=np.uint8)), 2.0)
    prov = Provenance(C)
    P = prov.to_dense()
    O, _, _ = reference_overlap(P, prov.included)
    H, _, _ = reference_ambiguity(P, prov.included)
    assert np.allclose(prov.overlap().per_feature, O)
    assert np.allclose(prov.ambiguity().per_feature, H)


def test_overlap_example() -> None:
    # Feature 0 draws on elements {0, 1}, feature 1 on {1, 2}, feature 2 on {3}.
    C = BoxMatrix((4, 3))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(1, 3, 1, 2, 1.0)
    C.add_boxes(3, 4, 2, 3, 1.0)
    overlap = Provenance(C).overlap()
    assert np.allclose(overlap.per_feature, [0.5, 0.5, 0.0])
    assert np.allclose(overlap.normalized, [0.25, 0.25, 0.0])


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
    b = rng.normal(size=prov.num_elements) * (rng.random(prov.num_elements) < 0.5)
    a = prov.pushforward(b)
    for j in range(prov.num_features):
        if np.all(P[b != 0, j] == 0):
            assert a[j] == 0


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_completeness_of_pushforward(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    b = is_sigma_consistent(prov.to_dense(), np.random.default_rng(seed).normal(size=prov.num_elements))
    assert np.isclose(prov.pushforward(b).sum(), b.sum())


@given(full_boxmatrices(), st.integers(0, 2 ** 16))
@SETTINGS
def test_independence_of_pushforward(C: BoxMatrix, seed: int) -> None:
    prov = Provenance(C)
    P = prov.to_dense()
    D = P.sum(axis=1)
    rng = np.random.default_rng(seed)
    b = rng.normal(size=prov.num_elements) * (rng.random(prov.num_elements) < 0.3)
    a = prov.pushforward(b)
    for j in range(prov.num_features):
        T = np.flatnonzero((b != 0) & (P[:, j] > 0))
        if T.size == 1:
            i = T[0]
            assert np.isclose(a[j], P[i, j] * b[i] / D[i])


################################################################################
# Theorems (manuscript, Section 3)
################################################################################


@given(st.one_of(full_boxmatrices(), unambiguous_boxmatrices()))
@SETTINGS
def test_unambiguous_provenance(C: BoxMatrix) -> None:
    """H = 0 if and only if all columns of P are one-hot."""
    prov = Provenance(C)
    onehot = bool(np.all((prov.to_dense() > 0).sum(axis=0) == 1))
    assert (prov.ambiguity().overall == 0) == onehot


@given(st.one_of(full_boxmatrices(), nonoverlapping_boxmatrices()))
@SETTINGS
def test_nonoverlapping_provenance(C: BoxMatrix) -> None:
    """O = 0 if and only if every row of P has at most one nonzero entry."""
    prov = Provenance(C)
    nonoverlapping = bool(np.all((prov.to_dense() > 0).sum(axis=1) <= 1))
    assert (np.isclose(prov.overlap().overall, 0.0, atol=1e-12)) == nonoverlapping


@given(st.one_of(full_boxmatrices(), nonoverlapping_boxmatrices()))
@SETTINGS
def test_perfect_pull_push(C: BoxMatrix) -> None:
    """The pull-push reconstruction is perfect if and only if O = 0."""
    prov = Provenance(C)
    perfect = all(prov.pull_push_error(e) < 1e-9 for e in np.eye(prov.num_features))
    assert perfect == bool(np.isclose(prov.overlap().overall, 0.0, atol=1e-12))


@given(st.one_of(full_boxmatrices(), unambiguous_boxmatrices()))
@SETTINGS
def test_perfect_push_pull(C: BoxMatrix) -> None:
    """The push-pull reconstruction is perfect for all sigma-consistent b if and only if H = 0."""
    prov = Provenance(C)
    P = prov.to_dense()
    basis = [is_sigma_consistent(P, e) for e in np.eye(prov.num_elements)]
    perfect = all(prov.push_pull_error(e) < 1e-9 for e in basis)
    assert perfect == (prov.ambiguity().overall == 0)
