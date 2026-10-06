"""
Problem-space explainers for MalConv, which consumes bytes directly.

Every explainer attributes the log-odds of the malware class and returns one attribution per byte of the input.
"""

from __future__ import annotations

import torch
from torch import Tensor
from torch.nn import functional as F

from provexp.explain.feature import integrated_gradients
from provexp.models.malconv import MalConv


__all__ = [
    "malconv_integrated_gradients",
    "malconv_occlusion",
]


def _log_odds_from_pooled(model: MalConv, h: Tensor) -> Tensor:
    z = model.fc_2(F.relu(model.fc_1(h)))
    return z[..., 1] - z[..., 0]  # type: ignore[no-any-return]


def malconv_integrated_gradients(model: MalConv, x: Tensor, steps: int = 256, batch_size: int = 8) -> Tensor:
    """
    Integrated Gradients over the byte embeddings, with the padding embedding (zero) as the baseline, summed over the
    embedding dimension to give one attribution per byte.

    Args:
        model: A MalConv model in evaluation mode.
        x: The input tokens of one file, shape (T,) (see `provexp.models.malconv.encode`).
        steps: The number of points along the path. MalConv's max-pooling makes the integrand piecewise, so it needs
            more steps than smooth models: on a 4 MB file, 64 steps leave a 1% completeness error and 256 leave <0.01%.
        batch_size: How many points along the path to evaluate at once.

    Returns:
        The attributions, shape (T,), which sum to approximately f(x) minus the log-odds of an all-padding input.
    """
    with torch.no_grad():
        z = model.embed(x.unsqueeze(0))                                         # (1, T', E)

    def f(e: Tensor) -> Tensor:
        logits = model.forward_embeddings(e)
        return logits[:, 1] - logits[:, 0]

    attributions = integrated_gradients(f, z, torch.zeros_like(z), steps=steps, batch_size=batch_size)
    return attributions[0, :x.shape[0]].sum(dim=-1)


@torch.no_grad()
def malconv_occlusion(model: MalConv, x: Tensor, blocks: int = 1) -> Tensor:
    """
    The decrease in log-odds when each window of `blocks * stride` bytes is replaced by padding, spread uniformly over
    the bytes of the window.

    This requires MalConv's kernel size to equal its stride, so its windows do not overlap. Then occluding an aligned
    window changes only the convolutional activations of that window, which become those of the (zero) padding
    embedding, and the occluded log-odds follow from the per-channel maximum over the other positions. Every window is
    evaluated exactly, in one pass. Bytes after the last complete window do not influence MalConv and receive zero.

    Args:
        model: A MalConv model in evaluation mode.
        x: The input tokens of one file, shape (T,).
        blocks: The number of convolutional windows per occluded window.

    Returns:
        The attributions, shape (T,).
    """
    k, s = model.conv_1.kernel_size[0], model.conv_1.stride[0]
    if k != s:
        raise ValueError(f"Occlusion requires non-overlapping windows. Got kernel size {k} and stride {s}.")

    z = model.embed(x.unsqueeze(0)).transpose(1, 2)                             # (1, E, T')
    G = (model.conv_1(z) * torch.sigmoid(model.conv_2(z)))[0]                   # (C, S)
    assert model.conv_1.bias is not None and model.conv_2.bias is not None
    g0 = model.conv_1.bias * torch.sigmoid(model.conv_2.bias)                   # (C,), any window of padding
    C, S = G.shape

    # The per-channel maximum over all positions outside each occluded window [w * blocks, (w + 1) * blocks).
    W = -(-S // blocks)
    pad = W * blocks - S
    Gp = F.pad(G, (0, pad), value=-torch.inf).view(C, W, blocks).amax(dim=-1)   # (C, W), the max within each window
    prefix = torch.cummax(Gp, dim=1).values
    suffix = torch.cummax(Gp.flip(1), dim=1).values.flip(1)
    ninf = torch.full((C, 1), -torch.inf, device=G.device, dtype=G.dtype)
    outside = torch.maximum(torch.cat([ninf, prefix[:, :-1]], dim=1), torch.cat([suffix[:, 1:], ninf], dim=1))
    occluded = torch.maximum(outside, g0[:, None]).T                            # (W, C)

    base = _log_odds_from_pooled(model, G.amax(dim=1))
    delta = base - _log_odds_from_pooled(model, occluded)                       # (W,)

    # Spread each window's attribution uniformly over the bytes it covers, i.e., the bytes of the original input that
    # fall within one of its convolutional windows.
    T = x.shape[0]
    width = blocks * s
    covered = min(T, S * s)
    window = torch.arange(covered, device=G.device) // width
    counts = torch.bincount(window, minlength=W).to(G.dtype)
    attributions = torch.zeros(T, dtype=G.dtype, device=G.device)
    attributions[:covered] = delta[window] / counts[window]
    return attributions
