"""
Tests for provexp.attacks.validity: the paper's rule for whether an attack's output counts.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import pickle
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
        if s is not None and s.pefile_functions and s.lief_functions:
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


def _dll_renamed(b: bytes) -> bytes:
    """The file with its first imported DLL's name changed in place (one letter): the DLL count is unchanged, but the
    original DLL is gone for every parser, as when an edit overwrites one import and another adds a DLL."""
    pe = pefile.PE(data=b)
    entry = pe.DIRECTORY_ENTRY_IMPORT[0]
    at = pe.get_offset_from_rva(entry.struct.Name)
    out = bytearray(b)
    out[at] = ord("Q") if out[at] != ord("Q") else ord("R")
    return bytes(out)


def _section_renamed(b: bytes) -> bytes:
    """The file with its first section renamed (the adaptive search's `ren`, MAB-Malware's SR)."""
    pe = pefile.PE(data=b, fast_load=True)
    at = pe.sections[0].get_file_offset()
    out = bytearray(b)
    out[at:at + 8] = b".renamed"
    return bytes(out)


def _section_moved(b: bytes) -> bytes:
    """The file with its last section's VirtualAddress moved far past the image (nothing referring to it rewritten)."""
    pe = pefile.PE(data=b, fast_load=True)
    last = pe.sections[-1]
    field = last.get_file_offset() + 12  # VirtualAddress
    out = bytearray(b)
    out[field:field + 4] = struct.pack("<I", last.VirtualAddress + 0x100000)
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

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_lost_dll_hidden_in_the_count_is_invalid(self, i: int) -> None:
        s, _ = structure(FILES[i])
        out = _dll_renamed(FILES[i])
        t, _ = structure(out)
        assert s is not None and t is not None
        assert len(t.pefile_dlls) == len(s.pefile_dlls)  # the count rule would have let it through
        why = output_invalid(s, out)
        assert why is not None and why.startswith("both: lost 1 dlls")

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_renamed_section_counts(self, i: int) -> None:
        s, _ = structure(FILES[i])
        assert s is not None
        assert output_invalid(s, _section_renamed(FILES[i])) is None

    @pytest.mark.parametrize("i", range(len(FILES)))
    def test_section_moved_in_memory_is_invalid(self, i: int) -> None:
        s, _ = structure(FILES[i])
        assert s is not None
        why = output_invalid(s, _section_moved(FILES[i]))
        assert why is not None and "sections" in why

    def test_lost_section_hidden_by_an_added_one_is_invalid(self) -> None:
        # The original as read, with one section's address replaced by one the file does not have: the count is the
        # same, the set is not.
        s, _ = structure(FILES[0])
        assert s is not None
        ghost = max(s.pefile_sections) + 0x100000
        original = replace(s, pefile_sections=(*s.pefile_sections[1:], ghost),
                           lief_sections=(*s.lief_sections[1:], ghost))
        why = output_invalid(original, FILES[0])
        assert why == f"both: lost 1 sections (0x{ghost:x})"

    def test_structure_pickles(self) -> None:
        s, _ = structure(FILES[0])
        assert s is not None and pickle.loads(pickle.dumps(s)) == s


class TestUnreadable:

    def test_readable(self) -> None:
        assert unreadable(FILES[0]) is None

    @pytest.mark.parametrize("data", [b"", b"MZ" + b"\x00" * 62, b"not a PE at all" * 10])
    def test_garbage(self, data: bytes) -> None:
        why = unreadable(data)
        assert why is not None and why.startswith("both")
