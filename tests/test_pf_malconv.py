"""
Unit tests for the pure helper of the pushforward-on-MalConv experiment (scripts/pf_malconv.py). The full pipeline
needs MalConv, the GPU, and the malware files, so it is exercised by the run script, not here.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

from provexp.boxmatrix import BoxMatrix
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pf_malconv import NUM_RANDOM  # noqa: E402
from pf_malconv import feature_explanations  # noqa: E402


################################################################################
# Feature Explanations
################################################################################


def _provenance() -> Provenance:
    """A byte histogram over 100 bytes: feature j is the count of byte value j (16 values)."""
    data = np.random.default_rng(0).integers(0, 16, size=100).astype(np.uint8)
    C = BoxMatrix((100, 16))
    C.add_keyed_boxes(0, 100, 0, C.add_key(data))
    return Provenance(C)


class TestFeatureExplanations:

    def test_keys_and_shapes(self) -> None:
        prov = _provenance()
        out = feature_explanations(prov, np.ones(100), np.zeros(16), np.random.default_rng(0))
        assert set(out) == {"pushforward", "surrogate", *(f"random_feat:{r}" for r in range(NUM_RANDOM))}
        assert all(a.shape == (16,) for a in out.values())

    def test_pushforward_conserves_the_bytes_attribution(self) -> None:
        """Every byte is read by one feature, so the pushforward hands each feature exactly its bytes' IG."""
        prov = _provenance()
        ig = np.random.default_rng(1).normal(size=100)
        a = feature_explanations(prov, ig, np.zeros(16), np.random.default_rng(0))["pushforward"]
        assert a.sum() == pytest.approx(ig.sum())

    @pytest.mark.parametrize("ig_size,surrogate_size", [(99, 16), (100, 15)])
    def test_rejects_wrong_shapes(self, ig_size: int, surrogate_size: int) -> None:
        with pytest.raises(ValueError):
            feature_explanations(_provenance(), np.ones(ig_size), np.zeros(surrogate_size), np.random.default_rng(0))
