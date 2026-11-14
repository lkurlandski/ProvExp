"""
Single field writes outside the threat model that can take a file out of the population (R7's escapes): each takes the
parsed file and its length and returns the written file, or None where it does not apply.
"""

from __future__ import annotations

from typing import Callable
from typing import Optional

import pefile

from provexp.featuresets.ember2024.catalogue import DEBUG_ENTRY
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY

__all__ = ["ARCH_ENTRY", "WRITES", "arch_entry", "cert_entry", "debug_entry", "image_size", "overlay_entry", "raw_size"]


ARCH_ENTRY = 7


def _entry(pe: pefile.PE, i: int, va: int, size: int) -> bytes:
    """The file with data directory entry `i` set to (va, size)."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[i]
    d.VirtualAddress, d.Size = va, size
    return bytes(pe.write())


def cert_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The certificate entry extended (or, if absent, placed) past the end of the file."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[SECURITY_ENTRY]
    if d.VirtualAddress and d.Size:
        return _entry(pe, SECURITY_ENTRY, d.VirtualAddress, d.Size + n)
    return _entry(pe, SECURITY_ENTRY, n, 8)


def debug_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The debug entry extended (or, if absent, placed) past the end of the file."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[DEBUG_ENTRY]
    if d.VirtualAddress and d.Size:
        return _entry(pe, DEBUG_ENTRY, d.VirtualAddress, d.Size + 2 * n)
    return _entry(pe, DEBUG_ENTRY, max(pe.OPTIONAL_HEADER.SizeOfImage, n), 28)


def arch_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The reserved architecture entry pointed past the end of the file and past the image."""
    if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= ARCH_ENTRY:
        return None
    return _entry(pe, ARCH_ENTRY, max(pe.OPTIONAL_HEADER.SizeOfImage, n), 8)


def image_size(pe: pefile.PE, n: int) -> Optional[bytes]:
    """SizeOfImage raised by one SectionAlignment."""
    pe.OPTIONAL_HEADER.SizeOfImage += pe.OPTIONAL_HEADER.SectionAlignment or 0x1000
    return bytes(pe.write())


def overlay_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The architecture entry pointed at the overlay's first 16 bytes (as an address in no section)."""
    start = pe.get_overlay_data_start_offset()
    if start is None or n - start < 16 or len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= ARCH_ENTRY:
        return None
    if any(s.VirtualAddress <= start < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in pe.sections):
        return None
    return _entry(pe, ARCH_ENTRY, start, 16)


def raw_size(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The section whose raw data ends last made to extend past the end of the file (control)."""
    if not pe.sections:
        return None
    s = max(pe.sections, key=lambda s: s.PointerToRawData + s.SizeOfRawData)
    fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200
    s.SizeOfRawData += ((n - (s.PointerToRawData + s.SizeOfRawData)) // fa + 1) * fa
    return bytes(pe.write())


WRITES: dict[str, Callable[[pefile.PE, int], Optional[bytes]]] = {
    "cert_entry": cert_entry,
    "debug_entry": debug_entry,
    "arch_entry": arch_entry,
    "image_size": image_size,
    "overlay_entry": overlay_entry,
    "raw_size": raw_size,
}
