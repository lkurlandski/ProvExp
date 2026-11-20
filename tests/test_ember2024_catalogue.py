"""
Tests for provexp.featuresets.ember2024.catalogue: the layout clauses of the precondition (`plain_layout`), each on a
test file edited into the layout it excludes; and the item-stated operations' declarations, each against re-extraction
of the file our own edit writes.

The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import struct
from typing import Optional
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024 import features
from provexp.featuresets.ember2024.catalogue import DATA_CHARACTERISTICS
from provexp.featuresets.ember2024.catalogue import DEBUG_ENTRY
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import plain_layout
from provexp.featuresets.ember2024.catalogue import predict_add_imports
from provexp.featuresets.ember2024.catalogue import predict_add_section
from provexp.featuresets.ember2024.catalogue import new_section_slot
from provexp.featuresets.ember2024.catalogue import predict_header_growth
from provexp.featuresets.ember2024.catalogue import predict_insert_gap
from provexp.featuresets.ember2024.catalogue import predict_rename
from provexp.featuresets.ember2024.catalogue import predict_zero_entry
from provexp.featuresets.ember2024.catalogue import write_header_growth
from provexp.featuresets.ember2024.catalogue import write_section
from provexp.featuresets.ember2024.catalogue import written_add_imports
from provexp.featuresets.ember2024.catalogue import written_add_section
from provexp.featuresets.ember2024.catalogue import written_rename
from provexp.featuresets.ember2024.catalogue import written_zero_entry
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.reach import Prediction

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see pipeline/setup/make_fixtures.py).")


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
        # Point the (unused) third directory entry's extent past the last raw data, inside the file: pefile's own
        # overlay rule then starts the overlay there, which the layout clause excludes, monkeypatched back below. Under
        # the rule installed by `features` (LIEF's, R7), the overlay still starts after the last section, and the
        # file stays plain.
        z = sample + b"\x00" * 0x400
        entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2]
        rva = last.VirtualAddress + max(last.SizeOfRawData - 0x10, 0)
        z = _put(_put(z, entry.get_file_offset(), rva), entry.get_file_offset() + 4, 0x200)
        assert _pe(z).get_overlay_data_start_offset() == max(ends)
        assert plain_layout(_pe(z)) == plain_layout(_pe(sample + b"\x00" * 0x400))
        with pytest.MonkeyPatch.context() as m:
            m.setattr(pefile.PE, "get_overlay_data_start_offset", features.PEFILE_OVERLAY_START)
            assert _pe(z).get_overlay_data_start_offset() > max(ends)
            assert not plain_layout(_pe(z))


################################################################################
# The item-stated operations, declared exactly
################################################################################


@pytest.fixture(scope="module")
def extractor() -> PEFeatureExtractor:
    return fix_quirks(PEFeatureExtractor())


def _check_exact(extractor: PEFeatureExtractor, p: Optional[Prediction]) -> None:
    """The declared prediction equals re-extraction of the written file on every modeled feature, or it is flagged."""
    if p is None or p.table is None:
        return
    modeled = ~np.array([n.startswith("pefilewarnings:") for n in extractor.feature_names])
    x = np.asarray(extractor.feature_vector(p.new))  # type: ignore[no-untyped-call]
    y = np.asarray(p.features(extractor.readouts))
    same = (x == y) | (np.isnan(x) & np.isnan(y))
    names = np.array(extractor.feature_names)
    assert same[modeled].all(), names[modeled & ~same][:10].tolist()


class TestDeclaredOperations:

    @pytest.mark.parametrize("before_overlay", [False, True])
    @pytest.mark.parametrize("name,content,characteristics", [
        (b".pv0", bytes(range(256)) * 16, DATA_CHARACTERISTICS),
        (b"", b"printable text " * 40, 0x60000020),
    ])
    def test_add_section(self, extractor: PEFeatureExtractor, sample: bytes, name: bytes, content: bytes,
                         characteristics: int, before_overlay: bool) -> None:
        table = extractor.item_table(sample)
        p = predict_add_section(extractor, table, sample, name, content, characteristics, before_overlay)
        if p is not None:
            assert p.new == write_section(sample, name, content, characteristics, before_overlay).new  # type: ignore[union-attr]
        _check_exact(extractor, p)

    @pytest.mark.parametrize("library,functions", [(b"pvext.dll", [b"PvOne", b"PvTwo"]), (b"pvempty.dll", [])])
    def test_add_imports(self, extractor: PEFeatureExtractor, sample: bytes, library: bytes, functions: list[bytes]) -> None:
        _check_exact(extractor, predict_add_imports(extractor, extractor.item_table(sample), sample, library, functions, False))

    @pytest.mark.parametrize("at_pe_header", [True, False])
    @pytest.mark.parametrize("fill", [b"\x00", b"A"])
    def test_insert_gap(self, extractor: PEFeatureExtractor, sample: bytes, at_pe_header: bool, fill: bytes) -> None:
        fa = _pe(sample).OPTIONAL_HEADER.FileAlignment or 0x200
        _check_exact(extractor, predict_insert_gap(extractor, extractor.item_table(sample), sample, at_pe_header, fill * fa))

    @pytest.mark.parametrize("fill", [b"\x00", b"A"])
    def test_header_growth(self, extractor: PEFeatureExtractor, sample: bytes, fill: bytes) -> None:
        fa = _pe(sample).OPTIONAL_HEADER.FileAlignment or 0x200
        _check_exact(extractor, predict_header_growth(extractor, extractor.item_table(sample), sample, fill * fa))

    @pytest.mark.parametrize("name", [b"", b".data", b"\xff\xfe.x"])
    def test_rename(self, extractor: PEFeatureExtractor, sample: bytes, name: bytes) -> None:
        _check_exact(extractor, predict_rename(extractor, extractor.item_table(sample), sample, 0, name))

    @pytest.mark.parametrize("index", [DEBUG_ENTRY, SECURITY_ENTRY])
    def test_zero_entry(self, extractor: PEFeatureExtractor, sample: bytes, index: int) -> None:
        _check_exact(extractor, predict_zero_entry(extractor, extractor.item_table(sample), sample, index))


################################################################################
# The same operations, written only
################################################################################


def _new(p: Optional[Prediction]) -> Optional[bytes]:
    return None if p is None else p.new


class TestWrittenOnly:
    """Each `written_*` returns the file its `predict_*` writes, and None exactly where the prediction is None."""

    @pytest.mark.parametrize("before_overlay", [False, True])
    def test_add_section(self, extractor: PEFeatureExtractor, sample: bytes, before_overlay: bool) -> None:
        name, content = b".pv0", bytes(range(256)) * 16
        p = predict_add_section(extractor, extractor.item_table(sample), sample, name, content, DATA_CHARACTERISTICS,
                                before_overlay)
        assert written_add_section(sample, name, content, DATA_CHARACTERISTICS, before_overlay) == _new(p)

    @pytest.mark.parametrize("library,functions", [(b"pvext.dll", [b"PvOne", b"PvTwo"]), (b"pvempty.dll", [])])
    def test_add_imports(self, extractor: PEFeatureExtractor, sample: bytes, library: bytes, functions: list[bytes]) -> None:
        p = predict_add_imports(extractor, extractor.item_table(sample), sample, library, functions, False)
        assert written_add_imports(sample, library, functions, False) == _new(p)

    @pytest.mark.parametrize("index,name", [(0, b".data"), (0, b""), (99, b".x")])
    def test_rename(self, extractor: PEFeatureExtractor, sample: bytes, index: int, name: bytes) -> None:
        p = predict_rename(extractor, extractor.item_table(sample), sample, index, name)
        assert written_rename(sample, index, name) == _new(p)

    @pytest.mark.parametrize("index", [DEBUG_ENTRY, SECURITY_ENTRY])
    def test_zero_entry(self, extractor: PEFeatureExtractor, sample: bytes, index: int) -> None:
        p = predict_zero_entry(extractor, extractor.item_table(sample), sample, index)
        assert written_zero_entry(sample, index) == _new(p)


################################################################################
# Header growth
################################################################################


class TestHeaderGrowth:

    @staticmethod
    def _grown(sample: bytes, slots: int) -> tuple[pefile.PE, bytes, int]:
        """The file with the headers grown by enough FileAlignment units for `slots` section headers (skip if not)."""
        pe = _pe(sample)
        fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200
        k = -(-40 * slots // fa) * fa
        written = write_header_growth(sample, b"\x00" * k)
        if written is None:
            pytest.skip("The headers cannot grow on this file.")
        return pe, written.new, k

    def test_layout(self, sample: bytes) -> None:
        pe, z, k = self._grown(sample, 1)
        new = _pe(z)
        at = pe.OPTIONAL_HEADER.SizeOfHeaders
        assert new.OPTIONAL_HEADER.SizeOfHeaders == at + k
        assert new.OPTIONAL_HEADER.SizeOfHeaders <= min(s.VirtualAddress for s in new.sections)
        for s, t in zip(pe.sections, new.sections, strict=True):
            assert t.PointerToRawData == s.PointerToRawData + (k if s.SizeOfRawData else 0)
            assert t.get_data() == s.get_data()
        assert z[at + k:] == sample[at:]
        assert z[at:at + k] == b"\x00" * k

    def test_makes_room(self, sample: bytes) -> None:
        """Thirty section headers fit after the growth, one after another, when the headers past the table are free."""
        pe, z, _ = self._grown(sample, 30)
        end = pe.DOS_HEADER.e_lfanew + 24 + pe.FILE_HEADER.SizeOfOptionalHeader + 40 * pe.FILE_HEADER.NumberOfSections
        if any(sample[end:pe.OPTIONAL_HEADER.SizeOfHeaders]):
            pytest.skip("The headers past the section table hold data.")
        for _ in range(30):
            new = _pe(z)
            slot = new_section_slot(new, z)
            assert slot is not None
            n = new.FILE_HEADER.NumberOfSections + 1
            header = b".pv\x00\x00\x00\x00\x00" + b"\x00" * 32
            z = z[:slot[0]] + header + z[slot[0] + 40:]
            offset = new.FILE_HEADER.get_file_offset() + 2
            z = z[:offset] + struct.pack("<H", n) + z[offset + 2:]

    @pytest.mark.parametrize("fill", [b"\x00", b"A"])
    def test_sums_exact(self, sample: bytes, fill: bytes) -> None:
        extractor = SumsFeatureExtractor()
        fa = _pe(sample).OPTIONAL_HEADER.FileAlignment or 0x200
        _check_exact(extractor, predict_header_growth(extractor, extractor.item_table(sample), sample, fill * fa))
