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
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.items import evaluate
from provexp.items import project

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
