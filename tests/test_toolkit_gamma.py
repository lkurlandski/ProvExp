"""
Tests for GAMMA written by our writers (provexp.attacks.toolkit): the room check, and the section and API problems'
edits, applied directly (no detector is queried), against the structure assertion and the paper's validity rule.

The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import warnings

import numpy as np
import pefile
import pytest

from provexp.attacks.toolkit import NotApplicable
from provexp.attacks.toolkit import _as_bytes
from provexp.attacks.toolkit import _as_sample
from provexp.attacks.toolkit import _gamma_problems
from provexp.attacks.toolkit import gamma_start
from provexp.attacks.validity import output_invalid
from provexp.attacks.validity import structure
from provexp.featuresets.ember2024.catalogue import section_slots

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]
DONORS = [list(b"A" * 3000), list(range(256)) * 4, list(b"\x00" * 100)]
API = [("kernel32.dll", ["GetTickCount", "Sleep", ""]), ("pvtest.dll", ["F", "G"])]


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    try:
        pe = pefile.PE(data=data, fast_load=True)
    except pefile.PEFormatError:
        pytest.skip("pefile cannot parse this file.")
    if not pe.sections or structure(data)[0] is None:
        pytest.skip("Not a start file the attacks apply to.")
    return data


def _problem(attack: str) -> Any:
    sections, api = _gamma_problems()
    if attack == "gamma_sections":
        return sections(DONORS, None, population_size=10, penalty_regularizer=1e-6, iterations=1, threshold=0)
    return api(API, None, population_size=10, penalty_regularizer=1e-6, iterations=1)


def _start(problem: Any, attack: str, data: bytes) -> None:
    if gamma_start(attack, data, len(DONORS))[0] is None:
        with pytest.raises(NotApplicable):
            problem.init_starting_point(_as_sample(data))
        pytest.skip("Not applicable to this file.")
    problem.init_starting_point(_as_sample(data))


################################################################################
# The room check
################################################################################


class TestGammaStart:

    @pytest.mark.parametrize("attack", ["gamma_sections", "gamma_api"])
    def test_cases(self, sample: bytes, attack: str) -> None:
        need = len(DONORS) if attack == "gamma_sections" else 1
        start, how = gamma_start(attack, sample, len(DONORS))
        if section_slots(sample, need) >= need:
            assert (start, how) == (sample, "fits")
        elif start is not None:
            assert how == "grown" and section_slots(start, need) >= need
        else:
            assert "growing the headers does not make room" in how

    def test_unknown_attack(self, sample: bytes) -> None:
        with pytest.raises(ValueError):
            gamma_start("padding", sample, 3)


################################################################################
# The edits
################################################################################


class TestSections:

    @pytest.mark.parametrize("genes", [[1.0, 1.0, 1.0], [0.5, 0.0, 0.3], [0.0, 0.0, 0.0]])
    def test_written(self, sample: bytes, genes: list[float]) -> None:
        problem = _problem("gamma_sections")
        _start(problem, "gamma_sections", sample)
        out = _as_bytes(problem.apply_feasible_manipulations(np.array(genes), None))
        pe, start = pefile.PE(data=out, fast_load=True), pefile.PE(data=problem.start_, fast_load=True)
        new = pe.sections[start.FILE_HEADER.NumberOfSections:]
        assert [s.Name.rstrip(b"\x00").decode() for s in new] == problem.names_
        for s, donor, g in zip(new, DONORS, genes, strict=True):
            assert s.Characteristics == 0
            assert s.get_data()[:s.Misc_VirtualSize] == bytes(donor[:int(g * len(donor))])
        original = structure(sample)[0]
        assert original is not None and output_invalid(original, out) is None


class TestApi:

    def test_written(self, sample: bytes) -> None:
        problem = _problem("gamma_api")
        _start(problem, "gamma_api", sample)
        out = _as_bytes(problem.apply_feasible_manipulations(np.array([1.0, 0.5]), None))
        pe = pefile.PE(data=out)
        added = [(e.dll.decode().lower(), f.name.decode()) for e in pe.DIRECTORY_ENTRY_IMPORT for f in e.imports
                 if f.name]
        assert ("pvtest.dll", "F") in added and ("pvtest.dll", "G") not in added
        for f in ("GetTickCount", "Sleep"):
            assert ("kernel32.dll", f) in added
            # once: added if the file lacked it, not added again if it had it
            assert added.count(("kernel32.dll", f)) == 1
        original = structure(sample)[0]
        assert original is not None and output_invalid(original, out) is None

    def test_nothing_chosen(self, sample: bytes) -> None:
        problem = _problem("gamma_api")
        _start(problem, "gamma_api", sample)
        out = _as_bytes(problem.apply_feasible_manipulations(np.array([0.0, 0.0]), None))
        assert out == problem.start_
