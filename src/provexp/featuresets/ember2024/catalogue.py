"""
The edit catalogue: the threat model's operations as item operations on EMBER's item table (docs/item-layer-design.md,
component 3; docs/direction-A-threat-model.md, Section 1).

Each operation maps the item table of a file z and a parameter value to the edited file (or its declared layout) and
the item delta, which the C1 engine (provexp.reach) turns into the new sums and features. Operations that write bytes
in place or append are stated as byte edits, and the engine derives their delta through the recognizers; structural
operations declare their delta. The catalogue is PE-specific and is the threat model, so it stays with the
experiment code; the model (provexp.items, provexp.reach) stays generic.
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import replace
import struct
from typing import Optional

import pefile

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import SectionInfo
from provexp.featuresets.ember2024.features import clipped
from provexp.featuresets.ember2024.features import entropy_H
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import section_data_range
from provexp.featuresets.ember2024.features import section_locating
from provexp.featuresets.ember2024.features import structure_range
from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Range
from provexp.items import Term
from provexp.items import feature_hash
from provexp.reach import BOTH
from provexp.reach import UP
from provexp.reach import ByteEdit
from provexp.reach import Change
from provexp.reach import ChangeHow
from provexp.reach import Entry
from provexp.reach import KindProfile
from provexp.reach import Prediction
from provexp.reach import Signs
from provexp.reach import meets
from provexp.reach import moved
from provexp.reach import predict_declared
from provexp.reach import predict_structural
from provexp.reach import region_changes

__all__ = [
    "add_section",
    "CONTENT_KINDS",
    "BODY_KINDS",
    "PAST_END_KINDS",
    "REGION_OPS",
    "regions",
    "file_region_changes",
    "declared_changes",
    "plain_layout",
    "precondition",
    "passes_precondition",
    "Written",
    "new_section_slot",
    "write_section",
    "write_imports",
    "write_gap",
    "write_rename",
    "write_zero_entry",
    "predict_add_section",
    "predict_add_imports",
    "predict_insert_gap",
    "predict_rename",
    "predict_zero_entry",
]


################################################################################
# Helpers
################################################################################


def _group(extractor: PEFeatureExtractor, name: str) -> object:
    for fe in extractor.features:
        if fe.name == name:
            return fe
    raise KeyError(f"The extractor has no feature type {name!r}.")


def _tagged(items: Sequence[Item], group: str) -> list[Item]:
    for item in items:
        item.group = item.group or group
    return list(items)


################################################################################
# Declared structural operations
################################################################################


def add_section(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, name: str, content: bytes, props: Sequence[str]) -> Prediction:
    """
    Add a section (`sec`): a new section item with the given name, raw content, and characteristics.

    The declared layout puts the content at the end of the file (as Table A0's predictor does, run 79), so the file's
    byte items, windows, and length grow as for an append, and the content's strings are its own (the tool pads around
    the section). The section item gets raw and virtual size len(content), the content's entropy, and the
    characteristics; the COFF NumberOfSections rises by one. The section's raw data then ends the file, so pefile's
    overlay rule finds no overlay: an old overlay's bytes stay in the file but no longer form the overlay (G7, finding
    4). What the declaration does not fix is the tool's layout: the section-table entry, alignment padding,
    SizeOfImage, and any directory it moves. Those are assumption A4 and show up as the residual against the tool's
    output.

    Args:
        extractor: The extractor whose item table `table` is.
        table: The item table of z.
        z: The file.
        name: The section name (at most 8 bytes).
        content: The section's raw content.
        props: Its characteristics, as pefile names without the IMAGE_SCN_ prefix (e.g., "MEM_READ").

    Returns:
        The prediction for the declared layout.
    """
    n = len(z)
    new = z + content
    append = ByteEdit(n, n, content)
    removed: list[Item] = []
    added: list[Item] = []

    # The content's bytes and windows, as appended.
    for group in ("general", "histogram", "byteentropy"):
        if any(fe.name == group for fe in extractor.features):
            r, a = _group(extractor, group).recognize(table.of_group(group), z, new, append)  # type: ignore[attr-defined]
            removed += r
            added += _tagged(a, group)

    # The content's own strings.
    strings = _group(extractor, "strings")
    added += _tagged(strings._string_items(new, n, n + len(content)), "strings")  # type: ignore[attr-defined]

    # The section, the file's length, and the section count.
    section: SectionInfo = _group(extractor, "section")  # type: ignore[assignment]
    file_items = [item for item in table.of_group("section") if item.kind == "file"]
    if file_items:
        s = {
            "name": name.strip("\x00").lower(),
            "size": len(content),
            "vsize": len(content),
            "entropy": entropy_H(content),
            "vsize_ratio": len(content) / max(len(content), 1),
            "props": list(props),
        }
        data: tuple[Range, ...] = ((n, n + len(content)),) if content else ()
        ranges: dict[str, tuple[Range, ...]] = {"table": (), "name": (), "size": (), "vsize": (), "props": (), "data": data}
        removed += file_items
        removed += [item for item in table.of_group("section") if item.kind == "overlay"]
        added += _tagged([section._file_item(len(new), file_items[0].locating), section.section_item(s, ranges, file_items[0].locating)], "section")
    for item in table.of_group("header"):
        if item.attrs.get("field") == "NumberOfSections":
            (term,) = item.terms
            removed.append(item)
            added += _tagged([replace(item, terms=(replace(term, value=term.value + 1),))], "header")

    return predict_declared(table, new, removed, added)


################################################################################
# C4: the operations as item changes over their domains
################################################################################


# NOTE: C4 (provexp.reach.directions) needs each operation as abstract item changes over its whole domain (any file,
# any parameter value), not one concrete edit. The in-place operations are derived from the bytes they write on each
# file (`regions`, through provexp.reach.region_changes, unioned over a corpus); the structural ones are declared here
# (`declared_changes`). The declared deltas are provisional until the catalogue's step 6 checks them against
# re-extraction (G7); they follow docs/direction-A-threat-model.md, Section 1, and name the anticipated
# disagreements of docs/item-layer-design.md where the hand rules disagree.

# The kinds recognized from content wherever it lies, and what an in-place write anywhere does to them: byte counts
# and windows get new values (the number of bytes stays), strings may appear, disappear, merge, or split.
CONTENT_KINDS: dict[str, ChangeHow] = {"bytes": "rewrite", "window": "rewrite", "string": "flag"}

# The same content restricted to the body regions (provexp.featuresets.ember2024.sums): the kinds of the re-encoded
# groups, located through the section table and the overlay rule. In-place writes reach them only through their
# members or locating ranges, like the parsed kinds.
BODY_KINDS = ("body_bytes", "body_window", "body_string")

# The (group, kind) pairs located through pointers that can lie past the end of the file (sections, directory
# addresses, the certificate table's offset, a header cut by the end): appending can complete them. Strict C4 flags
# them under append; the precondition row excludes the files where any locating range lies past the end.
PAST_END_KINDS = (
    ("section", "section"), ("section", "file"), ("section", "overlay"), ("section", "entry"),
    ("imports", "import"), ("imports", "library"), ("exports", "export"),
    ("datadirectories", "relocs"), ("datadirectories", "field"), ("header", "field"),
    ("authenticode", "certificate_table"),
    ("body_histogram", "body_bytes"), ("body_byteentropy", "body_window"), ("body_strings", "body_string"),
    ("section_split", "section"),
)

# The loader-ignored header fields (`hdr`; scripts/a1_adaptive.py, HDR_FIELDS).
HDR_FIELDS = (
    ("FILE_HEADER", "TimeDateStamp"), ("FILE_HEADER", "NumberOfSymbols"), ("FILE_HEADER", "PointerToSymbolTable"),
    ("OPTIONAL_HEADER", "MajorImageVersion"), ("OPTIONAL_HEADER", "MinorImageVersion"),
    ("OPTIONAL_HEADER", "MajorLinkerVersion"), ("OPTIONAL_HEADER", "MinorLinkerVersion"),
    ("OPTIONAL_HEADER", "MajorOperatingSystemVersion"), ("OPTIONAL_HEADER", "MinorOperatingSystemVersion"),
)
DEBUG_ENTRY, SECURITY_ENTRY = 6, 4
DOS_HEADER_SIZE = 64

# The operations derived from the bytes they write: (zero content, the change of kinds whose locating ranges they
# write, whether the write keeps every item's location, changes added whenever it writes a locating range).
REGION_OPS: dict[str, tuple[bool, dict[str, ChangeHow], bool, tuple[Change, ...]]] = {
    "slk": (False, {}, False, ()),
    "dos": (False, {}, False, ()),
    "hdr": (False, {}, False, ()),
    "chk": (False, {}, False, ()),
    # Renaming rewrites the name in the section table, which locates every section; the declared part: it changes
    # neither which sections exist nor where (pefile's plausibility checks do not read names).
    "ren": (False, {}, True, ()),
    # Removing debug removes one extent from pefile's overlay rule, so the overlay can only start earlier: it grows,
    # or one appears; the file's length stays. On a file where the debug directory is not the extent the overlay starts
    # after, nothing moves (`file_region_changes`).
    "rdb": (True, {"overlay": "grow", "file": "rewrite"}, False, (Change("add", "overlay"),)),
    # Removing the signature removes the certificate table.
    "rsg": (True, {"certificate_table": "remove"}, False, ()),
}


# The kinds whose bytes the loader reads wherever they lie (import, export, and relocation data, the signature).
LOADED_KINDS = ("import", "library", "export", "relocs", "certificate_table")


def _mapped(section: pefile.SectionStructure) -> int:
    """The raw bytes of a section the loader maps: up to its virtual size, or all of them when that is zero."""
    vsize, raw = int(section.Misc_VirtualSize), int(section.SizeOfRawData)
    return min(vsize, raw) if vsize > 0 else raw


def regions(pe: pefile.PE, z: bytes, table: ItemTable) -> dict[str, tuple[Range, ...]]:
    """
    The bytes each in-place operation writes on the file (its domain on this file, with any content). NOTE: slack and
    the DOS region are restricted to bytes the loader ignores (domain knowledge inside the experiment, as for the
    loader-safe edit rules): both exclude the headers past the DOS header, other sections' mapped data, directory data,
    and the bytes of the `LOADED_KINDS` items (a section's raw data or the DOS stub can hold them), and the DOS region
    ends where the PE header starts (it can start inside the DOS header).
    """
    n = len(z)
    e_lfanew = int(pe.DOS_HEADER.e_lfanew)
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    read: list[Range] = [r for item in table.items if item.kind in LOADED_KINDS for r in item.members + item.locating]
    holes = list(read)
    read.append((0, int(pe.OPTIONAL_HEADER.SizeOfHeaders)))
    read += [(s.PointerToRawData, s.PointerToRawData + _mapped(s)) for s in pe.sections]
    read += [r for i, d in enumerate(directories) if i != SECURITY_ENTRY and d.VirtualAddress and d.Size for r in rva_ranges(pe, d.VirtualAddress, d.Size)]
    if len(directories) > SECURITY_ENTRY and directories[SECURITY_ENTRY].Size:
        d = directories[SECURITY_ENTRY]
        read.append((d.VirtualAddress, d.VirtualAddress + d.Size))
    slack: list[Range] = []
    for s in pe.sections:
        lo = s.PointerToRawData + _mapped(s)
        hi = min(s.PointerToRawData + s.SizeOfRawData, n)
        if hi > lo:
            slack += cut([(lo, hi)], read)
    return {
        "slk": tuple(slack),
        "dos": tuple(cut(clipped(n, [(2, min(0x3C, e_lfanew)), (0x40, e_lfanew)]), holes)),
        "hdr": tuple(field_range(getattr(pe, h), f) for h, f in HDR_FIELDS),
        "chk": (field_range(pe.OPTIONAL_HEADER, "CheckSum"),),
        "ren": tuple(field_range(s, "Name") for s in pe.sections),
        "rdb": (structure_range(directories[DEBUG_ENTRY]),) if len(directories) > DEBUG_ENTRY else (),
        "rsg": (structure_range(directories[SECURITY_ENTRY]),) if len(directories) > SECURITY_ENTRY else (),
    }


def cut(ranges: Sequence[Range], holes: Sequence[Range]) -> list[Range]:
    """The ranges without the elements of the holes."""
    out = list(ranges)
    for a, b in holes:
        out = [r for lo, hi in out for r in ((lo, min(hi, a)), (max(lo, b), hi)) if r[1] > r[0]]
    return out


def overlay_start_without(pe: pefile.PE, entry: int) -> Optional[int]:
    """Where pefile's overlay would start with one data directory entry zeroed (`get_overlay_data_start_offset`)."""
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[entry]
    saved = directory.VirtualAddress, directory.Size
    directory.VirtualAddress, directory.Size = 0, 0
    try:
        start: Optional[int] = pe.get_overlay_data_start_offset()
    finally:
        directory.VirtualAddress, directory.Size = saved
    return start


def file_region_changes(pe: pefile.PE, z: bytes, table: ItemTable) -> dict[str, set[Change]]:
    """The changes each in-place operation makes on one file (union them over a corpus)."""
    out: dict[str, set[Change]] = {}
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    for op, region in regions(pe, z, table).items():
        zero, declared, keep, extra = REGION_OPS[op]
        if op == "rdb" and len(directories) > DEBUG_ENTRY:
            # Zeroing the debug entry is one edit with no parameter: whether it moves the overlay's start is decided on
            # the file. Where it does not, everything located through pefile's overlay rule keeps its place.
            keep = overlay_start_without(pe, DEBUG_ENTRY) == pe.get_overlay_data_start_offset()
        t = table if not keep else ItemTable(table.num_elements, table.families, [replace(item, locating=()) for item in table.items])
        out[op] = set(region_changes(t, region, CONTENT_KINDS, zero=zero, declared=declared))
        if any(meets(item.locating, r) for item in t.items for r in region):
            out[op].update(extra)
    return out


def _fields(profiles: Mapping[tuple[str, str], KindProfile], group: str, names: Sequence[str], signs: Signs) -> tuple[tuple[Entry, Signs], ...]:
    """Signs for the entries the named fields of a group write."""
    p = profiles[(group, "field")]
    missing = [f for f in names if f not in p.fields]
    if missing:
        raise KeyError(f"No recorded {group} fields {missing}.")
    return tuple((e, signs) for f in names for e in sorted(p.fields[f]))


def declared_changes(profiles: Mapping[tuple[str, str], KindProfile], regex_monotone: Sequence[bool], strict: bool) -> dict[str, list[Change]]:
    """
    The declared operations (append, add a section, add imports, the two insertions) as item changes.

    Args:
        profiles: The kinds' vocabulary (to resolve field names to entries).
        regex_monotone: Per regex index, whether a string that matches it still does when extended
            (provexp.reach.extension_monotone).
        strict: Whether lengthening the file (appending, adding a section or imports, inserting a gap) may complete
            structures past its end (strict C4); without, the precondition row's files, where no locating range lies
            past the end.

    Returns:
        The changes per operation.
    """
    content = [Change("add", k) for k in CONTENT_KINDS]
    # The content an append, an added section, or a section shift brings is body (a new region, or the extension of
    # the unclaimed run it follows: the run that ends the file, or one before the first section's data); a DOS
    # extension's gap is not (it lies below SizeOfHeaders). (Only for an extractor with the re-encoded groups.)
    groups = {g for g, _ in profiles}
    sums = bool(groups & set(SUMS_GROUPS))
    regex = tuple((("strings:regex", j), UP if mono else BOTH) for j, mono in enumerate(regex_monotone))
    body_regex = tuple((("body_strings:regex", j), s) for (_, j), s in regex)
    body = [Change("add", k) for k in BODY_KINDS] if sums else []
    # An unclaimed run extends at its end (its existing windows, full by construction, stay), and so does its
    # trailing string.
    body_grow = [Change("grow", "body_bytes"), Change("grow", "body_string", entries=body_regex)] if sums else []
    # Structural operations also write the header in place (a table entry, counts, pointers).
    in_place = [Change(how, k) for k, how in CONTENT_KINDS.items()]
    sizes_up = _fields(profiles, "header", ["NumberOfSections", "SizeOfImage", "SizeOfCode", "SizeOfInitializedData", "SizeOfUninitializedData"], UP)
    # The certificate table's offset is a file offset: content inserted before it raises it.
    security_up = Change("modify", "field", group="datadirectories", families=frozenset(), entries=_fields(profiles, "datadirectories", ["IMAGE_DIRECTORY_ENTRY_SECURITY.VirtualAddress"], UP))
    # Every operation that lengthens the file can complete a structure located past its old end (strict only; G7).
    past_end = [Change("flag", kind, group=group) for group, kind in PAST_END_KINDS if group in groups] if strict else []
    insertion = content + in_place + past_end + [
        # The gap's content joins the file; every window after it is re-tiled, and strings can merge across it.
        Change("flag", "window"),
        Change("grow", "file"),
        security_up,
    ]
    app = content + body + [
        # A file shorter than two windows is one window, which every append changes.
        Change("modify", "window"),
        # The trailing string, if the file ends in printable bytes, extends.
        Change("grow", "string", entries=regex),
        Change("grow", "file"),
        Change("grow", "overlay"),
        Change("add", "overlay"),
    ]
    app += body_grow + past_end
    sec = content + body + body_grow + in_place + past_end + [
        Change("add", "section"),
        Change("grow", "file"),
        # Placed before the overlay (as LIEF places it), the content moves the overlay and the certificate table in it.
        security_up,
        # Placed after it, the section claims the file's end: pefile's overlay rule finds no overlay (G7), and the old
        # overlay's bytes become a gap between sections (still body; padding up to FileAlignment extends it).
        Change("remove", "overlay"),
        Change("modify", "field", group="header", families=frozenset(), entries=sizes_up),
        # Anticipated disagreement: when no section contains the entry point, the first executable section is the
        # entry section, and an added one can become it.
        Change("modify", "entry"),
    ]
    imp = sec + [
        Change("add", "import"),
        Change("add", "library"),
        # The import directory moves to the new section.
        Change("modify", "field", group="datadirectories", families=frozenset(), entries=_fields(
            profiles, "datadirectories", [f"IMAGE_DIRECTORY_ENTRY_{d}.{a}" for d in ("IMPORT", "IAT") for a in ("VirtualAddress", "Size")], BOTH)),
    ]
    ext = insertion + [
        Change("modify", "field", group="header", families=frozenset(), entries=_fields(profiles, "header", ["e_lfanew", "SizeOfHeaders"], UP)),
        # Anticipated disagreement: pefile searches for the Rich header up to the optional header, so the gap's
        # content can create, change, or end one.
        Change("flag", "rich_pair"),
    ]
    return {"app": app, "sec": sec, "imp": imp, "ext": ext, "shf": insertion + body + body_grow}


def _align_up(x: int, a: int) -> int:
    return (x + a - 1) // a * a if a else x


def plain_layout(pe: pefile.PE) -> bool:
    """
    The layout clauses of the precondition (run 104, G7): the file's layout is one in which the operations move only what
    the catalogue declares. Each clause excludes a layout where they move more, witnessed on the 2,000-file set:
        - every section's virtual range lies within SizeOfImage (the loader rejects the others; pefile's RVA mapping
          then shifts exports and relocations with the file layout);
        - SizeOfImage is at most what the sections need, aligned (adding a section and recomputing it, as tools do,
          would otherwise lower it);
        - the headers hold only the headers: the PE header starts past the DOS header, and no section's raw data starts
          before the PE header (writing or moving header fields would otherwise move DOS fields or that section);
        - pefile's overlay starts where a section's raw data (or the optional header) ends, not at the end of a data
          directory's declared extent (a section inserted there would split an unclaimed body run).
    """
    oh = pe.OPTIONAL_HEADER
    sa = oh.SectionAlignment or 0x1000
    sections = list(pe.sections)
    if any(s.VirtualAddress + (s.Misc_VirtualSize or s.SizeOfRawData) > oh.SizeOfImage for s in sections):
        return False
    need = max([s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in sections] + [oh.SizeOfHeaders])
    if oh.SizeOfImage > _align_up(need, sa):
        return False
    e_lfanew = pe.DOS_HEADER.e_lfanew
    if e_lfanew < DOS_HEADER_SIZE or any(s.SizeOfRawData and section_data_range(s)[0] < e_lfanew for s in sections):
        return False
    overlay = pe.get_overlay_data_start_offset()
    if overlay is not None:
        n = len(pe.__data__)
        ends = [s.PointerToRawData + s.SizeOfRawData for s in sections if s.PointerToRawData + s.SizeOfRawData <= n]
        if overlay > max(ends + [oh.get_file_offset() + pe.FILE_HEADER.SizeOfOptionalHeader]):
            return False
    return True


def precondition(pe: pefile.PE, table: ItemTable) -> bool:
    """
    The precondition row's check, made at inference: nothing the parse is located through lies past the end of the
    file, so appending cannot complete any structure. No item has a locating range past the end, and no data directory
    (including one whose data pefile could not read, which has no items) or section extends past it. And the layout is
    plain (`plain_layout`).
    """
    if not plain_layout(pe):
        return False
    n = len(pe.__data__)
    if any(hi > n for item in table.items for _, hi in item.locating):
        return False
    for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
        if d.VirtualAddress and d.Size:
            data = ((d.VirtualAddress, d.VirtualAddress + d.Size),) if i == SECURITY_ENTRY else rva_ranges(pe, d.VirtualAddress, d.Size)
            if any(hi > n for _, hi in data):
                return False
    return all(s.PointerToRawData + s.SizeOfRawData <= n for s in pe.sections)


def passes_precondition(extractor: PEFeatureExtractor, z: bytes) -> bool:
    """`precondition` from the bytes: False for a file that does not parse as a PE (it has no guarantee either)."""
    try:
        pe = pefile.PE(data=z)
    except (pefile.PEFormatError, AttributeError):
        return False
    return precondition(pe, extractor.item_table(z))


################################################################################
# The item-stated operations, written and declared exactly (Table 5)
################################################################################

# NOTE: these are the operations of scripts/catalogue_checks.py (G7), written by our own byte-level edits, which do
# exactly the operation and nothing else (no relayout, unlike LIEF; assumption A4). Each `write_*` returns the byte
# edits that perform it, in order; each `predict_*` writes the operation and declares its item delta: the items it
# adds, removes, or modifies, and the items it keeps although it writes or moves the bytes that locate them (the
# pointers it adjusts). provexp.reach.predict_structural does the rest: the content kinds are re-recognized where the
# edits write, the items past an insertion move with their bytes, and an item the declaration does not cover flags the
# edit. Unlike `add_section` above (the end-of-file layout the toolkits' LIEF output is compared with), the declaration
# follows our own edit's layout, so its prediction is compared with re-extraction exactly. Items whose locating
# ranges reach past the end of the file are never declared kept: the operations' pointer updates do not cover data the
# parser had not found.

PAGE = 0x1000
SCN_CODE = 0x00000020
DATA_CHARACTERISTICS = 0x00000040 | 0x40000000 | 0x80000000  # initialized data, read, write
IMPORT_ENTRY = 1


@dataclass
class Written:
    """
    An operation written by our own byte-level edit.

    Attributes:
        new: The edited file.
        edits: The byte edits that perform it, in order, each in the coordinates of the file the previous ones produced.
        layout: Where the operation put things (offsets, the new section's RVA, the shift of the bytes past an insertion).
    """

    new: bytes
    edits: list[ByteEdit]
    layout: dict[str, int]


def _align(x: int, a: int) -> int:
    """`x` rounded up to a multiple of `a` (unchanged when `a` is 0)."""
    return (x + a - 1) // a * a if a else x


def _parse(z: bytes, fast: bool = False) -> Optional[pefile.PE]:
    """Parse as the extractor does, or None."""
    try:
        return pefile.PE(data=z, fast_load=fast)
    except (pefile.PEFormatError, AttributeError):
        return None


def _field(offset: int, fmt: str, value: int) -> ByteEdit:
    """Write `value` (masked to the field's width) at `offset`."""
    width = struct.calcsize(fmt)
    return ByteEdit(offset, offset + width, struct.pack(fmt, value & ((1 << (8 * width)) - 1)))


def _apply(z: bytes, edits: Sequence[ByteEdit]) -> bytes:
    for e in edits:
        z = e.apply(z)
    return z


def new_section_slot(pe: pefile.PE, z: bytes) -> Optional[tuple[int, int]]:
    """Where a new section header goes (40 zero bytes after the table, within the headers) and the new section's RVA."""
    start = pe.DOS_HEADER.e_lfanew + 4 + 20 + pe.FILE_HEADER.SizeOfOptionalHeader
    slot = start + 40 * pe.FILE_HEADER.NumberOfSections
    first_data = min((s.PointerToRawData for s in pe.sections if s.SizeOfRawData and s.PointerToRawData), default=len(z))
    if slot + 40 > min(pe.OPTIONAL_HEADER.SizeOfHeaders, first_data, len(z)) or any(z[slot:slot + 40]):
        return None
    sa = pe.OPTIONAL_HEADER.SectionAlignment or 0x1000
    end = max((s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in pe.sections), default=0)
    return slot, _align(max(end, pe.OPTIONAL_HEADER.SizeOfHeaders), sa)


def write_section(z: bytes, name: bytes, content: bytes, characteristics: int, before_overlay: bool,
                  content_at_rva: Optional[Callable[[int], bytes]] = None) -> Optional[Written]:
    """
    Add a section (`sec`): a header after the section table, the content padded to FileAlignment at the end of the file
    or (`before_overlay`) where pefile's overlay starts, moving the overlay and the certificate table's offset.

    Args:
        z: The file.
        name: The section name (at most 8 bytes; shorter names are NUL-padded).
        content: The section's content (ignored when `content_at_rva` is given).
        characteristics: The section's characteristics.
        before_overlay: Whether the content goes before the overlay (as LIEF puts it) instead of after it.
        content_at_rva: Builds the content from the section's RVA (for content that holds RVAs, as an import table).

    Returns:
        The written operation (layout: slot, rva, offset, at, raw, shift), or None if the headers have no room for
        another section header.
    """
    pe = _parse(z, fast=True)
    if pe is None:
        return None
    slot = new_section_slot(pe, z)
    if slot is None:
        return None
    table_slot, rva = slot
    fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200
    sa = pe.OPTIONAL_HEADER.SectionAlignment or 0x1000
    overlay = pe.get_overlay_data_start_offset() if before_overlay else None
    # Past every section's raw data, also where pefile's overlay rule skips a section that runs past the end.
    ends = [min(s.PointerToRawData + s.SizeOfRawData, len(z)) for s in pe.sections if s.SizeOfRawData]
    at = len(z) if overlay is None else max([overlay] + ends)
    offset = _align(at, fa)
    if sa < PAGE:
        # NOTE: a low-alignment image is mapped flat, so a section's raw offset must equal its virtual address (run 104).
        offset = rva = max(offset, rva)
    if content_at_rva is not None:
        content = content_at_rva(rva)
    raw = content + b"\x00" * (_align(len(content), fa) - len(content))
    inserted = b"\x00" * (offset - at) + raw
    edits: list[ByteEdit] = [ByteEdit(at, at, inserted)] if inserted else []
    shift = len(inserted) if at < len(z) else 0
    security = pe.OPTIONAL_HEADER.DATA_DIRECTORY[SECURITY_ENTRY] if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) > SECURITY_ENTRY else None
    if shift and security is not None and security.VirtualAddress >= at:
        edits.append(_field(security.get_file_offset(), "<I", security.VirtualAddress + shift))
    header = name[:8].ljust(8, b"\x00") + struct.pack("<IIII", len(content), rva, len(raw), offset) + b"\x00" * 12
    edits.append(ByteEdit(table_slot, table_slot + 40, header + struct.pack("<I", characteristics)))
    edits.append(_field(pe.FILE_HEADER.get_file_offset() + 2, "<H", pe.FILE_HEADER.NumberOfSections + 1))
    oh = pe.OPTIONAL_HEADER
    edits.append(_field(field_range(oh, "SizeOfImage")[0], "<I", _align(rva + len(content), sa)))
    size_field = "SizeOfCode" if characteristics & SCN_CODE else "SizeOfInitializedData"
    edits.append(_field(field_range(oh, size_field)[0], "<I", getattr(oh, size_field) + len(raw)))
    layout = {"slot": table_slot, "rva": rva, "offset": offset, "at": at, "raw": len(raw), "shift": shift}
    return Written(_apply(z, edits), edits, layout)


