"""
Tests for models/malconv.py.
"""

from pathlib import Path

import pytest
import torch
from torch.nn import functional as F

from provexp.models.malconv import MalConv
from provexp.models.malconv import convert_released_malconv_state_dict
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv


ROOT = Path(__file__).parent.parent
CHECKPOINT = ROOT / "checkpoints" / "malconv-medium.pt"
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())


def test_encode() -> None:
    assert encode(b"\x00\x01\xff").tolist() == [1, 2, 256]
    assert encode(b"\x00\x01\xff", max_length=2).tolist() == [1, 2]


def test_forward_shapes() -> None:
    model = MalConv(channels=4, window_size=8, stride=4, embd_size=3).eval()
    x = torch.randint(1, 257, (2, 37))
    assert model(x).shape == (2, 2)
    # Inputs shorter than the window are padded up to it.
    assert model(x[:, :5]).shape == (2, 2)
    assert torch.equal(model(x[:, :5]), model(F.pad(x[:, :5], (0, 3))))


def test_forward_embeddings_matches_forward() -> None:
    model = MalConv(channels=4, window_size=8, stride=4, embd_size=3).eval()
    x = torch.randint(1, 257, (2, 37))
    assert torch.equal(model(x), model.forward_embeddings(model.embed(x)))


def test_convert_released_malconv_state_dict() -> None:
    if not CHECKPOINT.exists():
        pytest.skip(f"{CHECKPOINT.as_posix()} not found.")
    state_dict = convert_released_malconv_state_dict(torch.load(CHECKPOINT, map_location="cpu", weights_only=True))
    assert state_dict["embd.weight"].shape == (257, 8)
    assert set(state_dict) == set(MalConv().state_dict())


def test_pretrained_predictions() -> None:
    """The pretrained model should separate the malware and goodware fixtures reasonably well."""
    if not CHECKPOINT.exists():
        pytest.skip(f"{CHECKPOINT.as_posix()} not found.")
    if not FILES:
        pytest.skip(f"No test files found in {DATA.as_posix()}.")
    model = load_pretrained_malconv(CHECKPOINT)
    correct = 0
    with torch.no_grad():
        for f in FILES:
            p = model(encode(f.read_bytes()).unsqueeze(0)).softmax(dim=-1)[0, 1].item()
            correct += int((p >= 0.5) == (f.parent.name == "malware"))
    assert correct / len(FILES) >= 0.75
