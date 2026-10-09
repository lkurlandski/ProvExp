"""
Tests for PF1's resolution trend (scripts/pf1_resolution.py): the sparse coarsened provenance must agree with the
dense one used everywhere else (`provexp.ablation.coarsen`, `coarsen_provenance`), and the window round trip must be
the pull-push round trip of the coarsened P, within CP's bound.
"""

from pathlib import Path
import sys

import numpy as np
import pytest

from provexp.ablation import coarsen
from provexp.ablation import coarsen_provenance
from provexp.ablation import window_edges
from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pf1_resolution import BYTES  # noqa: E402
from pf1_resolution import coarsen_sparse  # noqa: E402
from pf1_resolution import round_trips  # noqa: E402
from pf1_resolution import window_pushforward_sparse  # noqa: E402
from pf1_resolution import window_statistics  # noqa: E402


def random_provenance(seed: int, m: int = 40, n: int = 7) -> Provenance:
    """Random boxes over m elements and n features; the last feature is left empty (unattributable)."""
    rng = np.random.default_rng(seed)
    C = BoxMatrix((m, n))
    for _ in range(12):
        lo = int(rng.integers(0, m - 1))
        hi = int(rng.integers(lo + 1, m + 1))
        j = int(rng.integers(0, n - 1))
        C.add_boxes(lo, hi, j, j + 1, float(rng.uniform(0.5, 3.0)))
    return Provenance(C)


################################################################################
# The Sparse Coarsened Provenance
################################################################################


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("K", [1, 3, 8, 40])
class TestCoarsenSparse:

    def test_matches_the_dense_coarsening(self, seed: int, K: int) -> None:
        prov = random_provenance(seed)
        edges = window_edges(prov.num_elements, K)
        assert np.allclose(coarsen_sparse(prov, edges).toarray(), coarsen(prov, edges)[:-1])

    def test_overlap_matches_the_coarsened_provenance(self, seed: int, K: int) -> None:
        prov = random_provenance(seed)
        edges = window_edges(prov.num_elements, K)
        _, O = window_statistics(coarsen_sparse(prov, edges))
        expected = coarsen_provenance(prov, edges).overlap().per_feature
        att = prov.included
        assert np.allclose(O[att], expected[att])

    def test_pushforward_matches_the_coarsened_provenance(self, seed: int, K: int) -> None:
        prov = random_provenance(seed)
        edges = window_edges(prov.num_elements, K)
        P = coarsen_sparse(prov, edges)
        D, _ = window_statistics(P)
        b = np.random.default_rng(seed).normal(size=edges.shape[0] - 1)
        assert np.allclose(window_pushforward_sparse(P, D, b), coarsen_provenance(prov, edges).pushforward(b))


################################################################################
# Window Round Trips
################################################################################


@pytest.mark.parametrize("seed", range(5))
def test_round_trips_are_the_coarsened_pull_push_within_the_bound(seed: int) -> None:
    prov = random_provenance(seed)
    a = np.random.default_rng(seed).normal(size=prov.num_features)
    a_att = np.where(prov.included, a, 0.0)
    trips, records = round_trips(prov, a, (3, 8, BYTES))
    for K in (3, 8):
        expected = coarsen_provenance(prov, window_edges(prov.num_elements, K)).pull_push(a_att)
        assert np.allclose(trips[K], expected)
    assert np.allclose(trips[BYTES], prov.pull_push(a_att))
    for r in records:
        assert r["loss"] <= r["bound"] + 1e-9


def test_a_resolution_finer_than_the_file_is_the_bytes() -> None:
    prov = random_provenance(0)
    a = np.random.default_rng(0).normal(size=prov.num_features)
    trips, records = round_trips(prov, a, (1000, BYTES))
    assert np.array_equal(trips[1000], trips[BYTES])
    assert records[0]["num_windows"] == prov.num_elements
