"""
PE-aware ablation for the faithfulness experiments (E1): which bytes of a PE file must not be ablated, and checks that
an ablated file still parses with the same layout.

This is experiment code, not part of the framework. Ablating (zeroing) the bytes that tell the parser where everything
else is, e.g., e_lfanew or the section table's offsets, does not remove the evidence those bytes carry; it makes the
parser fail or reinterpret the rest of the file, and every PE feature changes at once. The protected header fields are
chosen empirically (scripts/discover_protected_fields.py): those whose zeroing alone makes pefile fail or changes the
layout in a non-negligible fraction of files (PROTECTED_FIELDS), plus, for each file, the fields whose zeroing breaks
that file (`breaking_fields`), because PE files can be strange (e.g., overlapping DOS and PE headers). An experiment
protects a file with `protect`, which also checks that ablating every unprotected byte at once keeps the file intact,
and checks every ablated file with `verify`.
"""

from __future__ import annotations
from functools import cache
import json
from pathlib import Path
from typing import Literal
from typing import NamedTuple
from typing import Optional

import numpy as np
from numpy import typing as npt
import pefile

from provexp.featuresets.ember2024.features import field_range


__all__ = [
    "LAYOUT_FIELDS",
    "PROTECTED_FIELDS",
    "TYPICAL_VALUES_FILE",
    "HeaderFill",
    "HeaderField",
    "Layout",
    "Parse",
    "Protection",
    "breaking_fields",
    "header_fields",
    "layout",
    "parse",
    "protect",
    "protected_mask",
    "typical_values",
    "verify",
]


# Fields that define the layout (see Layout): zeroing them makes the parser drop or reinterpret whole sections, which
# does not remove the evidence they carry. Protected by definition.
LAYOUT_FIELDS: frozenset[str] = frozenset({
    "IMAGE_DOS_HEADER.e_magic",
    "IMAGE_DOS_HEADER.e_lfanew",
    "IMAGE_NT_HEADERS.Signature",
    "IMAGE_FILE_HEADER.NumberOfSections",
    "IMAGE_FILE_HEADER.SizeOfOptionalHeader",
    "IMAGE_SECTION_HEADER.VirtualAddress",
    "IMAGE_SECTION_HEADER.PointerToRawData",
    "IMAGE_SECTION_HEADER.SizeOfRawData",
})

# Header fields that ablation must not touch in any file, as "{structure}.{field}" (see header_fields): the layout
# fields plus the fields whose zeroing breaks at least 1% of files in scripts/discover_protected_fields.py.
PROTECTED_FIELDS: frozenset[str] = LAYOUT_FIELDS

# The most common value of each header field in a sample of training files (scripts/header_typical_values.py).
TYPICAL_VALUES_FILE = Path(__file__).parent / "header_typical_values.json"

# How ablation fills header fields: with zeros, or with the field's most common value in training files. Zeros in fields
# such as ImageBase or Subsystem are values no real file has, and the model may react to the value itself rather than
# to the evidence being removed.
HeaderFill = Literal["zeros", "typical"]


################################################################################
# Parsing
################################################################################


class Layout(NamedTuple):
    """What tells the parser where everything else in the file is."""

    e_lfanew: int
    num_sections: int
    section_table: int
    sections: tuple[tuple[int, int], ...]  # (PointerToRawData, SizeOfRawData) of each section


class Parse(NamedTuple):
    """
    The outcome of parsing a file the way the feature extractor does.

    Attributes:
        status: "ok"; "not_pe" if pefile raises PEFormatError or AttributeError (the extractor then sets is_pe = 0);
            or "crash" if pefile raises anything else (the extractor would raise too).
        layout: The layout, if the file parsed.
        pe: The parsed file, if it parsed.
    """

    status: str
    layout: Optional[Layout]
    pe: Optional[pefile.PE]


