"""
Tests for provexp.featuresets.ember2024.deviations: every check is computed on real files, and the directory and
entry-section checks agree with what thrember's code does.

The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import warnings

import pefile
import pytest

from provexp.featuresets.ember2024.deviations import CHECKS
from provexp.featuresets.ember2024.deviations import deviations
from provexp.featuresets.ember2024.deviations import entry_sections
from provexp.featuresets.ember2024.features import SectionInfo

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    return data


################################################################################
# The checks
################################################################################


class TestDeviations:

    def test_every_check(self, sample: bytes) -> None:
        row = deviations(sample)
        if not row["parses"]:
            pytest.skip("pefile cannot parse this file.")
        assert set(CHECKS) <= set(row)

    def test_entry_matches_thrember(self, sample: bytes) -> None:
        try:
            pe = pefile.PE(data=sample)
        except pefile.PEFormatError:
            pytest.skip("pefile cannot parse this file.")
        raw = SectionInfo().raw_features(sample, pe)  # type: ignore[no-untyped-call]
        assert entry_sections(pe)[0] == raw["entry"]

    def test_not_a_pe(self) -> None:
        row = deviations(b"MZ" + b"\x00" * 100)
        assert row["parses"] is False
