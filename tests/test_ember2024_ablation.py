"""
Tests for featuresets/ember2024/ablation.py, on the test fixtures (real PE files).
"""

from pathlib import Path
import warnings

import numpy as np
import pytest

from provexp.featuresets.ember2024.ablation import LAYOUT_FIELDS
from provexp.featuresets.ember2024.ablation import PROTECTED_FIELDS
from provexp.featuresets.ember2024.ablation import Protection
from provexp.featuresets.ember2024.ablation import breaking_fields
from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import typical_values
from provexp.featuresets.ember2024.ablation import verify


warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())
PE_FILES = [f for f in FILES if parse(f.read_bytes()).status == "ok"]


def needs_files() -> None:
    if not PE_FILES:
        pytest.skip(f"No PE test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


@pytest.fixture(scope="module", params=PE_FILES, ids=[f.name[:16] for f in PE_FILES])
def data(request: pytest.FixtureRequest) -> bytes:
    return Path(request.param).read_bytes()


def zeroed(data: bytes, lo: int, hi: int) -> bytes:
    return data[:lo] + bytes(hi - lo) + data[hi:]


################################################################################
# Header Fields
################################################################################


def test_protected_fields_include_layout() -> None:
    assert LAYOUT_FIELDS <= PROTECTED_FIELDS


def test_header_fields(data: bytes) -> None:
    pe = parse(data).pe
    assert pe is not None
    fields = {f.key: f for f in header_fields(pe)}
    assert (fields["IMAGE_DOS_HEADER.e_magic"].lo, fields["IMAGE_DOS_HEADER.e_magic"].hi) == (0, 2)
    assert (fields["IMAGE_DOS_HEADER.e_lfanew"].lo, fields["IMAGE_DOS_HEADER.e_lfanew"].hi) == (60, 64)
    e_lfanew = int.from_bytes(data[60:64], "little")
    assert fields["IMAGE_NT_HEADERS.Signature"].lo == e_lfanew
    assert all(f.hi > f.lo for f in fields.values())


################################################################################
# Protection and Verification
################################################################################


def test_protect_keeps_the_file_intact(data: bytes) -> None:
    """Zeroing every unprotected byte at once keeps the file parseable with the same layout (checked by protect)."""
    protection = protect(data, per_file=False)
    assert protection.mask[:2].all() and protection.mask[60:64].all()
    assert protection.header[:64].all()
    assert not protection.mask[~protection.header].any()


def test_verify_accepts_unchanged_and_content_ablation(data: bytes) -> None:
    protection = protect(data, per_file=False)
    assert verify(protection, data, data) is None
    # Zero the last quarter of the file outside the headers.
    content = np.flatnonzero(~protection.header)
    lo = int(content[len(content) * 3 // 4])
    ablated = np.frombuffer(data, dtype=np.uint8).copy()
    ablated[lo:][~protection.header[lo:]] = 0
    assert verify(protection, data, ablated.tobytes()) is None


def test_verify_detects_problems(data: bytes) -> None:
    protection = protect(data, per_file=False)
    assert verify(protection, data, zeroed(data, 0, 2)) == "2 protected bytes changed"
    assert verify(protection, data, data[:-1]) is not None
    assert verify(protection, data, data, is_pe=0.0) == "is_pe = 0.0"
    # Without protection, zeroing the signature or the number of sections is caught by parsing or the layout.
    unprotected = Protection(np.zeros(len(data), dtype=np.bool_), protection.header, protection.header_values, protection.layout, frozenset(), frozenset())
    assert verify(unprotected, data, zeroed(data, 0, 2)) == "parse status not_pe"
    e_lfanew = int.from_bytes(data[60:64], "little")
    if any(data[e_lfanew + 6:e_lfanew + 8]):
        assert verify(unprotected, data, zeroed(data, e_lfanew + 6, e_lfanew + 8)) == "layout changed"


def test_typical_header_values(data: bytes) -> None:
    """Level 3: header fields take their typical values, which keep the file intact (checked by protect)."""
    zeros = protect(data, per_file=False)
    typical = protect(data, per_file=False, header="typical")
    assert not zeros.header_values.any()
    assert (typical.header_values[~typical.header] == 0).all()
    pe = parse(data).pe
    assert pe is not None
    machine = next(f for f in header_fields(pe) if f.key == "IMAGE_FILE_HEADER.Machine")
    assert typical.header_values[machine.lo:machine.hi].tobytes() == typical_values()["IMAGE_FILE_HEADER.Machine"]


def test_protect_rejects_non_pe() -> None:
    with pytest.raises(ValueError):
        protect(b"not a PE file" * 100)


@pytest.mark.parametrize("index", [0, 1])
def test_breaking_fields_and_per_file_protection(index: int) -> None:
    needs_files()
    small = sorted(PE_FILES, key=lambda f: f.stat().st_size)
    data = small[index].read_bytes()
    broken = {f.key for f, _ in breaking_fields(data)}
    assert {"IMAGE_DOS_HEADER.e_magic", "IMAGE_DOS_HEADER.e_lfanew", "IMAGE_NT_HEADERS.Signature"} <= broken
    protection = protect(data)
    assert protection.file_fields == frozenset(broken - PROTECTED_FIELDS)
    assert protection.fields == PROTECTED_FIELDS | protection.file_fields
