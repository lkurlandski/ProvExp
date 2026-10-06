"""
Tests for models/gbdt.py and models/mlp.py, on small synthetic data.
"""

from typing import Any

import numpy as np
import pytest
import torch

from provexp.models.gbdt import EMBER2024_CATEGORICAL
from provexp.models.gbdt import train_gbdt
from provexp.models.mlp import build_mlp
from provexp.models.mlp import fit_standardize
from provexp.models.mlp import train_mlp


THREADS = 2


def synthetic(n: int, d: int = 710, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Features with a few informative columns and wildly different scales, like EMBER's."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d)).astype(np.float32) * rng.choice([1e-3, 1.0, 1e6], size=d).astype(np.float32)
    categorical = [c for c in EMBER2024_CATEGORICAL if c < d]
    X[:, categorical] = rng.integers(0, 4, size=(n, len(categorical)))
    y = ((X[:, 10] / np.abs(X[:, 10]).max() + X[:, 20] / np.abs(X[:, 20]).max()) > 0).astype(np.int64)
    return X, y


def test_fit_standardize() -> None:
    X, _ = synthetic(1000)
    X[:, 0] = 7.0  # A constant feature.
    s = fit_standardize(X, chunk=128)
    assert np.allclose(s.mean.numpy(), X.astype(np.float64).mean(axis=0), rtol=1e-5)  # type: ignore[operator]
    assert np.allclose(s.std.numpy()[1:], X.astype(np.float64).std(axis=0)[1:], rtol=1e-4)  # type: ignore[operator]
    assert s.std[0] == 1.0  # type: ignore[index]
    Z = s(torch.from_numpy(X)).numpy()
    assert np.allclose(Z[:, 1:].mean(axis=0), 0.0, atol=1e-3)
    assert np.allclose(Z[:, 0], 0.0)


def test_train_gbdt() -> None:
    X, y = synthetic(4000)
    booster = train_gbdt(X[:3000], y[:3000], X[3000:], y[3000:], seed=0, num_iterations=30, num_threads=THREADS, verbosity=-1)
    assert 1 <= booster.best_iteration <= 30
    p = np.asarray(booster.predict(X[3000:], num_iteration=booster.best_iteration))
    assert ((p > 0.5) == y[3000:]).mean() > 0.9


def test_train_gbdt_is_seeded() -> None:
    X, y = synthetic(2000)
    kwds: dict[str, Any] = {"num_iterations": 10, "num_threads": THREADS, "verbosity": -1}
    a = train_gbdt(X[:1500], y[:1500], X[1500:], y[1500:], seed=3, **kwds).predict(X[1500:])
    b = train_gbdt(X[:1500], y[:1500], X[1500:], y[1500:], seed=3, **kwds).predict(X[1500:])
    c = train_gbdt(X[:1500], y[:1500], X[1500:], y[1500:], seed=4, **kwds).predict(X[1500:])
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_invalid_stopper_metric() -> None:
    X, y = synthetic(100)
    with pytest.raises(ValueError):
        train_gbdt(X, y, X, y, stopper_metric="f1")


def test_train_mlp() -> None:
    torch.set_num_threads(THREADS)
    X, y = synthetic(4000, d=32)
    model = train_mlp(X[:3000], y[:3000], X[3000:], y[3000:], seed=0, device=torch.device("cpu"), batch_size=256, max_epochs=10, patience=3)
    assert not model.training
    with torch.no_grad():
        p = model(torch.from_numpy(X[3000:])).argmax(dim=-1).numpy()
    assert (p == y[3000:]).mean() > 0.9


def test_mlp_consumes_raw_features() -> None:
    X, _ = synthetic(100)
    model = build_mlp(fit_standardize(X)).eval()
    x = torch.from_numpy(X[:4]).requires_grad_()
    model(x)[:, 1].sum().backward()
    assert x.grad is not None and x.grad.shape == x.shape
