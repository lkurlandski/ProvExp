"""
A multilayer perceptron for EMBER-2024 features, configured as in SSViT (which followed SOREL-20M).

The feature standardization is part of the model, so the model consumes raw features and gradient-based explanations
are with respect to the raw features, i.e., the quantities whose provenance the feature set tracks.
"""

from __future__ import annotations
from collections.abc import Iterator
from functools import partial
import math

import numpy as np
from numpy import typing as npt
import torch
from torch import nn
from torch import Tensor
from torch.nn import functional as F


__all__ = [
    "Standardize",
    "MLP",
    "build_mlp",
    "fit_standardize",
    "train_mlp",
]


class Standardize(nn.Module):
    """
    Standardize features to zero mean and unit variance with fixed statistics. Constant features are left centered.
    """

    def __init__(self, mean: Tensor, std: Tensor) -> None:
        super().__init__()
        self.register_buffer("mean", mean.to(torch.float32))
        self.register_buffer("std", torch.where(std > 0, std, torch.ones_like(std)).to(torch.float32))

    def forward(self, x: Tensor) -> Tensor:
        return (x - self.mean) / self.std  # type: ignore[operator]


class MLP(nn.Module):
    """
    Multilayer Perceptron for tabular classification.

    This is extremely similar to the network used by the SOREL paper. The only difference is that we use two output
    logits instead of one for detection.

    See: https://github.com/sophos/SOREL-20M/blob/master/nets.py
    """

    def __init__(self, input_size: int, layer_sizes: tuple[int, ...] = (512, 512, 128), output_size: int = 2, dropout: float = 0.05) -> None:
        super().__init__()

        build_layer = partial(self.build_layer, dropout=dropout)

        layers = []
        layers.extend(build_layer(input_size, layer_sizes[0]))
        for i in range(len(layer_sizes) - 1):
            layers.extend(build_layer(layer_sizes[i], layer_sizes[i + 1]))
        layers.append(nn.Linear(layer_sizes[-1], output_size))

        self.model = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.model(x)  # type: ignore[no-any-return]

    @staticmethod
    def build_layer(input_size: int, output_size: int, dropout: float) -> list[nn.Module]:
        return [
            nn.Linear(input_size, output_size),
            nn.LayerNorm(output_size),
            nn.ELU(),
            nn.Dropout(dropout),
        ]


def fit_standardize(X: npt.NDArray[np.float32], chunk: int = 2 ** 16) -> Standardize:
    """
    Compute the mean and standard deviation of each feature in float64, in chunks so that X can be memory-mapped.
    """
    n = X.shape[0]
    s = np.zeros(X.shape[1], dtype=np.float64)
    for i in range(0, n, chunk):
        s += X[i:i + chunk].sum(axis=0, dtype=np.float64)
    mean = s / n
    q = np.zeros(X.shape[1], dtype=np.float64)
    for i in range(0, n, chunk):
        q += ((X[i:i + chunk].astype(np.float64) - mean) ** 2).sum(axis=0)
    std = np.sqrt(q / n)
    return Standardize(torch.from_numpy(mean), torch.from_numpy(std))


def build_mlp(standardize: Standardize, layer_sizes: tuple[int, ...] = (512, 512, 128)) -> nn.Sequential:
    """
    An MLP that consumes raw features, i.e., `Standardize` followed by `MLP`.
    """
    return nn.Sequential(standardize, MLP(int(standardize.mean.shape[0]), layer_sizes))  # type: ignore[index]


def _batches(n: int, batch_size: int, generator: torch.Generator, shuffle: bool, device: torch.device) -> Iterator[Tensor]:
    order = torch.randperm(n, generator=generator, device="cpu").to(device) if shuffle else torch.arange(n, device=device)
    for i in range(0, n, batch_size):
        yield order[i:i + batch_size]


@torch.no_grad()
def _evaluate(model: nn.Module, X: Tensor, y: Tensor, batch_size: int) -> tuple[float, Tensor]:
    model.eval()
    logits = torch.cat([model(X[i:i + batch_size]) for i in range(0, X.shape[0], batch_size)])
    return float(F.cross_entropy(logits, y)), logits


def train_mlp(
    X_tr: npt.NDArray[np.float32],
    y_tr: npt.NDArray[np.int64],
    X_vl: npt.NDArray[np.float32],
    y_vl: npt.NDArray[np.int64],
    seed: int = 0,
    device: torch.device = torch.device("cuda"),
    layer_sizes: tuple[int, ...] = (512, 512, 128),
    batch_size: int = 8192,
    learning_rate: float = 3e-3,
    weight_decay: float = 1e-5,
    max_norm: float = 10.0,
    max_epochs: int = 160,
    patience: int = 16,
    min_delta: float = 1e-4,
) -> nn.Sequential:
    """
    Train an MLP with AdamW and a one-cycle schedule and keep the weights with the lowest validation loss.

    The defaults are those of SSViT for EMBER-2024: 160 epochs over the full training set and early stopping with a
    patience of a tenth of that. The data is moved to the device in its entirety, which is much faster than a
    DataLoader for tabular data (about 21 GB for the full training set).
    """
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)

    model = build_mlp(fit_standardize(X_tr), layer_sizes).to(device)
    Xtr, ytr = torch.from_numpy(np.ascontiguousarray(X_tr)).to(device), torch.from_numpy(y_tr).to(device)
    Xvl, yvl = torch.from_numpy(np.ascontiguousarray(X_vl)).to(device), torch.from_numpy(y_vl).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    steps_per_epoch = math.ceil(Xtr.shape[0] / batch_size)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=learning_rate,
        total_steps=steps_per_epoch * max_epochs,
        pct_start=0.05,
        div_factor=100.0,
        final_div_factor=100.0,
    )

    best_loss, best_state, since_best = math.inf, None, 0
    for epoch in range(max_epochs):
        model.train()
        total = 0.0
        for idx in _batches(Xtr.shape[0], batch_size, generator, True, device):
            loss = F.cross_entropy(model(Xtr[idx]), ytr[idx])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()  # type: ignore[no-untyped-call]
            nn.utils.clip_grad_norm_(model.parameters(), max_norm)
            optimizer.step()
            scheduler.step()
            total += float(loss.detach()) * idx.shape[0]
        vl_loss, _ = _evaluate(model, Xvl, yvl, batch_size)
        print(f"epoch={epoch} tr_loss={total / Xtr.shape[0]:.5f} vl_loss={vl_loss:.5f}", flush=True)

        if vl_loss < best_loss - min_delta:
            best_loss, since_best = vl_loss, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            since_best += 1
            if since_best >= patience:
                print(f"Stopping early at epoch {epoch}.", flush=True)
                break

    assert best_state is not None
    model.load_state_dict(best_state)
    return model.eval()