def import_table(descriptors: Sequence[bytes], library: bytes, functions: Sequence[bytes], thunk: str, rva: int) -> bytes:
    """
    An import table at `rva`: the given descriptors, one for `library` with its own lookup table, address table, and
    hint/name entries, and the terminator.
    """
    width = struct.calcsize(thunk)
    lookup = 20 * (len(descriptors) + 2)
    address = lookup + width * (len(functions) + 1)
    names = address + width * (len(functions) + 1)
    blob = bytearray()
    hint_names = []
    for f in functions:
        hint_names.append(names + len(blob))
        blob += b"\x00\x00" + f + b"\x00"
        if len(blob) % 2:
            blob += b"\x00"
    library_rva = rva + names + len(blob)
    blob += library + b"\x00"
    table = b"".join(struct.pack(thunk, rva + h) for h in hint_names) + b"\x00" * width
    new = struct.pack("<IIIII", rva + lookup, 0, 0, library_rva, rva + address)
    return b"".join(descriptors) + new + b"\x00" * 20 + table + table + bytes(blob)


def write_imports(z: bytes, library: bytes, functions: list[bytes], before_overlay: bool) -> Optional[Written]:
    """
    Add imports (`imp`): a new data section holding the existing import descriptors, one for `library` with its own
    lookup table, address table, and names, and the terminator; the IMPORT directory entry points to it.
    """
    pe = _parse(z)
    if pe is None or len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= IMPORT_ENTRY:
        return None
    old = [bytes(entry.struct.__pack__()) for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])]
    thunk = "<Q" if pe.PE_TYPE == pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS else "<I"
    written = write_section(z, b".pvimp", b"", DATA_CHARACTERISTICS, before_overlay,
                            content_at_rva=lambda rva: import_table(old, library, functions, thunk, rva))
    if written is None:
        return None
    entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[IMPORT_ENTRY]
    edits = [_field(entry.get_file_offset(), "<I", written.layout["rva"]),
             _field(entry.get_file_offset() + 4, "<I", 20 * (len(old) + 2))]
    return Written(_apply(written.new, edits), written.edits + edits, written.layout)


