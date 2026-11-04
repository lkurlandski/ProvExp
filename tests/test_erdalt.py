"""
Tests for provexp.models.erdalt: the monotone upper network, the violation count, training, and scoring.
"""

from pathlib import Path

import numpy as np
import pytest
import torch

from provexp.models.erdalt import ERDALT
from provexp.models.erdalt import ERDALTDetector
from provexp.models.erdalt import load_detector
from provexp.models.erdalt import num_violations
from provexp.models.erdalt import project_monotone
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
