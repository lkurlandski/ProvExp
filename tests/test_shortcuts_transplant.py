"""
Tests for 3-B's transplant test, training sample, reliance, and tables (scripts/shortcuts_transplant.py,
shortcuts_train_sample.py, shortcuts_reliance.py, shortcuts_tables.py): candidate selection, placement by provenance,
the summary's confirmation rule, 4-gram counting and scoring, occurrences, and the neutralize rule. Scoring needs the
model, so it is not tested here; the placement check on real files skips when tests/data is absent.
"""

from pathlib import Path
import sys

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st
import numpy as np
import polars as pl
import pytest
from scipy import stats

from provexp.boxmatrix import BoxMatrix
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance

from tests.strategies import full_boxmatrices

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from shortcuts_forge import forge_set  # noqa: E402
from shortcuts_forge import operating_threshold  # noqa: E402
from shortcuts_forge import write_all  # noqa: E402
from shortcuts_reliance import best_occurrence  # noqa: E402
from shortcuts_reliance import occurrences  # noqa: E402
from shortcuts_tables import label  # noqa: E402
from shortcuts_tables import neutralize  # noqa: E402
from shortcuts_train_sample import chi2  # noqa: E402
from shortcuts_train_sample import grams  # noqa: E402
from shortcuts_train_sample import information_gain  # noqa: E402
from shortcuts_train_sample import rank_grams  # noqa: E402
from shortcuts_transplant import choose_run  # noqa: E402
from shortcuts_transplant import family  # noqa: E402
from shortcuts_transplant import feature_runs  # noqa: E402
from shortcuts_transplant import overwrite  # noqa: E402
from shortcuts_transplant import select_candidates  # noqa: E402
from shortcuts_transplant import summarize  # noqa: E402


DATA = Path(__file__).parent / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())


################################################################################
# Candidates
################################################################################


class TestSelectCandidates:

    def test_takes_the_top_scores_among_recurring_patterns(self) -> None:
        patterns = pl.DataFrame({
            "top_feature": ["a", "b", "c", "d"], "content": [b"aaaa", b"bb", b"cccc", b"dddd"],
            "files": [5, 20, 30, 40], "score": [100.0, 3.0, 2.0, 1.0],
        }, schema_overrides={"content": pl.Binary})
        chosen = select_candidates(patterns, 2, min_files=10)
        assert chosen["top_feature"].to_list() == ["b", "c"]
        assert chosen["candidate"].to_list() == [0, 1]
        assert chosen["length"].to_list() == [2, 4]
        assert set(chosen["kind"].to_list()) == {"pullback"}

    def test_rejects_a_nonpositive_number(self) -> None:
        with pytest.raises(ValueError):
            select_candidates(pl.DataFrame(), 0, 10)


class TestFamily:

    @pytest.mark.parametrize("name, expected", [
        ("section:size_hash_43", "section:size_hash_*"),
        ("imports:library_hash_4", "imports:library_hash_*"),
        ("header:optional_header_SizeOfCode", "header:optional_header_SizeOfCode"),
    ])
    def test_strips_the_bucket(self, name: str, expected: str) -> None:
        assert family(name) == expected


################################################################################
# Placement by provenance
################################################################################


