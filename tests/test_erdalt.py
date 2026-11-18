"""
Tests for provexp.models.erdalt: the monotone upper network, the violation count, training, and scoring.
"""

from pathlib import Path

import numpy as np
import pytest
import torch

from provexp.models.erdalt import ERDALT
from provexp.models.erdalt import ERDALTDetector
from provexp.models.erdalt import fit_quantile_scale
from provexp.models.erdalt import load_detector
from provexp.models.erdalt import num_violations
from provexp.models.erdalt import project_monotone
from provexp.models.erdalt import pv_mask
from provexp.models.erdalt import save_erdalt
from provexp.models.erdalt import train_erdalt
from provexp.models.mlp import Standardize


def _model(d: int, seed: int, hidden: int = 16) -> ERDALT:
    torch.manual_seed(seed)
    std = Standardize(torch.randn(d), torch.rand(d) + 0.5)
    model = ERDALT(std, hidden)
    with torch.no_grad():
        for p in model.parameters():
            p.copy_(torch.randn_like(p))
    return model


################################################################################
# Monotonicity
################################################################################

class TestMonotone:

    @pytest.mark.parametrize("seed", range(5))
    def test_nonnegative_post_change_never_lowers_the_score(self, seed: int) -> None:
        """After projection, any change whose post-processed image is nonnegative cannot lower the logit (Prop. 3)."""
        d = 6
        model = _model(d, seed)
        project_monotone(model)
        model.eval()
        g = torch.Generator().manual_seed(seed)
        x = torch.randn(200, d, generator=g)
        # Choose delta with L(delta / std) = u >= 0: delta = std * L^-1 u.
        L = model.layer1.weight.detach()
        u = torch.rand(200, d, generator=g)
        delta = torch.linalg.solve(L, u.T).T * model.standardize.std
        assert torch.allclose(model.post_delta(delta), u, atol=1e-4)
        with torch.no_grad():
            assert bool((model(x + delta) >= model(x) - 1e-5).all())

    def test_projection_makes_upper_weights_positive(self) -> None:
        model = _model(5, 0)
        project_monotone(model)
        for layer in (model.layer2, model.layer3, model.fc4):
            assert bool((layer.weight > 0).all())
        assert bool((model.layer1.weight < 0).any())  # the post-processing itself is not constrained

    def test_free_output_layer_is_not_monotone(self) -> None:
        """The released code's configuration (output layer unprojected) can lower the score: the reason for our patch."""
        model = _model(4, 1)
        project_monotone(model)
        with torch.no_grad():
            model.fc4.weight.mul_(-1.0)
            model.layer1.weight.copy_(torch.eye(4))
        model.eval()
        x = torch.zeros(1, 4)
        with torch.no_grad():
            assert float(model(x + torch.ones(1, 4) * 5)) < float(model(x))


################################################################################
# Violations and training
################################################################################

class TestTraining:

    def test_num_violations_counts_negative_entries(self) -> None:
        model = _model(3, 0)
        with torch.no_grad():
            model.layer1.weight.copy_(torch.eye(3))
        deltas = torch.tensor([[1.0, -1.0, 0.0], [-2.0, -3.0, 4.0]])
        assert num_violations(model, deltas, batch_size=1) == 3

    def test_training_removes_violations(self) -> None:
        rng = np.random.default_rng(0)
        n, d = 512, 8
        X = rng.normal(size=(n, d)).astype(np.float32)
        y = (X[:, 2] - X[:, 0] > 0).astype(np.int64)
        # Attacks that, like real ones, move features in a narrow set of directions: feature 0 only down, feature 1
        # both ways, the others only up. A valid L exists (flip feature 0, drop feature 1).
        D = np.abs(rng.normal(size=(20, d))).astype(np.float32)
        D[:, 0] *= -1.0
        D[:, 1] *= rng.choice([-1.0, 1.0], size=20).astype(np.float32)
        model, summary = train_erdalt(X, y, X, y, D, device=torch.device("cpu"), hidden=16, batch_size=64, epochs=40,
                                      learning_rate=1e-2)
        assert summary["met_criterion"]
        assert num_violations(model, torch.from_numpy(D)) < 5
        assert summary["vl_roc"] > 0.6


