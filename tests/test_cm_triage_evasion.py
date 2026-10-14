"""
Unit tests for the pure helper of the triage-to-a-decision experiment (scripts/cm_triage_evasion.py). The full
pipeline needs the models, the GPU, and the malware files, so it is exercised by the run script, not here.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cm_triage_evasion import Q_A  # noqa: E402
from cm_triage_evasion import Q_B  # noqa: E402
from cm_triage_evasion import evidence_shares  # noqa: E402


def test_evidence_shares_partition_As_positive_evidence() -> None:
    """The blind/oppose/agree shares are nonnegative and sum to 1 (they partition A's positive top evidence)."""
    rng = np.random.default_rng(0)
    m = 2000
    e_a = rng.normal(size=m)
    e_b = rng.normal(size=m)
    ablatable = np.ones(m, dtype=np.bool_)
    perm = rng.permutation(m).astype(np.int64)
    shares = evidence_shares(e_a, e_b, ablatable, perm)
    assert set(shares) == {"blind", "oppose", "agree"}
    assert all(s >= 0 for s in shares.values())
    assert abs(sum(shares.values()) - 1.0) < 1e-9


def test_evidence_shares_labels_by_how_B_reads_each_byte() -> None:
    """A byte in A's top set is oppose iff B is negative there and attends to it, agree iff B is positive there."""
    m = 1000
    e_a = np.zeros(m)
    e_a[:50] = 1.0  # A's evidence is on the first 50 bytes
    e_b = np.zeros(m)
    e_b[:25] = -5.0  # B strongly opposes on the first 25
    e_b[25:50] = 5.0  # B agrees on the next 25
    ablatable = np.ones(m, dtype=np.bool_)
    perm = np.arange(m, dtype=np.int64)
    shares = evidence_shares(e_a, e_b, ablatable, perm)
    # A's top Q_A*m = 10 bytes fall within [0, 25), which B opposes; B attends to the top Q_B by |evidence|.
    assert shares["oppose"] == pytest.approx(1.0)
    assert shares["agree"] == 0.0
    assert shares["blind"] == 0.0


def test_evidence_shares_nan_when_no_positive_evidence() -> None:
    e_a = -np.ones(100)
    shares = evidence_shares(e_a, np.zeros(100), np.ones(100, dtype=np.bool_), np.arange(100, dtype=np.int64))
    assert all(np.isnan(v) for v in shares.values())


def test_fractions_are_the_triage_defaults() -> None:
    assert (Q_A, Q_B) == (0.01, 0.05)