def write_gap(z: bytes, at_pe_header: bool, gap: bytes) -> Optional[Written]:
    """
    Insert a gap (`ext` before the PE header, `shf` before the first section's data) of a multiple of FileAlignment
    bytes, raising the pointers past it: e_lfanew and SizeOfHeaders (`ext`), PointerToRawData, and the certificate
    table's offset. None if the gap is not a multiple of FileAlignment, the headers would outgrow the first section, or
    the image is low-alignment (mapped flat: raw data cannot move off its virtual address).
    """
    pe = _parse(z, fast=True)
    if pe is None:
        return None
    oh = pe.OPTIONAL_HEADER
    fa = oh.FileAlignment or 0x200
    if len(gap) % fa or oh.SectionAlignment < PAGE:
        # NOTE: a low-alignment image is mapped flat: moving raw data off its virtual address is not loader-safe.
        return None
    k = len(gap)
    if at_pe_header:
        at = pe.DOS_HEADER.e_lfanew
        first_rva = min((s.VirtualAddress for s in pe.sections), default=1 << 32)
        if oh.SizeOfHeaders + k > first_rva:
            return None
    else:
        data = [s.PointerToRawData for s in pe.sections if s.SizeOfRawData and s.PointerToRawData >= oh.SizeOfHeaders]
        if not data:
            return None
        at = min(data)

    def moved_offset(offset: int) -> int:
        return offset + k if offset >= at else offset

    # NOTE: on a truncated file the first section's data can start past the end; the gap then goes at the end (as the
    # original writer's slicing put it, runs 107 and 117), and the pointers past `at` are still raised.
    edits = [ByteEdit(min(at, len(z)), min(at, len(z)), gap)]
    if at_pe_header:
        edits.append(_field(0x3C, "<I", at + k))
        edits.append(_field(moved_offset(field_range(oh, "SizeOfHeaders")[0]), "<I", oh.SizeOfHeaders + k))
    for s in pe.sections:
        if s.SizeOfRawData and s.PointerToRawData >= at:
            edits.append(_field(moved_offset(s.get_file_offset() + 20), "<I", s.PointerToRawData + k))
    if len(oh.DATA_DIRECTORY) > SECURITY_ENTRY:
        security = oh.DATA_DIRECTORY[SECURITY_ENTRY]
        if security.Size and security.VirtualAddress >= at:
            edits.append(_field(moved_offset(security.get_file_offset()), "<I", security.VirtualAddress + k))
    return Written(_apply(z, edits), edits, {"at": at, "shift": k})