class TestDiagnosisOptions:

    @staticmethod
    def _data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rng = np.random.default_rng(0)
        X = rng.normal(size=(256, 6)).astype(np.float32)
        y = (X[:, 2] + X[:, 3] > 0).astype(np.int64)
        D = np.abs(rng.normal(size=(30, 6))).astype(np.float32)
        D[:, 0] *= -1.0
        D[:, 1] *= rng.choice([-1.0, 1.0], size=30).astype(np.float32)
        return X, y, D

    def test_pv_mask_keeps_the_never_lowered_features(self) -> None:
        _, _, D = self._data()
        assert pv_mask(D).tolist() == [False, False, True, True, True, True]

    def test_frozen_pv_post_has_no_violation_and_does_not_move(self) -> None:
        X, y, D = self._data()
        model, summary = train_erdalt(X, y, X, y, D, device=torch.device("cpu"), hidden=8, batch_size=64, epochs=3,
                                      learning_rate=1e-2, post_init="pv", freeze_post=True)
        expected = torch.diag(torch.tensor([0.0, 0.0, 1.0, 1.0, 1.0, 1.0]))
        assert torch.equal(model.layer1.weight.detach(), expected)
        assert all(h["violations"] == 0 for h in summary["history"])
        assert summary["met_criterion"] and summary["post_init"] == "pv" and summary["freeze_post"]

    def test_pv_init_trains_l(self) -> None:
        X, y, D = self._data()
        model, _ = train_erdalt(X, y, X, y, D, device=torch.device("cpu"), hidden=8, batch_size=64, epochs=2,
                                learning_rate=1e-2, post_init="pv")
        assert model.layer1.weight.requires_grad
        assert not torch.equal(model.layer1.weight.detach(), torch.diag(torch.tensor([0.0, 0.0, 1, 1, 1, 1])))

    def test_subsample_logs_violations_over_all_vectors(self) -> None:
        X, y, D = self._data()
        _, summary = train_erdalt(X, y, X, y, D, device=torch.device("cpu"), hidden=8, batch_size=64, epochs=2,
                                  deltas_subsample=10)
        assert summary["num_deltas"] == 10 and summary["num_deltas_all"] == 30
        assert all(h["violations_all"] >= h["violations"] for h in summary["history"])

    @pytest.mark.parametrize("bad", [0, 31])
    def test_subsample_out_of_range_is_an_error(self, bad: int) -> None:
        X, y, D = self._data()
        with pytest.raises(ValueError):
            train_erdalt(X, y, X, y, D, device=torch.device("cpu"), epochs=1, deltas_subsample=bad)

    def test_quantile_scale_is_the_larger_of_std_and_quantile(self) -> None:
        rng = np.random.default_rng(0)
        X = rng.normal(size=(10_000, 3)).astype(np.float32)
        X[:300, 0] = 50.0  # a fat tail: the 0.99 quantile of |x - mean| (~48) exceeds the std (~8.5)
        X[0, 1] = 1e6  # one huge outlier: the std (~1e4) exceeds the quantile
        X[:, 2] = 0.0
        X[:5, 2] = 1.0  # sparse: the quantile is |mean|, far below the std
        std = fit_quantile_scale(X, q=0.99)
        dev = np.abs(X.astype(np.float64) - X.astype(np.float64).mean(axis=0))
        expected = np.maximum(np.quantile(dev, 0.99, axis=0), X.astype(np.float64).std(axis=0))
        assert np.allclose(std.std.numpy(), expected, rtol=1e-4)  # type: ignore[operator]
        assert float(std.std[0]) > 3 * float(X[:, 0].std())  # type: ignore[index]

    def test_quantile_scale_trains(self) -> None:
        X, y, D = self._data()
        _, summary = train_erdalt(X, y, X, y, D, device=torch.device("cpu"), hidden=8, batch_size=64, epochs=1,
                                  input_scale="quantile")
        assert summary["input_scale"] == "quantile"


################################################################################
# Persistence and scoring
################################################################################

class TestDetector:

    def test_round_trip_and_column_selection(self, tmp_path: Path) -> None:
        names = ["a", "b", "c"]
        model = _model(3, 2)
        project_monotone(model)
        model.eval()
        save_erdalt(model, tmp_path, names, {"hidden": 16})
        det = load_detector(tmp_path, ["z", "c", "a", "b", "y"])
        assert isinstance(det, ERDALTDetector)
        rng = np.random.default_rng(0)
        own = rng.normal(size=(7, 3)).astype(np.float32)
        wide = np.zeros((7, 5), dtype=np.float32)
        wide[:, [2, 3, 1]] = own
        with torch.no_grad():
            expected = torch.sigmoid(model(torch.from_numpy(own))).double().numpy()
        np.testing.assert_allclose(det.predict(own), expected, rtol=1e-6)
        np.testing.assert_allclose(det.predict(wide), expected, rtol=1e-6)
        assert det.num_feature() == 5
        with pytest.raises(ValueError):
            det.predict(np.zeros((1, 4)))

    def test_missing_feature_is_an_error(self, tmp_path: Path) -> None:
        save_erdalt(_model(2, 0), tmp_path, ["a", "b"], {"hidden": 16})
        with pytest.raises(ValueError):
            ERDALTDetector(tmp_path, ["a", "x"])


class TestTemperature:

    def test_scaled_probabilities_do_not_saturate_and_keep_the_order(self) -> None:
        from provexp.models.erdalt import fit_temperature

        z = np.array([-500.0, -2.0, 40.0, 900.0, 1800.0])
        t = fit_temperature(z)
        p = 1.0 / (1.0 + np.exp(-z / t))
        assert t == pytest.approx(60.0)
        assert bool((p < 1.0).all() and (p > 0.0).all())
        assert list(np.argsort(p)) == list(np.argsort(z))
        assert fit_temperature(np.array([-3.0, 5.0])) == 1.0
