"""
Tests for explain/feature.py and explain/problem.py, on small synthetic models.
"""

import lightgbm as lgb
import numpy as np
import pytest
import torch
from torch import nn

from provexp.explain.feature import gbdt_function
from provexp.explain.feature import gradient_x_input
from provexp.explain.feature import integrated_gradients
from provexp.explain.feature import kernelshap
from provexp.explain.feature import log_odds
from provexp.explain.feature import mlp_function
from provexp.explain.feature import treeshap_interventional
from provexp.explain.feature import treeshap_path
from provexp.explain.problem import malconv_integrated_gradients
from provexp.explain.problem import malconv_occlusion
from provexp.models.malconv import MalConv


torch.set_num_threads(2)


@pytest.fixture(scope="module")
def booster() -> tuple[lgb.Booster, np.ndarray]:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(2000, 12))
    y = (X[:, 0] + X[:, 1] * X[:, 2] > 0).astype(int)
    params = {"objective": "binary", "num_iterations": 20, "num_leaves": 8, "verbosity": -1, "num_threads": 2, "seed": 0}
    return lgb.train(params, lgb.Dataset(X, label=y)), X


def linear_model(d: int, seed: int = 0) -> nn.Linear:
    torch.manual_seed(seed)
    return nn.Linear(d, 2).double()


def small_mlp(d: int, seed: int = 0) -> nn.Module:
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(d, 16), nn.Tanh(), nn.Linear(16, 2)).double()


################################################################################
# Tree Explainers
################################################################################


def test_treeshap_path_local_accuracy(booster: tuple[lgb.Booster, np.ndarray]) -> None:
    model, X = booster
    A, base = treeshap_path(model, X[:50])
    assert A.shape == (50, 12)
    assert np.allclose(A.sum(axis=1) + base, gbdt_function(model)(X[:50]))


def test_treeshap_interventional_local_accuracy(booster: tuple[lgb.Booster, np.ndarray]) -> None:
    model, X = booster
    background = X[1000:1300]  # More than shap's default limit of 100 background samples.
    A = treeshap_interventional(model, X[:20], background)
    f = gbdt_function(model)
    assert np.allclose(A.sum(axis=1), f(X[:20]) - f(background).mean(), atol=1e-6)


def test_treeshap_interventional_rejects_categorical_splits() -> None:
    """shap misrepresents categorical splits on large category codes, so the explainer must refuse such models."""
    rng = np.random.default_rng(0)
    X = rng.normal(size=(2000, 4))
    X[:, 0] = rng.integers(0, 200, size=2000)
    y = ((X[:, 0] % 7 < 3) ^ (X[:, 1] > 0)).astype(int)
    params = {"objective": "binary", "num_iterations": 20, "num_leaves": 8, "verbosity": -1, "num_threads": 2, "seed": 0, "min_data_per_group": 5, "cat_smooth": 1}
    model = lgb.train(params, lgb.Dataset(X, label=y, categorical_feature=[0]))
    with pytest.raises(RuntimeError):
        treeshap_interventional(model, X[:5], X[1000:1100])


def test_kernelshap_gbdt_local_accuracy(booster: tuple[lgb.Booster, np.ndarray]) -> None:
    model, X = booster
    background = X[1000:1010]
    f = gbdt_function(model)
    A = kernelshap(f, X[:3], background, nsamples=500)
    assert np.allclose(A.sum(axis=1), f(X[:3]) - f(background).mean(), atol=1e-6)


def test_kernelshap_linear_is_exact() -> None:
    """For a linear model, the Shapley values are w * (x - E[x]) regardless of the coalitions sampled."""
    model = linear_model(6)
    rng = np.random.default_rng(1)
    X, background = rng.normal(size=(4, 6)), rng.normal(size=(8, 6))
    A = kernelshap(mlp_function(model), X, background, nsamples=200)
    w = (model.weight[1] - model.weight[0]).detach().numpy()
    assert np.allclose(A, w * (X - background.mean(axis=0)), atol=1e-6)


################################################################################
# Gradient Explainers
################################################################################


@pytest.mark.parametrize("batch_size", [None, 5])
def test_integrated_gradients_completeness(batch_size: int | None) -> None:
    model = small_mlp(10)
    x = torch.randn(4, 10, dtype=torch.float64)
    b = torch.randn(10, dtype=torch.float64)
    f = log_odds(model)
    A = integrated_gradients(f, x, b, steps=64, batch_size=batch_size)
    with torch.no_grad():
        assert torch.allclose(A.sum(dim=1), f(x) - f(b.expand_as(x)), atol=1e-4)


def test_integrated_gradients_linear_is_exact() -> None:
    model = linear_model(10)
    x = torch.randn(3, 10, dtype=torch.float64)
    b = torch.randn(10, dtype=torch.float64)
    A = integrated_gradients(log_odds(model), x, b, steps=1)
    w = (model.weight[1] - model.weight[0]).detach()
    assert torch.allclose(A, w * (x - b))


def test_gradient_x_input() -> None:
    model = linear_model(10)
    x = torch.randn(3, 10, dtype=torch.float64)
    w = (model.weight[1] - model.weight[0]).detach()
    assert torch.allclose(gradient_x_input(log_odds(model), x), w * x)


################################################################################
# MalConv Explainers
################################################################################


def tiny_malconv(seed: int = 0) -> MalConv:
    torch.manual_seed(seed)
    model = MalConv(channels=6, window_size=8, stride=8, embd_size=3).double().eval()
    with torch.no_grad():
        model.embd.weight[0] = 0.0
    return model


def malconv_log_odds(model: MalConv, x: torch.Tensor) -> float:
    with torch.no_grad():
        z = model(x.unsqueeze(0))[0]
    return float(z[1] - z[0])


@pytest.mark.parametrize("T", [5, 8, 64, 75])
def test_malconv_integrated_gradients_completeness(T: int) -> None:
    model = tiny_malconv()
    x = torch.randint(1, 257, (T,))
    A = malconv_integrated_gradients(model, x, steps=256, batch_size=64)
    assert A.shape == (T,)
    baseline = malconv_log_odds(model, torch.zeros(max(T, 8), dtype=torch.int64))
    assert abs(float(A.sum()) - (malconv_log_odds(model, x) - baseline)) < 1e-3


@pytest.mark.parametrize("T, blocks", [(5, 1), (64, 1), (75, 1), (75, 2), (75, 4)])
def test_malconv_occlusion_matches_brute_force(T: int, blocks: int) -> None:
    model = tiny_malconv()
    x = torch.randint(1, 257, (T,))
    A = malconv_occlusion(model, x, blocks=blocks)
    base = malconv_log_odds(model, x)
    width = 8 * blocks
    covered = min(T, max(T, 8) // 8 * 8)
    expected = torch.zeros(T, dtype=torch.float64)
    for lo in range(0, covered, width):
        hi = min(lo + width, covered)
        occluded = x.clone()
        occluded[lo:hi] = 0
        expected[lo:hi] = (base - malconv_log_odds(model, occluded)) / (hi - lo)
    assert torch.allclose(A, expected, atol=1e-10)
    # Bytes after the last complete window do not influence MalConv.
    assert torch.all(A[covered:] == 0)


def test_malconv_occlusion_requires_aligned_windows() -> None:
    model = MalConv(channels=4, window_size=8, stride=4, embd_size=3)
    with pytest.raises(ValueError):
        malconv_occlusion(model, torch.randint(1, 257, (32,)))
