"""
Feature-space explainers for detectors that consume feature vectors (GBDTs and MLPs).

Every explainer attributes the log-odds of the malware class, i.e., the GBDT's raw score or the difference between an
MLP's two logits, and returns attributions of shape (N, d) for N explained samples with d features.
"""

from __future__ import annotations
from collections.abc import Callable
from typing import Optional
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import shap
import torch
from torch import nn
from torch import Tensor


__all__ = [
    "log_odds",
    "treeshap_path",
    "treeshap_interventional",
    "kernelshap",
    "integrated_gradients",
    "gradient_x_input",
]


FloatArray = npt.NDArray[np.float64]


################################################################################
# Utilities
################################################################################


def log_odds(model: nn.Module) -> Callable[[Tensor], Tensor]:
    """
    Wrap a two-logit classifier into a function computing the log-odds of the positive class, shape (N,).
    """
    def f(x: Tensor) -> Tensor:
        z = model(x)
        return z[:, 1] - z[:, 0]  # type: ignore[no-any-return]
    return f


def _numpy_function(
    f: Callable[[Tensor], Tensor],
    device: torch.device,
    dtype: torch.dtype = torch.float32,
    batch_size: int = 8192,
) -> Callable[[npt.NDArray[np.floating]], FloatArray]:
    @torch.no_grad()
    def g(X: npt.NDArray[np.floating]) -> FloatArray:
        out = [f(torch.as_tensor(np.asarray(X[i:i + batch_size]), dtype=dtype, device=device)) for i in range(0, X.shape[0], batch_size)]
        return torch.cat(out).double().cpu().numpy()
    return g


################################################################################
# Tree Explainers
################################################################################


def treeshap_path(booster: lgb.Booster, X: npt.NDArray[np.floating]) -> tuple[FloatArray, FloatArray]:
    """
    Path-dependent TreeSHAP, computed exactly by LightGBM. No background data is needed.

    Returns:
        The attributions, shape (N, d), and the expected value of each sample, shape (N,), such that the
        attributions sum to the raw score minus the expected value.
    """
    contrib = np.asarray(booster.predict(X, pred_contrib=True, num_iteration=booster.best_iteration), dtype=np.float64)
    return contrib[:, :-1], contrib[:, -1]


def treeshap_interventional(
    booster: lgb.Booster,
    X: npt.NDArray[np.floating],
    background: npt.NDArray[np.floating],
    atol: float = 1e-3,
) -> FloatArray:
    """
    Interventional TreeSHAP with respect to a background distribution.

    The attributions of each sample sum to its raw score minus the mean raw score over the background. A
    `RuntimeWarning` reports the samples for which they do not, to within `atol`.

    Raises:
        RuntimeError: If shap's parsed copy of the trees does not reproduce LightGBM's raw scores on the background,
            e.g., because of categorical splits, which shap does not represent correctly.
    """
    background = np.asarray(background)
    X = np.asarray(X)
    f = gbdt_function(booster)
    f_background = f(background)
    # NOTE: shap silently subsamples a plain background array to 100 samples, so the masker keeps all of them.
    masker = shap.maskers.Independent(background, max_samples=background.shape[0])
    explainer = shap.TreeExplainer(booster, data=masker, feature_perturbation="interventional", model_output="raw")
    error = np.abs(explainer.model.predict(background) - f_background).max(initial=0.0)
    if error > 1e-4:
        raise RuntimeError(f"shap's copy of the trees differs from LightGBM's raw scores by up to {error:.3g}.")
    A = np.asarray(explainer.shap_values(X, check_additivity=False), dtype=np.float64)
    # NOTE: shap 0.52 occasionally violates local accuracy on deep trees (up to 0.11 on 2 of 2,000 EMBER-2024 files,
    # with trees of depth 37), although its trees reproduce LightGBM's scores. The cause is unconfirmed.
    errors = np.abs(A.sum(axis=1) - (f(X) - f_background.mean()))
    bad = np.flatnonzero(errors > atol)
    if bad.size > 0:
        warnings.warn(
            f"Interventional TreeSHAP violates local accuracy on {bad.size} of {X.shape[0]} samples "
            f"(rows {bad[:10].tolist()}{'...' if bad.size > 10 else ''}; largest error {errors.max():.3g}).",
            RuntimeWarning,
            stacklevel=2,
        )
    return A


