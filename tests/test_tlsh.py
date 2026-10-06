"""
Tests for data/tlsh.py.
"""

import numpy as np
import pytest
import tlsh

from provexp.data.tlsh import greedy_dedup
from provexp.data.tlsh import parse_tlsh
from provexp.data.tlsh import tlsh_distance


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


def test_distance_matches_tlsh() -> None:
    hashes = random_hashes(40, 0)
    x = parse_tlsh(hashes)
    for i in range(x.n):
        expected = [tlsh.diff(hashes[i], h) for h in hashes]
        assert tlsh_distance(x, i, x, np.arange(x.n)).tolist() == expected


@pytest.mark.parametrize("threshold", [1, 10, 30, 36])
def test_greedy_dedup(threshold: int) -> None:
    hashes = random_hashes(80, 1)
    kept = greedy_dedup(parse_tlsh(hashes), threshold)
    # Brute force: a hash is kept iff it is not within the threshold of an earlier kept hash.
    expected: list[bool] = []
    for i, h in enumerate(hashes):
        expected.append(not any(tlsh.diff(h, hashes[j]) < threshold for j in range(i) if expected[j]))
    assert kept.tolist() == expected


def test_threshold_bounds() -> None:
    x = parse_tlsh(random_hashes(2, 2))
    with pytest.raises(ValueError):
        greedy_dedup(x, 37)
    with pytest.raises(ValueError):
        greedy_dedup(x, 0)
