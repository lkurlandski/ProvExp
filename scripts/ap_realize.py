"""
Direction A': lay an answer of the edit-choice encoding (`scripts/ap_encoding.py`) out as a file.

The solver chooses byte counts (appended `a`, section content `s`), the added sections (sizes, flags, and the hash
options of their names and flag strings), the new byte-entropy windows per entropy row and nibble (`wr`, `we`), and the
strings the new bytes bring (`ns`, `pd`, `rg`). Counts, sizes, and flags are written exactly. The byte *order* is free,
and the realizer chooses it to hit the windows and strings the solver assumed:
- the new tail is cut into the 1,024-byte blocks the windows step over (a window is two adjacent blocks); each block
  gets an entropy row, rows in runs so that a window's two blocks share it, and nibble counts drawn from the solver's
  counts for that row, shaped so that the block's nibble entropy lies in the row;
- reordering a block's bytes changes no window, so within a block the solver's strings are written as printable runs
  ended by a non-printable byte (a byte is printable exactly when its high nibble is 2-7), one regex literal per
  matching string the solver counts, and the other printable bytes in runs of at most four;
- each section's name comes from a search for a name that hits the chosen hash options.
What the realizer misses shows when the file is re-extracted and scored (check 2).

Usage:
    from ap_realize import realize
    edited = realize(enc, program_names, solution_vector)
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from pathlib import Path
import re
import sys
from typing import Optional

import numpy as np

from provexp.featuresets.ember2024.features import StringExtractor
from provexp.items import feature_hash

sys.path.insert(0, str(Path(__file__).parent))
from ap_encoding import BUCKETS  # noqa: E402
from ap_encoding import EMPTY  # noqa: E402
from ap_encoding import FLAGS  # noqa: E402
from ap_encoding import STEP  # noqa: E402
from ap_encoding import Choice  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import props_of  # noqa: E402
from ap_encoding import write  # noqa: E402

__all__ = [
    "Answer",
    "Strings",
    "allocate",
    "plan_strings",
    "realize",
    "regex_literals",
    "search_name",
    "shape_block",
]

# High nibbles of the printable bytes (0x20-0x7f, as thrember's strings read them).
PRINT_COLS = range(2, 8)
NONPRINT_COLS = (0, 1, *range(8, 16))
# Literals for the regexes whose pattern is not itself a matching string.
HAND_LITERALS = {
    "url": "http://a.b",
    "ipv4_addr": "10.0.0.1",
    "ipv6_addr": "1:2:3:4:5:6:7:8",
    "mac_addr": "00:11:22:33:44:55",
    "email_addr": "00:11:22:33:44:55",
    "btc_wallet": "1" + "A" * 30,
    "file_path": "C:/x",
    "registry_key": "HKCU",
    "base64string": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/",
}
NAME_CHARS = np.frombuffer(b"abcdefghijklmnopqrstuvwxyz0123456789", dtype=np.uint8)


################################################################################
# Counts
################################################################################


class Answer:
    """The solver's value of every variable, by name."""

    def __init__(self, names: Sequence[str], x: np.ndarray) -> None:
        if len(names) != x.size:
            raise ValueError(f"{len(names)} names for {x.size} values.")
        self.values = dict(zip(names, x.tolist(), strict=True))

    def __call__(self, name: str) -> float:
        return float(self.values.get(name, 0.0))

    def array(self, fmt: str, size: int) -> np.ndarray:
        """The values of the variables fmt.format(0), ..., fmt.format(size - 1)."""
        return np.asarray([self(fmt.format(i)) for i in range(size)], dtype=np.float64)


def round_counts(x: np.ndarray, total: int) -> np.ndarray:
    """Whole counts summing to `total`, proportional to x (largest remainders); x must not be all zero."""
    x = np.maximum(x, 0.0)
    if total <= 0:
        return np.zeros(x.size, dtype=np.int64)
    if x.sum() <= 0:
        raise ValueError(f"Cannot spread {total} over zero weights.")
    scaled = x * (total / x.sum())
    out: np.ndarray = np.floor(scaled).astype(np.int64)
    order = np.argsort(-(scaled - out), kind="stable")
    out[order[: total - int(out.sum())]] += 1
    return out