def layout(pe: pefile.PE) -> Layout:
    """The layout of a parsed file."""
    return Layout(
        e_lfanew=int(pe.DOS_HEADER.e_lfanew),
        num_sections=len(pe.sections),
        section_table=int(pe.sections[0].get_file_offset()) if pe.sections else -1,
        sections=tuple((int(s.PointerToRawData), int(s.SizeOfRawData)) for s in pe.sections),
    )


def parse(data: bytes, fast_load: bool = False) -> Parse:
    """
    Parse a file the way the feature extractor does (`pefile.PE(data=...)`, a full load by default).
    """
    try:
        pe = pefile.PE(data=data, fast_load=fast_load)
    except (pefile.PEFormatError, AttributeError):
        return Parse("not_pe", None, None)
    except Exception:
        return Parse("crash", None, None)
    try:
        return Parse("ok", layout(pe), pe)
    except Exception:
        return Parse("crash", None, pe)


################################################################################
# Header Fields
################################################################################


class HeaderField(NamedTuple):
    """A field of a header structure and its byte range [lo, hi) in the file."""

    key: str
    lo: int
    hi: int


def header_fields(pe: pefile.PE) -> list[HeaderField]:
    """
    Every field of the DOS header, the NT signature, the file and optional headers, the data directories, and the
    section headers, keyed as "{structure}.{field}", e.g., "IMAGE_DIRECTORY_ENTRY_IMPORT.Size". Aliased fields (e.g.,
    Misc and Misc_VirtualSize) appear once, under their first name.
    """
    structures: list[pefile.Structure] = [pe.DOS_HEADER, pe.NT_HEADERS, pe.FILE_HEADER]
    if getattr(pe, "OPTIONAL_HEADER", None) is not None:
        structures.append(pe.OPTIONAL_HEADER)
        structures.extend(getattr(pe.OPTIONAL_HEADER, "DATA_DIRECTORY", []))
    structures.extend(pe.sections)

    fields = []
    for structure in structures:
        # The 32- and 64-bit optional headers share keys; each data directory keeps its own (e.g., the import table).
        name = "IMAGE_OPTIONAL_HEADER" if structure.name == "IMAGE_OPTIONAL_HEADER64" else structure.name
        seen = set()
        for field in structure.__field_offsets__:
            if structure.name == "IMAGE_NT_HEADERS" and field != "Signature":
                continue
            lo, hi = field_range(structure, field)
            if (lo, hi) in seen:
                continue
            seen.add((lo, hi))
            fields.append(HeaderField(f"{name}.{field}", lo, hi))
    return fields


def protected_mask(pe: pefile.PE, size: int, fields: frozenset[str] = PROTECTED_FIELDS) -> npt.NDArray[np.bool_]:
    """
    Which bytes of a parsed file of `size` bytes must not be ablated: the bytes of every protected header field.
    """
    mask = np.zeros(size, dtype=np.bool_)
    for field in header_fields(pe):
        if field.key in fields:
            mask[max(field.lo, 0):min(field.hi, size)] = True
    return mask


def breaking_fields(data: bytes, original: Optional[Parse] = None) -> list[tuple[HeaderField, Parse]]:
    """
    Zero each header field of a file alone and parse the result. Returns every field whose zeroing makes pefile fail
    or changes the layout, with the outcome. Fields that are already zero are skipped.
    """
    original = parse(data) if original is None else original
    if original.status != "ok" or original.pe is None:
        raise ValueError(f"The file does not parse (status {original.status}).")
    broken = []
    for field in header_fields(original.pe):
        lo, hi = max(field.lo, 0), min(field.hi, len(data))
        if hi <= lo or not any(data[lo:hi]):
            continue
        result = parse(data[:lo] + bytes(hi - lo) + data[hi:])
        if result.status != "ok" or result.layout != original.layout:
            broken.append((field, result))
    return broken


################################################################################
# Protection and Verification
################################################################################


