"""
What an edit does to the features, computed from the item table (docs/feature-provenance-model.md, Section 3 and
claim C1; docs/item-layer-design.md, component 4).

C1, the side effects of one concrete edit: new sums = old sums + what the added items contribute - what the removed
items contributed, then the readouts. An edit is stated on the elements and translated into item operations:

    content       an in-place write that meets no locating range: the items it meets are re-recognized locally
                  (each feature type's recognizer, with its margins, assumption A3)
    item-creating an append: the open-ended items grow and new items are recognized from the appended elements
    structural    a write that meets a locating range (assumption A1): the edit catalogue declares the item delta,
                  or the engine flags the edit and the items whose location it may change

The engine never extracts the edited object: it reads the edited elements plus the recognizers' margins, and it
knows nothing about any file format (the recognizers and the catalogue do).
"""

from __future__ import annotations
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Protocol

import numpy as np
from numpy import typing as npt

from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Range
from provexp.items import Readout
from provexp.items import evaluate


__all__ = [
    "ByteEdit",
    "Prediction",
    "Recognizer",
    "NotLocal",
    "meets",
    "predict",
    "predict_declared",
]


################################################################################
# Edits
################################################################################


@dataclass(frozen=True)
class ByteEdit:
    """
    Replace the elements [lo, hi) of an object by `content`: an in-place write when len(content) == hi - lo, an
    append when lo == hi == len(object). Other insertions and deletions move elements and are declared structural.
    """

    lo: int
    hi: int
    content: bytes

    def apply(self, old: bytes) -> bytes:
        """The edited object."""
        if not 0 <= self.lo <= self.hi <= len(old):
            raise ValueError(f"Edit [{self.lo}, {self.hi}) out of range for an object of {len(old)} elements.")
        return old[:self.lo] + self.content + old[self.hi:]

    def is_append(self, old: bytes) -> bool:
        return self.lo == self.hi == len(old) and len(self.content) > 0

    def is_in_place(self) -> bool:
        return len(self.content) == self.hi - self.lo

    def touched(self, old: bytes) -> Range:
        """The elements the edit writes, in the old object's coordinates (past its end for an append)."""
        return (self.lo, self.lo + len(self.content)) if self.is_append(old) else (self.lo, self.hi)


def meets(ranges: Sequence[Range], span: Range) -> bool:
    """Whether any of the half-open ranges shares an element with the span."""
    lo, hi = span
    return any(a < hi and lo < b for a, b in ranges)


################################################################################
# Recognizers
################################################################################


class NotLocal(Exception):
    """Raised by a recognizer for an edit it cannot translate into local item operations; the engine flags it."""

    def __init__(self, items: Sequence[Item], reason: str) -> None:
        super().__init__(reason)
        self.items = list(items)
        self.reason = reason


class Recognizer(Protocol):
    """
    Re-recognizes one feature type's items after an in-place write or an append (assumption A3).

    Given the type's items in the old object, the old and new objects, and the edit, it returns the items that leave
    (old items, including modified ones) and the items that join (new and modified items), or raises NotLocal.
    """

    def recognize(self, items: Sequence[Item], old: bytes, new: bytes, edit: ByteEdit) -> tuple[list[Item], list[Item]]:
        ...


################################################################################
# C1
################################################################################


@dataclass
class Prediction:
    """
    The predicted effect of an edit.

    Attributes:
        new: The edited object.
        table: The predicted item table of the edited object, or None if the edit was flagged.
        removed: The items that left (or were modified).
        added: The items that joined (or the modified items' new versions).
        flagged: The items whose location the edit may change (structural, undeclared) or that a recognizer could not
            re-recognize locally; empty when the prediction is made.
        reason: Why the edit was flagged.
    """

    new: bytes
    table: Optional[ItemTable]
    removed: list[Item] = field(default_factory=list)
    added: list[Item] = field(default_factory=list)
    flagged: list[Item] = field(default_factory=list)
    reason: str = ""

    def features(self, readouts: Sequence[Readout]) -> npt.NDArray[np.float32]:
        """The predicted feature vector (raises if the edit was flagged)."""
        if self.table is None:
            raise RuntimeError(f"The edit was flagged: {self.reason}")
        return evaluate(self.table, readouts)


def predict(table: ItemTable, old: bytes, edit: ByteEdit, recognizers: Mapping[str, Recognizer]) -> Prediction:
    """
    C1 for an in-place write or an append: the item table of the edited object, from the old one, or a flag.

    Args:
        table: The item table of `old`; its items' `group` names their recognizer.
        old: The old object.
        edit: The edit.
        recognizers: The recognizer of each group that has items.

    Returns:
        The prediction; flagged if the edit writes a locating range or a recognizer cannot handle it.
    """
    if not (edit.is_in_place() or edit.is_append(old)):
        raise ValueError("Only in-place writes and appends are predicted from bytes; declare other edits.")
    if table.num_elements != len(old):
        raise ValueError(f"The table has {table.num_elements} elements; the object has {len(old)}.")
    new = edit.apply(old)

    # A1: a write to a locating range may change which items exist or where they are.
    span = edit.touched(old)
    located = [item for item in table.items if meets(item.locating, span)]
    if located:
        return Prediction(new, None, flagged=located, reason=f"structural: the edit writes locating elements of {len(located)} items")

    removed: list[Item] = []
    added: list[Item] = []
    groups = sorted({item.group for item in table.items})
    missing = [g for g in groups if g not in recognizers]
    if missing:
        raise KeyError(f"No recognizer for the groups {missing}.")
    for group in groups:
        try:
            r, a = recognizers[group].recognize(table.of_group(group), old, new, edit)
        except NotLocal as e:
            return Prediction(new, None, flagged=e.items, reason=f"{group}: {e.reason}")
        for item in a:
            item.group = item.group or group
        removed += r
        added += a
    return Prediction(new, table.replace(removed, added, len(new)), removed, added)


def predict_declared(table: ItemTable, new: bytes, removed: Sequence[Item], added: Sequence[Item]) -> Prediction:
    """
    C1 for a declared structural edit: the catalogue states the edited object (or its declared layout) and the item
    delta, and the engine updates the sums (model, Section 3, "declared").
    """
    return Prediction(new, table.replace(removed, added, len(new)), list(removed), list(added))
