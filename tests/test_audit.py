"""
Tests for 3-C revised's building blocks (scripts/audit_discover.py, scripts/audit_surrogate.py): the runs of a
feature's support with their credit, the choice of a feature's content, and the surrogate's fidelity.

None needs data.
"""

from pathlib import Path
import sys

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import pytest

from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

from tests.strategies import full_boxmatrices

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit_discover import choose_content  # noqa: E402
from audit_discover import feature_credit_runs  # noqa: E402
from audit_surrogate import fidelity  # noqa: E402


################################################################################
# Runs and their credit
################################################################################


def dense_runs(column: np.ndarray, weights: np.ndarray) -> list[tuple[int, int, float]]:
    """The maximal runs of nonzero entries of a column, with the weighted sum over each."""
    runs: list[tuple[int, int, float]] = []
    for i in np.flatnonzero(column > 0).tolist():
        if runs and runs[-1][0] + runs[-1][1] == i:
            s, n, c = runs[-1]
            runs[-1] = (s, n + 1, c + float(weights[i] * column[i]))
        else:
            runs.append((i, 1, float(weights[i] * column[i])))
    return runs


class TestFeatureCreditRuns:

    @settings(max_examples=200, deadline=None)
    @given(full_boxmatrices(), st.data())
    def test_matches_the_dense_matrix(self, C: BoxMatrix, data: st.DataObject) -> None:
        prov = Provenance(C)
        m = prov.num_elements
        P = prov.to_dense()[:m]
        w = np.asarray(data.draw(st.lists(st.floats(-5, 5), min_size=m, max_size=m)), dtype=np.float64)
        for j in range(prov.num_features):
            runs = feature_credit_runs(prov, j, w, max_runs=m + 1)
            assert runs is not None
            expected = dense_runs(P[:, j], w)
            assert [(s, n) for s, n, _ in runs] == [(s, n) for s, n, _ in expected]
            np.testing.assert_allclose([c for _, _, c in runs], [c for _, _, c in expected], atol=1e-9)

    @settings(max_examples=100, deadline=None)
    @given(full_boxmatrices(), st.data())
    def test_credits_sum_to_the_pushforward(self, C: BoxMatrix, data: st.DataObject) -> None:
        prov = Provenance(C)
        m = prov.num_elements
        b = np.asarray(data.draw(st.lists(st.floats(-5, 5), min_size=m, max_size=m)), dtype=np.float64)
        D = prov.rowsum()[:m]
        w = np.where(D > 0, b / np.where(D > 0, D, 1.0), 0.0)
        psi = prov.pushforward(b)
        for j in range(prov.num_features):
            runs = feature_credit_runs(prov, j, w, max_runs=m + 1)
            assert runs is not None
            assert sum(c for _, _, c in runs) == pytest.approx(psi[j], abs=1e-9)

    def test_without_weights_counts_provenance_mass(self) -> None:
        C = BoxMatrix((6, 1))
        C.add_boxes(0, 2, 0, 1, 1.0)
        C.add_boxes(4, 6, 0, 1, 3.0)
        runs = feature_credit_runs(Provenance(C), 0, None, max_runs=4)
        assert runs is not None
        assert [(s, n) for s, n, _ in runs] == [(0, 2), (4, 2)]
        np.testing.assert_allclose([c for _, _, c in runs], [0.25, 0.75])

    def test_gives_up_on_too_many_runs(self) -> None:
        C = BoxMatrix((5, 1))
        for i in (0, 2, 4):
            C.add_boxes(i, i + 1, 0, 1, 1.0)
        assert feature_credit_runs(Provenance(C), 0, None, max_runs=2) is None
        runs = feature_credit_runs(Provenance(C), 0, None, max_runs=3)
        assert runs is not None and len(runs) == 3


################################################################################
# Content
################################################################################


class TestChooseContent:

    def test_takes_the_most_credit_in_the_direction(self) -> None:
        runs = [(0, 4, 0.5), (10, 4, -2.0), (20, 4, 1.0)]
        assert choose_content(runs, 1.0, 256) == (20, 4)
        assert choose_content(runs, -1.0, 256) == (10, 4)

    def test_ties_take_the_first(self) -> None:
        assert choose_content([(0, 4, 1.0), (8, 4, 1.0)], 1.0, 256) == (0, 4)

    @pytest.mark.parametrize("runs", [None, []])
    def test_nothing_to_choose(self, runs: list[tuple[int, int, float]] | None) -> None:
        assert choose_content(runs, 1.0, 256) == (-1, 0)

    def test_rejects_long_runs(self) -> None:
        assert choose_content([(0, 300, 1.0)], 1.0, 256) == (-1, 0)


################################################################################
# Fidelity
################################################################################


class TestFidelity:

    def test_perfect(self) -> None:
        y = np.array([-2.0, -1.0, 0.5, 3.0])
        assert fidelity(y, y.copy()) == {"r2": 1.0, "spearman": pytest.approx(1.0), "sign_agreement": 1.0}

    def test_sign_agreement(self) -> None:
        assert fidelity(np.array([-1.0, 1.0, 2.0, 3.0]), np.array([1.0, 1.0, 2.0, 3.0]))["sign_agreement"] == 0.75

    def test_rejects_mismatched_shapes(self) -> None:
        with pytest.raises(ValueError):
            fidelity(np.zeros(3), np.zeros(4))
