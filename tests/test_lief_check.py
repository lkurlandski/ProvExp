"""
Tests for provexp.attacks.lief_check: LIEF's round trip passes well-formed files and fails files whose section table
points far past the end (the runaway rebuild session 76 traced the OOM-killed GAMMA workers to).

The file-based tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
The failing case lets the child allocate up to its 8 GiB cap: run it in a job, not on a shared head node.
"""

from pathlib import Path
import struct

import pefile
import pytest

from provexp.attacks.lief_check import dos_header_extensible
from provexp.attacks.lief_check import lief_round_trip
from provexp.attacks.lief_check import lief_round_trips

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:4]


################################################################################
# Fixtures
################################################################################

@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    try:
        pe = pefile.PE(data=data, fast_load=True)
    except pefile.PEFormatError:
        pytest.skip("pefile cannot parse this file.")
    if not pe.sections:
        pytest.skip("The file has no sections.")
    if lief_round_trip(data) is not None:
        pytest.skip("LIEF cannot rebuild this file as it is.")
    return data


def garbage_offset(data: bytes) -> bytes:
    """`data` with its first section's PointerToRawData and SizeOfRawData set to values past 3.5 GiB."""
    pe = pefile.PE(data=data, fast_load=True)
    at = pe.sections[0].get_file_offset()
    out = bytearray(data)
    out[at + 16:at + 24] = struct.pack("<II", 0x10000000, 0xE0000000)  # SizeOfRawData, PointerToRawData
    return bytes(out)


################################################################################
# Tests
################################################################################

class TestLiefRoundTrip:

    @pytest.mark.parametrize("data", [b"", b"MZ" + b"\x00" * 62, b"not a PE file" * 100])
    def test_not_a_pe(self, data: bytes) -> None:
        assert lief_round_trip(data) is not None

    def test_well_formed(self, sample: bytes) -> None:
        assert lief_round_trip(sample) is None

    def test_garbage_offset(self, sample: bytes) -> None:
        assert lief_round_trip(garbage_offset(sample)) is not None

    def test_many_in_order(self, sample: bytes) -> None:
        got = lief_round_trips(iter([sample, b"", sample]), workers=2)
        assert got[0] is None and got[1] is not None and got[2] is None

    @pytest.mark.parametrize("cap, timeout", [(0, 1.0), (2**30, 0.0)])
    def test_invalid_arguments(self, cap: int, timeout: float) -> None:
        with pytest.raises(ValueError):
            lief_round_trip(b"", memory_cap=cap, timeout=timeout)

    def test_invalid_workers(self) -> None:
        with pytest.raises(ValueError):
            lief_round_trips([], workers=0)


class TestDosHeaderExtensible:

    @pytest.mark.parametrize("e_lfanew,expected", [(0x40, True), (0x80, True), (0x3C, False), (0x10, False), (0x4, False)])
    def test_e_lfanew(self, e_lfanew: int, expected: bool) -> None:
        data = bytearray(b"MZ" + bytes(0x3A)) + struct.pack("<I", e_lfanew) + bytes(0x100)
        assert dos_header_extensible(bytes(data)) is expected

    def test_too_short(self) -> None:
        assert not dos_header_extensible(b"MZ" + bytes(0x20))
