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

from collections.abc import Sequence
from dataclasses import replace

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import SectionInfo
from provexp.featuresets.ember2024.features import entropy_H
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Range
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict_declared

__all__ = [
    "add_section",
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
    characteristics; the COFF NumberOfSections rises by one. What the declaration does not fix is the tool's layout:
    the section-table entry, alignment padding, SizeOfImage, where the content lands relative to an overlay, and any
    directory it moves. Those are assumption A4 and show up as the residual against the tool's output.

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
        added += _tagged([section._file_item(len(new), file_items[0].locating), section.section_item(s, ranges, file_items[0].locating)], "section")
    for item in table.of_group("header"):
        if item.attrs.get("field") == "NumberOfSections":
            (term,) = item.terms
            removed.append(item)
            added += _tagged([replace(item, terms=(replace(term, value=term.value + 1),))], "header")

    return predict_declared(table, new, removed, added)