def write_rename(pe: pefile.PE, z: bytes, index: int, name: bytes) -> Written:
    """Rename a section (`ren`): its 8-byte name field, NUL-padded."""
    lo = pe.sections[index].get_file_offset()
    edits = [ByteEdit(lo, lo + 8, name[:8].ljust(8, b"\x00"))]
    return Written(_apply(z, edits), edits, {"index": index})


def write_zero_entry(pe: pefile.PE, z: bytes, index: int) -> Optional[Written]:
    """Remove a data directory entry (`rdb`: debug, `rsg`: security) by zeroing it; None if the file has none."""
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    d = directories[index] if len(directories) > index else None
    if d is None or not (d.VirtualAddress or d.Size):
        return None
    lo = d.get_file_offset()
    edits = [ByteEdit(lo, lo + 8, b"\x00" * 8)]
    return Written(_apply(z, edits), edits, {"index": index})


# The attributes of the certificate table of a file without one (signify finds no signed data, and no error).
UNSIGNED = {"num_certs": 0, "self_signed": 0, "empty_program_name": 0, "no_countersigner": 0, "parse_error": 0,
            "chain_max_depth": 0, "latest_signing_time": 0, "signing_time_diff": 0}


def _kept(table: ItemTable, n: int, declared: Sequence[Item], excluded: Sequence[Item] = ()) -> list[Item]:
    """Every located item whose locating ranges lie within the file, except the declared and the excluded ones."""
    gone = {id(i) for i in declared} | {id(i) for i in excluded}
    return [i for i in table.items if i.locating and id(i) not in gone and all(b <= n for _, b in i.locating)]


