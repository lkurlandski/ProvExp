"""
Tests for provexp.featuresets.ember2024.catalogue: the layout clauses of the precondition (`plain_layout`), each on a
test file edited into the layout it excludes.

The tests need executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import struct
import warnings

import pefile
import pytest

from provexp.featuresets.ember2024.catalogue import plain_layout
from provexp.featuresets.ember2024.features import field_range

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


def _pe(data: bytes) -> pefile.PE:
    return pefile.PE(data=data, fast_load=True)


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    try:
        pe = _pe(data)
    except pefile.PEFormatError:
        pytest.skip("pefile cannot parse this file.")
    if not pe.sections or not plain_layout(pe):
        pytest.skip("The file is not plain to begin with.")
    return data


def _put(data: bytes, offset: int, value: int) -> bytes:
    return data[:offset] + struct.pack("<I", value) + data[offset + 4:]


################################################################################
# plain_layout
################################################################################


class TestPlainLayout:

    def test_section_past_image(self, sample: bytes) -> None:
        pe = _pe(sample)
        s = pe.sections[0]
        assert not plain_layout(_pe(_put(sample, s.get_file_offset() + 8, pe.OPTIONAL_HEADER.SizeOfImage + 0x10000)))

    def test_image_larger_than_needed(self, sample: bytes) -> None:
        pe = _pe(sample)
        lo, _ = field_range(pe.OPTIONAL_HEADER, "SizeOfImage")
        assert not plain_layout(_pe(_put(sample, lo, pe.OPTIONAL_HEADER.SizeOfImage + 0x100000)))

    def test_section_raw_data_before_pe_header(self, sample: bytes) -> None:
        pe = _pe(sample)
        s = next((s for s in pe.sections if s.SizeOfRawData), None)
        if s is None:
            pytest.skip("No section with raw data.")
        assert not plain_layout(_pe(_put(sample, s.get_file_offset() + 20, 0)))

    def test_overlay_past_last_raw_data(self, sample: bytes) -> None:
        pe = _pe(sample)
        n = len(sample)
        ends = [s.PointerToRawData + s.SizeOfRawData for s in pe.sections if s.PointerToRawData + s.SizeOfRawData <= n]
        last = max(pe.sections, key=lambda s: s.PointerToRawData + s.SizeOfRawData)
        if last.PointerToRawData + last.SizeOfRawData != max(ends) or len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) < 3:
            pytest.skip("The furthest raw data is not a section's within the file.")
        # Point the (unused) third directory entry's extent past the last raw data, inside the file: pefile's overlay
        # rule then starts the overlay there.
        z = sample + b"\x00" * 0x400
        entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2]
        rva = last.VirtualAddress + max(last.SizeOfRawData - 0x10, 0)
        z = _put(_put(z, entry.get_file_offset(), rva), entry.get_file_offset() + 4, 0x200)
        assert _pe(z).get_overlay_data_start_offset() is not None
        assert not plain_layout(_pe(z))
