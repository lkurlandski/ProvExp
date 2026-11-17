"""
Tests for pipeline/5-attacks/adaptive/adaptive.py: the adaptive search's C1 predictors come from the engine (derivation step 9), with
the hand predictors of pipeline/1-audit/hand-table/hand_table.py as their oracle.

The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
from provexp.attacks.adaptive import DATA_PROPS  # noqa: E402
from provexp.attacks.adaptive import Donors  # noqa: E402
from provexp.attacks.adaptive import _tie_order  # noqa: E402
from provexp.attacks.adaptive import bucket_names  # noqa: E402
from provexp.attacks.adaptive import engine_predictors  # noqa: E402
from provexp.attacks.adaptive import menu  # noqa: E402
from provexp.attacks.adaptive import prepare_files  # noqa: E402
from provexp.featuresets.ember2024 import catalogue  # noqa: E402
from provexp.featuresets.ember2024.edits import add_section as write_section  # noqa: E402
from provexp.featuresets.ember2024.escapes import WRITES as ESCAPES  # noqa: E402
from provexp.featuresets.ember2024.hand import predict_add_section  # noqa: E402
from provexp.featuresets.ember2024.hand import predict_append  # noqa: E402

DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]

EXTRACTOR = fix_quirks(PEFeatureExtractor())
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
        pytest.skip(f"No test files found in {DATA.as_posix()} (see pipeline/setup/make_fixtures.py).")


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


################################################################################
# The beam search's tie-breaking
################################################################################


class TestTieOrder:

    def test_sorted_ascending(self) -> None:
        logits = [3.0, -1.0, 2.0, 0.5]
        order = _tie_order(logits, np.random.default_rng(0))
        assert [logits[i] for i in order] == sorted(logits)

    @pytest.mark.parametrize("eps", [0.0, 1e-12])
    def test_ties_permuted_by_seed(self, eps: float) -> None:
        logits = [1.0 + eps * i for i in range(8)] + [0.0]
        orders = {tuple(_tie_order(logits, np.random.default_rng(seed))) for seed in range(20)}
        assert all(o[0] == 8 for o in orders)  # the strict minimum always first
        assert len(orders) > 1  # the eight tied entries are not left in index order
        assert tuple(_tie_order(logits, np.random.default_rng(3))) == tuple(_tie_order(logits, np.random.default_rng(3)))


################################################################################
# Setup
################################################################################

class TestPrepareFiles:

    @staticmethod
    def _serial_reference(malware: list[tuple[str, bytes]], escape: str) -> list[tuple[str, bytes, bytes, bool, bool]]:
        # The setup as adaptive.py computed it before prepare_files (one file after another, in the main process).
        attacks = []
        for name, data in malware:
            start = data
            if escape != "none":
                try:
                    out = ESCAPES[escape](pefile.PE(data=data), len(data))
                except Exception:  # noqa: BLE001
                    out = None
                if out is None or catalogue.passes_precondition(EXTRACTOR, out):
                    continue
                start = out
            in_pop = catalogue.passes_precondition(EXTRACTOR, data, loose=True)
            start_in_pop = in_pop if start is data else catalogue.passes_precondition(EXTRACTOR, start, loose=True)
            attacks.append((name, start, data, in_pop, start_in_pop))
        return attacks

    @pytest.mark.parametrize("escape", ["none", "debug_entry"])
    def test_workers_match_serial_reference(self, escape: str) -> None:
        needs_files()
        malware = [(f.name, f.read_bytes()) for f in FILES[:8]]
        one = prepare_files(malware, "predicted", escape, 1)
        two = prepare_files(malware, "predicted", escape, 2)
        reference = self._serial_reference(malware, escape)
        assert [p[0] for p in one] == [p[0] for p in two] == [r[0] for r in reference]
        for a, b, r in zip(one, two, reference):
            assert a[1] == b[1] == r[1] and a[2] == b[2] == r[2]  # start, original
            assert a[5:] == b[5:] == r[3:]  # population checks
            v_orig = EXTRACTOR.feature_vector(r[2])  # type: ignore[no-untyped-call]
            v_start = EXTRACTOR.feature_vector(r[1])  # type: ignore[no-untyped-call]
            for x, y in ((a[3], v_orig), (b[3], v_orig), (a[4], v_start), (b[4], v_start)):
                assert np.array_equal(x, y, equal_nan=True)
        if escape != "none":
            assert len(reference) > 0  # the escape case must exercise escaped starts

    def test_rejects_unknown_escape(self) -> None:
        with pytest.raises(ValueError, match="Unknown escape"):
            prepare_files([], "predicted", "nope", 1)
