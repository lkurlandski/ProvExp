"""
Direction A, Table A1's adaptive column (docs/direction-A-A1-design.md): a soundness test for our monotone detectors.

FOR ACADEMIC SECURITY RESEARCH ONLY. This is a defense-evaluation harness. A sound monotone detector (the C4 rows)
carries a guarantee: no loader-safe edit in the threat model M (docs/direction-A-threat-model.md, Section 1) can lower
its score. This script checks that guarantee on our own pilot samples against our own detectors, by trying the edits M
allows and recording whether any lowers the score. For a C4 row the expected result is "no edit helps" (0 by
construction, Gimenez Prop. 1 + C4 + A1-A4); a decrease below -1e-6 is an A1-A4 bug to debug against Table A0, not an
evasion. For the PV-seen row, which is sound only against the attacks it was built from, the same search realizes the
hole check 2 measured. Nothing is deployed; files are written only so their features can be re-extracted and re-scored.

This first part provides the material (goodware donors) and the loader-safe edits; the search over them is added next.
Each edit returns the new bytes and a description. Every edit keeps the original content in place -- each section's raw
data, the overlay, the DOS header and stub, and the header fields it does not itself set -- so the edit stays inside M
and does not exploit the writing tool's layout choices (A4); `lief_preserves` checks this for the LIEF edits.

Usage: see the search driver added in the next step.
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys
from typing import Any

import pefile

from provexp.featuresets.ember2024.features import field_range

sys.path.insert(0, str(Path(__file__).parent))
# (the search driver, added next, will import THREAT_MODELS and the C1 predictors)

__all__ = ["Donors", "HDR_FIELDS", "add_imports", "add_section", "lief_preserves", "rename_section",
           "set_header_fields", "zero_directory_entry"]

ROOT = Path(__file__).resolve().parent.parent

# The loader-ignored header fields (the threat model's `hdr`, matching scripts/a_directions.py's `header` group).
HDR_FIELDS = (("FILE_HEADER", "TimeDateStamp"), ("FILE_HEADER", "NumberOfSymbols"),
              ("FILE_HEADER", "PointerToSymbolTable"), ("OPTIONAL_HEADER", "MajorImageVersion"),
              ("OPTIONAL_HEADER", "MinorImageVersion"), ("OPTIONAL_HEADER", "MajorLinkerVersion"),
              ("OPTIONAL_HEADER", "MinorLinkerVersion"), ("OPTIONAL_HEADER", "MajorOperatingSystemVersion"),
              ("OPTIONAL_HEADER", "MinorOperatingSystemVersion"))
DEBUG_ENTRY, SECURITY_ENTRY = 6, 4


################################################################################
# Donors: goodware material the edits draw on (as the GAMMA attacks do)
################################################################################

class Donors:
    """Section names and contents, DOS stubs, header-field values, checksums, and imports taken from the goodware."""

    def __init__(self, goodware: list[tuple[str, bytes]]) -> None:
        self.sections: list[tuple[str, bytes, int]] = []
        self.stubs: list[bytes] = []
        self.fields: list[dict[str, int]] = []
        self.checksums: list[int] = []
        self.imports: list[tuple[str, list[str]]] = []
        for _, data in goodware:
            try:
                pe = pefile.PE(data=data)
            except Exception:
                continue
            for s in pe.sections:
                body = s.get_data()[:65536]
                if body:
                    self.sections.append((s.Name.rstrip(b"\x00").decode(errors="ignore"), body, int(s.Characteristics)))
            self.stubs.append(data[2:pe.DOS_HEADER.e_lfanew])
            self.fields.append({f"{h}.{f}": int(getattr(getattr(pe, h), f)) for h, f in HDR_FIELDS})
            self.checksums.append(int(pe.OPTIONAL_HEADER.CheckSum))
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
                names = [i.name.decode() for i in entry.imports if i.name]
                if names:
                    self.imports.append((entry.dll.decode(), names[:20]))
        if not (self.sections and self.stubs and self.imports):
            raise RuntimeError("The donor pool has no sections, stubs, or imports.")


################################################################################
# In-place byte edits (loader-ignored fields; no parse change, no length change)
################################################################################

def _overwrite(data: bytes, lo: int, content: bytes) -> bytes:
    """`data` with `content` written at offset `lo`, keeping the length (content must fit)."""
    if lo + len(content) > len(data):
        raise ValueError("The content does not fit at this offset.")
    return data[:lo] + content + data[lo + len(content):]


def _pack_field(structure: Any, field: str, value: int) -> tuple[int, bytes]:
    """The file offset of a pefile structure field and `value` packed to its width (little-endian)."""
    lo, hi = field_range(structure, field)
    fmt = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}[hi - lo]
    return lo, struct.pack(fmt, value & ((1 << (8 * (hi - lo))) - 1))


def set_header_fields(data: bytes, pe: pefile.PE, values: dict[str, int]) -> bytes:
    """Set the loader-ignored header fields (`HDR_FIELDS`) to `values` (keyed "STRUCT.field"); in place."""
    out = data
    for (struct_name, field), key in zip(HDR_FIELDS, (f"{h}.{f}" for h, f in HDR_FIELDS)):
        lo, packed = _pack_field(getattr(pe, struct_name), field, values[key])
        out = _overwrite(out, lo, packed)
    return out


def set_checksum(data: bytes, pe: pefile.PE, value: int) -> bytes:
    """Set OPTIONAL_HEADER.CheckSum to `value`; in place (the loader does not verify it for non-drivers)."""
    lo, packed = _pack_field(pe.OPTIONAL_HEADER, "CheckSum", value)
    return _overwrite(data, lo, packed)


def zero_directory_entry(data: bytes, pe: pefile.PE, index: int) -> bytes:
    """Zero a data-directory entry's RVA and size (e.g. DEBUG or SECURITY): removes the feature, keeps the length."""
    entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[index]
    out = _overwrite(data, entry.get_file_offset(), b"\x00" * 8)
    return out


