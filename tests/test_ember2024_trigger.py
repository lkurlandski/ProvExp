"""
Tests for the planted triggers (featuresets/ember2024/trigger.py).

The struct-trigger tests need real executables in tests/data/ (see scripts/make_fixtures.py) and are skipped without them.
"""

from pathlib import Path
import warnings

import numpy as np
import pytest

from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import CONTENT_KINDS
from provexp.featuresets.ember2024.trigger import MARKER
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.featuresets.ember2024.trigger import apply_struct
from provexp.featuresets.ember2024.trigger import content_block
from provexp.featuresets.ember2024.trigger import struct_trigger


warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())
PE_FILES = [f for f in FILES if parse(f.read_bytes(), fast_load=True).status == "ok"]
EXTRACTOR = PEFeatureExtractor()
INDEX = {name: i for i, name in enumerate(EXTRACTOR.feature_names)}


@pytest.fixture(scope="module", params=PE_FILES, ids=[f.name[:16] for f in PE_FILES])
def data(request: pytest.FixtureRequest) -> bytes:
    return Path(request.param).read_bytes()


def feature_name(key: str) -> str:
    """The EMBER header feature that reads a header field, e.g., IMAGE_OPTIONAL_HEADER.MinorImageVersion."""
    structure, field = key.split(".", 1)
    return f"header:{structure.removeprefix('IMAGE_').lower()}_{field}"


################################################################################
# Content Trigger
################################################################################


class TestContentBlock:

    @pytest.mark.parametrize("kind", CONTENT_KINDS)
    def test_deterministic(self, kind: str) -> None:
        a = content_block(kind, 1024, seed=3)  # type: ignore[arg-type]
        assert len(a) == 1024 and a == content_block(kind, 1024, seed=3)  # type: ignore[arg-type]

    def test_kinds(self) -> None:
        assert content_block("constant", 64) == b"\xa5" * 64
        marker = content_block("marker", 1024)
        assert marker.count(MARKER) == 4 and marker[:len(MARKER)] == MARKER
        assert MARKER not in content_block("random", 1024)

    def test_invalid(self) -> None:
        with pytest.raises(ValueError):
            content_block("zeros", 1024)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            content_block("marker", 4)


class TestApplyContent:

    def test_append(self) -> None:
        data, block = b"x" * 100, b"T" * 10
        t = apply_content(data, block, max_length=200)
        assert t.data == data + block and t.ranges == [(100, 110)] and t.mode == "append"

    def test_overwrite_at_the_truncation_length(self) -> None:
        data, block = bytes(range(256)) * 2, b"T" * 10
        t = apply_content(data, block, max_length=300)
        assert len(t.data) == 300 and t.data[290:] == block and t.data[:290] == data[:290]
        assert t.ranges == [(290, 300)] and t.mode == "overwrite"

    def test_block_too_long(self) -> None:
        with pytest.raises(ValueError):
            apply_content(b"x", b"T" * 10, max_length=5)


def test_content_trigger_keeps_pe_files_intact(data: bytes) -> None:
    block = content_block("marker", 2048)
    appended = apply_content(data, block)
    assert parse(appended.data, fast_load=True).layout == parse(data, fast_load=True).layout
    # Force an overwrite of the file's last bytes; it must keep the layout or refuse.
    try:
        overwritten = apply_content(data, block, max_length=len(data))
    except ValueError:
        return
    assert len(overwritten.data) == len(data) and overwritten.data[-2048:] == block


################################################################################
# Struct Trigger
################################################################################


def test_struct_trigger_spec() -> None:
    fields = struct_trigger()
    assert len(fields) >= 1
    for key, value in fields.items():
        assert key.startswith(("IMAGE_FILE_HEADER.", "IMAGE_OPTIONAL_HEADER.")) and len(value) in (1, 2, 4)
        assert feature_name(key) in INDEX


def test_struct_trigger(data: bytes) -> None:
    fields = struct_trigger()
    if parse(data).status != "ok":
        # Some fixtures are truncated and do not fully parse: their header features are zero, so the trigger refuses.
        with pytest.raises(ValueError):
            apply_struct(data, fields)
        return
    t = apply_struct(data, fields)
    assert len(t.data) == len(data) and t.mode == "struct"
    assert parse(t.data).status == "ok"
    changed = np.flatnonzero(np.frombuffer(t.data, np.uint8) != np.frombuffer(data, np.uint8))
    inside = np.zeros(len(data), dtype=bool)
    for lo, hi in t.ranges:
        inside[lo:hi] = True
    assert np.all(inside[changed])
    # The extractor reads the trigger's values, and their features' provenance is exactly the trigger's bytes.
    x, prov = EXTRACTOR.feature_vector_with_provenance(t.data)
    P = prov.contributions.pieces()
    pe = parse(t.data, fast_load=True).pe
    assert pe is not None
    located = {f.key: (f.lo, f.hi) for f in header_fields(pe)}
    assert sorted(located[key] for key in fields) == t.ranges
    for key, value in fields.items():
        lo, hi = located[key]
        j = INDEX[feature_name(key)]
        assert x[j] == int.from_bytes(value, "little")
        mask = P.col == j
        assert list(zip(P.lo[mask].tolist(), P.hi[mask].tolist())) == [(lo, hi)]


def test_struct_trigger_rejects_non_pe() -> None:
    with pytest.raises(ValueError):
        apply_struct(b"not a PE file" * 10, struct_trigger())
