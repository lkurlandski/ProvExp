"""
Tests for the faithfulness runner's parallelism (scripts/faithfulness.py).

The runner splits one file's work over chunks of windows evaluated in separate processes (docs/experiments/pb1.md, "Cost and
progress reporting"). These tests pin the two properties that make that safe:

    1. chunking an occlusion run gives exactly the same per-window scores as running it whole, and
    2. a mask's features do not depend on when or where it is evaluated, because its random fill is seeded by the
       mask itself.

A third group pins what the runner saves for PF1: the per-window scores it ranks with, and the fully ablated file's
features (docs/experiments/pf1.md).

They use a stub model, so they need neither a trained model nor the binaries' database, only a real PE file from
tests/data/ (see scripts/make_fixtures.py).
"""

from pathlib import Path
import sys
import warnings

import numpy as np
import pytest

from provexp.ablation import window_edges
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protect

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from faithfulness import _STATE  # noqa: E402
from faithfulness import Scorer  # noqa: E402
from faithfulness import chunk_windows  # noqa: E402
from faithfulness import extractions_per_file  # noqa: E402
from faithfulness import load_window_scores  # noqa: E402
from faithfulness import occlude  # noqa: E402
from faithfulness import occlude_range  # noqa: E402
from faithfulness import predict_seconds  # noqa: E402
from faithfulness import process_file  # noqa: E402
from faithfulness import save_window_scores  # noqa: E402
from provexp.featuresets.ember2024.features import PEFeatureExtractor  # noqa: E402


warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
PE_FILES = sorted(f for f in DATA.glob("*/*") if f.is_file() and parse(f.read_bytes(), fast_load=True).status == "ok")
NUM_WINDOWS = 24


@pytest.fixture(scope="module")
def stubbed() -> PEFeatureExtractor:
    """The real extractor with a stub model, so that these tests need no trained model."""
    extractor = PEFeatureExtractor()
    _STATE["extractor"] = extractor
    # A deterministic, non-trivial function of the features, standing in for a classifier's log-odds.
    _STATE["models"] = {"stub": lambda X: np.asarray(np.log1p(np.abs(X[:, :64])).sum(axis=1), dtype=np.float64)}
    return extractor


@pytest.fixture(scope="module")
def data() -> bytes:
    if not PE_FILES:
        pytest.skip(f"No PE test files in {DATA.as_posix()} (see scripts/make_fixtures.py).")
    # The smallest fixture, to keep the test quick: it still has hundreds of windows to chunk.
    return min(PE_FILES, key=lambda f: f.stat().st_size).read_bytes()


def scorer_for(data: bytes, fill: str, seed: int = 7) -> Scorer:
    return Scorer(data, protect(data, header="typical"), fill, seed)  # type: ignore[arg-type]


################################################################################
# Chunking
################################################################################


class TestChunkWindows:

    @pytest.mark.parametrize("num_windows", [1, 2, 7, 64, 256, 4096])
    @pytest.mark.parametrize("size", [1_000, 200_000, 4_000_000])
    def test_tiles_the_windows_exactly_once(self, num_windows: int, size: int) -> None:
        chunks = chunk_windows(num_windows, size)
        assert chunks[0][0] == 0 and chunks[-1][1] == num_windows
        assert all(lo < hi for lo, hi in chunks)
        assert [hi for _, hi in chunks[:-1]] == [lo for lo, _ in chunks[1:]]

    def test_a_large_file_is_split_and_a_small_one_is_not(self) -> None:
        assert len(chunk_windows(4096, 4_000_000)) > 1
        assert len(chunk_windows(4096, 1_000)) == 1

    def test_chunks_are_bounded_by_the_target(self) -> None:
        """No chunk should be much more than the target, which is what keeps one task from dominating a run."""
        chunks = chunk_windows(4096, 4_000_000, target_seconds=60.0)
        seconds_each = predict_seconds(np.asarray([4_000_000], dtype=np.int64), 1)[0]
        assert max(hi - lo for lo, hi in chunks) * seconds_each <= 120.0


def test_extractions_per_file_counts_every_phase() -> None:
    budgets = (0.1, 0.5)
    # The original and the fully ablated file, the windows of each occlusion run, the coalitions, and the curves.
    assert extractions_per_file(256, (), 0, budgets, num_methods=3) == 2 + 256 + 2 * 3
    assert extractions_per_file(256, (64,), 0, budgets, num_methods=3) == 2 + 256 + 64 + 2 * 3
    assert extractions_per_file(256, (64, 256), 100, budgets, num_methods=3) == 2 + 256 + 64 + 100 + 2 * 3


################################################################################
# Chunked Occlusion Equals Whole Occlusion
################################################################################


@pytest.mark.parametrize("fill", ["zeros", "random"])
def test_chunked_occlusion_matches_the_whole_run(stubbed: PEFeatureExtractor, data: bytes, fill: str) -> None:
    """The central property of the restructuring: chunk boundaries do not change any window's score."""
    whole = scorer_for(data, fill)
    _, window, _, expected, invalid_whole = occlude(whole, len(data), NUM_WINDOWS)
    K = int(window.max()) + 1

    # The same windows, evaluated in chunks by *separate* scorers, as separate processes would.
    f0 = scorer_for(data, fill).scores(np.zeros(len(data), dtype=np.bool_))[0]
    scores = {name: np.zeros(K) for name in expected}
    invalid_chunked = 0
    tiling: list[tuple[int, int]] = [(0, 1), (1, 5), (5, K - 1), (K - 1, K)]
    for lo, hi in tiling:
        chunk, bad = occlude_range(scorer_for(data, fill), window, f0, lo, hi)
        invalid_chunked += bad
        for name, values in chunk.items():
            scores[name][lo:hi] = values

    assert invalid_chunked == invalid_whole
    for name in expected:
        assert np.array_equal(scores[name], expected[name]), f"{name} differs between the chunked and whole runs"


