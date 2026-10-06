"""
Vectorized TLSH distances and near-duplicate removal, adapted from SSViT (scripts/soreltlshnear.py).

The distance matches `tlsh.diff` (with length differences included) for version T1 hashes.
"""

from __future__ import annotations
from collections import defaultdict
from collections.abc import Sequence
from typing import NamedTuple

import numpy as np
from numpy import typing as npt
from tqdm import tqdm


__all__ = [
    "TLSHArrays",
    "parse_tlsh",
    "tlsh_distance",
    "greedy_dedup",
]


# The neighbor search below only considers length buckets within +/-2, which is exhaustive for thresholds up to 36
# because a length difference of 3 alone costs 36.
MAX_THRESHOLD = 36


def _build_table() -> npt.NDArray[np.int16]:
    T = np.zeros((256, 256), np.int16)
    A = np.arange(256)
    for s in range(4):
        a = (A[:, None] >> (2 * s)) & 3
        b = (A[None, :] >> (2 * s)) & 3
        d = np.abs(a - b)
        T += np.where(d == 3, 6, d).astype(np.int16)
    return T


# The body distance between every pair of bytes, each of which packs four 2-bit quartile codes.
_TABLE = _build_table()


def _swap(b: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
    return (((b & 0x0F) << 4) | ((b & 0xF0) >> 4)).astype(np.uint8)


class TLSHArrays(NamedTuple):
    """
    The components of N TLSH hashes.

    Attributes:
        ck: The checksum, shape (N,).
        L: The log-length bucket, shape (N,).
        q1: The first quartile ratio, shape (N,).
        q2: The second quartile ratio, shape (N,).
        B: The body, shape (N, 32).
    """

    ck: npt.NDArray[np.int16]
    L: npt.NDArray[np.int16]
    q1: npt.NDArray[np.int16]
    q2: npt.NDArray[np.int16]
    B: npt.NDArray[np.uint8]

    @property
    def n(self) -> int:
        return int(self.ck.shape[0])


def parse_tlsh(hashes: Sequence[str]) -> TLSHArrays:
    """
    Parse version T1 TLSH hashes (with or without the "T1" prefix) into arrays.
    """
    raw = np.empty((len(hashes), 35), np.uint8)
    for i, h in enumerate(hashes):
        h = h.removeprefix("T1")
        if len(h) != 70:
            raise ValueError(f"Expected a 70-character TLSH body. Got {h!r}.")
        raw[i] = np.frombuffer(bytes.fromhex(h), np.uint8)
    return TLSHArrays(
        ck=_swap(raw[:, 0]).astype(np.int16),
        L=_swap(raw[:, 1]).astype(np.int16),
        q1=(_swap(raw[:, 2]) >> 4).astype(np.int16),
        q2=(_swap(raw[:, 2]) & 0x0F).astype(np.int16),
        B=raw[:, 3:35].copy(),
    )


def _length_cost(d: npt.NDArray[np.integer]) -> npt.NDArray[np.integer]:
    return np.where(d == 0, 0, np.where(d == 1, 1, d * 12))


def _quartile_cost(d: npt.NDArray[np.integer]) -> npt.NDArray[np.integer]:
    return np.where(d <= 1, d, (d - 1) * 12)


def _header_distance(x: TLSHArrays, i: int | npt.NDArray[np.int64], y: TLSHArrays, j: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    ld = np.abs(x.L[i] - y.L[j]).astype(np.int64)
    ld = np.minimum(ld, 256 - ld)
    d1 = np.abs(x.q1[i] - y.q1[j]).astype(np.int64)
    d1 = np.minimum(d1, 16 - d1)
    d2 = np.abs(x.q2[i] - y.q2[j]).astype(np.int64)
    d2 = np.minimum(d2, 16 - d2)
    return _length_cost(ld) + _quartile_cost(d1) + _quartile_cost(d2) + (x.ck[i] != y.ck[j])  # type: ignore[no-any-return]


def tlsh_distance(x: TLSHArrays, i: int, y: TLSHArrays, j: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """
    The TLSH distance between hash i of x and each hash j of y.
    """
    return _header_distance(x, i, y, j) + _TABLE[x.B[i], y.B[j]].sum(axis=-1)  # type: ignore[no-any-return]


def _key(x: TLSHArrays) -> npt.NDArray[np.int64]:
    return (x.L.astype(np.int64) << 8) | (x.q1.astype(np.int64) << 4) | x.q2.astype(np.int64)


def _neighbor_offsets(threshold: int) -> list[tuple[int, int, int]]:
    """The (length, q1, q2) bucket offsets whose header cost alone is below the threshold."""
    offsets = []
    for dl in range(-2, 3):
        lc = int(_length_cost(np.array(min(abs(dl), 256 - abs(dl)))))
        for dq1 in range(-3, 4):
            q1c = int(_quartile_cost(np.array(min(abs(dq1), 16 - abs(dq1)))))
            for dq2 in range(-3, 4):
                q2c = int(_quartile_cost(np.array(min(abs(dq2), 16 - abs(dq2)))))
                if lc + q1c + q2c < threshold:
                    offsets.append((dl, dq1, dq2))
    return offsets


def greedy_dedup(x: TLSHArrays, threshold: int, progress: bool = False) -> npt.NDArray[np.bool_]:
    """
    Keep one representative of each group of near-duplicates, in order: a hash is kept unless it is within
    `threshold` (exclusive) of a hash that was already kept. Kept hashes are therefore pairwise >= threshold apart.

    Candidates are restricted to the buckets of (length, q1, q2) whose header cost alone is below the threshold,
    which is exhaustive for thresholds up to `MAX_THRESHOLD`.

    Returns:
        Whether each hash is kept, shape (N,).
    """
    if not 0 < threshold <= MAX_THRESHOLD:
        raise ValueError(f"Expected a threshold in (0, {MAX_THRESHOLD}]. Got {threshold}.")
    offsets = _neighbor_offsets(threshold)
    keys = _key(x)
    kept = np.zeros(x.n, dtype=np.bool_)
    buckets: defaultdict[int, list[int]] = defaultdict(list)
    for i in tqdm(range(x.n), disable=not progress, desc="Deduplicating"):
        k = int(keys[i])
        L, Q1, Q2 = (k >> 8) & 0xFF, (k >> 4) & 0xF, k & 0xF
        candidates: list[int] = []
        for dl, dq1, dq2 in offsets:
            candidates.extend(buckets.get((((L + dl) % 256) << 8) | (((Q1 + dq1) % 16) << 4) | ((Q2 + dq2) % 16), []))
        if candidates:
            c = np.asarray(candidates, np.int64)
            h = _header_distance(x, i, x, c)
            close = np.flatnonzero(h < threshold)
            if close.size and np.any(h[close] + _TABLE[x.B[i], x.B[c[close]]].sum(axis=-1) < threshold):
                continue
        kept[i] = True
        buckets[k].append(i)
    return kept
