"""
Tests for featuresets/ember2024/attack.py, on the test fixtures (real PE files) and a tiny MalConv.
"""

from pathlib import Path
import warnings

import numpy as np
import pytest
import torch

from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.attack import attack_malconv
from provexp.featuresets.ember2024.attack import editable_region
from provexp.featuresets.ember2024.attack import region_parts
from provexp.models.malconv import MalConv
from provexp.models.malconv import encode


warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "tests" / "data"
FILES = sorted(f for f in DATA.glob("*/*") if f.is_file())
PE_FILES = [f for f in FILES if parse(f.read_bytes()).status == "ok"]
# The attack runs MalConv on whole files, so its per-file tests use the smallest few to stay light.
SMALL_PE_FILES = sorted(PE_FILES, key=lambda f: f.stat().st_size)[:3]


def needs_files() -> None:
    if not PE_FILES:
        pytest.skip(f"No PE test files found in {DATA.as_posix()} (see scripts/make_fixtures.py).")


@pytest.fixture(scope="module", params=PE_FILES, ids=[f.name[:16] for f in PE_FILES])
def data(request: pytest.FixtureRequest) -> bytes:
    return Path(request.param).read_bytes()


@pytest.fixture(scope="module", params=SMALL_PE_FILES, ids=[f.name[:16] for f in SMALL_PE_FILES])
def small_data(request: pytest.FixtureRequest) -> bytes:
    return Path(request.param).read_bytes()


class TestEditableRegion:
    def test_not_pe_is_empty(self) -> None:
        assert region_parts(b"not a pe file") == {}
        assert not editable_region(b"not a pe file").any()

    def test_region_within_file(self, data: bytes) -> None:
        needs_files()
        mask = editable_region(data)
        assert mask.shape == (len(data),)
        for ranges in region_parts(data).values():
            for lo, hi in ranges:
                assert 0 <= lo < hi <= len(data)

    def test_region_excludes_e_magic_and_e_lfanew(self, data: bytes) -> None:
        needs_files()
        mask = editable_region(data)
        # e_magic (0:2) and e_lfanew (0x3C:0x40) are read by the loader, never edited.
        assert not mask[0:2].any()
        assert not mask[0x3C:0x40].any()

    def test_region_is_loader_safe(self, small_data: bytes) -> None:
        """Rewriting the whole editable region keeps the file parsing with an unchanged layout."""
        needs_files()
        mask = editable_region(small_data)
        if not mask.any():
            pytest.skip("No editable bytes in this file.")
        rng = np.random.default_rng(0)
        perturbed = np.frombuffer(small_data, dtype=np.uint8).copy()
        perturbed[mask] = rng.integers(0, 256, size=int(mask.sum()), dtype=np.uint8)
        protection = protect(small_data, header="typical")
        assert verify(protection, small_data, perturbed.tobytes()) is None

    def test_region_disjoint_from_protected_header(self, small_data: bytes) -> None:
        """The editable region does not touch the layout-defining header bytes the deletion operator protects."""
        needs_files()
        mask = editable_region(small_data)
        # The section table and headers the protection marks must stay fixed; the stub/slack sit elsewhere.
        protection = protect(small_data, header="typical")
        assert not (mask & protection.mask).any()


class TestAttack:
    @staticmethod
    @pytest.fixture(scope="class")
    def model() -> MalConv:
        torch.manual_seed(0)
        m = MalConv(channels=4, window_size=8, stride=8, embd_size=4)
        return m.double().eval()

    def test_runs_and_stays_loader_safe(self, model: MalConv, small_data: bytes) -> None:
        needs_files()
        result = attack_malconv(model, small_data, threshold=-1e9, max_iterations=3, per_iteration=16)
        assert len(result.data) == len(small_data)
        assert result.queries >= 1
        # Only editable bytes changed, and the file still verifies.
        assert not (result.changed & ~editable_region(small_data)).any()
        protection = protect(small_data, header="typical")
        assert verify(protection, small_data, result.data) is None

    def test_no_editable_bytes_returns_input(self, model: MalConv) -> None:
        result = attack_malconv(model, b"not a pe", max_iterations=5)
        assert result.data == b"not a pe"
        assert result.iterations == 0

    def test_lowers_score(self, small_data: bytes) -> None:
        """A model that simply sums embeddings is driven down by the gradient step."""
        needs_files()
        if not editable_region(small_data).any():
            pytest.skip("No editable bytes in this file.")
        torch.manual_seed(1)
        model = MalConv(channels=4, window_size=8, stride=8, embd_size=4).double().eval()
        result = attack_malconv(model, small_data, threshold=-1e9, max_iterations=10, per_iteration=64)
        assert result.log_odds <= result.log_odds_0 + 1e-6

    def test_deterministic(self, model: MalConv, small_data: bytes) -> None:
        needs_files()
        a = attack_malconv(model, small_data, threshold=-1e9, max_iterations=3)
        b = attack_malconv(model, small_data, threshold=-1e9, max_iterations=3)
        assert a.data == b.data and a.log_odds == b.log_odds
