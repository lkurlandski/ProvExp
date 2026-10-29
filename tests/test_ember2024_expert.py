"""
Tests for provexp.featuresets.ember2024.expert: Gimenez et al.'s 40 features on pefile, their two assign-instead-of-
accumulate quirks, and the patched variant's claim that adding a section or an import never lowers a feature.

The real-file tests need executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import sys
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.expert import DEFAULT_DOS_STUB
from provexp.featuresets.ember2024.expert import ExpertFeatureExtractor
from provexp.featuresets.ember2024.expert import ExpertFeatures

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from catalogue_checks import add_imports  # noqa: E402
from catalogue_checks import add_section  # noqa: E402

DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]

PATCHED = ExpertFeatureExtractor()
QUIRKY = ExpertFeatureExtractor(accumulate=False)
NAMES = ExpertFeatures().feature_names
INDEX = {n: i for i, n in enumerate(NAMES)}
DATA_CHARACTERISTICS = 0xC0000040


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


def _pe(data: bytes) -> pefile.PE | None:
    try:
        return pefile.PE(data=data)
    except pefile.PEFormatError:
        return None


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    if _pe(data) is None:
        pytest.skip("pefile cannot parse this file.")
    return data


################################################################################
# Layout
################################################################################


class TestLayout:

    def test_forty_features_in_their_order(self) -> None:
        assert len(NAMES) == 40 == PATCHED.dim
        assert NAMES[0] == "kernel32.dll" and NAMES[15] == "nb_imports" and NAMES[-1] == "nb_sections"
        assert NAMES[31:33] == [".text_info", ".text-size"]

    def test_not_a_pe_is_zero(self) -> None:
        assert not PATCHED.feature_vector(b"not a PE file" * 10).any()  # type: ignore[no-untyped-call]

    def test_default_stub_length(self) -> None:
        # Their stub runs from the end of the DOS header to a PE header at 0xE0 (stub and a Rich header).
        assert len(DEFAULT_DOS_STUB) == 0xE0 - 64

    def test_default_stub_is_unmodified(self, sample: bytes) -> None:
        pe = _pe(sample)
        assert pe is not None
        if pe.DOS_HEADER.e_lfanew != 0xE0:
            pytest.skip("The PE header is not at 0xE0.")
        z = sample[:64] + DEFAULT_DOS_STUB + sample[0xE0:]
        assert PATCHED.feature_vector(z)[INDEX["modified_dos_stub"]] == 0  # type: ignore[no-untyped-call]


################################################################################
# The quirks and the patched variant
################################################################################


class TestQuirks:

    def test_same_on_unedited_files_without_repeats(self, sample: bytes) -> None:
        pe = _pe(sample)
        assert pe is not None
        names = [s.Name.split(b"\x00")[0] for s in pe.sections]
        libraries = [e.dll.lower() for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])]
        if len(set(names)) < len(names) or len(set(libraries)) < len(libraries):
            pytest.skip("The file repeats a section name or a library.")
        np.testing.assert_array_equal(PATCHED.feature_vector(sample), QUIRKY.feature_vector(sample))  # type: ignore[no-untyped-call]

    def test_a_second_text_section_replaces_its_size(self, sample: bytes) -> None:
        pe = _pe(sample)
        assert pe is not None
        if not any(s.Name.split(b"\x00")[0] == b".text" and s.SizeOfRawData > 0x200 for s in pe.sections):
            pytest.skip("No .text section larger than the added one.")
        written = add_section(sample, b".text", b"\x00" * 16, DATA_CHARACTERISTICS, before_overlay=False)
        if written is None:
            pytest.skip("No room for another section header.")
        j = INDEX[".text-size"]
        before = QUIRKY.feature_vector(sample)[j]  # type: ignore[no-untyped-call]
        assert QUIRKY.feature_vector(written[0])[j] < before  # type: ignore[no-untyped-call]
        assert PATCHED.feature_vector(written[0])[j] > before  # type: ignore[no-untyped-call]

    def test_a_second_kernel32_descriptor_replaces_its_count(self, sample: bytes) -> None:
        j = INDEX["kernel32.dll"]
        before = QUIRKY.feature_vector(sample)[j]  # type: ignore[no-untyped-call]
        if before < 2:
            pytest.skip("Fewer than two functions from kernel32.dll.")
        written = add_imports(sample, b"KERNEL32.dll", [b"Sleep"], before_overlay=False)
        if written is None:
            pytest.skip("No room for the import section.")
        assert QUIRKY.feature_vector(written)[j] == 1  # type: ignore[no-untyped-call]
        assert PATCHED.feature_vector(written)[j] == before + 1  # type: ignore[no-untyped-call]


class TestAdditionsRaise:

    @pytest.mark.parametrize("name", [b".text", b".data", b".rsrc", b".rdata", b".pv0"])
    def test_add_section(self, sample: bytes, name: bytes) -> None:
        content = bytes(range(256)) * 8
        written = add_section(sample, name, content, DATA_CHARACTERISTICS, before_overlay=False)
        if written is None:
            pytest.skip("No room for another section header.")
        x, y = PATCHED.feature_vector(sample), PATCHED.feature_vector(written[0])  # type: ignore[no-untyped-call]
        assert not [NAMES[i] for i in np.where(y < x)[0]]

    def test_add_imports(self, sample: bytes) -> None:
        written = add_imports(sample, b"KERNEL32.dll", [b"GetTickCount", b"Sleep"], before_overlay=False)
        if written is None:
            pytest.skip("No room for the import section.")
        x, y = PATCHED.feature_vector(sample), PATCHED.feature_vector(written)  # type: ignore[no-untyped-call]
        assert not [NAMES[i] for i in np.where(y < x)[0]]
