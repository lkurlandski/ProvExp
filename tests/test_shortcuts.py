"""
Tests for 3-B's building blocks (scripts/shortcuts.py): the top elements, reading rows of P from the boxes, spans that
share a top feature, and grouping spans into patterns.

Most need no data; the check on real files skips when tests/data is absent.
"""

from pathlib import Path
import sys

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import polars as pl
import pytest

from provexp.boxmatrix import BoxMatrix
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance

from tests.strategies import full_boxmatrices

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from shortcuts import feature_spans  # noqa: E402
from shortcuts import patterns  # noqa: E402
from shortcuts import provenance_rows  # noqa: E402
from shortcuts import top_elements  # noqa: E402


DATA = Path(__file__).parent / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())


################################################################################
# Top elements
################################################################################


class TestTopElements:

    def test_takes_the_most_credited_in_the_direction_in_order_of_position(self) -> None:
        scores = np.array([-3.0, 1.0, -1.0, -2.0, 0.5])
        tiebreak = np.arange(5)
        assert top_elements(scores, -1.0, 2, tiebreak).tolist() == [0, 3]
        assert top_elements(scores, 1.0, 2, tiebreak).tolist() == [1, 4]

    def test_never_takes_credit_of_the_wrong_sign(self) -> None:
        scores = np.array([-1.0, 2.0, 3.0])
        assert top_elements(scores, -1.0, 3, np.arange(3)).tolist() == [0]

    def test_ties_follow_the_permutation(self) -> None:
        scores = np.array([-1.0, -1.0, -1.0, -1.0])
        assert top_elements(scores, -1.0, 2, np.array([3, 1, 0, 2])).tolist() == [1, 3]

    @pytest.mark.parametrize("top_k", [0, -1])
    def test_rejects_a_nonpositive_top_k(self, top_k: int) -> None:
        with pytest.raises(ValueError):
            top_elements(np.array([-1.0]), -1.0, top_k, np.arange(1))


################################################################################
# Rows of P
################################################################################


class TestProvenanceRows:

    @settings(max_examples=200, deadline=None)
    @given(full_boxmatrices(), st.data())
    def test_matches_the_dense_matrix(self, C: BoxMatrix, data: st.DataObject) -> None:
        prov = Provenance(C)
        m = prov.num_elements
        rows = np.array(sorted(data.draw(st.sets(st.integers(0, m - 1), min_size=1, max_size=m))), dtype=np.int64)
        np.testing.assert_allclose(provenance_rows(prov, rows, chunk=3), prov.to_dense()[rows], atol=1e-12)

    def test_handles_keyed_boxes(self) -> None:
        C = BoxMatrix((4, 3))
        k = C.add_key(np.array([0, 1, 1, 2], dtype=np.uint8))
        C.add_keyed_boxes(0, 4, 0, k, 1.0)
        prov = Provenance(C)
        np.testing.assert_allclose(provenance_rows(prov, np.array([1, 3])), prov.to_dense()[[1, 3]])

    def test_rejects_out_of_range_rows(self) -> None:
        C = BoxMatrix((4, 1))
        C.add_boxes(0, 4, 0, 1, 1.0)
        with pytest.raises(ValueError):
            provenance_rows(Provenance(C), np.array([4]))


################################################################################
# Spans and patterns
################################################################################


class TestFeatureSpans:

    def test_splits_at_gaps_and_where_the_top_feature_changes(self) -> None:
        elements = np.array([2, 3, 4, 5, 9, 10])
        top = np.array([7, 7, 8, 8, 8, 8])
        assert feature_spans(elements, top) == [(2, 2, 7), (4, 2, 8), (9, 2, 8)]

    def test_empty(self) -> None:
        assert feature_spans(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)) == []


class TestPatterns:

    def test_groups_by_feature_and_content_and_counts_files_once(self) -> None:
        spans = pl.DataFrame({
            "index": [0, 0, 1, 2, 2],
            "label": [0, 0, 1, 0, 0],
            "length": [4, 4, 4, 4, 2],
            "content": [b"abcd", b"abcd", b"abcd", b"abcd", b"ab"],
            "credit": [1.0, 0.5, 2.0, 1.0, 9.0],
            "top_feature": ["f", "f", "f", "g", "f"],
        }, schema_overrides={"content": pl.Binary})
        t = patterns(spans, min_length=4)
        f = t.filter(pl.col("top_feature") == "f").row(0, named=True)
        assert (f["files"], f["benign_files"], f["malware_files"]) == (2, 1, 1)
        assert f["mean_credit"] == pytest.approx(1.75)
        assert f["score"] == pytest.approx(3.5)
        assert t.height == 2

    def test_rejects_a_nonpositive_min_length(self) -> None:
        with pytest.raises(ValueError):
            patterns(pl.DataFrame(), min_length=0)


################################################################################
# Real files
################################################################################


class TestRealFiles:

    @pytest.mark.parametrize("which", range(3))
    def test_rows_add_up_to_the_pullback(self, which: int) -> None:
        if len(FILES) <= which:
            pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")
        bytez = FILES[which].read_bytes()[:200_000]
        _, prov = PEFeatureExtractor().feature_vector_with_provenance(bytez)
        a = np.random.default_rng(which).normal(size=prov.num_features)
        b = prov.pullback(a)[:prov.num_elements]
        rows = np.sort(np.random.default_rng(which).choice(prov.num_elements, size=min(300, prov.num_elements), replace=False))
        per_feature = provenance_rows(prov, rows.astype(np.int64)) * a[None, :]
        np.testing.assert_allclose(per_feature.sum(axis=1), b[rows], rtol=1e-9, atol=1e-12)
