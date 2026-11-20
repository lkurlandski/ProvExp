"""
Byte-level edits that do exactly the declared operation and nothing else (the catalogue's writers, `catalogue.write_*`,
wrapped), and the in-place writes of data directory entries. Shared by the catalogue checks and the attacks.
"""

from __future__ import annotations

import struct
from typing import Callable
from typing import Optional

import pefile

from provexp.featuresets.ember2024.catalogue import DEBUG_ENTRY
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import write_gap
from provexp.featuresets.ember2024.catalogue import write_header_growth
from provexp.featuresets.ember2024.catalogue import write_imports
from provexp.featuresets.ember2024.catalogue import write_section
from provexp.reach import ByteEdit

__all__ = ["CODE_CHARACTERISTICS", "DATA_CHARACTERISTICS", "IMPORT_ENTRY", "add_imports", "add_section", "entry_write",
           "forged_rich", "grow_headers", "in_section", "insert_gap", "into_overlay", "past_end"]


SCN_CODE, SCN_DATA = 0x00000020, 0x00000040
SCN_EXECUTE, SCN_READ, SCN_WRITE = 0x20000000, 0x40000000, 0x80000000
DATA_CHARACTERISTICS = SCN_DATA | SCN_READ | SCN_WRITE
CODE_CHARACTERISTICS = SCN_CODE | SCN_READ | SCN_EXECUTE
IMPORT_ENTRY = 1


def add_section(z: bytes, name: bytes, content: bytes, characteristics: int, before_overlay: bool,
                content_at_rva: Optional[Callable[[int], bytes]] = None) -> Optional[tuple[bytes, int]]:
    """
    Add a section (`sec`; `catalogue.write_section`): a header after the section table, the content padded to
    FileAlignment at the end of the file or (`before_overlay`) where pefile's overlay starts.

    Returns:
        The edited file and the new section's RVA, or None if the headers have no room for another section header.
    """
    written = write_section(z, name, content, characteristics, before_overlay, content_at_rva)
    return None if written is None else (written.new, written.layout["rva"])


def add_imports(z: bytes, library: bytes, functions: list[bytes], before_overlay: bool) -> Optional[bytes]:
    """Add imports (`imp`; `catalogue.write_imports`): a new section holding the import table, pointed to by IMPORT."""
    written = write_imports(z, library, functions, before_overlay)
    return None if written is None else written.new


def insert_gap(z: bytes, at_pe_header: bool, gap: bytes) -> Optional[bytes]:
    """Insert a gap (`ext` before the PE header, `shf` before the first section's data; `catalogue.write_gap`)."""
    written = write_gap(z, at_pe_header, gap)
    return None if written is None else written.new


def grow_headers(z: bytes, gap: bytes) -> Optional[bytes]:
    """Grow the headers (`hgr`; `catalogue.write_header_growth`): a gap at SizeOfHeaders, which rises with it."""
    written = write_header_growth(z, gap)
    return None if written is None else written.new


def forged_rich(pairs: list[tuple[int, int]], key: int = 0x5EED5EED) -> bytes:
    """A Rich header block (DanS, padding, (comp.id, count) pairs, Rich, key), XOR-ed with `key`."""
    words = [0x536E6144 ^ key, key, key, key]
    for comp, count in pairs:
        words += [comp ^ key, count ^ key]
    return struct.pack(f"<{len(words)}I", *words) + b"Rich" + struct.pack("<I", key)


def entry_write(pe: pefile.PE, index: int, va: int, size: int) -> ByteEdit:
    """The in-place write of data directory entry `index` as (va, size)."""
    lo = pe.OPTIONAL_HEADER.DATA_DIRECTORY[index].get_file_offset()
    return ByteEdit(lo, lo + 8, struct.pack("<II", va, size))


def in_section(pe: pefile.PE, rva: int) -> bool:
    return any(s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in pe.sections)


def past_end(pe: pefile.PE, index: int, n: int, by: int) -> Optional[ByteEdit]:
    """
    Entry `index` made to end `by` bytes past the end of the file: its extent lengthened if it has one, else placed at
    an address that maps to the file's last bytes (outside every section, so pefile maps it one to one); None if
    neither applies or the file has no entry `index` (NumberOfRvaAndSizes <= index; 24 of the 2,000 evaluation files
    declare fewer than 16 entries).
    """
    if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= index:
        return None
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[index]
    if d.VirtualAddress and d.Size:
        try:
            start = d.VirtualAddress if index == SECURITY_ENTRY else pe.get_offset_from_rva(d.VirtualAddress)
        except pefile.PEFormatError:
            return None
        if start is None or start >= n:
            return None
        return entry_write(pe, index, d.VirtualAddress, n + by - start)
    va = max(n - 8, 0)
    if index != SECURITY_ENTRY and in_section(pe, va):
        return None
    return entry_write(pe, index, va, n + by - va)


def into_overlay(pe: pefile.PE, n: int) -> Optional[ByteEdit]:
    """
    The debug extent lengthened (from its address, or the first section's) to end one byte before the end of a file
    with an overlay: pefile's own overlay rule would then start the overlay at the file's last byte (LIEF's, installed
    by `features` since 2026-11-13, leaves it where it was; R7). None without an overlay.
    """
    if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= DEBUG_ENTRY:
        return None
    start = pe.get_overlay_data_start_offset()
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[DEBUG_ENTRY]
    va = d.VirtualAddress if d.VirtualAddress else (pe.sections[0].VirtualAddress if pe.sections else 0)
    try:
        lo = pe.get_offset_from_rva(va)
    except pefile.PEFormatError:
        return None
    if start is None or n - start < 2 or lo is None or lo >= n - 1:
        return None
    return entry_write(pe, DEBUG_ENTRY, va, n - 1 - lo)