class Protection(NamedTuple):
    """
    How a file may be ablated.

    Attributes:
        mask: Which bytes must not be ablated, shape (m,).
        header: Which bytes belong to a header field, shape (m,). Ablation fills these with `header_values`, never
            with random bytes: random values in fields such as FileAlignment or a section's VirtualSize make pefile
            drop sections.
        header_values: The value each header byte takes when ablated, shape (m,) (zero outside the header).
        layout: The file's layout, which every ablated file must keep.
        fields: The protected fields (global and file-specific).
        file_fields: The fields protected only because they break this file.
    """

    mask: npt.NDArray[np.bool_]
    header: npt.NDArray[np.bool_]
    header_values: npt.NDArray[np.uint8]
    layout: Layout
    fields: frozenset[str]
    file_fields: frozenset[str]


def protect(data: bytes, fields: frozenset[str] = PROTECTED_FIELDS, per_file: bool = True, header: HeaderFill = "zeros") -> Protection:
    """
    Determine which bytes of a file must not be ablated, and check that ablating all the others keeps it intact.

    Args:
        data: The file.
        fields: The globally protected fields.
        per_file: Whether to also protect the fields whose zeroing alone breaks this file (about one full parse per
            header field).
        header: How ablation fills header fields (see HeaderFill).

    Returns:
        The protection.

    Raises:
        ValueError: If the file does not parse, or if ablating every unprotected byte at once breaks it.
    """
    original = parse(data)
    if original.status != "ok" or original.pe is None or original.layout is None:
        raise ValueError(f"The file does not parse (status {original.status}).")
    file_fields = frozenset(f.key for f, _ in breaking_fields(data, original)) - fields if per_file else frozenset()
    m = len(data)
    in_header = np.zeros(m, dtype=np.bool_)
    values = np.zeros(m, dtype=np.uint8)
    typical = typical_values() if header == "typical" else {}
    for field in header_fields(original.pe):
        lo, hi = max(field.lo, 0), min(field.hi, m)
        in_header[lo:hi] = True
        if field.key in typical and hi > lo:
            values[lo:hi] = np.frombuffer(typical[field.key].ljust(field.hi - field.lo, b"\x00")[lo - field.lo:hi - field.lo], dtype=np.uint8)
    mask = protected_mask(original.pe, m, fields | file_fields)
    protection = Protection(mask, in_header, values, original.layout, fields | file_fields, file_fields)
    buffer = np.frombuffer(data, dtype=np.uint8)
    ablated = np.where(mask, buffer, np.where(in_header, values, 0)).astype(np.uint8).tobytes()
    problem = verify(protection, data, ablated)
    if problem is not None:
        raise ValueError(f"Ablating every unprotected byte breaks the file: {problem}.")
    return protection


@cache
def typical_values(path: Path = TYPICAL_VALUES_FILE) -> dict[str, bytes]:
    """The most common value of each header field in training files, as raw bytes."""
    if not path.exists():
        raise FileNotFoundError(f"{path.as_posix()} does not exist; run scripts/header_typical_values.py.")
    table = json.loads(path.read_text())
    return {key: bytes.fromhex(entry["value"]) for key, entry in table["fields"].items()}


def verify(protection: Protection, data: bytes, ablated: bytes, is_pe: Optional[float] = None) -> Optional[str]:
    """
    Check an ablated file: its protected bytes are unchanged, it parses as the feature extractor parses it, its layout
    is unchanged, and, if given, the extracted is_pe feature is 1.

    Returns:
        None if the ablated file is intact, otherwise a description of the problem.
    """
    if len(ablated) != len(data):
        return f"length changed from {len(data)} to {len(ablated)}"
    original = np.frombuffer(data, dtype=np.uint8)
    changed = np.frombuffer(ablated, dtype=np.uint8) != original
    if np.any(changed & protection.mask):
        return f"{int((changed & protection.mask).sum())} protected bytes changed"
    if is_pe is not None and is_pe != 1:
        return f"is_pe = {is_pe}"
    result = parse(ablated)
    if result.status != "ok":
        return f"parse status {result.status}"
    if result.layout != protection.layout:
        return "layout changed"
    return None
