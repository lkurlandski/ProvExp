"""
Tests for scripts/a1_adaptive.py: the adaptive search's C1 predictors come from the engine (derivation step 9), with
the hand predictors of scripts/a_c1_table0.py as their oracle.

The tests need executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import sys
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from a1_adaptive import DATA_PROPS  # noqa: E402
from a1_adaptive import Donors  # noqa: E402
from a1_adaptive import bucket_names  # noqa: E402
from a1_adaptive import engine_predictors  # noqa: E402
from a1_adaptive import menu  # noqa: E402
from a_c1_table0 import predict_add_section  # noqa: E402
from a_c1_table0 import predict_append  # noqa: E402
from catalogue_checks import add_section as write_section  # noqa: E402

DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]

EXTRACTOR = merge_import_descriptors(PEFeatureExtractor())
NAMES = EXTRACTOR.feature_names
INDEX = {n: i for i, n in enumerate(NAMES)}
MODELED = np.array([not n.startswith("pefilewarnings:") for n in NAMES])
# The section features an overlay enters: its own three and the summaries over sections and overlay.
OVERLAY = np.array([n in {"section:overlay_size", "section:overlay_size_ratio", "section:overlay_entropy",
                          "section:max_entropy", "section:min_entropy", "section:max_size_ratio",
                          "section:min_size_ratio"} for n in NAMES])
DATA_CHARACTERISTICS = 0xC0000040


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


def _overlay(data: bytes) -> bool:
    try:
        return pefile.PE(data=data, fast_load=True).get_overlay_data_start_offset() is not None
    except pefile.PEFormatError:
        return False


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> bytes:
    data: bytes = request.param.read_bytes()
    return data


################################################################################
# The engine against the hand predictors
################################################################################


class TestEnginePredictors:

    @pytest.mark.parametrize("seed", [0, 1])
    def test_append_equals_hand(self, sample: bytes, seed: int) -> None:
        needs_files()
        # The menu's form: a NUL first, so no string merges across the old end (the hand predictor assumes none).
        blob = b"\x00" + np.random.default_rng(seed).integers(0, 256, 4096, dtype=np.uint8).tobytes()
        append, _ = engine_predictors(EXTRACTOR)
        try:
            y = append(EXTRACTOR, sample, blob)
        except RuntimeError:
            pytest.skip("The engine flags this append (a structure past the end of the file).")
        hand = predict_append(EXTRACTOR, sample, blob)
        bad = [NAMES[i] for i in np.where(MODELED & (y != hand))[0]]
        assert not bad

    @pytest.mark.parametrize("seed", [0, 1])
    def test_append_equals_reextraction(self, sample: bytes, seed: int) -> None:
        needs_files()
        # Any first byte: the engine re-recognizes a string the append extends.
        blob = np.random.default_rng(seed).integers(0, 256, 4096, dtype=np.uint8).tobytes()
        append, _ = engine_predictors(EXTRACTOR)
        try:
            y = append(EXTRACTOR, sample, blob)
        except RuntimeError:
            pytest.skip("The engine flags this append (a structure past the end of the file).")
        x = EXTRACTOR.feature_vector(sample + blob)  # type: ignore[no-untyped-call]
        bad = [NAMES[i] for i in np.where(MODELED & (y != x))[0]]
        assert not bad

    def test_add_section_equals_hand_but_overlay(self, sample: bytes) -> None:
        needs_files()
        content = bytes(range(256)) * 16
        _, section = engine_predictors(EXTRACTOR)
        try:
            hand = predict_add_section(EXTRACTOR, sample, ".pv0", content, DATA_PROPS)
        except pefile.PEFormatError:
            pytest.skip("Not a PE.")
        y = section(EXTRACTOR, sample, ".pv0", content, DATA_PROPS)
        # The hand predictor keeps the overlay (it models LIEF, which puts the section before it); the engine's
        # declared layout ends the file with the section, which leaves no overlay.
        keep = MODELED & ~OVERLAY if _overlay(sample) else MODELED
        bad = [NAMES[i] for i in np.where(keep & (y != hand))[0]]
        assert not bad
        assert y[INDEX["section:overlay_size"]] == 0

    def test_add_section_removes_overlay_as_pefile(self, sample: bytes) -> None:
        needs_files()
        if not _overlay(sample):
            pytest.skip("No overlay.")
        written = write_section(sample, b".pv0", bytes(range(256)) * 16, DATA_CHARACTERISTICS, before_overlay=False)
        if written is None:
            pytest.skip("No room for another section header.")
        x = EXTRACTOR.feature_vector(written[0])  # type: ignore[no-untyped-call]
        assert x[INDEX["section:overlay_size"]] == 0

    def test_no_missing_values(self, sample: bytes) -> None:
        needs_files()
        # The unmodeled features (pefile's warnings) keep the file's values: a NaN would read as missing to a GBDT.
        append, section = engine_predictors(EXTRACTOR)
        x = EXTRACTOR.feature_vector(sample)  # type: ignore[no-untyped-call]
        y = section(EXTRACTOR, sample, ".pv0", bytes(range(256)) * 16, DATA_PROPS)
        assert not np.isnan(y).any()
        np.testing.assert_array_equal(y[~MODELED], x[~MODELED])
        try:
            y = append(EXTRACTOR, sample, b"\x00" * 4096)
        except RuntimeError:
            return
        assert not np.isnan(y).any()

    def test_table_kept_per_state(self, sample: bytes) -> None:
        needs_files()
        append, _ = engine_predictors(EXTRACTOR)
        blob = b"\x00" * 4096
        try:
            first = append(EXTRACTOR, sample, blob)
        except RuntimeError:
            pytest.skip("The engine flags this append.")
        np.testing.assert_array_equal(first, append(EXTRACTOR, sample, blob))
        grown = sample + blob
        y = append(EXTRACTOR, grown, blob)
        np.testing.assert_array_equal(y[MODELED], predict_append(EXTRACTOR, grown, blob)[MODELED])


################################################################################
# The search's steps
################################################################################


class TestSearchSteps:

    def test_section_step_ends_overlay(self, sample: bytes) -> None:
        needs_files()
        if not _overlay(sample):
            pytest.skip("No overlay.")
        # The search materializes a chosen add-section with our own byte-level edit, after the overlay, as the engine
        # declares it: the written file has no overlay left, so a later step cannot claim its removal again (run 105).
        donors = Donors([(f.name, f.read_bytes()) for f in FILES])
        names = bucket_names()
        ops = menu(donors, np.random.default_rng(0), 12, engine_predictors(EXTRACTOR), list(names)[:8], names)
        op = next(o for o in ops if o[0] == "sec")
        try:
            op[1](EXTRACTOR, sample)
        except RuntimeError:
            pytest.skip("No room for another section header.")
        written = op[2](sample)
        assert not _overlay(written)
        assert len(written) > len(sample)
