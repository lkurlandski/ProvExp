"""
Tests for the EMBER-2024 feature set (featuresets/ember2024/features.py).

Most of these tests need real executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

import collections
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
import warnings

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import pefile
import pytest
from sklearn.feature_extraction import FeatureHasher

from provexp.boxmatrix import Pieces
from provexp.featuresets.ember2024 import features
from provexp.featuresets.ember2024.features import ExportsInfo
from provexp.featuresets.ember2024.features import HeaderFileInfo
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import hash_indices
from provexp.featuresets.ember2024.features import rva_string_range
from provexp.provenance import Provenance

from tests.reference.thrember_features import PEFeatureExtractor as ReferenceExtractor

warnings.filterwarnings("ignore", category=SyntaxWarning)


ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())

EXTRACTOR = PEFeatureExtractor()
REFERENCE = ReferenceExtractor()
NAMES = EXTRACTOR.feature_names
INDEX = {n: i for i, n in enumerate(NAMES)}

# Features whose value is a count (or sum) of exactly the units of contribution they receive.
COUNT_FEATURES = [
    "general:size",
    "strings:numstrings",
    "strings:printables",
    "section:num_sections",
    "section:num_zero_size",
    "section:num_empty_name",
    "section:num_rx",
    "section:num_w",
    "section:overlay_size",
    "richheader:num_pairs",
]
COUNT_FEATURES += [n for n in NAMES if n.startswith("strings:regex_")]


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


@lru_cache(maxsize=4)
def _contribution_pieces(prov: Provenance) -> Pieces:
    """The canonical form of the raw contributions, computed once per (module-scoped) sample."""
    return prov.contributions.pieces()


def column_ranges(prov: Provenance, col: int) -> list[tuple[int, int]]:
    """The byte ranges with nonzero raw contributions to a feature."""
    pieces = _contribution_pieces(prov)
    mask = pieces.col == col
    return list(zip(pieces.lo[mask].tolist(), pieces.hi[mask].tolist()))


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:16] for f in FILES])
def sample(request: pytest.FixtureRequest) -> tuple[bytes, np.ndarray, Provenance]:
    data = Path(request.param).read_bytes()
    x, prov = EXTRACTOR.feature_vector_with_provenance(data)
    return data, x, prov


################################################################################
# Feature Names and Hashing
################################################################################


def test_feature_names() -> None:
    assert len(NAMES) == EXTRACTOR.dim == 2568
    assert len(set(NAMES)) == len(NAMES)
    for fe in EXTRACTOR.features:
        assert len(fe.feature_names) == fe.dim


@given(st.lists(st.text(min_size=0, max_size=12), min_size=1, max_size=16), st.sampled_from([10, 32, 50, 128, 1024]))
@settings(max_examples=100, deadline=None)
def test_hash_indices(items: list[str], n: int) -> None:
    """The bucket of each item matches FeatureHasher, for both input types and either sign convention."""
    buckets = hash_indices(n, items)
    for item, b in zip(items, buckets, strict=True):
        for alternate_sign in (True, False):
            for X in (
                FeatureHasher(n, input_type="string", alternate_sign=alternate_sign).transform([[item]]),
                FeatureHasher(n, input_type="pair", alternate_sign=alternate_sign).transform([[(item, 7.0)]]),
            ):
                assert X.tocsr().indices.tolist() == [b]


################################################################################
# Equivalence with thrember
################################################################################


def test_feature_vector_is_identical(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    data, x, _ = sample
    reference = REFERENCE.feature_vector(data)  # type: ignore[no-untyped-call]
    assert np.array_equal(x, reference, equal_nan=True)
    assert np.array_equal(EXTRACTOR.feature_vector(data), reference, equal_nan=True)  # type: ignore[no-untyped-call]


################################################################################
# Provenance
################################################################################


def test_shape_and_axioms(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    data, _, prov = sample
    assert prov.shape == (len(data) + 1, EXTRACTOR.dim)  # The null element is the last row.
    assert prov.feature_names == NAMES
    prov.check_axioms()
    Provenance(prov.contributions, empty="ignore").check_axioms()


def test_count_features(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """Count features receive exactly as many units of contribution as their value."""
    _, x, prov = sample
    for name in COUNT_FEATURES:
        i = INDEX[name]
        assert np.isclose(prov.colsum[i], x[i]), name


def test_histograms(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """Every histogram bin receives one unit of contribution per counted byte."""
    data, _, prov = sample
    raw = REFERENCE.raw_features(data)
    for group, counts in [
        ("histogram", raw["histogram"]),
        ("byteentropy", raw["byteentropy"]),
        ("strings", [raw["strings"]["printabledist"]]),
    ]:
        cols = [i for i, n in enumerate(NAMES) if n.startswith(f"{group}:")]
        if group == "strings":
            cols = [i for i in cols if NAMES[i].startswith("strings:printable_")]
            counts = counts[0]
        assert np.allclose(prov.colsum[cols], counts), group


def test_histogram_support(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """The provenance of each byte histogram bin is exactly the positions of that byte value."""
    data, _, prov = sample
    a = np.frombuffer(data, dtype=np.uint8)
    for v in np.unique(a)[:8]:
        positions = np.concatenate([np.arange(lo, hi) for lo, hi in column_ranges(prov, INDEX[f"histogram:byte_{v:02x}"])])
        assert np.array_equal(positions, np.flatnonzero(a == v))


def test_header_fields(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """Each header feature's provenance is exactly the bytes of the field it is read from."""
    data, _, prov = sample
    pe = _parse(data)
    if pe is None:
        pytest.skip("Not a PE file.")
    for header_name, field in HeaderFileInfo._fields:
        structure = getattr(pe, header_name)
        lo, hi = field_range(structure, field)
        assert column_ranges(prov, INDEX[f"header:{header_name.lower()}_{field}"]) == [(lo, hi)]
        assert int.from_bytes(data[lo:hi], "little") == getattr(structure, field)


