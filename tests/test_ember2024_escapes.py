"""
Tests for provexp.featuresets.ember2024.escapes: every escape write changes one field of the file and nothing else (the
escape audit's one-field check), with the values it documents.

The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import struct
import warnings

import pefile
import pytest

from provexp.featuresets.ember2024 import features  # noqa: F401  (installs the overlay rule and the guard in pefile)
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.escapes import WRITES

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    try:
        pefile.PE(data=data)
    except pefile.PEFormatError:
        pytest.skip("pefile cannot parse this file.")
    return data


################################################################################
# One field per write
################################################################################


class TestWrites:

    @pytest.mark.parametrize("write", list(WRITES))
    def test_one_field(self, sample: bytes, write: str) -> None:
        out = WRITES[write](pefile.PE(data=sample), len(sample))
        if out is None:
            pytest.skip(f"{write} does not apply to this file.")
        assert len(out) == len(sample)
        changed = [i for i, (a, b) in enumerate(zip(out, sample)) if a != b]
        assert len(changed) <= 8
        assert not changed or changed[-1] - changed[0] < 8

    def test_cert_entry_value(self, sample: bytes) -> None:
        pe = pefile.PE(data=sample)
        d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[SECURITY_ENTRY]
        lo = d.get_file_offset()
        out = WRITES["cert_entry"](pe, len(sample))
        assert out is not None
        va, size = struct.unpack("<II", out[lo:lo + 8])
        if d.VirtualAddress and d.Size:
            assert (va, size) == (d.VirtualAddress, d.Size + len(sample))
        else:
            assert (va, size) == (len(sample), 8)

    def test_image_size_value(self, sample: bytes) -> None:
        pe = pefile.PE(data=sample)
        oh = pe.OPTIONAL_HEADER
        out = WRITES["image_size"](pe, len(sample))
        assert out is not None
        assert pefile.PE(data=out).OPTIONAL_HEADER.SizeOfImage == oh.SizeOfImage + (oh.SectionAlignment or 0x1000)