def _move(extractor: PEFeatureExtractor, items: Sequence[Item], edit: Optional[ByteEdit], old: bytes) -> list[Item]:
    """The items moved by an insertion (copies when there is none), as their feature types move them."""
    if edit is None or edit.shift == 0 or edit.is_append(old):
        return [replace(i) for i in items]
    new = edit.apply(old)
    rec = extractor.recognizers
    return [rec[i.group].move(i, edit, old, new) if hasattr(rec[i.group], "move") else moved(i, edit, old) for i in items]  # type: ignore[attr-defined]


def _section_name(raw: bytes) -> str:
    """A section's name as the extractor reads it."""
    return raw.strip(b"\x00").decode(errors="ignore").lower()


def _entry_choice(pe: pefile.PE, names: Sequence[str]) -> tuple[str, int, bool]:
    """
    The entry section the extractor selects, for the file's sections renamed to `names`: its name, its index (-1 if
    none), and whether it was selected as a fallback (the first executable section; see `SectionInfo.raw_features`).
    """
    aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    name, index, fallback = "", -1, False
    for i, section in enumerate(pe.sections):
        if section.contains_rva(aoep):
            name, index = names[i], i
    i = 0
    while name == "" and i < len(pe.sections):
        if pe.sections[i].Characteristics & 0x20000000 > 0:
            name, index, fallback = names[i], i, True
        i += 1
    return name, index, fallback


