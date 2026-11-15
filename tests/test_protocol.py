"""
Tests for the scale-up's protocol helpers: thresholds set on a chosen split (provexp.detectors), complete files only
(provexp.data.tabular.load_features), and the choice between the pilot's and the scale-up's attacked files
(provexp.data.files.load_attacked).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from provexp.data.files import PROTOCOLS
from provexp.data.files import load_attacked
from provexp.data.tabular import FEATURES_FILE
from provexp.data.tabular import META_FILE
from provexp.data.tabular import load_features
from provexp.detectors import calibrate_threshold
from provexp.detectors import detection_at
from provexp.detectors import model_threshold
from provexp.registry import DESCRIPTIONS
from provexp.registry import TOOLKIT_ATTACKS
from provexp.registry import Detector
from provexp.registry import defense_args
from provexp.registry import detector
from provexp.registry import scaleup_models


def _predictions(path: Path, good: list[float], bad: list[float]) -> None:
    probs = good + bad
    labels = [0] * len(good) + [1] * len(bad)
    pl.DataFrame({"name": [f"f{i}" for i in range(len(probs))], "label": labels, "prob": probs}).write_parquet(path)


################################################################################
# Thresholds
################################################################################

class TestThresholds:

    @pytest.fixture
    def model(self, tmp_path: Path) -> Path:
        # Validation goodware: 100 scores 0.00..0.99; test goodware shifted up, so the two thresholds differ.
        _predictions(tmp_path / "vl_predictions.parquet", [i / 100 for i in range(100)], [0.995] * 10)
        _predictions(tmp_path / "ts_predictions.parquet", [0.5 + i / 200 for i in range(100)],
                     [0.2, 0.9, 0.95, 0.985, 0.999])
        return tmp_path

    @pytest.mark.parametrize("split", ["vl", "ts"])
    def test_matches_calibrate(self, model: Path, split: str) -> None:
        pred = pl.read_parquet(model / f"{split}_predictions.parquet")
        expected = calibrate_threshold(pred["prob"].to_numpy(), pred["label"].to_numpy(), 0.01)
        assert model_threshold(model, 0.01, split) == expected

    def test_splits_differ(self, model: Path) -> None:
        assert model_threshold(model, 0.01, "vl") != model_threshold(model, 0.01, "ts")

    def test_invalid_split(self, model: Path) -> None:
        with pytest.raises(ValueError, match="split"):
            model_threshold(model, 0.01, "tr")

    def test_missing_predictions(self, tmp_path: Path) -> None:
        _predictions(tmp_path / "ts_predictions.parquet", [0.1, 0.2], [0.9])
        with pytest.raises(FileNotFoundError):
            model_threshold(tmp_path, 0.01, "vl")

    def test_detection_at(self, model: Path) -> None:
        # vl at 1%: the second largest of the goodware scores 0.00..0.99, so p > 0.98 flags one of 100.
        out = detection_at(model, 0.01, "vl")
        assert out["tau"] == pytest.approx(0.98)
        assert out["tpr"] == pytest.approx(2 / 5)  # 0.985 and 0.999
        assert out["fpr_ts"] == pytest.approx(3 / 100)  # 0.5 + i / 200 > 0.98 for i = 97, 98, 99


################################################################################
# Complete files only
################################################################################

class TestCompleteOnly:

    @pytest.fixture
    def store(self, tmp_path: Path) -> Path:
        split = tmp_path / "tr"
        split.mkdir()
        np.save(split / FEATURES_FILE, np.arange(12, dtype=np.float32).reshape(6, 2))
        pl.DataFrame({
            "row": list(range(6)),
            "name": [f"f{i}" for i in range(6)],
            "label": [0, 1, 0, 1, 0, 1],
            "status": ["ok", "ok", "error", "ok", "ok", "ok"],
            "truncated": [False, True, False, False, True, False],
        }).write_parquet(split / META_FILE)
        return tmp_path

    @pytest.mark.parametrize(("only_ok", "complete_only", "names"), [
        (False, False, ["f0", "f1", "f2", "f3", "f4", "f5"]),
        (True, False, ["f0", "f1", "f3", "f4", "f5"]),
        (False, True, ["f0", "f2", "f3", "f5"]),
        (True, True, ["f0", "f3", "f5"]),
    ])
    def test_filters(self, store: Path, only_ok: bool, complete_only: bool, names: list[str]) -> None:
        X, meta = load_features(store, "tr", only_ok=only_ok, complete_only=complete_only)
        assert meta["name"].to_list() == names
        rows = [int(n[1:]) for n in names]
        np.testing.assert_array_equal(X, np.arange(12, dtype=np.float32).reshape(6, 2)[rows])


################################################################################
# Attacked files
################################################################################

class TestLoadAttacked:

    def test_protocols(self) -> None:
        assert PROTOCOLS == {"pilot": "ts", "scaleup": "vl"}

    def test_unknown_protocol(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="protocol"):
            load_attacked("final", tmp_path, tmp_path)

    def test_pilot_rejects_donors(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="drop --donors"):
            load_attacked("pilot", tmp_path, tmp_path, donors=tmp_path / "donors.parquet")

    def test_scaleup_needs_donors(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="--donors"):
            load_attacked("scaleup", tmp_path, tmp_path)


################################################################################
# The registry's scale-up model set
################################################################################

class TestScaleupModels:

    def test_layout(self) -> None:
        models = scaleup_models("root")
        assert set(models) == set(DESCRIPTIONS)
        assert models["unconstrained"] == Detector("root/4-detectors/unconstrained", "root/2-features/sums")
        assert models["expert-set"].features == "root/2-features/expert"
        assert {f"pv-loo-{a}" for a in TOOLKIT_ATTACKS} <= set(models)

    def test_defense_args(self) -> None:
        args = defense_args(["unconstrained", "monotone-sums", "iterated-2"], "scaleup")
        assert args[0] == "--defense" and args[1].startswith("unconstrained=") and args[1].endswith("/unconstrained")
        with pytest.raises(ValueError):
            defense_args(["unconstrained", "expert-set"], "scaleup")  # two stores
        with pytest.raises(ValueError):
            detector("iterated-1", "pilot")
