"""
Tests for scripts/ap_encoding.py: every split link is sound (the true side of a split is always allowed).
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ap_encoding import Ent  # noqa: E402
from ap_encoding import Frac  # noqa: E402
from ap_encoding import Lin  # noqa: E402
from ap_encoding import MaxOf  # noqa: E402
from ap_encoding import mixture_floor  # noqa: E402
from ap_encoding import Program  # noqa: E402
from ap_encoding import references  # noqa: E402
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