def test_import_and_export_names(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """The byte ranges used for imported and exported names contain those names."""
    data, _, _ = sample
    pe = _parse(data)
    if pe is None:
        pytest.skip("Not a PE file.")
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        r = rva_string_range(pe, entry.struct.Name, len(entry.dll))
        if r is not None:
            assert data[r[0]:r[1]] == entry.dll
        for imp in entry.imports:
            if imp.name and imp.name_offset is not None:
                assert data[imp.name_offset:imp.name_offset + len(imp.name)] == imp.name
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if exp.name and exp.name_offset is not None:
                assert data[exp.name_offset:exp.name_offset + len(exp.name)] == exp.name


def test_non_pe_features_are_empty(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    """If the file does not parse, only the format-agnostic feature types receive contributions."""
    data, _, prov = sample
    if _parse(data) is not None:
        pytest.skip("A PE file.")
    agnostic = ("general:", "histogram:", "byteentropy:", "strings:")
    for i, name in enumerate(NAMES):
        if not name.startswith(agnostic):
            assert prov.is_empty[i], name


def test_pullback_completeness(sample: tuple[bytes, np.ndarray, Provenance]) -> None:
    _, _, prov = sample
    a = np.random.default_rng(0).normal(size=prov.num_features)
    assert np.isclose(prov.pullback(a).sum(), a.sum())
    ignore = Provenance(prov.contributions, empty="ignore")
    assert np.isclose(ignore.pullback(a).sum(), a[~ignore.is_empty].sum())


def test_ordinal_only_exports() -> None:
    """pefile omits the address offset of exports found only by ordinal; their provenance is the address table entry."""
    exp = pefile.ExportData(ordinal=7, address=0x1234, name=None, forwarder=None)
    assert getattr(exp, "address_offset", None) is None
    directory = SimpleNamespace(struct=SimpleNamespace(AddressOfFunctions=0x2000, Base=5))
    pe = SimpleNamespace(DIRECTORY_ENTRY_EXPORT=SimpleNamespace(symbols=[exp], struct=directory.struct), get_offset_from_rva=lambda rva: rva - 0x1C00)
    feature = ExportsInfo()  # type: ignore[no-untyped-call]
    C = feature.provenance(bytes(0x1000), pe)
    col = 1 + hash_indices(128, ["ordinal7"])[0]
    pieces = C.pieces()
    assert list(zip(pieces.col.tolist(), pieces.lo.tolist(), pieces.hi.tolist())) == [(col, 0x408, 0x40C)]


def _parse(data: bytes) -> pefile.PE | None:
    try:
        return pefile.PE(data=data)
    except (pefile.PEFormatError, AttributeError):
        return None


################################################################################
# Speed-up of the string features (an exact replacement added on top of thrember)
################################################################################


class TestSpeedups:

    @pytest.mark.parametrize("text", [
        b"",
        b"short",
        b"C:/Windows\x00https://example.com/a?b=c\x00\x01.click(here)\x00x.clickme now\x00",
        b"HKCU\\Software\x00\x00KHLMstart\x00192.168.001.010 and 10.0.0.1\x00aa:bb:cc:dd:ee:ff\x00",
        b"!This program cannot be run in DOS mode.\r\n$\x00Invoke-Expression powershell GET /index POST /x",
        b"1BoatSLRHtKNngkdXEeobR76b53LETtpyT\x00fe80::1 and 2001:db8:0:0:0:0:2:1\x00/dev/null /proc/self",
        b"PASSWORD password Password\x00\x00\x00mutexmutex\x00ftp://host/x ftp: html<script>\x7f\x7f\x7f\x7f\x7f",
    ], ids=range(7))
    def test_strings_raw_features_match_original(self, text: bytes) -> None:
        """Every regex count, at string boundaries included, equals the original per-string search."""
        extractor = features.StringExtractor()  # type: ignore[no-untyped-call]
        original = features._strings_raw_features_original(extractor, text, None)  # type: ignore[no-untyped-call]
        assert features._strings_raw_features(extractor, text, None) == original

    def test_strings_on_files(self, sample: tuple[bytes, np.ndarray, Provenance]) -> None:
        data, _, _ = sample
        extractor = features.StringExtractor()  # type: ignore[no-untyped-call]
        original = features._strings_raw_features_original(extractor, data, None)  # type: ignore[no-untyped-call]
        assert features._strings_raw_features(extractor, data, None) == original


################################################################################
# Speed-up of the byte counts (an exact replacement of collections.Counter, added on top of thrember and pefile)
################################################################################


def _late_values() -> bytes:
    """Bytes whose last values first appear well beyond the first chunk of byte_counter."""
    rng = np.random.default_rng(0)
    return bytes(rng.integers(0, 40, size=3 * (1 << 16), dtype=np.uint8)) + bytes(range(255, 39, -1))


class TestByteCounter:

    @pytest.mark.parametrize("data", [
        b"",
        b"a",
        b"\x00" * 1000,
        bytes(range(256)),
        bytes(range(255, -1, -1)) * 3,
        bytes(np.random.default_rng(1).integers(0, 256, size=100_000, dtype=np.uint8)),
        _late_values(),
        bytearray(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"),
    ], ids=range(8))
    def test_matches_counter(self, data: bytes) -> None:
        """The same counts in the same order, as a Counter."""
        counts = features.byte_counter(data)
        assert isinstance(counts, collections.Counter)
        assert list(counts.items()) == list(collections.Counter(data).items())

    @pytest.mark.parametrize("data", [[3, 1, 3, 2], "hello", memoryview(b"abca")], ids=["list", "str", "memoryview"])
    def test_other_inputs_fall_back(self, data: object) -> None:
        assert list(features.byte_counter(data).items()) == list(collections.Counter(data).items())  # type: ignore[call-overload]

    def test_installed(self) -> None:
        assert getattr(features, "Counter") is features.byte_counter
        assert getattr(pefile, "Counter") is features.byte_counter

    def test_pefile_on_files(self, sample: tuple[bytes, np.ndarray, Provenance], monkeypatch: pytest.MonkeyPatch) -> None:
        """pefile's warnings and section entropies are the same with and without the replacement."""
        needs_files()
        data, _, _ = sample
        patched = _parse(data)
        monkeypatch.setattr(pefile, "Counter", collections.Counter)
        original = _parse(data)
        if original is None:
            assert patched is None
            return
        assert patched is not None
        assert patched.get_warnings() == original.get_warnings()
        assert [s.get_entropy() for s in patched.sections] == [s.get_entropy() for s in original.sections]

