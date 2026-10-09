"""
Tests for the 3-B insertion test's pure helpers (scripts/shortcuts_insert.py): pattern selection, the random control,
and the per-pattern summary. The scoring and file I/O need the data and the model, so they are not tested here.
"""

from pathlib import Path
import sys

import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from shortcuts_insert import random_block  # noqa: E402
from shortcuts_insert import select_patterns  # noqa: E402
from shortcuts_insert import summarize  # noqa: E402


def patterns_frame() -> pl.DataFrame:
    return pl.DataFrame({
        "top_feature": ["strings:regex_dos_msg", "imports:library_hash_4", "strings:regex_thread", "header:x"],
        "files": [100, 50, 5, 200],
        "score": [9.0, 8.0, 7.0, 10.0],
        "content": [b"abcd", b"efgh", b"ij", b"kl"],
    }, schema_overrides={"content": pl.Binary})


class TestSelectPatterns:

    def test_filters_by_group_and_min_files_and_ranks_by_score(self) -> None:
        chosen = select_patterns(patterns_frame(), ["strings"], min_files=10, num_patterns=10)
        assert chosen["top_feature"].to_list() == ["strings:regex_dos_msg"]

    def test_several_groups(self) -> None:
        chosen = select_patterns(patterns_frame(), ["strings", "imports"], min_files=10, num_patterns=10)
        assert chosen["top_feature"].to_list() == ["strings:regex_dos_msg", "imports:library_hash_4"]

    def test_num_patterns_caps_the_result(self) -> None:
        chosen = select_patterns(patterns_frame(), ["strings", "imports", "header"], min_files=1, num_patterns=2)
        assert chosen["top_feature"].to_list() == ["header:x", "strings:regex_dos_msg"]


class TestRandomBlock:

    def test_length_and_determinism(self) -> None:
        a = random_block(2048, np.random.default_rng([0, 1, 2]))
        b = random_block(2048, np.random.default_rng([0, 1, 2]))
        assert len(a) == 2048 and a == b

    def test_rejects_a_nonpositive_length(self) -> None:
        with pytest.raises(ValueError):
            random_block(0, np.random.default_rng(0))


class TestSummarize:

    def test_pivots_pattern_and_random_side_by_side(self) -> None:
        results = pl.DataFrame({
            "index": [0, 0, 1, 1],
            "pattern": [0, 0, 0, 0],
            "source": ["pattern", "random", "pattern", "random"],
            "length": [4, 4, 4, 4],
            "parsed": [True, True, True, True],
            "drop": [2.0, 0.1, 4.0, 0.3],
            "flipped": [True, False, True, False],
        })
        blocks = pl.DataFrame({"pattern": [0], "length": [4], "top_feature": ["strings:x"], "content": [b"abcd"]}, schema_overrides={"content": pl.Binary})
        s = summarize(results, blocks).row(0, named=True)
        assert s["median_drop_pattern"] == pytest.approx(3.0)
        assert s["median_drop_random"] == pytest.approx(0.2)
        assert s["flip_rate_pattern"] == pytest.approx(1.0)
        assert s["flip_rate_random"] == pytest.approx(0.0)

    def test_ignores_rows_that_did_not_parse(self) -> None:
        results = pl.DataFrame({
            "index": [0, 1],
            "pattern": [0, 0],
            "source": ["pattern", "pattern"],
            "length": [4, 4],
            "parsed": [True, False],
            "drop": [2.0, float("nan")],
            "flipped": [True, False],
        })
        blocks = pl.DataFrame({"pattern": [0], "length": [4], "top_feature": ["strings:x"], "content": [b"abcd"]}, schema_overrides={"content": pl.Binary})
        s = summarize(results, blocks).row(0, named=True)
        assert s["median_drop_pattern"] == pytest.approx(2.0)
        assert s["files_pattern"] == 1
