"""
Tests for scripts/ap_encoding.py: every split link is sound (the true side of a split is always allowed).
"""

from __future__ import annotations

import math
from pathlib import Path
import re
import sys

import numpy as np
import pytest

from provexp.featuresets.ember2024.features import StringExtractor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ap_encoding import ROW_REFS  # noqa: E402
from ap_encoding import WINDOW  # noqa: E402
from ap_encoding import Ent  # noqa: E402
from ap_encoding import Frac  # noqa: E402
from ap_encoding import Lin  # noqa: E402
from ap_encoding import MaxOf  # noqa: E402
from ap_encoding import boundary_references  # noqa: E402
from ap_encoding import dominance_cuts  # noqa: E402
from ap_encoding import dominant_share  # noqa: E402
from ap_encoding import mixture_floor  # noqa: E402
from ap_encoding import pinsker_radius  # noqa: E402
from ap_encoding import Program  # noqa: E402
from ap_encoding import reachable_rows  # noqa: E402
from ap_encoding import regex_requirements  # noqa: E402
from ap_encoding import references  # noqa: E402
from ap_encoding import row_cuts  # noqa: E402
from ap_encoding import share_bounds  # noqa: E402

__all__: list[str] = []


################################################################################
# Helpers
################################################################################


def _entropy(c: np.ndarray) -> float:
    t = c.sum()
    return float(sum(-x / t * math.log2(x / t) for x in c if x > 0))


def _feasible(build: object, side: bool) -> bool:
    """Whether the program `build` makes, with the split binary fixed to `side`, is feasible."""
    p = Program()
    z = p.binary("z")
    build(p, z)  # type: ignore[operator]
    p.restrict(z, float(side))
    return bool(p.solve().status == 0)


################################################################################
# Links
################################################################################