def _entry_item(pe: pefile.PE, n: int, old: Item, name: str, index: int, fallback: bool) -> Item:
    """The entry item for the selected section (the extractor's ranges: the entry point, the name, the fallback's flags)."""
    ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint")]
    if index >= 0:
        ranges.append(field_range(pe.sections[index], "Name"))
        if fallback:
            ranges.append(field_range(pe.sections[index], "Characteristics"))
    (b,), (sign,) = feature_hash(10, [name])
    term = Term("hashed", "section:entry_name_hash", index=int(b), sign=int(sign), key=name, ranges=clipped(n, ranges))
    return replace(old, terms=(term,), attrs={"name": name})


def _new_section(extractor: PEFeatureExtractor, pe: pefile.PE, new: bytes, written: Written, header: bytes) -> Item:
    """The item of the section `write_section` added, read from its declared header (as pefile reads a section)."""
    s = pefile.SectionStructure(getattr(pefile.PE, "__IMAGE_SECTION_HEADER_format__"), pe=pe)
    s.__unpack__(header)
    lo, hi = section_data_range(s)
    slot = written.layout["slot"]
    raw = {
        "name": _section_name(s.Name),
        "size": s.SizeOfRawData,
        "entropy": entropy_H(new[lo:hi]),
        "vsize": s.Misc_VirtualSize,
        "vsize_ratio": s.SizeOfRawData / max(s.Misc_VirtualSize, 1),
        "props": [sc[10:] for sc, _ in pefile.section_characteristics if s.__dict__.get(sc)],
    }
    ranges: dict[str, tuple[Range, ...]] = {
        "table": ((slot, slot + 40),), "name": ((slot, slot + 8),), "vsize": ((slot + 8, slot + 12),),
        "size": ((slot + 16, slot + 20),), "props": ((slot + 36, slot + 40),), "data": ((lo, hi),) if hi > lo else (),
    }
    section: SectionInfo = _group(extractor, "section")  # type: ignore[assignment]
    return _tagged([section.section_item(raw, ranges, section_locating(pe) + ((slot, slot + 40),))], "section")[0]