class TestFeatureRuns:

    @settings(max_examples=200, deadline=None)
    @given(full_boxmatrices())
    def test_runs_cover_exactly_the_support_of_each_column(self, C: BoxMatrix) -> None:
        prov = Provenance(C)
        dense = prov.to_dense()[:prov.num_elements]
        features = np.arange(prov.num_features, dtype=np.int64)
        runs = feature_runs(prov, features)
        for j in features.tolist():
            covered = np.zeros(prov.num_elements, dtype=np.bool_)
            for start, length in runs[j]:
                assert length > 0
                covered[start:start + length] = True
            np.testing.assert_array_equal(covered, np.abs(dense[:, j]) > 1e-12 * max(1.0, np.abs(dense[:, j]).max()))
            # Runs are maximal: no two touch.
            ends = [s + n for s, n in runs[j]]
            assert all(e < s for e, (s, _) in zip(ends, runs[j][1:]))

    def test_separates_disjoint_pieces(self) -> None:
        C = BoxMatrix((10, 2))
        C.add_boxes(1, 3, 0, 1, 1.0)
        C.add_boxes(3, 5, 0, 1, 2.0)
        C.add_boxes(7, 9, 0, 1, 1.0)
        C.add_boxes(0, 10, 1, 2, 1.0)
        runs = feature_runs(Provenance(C), np.array([0, 1]))
        assert runs[0] == [(1, 4), (7, 2)]
        assert runs[1] == [(0, 10)]

    def test_empty_selection(self) -> None:
        C = BoxMatrix((4, 1))
        C.add_boxes(0, 4, 0, 1, 1.0)
        assert feature_runs(Provenance(C), np.zeros(0, dtype=np.int64)) == {}


class TestChooseRun:

    def test_prefers_the_feature_and_skips_runs_that_hold_the_content(self) -> None:
        data = b"abcdXXXXabcd"
        runs = {0: [(0, 4), (4, 4)], 1: [(8, 4)]}
        start, mode = choose_run(data, runs, 0, [0, 1], b"abcd", np.random.default_rng(0))
        assert (start, mode) == (4, "feature")

    def test_falls_back_to_the_family(self) -> None:
        data = b"XXXXYYYY"
        runs = {0: [(0, 2)], 1: [(4, 4)]}
        assert choose_run(data, runs, 0, [0, 1], b"abcd", np.random.default_rng(0)) == (4, "family")

    def test_reports_content_already_present(self) -> None:
        data = b"abcd"
        runs = {0: [(0, 4)]}
        assert choose_run(data, runs, 0, [0], b"abcd", np.random.default_rng(0)) == (None, "present")

    def test_reports_no_run_of_the_right_length(self) -> None:
        runs = {0: [(0, 3)], 1: [(4, 5)]}
        assert choose_run(b"x" * 9, runs, 0, [0, 1], b"abcd", np.random.default_rng(0)) == (None, "none")

    def test_draws_among_runs_with_the_seed(self) -> None:
        data = b"\x00" * 40
        runs = {0: [(i, 4) for i in range(0, 40, 4)]}
        picks = {choose_run(data, runs, 0, [0], b"abcd", np.random.default_rng(s))[0] for s in range(50)}
        assert len(picks) > 1
        assert choose_run(data, runs, 0, [0], b"abcd", np.random.default_rng(7)) == choose_run(data, runs, 0, [0], b"abcd", np.random.default_rng(7))


class TestOverwrite:

    def test_writes_in_place(self) -> None:
        assert overwrite(b"abcdef", 2, b"XY") == b"abXYef"

    @pytest.mark.parametrize("start", [-1, 5])
    def test_rejects_out_of_range(self, start: int) -> None:
        with pytest.raises(ValueError):
            overwrite(b"abcdef", start, b"XY")


class TestRealFiles:

    @pytest.mark.parametrize("name", ["header:file_header_TimeDateStamp", "datadirectories:debug_size"])
    def test_a_header_feature_runs_over_its_field(self, name: str) -> None:
        if not FILES:
            pytest.skip(f"No test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")
        extractor = PEFeatureExtractor()
        data = FILES[0].read_bytes()
        x, prov = extractor.feature_vector_with_provenance(data)
        j = extractor.feature_names.index(name)
        runs = feature_runs(prov, np.array([j]))[j]
        if not runs:
            pytest.skip(f"{FILES[0].name} has no bytes feeding {name}.")
        assert len(runs) == 1 and runs[0][1] == 4
        start = runs[0][0]
        assert np.float32(int.from_bytes(data[start:start + 4], "little")) == np.float32(x[j])


################################################################################
# Summary
################################################################################