def overwrite_dos_stub(data: bytes, pe: pefile.PE, stub: bytes) -> bytes:
    """
    Overwrite the DOS header fields [2, 60) and the stub [64, e_lfanew) with `stub`, keeping e_magic ("MZ", [0, 2))
    and e_lfanew ([60, 64)) so the PE header is still located (the threat model's `dos` operation).
    """
    lfanew = pe.DOS_HEADER.e_lfanew
    room = (60 - 2) + max(0, lfanew - 64)
    content = (stub + b"\x00" * room)[:room]
    out = _overwrite(data, 2, content[:58])
    if lfanew > 64 and len(content) > 58:
        out = _overwrite(out, 64, content[58:])
    return out


################################################################################
# Structural edits via LIEF (add a section / imports, rename a section)
################################################################################

def _characteristics(code: bool) -> int:
    """A section's characteristics: executable code, or readable/writable initialized data."""
    import lief

    c = lief.PE.Section.CHARACTERISTICS
    if code:
        return int(c.MEM_READ.value | c.MEM_EXECUTE.value | c.CNT_CODE.value)
    return int(c.MEM_READ.value | c.MEM_WRITE.value | c.CNT_INITIALIZED_DATA.value)


def add_section(data: bytes, name: str, content: bytes, code: bool) -> bytes:
    """Add a section with the given name, content, and kind (via LIEF), returning the rewritten file."""
    import lief

    pe = lief.PE.parse(list(data))
    if pe is None:
        raise RuntimeError("LIEF could not parse the file.")
    section = lief.PE.Section(name[:8])
    section.content = list(content)
    section.characteristics = _characteristics(code)
    pe.add_section(section)
    return bytes(pe.write_to_bytes())


def add_imports(data: bytes, library: str, functions: list[str]) -> bytes:
    """Add an import of `functions` from `library` (via LIEF), returning the rewritten file."""
    import lief

    pe = lief.PE.parse(list(data))
    if pe is None:
        raise RuntimeError("LIEF could not parse the file.")
    lib = pe.add_import(library)
    for function in functions:
        lib.add_entry(function)
    config = lief.PE.Builder.config_t()
    config.imports = True
    config.overlay = True
    return bytes(pe.write_to_bytes(config))


def rename_section(data: bytes, index: int, name: str) -> bytes:
    """Rename the section at `index` to `name` (<= 8 bytes), in place -- an overwrite of the name field."""
    pe = pefile.PE(data=data)
    if index >= len(pe.sections):
        raise ValueError(f"The file has only {len(pe.sections)} sections.")
    offset = pe.sections[index].get_file_offset()
    return _overwrite(data, offset, (name.encode()[:8].ljust(8, b"\x00")))


def lief_preserves(original: bytes, edited: bytes, op: str) -> bool:
    """
    Whether a LIEF edit kept the file inside the threat model: the original section bodies, the overlay, the DOS
    header and stub, and (for add-section / add-imports) the original sections' names are all still present unchanged.

    LIEF may relayout the file (A4); M only sanctions the declared change, so an edit that moved or rewrote existing
    content is rejected and not counted. The check is conservative: it requires every original section's data to
    appear verbatim in the edited file and the DOS stub to be byte-identical.
    """
    try:
        a, b = pefile.PE(data=original), pefile.PE(data=edited)
    except Exception:
        return False
    if edited[:2] != b"MZ" or original[2:original.find(b"PE\x00\x00")] not in edited:
        return False
    edited_bodies = {bytes(s.get_data()) for s in b.sections}
    for s in a.sections:
        body = bytes(s.get_data())
        if body and not any(body in eb for eb in edited_bodies):
            return False
    if op != "ren":
        edited_names = {s.Name for s in b.sections}
        if not all(s.Name in edited_names for s in a.sections):
            return False
    return True
