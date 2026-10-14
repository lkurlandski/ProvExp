"""
Unit tests for the pure helpers of the audit's test-time mitigation (scripts/audit_mitigate.py). The full pipeline
needs MalConv and the malware files, so it is exercised by the run script, not here.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit_mitigate import defended_fields  # noqa: E402
from audit_mitigate import detection_threshold  # noqa: E402
from audit_mitigate import zero_fields  # noqa: E402


################################################################################
# Defense
################################################################################


class TestZeroFields:

    def test_zeroes_only_the_runs_of_the_given_features(self) -> None:
        data = bytes(range(1, 21))
        runs = {0: [(2, 3)], 1: [(10, 2), (15, 1)], 2: [(18, 2)]}
        out = zero_fields(data, runs, [0, 1], max_content=256)
        assert len(out) == len(data)
        zeroed = {2, 3, 4, 10, 11, 15}
        assert all((out[i] == 0) == (i in zeroed) for i in range(len(data)))

    def test_skips_features_too_large_to_locate(self) -> None:
        data = bytes(range(1, 21))
        assert zero_fields(data, {0: [(0, 10)]}, [0], max_content=8) == data


class TestDetectionThreshold:

    @pytest.mark.parametrize("fpr", [0.0, 0.01, 0.1, 0.5])
    def test_flags_at_most_fpr(self, fpr: float) -> None:
        benign = np.random.default_rng(0).normal(size=1000)
        t = detection_threshold(benign, fpr)
        assert (benign > t).mean() <= fpr

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError):
            detection_threshold(np.array([]))


def test_defended_fields_keep_only_attacker_changeable_fields() -> None:
    confirmed = ["header:optional_header_CheckSum", "header:optional_header_ImageBase", "datadirectories:import_virtual_address"]
    assert defended_fields(confirmed) == ["header:optional_header_CheckSum", "header:optional_header_ImageBase"]
