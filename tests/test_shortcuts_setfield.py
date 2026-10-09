"""
Tests for the 3-B set-field spot-check (scripts/shortcuts_setfield.py): the field-write mechanic on a real file and
the per-field summary. Scoring needs the model, so it is not tested here.
"""

from pathlib import Path
import sys

import polars as pl
import pytest

from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.trigger import apply_struct

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from shortcuts_setfield import summarize  # noqa: E402


DATA = Path(__file__).parent / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())


class TestFieldWrite:

    def test_sets_the_named_bytes_and_still_parses(self) -> None:
        if not FILES:
            pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")
        data = FILES[0].read_bytes()
        field = next(f for f in header_fields(parse(data, fast_load=True).pe) if f.key == "IMAGE_FILE_HEADER.TimeDateStamp")
        value = bytes.fromhex("195e422a")
        result = apply_struct(data, {"IMAGE_FILE_HEADER.TimeDateStamp": value})
        assert result.data[field.lo:field.hi] == value
        assert parse(result.data).status == "ok"
        assert len(result.data) == len(data)


class TestSummarize:

    def test_pivots_benign_and_random_side_by_side(self) -> None:
        results = pl.DataFrame({
            "index": [0, 0, 1, 1],
            "field": ["F", "F", "F", "F"],
            "source": ["benign", "random", "benign", "random"],
            "set_ok": [True, True, True, True],
            "drop": [1.0, 0.0, 3.0, 0.2],
            "flipped": [True, False, False, False],
        })
        s = summarize(results).row(0, named=True)
        assert s["median_drop_benign"] == pytest.approx(2.0)
        assert s["median_drop_random"] == pytest.approx(0.1)
        assert s["flip_rate_benign"] == pytest.approx(0.5)
        assert s["files_benign"] == 2

    def test_ignores_rows_where_the_write_failed(self) -> None:
        results = pl.DataFrame({
            "index": [0, 1],
            "field": ["F", "F"],
            "source": ["benign", "benign"],
            "set_ok": [True, False],
            "drop": [2.0, float("nan")],
            "flipped": [False, False],
        })
        s = summarize(results).row(0, named=True)
        assert s["median_drop_benign"] == pytest.approx(2.0)
        assert s["files_benign"] == 1
