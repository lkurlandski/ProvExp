"""
Unit tests for the pure helpers of the shared-field edits (scripts/cm_shared_edit.py). The full pipeline needs the
models, the GPU, and the malware files, so it is exercised by the run script, not here.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cm_shared_edit import ARMS  # noqa: E402
from cm_shared_edit import choose_fields  # noqa: E402
from cm_shared_edit import field_evidence  # noqa: E402
from cm_shared_edit import paired  # noqa: E402
from cm_shared_edit import predictors  # noqa: E402
from cm_shared_edit import summarize  # noqa: E402


################################################################################
# Fields
################################################################################


class TestFieldEvidence:

    def test_sums_over_every_run(self) -> None:
        """A field's evidence is the sum over all of its runs; a field without runs has none."""
        e = np.arange(10, dtype=np.float64)
        runs = {3: [(0, 2), (5, 3)], 7: [(9, 1)]}
        out = field_evidence(e, runs, [3, 7, 8])
        assert out.tolist() == [0 + 1 + 5 + 6 + 7, 9, 0]

    def test_overlapping_fields_both_count_the_shared_bytes(self) -> None:
        """Two fields that read the same bytes each receive those bytes' evidence."""
        e = np.ones(4)
        out = field_evidence(e, {0: [(0, 4)], 1: [(2, 2)]}, [0, 1])
        assert out.tolist() == [4.0, 2.0]


class TestChooseFields:

    def test_top_n_by_score(self) -> None:
        scores = np.array([0.1, 3.0, -1.0, 2.0])
        assert choose_fields(scores, 2, np.arange(4, dtype=np.int64)) == [1, 3]

    @pytest.mark.parametrize("seed", [0, 1, 2])
    def test_ties_follow_the_permutation(self, seed: int) -> None:
        """Equal scores are ordered by the tie-break permutation, never by position."""
        perm = np.random.default_rng(seed).permutation(5).astype(np.int64)
        chosen = choose_fields(np.ones(5), 5, perm)
        assert chosen == perm.tolist()

    def test_fewer_fields_than_n(self) -> None:
        assert sorted(choose_fields(np.array([1.0, 2.0]), 5, np.arange(2, dtype=np.int64))) == [0, 1]

    def test_mismatched_tiebreak_raises(self) -> None:
        with pytest.raises(ValueError):
            choose_fields(np.ones(3), 1, np.arange(4, dtype=np.int64))


################################################################################
# Summary
################################################################################


def _table() -> pl.DataFrame:
    """Two files, every arm; the shared arm makes both detectors drop on both files, the others on none."""
    rows = []
    for index in (0, 1):
        for arm in ARMS:
            hit = arm == "shared_pullback"
            rows.append({"index": index, "status": "ok", "arm": arm, "parsed": True, "num_fields": 3,
                         "malconv_drop": 2.0 if hit else 0.5, "gbdt_drop": 1.5 if hit else 0.2,
                         "malconv_edited": 0.0, "gbdt_edited": 5.0, "bytes": 8,
                         "gbdt_evidence": 1.0 if hit else 0.1, "gbdt_window_evidence": 0.5})
    return pl.DataFrame(rows)


class TestSummary:

    def test_both_drop_share(self) -> None:
        s = summarize(_table(), gbdt_threshold=0.0, malconv_threshold=1.0, delta=1.0)
        assert s["arm"].to_list() == list(ARMS)
        both = dict(zip(s["arm"].to_list(), s["both_drop"].to_list()))
        assert both["shared_pullback"] == 1.0 and both["random"] == 0.0

    def test_paired_counts_discordant_files(self) -> None:
        p = paired(_table(), delta=1.0)
        row = p.filter(pl.col("against") == "random").row(0, named=True)
        assert row["wins"] == 2 and row["both_only_reference"] == 2 and row["both_only_other"] == 0

    def test_predictors_rank_the_drop(self) -> None:
        """A predictor that orders the files like the GBDT's drop has rho 1 and AUC 1."""
        rows = [{"index": i, "status": "ok", "arm": "malconv_only", "parsed": True, "gbdt_drop": float(i),
                 "gbdt_evidence": float(i), "gbdt_window_evidence": float(-i), "bytes": 4} for i in range(10)]
        p = predictors(pl.DataFrame(rows), delta=4.5, num_boot=50)
        row = p.row(0, named=True)
        assert row["rho_pullback"] == pytest.approx(1.0) and row["auc_pullback"] == pytest.approx(1.0)
        assert row["rho_windows"] == pytest.approx(-1.0) and row["positives"] == 5
