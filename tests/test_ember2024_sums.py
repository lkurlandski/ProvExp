"""
Tests for the layer-2 re-encodings of EMBER v3 (featuresets/ember2024/sums.py).

Most of these tests need real executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import sys
import warnings

import numpy as np
import pefile
import pytest

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.featuresets.ember2024.sums import BodyByteEntropyHistogram
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.featuresets.ember2024.sums import body_layout
from provexp.featuresets.ember2024.sums import body_regions
from provexp.featuresets.ember2024.sums import signed_bucket
from provexp.items import evaluate

warnings.filterwarnings("ignore", category=SyntaxWarning)


ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())[:12]

SUMS = SumsFeatureExtractor()
BASE = merge_import_descriptors(PEFeatureExtractor())
NAMES = SUMS.feature_names
INDEX = {n: i for i, n in enumerate(NAMES)}
SUMS_COLUMNS = np.array([i for i, n in enumerate(NAMES) if n.split(":")[0] in SUMS_GROUPS])


def needs_files() -> None:
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


def _parse(data: bytes) -> Optional[pefile.PE]:
    try:
        return pefile.PE(data=data)
    except Exception:
        return None


@pytest.fixture(scope="module", params=FILES, ids=[f.name[:12] for f in FILES])
def sample(request: pytest.FixtureRequest) -> tuple[bytes, np.ndarray]:
    data = request.param.read_bytes()
    return data, SUMS.feature_vector(data)  # type: ignore[no-untyped-call]


################################################################################
# Extractor
################################################################################


class TestItems:

    def test_g1(self, sample: tuple[bytes, np.ndarray]) -> None:
        # The readouts over the item table reproduce the re-encoded groups bit for bit (G1 for sums).
        data, x = sample
        y = evaluate(SUMS.item_table(data), SUMS.readouts)
        np.testing.assert_array_equal(y[SUMS_COLUMNS], x[SUMS_COLUMNS])

    def test_body_items_in_regions(self, sample: tuple[bytes, np.ndarray]) -> None:
        data, _ = sample
        layout = body_layout(data, _parse(data))
        table = SUMS.item_table(data)
        for item in table.items:
            if item.kind.startswith("body_"):
                assert item.locating
                assert any(r.range[0] <= lo and hi <= r.range[1] for lo, hi in item.members for r in layout)


class TestSumsFeatureExtractor:

    def test_layout(self) -> None:
        assert NAMES[:BASE.dim] == BASE.feature_names
        assert SUMS.dim == len(NAMES) == BASE.dim + 256 + 256 + (2 + 96 + 77) + 400
        assert len(set(NAMES)) == len(NAMES)

    def test_prefix_is_merged_extractor(self, sample: tuple[bytes, np.ndarray]) -> None:
        needs_files()
        data, x = sample
        assert np.array_equal(x[:BASE.dim], BASE.feature_vector(data))  # type: ignore[no-untyped-call]

    @pytest.mark.parametrize("kind", ["size", "vsize", "entropy", "characteristics"])
    def test_split_buckets_sum_to_original(self, sample: tuple[bytes, np.ndarray], kind: str) -> None:
        needs_files()
        _, x = sample
        original = x[[INDEX[f"section:{kind}_hash_{i}"] for i in range(50)]]
        pos = x[[INDEX[f"section_split:{kind}_hash_{i}_pos"] for i in range(50)]]
        neg = x[[INDEX[f"section_split:{kind}_hash_{i}_neg"] for i in range(50)]]
        assert np.all(pos >= 0) and np.all(neg >= 0)
        np.testing.assert_allclose(pos - neg, original, rtol=1e-5, atol=1e-2)

    def test_body_histogram_counts_regions(self, sample: tuple[bytes, np.ndarray]) -> None:
        needs_files()
        data, x = sample
        regions = body_regions(data, _parse(data))
        total = x[[INDEX[f"body_histogram:byte_{b:02x}"] for b in range(256)]].sum()
        assert total == sum(hi - lo for lo, hi in regions)

    def test_body_strings_at_most_file_strings(self, sample: tuple[bytes, np.ndarray]) -> None:
        """Strings of the body regions are (pieces of) the file's strings, so there are no more printables."""
        needs_files()
        _, x = sample
        assert x[INDEX["body_strings:printables"]] <= x[INDEX["strings:printables"]]