def allocate(total: int, weights: np.ndarray, caps: np.ndarray) -> np.ndarray:
    """Whole counts summing to min(total, sum of caps), each within its cap, proportional to `weights` where they fit."""
    caps = np.asarray(caps, dtype=np.int64)
    total = min(int(total), int(caps.sum()))
    out = np.zeros(caps.size, dtype=np.int64)
    w = np.maximum(np.asarray(weights, dtype=np.float64), 0.0)
    while out.sum() < total:
        room = caps - out
        ww = np.where(room > 0, w, 0.0)
        if ww.sum() <= 0:
            ww = room.astype(np.float64)
        add = np.minimum(round_counts(ww, total - int(out.sum())), room)
        if add.sum() == 0:
            add[int(np.argmax(ww))] = 1
        out += add
    return out


def _entropy(c: np.ndarray) -> float:
    t = float(c.sum())
    p = c[c > 0] / t if t > 0 else c[:0]
    return float(-np.sum(p * np.log2(p)))


def shape_block(fixed: np.ndarray, free: int, avail: np.ndarray, target: np.ndarray, row: int) -> np.ndarray:
    """
    Nibble counts for `free` bytes of a block, within `avail` per nibble, close to the proportions of `target`, and
    such that the window the block closes (its `fixed` counts: the previous block and the block's fixed bytes) has
    nibble entropy in byte-entropy row `row`, i.e. in [row / 4, (row + 1) / 4), when the supply allows: too high, the
    counts are mixed toward one nibble (the window's own dominant one where available, so that adjacent blocks agree);
    too low, toward an even spread.
    """
    base = allocate(free, target if target.sum() > 0 else avail, avail)
    lo, hi, mid = row / 4, (row + 1) / 4 if row < 15 else math.inf, (row + 0.5) / 4
    h0 = _entropy(fixed + base)
    if lo <= h0 < hi:
        return base
    high = h0 >= hi
    if high:
        dominant = int(np.argmax(np.where(avail > 0, fixed * float(avail.sum() + 1) + avail, -1.0)))
        other = allocate(free, (np.arange(avail.size) == dominant).astype(np.float64), avail)
    else:
        other = allocate(free, (avail > 0).astype(np.float64), avail)
    a, b = 0.0, 1.0
    for _ in range(20):
        w = (a + b) / 2
        h = _entropy(fixed + allocate(free, (1 - w) * base + w * other, avail))
        if (h > mid) == high:
            a = w
        else:
            b = w
    return allocate(free, (1 - b) * base + b * other, avail)


################################################################################
# Strings
################################################################################


def regex_literals(regexes: dict[str, re.Pattern[str]]) -> dict[str, str]:
    """A string matching each regex (its own pattern where that is plain text), padded with spaces to 5 characters."""
    out = {}
    for k, r in regexes.items():
        lit = HAND_LITERALS.get(k, r.pattern.replace("\\b", "").replace("\\", ""))
        lit = lit.ljust(5)
        if not r.search(lit):
            raise RuntimeError(f"Literal {lit!r} does not match regex {k!r}.")
        out[k] = lit
    return out


@dataclass
class Strings:
    """The strings still to write: regex literals, how many strings in all, and the characters they still need."""

    literals: list[bytes]
    left: int
    need: np.ndarray
    chars: int
    carry: float = 0.0