class TestLink:

    @pytest.mark.parametrize("seed", range(20))
    def test_lin_and_frac_true_side(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        num, den = float(rng.integers(0, 1000)), float(rng.integers(1, 1000))
        t = float(rng.uniform(0, 1.5))

        def build(p: Program, z: int) -> None:
            a = p.var("a", 0, 2000)
            b = p.var("b", 1, 2000)
            p.fix(a, num)
            p.fix(b, den)
            p.link(Frac(Lin.of(a), Lin.of(b)), t, z)

        assert _feasible(build, num / den <= t)

    def test_lin_both_sides_excluded(self) -> None:
        def build(p: Program, z: int) -> None:
            a = p.var("a", 0, 10)
            p.fix(a, 7.0)
            p.link(Lin.of(a), 5.0, z)

        assert _feasible(build, False)
        assert not _feasible(build, True)

    @pytest.mark.parametrize("seed", range(20))
    def test_entropy_true_side(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        old = rng.integers(0, 50, 8).astype(float) + 1
        add = rng.integers(0, 30, 8).astype(float)
        new = old + add
        h = _entropy(new)
        t = h + float(rng.choice([-0.3, -0.01, 0.01, 0.3]))
        lo, hi = share_bounds(old, np.zeros(8), 0.0, old.sum(), old.sum() + 240, 240)

        def build(p: Program, z: int) -> None:
            xs = [p.var(f"x{i}", 0, 30) for i in range(8)]
            for x, v in zip(xs, add.tolist()):
                p.fix(x, v)
            counts = tuple(float(o) + Lin.of(x) for o, x in zip(old.tolist(), xs))
            floor = Lin(mixture_floor(float(old.sum()), _entropy(old), 0.0, 8))
            p.link(Ent(counts, Lin.total(counts), lo, hi, references([old]), floor), t, z)

        assert _feasible(build, h <= t)

    def test_entropy_excludes_far_side(self) -> None:
        # A uniform distribution has entropy 3 bits; "at most 2" must be excluded (the chords are tight at a point).
        c = np.full(8, 10.0)

        def build(p: Program, z: int) -> None:
            counts = tuple(Lin(float(v)) for v in c)
            p.link(Ent(counts, Lin(c.sum()), c / c.sum(), c / c.sum(), references([c]), Lin(0.0)), 2.0, z)

        assert not _feasible(build, True)

    def test_max(self) -> None:
        def build(p: Program, z: int) -> None:
            a = p.var("a", 0, 10)
            p.fix(a, 4.0)
            p.link(MaxOf((Lin.of(a),), 3.0), 3.5, z)

        assert _feasible(build, False)
        assert not _feasible(build, True)


def _distribution(rng: np.random.Generator, symbols: int) -> np.ndarray:
    """Random counts: near uniform, concentrated on a few symbols, or one dominant symbol over a spread rest."""
    kind = rng.integers(3)
    if kind == 0:
        return rng.integers(900, 1100, symbols).astype(float)
    if kind == 1:
        c = np.zeros(symbols)
        c[rng.choice(symbols, rng.integers(1, 6), replace=False)] = rng.integers(1, 1000, 1).astype(float) + rng.integers(0, 50)
        return c
    c = rng.integers(0, 20, symbols).astype(float)
    c[rng.integers(symbols)] += float(rng.integers(0, 50_000))
    return c


class TestEntropyCuts:

    @pytest.mark.parametrize("seed", range(40))
    @pytest.mark.parametrize("symbols", [96, 256])
    def test_pinsker_sound(self, seed: int, symbols: int) -> None:
        c = _distribution(np.random.default_rng(seed), symbols)
        if c.sum() == 0:
            return
        h = _entropy(c)
        l1 = float(np.abs(c / c.sum() - 1.0 / symbols).sum())
        for t in (h - 1e-3, h - 0.1, h - 1.0):
            assert l1 <= pinsker_radius(t, symbols) + 1e-12

    @pytest.mark.parametrize("seed", range(40))
    def test_dominant_share_sound(self, seed: int) -> None:
        c = _distribution(np.random.default_rng(seed), 256)
        if c.sum() == 0:
            return
        h = _entropy(c)
        for t in (h, h + 1e-3, h + 0.1, h + 1.0):
            assert c.max() / c.sum() >= dominant_share(t) - 1e-12

    def test_dominant_share_tight_cases(self) -> None:
        # k equal symbols: entropy log2 k, largest share 1/k (min-entropy equals entropy).
        for k in (1, 2, 4, 16):
            assert dominant_share(math.log2(k)) == pytest.approx(1.0 / k, rel=1e-4)
        # Below one bit the binary entropy decides: two symbols at 0.9 / 0.1 have entropy 0.469.
        assert dominant_share(0.469) == pytest.approx(0.9, abs=1e-3)

    @staticmethod
    def _build(c: np.ndarray, t: float) -> object:
        def build(p: Program, z: int) -> None:
            xs = [p.var(f"x{i}", 0, float(c.sum())) for i in range(c.size)]
            for x, v in zip(xs, c.tolist()):
                p.fix(x, v)
            counts = tuple(Lin.of(x) for x in xs)
            total = Lin.total(counts)
            e = Ent(counts, total, np.zeros(c.size), np.ones(c.size), references([np.ones(c.size)]), Lin(),
                    dev=p.deviation("e", counts, total), top=p.largest("e", counts, float(c.sum())), symbols=c.size)
            p.link(e, t, z)
        return build

    @pytest.mark.parametrize("seed", range(20))
    def test_link_true_side(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        c = _distribution(rng, 256)
        if c.sum() == 0:
            return
        h = _entropy(c)
        t = float(np.clip(h + rng.choice([-0.3, -0.01, 0.01, 0.3]), 0.05, 7.99))
        assert _feasible(self._build(c, t), h <= t)

    def test_link_excludes_far_sides(self) -> None:
        # Half the bytes one value, the rest spread: entropy ~5 bits; "above 7.9" breaks Pinsker, "at most 0.5" the
        # dominant share.
        c = np.full(256, 10.0)
        c[0] = 2550.0
        assert not _feasible(self._build(c, 7.9), False)
        assert not _feasible(self._build(c, 0.5), True)

    def test_tied_variable(self) -> None:
        # A variable tied to an entropy gets the entropy's rows when a split is on the variable itself.
        c = np.full(256, 10.0)
        c[0] = 2550.0

        def build(p: Program, z: int) -> None:
            xs = [p.var(f"x{i}", 0, float(c.sum())) for i in range(256)]
            for x, v in zip(xs, c.tolist()):
                p.fix(x, v)
            counts = tuple(Lin.of(x) for x in xs)
            total = Lin.total(counts)
            e = p.var("e", 0, 8)
            p.tied[e] = Ent(counts, total, np.zeros(256), np.ones(256), references([np.ones(256)]), Lin(),
                            dev=p.deviation("e", counts, total), top=p.largest("e", counts, float(c.sum())))
            p.link(Lin.of(e), 7.9, z)

        assert not _feasible(build, False)
        assert _feasible(build, True)


class TestMixtureFloor:

    @pytest.mark.parametrize("seed", range(50))
    def test_sound(self, seed: int) -> None:
        # Remove up to R counts and add any: entropy * total never falls below the floor.
        rng = np.random.default_rng(seed)
        old = rng.integers(0, 200, 16).astype(float)
        removed = np.minimum(old, rng.integers(0, 5, 16))
        added = rng.integers(0, 50, 16) * (rng.random(16) < 0.3)
        new = old - removed + added
        floor = mixture_floor(float(old.sum()), _entropy(old), float(removed.sum()), 16)
        assert _entropy(new) * new.sum() >= floor - 1e-9

    def test_exact_without_edits(self) -> None:
        old = np.array([5.0, 3.0, 2.0])
        assert mixture_floor(10.0, _entropy(old), 0.0, 3) == pytest.approx(10.0 * _entropy(old))


################################################################################
# Byte-entropy rows
################################################################################


def _window(rng: np.random.Generator) -> np.ndarray:
    """The nibble counts of a random 2,048-byte window (runs of a few values, random bytes, or a mix)."""
    kind = rng.integers(3)
    if kind == 0:
        values = rng.integers(0, 256, rng.integers(1, 6))
        a = rng.choice(values, WINDOW)
    elif kind == 1:
        a = rng.integers(0, 256, WINDOW)
    else:
        a = np.where(rng.random(WINDOW) < rng.random(), rng.integers(0, 256, WINDOW), rng.integers(0, 256))
    return np.bincount(a.astype(np.uint8) >> 4, minlength=16)


def _row(c: np.ndarray) -> int:
    return min(15, int(2 * 2 * _entropy(c)))


class TestRows:

    @pytest.mark.parametrize("r", range(1, 16))
    def test_references_on_the_boundary(self, r: int) -> None:
        for q in boundary_references(r / 4):
            assert q.min() > 0 and q.sum() == pytest.approx(1.0)
            assert _entropy(q) == pytest.approx(r / 4, abs=1e-9)

    @pytest.mark.parametrize("seed", range(20))
    def test_cuts_hold_on_pooled_windows(self, seed: int) -> None:
        # The windows of one row, pooled, satisfy every cut of that row.
        rng = np.random.default_rng(seed)
        windows = [_window(rng) for _ in range(60)]
        for r in range(1, 16):
            pooled = sum((w for w in windows if _row(w) == r), np.zeros(16))
            m = pooled.sum() / WINDOW
            for q in ROW_REFS[r]:
                assert float(pooled @ -np.log2(q)) >= (r / 4) * WINDOW * m - 1e-6

    def test_cuts_exclude_low_entropy(self) -> None:
        # A window of a single nibble cannot sit in row 8 (it has entropy 0).
        p = Program()
        xs = [p.var(f"x{c}", 0, WINDOW) for c in range(16)]
        for c, x in enumerate(xs):
            p.fix(x, WINDOW if c == 3 else 0)
        row_cuts(p, [Lin.of(x) for x in xs], Lin(1.0), 8)
        assert p.solve().status == 2

    @pytest.mark.parametrize("seed", range(20))
    def test_dominance_holds_on_pooled_windows(self, seed: int) -> None:
        # The windows of one row, pooled, satisfy that row's dominance cuts.
        rng = np.random.default_rng(seed)
        windows = [_window(rng) for _ in range(60)]
        for r in range(15):
            mine = [w for w in windows if _row(w) == r]
            p = Program()
            xs = [p.var(f"x{c}", 0, WINDOW * 60) for c in range(16)]
            pooled = sum(mine, np.zeros(16))
            for c, x in enumerate(xs):
                p.fix(x, float(pooled[c]))
            dominance_cuts(p, [Lin.of(x) for x in xs], Lin(float(len(mine))), r, "d", 60.0)
            assert p.solve().status == 0, f"row {r}: {len(mine)} windows"

    def test_dominance_excludes_spread(self) -> None:
        # An even spread over the 16 nibbles (entropy 4) cannot sit in row 0, nor two windows spread over 16 nibbles.
        for windows in (1.0, 2.0):
            p = Program()
            xs = [p.var(f"x{c}", 0, WINDOW * 2) for c in range(16)]
            for x in xs:
                p.fix(x, windows * WINDOW / 16)
            dominance_cuts(p, [Lin.of(x) for x in xs], Lin(windows), 0, "d", 2.0)
            assert p.solve().status == 2

    @pytest.mark.parametrize("seed", range(30))
    def test_reachable_rows_sound(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        a = np.frombuffer(rng.integers(0, 256, WINDOW, dtype=np.uint8).tobytes(), dtype=np.uint8).copy()
        if seed % 2:
            a[: rng.integers(0, WINDOW)] = 0
        moved = int(rng.integers(0, 200))
        reach = reachable_rows(np.bincount(a >> 4, minlength=16), moved)
        for _ in range(20):
            b = a.copy()
            at = rng.choice(WINDOW, moved, replace=False)
            b[at] = rng.choice([0, int(rng.integers(256))], moved) if rng.random() < 0.5 else rng.integers(0, 256, moved)
            assert _row(np.bincount(b >> 4, minlength=16)) in reach


################################################################################
# Strings
################################################################################


REGEXES: dict[str, re.Pattern[str]] = StringExtractor()._regexes  # type: ignore[no-untyped-call]
FRAGMENTS = ["http://a.b/c", "ftp://x", "10.20.30.40", "1:2:3:4:5:6:7:8", "a::b", "00-11-22-33-44-55", "HKCU", "C:/w",
             "1BoatSLRHtKNngkdXEeobR76b53LETtpyT", "!This program ", "x.click(", "Invoke-Command"]


class TestRegexRequirements:

    @pytest.mark.parametrize("seed", range(10))
    def test_matches_hold_the_required_characters(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        req = regex_requirements(REGEXES)
        words = [r.pattern for k, r in REGEXES.items() if k in req and k not in ("ipv4_addr",)] + FRAGMENTS
        alphabet = np.frombuffer(bytes(range(0x20, 0x80)), dtype=np.uint8)
        checked = 0
        for _ in range(300):
            parts = []
            for _ in range(int(rng.integers(1, 4))):
                w = str(rng.choice(words)).replace("\\b", "").replace("\\", "")
                w = "".join(c.upper() if rng.random() < 0.5 else c for c in w)
                parts.append(w)
                parts.append(bytes(rng.choice(alphabet, int(rng.integers(0, 4)))).decode())
            s = "".join(parts)
            counts = np.bincount(np.frombuffer(s.encode(), dtype=np.uint8), minlength=256)
            for k, r in REGEXES.items():
                if k in req and r.search(s):
                    checked += 1
                    for vals, mult in req[k]:
                        assert sum(int(counts[v]) for v in vals) >= mult, (k, s)
        assert checked > 100