################################################################################
# Body regions
################################################################################


class TestBodyRegions:

    def test_not_a_pe(self) -> None:
        assert body_regions(b"not a PE file", None) == []

    def test_within_file_and_out_of_headers(self, sample: tuple[bytes, np.ndarray]) -> None:
        needs_files()
        data, _ = sample
        pe = _parse(data)
        if pe is None:
            pytest.skip("Not a PE.")
        for lo, hi in body_regions(data, pe):
            assert pe.OPTIONAL_HEADER.SizeOfHeaders <= lo < hi <= len(data) or lo == len(data) == hi

    def test_section_after_overlay_keeps_body(self, sample: tuple[bytes, np.ndarray]) -> None:
        """
        A section added after the overlay turns it into a gap between sections (pefile finds no overlay), which stays
        body: no re-encoded body count falls (G7), except the regexes that end in a word boundary.
        """
        needs_files()
        from catalogue_checks import DATA_CHARACTERISTICS
        from catalogue_checks import add_section
        data, x = sample
        pe = _parse(data)
        if pe is None or pe.get_overlay_data_start_offset() is None:
            pytest.skip("Not a PE with an overlay.")
        added = add_section(data, b".pv0", bytes(range(256)) * 8, DATA_CHARACTERISTICS, before_overlay=False)
        if added is None:
            pytest.skip("No room for another section header.")
        x_new = SUMS.feature_vector(added[0])  # type: ignore[no-untyped-call]
        body = [j for j in SUMS_COLUMNS if NAMES[j].startswith("body_")]
        lowered = [NAMES[j] for j in body if x_new[j] < x[j]]
        boundary = {"body_strings:regex_" + k for k in ("ipv4_addr", "ipv6_addr", "mac_addr", "email_addr")}
        assert set(lowered) <= boundary


################################################################################
# Directions: appending only raises the sums
################################################################################


class TestAppendRaises:

    @pytest.mark.parametrize("seed", [0, 1])
    def test_append_never_lowers(self, sample: tuple[bytes, np.ndarray], seed: int) -> None:
        """
        Appending content (random bytes with printable runs, which can extend a string at the end of the file) never
        lowers a re-encoded feature, except the regexes that end in a word boundary (two-sided by design).
        """
        needs_files()
        data, x = sample
        if _parse(data) is None:
            pytest.skip("Not a PE.")
        rng = np.random.default_rng(seed)
        block = rng.integers(0, 256, 5000, dtype=np.uint8)
        block[:40] = rng.integers(0x41, 0x5b, 40, dtype=np.uint8)
        x_new = SUMS.feature_vector(data + block.tobytes())  # type: ignore[no-untyped-call]
        lowered = [NAMES[j] for j in SUMS_COLUMNS if x_new[j] < x[j]]
        boundary = {"body_strings:regex_" + k for k in ("ipv4_addr", "ipv6_addr", "mac_addr", "email_addr")}
        assert set(lowered) <= boundary

    def test_byteentropy_full_windows_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Extending a region keeps every existing window, so the counts only grow."""
        import provexp.featuresets.ember2024.sums as sums
        bh = BodyByteEntropyHistogram()
        data = np.random.default_rng(0).integers(0, 256, 9000, dtype=np.uint8).tobytes()
        counts = []
        for n in (1000, 3000, 6000, 9000):
            # One region spanning the first n bytes.
            monkeypatch.setattr(sums, "body_regions", lambda bytez, pe, n=n: [(0, n)])
            counts.append(np.asarray(bh.raw_features(data, None)))
        assert counts[0].sum() == 0
        for prev, nxt in zip(counts, counts[1:]):
            assert np.all(nxt >= prev)


################################################################################
# Hashing
################################################################################


class TestSignedBucket:

    @pytest.mark.parametrize("key", [".text", ".rsrc", "", "upx0", ".text:MEM_READ"])
    def test_matches_feature_hasher(self, key: str) -> None:
        from sklearn.feature_extraction import FeatureHasher
        x = FeatureHasher(50, input_type="pair").transform([[(key, 2.5)]]).toarray()[0]
        b, sign = signed_bucket(50, key)
        assert x[b] == 2.5 * sign and np.count_nonzero(x) == 1