def _declare_section(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, pe: pefile.PE, written: Written
                     ) -> tuple[list[Item], list[Item], list[Item]]:
    """
    The delta of `write_section` (and of the section `write_imports` adds): the new section; at the end of the file, the
    file's length and no overlay (the section's raw data now ends the file; an old overlay's bytes stay but are no
    longer past every extent); before the overlay, the overlay and the certificate table move with their bytes. The
    entry section is kept if some old section contains the entry point (the new one lies past every old one); otherwise
    the fallback may pick the new section, which the declaration does not state (flagged).
    """
    new, n = written.new, len(z)
    insertion = written.edits[0] if written.edits and written.edits[0].lo == written.layout["at"] and written.layout["at"] < n else None
    slot = written.layout["slot"]
    header = next(e.content for e in written.edits if e.lo == slot and len(e.content) == 40)
    removed: list[Item] = []
    added: list[Item] = [_new_section(extractor, pe, new, written, header)]
    excluded: list[Item] = []
    if insertion is None:
        # The section's data ends the file: the file grows, and there is no overlay.
        section: SectionInfo = _group(extractor, "section")  # type: ignore[assignment]
        file_items = [i for i in table.of_group("section") if i.kind == "file"]
        removed += file_items + [i for i in table.of_group("section") if i.kind == "overlay"]
        added += _tagged([section._file_item(len(new), i.locating) for i in file_items], "section")
    certificates = [i for i in table.of_group("authenticode") if i.kind == "certificate_table"]
    if insertion is not None and written.layout["shift"]:
        # The certificate table moves with its bytes (its offset is rewritten; it is otherwise the same table).
        removed += certificates
        added += _move(extractor, certificates, insertion, z)
    aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    if not any(s.contains_rva(aoep) for s in pe.sections):
        excluded += [i for i in table.of_group("section") if i.kind == "entry"]
    return removed, added, excluded


def predict_add_section(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, name: bytes, content: bytes,
                        characteristics: int, before_overlay: bool) -> Optional[Prediction]:
    """
    `sec`, written by `write_section` and declared item by item (Table 5). None if it does not apply to the file.
    The prediction's `new` is the written file.
    """
    pe = _parse(z)
    written = write_section(z, name, content, characteristics, before_overlay)
    if pe is None or written is None:
        return None
    removed, added, excluded = _declare_section(extractor, table, z, pe, written)
    kept = _kept(table, len(z), removed, excluded)
    return predict_structural(table, z, written.edits, removed, added, kept, extractor.recognizers)


