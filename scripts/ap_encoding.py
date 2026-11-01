"""
Direction A', step 4: the edit-choice encoding (docs/direction-A-prime-encoding.md).

The solver's variables are the attacker's choices in the edit catalogue (add up to K sections, then append), and every
feature those edits move is written as a function of the choices, starting from the file's item table: the old sums
plus what the added items contribute (C1, now over a whole family of edits), and the readouts on top (C3). Sums,
counts, hashed buckets, and ratios are exact (a ratio's split clears its positive denominator); entropies are bounded
soundly from concavity (Gibbs' inequality above, chords below); the bytes the edits write into the header (the
section-table entry, the rewritten size fields) are free bytes. Every relaxation widens: the encoded region contains
every file the catalogue can produce, so a proof that no point in it evades is a certificate.

The edits are those of `scripts/catalogue_checks.py` (`add_section(..., before_overlay=False)`, then concatenation),
which also writes the files the encoding is tested against (`scripts/ap_containment.py`).
"""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
import math
from pathlib import Path
import re
import sys
import time
from typing import Any
from typing import Optional
from typing import Union

import highspy
import numpy as np
import pefile
from scipy.sparse import coo_matrix
from scipy.sparse import csc_matrix

from provexp.featuresets.ember2024.catalogue import precondition
from provexp.featuresets.ember2024.features import ByteEntropyHistogram
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import StringExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.items import Entropy
from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Max
from provexp.items import Min
from provexp.items import Normalized
from provexp.items import Ratio
from provexp.items import Selection
from provexp.items import feature_hash

sys.path.insert(0, str(Path(__file__).parent))
from ap_check0_solver import Ensemble  # noqa: E402
from catalogue_checks import PAGE  # noqa: E402
from catalogue_checks import add_section  # noqa: E402

__all__ = [
    "Choice",
    "Encoding",
    "Ent",
    "FLAGS",
    "Frac",
    "Lin",
    "MaxOf",
    "NotCovered",
    "Program",
    "budget",
    "certify",
    "dominance_cuts",
    "dominant_share",
    "fano_share",
    "least_share",
    "link_ensemble",
    "pinsker_radius",
    "props_of",
    "regex_requirements",
    "write",
]

# The section flags an added section may carry (loader-safe; single bits, so pefile's flag names are exact).
FLAGS: dict[str, int] = {
    "CNT_CODE": 0x00000020,
    "CNT_INITIALIZED_DATA": 0x00000040,
    "MEM_DISCARDABLE": 0x02000000,
    "MEM_EXECUTE": 0x20000000,
    "MEM_READ": 0x40000000,
    "MEM_WRITE": 0x80000000,
}
# The header fields an added section rewrites, with their sizes in bytes.
FIELDS: dict[str, int] = {"NumberOfSections": 2, "SizeOfImage": 4, "SizeOfCode": 4, "SizeOfInitializedData": 4}
# A section name's options: the 100 (bucket, sign) pairs of the 50-bucket signed hash, then the empty name.
BUCKETS = 50
EMPTY = 2 * BUCKETS
WINDOW, STEP = 2048, 1024
PRINTABLE = (0x20, 0x80)
SECTION_ENTRY = 40
# NOTE: tolerances that widen every split (features are float32; thresholds float64): relative for ratios and
# integer-valued features, absolute for entropies.
TOL_REL = 1e-6
TOL_ENT = 1e-5
# Coefficients smaller than this (relative to a row's largest) are folded into its bounds (HiGHS drops them).
SMALL_COEF = 1e-8
# The largest unit a continuous variable is scaled by for the solver.
MAX_UNIT = np.inf
# HiGHS's feasibility tolerances (on the scaled program): one byte in half a million needs well below the default 1e-7.
FEASIBILITY_TOL = 1e-9
# The Gibbs reference distributions mix the old distribution with the uniform one by these weights.
GIBBS_MIX = (1e-3, 0.05, 0.3)
# The entropy levels of the per-window Gibbs references (each level's 16 one-nibble boundary distributions).
GIBBS_LEVELS = (0.5, 1.0, 2.0, 3.0)
# The thresholds every added section's entropy variable is tied to its byte counts at (besides the ensemble's own
# thresholds on the section-entropy maxima): for the entropy-hash buckets, whose splits are on sums of them.
SECTION_GRID = tuple(float(t) for t in np.arange(0.5, 8.0, 0.5))
# The pefile warnings the catalogue reaches, and their number.
WARN_BYTE = "pefilewarnings:warning_Byte 0x..."
WARN_FLAGS = "pefilewarnings:warning_Suspicious flags set for section..."
WARN_COUNT = "pefilewarnings:num_warnings"
# The names of the choice variables (reported with a solver's evasion).
CHOICE = re.compile(r"^(D|A|a\d+|s\d+|on\d+|m\d+|c\d+|pages\d+|e\d+|y\d+_\d+|fl\d+_\w+|q\d+_\w+)$")


_STRINGS = StringExtractor()  # type: ignore[no-untyped-call]
_BYTE_ENTROPY = ByteEntropyHistogram(STEP, WINDOW)  # type: ignore[no-untyped-call]


class NotCovered(Exception):
    """A file the encoding does not cover (precondition, layout); it gets no certificate."""


################################################################################
# Linear expressions and the values features take
################################################################################


class Lin:
    """A linear expression `const + sum(coef * var)` over the program's variables."""

    __slots__ = ("const", "terms")

    def __init__(self, const: float = 0.0, terms: Optional[dict[int, float]] = None) -> None:
        self.const = float(const)
        self.terms: dict[int, float] = terms if terms is not None else {}

    @staticmethod
    def of(var: int, coef: float = 1.0) -> Lin:
        return Lin(0.0, {var: float(coef)})

    @staticmethod
    def total(parts: Iterable[Union[Lin, float]]) -> Lin:
        """The sum of the parts, accumulated in one expression."""
        out = Lin()
        for p in parts:
            out._iadd(p, 1.0)
        return out

    def _iadd(self, other: Union[Lin, float], k: float) -> None:
        if isinstance(other, Lin):
            self.const += k * other.const
            for v, c in other.terms.items():
                self.terms[v] = self.terms.get(v, 0.0) + k * c
        else:
            self.const += k * float(other)

    def __add__(self, other: Union[Lin, float]) -> Lin:
        out = Lin(self.const, dict(self.terms))
        out._iadd(other, 1.0)
        return out

    __radd__ = __add__

    def __sub__(self, other: Union[Lin, float]) -> Lin:
        out = Lin(self.const, dict(self.terms))
        out._iadd(other, -1.0)
        return out

    def __rsub__(self, other: Union[Lin, float]) -> Lin:
        return (-1.0) * self + other

    def __mul__(self, k: float) -> Lin:
        return Lin(self.const * k, {v: c * k for v, c in self.terms.items()})

    __rmul__ = __mul__

    def __neg__(self) -> Lin:
        return self * -1.0

    def __repr__(self) -> str:
        return f"Lin({self.const:g} + {len(self.terms)} terms)"


@dataclass(frozen=True)
class Frac:
    """num / den with den >= 0 (a ratio readout, a normalized bin, a size over the file size)."""

    num: Lin
    den: Lin


@dataclass(frozen=True)
class Ent:
    """
    The entropy (bits) of the distribution counts / total. `lo` and `hi` bound each share over the whole region (for the
    chords); `refs` are the reference distributions of Gibbs' inequality (each entry positive); `floor` is a lower bound
    on entropy * total (`mixture_floor`). Optionally (`Program.deviation`, `Program.largest`): `dev` is at least the L1
    distance of the counts from the uniform split of the total over `symbols` symbols (for `pinsker_radius`), and
    `top` at most the largest count (for `dominant_share`).
    """

    counts: tuple[Lin, ...]
    total: Lin
    lo: np.ndarray
    hi: np.ndarray
    refs: tuple[np.ndarray, ...]
    floor: Lin
    dev: Optional[Lin] = None
    top: Optional[Lin] = None
    symbols: int = 256


@dataclass(frozen=True)
class MaxOf:
    """The maximum of some candidate values and a constant (the old items' values and the floor)."""

    candidates: tuple[Value, ...]
    const: float


FREE = "free"
Value = Union[float, Lin, Frac, Ent, MaxOf, str]


def _plogp(p: float) -> float:
    return -p * math.log2(p) if p > 0 else 0.0


