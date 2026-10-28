"""
Tests for the item layer of the EMBER-2024 feature set (the `items` methods and `readouts` properties of features.py).

The real-file tests need executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.features import ImportsInfo
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import clipped
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import header_locating
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import zstring_end
from provexp.items import Item
from provexp.items import evaluate
from provexp.items import project
from provexp.reach import ByteEdit
from provexp.reach import predict

warnings.filterwarnings("ignore", category=SyntaxWarning)


ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:6]

EXTRACTOR = merge_import_descriptors(PEFeatureExtractor())
NAMES = EXTRACTOR.feature_names
ORIGINAL_IMPORTS = ImportsInfo()  # type: ignore[no-untyped-call]
MODELED = np.array([not n.startswith("pefilewarnings:") for n in NAMES])


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


################################################################################
# Readouts and helpers
################################################################################


class TestReadouts:

    @pytest.mark.parametrize("fe", EXTRACTOR.features + [ORIGINAL_IMPORTS], ids=lambda fe: type(fe).__name__)
    def test_dims(self, fe: object) -> None:
        assert sum(r.dim for r in fe.readouts) == fe.dim  # type: ignore[attr-defined]

    @pytest.mark.parametrize(
        "ranges,expected",
        [
            ([None, (5, 3)], ()),
            ([(-2, 4), (8, 20)], ((0, 4), (8, 10))),
            ([(1, 2), (1, 2)], ((1, 2), (1, 2))),
        ],
    )
    def test_clipped(self, ranges: list[tuple[int, int] | None], expected: tuple[tuple[int, int], ...]) -> None:
        assert clipped(10, ranges) == expected

    @pytest.mark.parametrize(
        "bytez,lo,limit,expected",
        [
            (b"abc\0def", 0, 16, 4),
            (b"abc\0def", 4, 16, 4 + 16),
            (b"abcdef\0", 0, 3, 3),
            (b"\0", 0, 8, 1),
        ],
    )
    def test_zstring_end(self, bytez: bytes, lo: int, limit: int, expected: int) -> None:
        assert zstring_end(bytez, lo, limit) == expected


class TestNonPE:

    @pytest.mark.parametrize("bytez", [b"x", b"MZ" + bytes(100), bytes(range(256)) * 20])
    def test_exact(self, bytez: bytes) -> None:
        x = EXTRACTOR.feature_vector(bytez)  # type: ignore[no-untyped-call]
        y = evaluate(EXTRACTOR.item_table(bytez), EXTRACTOR.readouts)
        np.testing.assert_array_equal(x[MODELED], y[MODELED])


################################################################################
# Real files: G1 and G2
################################################################################


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    return Path(request.param).read_bytes()


class TestRealFiles:

    def test_g1_exact(self, sample: bytes) -> None:
        needs_files()
        x = EXTRACTOR.feature_vector(sample)  # type: ignore[no-untyped-call]
        y = evaluate(EXTRACTOR.item_table(sample), EXTRACTOR.readouts)
        bad = [NAMES[i] for i in np.where(MODELED & (x != y))[0]]
        assert not bad

    def test_g1_original_imports(self, sample: bytes) -> None:
        needs_files()
        fe = ORIGINAL_IMPORTS
        pe = pefile.PE(data=sample)
        np.testing.assert_array_equal(fe.feature_vector(sample, pe), evaluate(fe.items(sample, pe), fe.readouts))
        assert all(not item.local for item in fe.items(sample, pe).of_kind("import"))

    def test_g2_projection(self, sample: bytes) -> None:
        needs_files()
        p = EXTRACTOR.provenance(sample).contributions.pieces()
        q = project(EXTRACTOR.item_table(sample), EXTRACTOR.readouts).pieces()
        for a, b in zip(p[:3], q[:3]):
            np.testing.assert_array_equal(a, b)
        np.testing.assert_allclose(p.val, q.val, rtol=1e-12)


################################################################################
# Real files: locating ranges (a small G5)
################################################################################


def _parsed_items(extractor: PEFeatureExtractor, bytez: bytes) -> dict[tuple[object, ...], Item]:
    out: dict[tuple[object, ...], Item] = {}
    for item in extractor.item_table(bytez).items:
        if item.kind in ("bytes", "window", "string"):
            continue
        key = (item.kind, item.members, item.attrs.get("field"))
        k = 0
        while (*key, k) in out:
            k += 1
        out[(*key, k)] = item
    return out


class TestLocating:

    def test_pe_items_are_located(self, sample: bytes) -> None:
        needs_files()
        pe = pefile.PE(data=sample)
        e_lfanew = field_range(pe.DOS_HEADER, "e_lfanew")
        for item in _parsed_items(EXTRACTOR, sample).values():
            # The first four bytes (general) are read by position, not parsed.
            if item.kind != "field" or item.attrs.get("field") is not None:
                assert e_lfanew in item.locating, item.kind

    def test_per_structure(self, sample: bytes) -> None:
        # Header fields and Rich pairs are located through the headers only, never through a directory's data.
        needs_files()
        pe = pefile.PE(data=sample)
        base = set(header_locating(pe))
        for item in _parsed_items(EXTRACTOR, sample).values():
            if item.kind == "field" and item.attrs.get("field") in ("Machine", "SizeOfCode", "e_cblp"):
                assert set(item.locating) == base, item.attrs
            if item.kind == "rich_pair":
                assert set(item.locating) - base == {(0x80, pe.OPTIONAL_HEADER.get_file_offset())}

    def test_unmapped_address_past_end(self, sample: bytes) -> None:
        # pefile reads an address in no section at that file offset once the file reaches it.
        needs_files()
        pe = pefile.PE(data=sample)
        rva = 0x7FFF0000
        if pe.get_section_by_rva(rva) is not None:
            pytest.skip("The address lies in a section.")
        assert rva_ranges(pe, rva, 4) == ((rva, rva + 4),)
        assert rva_ranges(pe, rva, 0) == ()

    def test_flips(self, sample: bytes) -> None:
        needs_files()
        pe = pefile.PE(data=sample)
        lo = pe.sections[0].get_file_offset() if pe.sections else 0
        before = _parsed_items(EXTRACTOR, sample)
        for offset in range(lo, min(lo + 64, len(sample))):
            edited = bytearray(sample)
            edited[offset] ^= 0xFF
            after = _parsed_items(EXTRACTOR, bytes(edited))
            for items, other in [(before, after), (after, before)]:
                for key, item in items.items():
                    if key not in other:
                        assert any(a <= offset < b for a, b in item.locating), (offset, item.kind)


################################################################################
# Real files: the C1 engine
################################################################################


def _edits(sample: bytes) -> list[ByteEdit]:
    """An append with printable text (strings across the old end), a DOS-header write, and a write into code."""
    rng = np.random.default_rng(0)
    pe = pefile.PE(data=sample)
    edits = [
        ByteEdit(len(sample), len(sample), b"tail text http://example.com " * 4),
        ByteEdit(2, 60, rng.integers(0, 256, 58, dtype=np.uint8).tobytes()),
    ]
    data = [s for s in pe.sections if s.SizeOfRawData >= 256 and s.PointerToRawData + s.SizeOfRawData <= len(sample)]
    if data:
        lo = data[0].PointerToRawData + 64
        edits.append(ByteEdit(lo, lo + 32, b"PRINTABLE_" + rng.integers(0, 256, 22, dtype=np.uint8).tobytes()))
    return edits


class TestEngine:

    def test_exact_or_flagged(self, sample: bytes) -> None:
        needs_files()
        table = EXTRACTOR.item_table(sample)
        for edit in _edits(sample):
            p = predict(table, sample, edit, EXTRACTOR.recognizers)
            if p.table is None:
                assert p.flagged and p.reason
                continue
            x = EXTRACTOR.feature_vector(p.new)  # type: ignore[no-untyped-call]
            bad = [NAMES[i] for i in np.where(MODELED & (x != p.features(EXTRACTOR.readouts)))[0]]
            assert not bad, (edit.lo, edit.hi)
