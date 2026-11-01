"""
Tests for scripts/ap_realize.py: a hand-made answer of the encoding is written as a file that carries exactly the
chosen counts, sizes, names, and strings.

The round-trip tests need executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from __future__ import annotations

import math
from pathlib import Path
import re
import sys

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.features import StringExtractor
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ap_encoding import EMPTY  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import NotCovered  # noqa: E402
from ap_encoding import name_key  # noqa: E402
from ap_encoding import option  # noqa: E402
from ap_realize import _strings  # noqa: E402
from ap_realize import allocate  # noqa: E402
from ap_realize import plan_strings  # noqa: E402
from ap_realize import realize  # noqa: E402
from ap_realize import regex_literals  # noqa: E402
from ap_realize import search_name  # noqa: E402
from ap_realize import shape_block  # noqa: E402

__all__: list[str] = []

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(f for f in (ROOT / "tests" / "data").glob("*/*") if f.is_file())[:8]
REGEXES: dict[str, re.Pattern[str]] = StringExtractor()._regexes  # type: ignore[no-untyped-call]


################################################################################
# Helpers
################################################################################


def _entropy(c: np.ndarray) -> float:
    t = c.sum()
    return float(sum(-x / t * math.log2(x / t) for x in c if x > 0))


################################################################################
# Pieces
################################################################################


class TestPieces:

    @pytest.mark.parametrize("seed", range(10))
    def test_allocate_sums_and_caps(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        caps = rng.integers(0, 50, size=16)
        total = int(rng.integers(0, caps.sum() + 10))
        out = allocate(total, rng.random(16), caps)
        assert out.sum() == min(total, caps.sum())
        assert np.all(out <= caps) and np.all(out >= 0)

    @pytest.mark.parametrize("row", [0, 3, 8, 12, 15])
    def test_shape_block_hits_row(self, row: int) -> None:
        avail = np.full(16, 4096)
        for target in (np.ones(16), np.eye(16)[3]):
            cols = shape_block(np.zeros(16), 1024, avail, target, row)
            assert cols.sum() == 1024
            assert row / 4 - 0.02 <= _entropy(cols) < (row + 1) / 4 + 0.02

    def test_literals_match(self) -> None:
        for k, lit in regex_literals(REGEXES).items():
            assert REGEXES[k].search(lit)

    def test_plan_strings(self) -> None:
        pd = np.zeros(96, dtype=np.int64)
        pd[ord("a") - 0x20:ord("z") - 0x20 + 1] = 20
        plan = plan_strings(30, pd, {"shell": 2, "system": 40}, REGEXES)
        assert plan.left == 40 and plan.chars == pd.sum()
        # Case-insensitive regexes get three spellings, each matching.
        assert len(plan.spellings["shell"]) == 2 and all(REGEXES["shell"].search(s.decode()) for s in plan.spellings["shell"])
        assert plan.spellings["dos_msg"] == [b"!This program "]

    def test_strings_carry_matches(self) -> None:
        # Two strings from letters: the owed matches are spelled into them and counted as written.
        pd = np.zeros(96, dtype=np.int64)
        plan = plan_strings(2, pd, {"system": 2, "token": 1}, REGEXES)
        printable = np.frombuffer(b"systemsystemtokenabcdefgh", dtype=np.uint8).astype(np.int64)
        out, rest = _strings(printable, 2, 25, plan)
        assert len(out) == 2 and all(len(s) >= 5 for s in out)
        assert sum(bool(REGEXES["system"].search(s.decode())) for s in out) == 2
        assert sum(bool(REGEXES["token"].search(s.decode())) for s in out) == 1
        assert plan.rg["system"] == 0 and plan.rg["token"] == 0 and rest.size == 0

    def test_search_name_hits_option(self) -> None:
        rng = np.random.default_rng(0)
        name = search_name(17, {}, 20_000, rng)
        assert option(name_key(name)) == 17
        assert search_name(EMPTY, {}, 10, rng) == b""


################################################################################
# Round trip
################################################################################


@pytest.mark.skipif(not FILES, reason="No test files in tests/data (see scripts/make_fixtures.py).")
class TestRoundTrip:

    @pytest.mark.parametrize("path", FILES, ids=[f.name[:12] for f in FILES])
    def test_counts_sizes_names_strings(self, path: Path) -> None:
        z = path.read_bytes()
        try:
            enc = Encoding(SumsFeatureExtractor(), z, 65536, 1)
        except NotCovered:
            pytest.skip("not covered")
        names = enc.program.names
        x = np.zeros(len(names))
        idx = {nm: i for i, nm in enumerate(names)}
        rng = np.random.default_rng(0)
        a = rng.integers(0, 40, size=256)
        a[ord("a"):ord("z") + 1] += 200
        for v in range(256):
            x[idx[f"a{v}"]] = a[v]
        x[idx["A"]] = a.sum()
        x[idx["ns"]] = 20
        x[idx["pd" + str(ord("e") - 0x20)]] = 100
        if enc.k:
            content = 3000
            x[idx["on0"]], x[idx["m0"]], x[idx["c0"]] = 1, -(-content // enc.fa), content
            x[idx["y0_42"]] = 1
            s = np.zeros(256)
            s[0], s[0x41] = 1000, 2000
            for v in range(256):
                x[idx[f"s{v}"]] = x[idx[f"s0_{v}"]] = s[v]
        edited = realize(enc, names, x, name_tries=50_000)
        tail = np.frombuffer(edited[-int(a.sum()):], dtype=np.uint8)
        assert np.array_equal(np.bincount(tail, minlength=256), a)
        # The strings may land in the section's content or the append (both new bytes).
        strings = re.findall(rb"[\x20-\x7f]{5,}", edited[len(z):])
        assert len(strings) >= 20
        if enc.k:
            pe = pefile.PE(data=edited)
            added = pe.sections[-1]
            assert len(pe.sections) == len(pefile.PE(data=z).sections) + 1
            assert added.Misc_VirtualSize == 3000
            assert option(name_key(added.Name)) == 42
            body = edited[added.PointerToRawData:added.PointerToRawData + 3000]
            assert body.count(0) == 1000 and body.count(0x41) == 2000