def results(drops: list[tuple[float, float]], kind: str = "pullback") -> pl.DataFrame:
    """Result rows for one candidate: a (content, random) drop per file, all parsed."""
    rows = []
    for i, (c, r) in enumerate(drops):
        for source, d in (("content", c), ("random", r)):
            rows.append({"index": i, "kind": kind, "candidate": 0, "source": source, "mode": "feature",
                         "parsed": True, "drop": d, "flipped": False})
    return pl.DataFrame(rows)


class TestSummarize:

    def test_confirms_a_clear_effect_toward_benign(self) -> None:
        s = summarize(results([(1.0 + 0.01 * i, 0.0) for i in range(30)]), 20, 20, 0.1).row(0, named=True)
        assert s["applicable"] == 30 and s["confirmed"]
        assert s["median_effect"] == pytest.approx(1.145)

    def test_beating_an_anomalous_control_is_not_enough(self) -> None:
        # The content moves the file toward malware, only less than the random value does.
        s = summarize(results([(-0.2, -2.0 - 0.01 * i) for i in range(30)]), 20, 20, 0.1).row(0, named=True)
        assert s["median_effect"] > 1.0 and not s["confirmed"]

    def test_needs_enough_files(self) -> None:
        s = summarize(results([(1.0, 0.0)] * 10), 1, 20, 0.1).row(0, named=True)
        assert not s["confirmed"]

    def test_counts_placement_modes_and_ignores_unparsed_rows(self) -> None:
        r = results([(1.0, 0.0)] * 3)
        extra = pl.DataFrame([{"index": 9, "kind": "pullback", "candidate": 0, "source": "content", "mode": "present",
                               "parsed": False, "drop": float("nan"), "flipped": False}])
        s = summarize(pl.concat([r, extra]), 1, 1, 0.1).row(0, named=True)
        assert (s["placed_feature"], s["already_present"], s["applicable"]) == (3, 1, 3)

    def test_rejects_no_tests(self) -> None:
        with pytest.raises(ValueError):
            summarize(results([(1.0, 0.0)]), 0, 1, 0.1)


################################################################################
# Training sample
################################################################################


class TestGrams:

    def test_distinct_little_endian_4_grams(self) -> None:
        g = grams(b"abcdeabcd")
        expected = {int.from_bytes(b"abcdeabcd"[i:i + 4], "little") for i in range(6)}
        assert set(g.tolist()) == expected and g.size == len(expected)

    def test_short_input(self) -> None:
        assert grams(b"abc").size == 0


class TestScores:

    @pytest.mark.parametrize("b, m", [(30, 5), (5, 30), (10, 10), (0, 7)])
    def test_chi2_matches_scipy(self, b: int, m: int) -> None:
        nb, nm = 50, 40
        table = np.array([[b, nb - b], [m, nm - m]])
        expected = stats.chi2_contingency(table, correction=False).statistic if b + m > 0 else 0.0
        assert chi2(np.array([b]), np.array([m]), nb, nm)[0] == pytest.approx(expected)

    def test_information_gain_bounds(self) -> None:
        nb = nm = 10
        assert information_gain(np.array([10]), np.array([0]), nb, nm)[0] == pytest.approx(1.0)
        assert information_gain(np.array([5]), np.array([5]), nb, nm)[0] == pytest.approx(0.0, abs=1e-12)

    def test_rank_grams_splits_directions_and_filters_rare(self) -> None:
        benign = np.zeros(16, dtype=np.uint16)
        malware = np.zeros(16, dtype=np.uint16)
        benign[3], malware[3] = 9, 1     # benign-skewed
        benign[5], malware[5] = 1, 9     # malware-skewed
        benign[7], malware[7] = 1, 0     # too rare
        table = rank_grams(benign, malware, 10, 10, num=5, min_df=5, chunk=4)
        assert table.filter(pl.col("direction") == "benign")["gram"].to_list() == [3]
        assert table.filter(pl.col("direction") == "malware")["gram"].to_list() == [5]
        assert table.filter(pl.col("gram") == 3)["content"][0] == (3).to_bytes(4, "little")