def plan_strings(ns: int, pd: np.ndarray, rg: dict[str, int], regexes: dict[str, re.Pattern[str]]) -> Strings:
    """
    The strings to write: a literal per regex match the solver counts (longest first, counting every regex a literal
    matches, e.g. "powershell" also counts for "shell"), and `ns` strings in all over the characters `pd` (96 counts).
    """
    literals = regex_literals(regexes)
    got = dict.fromkeys(regexes, 0)
    out = []
    for k in sorted(rg, key=lambda k: -len(literals[k])):
        while got[k] < rg[k]:
            out.append(literals[k].encode())
            for j, r in regexes.items():
                got[j] += bool(r.search(literals[k]))
    need = np.zeros(256, dtype=np.int64)
    need[0x20:0x80] = pd
    return Strings(out, max(ns, len(out)), need, int(pd.sum()))


################################################################################
# Names
################################################################################


def search_name(name_option: int, flag_options: dict[str, int], tries: int, rng: np.random.Generator) -> bytes:
    """
    An 8-byte (or shorter) name whose hash option is `name_option` and whose "name:flag" strings hit as many of
    `flag_options` (pefile flag name -> option) as a random search of `tries` names finds.
    """
    if name_option == EMPTY:
        return b""
    lengths = rng.integers(1, 9, size=tries)
    raw = NAME_CHARS[rng.integers(0, NAME_CHARS.size, size=(tries, 8))]
    names = sorted({raw[i, : lengths[i]].tobytes().decode() for i in range(tries)})
    buckets, signs = feature_hash(BUCKETS, names)
    options = 2 * buckets + (signs < 0)
    hits = [n for n, o in zip(names, options.tolist(), strict=True) if o == name_option]
    if not hits:
        raise RuntimeError(f"No name in {tries} tries hits option {name_option}.")
    if not flag_options:
        return hits[0].encode()
    keys = [f"{n}:{pn}" for n in hits for pn in flag_options]
    b, s = feature_hash(BUCKETS, keys)
    got = (2 * b + (s < 0)).reshape(len(hits), len(flag_options))
    want = np.asarray(list(flag_options.values()))
    return hits[int(np.argmax((got == want).sum(axis=1)))].encode()


################################################################################
# Realizing an answer
################################################################################


