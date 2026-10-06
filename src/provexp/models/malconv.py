"""
A standard-memory implementation of MalConv and utilities to load the released EMBER-2024 checkpoints.

The released checkpoints were trained with the constant-memory MalConv from MalConv2
(github.com/FutureComputing4AI/MalConv2), which computes the same function with less memory. This implementation keeps
MalConv2's parameter names, so a converted checkpoint loads directly.

See: Raff "Malware detection by eating a whole EXE." AICS 2018.
See: Raff "Classifying Sequences of Extreme Length with Constant Memory Applied to Malware Detection" AAAI 2021.
"""

from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from typing import Optional

import torch
from torch import nn
from torch.nn import functional as F
from torch import Tensor


__all__ = [
    "MalConv",
    "encode",
    "convert_released_malconv_state_dict",
    "load_pretrained_malconv",
    "PRETRAINED_CONFIGS",
]


PADDING_IDX = 0


def encode(data: bytes | memoryview, max_length: Optional[int] = None) -> Tensor:
    """
    Encode the bytes of a file as MalConv's input tokens, i.e., byte b becomes token b + 1 and 0 is padding.

    Returns:
        An int64 tensor of shape (T,).
    """
    x = torch.frombuffer(bytearray(data[:max_length]), dtype=torch.uint8).to(torch.int64)
    return x + 1


class MalConv(nn.Module):
    """
    MalConv with standard memory, i.e., the gated convolution is applied to the entire input at once.

    Args:
        channels: The number of convolutional channels.
        window_size: The kernel size of the convolutions.
        stride: The stride of the convolutions.
        embd_size: The dimension of the byte embeddings.
        out_size: The number of output classes.
    """

    def __init__(self, channels: int = 128, window_size: int = 512, stride: int = 512, embd_size: int = 8, out_size: int = 2) -> None:
        super().__init__()
        self.window_size = window_size
        self.embd = nn.Embedding(257, embd_size, padding_idx=PADDING_IDX)
        self.conv_1 = nn.Conv1d(embd_size, channels, window_size, stride=stride, bias=True)
        self.conv_2 = nn.Conv1d(embd_size, channels, window_size, stride=stride, bias=True)
        self.fc_1 = nn.Linear(channels, channels)
        self.fc_2 = nn.Linear(channels, out_size)

    def embed(self, x: Tensor) -> Tensor:
        """
        Args:
            x: Input tokens of shape (B, T).
        Returns:
            Embeddings of shape (B, T', E), where inputs shorter than the window are padded up to it (T' >= T).
        """
        if x.shape[1] < self.window_size:
            # MalConv2 pads tiny inputs up to the receptive field with the padding token.
            x = F.pad(x, (0, self.window_size - x.shape[1]), value=PADDING_IDX)
        return self.embd(x)  # type: ignore[no-any-return]

    def forward_embeddings(self, z: Tensor) -> Tensor:
        """
        Args:
            z: Embeddings of shape (B, T, E), e.g., from `embed`. Useful for gradient-based explanations.
        Returns:
            Logits of shape (B, out_size).
        """
        z = z.transpose(1, 2)                                   # (B, E, T)
        g = self.conv_1(z) * torch.sigmoid(self.conv_2(z))      # (B, C, S)
        h = g.amax(dim=-1)                                      # (B, C)
        h = F.relu(self.fc_1(h))                                # (B, C)
        return self.fc_2(h)  # type: ignore[no-any-return]

    def forward(self, x: Tensor) -> Tensor:
        """
        Args:
            x: Input tokens of shape (B, T), e.g., from `encode`.
        Returns:
            Logits of shape (B, out_size).
        """
        return self.forward_embeddings(self.embed(x))


################################################################################
# Pretrained Models and State Dict Management
################################################################################


def _unwrap_state_dict(state_dict: Mapping[str, Tensor]) -> dict[str, Tensor]:
    """Remove the bookkeeping and prefixes from the AveragedModel and torch.compile wrappers."""
    return {k.removeprefix("module.").replace("_orig_mod.", ""): v for k, v in state_dict.items() if k != "n_averaged"}


def _unshard_embedding(state_dict: dict[str, Tensor], name: str) -> dict[str, Tensor]:
    """Convert a ShardedTokenEmbedding into an nn.Embedding(257, ...), since its extra rows are just copies of the first 257."""
    state_dict[f"{name}.weight"] = state_dict.pop(f"{name}.embedding.weight")[:257]
    return state_dict


def convert_released_malconv_state_dict(state_dict: Mapping[str, Tensor]) -> dict[str, Tensor]:
    """Convert a released MalConv checkpoint (from `torch.load`) into a state dict for `MalConv`."""
    state_dict = {k.removeprefix("model."): v for k, v in _unwrap_state_dict(state_dict).items()}
    return _unshard_embedding(state_dict, "embd")


# Configurations of the released models, i.e., the keyword arguments to `MalConv`.
PRETRAINED_CONFIGS: dict[str, dict[str, Any]] = {
    "medium": {"channels": 128, "window_size": 512, "stride": 512, "embd_size": 8},
}


def load_pretrained_malconv(path: Path | str, size: str = "medium") -> MalConv:
    """
    Load a released MalConv checkpoint, e.g., `release/models/malconv-medium.pt`, in evaluation mode.
    """
    model = MalConv(**PRETRAINED_CONFIGS[size])
    state_dict = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(convert_released_malconv_state_dict(state_dict))
    return model.eval()
