"""
Tests for PF1's building blocks (scripts/pf1.py): the rankings, the window pushforward and its naive baseline, and the
feature-space deletion under both references.

They need no data: the provenance is built by hand and the model is a known function.
"""

from pathlib import Path
import sys

import numpy as np
import pytest

from provexp.ablation import window_edges
from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pf1 import band  # noqa: E402
from pf1 import delete_to_background  # noqa: E402
from pf1 import delete_to_reference  # noqa: E402
from pf1 import feature_order  # noqa: E402
from pf1 import incidence_pushforward  # noqa: E402
from pf1 import window_pushforward  # noqa: E402
from provexp.ablation import coarsen  # noqa: E402


def small_provenance() -> Provenance:
    """
    Eight elements, four features: feature 0 reads elements 0-1, feature 1 reads 0-7 (a global feature), feature 2
    reads 6-7, and feature 3 reads nothing (unattributable).
    """
    C = BoxMatrix((8, 4))
    C.add_boxes(0, 2, 0, 1, 1.0)
    C.add_boxes(0, 8, 1, 2, 1.0)
    C.add_boxes(6, 8, 2, 3, 3.0)
    return Provenance(C)


################################################################################
# Rankings
################################################################################


class TestFeatureOrder:

    def test_orders_by_signed_score(self) -> None:
        scores = np.array([0.5, -2.0, 1.0, 0.0])
        tiebreak = np.arange(4)
        assert feature_order(scores, 1.0, tiebreak).tolist() == [2, 0, 3, 1]
        assert feature_order(scores, -1.0, tiebreak).tolist() == [1, 3, 0, 2]

    def test_ties_follow_the_permutation_not_the_index(self) -> None:
        scores = np.array([0.0, 0.0, 0.0, 1.0])
        assert feature_order(scores, 1.0, np.array([2, 0, 3, 1])).tolist() == [3, 2, 0, 1]

    def test_rejects_a_mismatched_permutation(self) -> None:
        with pytest.raises(ValueError):
            feature_order(np.zeros(3), 1.0, np.arange(4))


################################################################################
# The Window Pushforward and the Naive Baseline
################################################################################


class TestWindowPushforward:

    def test_matches_the_definition(self) -> None:
        prov = small_provenance()
        edges = window_edges(8, 4)
        b = np.array([1.0, -2.0, 0.5, 3.0])
        push, _ = window_pushforward(prov, edges, b)
        # P over windows: column-normalized coarsened contributions; D the row sums; a = P^T D^+ b.
        P = coarsen(prov, edges)[:4]
        P = np.divide(P, P.sum(axis=0), out=np.zeros_like(P), where=P.sum(axis=0) > 0)
        D = P.sum(axis=1)
        assert np.allclose(push, P.T @ np.where(D > 0, b / np.where(D > 0, D, 1.0), 0.0))

    def test_conserves_the_mass_of_live_windows(self) -> None:
        prov = small_provenance()
        b = np.random.default_rng(0).normal(size=4)
        push, _ = window_pushforward(prov, window_edges(8, 4), b)
        assert np.isclose(push.sum(), b.sum())  # every window feeds some feature (feature 1 reads them all)

    def test_never_credits_unattributable_features(self) -> None:
        push, naive = window_pushforward(small_provenance(), window_edges(8, 4), np.ones(4))
        assert push[3] == 0.0 and naive[3] == 0.0

    def test_naive_baseline_is_the_plain_incidence_sum(self) -> None:
        prov = small_provenance()
        edges = window_edges(8, 4)
        b = np.array([1.0, -2.0, 0.5, 3.0])
        _, naive = window_pushforward(prov, edges, b)
        # Feature 0 reads window 0, feature 1 every window, feature 2 window 3.
        assert np.allclose(naive, [1.0, b.sum(), 3.0, 0.0])
        assert np.allclose(naive, incidence_pushforward(coarsen(prov, edges), b))

    def test_naive_baseline_rejects_the_wrong_length(self) -> None:
        with pytest.raises(ValueError):
            incidence_pushforward(np.zeros((5, 4)), np.zeros(3))


################################################################################
# Feature-Space Deletion
################################################################################


def linear(X: np.ndarray) -> np.ndarray:
    return np.asarray(X @ np.array([1.0, 2.0, -1.0, 0.5]), dtype=np.float64)


class TestDeletion:

    x = np.array([1.0, 1.0, 1.0, 1.0])

    def test_reference_end_points(self) -> None:
        reference = np.array([0.0, 3.0, -1.0, 2.0])
        masks = [np.zeros(4, dtype=np.bool_), np.ones(4, dtype=np.bool_), np.array([True, False, False, False])]
        out = delete_to_reference(linear, self.x, reference, masks)
        assert np.allclose(out, [linear(self.x[None])[0], linear(reference[None])[0], linear(self.x[None])[0] - 1.0])

    @pytest.mark.parametrize("which", [[], [0], [1, 2], [0, 1, 2, 3]])
    def test_background_is_the_interventional_expectation(self, which: list[int]) -> None:
        background = np.random.default_rng(0).normal(size=(50, 4))
        mask = np.zeros(4, dtype=np.bool_)
        mask[which] = True
        out = delete_to_background(linear, self.x, background, [mask])
        # For a linear model the expectation replaces the deleted features by their background mean.
        expected = linear(np.where(mask, background.mean(axis=0), self.x)[None])[0]
        assert np.isclose(out[0], expected)

    def test_background_does_not_modify_the_background(self) -> None:
        background = np.random.default_rng(0).normal(size=(5, 4))
        copy = background.copy()
        delete_to_background(linear, self.x, background, [np.array([True, False, True, False])])
        assert np.array_equal(background, copy)


@pytest.mark.parametrize("R,expected", [(0.95, "faithful"), (0.8, "faithful"), (0.79, "partial"), (0.5, "partial"), (0.49, "weakened")])
def test_band_matches_the_criterion_fixed_in_advance(R: float, expected: str) -> None:
    assert band(R) == expected
