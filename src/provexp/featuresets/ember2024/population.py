"""
Which clause of the population check a file fails (incomplete or unusual layout), whether files pass the precondition,
and the overrun-section test.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from typing import Any

import pefile

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import DOS_HEADER_SIZE
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.catalogue import precondition
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import section_data_range

__all__ = ["LAYOUT", "PAST_END", "clauses", "has_overrun_section", "population"]


################################################################################
# The clauses
################################################################################


LAYOUT = ["vrange_beyond_image", "image_too_large", "lfanew_in_dos", "section_in_headers", "overlay_at_directory"]
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


def _init(db: str) -> None:
    _W["reader"] = SimpleDBReader(SimpleDB(Path(db), check=False))
    _W["extractor"] = merge_import_descriptors(PEFeatureExtractor())


def _precondition(name: str) -> tuple[str, bool]:
    data = bytes(_W["reader"].get(name).data)
    return name, bool(passes_precondition(_W["extractor"], data))


def population(names: list[str], db: Path, workers: int) -> dict[str, bool]:
    """Whether each training file passes the precondition (the population of the plain layouts)."""
    with get_context("spawn").Pool(workers, initializer=_init, initargs=(str(db),)) as pool:
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