def predict_add_imports(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, library: bytes,
                        functions: list[bytes], before_overlay: bool) -> Optional[Prediction]:
    """
    `imp`, written by `write_imports` and declared item by item: the section that holds the new import table (as
    `predict_add_section`), and one library and one import item per function for the new descriptor (pefile skips a
    descriptor without functions, so it adds nothing). The old imports are kept: the new table copies their descriptors.
    """
    pe = _parse(z)
    written = write_imports(z, library, functions, before_overlay)
    if pe is None or written is None:
        return None
    removed, added, excluded = _declare_section(extractor, table, z, pe, written)
    if functions:
        n = len(written.new)
        lo, hi = written.layout["offset"], written.layout["offset"] + written.layout["raw"]
        r = clipped(n, [(lo, hi)])
        # NOTE: the new items' ranges are the whole import section (their own names lie within it).
        old = table.of_group("imports")
        locating = old[0].locating if old else section_locating(pe)
        dll = library.decode().lower()
        (b,), _ = feature_hash(256, [dll])
        new_items = [Item("library", terms=(Term("keyed", "imports:libraries", index=int(b), key=dll, ranges=r),), locating=locating)]
        keys = [dll + ":" + f.decode()[:10000] for f in functions]
        buckets, _ = feature_hash(1024, keys)
        for key, fb in zip(keys, buckets.tolist(), strict=True):
            new_items.append(Item("import", terms=(
                Term("count", "imports:num_imports", ranges=r),
                Term("hashed", "imports:functions", index=fb, key=key, ranges=r),
            ), attrs={"dll": dll}, locating=locating))
        added += _tagged(new_items, "imports")
    kept = _kept(table, len(z), removed, excluded)
    return predict_structural(table, z, written.edits, removed, added, kept, extractor.recognizers)


def predict_insert_gap(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, at_pe_header: bool, gap: bytes) -> Optional[Prediction]:
    """
    `ext` (`at_pe_header`) or `shf`, written by `write_gap` and declared: every item past the gap moves with its bytes,
    and nothing else changes but the pointers the edit rewrites (e_lfanew and SizeOfHeaders, which are features, are
    re-read). The sections and the certificate table, whose pointers are rewritten, are declared moved. On a file without
    a Rich header, a gap that holds the "Rich" marker in the range pefile searches makes one, which the declaration does
    not state (flagged).
    """
    pe = _parse(z)
    written = write_gap(z, at_pe_header, gap)
    if pe is None or written is None:
        return None
    insertion = written.edits[0]
    moving = [i for i in table.of_group("section") if i.kind == "section"] + [i for i in table.of_group("authenticode") if i.kind == "certificate_table"]
    removed, added = moving, _move(extractor, moving, insertion, z)
    excluded: list[Item] = []
    if pe.RICH_HEADER is None:
        k = written.layout["shift"]
        if b"Rich" in written.new[0x80:pe.OPTIONAL_HEADER.get_file_offset() + (k if at_pe_header else 0)]:
            excluded += table.of_group("richheader")
    kept = _kept(table, len(z), removed, excluded)
    return predict_structural(table, z, written.edits, removed, added, kept, extractor.recognizers)


def predict_rename(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, index: int, name: bytes) -> Optional[Prediction]:
    """
    `ren`, written by `write_rename` and declared: the section's item gets the new name (its hashed contributions move
    to the new name's buckets; an empty name counts), and the entry item follows if the extractor selects that section.
    """
    pe = _parse(z)
    if pe is None or not 0 <= index < len(pe.sections):
        return None
    written = write_rename(pe, z, index, name)
    section: SectionInfo = _group(extractor, "section")  # type: ignore[assignment]
    sections = [i for i in table.of_group("section") if i.kind == "section"]
    if len(sections) != len(pe.sections):
        return None
    old = sections[index]
    n = len(z)
    s = pe.sections[index]
    new_name = _section_name(written.edits[0].content)
    raw = {k: old.attrs[k] for k in ("size", "vsize", "entropy", "vsize_ratio", "props")} | {"name": new_name}
    ranges = {"table": clipped(n, [structure_range(s)]), "name": clipped(n, [field_range(s, "Name")]),
              "size": clipped(n, [field_range(s, "SizeOfRawData")]), "vsize": clipped(n, [field_range(s, "Misc_VirtualSize")]),
              "props": clipped(n, [field_range(s, "Characteristics")]), "data": old.attrs["data"]}
    removed, added = [old], _tagged([section.section_item(raw, ranges, old.locating)], "section")
    names = [_section_name(x.Name) for x in pe.sections]
    before = _entry_choice(pe, names)
    names[index] = new_name
    after = _entry_choice(pe, names)
    if before != after or after[1] == index:
        entries = [i for i in table.of_group("section") if i.kind == "entry"]
        removed += entries
        added += [_entry_item(pe, n, e, *after) for e in entries]
    kept = _kept(table, n, removed)
    return predict_structural(table, z, written.edits, removed, added, kept, extractor.recognizers)


def predict_zero_entry(extractor: PEFeatureExtractor, table: ItemTable, z: bytes, index: int) -> Optional[Prediction]:
    """
    `rdb` (the debug entry) or `rsg` (the security entry), written by `write_zero_entry` and declared. Removing the debug
    entry removes one extent from pefile's overlay rule, so the overlay may start earlier (or appear); removing the
    security entry removes the certificate table (its bytes stay, as overlay bytes, which they already were: pefile's
    overlay rule skips the security entry). The entry's two fields are re-read.
    """
    pe = _parse(z)
    if pe is None:
        return None
    written = write_zero_entry(pe, z, index)
    if written is None:
        return None
    n = len(z)
    removed: list[Item] = []
    added: list[Item] = []
    if index == SECURITY_ENTRY:
        certificates = [i for i in table.of_group("authenticode") if i.kind == "certificate_table"]
        removed += certificates
        added += [replace(i, attrs=dict(UNSIGNED)) for i in certificates]
    elif index == DEBUG_ENTRY:
        start, after = pe.get_overlay_data_start_offset(), overlay_start_without(pe, DEBUG_ENTRY)
        if start != after:
            section: SectionInfo = _group(extractor, "section")  # type: ignore[assignment]
            overlays = [i for i in table.of_group("section") if i.kind == "overlay"]
            file_items = [i for i in table.of_group("section") if i.kind == "file"]
            locating = (overlays or file_items)[0].locating
            removed += overlays
            if after is not None:
                added += _tagged([section._overlay_item(written.new, after, locating)], "section")
    kept = _kept(table, n, removed)
    return predict_structural(table, z, written.edits, removed, added, kept, extractor.recognizers)
