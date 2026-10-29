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

from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import replace
from typing import Optional

import pefile

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import SectionInfo
from provexp.featuresets.ember2024.features import clipped
from provexp.featuresets.ember2024.features import entropy_H
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import section_data_range
from provexp.featuresets.ember2024.features import structure_range
from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Range
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
from provexp.reach import predict_declared
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
