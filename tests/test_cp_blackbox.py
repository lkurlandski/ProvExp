"""
Tests for CP.3's comparison of the instrumented and black-box provenance through their statistics
(scripts/cp_blackbox.py).
"""

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cp_blackbox import compare  # noqa: E402


def stats_for(files: int = 3) -> dict[str, np.ndarray]:
    """Two subsets of two features: `a` agrees exactly, `b` differs; feature 3 is never attributable."""
    H = np.tile([1.0, 2.0, 0.5, 0.0], (files, 1))
    O = np.tile([0.1, 0.2, 0.3, 0.0], (files, 1))
    return {
        "tv": np.tile([0.0, 0.0, 0.4, np.nan], (files, 1)),
        "attributable": np.tile([True, True, True, False], (files, 1)),
        "estimated": np.tile([True, True, True, True], (files, 1)),
        "ambiguity_instrumented": H, "ambiguity_blackbox": H + np.array([0.0, 0.0, 0.7, 0.0]),
        "overlap_instrumented": O, "overlap_blackbox": O + np.array([0.0, 0.05, 0.1, 0.0]),
    }


def test_agreement_per_subset() -> None:
    table = compare(stats_for(), np.array(["a", "a", "b", "b"])).to_dicts()
    rows = {r["subset"]: r for r in table}
    assert rows["a"]["pairs"] == 6 and rows["b"]["pairs"] == 3  # feature 3 is excluded: not attributable
    assert rows["a"]["ambiguity agrees"] == 1.0 and rows["b"]["ambiguity agrees"] == 0.0
    # Overlap can differ although the column agrees (feature 1): it depends on the other features through D.
    assert rows["a"]["overlap agrees"] == 0.5 and rows["a"]["overlap agrees where tv = 0"] == 0.5
    assert rows["all"]["pairs"] == 9


def test_rejects_a_run_without_the_statistics() -> None:
    stats = stats_for()
    del stats["overlap_blackbox"]
    with pytest.raises(ValueError):
        compare(stats, np.array(["a", "a", "b", "b"]))
