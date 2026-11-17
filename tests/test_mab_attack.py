"""
Tests for pipeline/5-attacks/mab-malware/mab.py: our single-threaded MAB-Malware run with its direct hand-over to the classifier makes
the same run as upstream's code handing each file over through its polled folders.

Both runs use a stand-in classifier (a fixed pseudo-random verdict per file content), so they exercise the rewriter,
the bandit, and the minimizer quickly. The tests need executables in tests/data/ (see pipeline/setup/make_fixtures.py) and are
skipped without them.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from typing import Any
from typing import Optional

import pefile
import pytest

ROOT = Path(__file__).parent.parent
from provexp.attacks.mab import checked_os  # noqa: E402
from provexp.attacks.mab import checked_system  # noqa: E402
from provexp.attacks.mab import donor_contents  # noqa: E402
from provexp.attacks.mab import trace_run  # noqa: E402

DATA = ROOT / "tests" / "data"
MALWARE = sorted(f for f in (DATA / "malware").glob("*") if f.is_file())
GOODWARE = sorted(f for f in (DATA / "goodware").glob("*") if f.is_file())


################################################################################
# Helpers
################################################################################

def needs_files() -> None:
    if len(MALWARE) < 4 or len(GOODWARE) < 4:
        pytest.skip(f"Not enough test files in {DATA.as_posix()} (see pipeline/setup/make_fixtures.py).")


def _smallest(files: list[Path], n: int) -> list[tuple[str, bytes]]:
    chosen = sorted(files, key=lambda f: f.stat().st_size)[:n]
    return [(f.name, f.read_bytes()) for f in chosen]


def _parse(data: bytes) -> Optional[pefile.PE]:
    try:
        return pefile.PE(data=data)
    except pefile.PEFormatError:
        return None


def _run(task: dict[str, Any]) -> dict[str, Any]:
    # A fresh process per run: upstream's modules read the run directory's config at import and hold global state.
    with get_context("spawn").Pool(1, maxtasksperchild=1) as pool:
        out: dict[str, Any] = pool.apply(trace_run, (task,))
    return out


################################################################################
# The hand-over
################################################################################

class TestHandOver:
    @pytest.mark.parametrize("modulus", [5, 23])
    def test_same_run_as_upstream_folders(self, tmp_path: Path, modulus: int) -> None:
        needs_files()
        donors = tmp_path / "donors"
        donor_contents(_smallest(GOODWARE, 6), donors)
        base = {"malware": _smallest(MALWARE, 5), "donor_dir": str(donors), "seed": 0, "max_pull": 15,
                "max_length": 4, "modulus": modulus}
        channel = _run({**base, "mode": "channel", "workdir": str(tmp_path / "channel")})
        folders = _run({**base, "mode": "folders", "workdir": str(tmp_path / "folders")})
        assert channel == folders
        # The run must exercise what it compares: evasions (and so the minimizer) and failed chains.
        statuses = [s["status"] for s in channel["samples"].values()]
        assert any(s["pull_count"] > 1 for s in channel["samples"].values())
        if modulus == 5:
            assert statuses.count(4) >= 2  # SAMPLE_STATUS_MINIMAL
            assert any(s["minimal"] for s in channel["samples"].values())

    def test_reproducible(self, tmp_path: Path) -> None:
        needs_files()
        donors = tmp_path / "donors"
        donor_contents(_smallest(GOODWARE, 6), donors)
        base = {"malware": _smallest(MALWARE, 3), "donor_dir": str(donors), "seed": 1, "max_pull": 10,
                "max_length": 4, "modulus": 7, "mode": "channel"}
        a = _run({**base, "workdir": str(tmp_path / "a")})
        b = _run({**base, "workdir": str(tmp_path / "b")})
        assert a == b


################################################################################
# Donor contents
################################################################################

class TestDonors:
    def test_no_empty_contents(self, tmp_path: Path) -> None:
        # An empty content would make upstream's section-append action loop forever (ArmSP.transfer).
        needs_files()
        n = donor_contents(_smallest(GOODWARE, 10), tmp_path)
        files = list(tmp_path.iterdir())
        assert n == len(files) > 0
        assert all(f.stat().st_size > 0 for f in files)
        assert all(len(f.name.split("|")) == 3 for f in files)

    def test_section_name_with_slash(self, tmp_path: Path) -> None:
        # A COFF long-name reference such as '/4' cannot go into a file name as is; upstream loses the section.
        needs_files()
        name, pe = next((n, pe) for n, d in _smallest(GOODWARE, len(GOODWARE)) if (pe := _parse(d)) and pe.sections)
        pe.sections[0].Name = b"/4\0\0\0\0\0\0"
        renamed = bytes(pe.write())
        n = donor_contents([(name, renamed)], tmp_path)
        names = sorted(f.name.split("|")[1] for f in tmp_path.iterdir())
        assert n == len(names) and "_4" in names


################################################################################
# Checked shell commands
################################################################################

class TestCheckedSystem:
    def test_success(self, tmp_path: Path) -> None:
        src, dst = tmp_path / "a", tmp_path / "b"
        src.write_bytes(b"x")
        assert checked_system(f"cp -p {src} {dst}") == 0
        assert dst.read_bytes() == b"x"

    @pytest.mark.parametrize("command", ["cp -p {d}/missing {d}/out", "mv {d}/missing {d}/out", "exit 3"])
    def test_failure_raises(self, tmp_path: Path, command: str) -> None:
        with pytest.raises(RuntimeError, match="shell command failed"):
            checked_system(command.format(d=tmp_path))

    def test_shell_not_started_is_retried(self, monkeypatch: pytest.MonkeyPatch) -> None:
        results = iter([-1, 0])
        monkeypatch.setattr("provexp.attacks.mab.os.system", lambda _: next(results))
        monkeypatch.setattr("provexp.attacks.mab.time.sleep", lambda _: None)
        assert checked_system("true") == 0

    def test_shell_never_started_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("provexp.attacks.mab.os.system", lambda _: -1)
        monkeypatch.setattr("provexp.attacks.mab.time.sleep", lambda _: None)
        with pytest.raises(RuntimeError, match="status -1"):
            checked_system("true", attempts=2)

    def test_checked_os_leaves_os_alone(self) -> None:
        import os
        module = checked_os()
        assert module.system is checked_system and os.system is not checked_system
        assert module.path is os.path