def share_bounds(c_old: np.ndarray, rem: np.ndarray, h: float, t_lo: float, t_hi: float, gmax: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Bounds on each share c / T when each count c is its old value less at most `rem` plus at most `h + g` and the total
    T lies in [t_lo + g, t_hi] for a gain g in [0, gmax]: the lower bound at the largest total, the upper bound at an
    end of the gain's range ((c + h + g) / (t_lo + g) is monotone in g).
    """
    lo = np.clip((c_old - rem) / max(t_hi, 1.0), 0.0, 1.0)
    f0 = (c_old + h) / max(t_lo, 1.0)
    f1 = (c_old + h + gmax) / max(t_lo + gmax, 1.0)
    hi = np.clip(np.maximum(f0, f1), 0.0, 1.0)
    return lo, np.maximum(hi, lo)


def mixture_floor(total: float, entropy: float, removed: float, symbols: int) -> float:
    """
    A lower bound on H' * T' for a distribution made from an old one (T counts, entropy H) by removing at most `removed`
    counts and adding any. By concavity (the entropy of a mixture is at least its weighted entropies), adding never
    lowers H * T; removing R counts lowers it by at most R log2(symbols) + T h(R / T), with h the binary entropy
    (the entropy of a mixture is at most its weighted entropies plus the mixing weights' entropy).
    """
    if total <= 0 or entropy <= 0:
        return 0.0
    r = min(removed, total)
    if r >= total / 2:
        return 0.0
    w = r / total
    h = -w * math.log2(w) - (1 - w) * math.log2(1 - w) if 0 < w < 1 else 0.0
    return max(0.0, total * entropy - r * math.log2(symbols) - total * h)


def pinsker_radius(t: float, symbols: int) -> float:
    """
    Pinsker's inequality in bits, D(p || u) >= ||p - u||_1^2 / (2 ln 2), with D(p || u) = log2(symbols) - H(p): a
    distribution of entropy above t lies within this L1 distance of the uniform one (widened by TOL_ENT).
    """
    return math.sqrt(2.0 * math.log(2.0) * max(0.0, math.log2(symbols) - t + TOL_ENT))


def dominant_share(t: float) -> float:
    """
    The least largest share of a distribution of entropy at most t (widened by TOL_ENT): min-entropy is at most entropy
    (p_max >= 2^-t), and H >= h(p_max), the binary entropy, which below one bit puts p_max above h's inverse on [1/2, 1].
    """
    t = t + TOL_ENT
    out = 2.0 ** -t
    if t < 1.0:
        lo, hi = 0.5, 1.0  # h decreases on [1/2, 1]
        for _ in range(60):
            mid = (lo + hi) / 2
            if -mid * math.log2(mid) - (1 - mid) * math.log2(1 - mid) > t:
                lo = mid
            else:
                hi = mid
        out = max(out, lo)
    return float(out)


def least_share(t: float, symbols: int) -> float:
    """
    The least share every symbol must have in a distribution of entropy above t (widened by TOL_ENT): grouping one
    symbol against the rest, H <= h(p) + (1 - p) log2(symbols - 1), which increases in p on [0, 1 / symbols] from
    log2(symbols - 1); so above that entropy every symbol is present. Zero for t at most log2(symbols - 1).
    """
    t = t - TOL_ENT
    floor = math.log2(symbols - 1)
    if t <= floor:
        return 0.0

    def g(p: float) -> float:
        h = -p * math.log2(p) - (1 - p) * math.log2(1 - p) if 0 < p < 1 else 0.0
        return h + (1 - p) * floor

    lo, hi = 0.0, 1.0 / symbols
    for _ in range(60):
        mid = (lo + hi) / 2
        if g(mid) < t:
            lo = mid
        else:
            hi = mid
    return float(lo)


def fano_share(t: float, symbols: int = 16) -> float:
    """
    The largest share a distribution over `symbols` symbols with entropy at least t can have (widened by TOL_ENT):
    Fano's bound H <= h(p_max) + (1 - p_max) log2(symbols - 1), whose right side decreases in p_max on [1/symbols, 1].
    """
    t = t - TOL_ENT
    if t <= 0:
        return 1.0
    if t >= math.log2(symbols):
        return 1.0 / symbols

    def g(p: float) -> float:
        h = -p * math.log2(p) - (1 - p) * math.log2(1 - p) if 0 < p < 1 else 0.0
        return h + (1 - p) * math.log2(symbols - 1)

    lo, hi = 1.0 / symbols, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if g(mid) >= t:
            lo = mid
        else:
            hi = mid
    return float(hi)


def references(dists: Sequence[np.ndarray]) -> tuple[np.ndarray, ...]:
    """Gibbs reference distributions: each given distribution mixed with the uniform one."""
    out = []
    for d in dists:
        total = float(d.sum())
        p = d / total if total > 0 else np.full(d.size, 1.0 / d.size)
        out += [(1.0 - w) * p + w / d.size for w in GIBBS_MIX]
    return tuple(out)


def boundary_references(h: float, size: int = 16) -> tuple[np.ndarray, ...]:
    """
    Distributions of entropy exactly h (bits) concentrated on one symbol or two, mixed with the uniform one: Gibbs
    cuts at them are tangent to {H >= h} near its sharpest corners (the low-entropy distributions).
    """
    if not 0 < h < math.log2(size):
        raise ValueError(f"Entropy {h} outside (0, {math.log2(size)}).")
    out = []
    for centre in [[c] for c in range(size)] + [[c, d] for c in range(size) for d in range(c + 1, size)]:
        if len(centre) == 2 and h <= 1.0:
            continue  # the uniform pair already has entropy 1
        e = np.zeros(size)
        e[centre] = 1.0 / len(centre)
        lo, hi = 0.0, 1.0  # the entropy of (1 - w) e + w u rises with w from log2(len(centre)) to log2(size)
        for _ in range(60):
            w = (lo + hi) / 2
            q = (1.0 - w) * e + w / size
            if -float(np.sum(q * np.log2(q))) < h:
                lo = w
            else:
                hi = w
        out.append((1.0 - hi) * e + hi / size)
    return tuple(out)


# The Gibbs references of each byte-entropy row r >= 1 (a window in row r has nibble entropy at least r / 4).
ROW_REFS: dict[int, tuple[np.ndarray, ...]] = {r: boundary_references(r / 4 - TOL_ENT) for r in range(1, 16)}


def reachable_rows(counts: np.ndarray, moved: int) -> range:
    """
    The byte-entropy rows a window's nibble counts can reach when at most `moved` of its bytes are rewritten: the
    entropy is Schur-concave, so its extremes move counts one at a time from the largest to the smallest (highest) or
    from the smallest nonzero to the largest (lowest). Widened by TOL_ENT at both ends.
    """
    def row(c: np.ndarray, side: float) -> int:
        p = c[c > 0] / c.sum()
        h = float(-np.sum(p * np.log2(p))) + side * TOL_ENT
        return min(15, max(0, int(math.floor(4 * h))))

    hi, lo = counts.astype(np.int64).copy(), counts.astype(np.int64).copy()
    for _ in range(moved):
        hi[np.argmax(hi)] -= 1
        hi[np.argmin(hi)] += 1
        nz = np.flatnonzero(lo)
        if nz.size > 1:
            src = nz[np.argmin(lo[nz])]
            lo[src] -= 1
            lo[np.argmax(lo)] += 1
    return range(row(lo, -1.0), row(hi, 1.0) + 1)


def row_cuts(P: Program, counts: Sequence[Lin], windows: Lin, r: int) -> None:
    """
    A byte-entropy row's nibble counts (over `windows` windows of WINDOW bytes, all in row r): each window has nibble
    entropy at least r / 4, so by concavity their pooled distribution does too, and by Gibbs' inequality
    sum_c counts_c * (-log2 q_c) >= (r / 4) * WINDOW * windows for every distribution q (linear).
    """
    for q in ROW_REFS.get(r, ()):
        cross = Lin.total(x * float(-math.log2(w)) for x, w in zip(counts, q.tolist(), strict=True))
        P.row(cross - windows * ((r / 4 - TOL_ENT) * WINDOW), lo=0.0)


def dominance_cuts(P: Program, counts: Sequence[Lin], windows: Lin, r: int, name: str, most: float) -> None:
    """
    The upper side of byte-entropy row r (the lower side is `row_cuts`): a window in row r has nibble entropy below
    (r + 1) / 4, and min-entropy is at most entropy, so one nibble holds more than theta = WINDOW * 2^-((r + 1) / 4)
    of its counts. Pooled over the row's `windows` windows (at most `most`): `n_c` of them dominated by nibble c,
    holding at least theta and at most WINDOW of c each (`m_c`, at most the row's count of c), and the counts outside
    the dominant nibbles at most (WINDOW - theta) per window. Sound: every real window meets it, so their sums do.
    """
    if r >= 15:
        return  # row 15 has no upper side
    theta = WINDOW * 2.0 ** -((r + 1) / 4 + TOL_ENT)
    n = [P.var(f"{name}n{r}_{c}", 0, most, integer=True) for c in range(16)]
    m = [P.var(f"{name}m{r}_{c}", 0, most * WINDOW) for c in range(16)]
    P.row(Lin.total(Lin.of(x) for x in n) - windows, 0, 0)
    for c in range(16):
        P.row(Lin.of(m[c]) - Lin.of(n[c], theta), lo=0)
        P.row(Lin.of(m[c]) - Lin.of(n[c], WINDOW), hi=0)
        P.row(Lin.of(m[c]) - counts[c], hi=0)
    P.row(Lin.total(counts) - Lin.total(Lin.of(x) for x in m) - windows * (WINDOW - theta), hi=0)


_HEX = frozenset(b"0123456789abcdefABCDEF")
_DIGITS = frozenset(b"0123456789")
# The characters every match of a non-plain regex holds (a sound minimum; base64string is left out).
_REQUIRED: dict[str, list[tuple[frozenset[int], int]]] = {
    ".click(": [(frozenset(b"cC"), 2), (frozenset(b"lL"), 1), (frozenset(b"iI"), 1), (frozenset(b"kK"), 1)],
    "ipv4_addr": [(frozenset(b"."), 3), (_DIGITS, 4)],
    "ipv6_addr": [(frozenset(b":"), 2)],
    "mac_addr": [(frozenset(b":-"), 5), (_HEX, 12)],
    "email_addr": [(frozenset(b":-"), 5), (_HEX, 12)],
    "url": [(frozenset(b":"), 1), (frozenset(b"/"), 2)],
    "registry_key": [(frozenset(b"K"), 1), (frozenset(b"H"), 1)],
    "btc_wallet": [(frozenset(b"13"), 1), (frozenset(b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"), 26)],
}


def regex_requirements(regexes: dict[str, re.Pattern[str]]) -> dict[str, list[tuple[frozenset[int], int]]]:
    """
    Per regex, the characters every string matching it holds: (the byte values that count, how many). A plain word
    (its pattern without word boundaries has no special character) holds each of its characters, either case when the
    regex ignores case; the others are listed by hand (`_REQUIRED`).
    """
    out: dict[str, list[tuple[frozenset[int], int]]] = {}
    for k, r in regexes.items():
        word = r.pattern.replace("\\b", "")
        if k in _REQUIRED:
            out[k] = _REQUIRED[k]
        elif not set(word) & set(".^$*+?{}[]()|\\"):
            counts: dict[frozenset[int], int] = {}
            for ch in word:
                key = frozenset({ord(ch.lower()), ord(ch.upper())} if r.flags & re.IGNORECASE else {ord(ch)})
                counts[key] = counts.get(key, 0) + 1
            out[k] = list(counts.items())
    return out


################################################################################
# The program
################################################################################


class Program:
    """A mixed-integer linear program built row by row (HiGHS through scipy)."""

    def __init__(self) -> None:
        self.lb: list[float] = []
        self.ub: list[float] = []
        self.integer: list[bool] = []
        self.names: list[str] = []
        self._rows: list[int] = []
        self._cols: list[int] = []
        self._vals: list[float] = []
        self.rlo: list[float] = []
        self.rhi: list[float] = []
        self.switch: list[int] = []
        # Binaries fixed both ways (a held-fixed feature on the wrong side of a fixed split): the program is infeasible.
        self.conflicts: list[str] = []
        # Variables equal to an entropy: a split on the variable also gets the entropy's rows.
        self.tied: dict[int, Ent] = {}

    def var(self, name: str, lb: float = 0.0, ub: float = 1.0, integer: bool = False) -> int:
        if not lb <= ub:
            raise ValueError(f"Empty bounds for {name}: [{lb}, {ub}].")
        self.lb.append(float(lb))
        self.ub.append(float(ub))
        self.integer.append(integer)
        self.names.append(name)
        return len(self.lb) - 1

    def binary(self, name: str) -> int:
        return self.var(name, 0.0, 1.0, integer=True)

    def fix(self, var: int, value: float) -> None:
        self.lb[var] = self.ub[var] = float(value)

    def bounds(self, x: Lin) -> tuple[float, float]:
        """Interval bounds of an expression from its variables' bounds."""
        lo = hi = x.const
        for v, c in x.terms.items():
            if c > 0:
                lo += c * self.lb[v]
                hi += c * self.ub[v]
            else:
                lo += c * self.ub[v]
                hi += c * self.lb[v]
        return lo, hi

    def row(self, x: Lin, lo: float = -np.inf, hi: float = np.inf, switch: int = -1) -> None:
        """lo <= x <= hi (scaled when solved, ignoring a big-M `switch` binary's coefficient)."""
        terms = {v: c for v, c in x.terms.items() if c != 0.0}
        if not terms:
            if not lo - 1e-9 <= x.const <= hi + 1e-9:
                raise ValueError(f"Infeasible constant row: {lo} <= {x.const} <= {hi}.")
            return
        r = len(self.rlo)
        for v, c in terms.items():
            self._rows.append(r)
            self._cols.append(v)
            self._vals.append(c)
        self.rlo.append(lo - x.const)
        self.rhi.append(hi - x.const)
        self.switch.append(switch)

    def restrict(self, z: int, value: float) -> None:
        """Fix a binary, recording a conflict if it was already fixed to the other value."""
        lo, hi = max(self.lb[z], value), min(self.ub[z], value)
        if lo > hi:
            self.conflicts.append(self.names[z])
            return
        self.lb[z], self.ub[z] = lo, hi

    def at_most_when(self, x: Lin, z: int, when: int) -> None:
        """x <= 0 whenever the binary z equals `when` (big-M from the bounds)."""
        lo, hi = self.bounds(x)
        if hi <= 0:
            return
        if lo > 0:  # x <= 0 is impossible: z cannot take the value `when`
            self.restrict(z, 1.0 - when)
            return
        # when = 1: x <= hi * (1 - z); when = 0: x <= hi * z.
        self.row(x + Lin.of(z, hi) if when == 1 else x - Lin.of(z, hi), hi=hi if when == 1 else 0.0, switch=z)

    def link(self, value: Value, t: float, z: int, integral: bool = False) -> None:
        """
        z = 1 if the value is at most t, 0 if above (soundly widened: ties and rounding allow both sides). An
        `integral` value (a count, a size) is at most floor(t) or at least floor(t) + 1.
        """
        if isinstance(value, str):
            return
        if isinstance(value, (int, float)):
            self.restrict(z, float(float(value) <= t))
            return
        if isinstance(value, Lin) and integral:
            self.at_most_when(value - math.floor(t), z, when=1)
            self.at_most_when((math.floor(t) + 1) - value, z, when=0)
            return
        if isinstance(value, Lin):
            d = TOL_REL * max(1.0, abs(t))
            self.at_most_when(value - (t + d), z, when=1)
            self.at_most_when((t - d) - value, z, when=0)
            if value.const == 0.0 and len(value.terms) == 1:
                (v, coef), = value.terms.items()
                if coef == 1.0 and v in self.tied:
                    self._link_entropy(self.tied[v], t, z)
            return
        if isinstance(value, Frac):
            # NOTE: relative only: shares are split at thresholds as small as 1e-35, and float32 division is off by at
            # most ~6e-8 of the value.
            d = TOL_REL * abs(t)
            self.at_most_when(value.num - (t + d) * value.den, z, when=1)
            if 0 <= t and t * self.bounds(value.den)[1] < 1:
                # Below one count's share: above it means at least one count (the numerators are counts or sizes).
                self.at_most_when(1.0 - value.num, z, when=0)
            else:
                self.at_most_when((t - d) * value.den - value.num, z, when=0)
            return
        if isinstance(value, Ent):
            self._link_entropy(value, t, z)
            return
        if isinstance(value, MaxOf):
            if value.const > t:
                self.restrict(z, 0.0)
                return
            ws = []
            for k, cand in enumerate(value.candidates):
                w = self.binary(f"max_w{k}")
                self.link(cand, t, w)
                self.row(Lin.of(z) - Lin.of(w), hi=0.0)  # max <= t -> every candidate <= t
                ws.append(w)
            if not ws:
                self.restrict(z, 1.0)
                return
            # max > t -> some candidate > t.
            self.row(Lin.of(z) - Lin.total(Lin.of(w) for w in ws), lo=1.0 - len(ws))
            return
        raise TypeError(f"Unknown value {value!r}.")

    def _link_entropy(self, e: Ent, t: float, z: int) -> None:
        # H <= t (z = 1): the chords of -p log p lie below it on each share's range, so their sum is <= H <= t.
        chord = Lin()
        for c, lo, hi in zip(e.counts, e.lo.tolist(), e.hi.tolist(), strict=True):
            slope = (_plogp(hi) - _plogp(lo)) / (hi - lo) if hi - lo > 1e-12 else 0.0
            chord._iadd(e.total, _plogp(lo) - slope * lo)
            chord._iadd(c, slope)
        self.at_most_when(chord - (t + TOL_ENT) * e.total, z, when=1)
        # H <= t (z = 1) also needs H * T, at least the mixture floor, to be at most t * T.
        self.at_most_when(e.floor - (t + TOL_ENT) * e.total, z, when=1)
        # H > t (z = 0): Gibbs' inequality H(p) <= -sum p log q for every distribution q, so each such sum is > t.
        for q in e.refs:
            gibbs = Lin.total(c * float(-math.log2(w)) for c, w in zip(e.counts, q.tolist(), strict=True))
            self.at_most_when((t - TOL_ENT) * e.total - gibbs, z, when=0)
        # H > t (z = 0): within Pinsker's L1 distance of uniform (useful only below the trivial distance 2).
        r = pinsker_radius(t, e.symbols)
        if e.dev is not None and r < 2.0:
            # Big-M from the L1 distance's own bound (at most 2 * total, with each deviation at its least), far smaller
            # than one from the deviation variables' bounds (the symbol count times the largest total).
            m = (2.0 - r) * self.bounds(e.total)[1]
            self.row(e.dev - r * e.total - Lin.of(z, m), hi=0.0, switch=z)
        # H > t (z = 0) near the maximum: every symbol holds at least the least share.
        least = least_share(t, e.symbols)
        if least > 0.0:
            for c in e.counts:
                self.at_most_when(e.total * least - c, z, when=0)
        # H <= t (z = 1): some symbol holds at least the dominant share.
        if e.top is not None and t < math.log2(e.symbols):
            self.at_most_when(dominant_share(t) * e.total - e.top, z, when=1)

    def deviation(self, name: str, counts: Sequence[Lin], total: Lin) -> Lin:
        """A sum of variables at least the L1 distance of `counts` from total / len(counts) each (Ent.dev)."""
        ub = self.bounds(total)[1]
        out = Lin()
        for v, c in enumerate(counts):
            d = self.var(f"{name}dev{v}", 0.0, ub)
            self.row(Lin.of(d) - c + total * (1.0 / len(counts)), lo=0.0)
            self.row(Lin.of(d) + c - total * (1.0 / len(counts)), lo=0.0)
            out._iadd(Lin.of(d), 1.0)
        return out

    def largest(self, name: str, counts: Sequence[Lin], ub: float) -> Lin:
        """A variable at most the largest of `counts` (each at most `ub`): at most the count of a chosen symbol (Ent.top)."""
        top = self.var(f"{name}top", 0.0, ub)
        d = [self.binary(f"{name}dom{v}") for v in range(len(counts))]
        self.row(Lin.total(Lin.of(x) for x in d), 1, 1)
        for c, x in zip(counts, d, strict=True):
            self.row(Lin.of(top) - c + Lin.of(x, ub), hi=ub, switch=x)
        return Lin.of(top)

    def product(self, name: str, x: Lin, ub: float, b: int) -> int:
        """A variable equal to x * b for a binary b and 0 <= x <= ub (exact)."""
        p = self.var(name, 0.0, ub)
        self.row(Lin.of(p) - Lin.of(b, ub), hi=0.0)
        self.row(Lin.of(p) - x, hi=0.0)
        self.row(Lin.of(p) - x - Lin.of(b, ub), lo=-ub)
        return p

    def solve(self, objective: Optional[dict[int, float]] = None, time_limit: float = 60.0) -> Any:
        """
        Solve with HiGHS. NOTE: byte amounts reach millions next to 0/1 binaries in the same rows, which stalls even
        the LP relaxation, while some splits need single-byte precision (a share of 1e-7 is one count in a 4 MB
        file). So the solver sees each continuous variable in units of its largest magnitude capped at MAX_UNIT (the
        feasibility tolerance stays far below one byte), and each row divided by its largest coefficient other than its
        big-M switch's. HiGHS drops coefficients below 1e-9, which could tighten a row and exclude real files, so
        coefficients below SMALL_COEF of a row's scale are removed here and the row's bounds widened by their largest
        effect: rows only loosen. The returned `x` is in the original units.
        """
        if self.conflicts:
            return _Infeasible(f"conflicting fixed binaries: {self.conflicts[:5]}")
        n = len(self.lb)
        lb, ub = np.array(self.lb), np.array(self.ub)
        unit = np.where(np.array(self.integer), 1.0, np.clip(np.maximum(np.abs(lb), np.abs(ub)), 1.0, MAX_UNIT))
        rows, cols = np.array(self._rows, dtype=np.int64), np.array(self._cols, dtype=np.int64)
        vals = np.array(self._vals) * unit[cols]
        rlo, rhi = np.array(self.rlo), np.array(self.rhi)
        if rows.size:
            s = np.zeros(len(rlo))
            switch = np.array(self.switch, dtype=np.int64)
            own = cols != switch[rows]
            np.maximum.at(s, rows[own], np.abs(vals[own]))
            s = np.where(s > 0, s, 1.0)
            small = (np.abs(vals) < SMALL_COEF * s[rows]) & own
            # Each dropped term moves its row by at most |coefficient| * max |scaled variable| (<= 1 for continuous).
            slack = np.zeros(len(rlo))
            np.add.at(slack, rows[small], np.abs(vals[small]) * np.maximum(np.abs(lb), np.abs(ub))[cols[small]] / unit[cols[small]])
            rlo, rhi = (rlo - slack) / s, (rhi + slack) / s
            keep = ~small
            rows, cols, vals = rows[keep], cols[keep], vals[keep] / s[rows[keep]]
        a = coo_matrix((vals, (rows, cols)), shape=(len(rlo), n)).tocsr()
        c = np.zeros(n)
        for v, k in (objective or {}).items():
            c[v] = k
        c = c * unit
        integer = np.array(self.integer, dtype=bool)

        def run(presolve: bool, seconds: float) -> _Result:
            return _highs(c, integer, lb / unit, ub / unit, a, rlo, rhi, presolve, seconds)

        t0 = time.time()
        res = run(True, time_limit)
        if res.status == 2:
            # NOTE: HiGHS's presolve has declared a feasible program infeasible at these tolerances (containment, run
            # 113): an infeasibility stands only if the solve without presolve confirms it (given the remaining time,
            # and at least a minute); otherwise that solve's outcome is returned.
            res = run(False, max(60.0, time_limit - (time.time() - t0)))
        if res.x is not None:
            res.x = res.x * unit
        return res


@dataclass
class _Result:
    """A solver result: scipy's `milp` status codes (0 optimal, 1 limit, 2 infeasible, 4 other), the solution if one
    was found, and HiGHS's MIP statistics (the dual bound survives a time limit, unlike scipy's wrapper's)."""

    status: int
    message: str
    x: Optional[np.ndarray]
    mip_dual_bound: Optional[float]
    mip_gap: Optional[float]
    mip_node_count: Optional[int]


def _highs(c: np.ndarray, integer: np.ndarray, lb: np.ndarray, ub: np.ndarray, a: Any, rlo: np.ndarray,
           rhi: np.ndarray, presolve: bool, seconds: float) -> _Result:
    """
    Minimize c @ x subject to rlo <= a @ x <= rhi and lb <= x <= ub, `integer` columns integral, with HiGHS (highspy).

    NOTE: called directly rather than through `scipy.optimize.milp`, whose wrapper drops the dual bound when the time
    limit stops a solve that found no feasible point (every open solve of run 114), which is the bracket's floor.
    """
    inf = highspy.kHighsInf
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = int(c.size), int(len(rlo))
    lp.col_cost_ = np.asarray(c, dtype=np.float64)
    lp.col_lower_ = np.where(np.isfinite(lb), lb, -inf)
    lp.col_upper_ = np.where(np.isfinite(ub), ub, inf)
    lp.row_lower_ = np.where(np.isfinite(rlo), rlo, -inf)
    lp.row_upper_ = np.where(np.isfinite(rhi), rhi, inf)
    m = csc_matrix(a) if lp.num_row_ else csc_matrix((0, c.size))
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.num_col_, lp.a_matrix_.num_row_ = lp.num_col_, lp.num_row_
    lp.a_matrix_.start_ = m.indptr.astype(np.int32)
    lp.a_matrix_.index_ = m.indices.astype(np.int32)
    lp.a_matrix_.value_ = m.data.astype(np.float64)
    lp.integrality_ = [highspy.HighsVarType.kInteger if i else highspy.HighsVarType.kContinuous for i in integer]
    h = highspy.Highs()  # type: ignore[no-untyped-call]
    for k, v in {"output_flag": False, "threads": 1, "time_limit": float(seconds), "presolve": "on" if presolve else "off",
                 "primal_feasibility_tolerance": FEASIBILITY_TOL, "dual_feasibility_tolerance": FEASIBILITY_TOL,
                 "mip_feasibility_tolerance": FEASIBILITY_TOL}.items():
        h.setOptionValue(k, v)
    h.passModel(lp)
    h.run()
    ms = h.getModelStatus()
    info = h.getInfo()
    S = highspy.HighsModelStatus
    if ms == S.kOptimal:
        status = 0
    elif ms in (S.kTimeLimit, S.kIterationLimit, S.kSolutionLimit, S.kInterrupt):
        status = 1
    elif ms == S.kInfeasible:
        status = 2
    else:
        status = 4  # including "unbounded or infeasible": never read as a certificate
    feasible = info.primal_solution_status == highspy.SolutionStatus.kSolutionStatusFeasible
    x = np.array(h.getSolution().col_value) if feasible else None
    dual = float(info.mip_dual_bound)
    return _Result(status, h.modelStatusToString(ms), x, dual if abs(dual) < inf else None,
                   float(info.mip_gap), int(info.mip_node_count))


@dataclass
class _Infeasible:
    """A solver result for a program infeasible by its bounds alone."""

    message: str
    status: int = 2
    x: Optional[np.ndarray] = None


################################################################################
# The catalogue: add up to K sections, then append
################################################################################


@dataclass(frozen=True)
class Choice:
    """One edit of the catalogue: sections (name, content, characteristics) added in order, then an append."""

    sections: tuple[tuple[bytes, bytes, int], ...]
    append: bytes


def budget(n: int, frac: float, minimum: int) -> int:
    """The byte budget of Table A1's protocol: max(frac of the file's size, minimum)."""
    return max(int(frac * n), minimum)


def write(z: bytes, choice: Choice) -> Optional[bytes]:
    """The edited file, written by our own byte-level edits, or None if a section header does not fit."""
    for name, content, characteristics in choice.sections:
        out = add_section(z, name, content, characteristics, before_overlay=False)
        if out is None:
            return None
        z = out[0]
    return z + choice.append


def props_of(characteristics: int) -> list[str]:
    """The flag names thrember hashes for a section's characteristics (pefile's flags whose bits overlap)."""
    return [k[len("IMAGE_SCN_"):] for k, v in pefile.section_characteristics if v & characteristics]


def name_key(name: bytes) -> str:
    """A section name as thrember reads it."""
    return name.strip(b"\x00").decode(errors="ignore").lower()


def option(key: str, empty: bool = True) -> int:
    """The name option a key hashes to: 2 * bucket (+ 1 for a negative sign), or EMPTY for the empty name."""
    if key == "" and empty:
        return EMPTY
    (b,), (s,) = feature_hash(BUCKETS, [key])
    return 2 * int(b) + (0 if s > 0 else 1)


def _align(x: int, a: int) -> int:
    return (x + a - 1) // a * a if a else x


def free_slots(pe: pefile.PE, z: bytes) -> list[int]:
    """The offsets of the free section-header slots, in the order `add_section` fills them."""
    start = pe.DOS_HEADER.e_lfanew + 4 + 20 + pe.FILE_HEADER.SizeOfOptionalHeader
    slot = start + SECTION_ENTRY * pe.FILE_HEADER.NumberOfSections
    first = min((s.PointerToRawData for s in pe.sections if s.SizeOfRawData and s.PointerToRawData), default=len(z))
    limit = min(pe.OPTIONAL_HEADER.SizeOfHeaders, first, len(z))
    out = []
    while slot + SECTION_ENTRY <= limit and not any(z[slot:slot + SECTION_ENTRY]):
        out.append(slot)
        slot += SECTION_ENTRY
    return out


def _printable(b: int) -> bool:
    return PRINTABLE[0] <= b < PRINTABLE[1]


def _widen(z: bytes, lo: int, hi: int) -> tuple[int, int]:
    """A written range widened to the printable runs around it (a string's extent depends only on its neighbors)."""
    while lo > 0 and _printable(z[lo - 1]):
        lo -= 1
    while hi < len(z) and _printable(z[hi]):
        hi += 1
    return lo, hi


def _merge(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for lo, hi in sorted(ranges):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def _meets(item: Item, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(lo < b and a < hi for a, b in item.members for lo, hi in ranges)


def _sums(table: ItemTable, items: Sequence[Item]) -> dict[str, np.ndarray]:
    return ItemTable(table.num_elements, table.families, list(items)).sums


################################################################################
# The encoding of one file
################################################################################


class Encoding:
    """
    The choice block of one file and the value of every feature as a function of it.

    Attributes:
        program: The program (choice variables and their rows; the ensemble is linked by `link_ensemble`).
        values: Feature index -> its value (a constant when no edit in the catalogue moves it).
        x0: The file's feature vector.
        k: The number of section slots encoded (min(K, free header slots)).
        budget: The byte budget.
    """

    def __init__(self, extractor: PEFeatureExtractor, z: bytes, budget_bytes: int, max_sections: int) -> None:
        pe = pefile.PE(data=z)
        table = extractor.item_table(z)
        if not precondition(pe, table):
            raise NotCovered("precondition")
        oh = pe.OPTIONAL_HEADER
        fa, sa = int(oh.FileAlignment), int(oh.SectionAlignment)
        if sa < PAGE or fa <= 0 or sa % fa:
            raise NotCovered(f"alignment (FileAlignment {fa}, SectionAlignment {sa})")
        n = len(z)
        if n < 2 * WINDOW:
            raise NotCovered("shorter than two windows")
        self.z, self.n, self.fa, self.sa = z, n, fa, sa
        self.x0 = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
        self.budget = B = int(budget_bytes)
        slots = free_slots(pe, z)
        self.k = k = min(max_sections, len(slots))
        sums = table.sums
        P = self.program = Program()

        # The amounts: bytes added in all (D), appended (A, a), added as section content (s).
        D = P.var("D", 0, B)
        A = P.var("A", 0, B)
        a = [P.var(f"a{v}", 0, B) for v in range(256)]
        s = [P.var(f"s{v}", 0, B) for v in range(256)]
        P.row(Lin.total(Lin.of(x) for x in a) - Lin.of(A), 0, 0)

        # The sections.
        self.on = on = [P.binary(f"on{i}") for i in range(k)]
        self.zs = zs = [P.binary(f"zs{i}") for i in range(k)]
        self.m = m = [P.var(f"m{i}", 0, B // fa, integer=True) for i in range(k)]
        self.c = c = [P.var(f"c{i}", 0, B) for i in range(k)]
        self.pages = pages = [P.var(f"pages{i}", 0, B // sa + 1, integer=True) for i in range(k)]
        self.e = e = [P.var(f"e{i}", 0, 8) for i in range(k)]
        self.y = y = [[P.binary(f"y{i}_{o}") for o in range(EMPTY + 1)] for i in range(k)]
        self.fl = fl = [{f: P.binary(f"fl{i}_{f}") for f in FLAGS} for i in range(k)]
        self.prop_names = {f: props_of(bit) for f, bit in FLAGS.items()}
        self.q = q = [{(f, pn): [P.binary(f"q{i}_{pn}_{o}") for o in range(EMPTY)] for f in FLAGS for pn in self.prop_names[f]}
                      for i in range(k)]
        raw = [Lin.of(m[i], fa) for i in range(k)]
        rx: list[int] = []
        rc: list[int] = []
        for i in range(k):
            if i:
                P.row(Lin.of(on[i]) - Lin.of(on[i - 1]), hi=0)
            P.row(raw[i] - Lin.of(c[i]), 0, fa - 1)  # padding to FileAlignment, exact
            P.row(Lin.of(m[i]) - Lin.of(on[i], B // fa), hi=0)
            P.row(Lin.of(zs[i]) - Lin.of(on[i]), hi=0)
            P.row(Lin.of(m[i]) + Lin.of(zs[i], B // fa), hi=B // fa)  # zero-size -> no raw data
            P.row(Lin.of(m[i]) - Lin.of(on[i]) + Lin.of(zs[i]), lo=0)  # added and not zero-size -> raw data
            P.row(Lin.of(pages[i], sa) - raw[i], 0, sa - fa)  # virtual pages, exact
            P.row(Lin.of(e[i]) - Lin.of(on[i], 8), hi=0)
            P.row(Lin.total(Lin.of(v) for v in y[i]) - Lin.of(on[i]), 0, 0)
            for f in FLAGS:
                P.row(Lin.of(fl[i][f]) - Lin.of(on[i]), hi=0)
                for pn in self.prop_names[f]:
                    P.row(Lin.total(Lin.of(v) for v in q[i][(f, pn)]) - Lin.of(fl[i][f]), 0, 0)
            r_, x_ = fl[i]["MEM_READ"], fl[i]["MEM_EXECUTE"]
            rx.append(P.binary(f"rx{i}"))
            P.row(Lin.of(rx[i]) - Lin.of(r_), hi=0)
            P.row(Lin.of(rx[i]) - Lin.of(x_), hi=0)
            P.row(Lin.of(rx[i]) - Lin.of(r_) - Lin.of(x_), lo=-1)
            rc.append(P.product(f"rc{i}", raw[i], B, fl[i]["CNT_CODE"]))
        P.row(Lin.total(Lin.of(x) for x in s) - Lin.total(Lin.of(x) for x in c), 0, 0)
        # Each section's own content counts (they sum to s), its data (content, then zero padding), and its entropy.
        self.sv = sv = [[P.var(f"s{i}_{v}", 0, B) for v in range(256)] for i in range(k)]
        for i in range(k):
            P.row(Lin.total(Lin.of(x) for x in sv[i]) - Lin.of(c[i]), 0, 0)
            P.row(Lin.of(e[i]) + Lin.of(zs[i], 8), hi=8)  # no data, entropy zero
        if k:
            for v in range(256):
                P.row(Lin.of(s[v]) - Lin.total(Lin.of(sv[i][v]) for i in range(k)), 0, 0)
        on0 = Lin.of(on[0]) if k else Lin()
        gap = _align(n, fa) - n
        pad = gap * on0 + Lin.total(raw[i] - Lin.of(c[i]) for i in range(k))
        P.row(Lin.of(D) - pad - Lin.total(Lin.of(c[i]) for i in range(k)) - Lin.of(A), 0, 0)
        P.row(Lin.of(D), hi=B)
        self.D, self.A, self.a, self.s = D, A, a, s
        for i in range(k):
            data = [Lin.of(sv[i][v]) + ((raw[i] - Lin.of(c[i])) if v == 0 else 0.0) for v in range(256)]
            P.tied[e[i]] = Ent(tuple(data), raw[i], np.zeros(256), np.ones(256), references([np.ones(256)]), Lin(),
                               dev=P.deviation(f"sec{i}", data, raw[i]), top=P.largest(f"sec{i}", data, float(B)))
            for t in SECTION_GRID:
                P.link(Lin.of(e[i]), t, P.binary(f"egrid{i}_{t}"))
        n1 = n + Lin.of(D)  # the new length

        # The header bytes the sections write: their table entries and the rewritten fields.
        fields = {f: field_range(pe.FILE_HEADER if f == "NumberOfSections" else oh, f) for f in FIELDS}
        written = [(slots[i], slots[i] + SECTION_ENTRY) for i in range(k)] + list(fields.values()) if k else []
        field_bytes = np.bincount(np.frombuffer(b"".join(z[lo:hi] for lo, hi in fields.values()), dtype=np.uint8), minlength=256)
        h_max = SECTION_ENTRY * k + sum(FIELDS.values())
        hb = [P.var(f"hb{v}", 0, h_max) for v in range(256)]
        P.row(Lin.total(Lin.of(x) for x in hb) - Lin.total(Lin.of(o, SECTION_ENTRY) for o in on) - sum(FIELDS.values()) * on0, 0, 0)
        if not k:
            for x in hb:
                P.fix(x, 0)

        # Byte counts (general:bytes and histogram:counts are the same counts).
        counts = []
        for v in range(256):
            x = float(sums["histogram:counts"][v]) + Lin.of(a[v]) + Lin.of(s[v]) + Lin.of(hb[v]) - float(field_bytes[v]) * on0
            if v == 0:
                x = x + pad - Lin.total(Lin.of(o, SECTION_ENTRY) for o in on)
            counts.append(x)
        rem = field_bytes.astype(np.float64)
        rem[0] += SECTION_ENTRY * k
        old_counts = np.asarray(sums["histogram:counts"], dtype=np.float64)
        lo, hi = share_bounds(old_counts, rem, h_max, n, n + B, B)
        h_bytes = float(self.x0[extractor.feature_names.index("general:entropy")])
        # The floor's correction for overwritten bytes applies only when a section is added.
        penalty = n * h_bytes - mixture_floor(n, h_bytes, h_max, 256)
        bytes_ent = Ent(tuple(counts), n1, lo, hi, references([old_counts]), n * h_bytes - penalty * on0,
                        dev=P.deviation("bytes", counts, n1))

        # Byte-entropy windows: the new windows over the new tail, and the header windows the writes touch.
        w0 = (n - WINDOW) // STEP + 1
        w1 = P.var("windows", w0, (n + B - WINDOW) // STEP + 1, integer=True)
        P.row(Lin.of(w1, STEP) - Lin.of(D), hi=n - WINDOW + STEP)  # STEP * (w1 - 1) <= n1 - WINDOW
        P.row(Lin.of(D) - Lin.of(w1, STEP), hi=-n + WINDOW - 1)  # n1 - WINDOW < STEP * w1
        we, rows_new = self._blocks(z, D, w1, [Lin.total(Lin.of(a[v]) + Lin.of(s[v]) for v in range(16 * col, 16 * col + 16))
                                               + (pad if col == 0 else 0.0) for col in range(16)])
        we_max = WINDOW * ((n + B - WINDOW) // STEP + 1 - w0)
        for r in range(16):
            # Implied by the windows' own cuts (on the pooled counts, with more references): cheap, kept.
            row_cuts(P, we[r], rows_new[r], r)
            dominance_cuts(P, we[r], rows_new[r], r, "wd", we_max / WINDOW)
        ent_counts = [float(sums["byteentropy:counts"][16 * r + col]) + we[r][col] for r in range(16) for col in range(16)]
        hdr_windows = [w for w in table.of_group("byteentropy") if w.kind == "window" and _meets(w, written)] if k else []
        for h, w in enumerate(hdr_windows):
            lo_, hi_ = w.attrs["span"]
            oc = np.bincount(np.frombuffer(z[lo_:hi_], dtype=np.uint8) >> 4, minlength=16)
            nh = sum(max(0, min(hi_, b) - max(lo_, a_)) for a_, b in written)
            h0 = int(w.attrs["Hbin"])
            u = [P.binary(f"hw{h}_u{r}") for r in range(16)]
            xw = [[P.var(f"hw{h}_{r}_{col}", 0, WINDOW) for col in range(16)] for r in range(16)]
            P.row(Lin.total(Lin.of(x) for x in u), 1, 1)
            reach = reachable_rows(oc, nh)
            for r in range(16):
                if r not in reach:
                    P.fix(u[r], 0)
            P.row(Lin.of(u[h0]) + on0, lo=1)  # unchanged unless a section is added
            for r in range(16):
                P.row(Lin.total(Lin.of(x) for x in xw[r]) - Lin.of(u[r], WINDOW), 0, 0)
                row_cuts(P, [Lin.of(x) for x in xw[r]], Lin.of(u[r]), r)
            for col in range(16):
                colsum = Lin.total(Lin.of(xw[r][col]) for r in range(16))
                P.row(colsum - float(oc[col]) - nh * on0, hi=0)
                P.row(colsum - float(oc[col]) + nh * on0, lo=0)
                ent_counts[16 * h0 + col] = ent_counts[16 * h0 + col] - float(oc[col])
                for r in range(16):
                    ent_counts[16 * r + col] = ent_counts[16 * r + col] + Lin.of(xw[r][col])

        # Strings: the new region (the new bytes and the printable run the old file ends in) and the header.
        st = [i for i in table.of_group("strings") if i.kind == "string"]
        run = 0
        while run < n and _printable(z[n - 1 - run]):
            run += 1
        run_chars = np.bincount(np.frombuffer(z[n - run:], dtype=np.uint8) - PRINTABLE[0], minlength=96).astype(np.float64)
        tail_string = [i for i in st if i.members and i.members[-1][1] == n] if run >= 5 else []
        if run >= 5 and len(tail_string) != 1:
            raise RuntimeError(f"Expected one string item ending the file; found {len(tail_string)}.")
        t_sums = _sums(table, tail_string)
        dT = P.binary("drop_tail") if tail_string else None
        regexes = len(sums["strings:regex"])
        ns = P.var("ns", 0, (B + run + 1) / 6)
        pd = [P.var(f"pd{ch}", 0, B + run) for ch in range(96)]
        rg = [P.var(f"rg{j}", 0, (B + run + 1) / 6) for j in range(regexes)]
        for ch in range(96):
            v = ch + PRINTABLE[0]
            avail = Lin.of(a[v]) + Lin.of(s[v]) + (Lin.of(dT, run_chars[ch]) if dT is not None else run_chars[ch])
            P.row(Lin.of(pd[ch]) - avail, hi=0)
        np_new = Lin.total(Lin.of(x) for x in pd)
        P.row(self.forced_chars - np_new, hi=0)
        if dT is not None:
            # The tail string changes only by merging with added bytes, into a string that holds all of its characters.
            P.row(Lin.of(dT) - Lin.of(D), hi=0)
            P.row(Lin.of(ns) - Lin.of(dT), lo=0)
            for ch in range(96):
                P.row(Lin.of(pd[ch]) - Lin.of(dT, run_chars[ch]), lo=0)
        P.row(Lin.of(ns, 5) - np_new, hi=0)
        P.row(Lin.of(ns, 6) - Lin.of(D), hi=run + 1)
        for j in range(regexes):
            P.row(Lin.of(rg[j]) - Lin.of(ns), hi=0)
        # A string matching a regex holds the characters the regex requires, and distinct strings hold distinct ones.
        regex_names = sorted(_STRINGS.regex_idxs, key=lambda k: _STRINGS.regex_idxs[k])
        required = regex_requirements(_STRINGS._regexes)
        if len(regex_names) != regexes:
            raise RuntimeError(f"{len(regex_names)} regexes, {regexes} regex features.")
        for j, name in enumerate(regex_names):
            for vals, mult in required.get(name, []):
                P.row(Lin.of(rg[j], mult) - Lin.total(Lin.of(pd[v - PRINTABLE[0]]) for v in vals), hi=0)
        hranges = _merge(_widen(z, lo_, hi_) for lo_, hi_ in written)
        if hranges and run and hranges[-1][1] > n - run:
            raise NotCovered("header strings meet the tail run")
        h_strings = [i for i in st if _meets(i, hranges)]
        h_sums = _sums(table, h_strings)
        h_len = sum(hi_ - lo_ for lo_, hi_ in hranges)
        h_chars = np.zeros(96)
        for lo_, hi_ in hranges:
            arr = np.frombuffer(z[lo_:hi_], dtype=np.uint8)
            arr = arr[(arr >= PRINTABLE[0]) & (arr < PRINTABLE[1])]
            h_chars += np.bincount(arr - PRINTABLE[0], minlength=96)
        h_written = sum(hi_ - lo_ for lo_, hi_ in written)
        dH = P.binary("drop_header_strings")
        hs = P.var("hs", 0, (h_len + len(hranges)) / 6 + 1)
        hpd = [P.var(f"hpd{ch}", 0, h_len) for ch in range(96)]
        hrg = [P.var(f"hrg{j}", 0, (h_len + len(hranges)) / 6 + 1) for j in range(regexes)]
        P.row(Lin.of(dH) - on0, hi=0)
        for ch in range(96):
            P.row(Lin.of(hpd[ch]) - (h_written + h_chars[ch]) * on0, hi=0)
        P.row(Lin.total(Lin.of(x) for x in hpd) - h_len * on0, hi=0)
        P.row(Lin.of(hs, 5) - Lin.total(Lin.of(x) for x in hpd), hi=0)
        P.row(Lin.of(hs, 6) - (h_len + len(hranges)) * on0, hi=0)
        for j in range(regexes):
            P.row(Lin.of(hrg[j]) - Lin.of(hs), hi=0)
            for vals, mult in required.get(regex_names[j], []):
                P.row(Lin.of(hrg[j], mult) - Lin.total(Lin.of(hpd[v - PRINTABLE[0]]) for v in vals), hi=0)

        def dropped(family: str, i: int) -> Lin:
            out = Lin()
            if dT is not None:
                out._iadd(Lin.of(dT, float(t_sums[family][i])), 1.0)
            out._iadd(Lin.of(dH, float(h_sums[family][i])), 1.0)
            return out

        num_strings = float(sums["strings:numstrings"][0]) - dropped("strings:numstrings", 0) + Lin.of(ns) + Lin.of(hs)
        printables = (float(sums["strings:printables"][0]) - dropped("strings:printables", 0) + np_new
                      + Lin.total(Lin.of(x) for x in hpd))
        pdist = [float(sums["strings:printabledist"][ch]) - dropped("strings:printabledist", ch) + Lin.of(pd[ch]) + Lin.of(hpd[ch])
                 for ch in range(96)]
        regex = [float(sums["strings:regex"][j]) - dropped("strings:regex", j) + Lin.of(rg[j]) + Lin.of(hrg[j]) for j in range(regexes)]
        old_pd = np.asarray(sums["strings:printabledist"], dtype=np.float64)
        rem_pd = np.asarray(t_sums["strings:printabledist"], dtype=np.float64) + np.asarray(h_sums["strings:printabledist"], dtype=np.float64)
        old_p = float(sums["strings:printables"][0])
        lo, hi = share_bounds(old_pd, rem_pd, h_len + run, old_p - float(rem_pd.sum()), old_p + B + h_len + run, B)
        h_strings = float(self.x0[extractor.feature_names.index("strings:entropy")])
        strings_ent = Ent(tuple(pdist), printables, lo, hi, references([old_pd]),
                          old_p * h_strings - (old_p * h_strings - mixture_floor(old_p, h_strings, float(rem_pd.sum()), 96))
                          * (Lin.of(dH) + (Lin.of(dT) if dT is not None else 0.0)),
                          dev=P.deviation("strings", pdist, printables), symbols=96)

        # The section group.
        sec = [i for i in table.of_group("section") if i.kind == "section"]
        overlay = [i for i in table.of_group("section") if i.kind == "overlay"]
        ov_start = int(overlay[0].attrs["start"]) if overlay else n
        ov_counts = np.bincount(np.frombuffer(z[ov_start:], dtype=np.uint8), minlength=256).astype(np.float64)
        keep = 1.0 - on0  # the old overlay survives only if no section is added
        ov_size = (n - ov_start) * keep + Lin.of(A)
        h_overlay = float(self.x0[extractor.feature_names.index("section:overlay_entropy")])
        ov_data = tuple(float(ov_counts[v]) * keep + Lin.of(a[v]) for v in range(256))
        ov_ent = Ent(ov_data, ov_size, np.zeros(256), np.ones(256), references([ov_counts, old_counts]),
                     mixture_floor(n - ov_start, h_overlay, 0.0, 256) * keep, dev=P.deviation("overlay", ov_data, ov_size))
        counts_sec = [float(x) for x in sums["section:counts"]]
        sec_counts = [
            counts_sec[0] + Lin.total(Lin.of(o) for o in on),
            counts_sec[1] + Lin.total(Lin.of(x) for x in zs),
            counts_sec[2] + Lin.total(Lin.of(y[i][EMPTY]) for i in range(k)),
            counts_sec[3] + Lin.total(Lin.of(x) for x in rx),
            counts_sec[4] + Lin.total(Lin.of(fl[i]["MEM_WRITE"]) for i in range(k)),
        ]
        empty_option = option("", empty=False)
        hashes: dict[str, list[Lin]] = {}
        for fam, qty, ub in (("section:size_hash", raw, B), ("section:vsize_hash", [Lin.of(x) for x in c], B),
                             ("section:entropy_hash", [Lin.of(x) for x in e], 8.0)):
            col = [Lin(float(v)) for v in sums[fam]]
            for i in range(k):
                for o in range(EMPTY + 1):
                    p = P.product(f"{fam}{i}_{o}", qty[i], ub, y[i][o])
                    oo = empty_option if o == EMPTY else o
                    col[oo // 2] = col[oo // 2] + Lin.of(p, 1.0 if oo % 2 == 0 else -1.0)
            hashes[fam] = col
        chars = [Lin(float(v)) for v in sums["section:characteristics_hash"]]
        for i in range(k):
            for key, vs in q[i].items():
                for o, v in enumerate(vs):
                    chars[o // 2] = chars[o // 2] + Lin.of(v, 1.0 if o % 2 == 0 else -1.0)
        hashes["section:characteristics_hash"] = chars

        # The header fields.
        index = {item.attrs.get("field"): item.terms[0].index for item in table.of_group("header") if item.kind == "field"}
        hdr = [Lin(float(v)) for v in sums["header:fields"]]
        old = {f: float(sums["header:fields"][index[f]]) for f in FIELDS}
        end0 = max([int(x.VirtualAddress) + max(int(x.Misc_VirtualSize), int(x.SizeOfRawData)) for x in pe.sections] + [0])
        rva1 = _align(max(end0, int(oh.SizeOfHeaders)), sa)
        code = Lin.total(Lin.of(x) for x in rc)
        hdr[index["NumberOfSections"]] = old["NumberOfSections"] + Lin.total(Lin.of(o) for o in on)
        hdr[index["SizeOfImage"]] = old["SizeOfImage"] * keep + rva1 * on0 + Lin.total(Lin.of(x, sa) for x in pages)
        hdr[index["SizeOfCode"]] = old["SizeOfCode"] + code
        hdr[index["SizeOfInitializedData"]] = old["SizeOfInitializedData"] + Lin.total(raw) - code

        self.fam: dict[str, list[Any]] = {
            "general:size": [n1],
            "general:bytes": counts,
            "histogram:counts": counts,
            "byteentropy:counts": ent_counts,
            "strings:numstrings": [num_strings],
            "strings:printables": [printables],
            "strings:printabledist": pdist,
            "strings:regex": regex,
            "header:fields": hdr,
            "section:file_size": [n1],
            "section:counts": sec_counts,
            "section:overlay": [ov_size, ov_ent],
            **hashes,
        }
        totals: dict[str, Lin] = {"histogram:counts": n1, "byteentropy:counts": Lin.of(w1, WINDOW), "strings:printabledist": printables}
        entropies: dict[str, Ent] = {"general:bytes": bytes_ent, "strings:printabledist": strings_ent}
        # The attributes the added sections and the new overlay take (the Max readouts' candidates).
        new_items: dict[str, list[Value]] = {
            "entropy": [Lin.of(x) for x in e],
            "size": list(raw),
            "vsize_ratio": [Frac(raw[i], Lin.of(c[i])) for i in range(k)],
        }
        new_overlay: dict[str, Value] = {"entropy": ov_ent, "size": ov_size}
        entry = next((i for i in table.of_group("section") if i.kind == "entry"), None)

        # The value of every feature.
        self.values: dict[int, Value] = {}
        col = 0
        for fe in extractor.features:
            readouts = fe.readouts() if callable(fe.readouts) else fe.readouts
            for r in readouts:
                for j, v in enumerate(self._values(r, totals, entropies, new_items, new_overlay, sec, n1, entry)):
                    # Constants (and expressions no choice enters) keep the file's extracted value.
                    if not isinstance(v, (int, float)) and not (isinstance(v, Lin) and not v.terms):
                        self.values[col + j] = v
                col += r.dim

        # pefile's warnings (outside the model; the extractor's flags of warning types and their number). Two of them
        # are functions of the choices: a byte value making up more than 50% (zero) or 15% (any other) of the file,
        # and an added section both writable and executable. The others are held at the file's values (an assumption
        # the containment test checks).
        names = {name: i for i, name in enumerate(extractor.feature_names)}
        byte_w, flags_w = names[WARN_BYTE], names[WARN_FLAGS]
        old_byte, old_flags = float(self.x0[byte_w]), float(self.x0[flags_w])
        dominant = P.binary("warn_byte")
        shares = []
        for v in range(256):
            share = P.binary(f"share{v}")  # 1: byte v makes up at most its threshold
            P.link(Frac(counts[v], n1), 0.5 if v == 0 else 0.15, share)
            P.row(Lin.of(dominant) + Lin.of(share), lo=1)
            shares.append(share)
        P.row(Lin.of(dominant) + Lin.total(Lin.of(x) for x in shares), hi=256)
        suspicious = P.binary("warn_flags")
        added_wx = []
        for i in range(k):
            wx = P.binary(f"wx{i}")
            w_, x_ = fl[i]["MEM_WRITE"], fl[i]["MEM_EXECUTE"]
            P.row(Lin.of(wx) - Lin.of(w_), hi=0)
            P.row(Lin.of(wx) - Lin.of(x_), hi=0)
            if not pe.is_driver():
                # NOTE: pefile spares a driver's section named PAGE; for a driver the warning is left free below.
                P.row(Lin.of(wx) - Lin.of(w_) - Lin.of(x_), lo=-1)
            P.row(Lin.of(suspicious) - Lin.of(wx), lo=0)
            added_wx.append(wx)
        P.row(Lin.of(suspicious) - Lin.total(Lin.of(x) for x in added_wx), hi=old_flags)
        if old_flags:
            P.fix(suspicious, 1)
        self.values[byte_w] = Lin.of(dominant)
        self.values[flags_w] = Lin.of(suspicious)
        self.values[names[WARN_COUNT]] = float(self.x0[names[WARN_COUNT]]) - old_byte - old_flags + Lin.of(dominant) + Lin.of(suspicious)
        # The features whose values are whole numbers (counts, sizes, fields, flags; not the entropy-hash buckets).
        self.integral = {f for f, v in self.values.items() if isinstance(v, Lin) and not extractor.feature_names[f].startswith("section:entropy_hash")}

    def _blocks(self, z: bytes, D: int, w1: int, newnib: Sequence[Lin]) -> tuple[list[list[Lin]], list[Lin]]:
        """
        The new byte-entropy windows, exactly (up to the byte order inside a block): the new tail as blocks of STEP
        bytes with nibble counts (`bk{i}_{c}`; block 0 also holds the old file's last partial block), window i the
        blocks i - 1 and i (block -1 is the old file's last full block), active (`bact{i}`) for the first w1 - w0, each
        active window in one entropy row (`bu{i}_{r}`) and its counts split exactly by row (`bz{i}_{r}_{c}`, nonzero
        only in its row). Each window's row bounds its nibble counts: Gibbs (cross-entropy at least the window's
        entropy, at least r / 4), Pinsker and Fano (no nibble above the largest share entropy r / 4 allows) above;
        the dominant share below (a nibble holds at least what entropy (r + 1) / 4 needs).

        Returns:
            The (row, nibble) counts over the new windows, and the number of new windows per row.
        """
        P, n, B = self.program, self.n, self.budget
        nb0 = n // STEP
        w0 = (n - WINDOW) // STEP + 1
        nw = (n + B - WINDOW) // STEP + 1 - w0
        nb = -(-(n + B) // STEP) - nb0
        part = np.bincount(np.frombuffer(z[nb0 * STEP:], dtype=np.uint8) >> 4, minlength=16).astype(np.float64)
        prev = np.bincount(np.frombuffer(z[(nb0 - 1) * STEP:nb0 * STEP], dtype=np.uint8) >> 4, minlength=16).astype(np.float64)
        bk = [[P.var(f"bk{i}_{c}", 0, STEP) for c in range(16)] for i in range(nb)]
        self.bk = bk
        # Printable bytes outside strings come in runs of at most four, so a block's new bytes hold at least
        # printable - 4 (non-printable + 1) string characters (high nibbles 2-7 are the printable bytes).
        self.forced_chars = Lin()
        for i in range(nb):
            y = P.var(f"by{i}", 0, STEP)
            pr = Lin.total(Lin.of(bk[i][c]) for c in range(2, 8))
            np_ = Lin.total(Lin.of(bk[i][c]) for c in range(16) if not 2 <= c < 8)
            P.row(Lin.of(y) - pr + np_ * 4.0, lo=-4.0)
            self.forced_chars._iadd(Lin.of(y), 1.0)
        blk = [[Lin.of(bk[i][c]) + (float(part[c]) if i == 0 else 0.0) for c in range(16)] for i in range(nb)]
        for c in range(16):
            P.row(Lin.total(Lin.of(bk[i][c]) for i in range(nb)) - newnib[c], 0, 0)
        act = [P.binary(f"bact{i}") for i in range(nw)]
        self.bact = act
        self.bu: list[list[int]] = []
        self.bz: list[list[list[int]]] = []
        self.bdom: list[list[int]] = []
        P.row(Lin.total(Lin.of(x) for x in act) - Lin.of(w1) + w0, 0, 0)
        for i in range(nb):
            P.row(Lin.total(blk[i]), hi=STEP)
            if i < nw:
                P.row(Lin.total(blk[i]) - Lin.of(act[i], STEP), lo=0)  # an active window's blocks are full
            if 0 < i < nw:
                P.row(Lin.of(act[i]) - Lin.of(act[i - 1]), hi=0)
        theta = [dominant_share((r + 1) / 4) if r < 15 else 0.0 for r in range(16)]
        rho = [min(2.0, pinsker_radius(r / 4, 16)) for r in range(16)]
        phi = [fano_share(r / 4) for r in range(16)]
        refs = [q for lvl in GIBBS_LEVELS for q in boundary_references(lvl)[:16]]
        we = [[Lin() for _ in range(16)] for _ in range(16)]
        rows = [Lin() for _ in range(16)]
        for i in range(nw):
            cnt = [(blk[i - 1][c] if i else Lin(float(prev[c]))) + blk[i][c] for c in range(16)]
            u = [P.binary(f"bu{i}_{r}") for r in range(16)]
            self.bu.append(u)
            P.row(Lin.total(Lin.of(x) for x in u) - Lin.of(act[i]), 0, 0)
            bz = [[P.var(f"bz{i}_{r}_{c}", 0, WINDOW) for c in range(16)] for r in range(16)]
            self.bz.append(bz)
            for r in range(16):
                P.row(Lin.total(Lin.of(x) for x in bz[r]) - Lin.of(u[r], WINDOW), 0, 0)
                rows[r]._iadd(Lin.of(u[r]), 1.0)
                for c in range(16):
                    we[r][c]._iadd(Lin.of(bz[r][c]), 1.0)
            for c in range(16):
                P.row(Lin.total(Lin.of(bz[r][c]) for r in range(16)) - cnt[c], hi=0)  # equal when active (both sum to WINDOW)
            idle = 1.0 - Lin.of(act[i])
            level = Lin.total(Lin.of(u[r], WINDOW * (r / 4 - TOL_ENT)) for r in range(1, 16))
            for q in refs:
                P.row(Lin.total(x * float(-math.log2(w)) for x, w in zip(cnt, q.tolist(), strict=True)) - level, lo=0)
            dev = P.deviation(f"bw{i}", cnt, Lin.of(act[i], WINDOW))
            P.row(dev - Lin.total(Lin.of(u[r], WINDOW * rho[r]) for r in range(16)) - idle * (2 * WINDOW), hi=0)
            for c in range(16):
                P.row(cnt[c] - Lin.total(Lin.of(u[r], WINDOW * phi[r]) for r in range(16)) - idle * WINDOW, hi=0)
            top = P.largest(f"bw{i}", cnt, float(WINDOW))
            self.bdom.append([v for v in range(len(P.names) - 16, len(P.names))])
            P.row(top - Lin.total(Lin.of(u[r], WINDOW * theta[r]) for r in range(16)), lo=0)
        return we, rows

    def _values(self, r: Any, totals: dict[str, Lin], entropies: dict[str, Ent], new_items: dict[str, list[Value]],
                new_overlay: dict[str, Value], sec: list[Item], n1: Lin, entry: Optional[Item]) -> list[Value]:
        """The values of one readout's features (constants for the ones the catalogue does not move)."""
        const: list[Value] = [0.0] * r.dim
        if isinstance(r, Selection):
            # NOTE: an added section never holds the entry point; it can become the entry section only through the
            # fallback (no section holds it), and then the hashed name is left free.
            return [FREE] * r.dim if entry is not None and entry.attrs["name"] == "" else const
        if isinstance(r, Identity):
            return list(self.fam[r.family][r.start:r.start + r.size]) if r.family in self.fam else const
        if isinstance(r, Normalized):
            if r.family not in self.fam:
                return const
            return [Frac(x, totals[r.family]) for x in self.fam[r.family]]
        if isinstance(r, Ratio):
            if r.num[0] not in self.fam or r.den[0] not in self.fam:
                raise NotImplementedError(f"A ratio over a moved and an unmoved family: {r!r}.")
            return [Frac(self.fam[r.num[0]][r.num[1]], self.fam[r.den[0]][r.den[1]])]
        if isinstance(r, Entropy):
            return [entropies[r.family]] if r.family in entropies else const
        if isinstance(r, Max) and r.group == "section":
            # The old sections' values, the added sections', and the overlay's (old or new; it replaces the old one).
            olds = [float(i.attrs[r.attr]) for i in sec if i.kind in r.kinds]
            cands = list(new_items[r.attr]) + ([new_overlay[r.attr]] if "overlay" in r.kinds else [])
            if r.divide_by is not None:
                if r.divide_by != ("section:file_size", 0) or not all(isinstance(x, Lin) for x in cands):
                    raise NotImplementedError(f"Unexpected Max readout {r!r}.")
                return [MaxOf(tuple(Frac(x, n1) for x in cands) + tuple(Frac(Lin(v), n1) for v in olds), r.floor)]  # type: ignore[arg-type]
            return [MaxOf(tuple(cands), max(olds + [r.floor]))]
        if isinstance(r, Min) and r.floor == 0.0:
            return const  # constant zero: the attributes are nonnegative
        return const

    def resolve(self, f: int) -> Value:
        """The value of feature f (its current value when no edit moves it)."""
        return self.values.get(f, float(self.x0[f]))

    def fixed_value(self, f: int) -> Optional[float]:
        """Feature f's value when every variable it depends on is fixed (an exact feature under `fix`), else None."""
        P = self.program

        def ev(x: Lin) -> Optional[float]:
            if any(P.lb[v] != P.ub[v] for v in x.terms):
                return None
            return x.const + sum(c * P.lb[v] for v, c in x.terms.items())

        v = self.values.get(f)
        if isinstance(v, Lin):
            return ev(v)
        if isinstance(v, Frac):
            num, den = ev(v.num), ev(v.den)
            return None if num is None or den is None else (num / den if den else 0.0)
        return None

    def fix(self, choice: Choice, edited: bytes) -> None:
        """Fix the choice variables to one edit (for the containment test); `edited` is the written file."""
        P = self.program
        if len(choice.sections) > self.k:
            raise ValueError(f"{len(choice.sections)} sections, {self.k} encoded.")
        pe = pefile.PE(data=edited)
        added = list(pe.sections)[len(pe.sections) - len(choice.sections):]
        for i in range(self.k):
            on = i < len(choice.sections)
            name, content, characteristics = choice.sections[i] if on else (b"", b"", 0)
            raw = _align(len(content), self.fa)
            P.fix(self.on[i], on)
            P.fix(self.m[i], raw // self.fa)
            P.fix(self.c[i], len(content))
            P.fix(self.pages[i], -(-raw // self.sa))
            P.fix(self.zs[i], on and raw == 0)
            P.fix(self.e[i], added[i].get_entropy() if on else 0.0)
            key = name_key(name)
            for o, v in enumerate(self.y[i]):
                P.fix(v, on and o == option(key))
            for f, bit in FLAGS.items():
                P.fix(self.fl[i][f], on and bool(characteristics & bit))
                for pn in self.prop_names[f]:
                    hit = option(f"{key}:{pn}", empty=False) if on and characteristics & bit else -1
                    for o, v in enumerate(self.q[i][(f, pn)]):
                        P.fix(v, o == hit)
        content = b"".join(c for _, c, _ in choice.sections)
        for i in range(self.k):
            own = choice.sections[i][1] if i < len(choice.sections) else b""
            for v, x in enumerate(np.bincount(np.frombuffer(own, dtype=np.uint8), minlength=256).tolist()):
                P.fix(self.sv[i][v], x)
        for v, x in enumerate(np.bincount(np.frombuffer(choice.append, dtype=np.uint8), minlength=256).tolist()):
            P.fix(self.a[v], x)
        for v, x in enumerate(np.bincount(np.frombuffer(content, dtype=np.uint8), minlength=256).tolist()):
            P.fix(self.s[v], x)
        P.fix(self.A, len(choice.append))
        P.fix(self.D, len(edited) - self.n)
        # The block model: the written file's new bytes per block, and which new windows exist.
        nb0, w0 = self.n // STEP, (self.n - WINDOW) // STEP + 1
        nib = np.frombuffer(edited, dtype=np.uint8) >> 4
        for i, row in enumerate(self.bk):
            lo, hi = max((nb0 + i) * STEP, self.n), min((nb0 + i + 1) * STEP, len(edited))
            got = np.bincount(nib[lo:hi], minlength=16) if hi > lo else np.zeros(16, dtype=np.int64)
            for c, v in enumerate(row):
                P.fix(v, float(got[c]))
        windows = (len(edited) - WINDOW) // STEP + 1 - w0
        for i, v in enumerate(self.bact):
            P.fix(v, float(i < windows))
            # An existing window's row (thrember's own computation), its counts by row, and its dominant nibble.
            block = np.frombuffer(edited[(w0 + i) * STEP:(w0 + i) * STEP + WINDOW], dtype=np.uint8)
            if i < windows:
                row, counts = _BYTE_ENTROPY._entropy_bin_counts(block)  # type: ignore[no-untyped-call]
            else:
                row, counts = -1, np.zeros(16, dtype=np.int64)
            for r in range(16):
                P.fix(self.bu[i][r], float(r == row))
                for c in range(16):
                    P.fix(self.bz[i][r][c], float(counts[c]) if r == row else 0.0)
            for c, d in enumerate(self.bdom[i]):
                P.fix(d, float(c == int(np.argmax(counts))))


################################################################################
# Linking the ensemble
################################################################################


def link_ensemble(enc: Encoding, ens: Ensemble, sides: Optional[np.ndarray] = None) -> dict[tuple[int, int], int]:
    """
    One binary per (feature, threshold), "x_f <= t_j", linked to the feature's value (or fixed to `sides`' side of
    each split, a feature vector, for the containment test).

    Returns:
        (feature, threshold index) -> the binary's variable.
    """
    P = enc.program
    out: dict[tuple[int, int], int] = {}
    for f, ts in ens.thresholds.items():
        value = enc.resolve(f)
        for j, t in enumerate(ts.tolist()):
            z = out[(f, j)] = P.binary(f"split{f}_{j}")
            if sides is not None:
                P.fix(z, float(sides[f]) <= t)
            P.link(value, t, z, integral=f in enc.integral)
        if sides is None:
            for j in range(ts.size - 1):
                P.row(Lin.of(out[(f, j)]) - Lin.of(out[(f, j + 1)]), hi=0)
    return out


def certify(enc: Encoding, ens: Ensemble, below: float, time_limit: float, minimize: bool = False) -> dict[str, Any]:
    """
    Decide whether some edit in the encoded catalogue brings the ensemble's raw score below `below`.

    With `minimize`, the solver also minimizes the score among the edits that go below `below`, so that a solve
    stopped by the time limit still returns a proven floor: HiGHS's dual bound d bounds the lowest score over the
    edits below `below`; if there are none, the true lowest score is above `below` >= d. Either way d is a lower bound
    on the lowest score any edit in the catalogue reaches (the bracket's floor; docs/direction-A-prime-plan.md).

    Returns:
        status, message, seconds, evaded (a choice was found), certified (proved infeasible), the found score, the
        program's size, and (if evaded) the choice variables' values, the side of every split, and the solution. With
        `minimize`, also `floor` (the proven lower bound; `below` when certified, None if the solver proved nothing).
    """
    P = enc.program
    z = link_ensemble(enc, ens)
    leaves = [P.var(f"leaf{i}", 0, 1) for i in range(ens.values.size)]
    for tree_leaves, nodes in zip(ens.leaves, ens.nodes):
        P.row(Lin.total(Lin.of(leaves[i]) for i in tree_leaves), 1, 1)
        for f, j, left, right in nodes:
            P.row(Lin.total(Lin.of(leaves[i]) for i in left) - Lin.of(z[(f, j)]), hi=0)
            P.row(Lin.total(Lin.of(leaves[i]) for i in right) + Lin.of(z[(f, j)]), hi=1)
    score = Lin.total(Lin.of(leaves[i], float(v)) for i, v in enumerate(ens.values.tolist()))
    P.row(score, hi=below)
    objective = {leaves[i]: float(v) for i, v in enumerate(ens.values.tolist())} if minimize else None
    t0 = time.time()
    res = P.solve(objective=objective, time_limit=time_limit)
    seconds = time.time() - t0
    out: dict[str, Any] = {
        "status": int(res.status), "message": str(res.message), "seconds": seconds,
        "evaded": res.x is not None, "certified": res.status == 2,
        "variables": len(P.lb), "rows": len(P.rlo), "binaries": int(sum(P.integer)),
    }
    if minimize:
        dual = getattr(res, "mip_dual_bound", None)
        floor = below if res.status == 2 else (None if dual is None or not np.isfinite(dual) else float(dual))
        out.update(floor=floor, gap=getattr(res, "mip_gap", None), nodes=getattr(res, "mip_node_count", None))
    if res.x is not None:
        out["score"] = float(ens.values @ res.x[leaves[0]:leaves[0] + len(leaves)])
        out["choice"] = {name: float(res.x[i]) for i, name in enumerate(P.names) if CHOICE.match(name) and abs(res.x[i]) > 1e-9}
        # The solver's side of every split (for attributing a gap between its score and a written file's).
        out["sides"] = {key: bool(res.x[v] > 0.5) for key, v in z.items()}
        out["x"] = res.x
    return out