def _place(cols: np.ndarray, pool: np.ndarray, plan: Strings, share: float, first: bool) -> bytes:
    """
    The bytes of one block segment with nibble counts `cols`, drawn from `pool` (256 counts, updated): a non-printable
    byte first (when `first`), then the regex literals that fit, then the block's `share` of the other strings (made
    of its printable bytes, the characters the strings need first), each ended by a non-printable byte, then the other
    printable bytes in runs of at most four. Printable bytes the separators cannot break up lengthen the strings.
    """
    cols = cols.copy()

    def draw(col: int, k: int, prefer: Optional[np.ndarray] = None) -> list[int]:
        sl = slice(16 * col, 16 * col + 16)
        w = (np.maximum(prefer[sl], 0) + 1e-3) if prefer is not None else pool[sl].astype(np.float64)
        c = allocate(k, w, pool[sl])
        pool[sl] -= c
        return np.repeat(np.arange(16 * col, 16 * col + 16), c).tolist()

    def take_nonprint() -> Optional[int]:
        for col in NONPRINT_COLS:
            if cols[col] > 0 and pool[16 * col:16 * col + 16].sum() > 0:
                cols[col] -= 1
                return draw(col, 1)[0]
        return None

    out = bytearray()
    if first:
        b = take_nonprint()
        if b is not None:
            out.append(b)
    i = 0
    while i < len(plan.literals) and i < 200 and any(cols[c] > 0 for c in NONPRINT_COLS):
        s = plan.literals[i]
        need = np.bincount(np.frombuffer(s, dtype=np.uint8), minlength=256)
        if np.any(need > pool) or np.any(np.bincount(np.frombuffer(s, dtype=np.uint8) >> 4, minlength=16) > cols):
            i += 1
            continue
        pool -= need
        plan.need -= np.minimum(plan.need, need)
        plan.chars -= len(s)
        plan.left -= 1
        cols -= np.bincount(np.frombuffer(s, dtype=np.uint8) >> 4, minlength=16)
        out += s
        term = take_nonprint()
        if term is not None:
            out.append(term)
        plan.literals.pop(i)

    printable = np.asarray([v for col in PRINT_COLS for v in draw(col, int(cols[col]), plan.need)], dtype=np.int64)
    nonprint = [v for col in NONPRINT_COLS for v in draw(col, int(cols[col]))]
    # The block's strings (pacing the remaining ones by its share of the printable supply).
    plan.carry += max(plan.left - len(plan.literals), 0) * share
    k = min(math.ceil(plan.carry), max(plan.left - len(plan.literals), 0), len(nonprint), printable.size // 5)
    plan.carry -= k
    wanted = np.zeros(printable.size, dtype=bool)
    left = plan.need.copy()
    for idx, b in enumerate(printable.tolist()):
        if left[b] > 0:
            left[b] -= 1
            wanted[idx] = True
    order = np.concatenate([printable[wanted], printable[~wanted]])
    length = min(printable.size, max(5 * k, round(plan.chars * share))) if k else 0
    spare = len(nonprint) - k
    if printable.size - length > 4 * spare:
        length = printable.size - 4 * spare if k else length
    chars, rest = order[:length], order[length:]
    for chunk in (np.array_split(chars, k) if k else []):
        out += bytes(chunk.tolist())
        out.append(nonprint.pop())
    plan.left -= k
    plan.chars -= int(length)
    plan.need -= np.minimum(plan.need, np.bincount(chars, minlength=256))
    rest_l = rest.tolist()
    for j in range(0, len(rest_l), 4):
        out += bytes(rest_l[j:j + 4])
        if nonprint:
            out.append(nonprint.pop())
    out += bytes(nonprint)
    return bytes(out)


def realize(enc: Encoding, names: Sequence[str], x: np.ndarray, regexes: Optional[dict[str, re.Pattern[str]]] = None,
            name_tries: int = 200_000, seed: int = 0, descending: bool = True) -> bytes:
    """
    The file an answer of the encoding describes (sections, then the append), with its new bytes ordered to hit the
    solver's windows and strings.

    Args:
        enc: The encoding the answer solves.
        names: The program's variable names.
        x: The answer (one value per variable).
        regexes: thrember's string regexes (by default, its StringExtractor's).
        name_tries: Random names tried per added section.
        seed: Seeds the string fillers and the name search.
        descending: Lay the windows' rows out from the highest entropy down (the even spreads the high rows need are
            taken while the supply still has them; the low rows need only one plentiful nibble).

    Returns:
        The edited file.
    """
    v = Answer(names, x)
    rng = np.random.default_rng(seed)
    if regexes is None:
        regexes = StringExtractor()._regexes  # type: ignore[no-untyped-call]
    n, fa = enc.n, enc.fa

    # The sections: sizes, flags, names.
    sections = []
    for i in range(enc.k):
        if v(f"on{i}") < 0.5:
            break
        raw = fa * round(v(f"m{i}"))
        c = min(raw, max(raw - fa + 1, round(v(f"c{i}")))) if raw else 0
        flags = [f for f in FLAGS if v(f"fl{i}_{f}") > 0.5]
        name_opt = int(np.argmax([v(f"y{i}_{o}") for o in range(EMPTY + 1)]))
        flag_opts = {pn: int(np.argmax([v(f"q{i}_{pn}_{o}") for o in range(EMPTY)])) for f in flags for pn in props_of(FLAGS[f])}
        name = search_name(name_opt, flag_opts, name_tries, rng)
        sections.append((name, c, raw, sum(FLAGS[f] for f in flags)))
    gap = (-n) % fa if sections else 0
    A = round(v("A"))
    total = gap + sum(r for _, _, r, _ in sections) + A

    # The byte pools: each section's content and the append.
    s = round_counts(v.array("s{}", 256), sum(c for _, c, _, _ in sections)) if sections else np.zeros(256, dtype=np.int64)
    pools = []
    for i, (_, c, _, _) in enumerate(sections):
        pools.append(s.copy() if i == len(sections) - 1 else allocate(c, s, s))
        s = s - pools[-1]
    a = v.array("a{}", 256)
    pools.append(round_counts(a, A) if A else np.zeros(256, dtype=np.int64))

    # The free intervals of the new tail (absolute offsets), each with its pool; everything else is zero padding.
    free: list[tuple[int, int, int]] = []
    at = n + gap
    for i, (_, c, raw, _) in enumerate(sections):
        free.append((at, at + c, i))
        at += raw
    free.append((at, at + A, len(sections)))
    end = n + total

    # The rows of the new windows, in runs, and the solver's counts per (row, nibble) over the blocks.
    w0 = (n - 2 * STEP) // STEP + 1
    windows = max(0, (end - 2 * STEP) // STEP + 1 - w0)
    wr = v.array("wr{}", 16)
    rows = np.repeat(np.arange(16), round_counts(wr, windows)) if windows and wr.sum() > 0 else np.zeros(0, dtype=np.int64)
    if descending:
        rows = rows[::-1]
    target = np.asarray([[v(f"we{r}_{col}") / 2 for col in range(16)] for r in range(16)])

    # The strings, written in order through the blocks.
    pd = np.rint(v.array("pd{}", 96)).astype(np.int64)
    rg = {k: round(v(f"rg{j}")) for j, k in enumerate(sorted(regexes))}
    plan = plan_strings(round(v("ns")), pd, {k: c for k, c in rg.items() if c > 0}, regexes)

    tail = bytearray(total)
    prev = np.bincount(np.frombuffer(enc.z[(n // STEP - 1) * STEP:n // STEP * STEP], dtype=np.uint8) >> 4, minlength=16)
    for j in range(n // STEP, -(-end // STEP)):
        lo, hi = j * STEP, (j + 1) * STEP
        k = j - 1 - w0  # block j closes window j - 1 (blocks j - 1 and j)
        row = int(rows[min(k, rows.size - 1)]) if rows.size and k >= 0 else -1
        segs = [(max(lo, f0), min(hi, f1), p) for f0, f1, p in free if max(lo, f0) < min(hi, f1)]
        mask = np.ones(min(hi, end) - lo, dtype=bool)
        for s0, s1, _ in segs:
            mask[s0 - lo:s1 - lo] = False
        old = np.frombuffer(enc.z[lo:min(hi, n)], dtype=np.uint8)
        own = np.bincount(old >> 4, minlength=16) + np.asarray([int(mask[len(old):].sum())] + [0] * 15)
        fixed = prev + own
        for s0, s1, p in segs:
            avail = pools[p].reshape(16, 16).sum(axis=1)
            if row >= 0 and row < 16:
                cols = shape_block(fixed, s1 - s0, avail, np.maximum(target[row], 0), row)
                target[row] = np.maximum(target[row] - cols, 0)
            else:
                cols = allocate(s1 - s0, avail, avail)
            supply = sum(int(q[0x20:0x80].sum()) for q in pools)
            share = float(cols[2:8].sum()) / supply if supply else 0.0
            body = _place(cols, pools[p], plan, share, first=True)
            if len(body) != s1 - s0:
                raise RuntimeError(f"Block {j}: wrote {len(body)} bytes for {s1 - s0}.")
            tail[s0 - n:s1 - n] = body
            fixed = fixed + cols
            own = own + cols
        prev = own
    if any(p.sum() for p in pools):
        raise RuntimeError("Bytes left in the pools after the layout.")

    contents = []
    for (name, c, _, ch), (f0, f1, _) in zip(sections, free, strict=False):
        contents.append((name, bytes(tail[f0 - n:f1 - n]), ch))
    a0, a1, _ = free[-1]
    edited = write(enc.z, Choice(tuple(contents), bytes(tail[a0 - n:a1 - n])))
    if edited is None:
        raise RuntimeError("A section header did not fit.")
    if len(edited) != end:
        raise RuntimeError(f"Wrote {len(edited)} bytes, expected {end}.")
    return edited