################################################################################
# Reliance
################################################################################


class TestOccurrences:

    def test_finds_overlapping_occurrences(self) -> None:
        d = np.frombuffer(b"aaaXaa", dtype=np.uint8)
        assert occurrences(d, b"aa").tolist() == [0, 1, 4]

    def test_content_longer_than_data(self) -> None:
        assert occurrences(np.frombuffer(b"ab", dtype=np.uint8), b"abc").size == 0

    def test_best_occurrence(self) -> None:
        credit = np.array([1.0, -1.0, 2.0, 2.0, 0.0])
        assert best_occurrence(credit, np.array([0, 2]), 2) == pytest.approx(4.0)
        assert np.isnan(best_occurrence(credit, np.zeros(0, dtype=np.int64), 2))


################################################################################
# Tables
################################################################################


class TestNeutralize:

    def test_takes_carried_features_of_confirmed_artifacts_only(self) -> None:
        summary = pl.DataFrame({
            "kind": ["pullback"] * 3, "candidate": [0, 1, 2], "confirmed": [True, True, False],
            "top_feature": ["datadirectories:security_size", "datadirectories:resource_virtual_address", "datadirectories:debug_size"],
            "content": [bytes.fromhex("38280000"), bytes.fromhex("00000000"), bytes.fromhex("54000000")],
        })
        assert label(summary["top_feature"][0], summary["content"][0])[0] == "artifact"
        assert label(summary["top_feature"][1], summary["content"][1])[0] == "structural"
        reliance = pl.DataFrame({"kind": ["pullback"] * 3, "candidate": [0, 1, 2], "at_feature_files": [10, 10, 10]})
        carried = pl.DataFrame({
            "candidate": [0, 0, 1, 2], "files": [10, 3, 10, 10],
            "name": ["datadirectories:security_size", "rare", "datadirectories:resource_virtual_address", "datadirectories:debug_size"],
        })
        assert neutralize(summary, carried, reliance) == ["datadirectories:security_size"]


################################################################################
# Forge
################################################################################


class TestForge:

    def test_forge_set_one_confirmed_artifact_per_feature(self) -> None:
        summary = pl.DataFrame({
            "kind": ["pullback"] * 5 + ["mined"], "candidate": [15, 13, 19, 2, 4, 0],
            "confirmed": [True, True, True, True, False, True],
            "top_feature": ["datadirectories:security_size", "datadirectories:security_size",
                            "datadirectories:resource_virtual_address", "datadirectories:debug_size",
                            "datadirectories:debug_size", "x"],
            "content": [bytes.fromhex(h) for h in ("20280000", "38280000", "00000000", "54000000", "70000000", "00")],
        })
        out = forge_set(summary)
        assert out["candidate"].to_list() == [2, 13]
        assert out["content"].to_list() == [bytes.fromhex("54000000"), bytes.fromhex("38280000")]

    @pytest.mark.parametrize("fpr", [0.01, 0.1, 0.5])
    def test_threshold_keeps_fpr(self, fpr: float) -> None:
        scores = np.random.default_rng(0).normal(size=10_001)
        t = operating_threshold(scores, fpr)
        assert np.mean(scores > t) <= fpr
        assert t in scores

    def test_threshold_rejects_bad_fpr(self) -> None:
        with pytest.raises(ValueError):
            operating_threshold(np.zeros(3), 1.0)

    def test_write_all(self) -> None:
        data = bytes(10)
        assert write_all(data, [(6, b"\x02\x02"), (1, b"\x01")]) == b"\x00\x01\x00\x00\x00\x00\x02\x02\x00\x00"
        assert write_all(data, [(1, b"\x01\x01"), (2, b"\x02")]) is None
        assert write_all(data, [(1, b"\x01"), (2, b"\x02")]) == b"\x00\x01\x02" + bytes(7)
