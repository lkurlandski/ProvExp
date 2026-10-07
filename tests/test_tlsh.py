"""
Tests for data/tlsh.py.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
from numpy import typing as npt
import pytest
import tlsh

from provexp.data.tlsh import MAX_DISTANCE
from provexp.data.tlsh import TLSHArrays
from provexp.data.tlsh import greedy_dedup
from provexp.data.tlsh import parse_tlsh
from provexp.data.tlsh import tlsh_distance


################################################################################
# Helpers
################################################################################


def random_hashes(n: int, seed: int) -> list[str]:
    """TLSH hashes of random variations of a few random files, so that some are near-duplicates."""
    rng = np.random.default_rng(seed)
    bases = [rng.integers(0, 256, rng.integers(512, 8192)).astype(np.uint8) for _ in range(4)]
    hashes = []
    for _ in range(n):
        data = bases[rng.integers(len(bases))].copy()
        flips = rng.integers(0, data.size, rng.integers(0, data.size // 100))
        data[flips] = rng.integers(0, 256, flips.size)
        hashes.append(tlsh.hash(data.tobytes()))
    return hashes


def make_arrays(ck: list[int], L: list[int], q1: list[int], q2: list[int], B: list[list[int]] | npt.NDArray[np.uint8]) -> TLSHArrays:
    """TLSHArrays from explicit components; each row of B is broadcast to 32 bytes."""
    body = np.asarray(B, dtype=np.uint8)
    body = np.broadcast_to(body if body.ndim == 2 else body[:, None], (len(ck), 32)).copy()
    return TLSHArrays(
        ck=np.asarray(ck, np.int16),
        L=np.asarray(L, np.int16),
        q1=np.asarray(q1, np.int16),
        q2=np.asarray(q2, np.int16),
        B=body,
    )


def clustered_arrays(n: int, seed: int, num_bases: int = 4) -> TLSHArrays:
    """
    Synthetic hashes clustered around a few random bases, with header shifts of up to 8 length buckets and 8 quartile
    steps (wrapping around) and a few changed body bytes, so that many near pairs lie outside a fixed bucket window.
    One base sits at the edge of the length range to exercise the wraparound.
    """
    rng = np.random.default_rng(seed)
    base_L = rng.integers(0, 256, num_bases)
    base_L[0] = 254
    base_q = rng.integers(0, 16, (num_bases, 2))
    base_B = rng.integers(0, 256, (num_bases, 32))
    which = rng.integers(0, num_bases, n)
    L = (base_L[which] + rng.integers(-8, 9, n)) % 256
    q1 = (base_q[which, 0] + rng.integers(-8, 9, n)) % 16
    q2 = (base_q[which, 1] + rng.integers(-8, 9, n)) % 16
    B = base_B[which].copy()
    for r in range(n):
        cols = rng.integers(0, 32, rng.integers(0, 4))
        B[r, cols] = rng.integers(0, 256, cols.size)
    ck = rng.integers(0, 3, n)
    return make_arrays(ck.tolist(), L.tolist(), q1.tolist(), q2.tolist(), B.astype(np.uint8))


def reference_dedup(x: TLSHArrays, threshold: int) -> list[bool]:
    """Brute force: a hash is kept iff it is not within the threshold of an earlier kept hash."""
    kept: list[int] = []
    result = []
    for i in range(x.n):
        keep = not kept or not bool(np.any(tlsh_distance(x, i, x, np.asarray(kept, np.int64)) < threshold))
        if keep:
            kept.append(i)
        result.append(keep)
    return result


def pairwise(x: TLSHArrays) -> npt.NDArray[np.int64]:
    return np.stack([tlsh_distance(x, i, x, np.arange(x.n)) for i in range(x.n)]) if x.n else np.zeros((0, 0), np.int64)


################################################################################
# Distances
################################################################################


class TestDistance:

    def test_matches_tlsh(self) -> None:
        hashes = random_hashes(40, 0)
        x = parse_tlsh(hashes)
        for i in range(x.n):
            expected = [tlsh.diff(hashes[i], h) for h in hashes]
            assert tlsh_distance(x, i, x, np.arange(x.n)).tolist() == expected

    def test_max_distance(self) -> None:
        x = make_arrays([0, 1], [0, 128], [0, 8], [3, 11], [[0x00], [0xFF]])
        assert tlsh_distance(x, 0, x, np.array([1])).tolist() == [MAX_DISTANCE]
        assert int(pairwise(clustered_arrays(200, 0)).max()) <= MAX_DISTANCE

    @pytest.mark.parametrize("L", [(0, 255), (255, 0), (1, 254), (254, 1)])
    def test_length_wraparound(self, L: tuple[int, int]) -> None:
        x = make_arrays([0, 0], list(L), [0, 0], [0, 0], [[0], [0]])
        expected = {1: 1, 3: 36}[min(abs(L[0] - L[1]), 256 - abs(L[0] - L[1]))]
        assert tlsh_distance(x, 0, x, np.array([1])).tolist() == [expected]

    @pytest.mark.parametrize("q", [(0, 15), (15, 0), (0, 12), (2, 14)])
    def test_quartile_wraparound(self, q: tuple[int, int]) -> None:
        x = make_arrays([0, 0], [0, 0], list(q), [0, 0], [[0], [0]])
        d = min(abs(q[0] - q[1]), 16 - abs(q[0] - q[1]))
        expected = d if d <= 1 else (d - 1) * 12
        assert tlsh_distance(x, 0, x, np.array([1])).tolist() == [expected]


################################################################################
# Deduplication
################################################################################


THRESHOLDS = [1, 2, 10, 30, 36, 37, 38, 50, 60, 100, 150, 200, 400, 1000, MAX_DISTANCE, MAX_DISTANCE + 1, 10 ** 6]


class TestGreedyDedup:

    @pytest.mark.parametrize("threshold", THRESHOLDS)
    def test_real_hashes(self, threshold: int) -> None:
        hashes = random_hashes(80, 1)
        x = parse_tlsh(hashes)
        kept = greedy_dedup(x, threshold)
        expected: list[bool] = []
        for i, h in enumerate(hashes):
            expected.append(not any(tlsh.diff(h, hashes[j]) < threshold for j in range(i) if expected[j]))
        assert kept.tolist() == expected

    @pytest.mark.parametrize("threshold", THRESHOLDS)
    @pytest.mark.parametrize("seed", [0, 1, 2])
    def test_clustered(self, threshold: int, seed: int) -> None:
        x = clustered_arrays(400, seed)
        assert greedy_dedup(x, threshold).tolist() == reference_dedup(x, threshold)

    @pytest.mark.parametrize("threshold", [10, 37, 60, 200, 1000])
    @pytest.mark.parametrize("scan_limit", [0, 1, 7, 10 ** 9])
    @pytest.mark.parametrize("chunk_size", [1, 13, 2 ** 16])
    def test_strategies_agree(self, threshold: int, scan_limit: int, chunk_size: int) -> None:
        x = clustered_arrays(300, 3)
        kept = greedy_dedup(x, threshold, scan_limit=scan_limit, chunk_size=chunk_size)
        assert kept.tolist() == reference_dedup(x, threshold)

    @pytest.mark.parametrize("threshold", [30, 37, 100, 200])
    def test_invariants(self, threshold: int) -> None:
        x = clustered_arrays(600, 4)
        kept = greedy_dedup(x, threshold)
        D = pairwise(x)
        k = np.flatnonzero(kept)
        # Kept hashes are pairwise at least the threshold apart.
        Dk = D[np.ix_(k, k)]
        assert np.all(Dk[~np.eye(k.size, dtype=bool)] >= threshold)
        # Every dropped hash is within the threshold of an earlier kept hash.
        for i in np.flatnonzero(~kept):
            earlier = k[k < i]
            assert np.any(D[i, earlier] < threshold)

    def test_beyond_fixed_window(self) -> None:
        # Identical bodies, lengths 3 apart across the wraparound (cost 36), and quartiles 4 apart (cost 36).
        x = make_arrays([0, 0, 0], [254, 1, 254], [5, 5, 9], [0, 0, 0], [[7], [7], [7]])
        assert greedy_dedup(x, 36).tolist() == [True, True, True]
        assert greedy_dedup(x, 37).tolist() == [True, False, False]

    def test_exact_duplicates(self) -> None:
        x = make_arrays([3] * 5, [10] * 5, [1] * 5, [2] * 5, [[9]] * 5)
        assert greedy_dedup(x, 1).tolist() == [True, False, False, False, False]

    def test_checksum_only(self) -> None:
        x = make_arrays([0, 1], [10, 10], [1, 1], [2, 2], [[9], [9]])
        assert greedy_dedup(x, 1).tolist() == [True, True]
        assert greedy_dedup(x, 2).tolist() == [True, False]

    def test_order(self) -> None:
        x = clustered_arrays(200, 5)
        perm = np.random.default_rng(0).permutation(x.n)
        y = TLSHArrays(ck=x.ck[perm], L=x.L[perm], q1=x.q1[perm], q2=x.q2[perm], B=x.B[perm])
        assert greedy_dedup(y, 60).tolist() == reference_dedup(y, 60)

    def test_above_max_distance(self) -> None:
        x = clustered_arrays(100, 6)
        kept = greedy_dedup(x, MAX_DISTANCE + 1)
        assert kept.tolist() == [True] + [False] * (x.n - 1)

    @pytest.mark.parametrize("n", [0, 1])
    def test_tiny(self, n: int) -> None:
        kept = greedy_dedup(clustered_arrays(n, 7), 30)
        assert kept.dtype == np.bool_
        assert kept.tolist() == [True] * n

    @pytest.mark.parametrize("threshold", [0, -1])
    def test_invalid_threshold(self, threshold: int) -> None:
        with pytest.raises(ValueError):
            greedy_dedup(clustered_arrays(2, 8), threshold)

    def test_invalid_chunk_size(self) -> None:
        with pytest.raises(ValueError):
            greedy_dedup(clustered_arrays(2, 8), 30, chunk_size=0)

    @settings(max_examples=150, deadline=None)
    @given(
        seed=st.integers(0, 2 ** 32 - 1),
        n=st.integers(0, 120),
        num_bases=st.integers(1, 6),
        threshold=st.integers(1, MAX_DISTANCE + 2),
    )
    def test_property(self, seed: int, n: int, num_bases: int, threshold: int) -> None:
        x = clustered_arrays(n, seed, num_bases)
        assert greedy_dedup(x, threshold).tolist() == reference_dedup(x, threshold)
