"""
Which clause of the population check a file fails (incomplete or unusual layout), whether files pass the precondition,
and the overrun-section test.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from typing import Any
from typing import Optional

import pefile

from provexp.data.files import FileReader
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import DOS_HEADER_SIZE
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.catalogue import precondition
from provexp.featuresets.ember2024.catalogue import section_table_end
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import section_data_range

__all__ = ["LAYOUT", "PAST_END", "clauses", "has_overrun_section", "population"]


################################################################################
# The clauses
################################################################################


LAYOUT = ["vrange_beyond_image", "image_too_large", "lfanew_in_dos", "section_in_headers", "table_past_headers",
          "overlay_at_directory"]
PAST_END = ["item_past_end", "directory_past_end", "section_past_end"]


def _align_up(x: int, a: int) -> int:
    return (x + a - 1) // a * a if a else x


def clauses(z: bytes, extractor: PEFeatureExtractor) -> dict[str, Any]:
    """
    Each clause of `catalogue.precondition` on one file, mirroring `plain_layout` and `precondition` clause by clause.

    Args:
        z: The file's bytes.
        extractor: The instrumented extractor (for the item table's locating ranges).

    Returns:
        One row: a bool per clause (True: the clause fails), context, and the category.
    """
    try:
        pe = pefile.PE(data=z)
    except (pefile.PEFormatError, AttributeError) as e:
        return {"parses": False, "error": repr(e), "category": "not parsing", "in_population": False}
    table = extractor.item_table(z)
    oh = pe.OPTIONAL_HEADER
    sa = oh.SectionAlignment or 0x1000
    sections = list(pe.sections)
    n = len(pe.__data__)
    row: dict[str, Any] = {"parses": True, "error": None, "length": n}
    row["vrange_beyond_image"] = any(
        s.VirtualAddress + (s.Misc_VirtualSize or s.SizeOfRawData) > oh.SizeOfImage for s in sections)
    need = max([s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in sections] + [oh.SizeOfHeaders])
    row["image_too_large"] = oh.SizeOfImage > _align_up(need, sa)
    e_lfanew = pe.DOS_HEADER.e_lfanew
    row["lfanew_in_dos"] = e_lfanew < DOS_HEADER_SIZE
    row["section_in_headers"] = any(s.SizeOfRawData and section_data_range(s)[0] < e_lfanew for s in sections)
    row["table_past_headers"] = section_table_end(pe) > oh.SizeOfHeaders
    overlay = pe.get_overlay_data_start_offset()
    row["overlay_at_directory"] = False
    if overlay is not None:
        ends = [s.PointerToRawData + s.SizeOfRawData for s in sections if s.PointerToRawData + s.SizeOfRawData <= n]
        row["overlay_at_directory"] = overlay > max(ends + [oh.get_file_offset() + pe.FILE_HEADER.SizeOfOptionalHeader])
    groups = sorted({item.group for item in table.items for _, hi in item.locating if hi > n})
    row["item_past_end"] = bool(groups)
    row["groups_past_end"] = ",".join(groups)
    directories = []
    for i, d in enumerate(oh.DATA_DIRECTORY):
        if d.VirtualAddress and d.Size:
            data = ((d.VirtualAddress, d.VirtualAddress + d.Size),) if i == SECURITY_ENTRY else rva_ranges(pe, d.VirtualAddress, d.Size)
            if any(hi > n for _, hi in data):
                directories.append(str(d.name).replace("IMAGE_DIRECTORY_ENTRY_", ""))
    row["directory_past_end"] = bool(directories)
    row["directories_past_end"] = ",".join(directories)
    row["section_past_end"] = any(s.PointerToRawData + s.SizeOfRawData > n for s in sections)
    row["max_section_end"] = max([s.PointerToRawData + s.SizeOfRawData for s in sections] + [0])
    row["in_population"] = precondition(pe, table)
    incomplete = any(row[k] for k in PAST_END)
    unusual = any(row[k] for k in LAYOUT)
    if row["in_population"] == (incomplete or unusual):
        raise RuntimeError(f"The clauses disagree with catalogue.precondition ({row}).")
    row["category"] = "population" if row["in_population"] else "incomplete" if incomplete else "unusual layout"
    return row


################################################################################
# The precondition over many files
################################################################################


_W: dict[str, Any] = {}


def _init(db: Optional[str]) -> None:
    """One worker's reader (the file store, or the SimpleDB `db`) and extractor."""
    if db is None:
        _W["read"] = FileReader().get
    else:
        reader = SimpleDBReader(SimpleDB(Path(db), check=False))
        _W["read"] = lambda name: bytes(reader.get(name).data)
    _W["extractor"] = fix_quirks(PEFeatureExtractor())


def _precondition(name: str) -> tuple[str, bool]:
    return name, bool(passes_precondition(_W["extractor"], _W["read"](name)))


def population(names: list[str], workers: int, db: Optional[Path] = None) -> dict[str, bool]:
    """
    Whether each training file passes the precondition (the population of the plain layouts).

    Args:
        names: The files.
        workers: Processes.
        db: None reads the files from the file store (the scale-up; all of them must be there, checked first); a
            SimpleDB directory reads them from it, one shard decompressed per file (the pilot's files only, which the
            store does not hold).

    Returns:
        {name: passes}.
    """
    if db is None:
        FileReader().check(names)
    with get_context("spawn").Pool(workers, initializer=_init, initargs=(None if db is None else str(db),)) as pool:
        return dict(pool.map(_precondition, names, chunksize=8))


################################################################################
# Sections past the end
################################################################################


def has_overrun_section(pe: pefile.PE) -> bool:
    """True if any section's declared raw data runs past the end of the file.

    Such a section's content is clamped by the file length, so appending bytes extends it: its contribution depends
    on |z| (an A2 locality failure the model flags rather than predicts).
    """
    return any(s.PointerToRawData + s.SizeOfRawData > len(pe.__data__) for s in pe.sections)