def test_chunk_boundaries_do_not_matter(stubbed: PEFeatureExtractor, data: bytes) -> None:
    """Any tiling of the windows gives the same scores, so the chunk size is free to follow the cost model."""
    window = np.repeat(np.arange(NUM_WINDOWS), np.diff(window_edges(len(data), NUM_WINDOWS)))
    K = int(window.max()) + 1
    f0 = scorer_for(data, "random").scores(np.zeros(len(data), dtype=np.bool_))[0]

    def run(tiling: list[tuple[int, int]]) -> np.ndarray:
        out = np.zeros(K)
        for lo, hi in tiling:
            chunk, _ = occlude_range(scorer_for(data, "random"), window, f0, lo, hi)
            out[lo:hi] = chunk["stub"]
        return out

    one_chunk = run([(0, K)])
    assert np.array_equal(one_chunk, run([(i, min(i + 1, K)) for i in range(K)]))
    assert np.array_equal(one_chunk, run([(0, 3), (3, K)]))


################################################################################
# The Scorer Is Order-Independent
################################################################################


@pytest.mark.parametrize("fill", ["zeros", "random"])
def test_the_same_mask_gives_the_same_features_in_any_order(stubbed: PEFeatureExtractor, data: bytes, fill: str) -> None:
    """
    A mask's random fill is seeded by the mask, so evaluating masks in a different order, or in a different process,
    cannot change the result. This is what lets the work of one file be split across workers.
    """
    rng = np.random.default_rng(0)
    masks = [rng.random(len(data)) < p for p in (0.01, 0.2, 0.5)]
    forward = [scorer_for(data, fill).features(m)[0] for m in masks]
    backward = [scorer_for(data, fill).features(m)[0] for m in reversed(masks)][::-1]
    shared = scorer_for(data, fill)
    together = [shared.features(m)[0] for m in masks]
    for a, b, c in zip(forward, backward, together, strict=True):
        assert np.array_equal(a, b) and np.array_equal(a, c)


def test_a_different_seed_changes_the_random_fill_but_not_the_zero_fill(stubbed: PEFeatureExtractor, data: bytes) -> None:
    mask = np.random.default_rng(1).random(len(data)) < 0.3
    assert np.array_equal(scorer_for(data, "zeros", seed=1).features(mask)[0], scorer_for(data, "zeros", seed=2).features(mask)[0])
    a = scorer_for(data, "random", seed=1).features(mask)[0]
    b = scorer_for(data, "random", seed=2).features(mask)[0]
    assert not np.array_equal(a, b)


################################################################################
# Window Scores (PF1)
################################################################################


SWEEP = 8


def test_process_file_saves_the_scores_it_ranks_with(stubbed: PEFeatureExtractor, data: bytes) -> None:
    """The saved scores are exactly the occlusion, sweep, and KernelSHAP scores, and the ablated file's features."""
    seed = 7
    scorer = scorer_for(data, "zeros", seed)
    f0, _ = scorer.scores(np.zeros(len(data), dtype=np.bool_))
    edges_j = window_edges(len(data), SWEEP)
    window_j = np.repeat(np.arange(edges_j.shape[0] - 1), np.diff(edges_j))
    sweep = {SWEEP: occlude_range(scorer, window_j, f0, 0, edges_j.shape[0] - 1)[0]}
    shapley = {"stub": np.random.default_rng(0).normal(size=NUM_WINDOWS)}
    _, _, arrays = process_file(data, {}, NUM_WINDOWS, "zeros", "typical", seed, (0.5, 1.0), sweep, shapley)
    saved = arrays["windows"]

    edges, _, _, occlusion, _ = occlude(scorer_for(data, "zeros", seed), len(data), NUM_WINDOWS)
    assert np.array_equal(saved["edges"], edges)
    assert np.array_equal(saved["occlusion:stub"], occlusion["stub"])
    assert np.array_equal(saved[f"edges_k{SWEEP}"], edges_j)
    assert np.array_equal(saved[f"occlusion_k{SWEEP}:stub"], sweep[SWEEP]["stub"])
    assert np.array_equal(saved["kernelshap_windows:stub"], shapley["stub"])
    protection = protect(data, header="typical")
    x_ablated, problem = scorer.features(~protection.mask)
    assert problem is None
    assert np.array_equal(saved["x_ablated"], x_ablated)
    assert np.array_equal(saved["x"], scorer.features(np.zeros(len(data), dtype=np.bool_))[0])


def test_window_scores_round_trip(tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    arrays = {
        3: {"edges": np.arange(5), "occlusion:gbdt": rng.normal(size=4), "x_ablated": np.full(2, np.nan)},
        11: {"edges": np.arange(3), "kernelshap_windows:gbdt": rng.normal(size=2)},
    }
    save_window_scores(tmp_path / "w.npz", arrays)
    loaded = load_window_scores(tmp_path / "w.npz")
    assert loaded.keys() == arrays.keys()
    for index, per_file in arrays.items():
        assert loaded[index].keys() == per_file.keys()
        for key, value in per_file.items():
            assert np.array_equal(loaded[index][key], value, equal_nan=True)
