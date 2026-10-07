"""
Vectorized TLSH distances and near-duplicate removal, adapted from SSViT (scripts/soreltlshnear.py).

The distance matches `tlsh.diff` (with length differences included) for version T1 hashes.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import NamedTuple
from typing import Optional

import numba
import numpy as np
from numpy import typing as npt
from tqdm import tqdm


__all__ = [
    "MAX_DISTANCE",
    "TLSHArrays",
    "parse_tlsh",
    "tlsh_distance",
    "greedy_dedup",
]


################################################################################
# Distances
################################################################################


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


# The cost of a difference of |d| between log-length buckets (modulo 256) and between quartile ratios (modulo 16).
_LENGTH_COSTS = _length_cost(np.minimum(np.arange(256), 256 - np.arange(256))).astype(np.int64)
_QUARTILE_COSTS = _quartile_cost(np.minimum(np.arange(16), 16 - np.arange(16))).astype(np.int64)

# The largest possible distance: the lengths differ by 128 buckets, both quartile ratios by 8, the checksums differ,
# and all 128 body codes differ by 3.
MAX_DISTANCE = int(_LENGTH_COSTS.max() + 2 * _QUARTILE_COSTS.max() + 1 + _TABLE.max() * 32)


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


################################################################################
# Deduplication
################################################################################


def _neighbor_offsets(threshold: int) -> npt.NDArray[np.int64]:
    """
    The bucket offsets (dL mod 256, dq1 mod 16, dq2 mod 16) whose header cost alone is below the threshold, cheapest
    first, shape (K, 3). Every pair of hashes within the threshold lies in buckets separated by one of these offsets.
    """
    cost = _LENGTH_COSTS[:, None, None] + _QUARTILE_COSTS[None, :, None] + _QUARTILE_COSTS[None, None, :]
    offsets = np.argwhere(cost < threshold)
    order = np.argsort(cost[offsets[:, 0], offsets[:, 1], offsets[:, 2]], kind="stable")
    return np.ascontiguousarray(offsets[order], dtype=np.int64)


@numba.njit(cache=True)
def _within(
    i: int,
    j: int,
    threshold: int,
    ck: npt.NDArray[np.int64],
    L: npt.NDArray[np.int64],
    q1: npt.NDArray[np.int64],
    q2: npt.NDArray[np.int64],
    B: npt.NDArray[np.uint8],
    table: npt.NDArray[np.int64],
    lcost: npt.NDArray[np.int64],
    qcost: npt.NDArray[np.int64],
) -> bool:
    """Whether hashes i and j are within the threshold (exclusive), stopping as soon as the distance reaches it."""
    d = lcost[abs(L[i] - L[j])] + qcost[abs(q1[i] - q1[j])] + qcost[abs(q2[i] - q2[j])] + (ck[i] != ck[j])
    if d >= threshold:
        return False
    for b in range(B.shape[1]):
        d += table[B[i, b], B[j, b]]
        if d >= threshold:
            return False
    return True


@numba.njit(cache=True)
def _dedup_kernel(
    start: int,
    stop: int,
    threshold: int,
    ck: npt.NDArray[np.int64],
    L: npt.NDArray[np.int64],
    q1: npt.NDArray[np.int64],
    q2: npt.NDArray[np.int64],
    B: npt.NDArray[np.uint8],
    table: npt.NDArray[np.int64],
    lcost: npt.NDArray[np.int64],
    qcost: npt.NDArray[np.int64],
    offsets: npt.NDArray[np.int64],
    scan_limit: int,
    head: npt.NDArray[np.int64],
    nxt: npt.NDArray[np.int64],
    kept_idx: npt.NDArray[np.int64],
    num_kept: int,
    kept: npt.NDArray[np.bool_],
) -> int:
    """
    Decide whether to keep hashes start, ..., stop - 1, given the hashes kept so far, and return the new number of
    kept hashes. The kept hashes are stored in insertion order (`kept_idx[:num_kept]`) and in one linked list per
    (L, q1, q2) bucket (`head[bucket]`, then `nxt[i]`, -1 terminated).

    While at most `scan_limit` hashes are kept, a hash is compared with every kept hash. Afterwards, it is compared
    only with the kept hashes in the buckets reachable through `offsets`. Both are exact; the first is faster when
    the kept set is small compared to the number of offsets, which happens at large thresholds.
    """
    for i in range(start, stop):
        found = False
        if num_kept <= scan_limit:
            for t in range(num_kept):
                if _within(i, kept_idx[t], threshold, ck, L, q1, q2, B, table, lcost, qcost):
                    found = True
                    break
        else:
            for o in range(offsets.shape[0]):
                bucket = (((L[i] + offsets[o, 0]) & 255) << 8) | (((q1[i] + offsets[o, 1]) & 15) << 4) | ((q2[i] + offsets[o, 2]) & 15)
                j = head[bucket]
                while j >= 0:
                    if _within(i, j, threshold, ck, L, q1, q2, B, table, lcost, qcost):
                        found = True
                        break
                    j = nxt[j]
                if found:
                    break
        if not found:
            bucket = (L[i] << 8) | (q1[i] << 4) | q2[i]
            kept[i] = True
            kept_idx[num_kept] = i
            num_kept += 1
            nxt[i] = head[bucket]
            head[bucket] = i
    return num_kept


def greedy_dedup(
    x: TLSHArrays,
    threshold: int,
    progress: bool = False,
    scan_limit: Optional[int] = None,
    chunk_size: int = 2 ** 16,
) -> npt.NDArray[np.bool_]:
    """
    Keep one representative of each group of near-duplicates, in order: a hash is kept unless it is within
    `threshold` (exclusive) of a hash that was already kept. Kept hashes are therefore pairwise >= threshold apart.

    The result is exact for every threshold. Candidates are restricted to the buckets of (L, q1, q2) whose header cost
    alone is below the threshold, and while the kept set is smaller than the number of such buckets, a hash is
    compared with every kept hash instead.

    Args:
        x: The hashes, in the order of preference.
        threshold: The distance below which two hashes are near-duplicates. Thresholds above `MAX_DISTANCE` keep only
            the first hash.
        progress: Whether to show a progress bar.
        scan_limit: The number of kept hashes up to which a hash is compared with all of them. Defaults to the number
            of candidate buckets. Only affects speed.
        chunk_size: The number of hashes processed between progress updates. Only affects progress reporting.

    Returns:
        Whether each hash is kept, shape (N,).
    """
    if threshold < 1:
        raise ValueError(f"Expected a positive threshold. Got {threshold}.")
    if chunk_size < 1:
        raise ValueError(f"Expected a positive chunk size. Got {chunk_size}.")
    offsets = _neighbor_offsets(threshold)
    if scan_limit is None:
        scan_limit = offsets.shape[0]
    ck, L, q1, q2 = (np.ascontiguousarray(a, dtype=np.int64) for a in (x.ck, x.L, x.q1, x.q2))
    B = np.ascontiguousarray(x.B, dtype=np.uint8)
    table = _TABLE.astype(np.int64)
    head = np.full(1 << 16, -1, dtype=np.int64)
    nxt = np.full(x.n, -1, dtype=np.int64)
    kept_idx = np.empty(x.n, dtype=np.int64)
    kept = np.zeros(x.n, dtype=np.bool_)
    num_kept = 0
    with tqdm(total=x.n, disable=not progress, desc="Deduplicating") as bar:
        for start in range(0, x.n, chunk_size):
            stop = min(start + chunk_size, x.n)
            num_kept = _dedup_kernel(
                start, stop, threshold, ck, L, q1, q2, B, table, _LENGTH_COSTS, _QUARTILE_COSTS,
                offsets, scan_limit, head, nxt, kept_idx, num_kept, kept,
            )
            bar.update(stop - start)
            bar.set_postfix(kept=num_kept)
    return kept
