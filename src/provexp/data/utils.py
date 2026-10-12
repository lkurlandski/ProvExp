"""
Utilities.
"""

import torch
from torch import Tensor


def encode_sha256_tensor(shas: list[str]) -> Tensor:
    return torch.tensor([s.encode("latin1") for s in shas], dtype=torch.uint8)


def decode_sha256_tensor(shas: Tensor) -> list[str]:
    return [s.tobytes().decode('utf-8') for s in shas.numpy(force=True)]