################################################################################
# Model-Agnostic Explainers
################################################################################


def kernelshap(
    f: Callable[[npt.NDArray[np.floating]], FloatArray],
    X: npt.NDArray[np.floating],
    background: npt.NDArray[np.floating],
    nsamples: int | str = "auto",
    seed: int = 0,
    l1_reg: bool | str = False,
) -> FloatArray:
    """
    KernelSHAP for any function mapping feature vectors (N, d) to log-odds (N,).

    The cost per explained sample is about `nsamples * len(background)` evaluations of f, so the background should be
    small (e.g., a few dozen representative samples or k-means centroids).

    Args:
        l1_reg: Passed to shap. NOTE: shap's default ("auto") silently keeps only about 10 features when the coalitions
            are sparsely sampled, which is not a full explanation; the default here is False (least squares over every
            feature that differs from the background).
    """
    np.random.seed(seed)  # shap's sampler uses the global numpy state.
    explainer = shap.KernelExplainer(f, np.asarray(background))
    return np.asarray(explainer.shap_values(np.asarray(X), nsamples=nsamples, l1_reg=l1_reg, silent=True), dtype=np.float64)


def gbdt_function(booster: lgb.Booster) -> Callable[[npt.NDArray[np.floating]], FloatArray]:
    """The raw score (log-odds) of a GBDT as a function of feature vectors."""
    def f(X: npt.NDArray[np.floating]) -> FloatArray:
        return np.asarray(booster.predict(X, raw_score=True, num_iteration=booster.best_iteration), dtype=np.float64)
    return f


def mlp_function(model: nn.Module, device: torch.device = torch.device("cpu")) -> Callable[[npt.NDArray[np.floating]], FloatArray]:
    """The log-odds of a two-logit MLP as a function of feature vectors, evaluated in the model's dtype."""
    return _numpy_function(log_odds(model), device, next(model.parameters()).dtype)


################################################################################
# Gradient Explainers
################################################################################


def integrated_gradients(
    f: Callable[[Tensor], Tensor],
    x: Tensor,
    baseline: Tensor,
    steps: int = 64,
    batch_size: Optional[int] = None,
) -> Tensor:
    """
    Integrated Gradients with the midpoint rule, whose completeness error decreases as O(1 / steps^2).

    Args:
        f: Maps inputs (B, ...) to scalar outputs (B,), e.g., `log_odds(model)`.
        x: The explained inputs, shape (N, ...).
        baseline: The baseline, broadcastable to x.
        steps: The number of points along the path.
        batch_size: How many points along the path to evaluate at once (all of them by default).

    Returns:
        The attributions, shape (N, ...), which sum to approximately f(x) - f(baseline) for each sample.
    """
    baseline = baseline.expand_as(x)
    alphas = (torch.arange(steps, dtype=x.dtype, device=x.device) + 0.5) / steps
    batch_size = steps if batch_size is None else batch_size
    total = torch.zeros_like(x)
    for i in range(0, steps, batch_size):
        a = alphas[i:i + batch_size].view(-1, *([1] * x.dim()))                # (S, 1, ...)
        points = (baseline + a * (x - baseline)).reshape(-1, *x.shape[1:])    # (S * N, ...)
        points.requires_grad_(True)
        (grads,) = torch.autograd.grad(f(points).sum(), points)
        total += grads.reshape(-1, *x.shape).sum(dim=0)
    return (x - baseline) * total / steps


def gradient_x_input(f: Callable[[Tensor], Tensor], x: Tensor) -> Tensor:
    """
    Gradient times input, i.e., the first-order Taylor attribution with a zero baseline.
    """
    x = x.detach().clone().requires_grad_(True)
    (grads,) = torch.autograd.grad(f(x).sum(), x)
    return grads * x.detach()
