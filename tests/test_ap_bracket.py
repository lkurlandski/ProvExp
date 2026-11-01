"""
Tests for scripts/ap_bracket.py: the cheap per-tree floor and the ceiling from attack results.
"""

from __future__ import annotations

from pathlib import Path
import sys

import lightgbm
import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ap_bracket import ceilings  # noqa: E402
from ap_bracket import cheap_floor  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402


################################################################################
# Cheap floor
################################################################################


@pytest.fixture(scope="module")
def model() -> tuple[lightgbm.Booster, np.ndarray]:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(400, 6))
    y = (x[:, 0] + x[:, 1] * x[:, 2] > 0).astype(int)
    booster = lightgbm.train({"objective": "binary", "num_leaves": 8, "verbose": -1, "seed": 0},
                             lightgbm.Dataset(x, y), num_boost_round=20)
    return booster, x[:20]


class TestCheapFloor:

    def test_nothing_moved_is_the_score(self, model: tuple[lightgbm.Booster, np.ndarray]) -> None:
        booster, xs = model
        ens = Ensemble(booster)
        for x in xs:
            floor, moved = cheap_floor(ens, x, set())
            assert moved == 0
            assert floor == pytest.approx(float(booster.predict(x.reshape(1, -1), raw_score=True)[0]), abs=1e-9)

    def test_everything_moved_is_each_trees_lowest_leaf(self, model: tuple[lightgbm.Booster, np.ndarray]) -> None:
        booster, xs = model
        ens = Ensemble(booster)
        floor, moved = cheap_floor(ens, xs[0], set(range(6)))
        assert moved == sum(len(n) for n in ens.nodes)
        assert floor == pytest.approx(sum(float(ens.values[leaves].min()) for leaves in ens.leaves))

    @pytest.mark.parametrize("seed", [0, 1, 2])
    def test_sound_against_sampled_moves(self, model: tuple[lightgbm.Booster, np.ndarray], seed: int) -> None:
        booster, xs = model
        ens = Ensemble(booster)
        rng = np.random.default_rng(seed)
        moved = {0, 2}
        x = xs[seed]
        floor, _ = cheap_floor(ens, x, moved)
        for _ in range(200):
            x2 = x.copy()
            x2[list(moved)] = rng.normal(scale=3.0, size=len(moved))
            assert float(booster.predict(x2.reshape(1, -1), raw_score=True)[0]) >= floor - 1e-9


################################################################################
# Ceiling
################################################################################


class TestCeilings:

    def test_lowest_valid_score_wins(self, tmp_path: Path) -> None:
        toolkit = tmp_path / "toolkit.parquet"
        pl.DataFrame({
            "defense": ["d", "d", "d", "d"], "name": ["f"] * 4, "attack": ["a", "b", "c", "e"],
            "p_adv": [0.6, 0.2, 0.01, 0.1], "ok": [True, True, True, False], "valid": [True, True, True, True],
            "over_budget": [False, False, True, False],
        }).write_parquet(toolkit)
        adaptive = tmp_path / "adaptive.parquet"
        pl.DataFrame({"defense": ["d"], "name": ["f"], "p_adv_real": [0.3]}).write_parquet(adaptive)
        score, attack = ceilings([toolkit], [adaptive])[("d", "f")]
        assert attack == "b"  # c is over budget, e did not load
        assert score == pytest.approx(np.log(0.2 / 0.8))
