"""
Tests for provexp.attacks.validity: the paper's rule for whether an attack's output counts.
"""

from __future__ import annotations

from pathlib import Path
import struct

import pefile
import pytest

from provexp.attacks.validity import output_invalid
from provexp.attacks.validity import structure
from provexp.attacks.validity import unreadable

DATA = Path(__file__).parent / "data" / "malware"


def _with_imports() -> list[bytes]:
    """Fixture malware both parsers read and that import at least one function."""
    if not DATA.exists():
        return []
    out = []
    for p in sorted(DATA.iterdir()):
        b = p.read_bytes()
        s, _ = structure(b)
        if s is not None and s.pefile_functions > 0 and s.lief_functions > 0:
            out.append(b)
    return out[:3]


FILES = _with_imports()
pytestmark = pytest.mark.skipif(not FILES, reason="no fixture malware in tests/data (pipeline/setup/make_fixtures.py)")


def _import_directory_zeroed(b: bytes) -> bytes:
    """The file with its import directory entry set to (0, 0): the import table is gone for every parser."""
    pe = pefile.PE(data=b, fast_load=True)
    entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
    out = bytearray(b)
    out[entry.get_file_offset():entry.get_file_offset() + 8] = struct.pack("<II", 0, 0)
    return bytes(out)


################################################################################
# The rule
################################################################################


class TestOutputInvalid:

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_unchanged_counts(self, i: int) -> None:
        s, _ = structure(FILES[i])
        assert s is not None
        assert output_invalid(s, FILES[i]) is None

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_appended_bytes_count(self, i: int) -> None:
        s, _ = structure(FILES[i])
        assert s is not None
        assert output_invalid(s, FILES[i] + b"\x00" * 4096) is None

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_padding_before_mz_is_invalid_for_both(self, i: int) -> None:
        # secml-malware's shift bug (session 85): padding written in front of the MZ header.
        s, _ = structure(FILES[i])
        assert s is not None
        why = output_invalid(s, b"\x00" * 512 + FILES[i])
        assert why is not None and why.startswith("both")

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_lost_imports_are_invalid(self, i: int) -> None:
        s, _ = structure(FILES[i])
        assert s is not None
        why = output_invalid(s, _import_directory_zeroed(FILES[i]))
        assert why is not None and "lost" in why and "dlls" in why


class TestUnreadable:

    def test_readable(self) -> None:
        assert unreadable(FILES[0]) is None

    @pytest.mark.parametrize("data", [b"", b"MZ" + b"\x00" * 62, b"not a PE at all" * 10])
    def test_garbage(self, data: bytes) -> None:
        why = unreadable(data)
        assert why is not None and why.startswith("both")
