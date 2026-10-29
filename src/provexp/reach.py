"""
What an edit does to the features, computed from the item table (docs/feature-provenance-model.md, Sections 3-4,
claims C1 and C4; docs/item-layer-design.md, components 4 and 5).

C1, the side effects of one concrete edit: new sums = old sums + what the added items contribute - what the removed
items contributed, then the readouts. An edit is stated on the elements and translated into item operations:

    content       an in-place write that meets no locating range: the items it meets are re-recognized locally
                  (each feature type's recognizer, with its margins, assumption A3)
    item-creating an append: the open-ended items grow and new items are recognized from the appended elements
    structural    a write that meets a locating range (assumption A1): the edit catalogue declares the item delta,
                  or the engine flags the edit and the items whose location it may change

The engine never extracts the edited object: it reads the edited elements plus the recognizers' margins, and it
knows nothing about any file format (the recognizers and the catalogue do).

C4, the directions an operation can move each feature on some object: the catalogue states each operation as abstract
item changes (add, remove, modify, grow, or flag items of a kind); each kind's term vocabulary, collected from every
recorded item, gives the signs the changes can give each sum; each readout type turns the sums' signs into the
feature's (fixed, up, down, or both).
"""

from __future__ import annotations
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from functools import cache
from itertools import product
import math
from re import _parser as sre_parse  # type: ignore[attr-defined]
from typing import Literal
from typing import Optional
from typing import Protocol

import numpy as np
from numpy import typing as npt

from provexp.items import BitTest
from provexp.items import DistinctCount
from provexp.items import Entropy
from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Lookup
from provexp.items import Max
from provexp.items import Min
from provexp.items import Normalized
from provexp.items import Opaque
from provexp.items import Outside
from provexp.items import Positive
from provexp.items import Range
from provexp.items import Ratio
from provexp.items import Readout
from provexp.items import evaluate
from provexp.items import feature_hash


__all__ = [
    "ByteEdit",
    "Prediction",
    "Recognizer",
    "NotLocal",
    "meets",
    "predict",
    "predict_declared",
    "Signs",
    "FIXED",
    "UP",
    "DOWN",
    "BOTH",
    "direction",
    "KindProfile",
    "Vocabulary",
    "profile_kinds",
    "Change",
    "ChangeHow",
    "Entry",
    "Envelope",
    "envelope",
    "region_changes",
    "readout_signs",
    "directions",
    "hash_image",
    "extension_monotone",
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


################################################################################
# C4: signs
################################################################################


Signs = frozenset[str]
FIXED: Signs = frozenset()
UP: Signs = frozenset("+")
DOWN: Signs = frozenset("-")
BOTH: Signs = frozenset("+-")

# An entry of a family of sums.
Entry = tuple[str, int]


def negate(s: Signs) -> Signs:
    """The opposite signs."""
    return frozenset({"+": "-", "-": "+"}[c] for c in s)


def direction(s: Signs) -> str:
    """The direction of a set of signs: fixed, up, down, or both."""
    return {FIXED: "fixed", UP: "up", DOWN: "down"}.get(s, "both")


def ratio_signs(num: Signs, den: Signs) -> Signs:
    """The signs of a ratio of nonnegative quantities, from its numerator's and denominator's."""
    if num and den:
        return BOTH
    return num if num else negate(den)


################################################################################
# C4: the kinds' term vocabulary
################################################################################


@dataclass
class TermProfile:
    """
    What the terms of one kind write to one entry of a family (count, add, and slot terms) or to a whole family (bins,
    hashed, split, and keyed terms, whose entry depends on content or key).

    Attributes:
        op: The term op (one per entry and kind).
        per_byte: Whether the terms count elements, so that they grow when the item grows (one value per entry).
        signed: For hashed terms, whether the key's hash sign is applied (checked against the hash of every key).
        min_value: The smallest value recorded (count, add, and slot terms).
        items: The number of recorded items with a term on the entry (an entry every item of the kind writes is
            unconditional: a count there changes only when items appear or disappear).
    """

    op: str
    per_byte: bool
    signed: bool = False
    min_value: float = math.inf
    items: int = 0


@dataclass
class KindProfile:
    """
    The term vocabulary of one kind of one group, collected from every recorded item: which entries its items write,
    how, and the range of their attributes. C4 reads signs off it; it states nothing about any operation.

    Attributes:
        group: The feature type that records the items.
        kind: The item kind.
        terms: Per entry (family, index), or per family (family, -1) for bins, hashed, split, and keyed terms.
        attrs: The recorded range (min, max) of each numeric attribute.
        growing: The attributes read from a per-element add term (they grow when the item grows).
        fields: For items with a "field" attribute, the entries each field writes.
        local: Whether every item is local (assumption A2).
        items: The number of items recorded.
    """

    group: str
    kind: str
    terms: dict[Entry, TermProfile] = field(default_factory=dict)
    attrs: dict[str, tuple[float, float]] = field(default_factory=dict)
    growing: set[str] = field(default_factory=set)
    fields: dict[str, set[Entry]] = field(default_factory=dict)
    local: bool = True
    items: int = 0


_WHOLE_FAMILY = ("bins", "hashed", "split", "keyed")


class Vocabulary:
    """
    Collects the term vocabulary of every (group, kind) from item tables (`add`), possibly in several processes
    (`merge`), and checks it (`finish`).
    """

    def __init__(self) -> None:
        self.profiles: dict[tuple[str, str], KindProfile] = {}
        self.sizes: dict[str, int] = {}
        self.hashed: dict[tuple[str, str, str], set[tuple[str, int]]] = {}
        self.split: dict[tuple[str, str, str], set[tuple[str, int]]] = {}

    def add(self, table: ItemTable) -> None:
        """Record every item of a table."""
        for family, size in table.families.items():
            self._size(family, size)
        for item in table.items:
            p = self.profiles.setdefault((item.group, item.kind), KindProfile(item.group, item.kind))
            p.items += 1
            p.local &= item.local
            seen: set[Entry] = set()
            for t in item.terms:
                key: Entry = (t.family, -1 if t.op in _WHOLE_FAMILY else t.index)
                tp = self._term(p, key, TermProfile(t.op, t.per_byte))
                if key not in seen:
                    seen.add(key)
                    tp.items += 1
                if t.op in ("count", "add", "slot"):
                    tp.min_value = min(tp.min_value, float(t.value))
                    if t.op == "add" and t.per_byte and t.attr is not None:
                        p.growing.add(t.attr)
                if t.op == "hashed":
                    assert t.key is not None
                    self.hashed.setdefault((item.group, item.kind, t.family), set()).add((t.key, t.sign))
                if t.op == "split":
                    assert t.key is not None
                    self.split.setdefault((item.group, item.kind, t.family), set()).add((t.key, t.index))
            for a, v in item.attrs.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    self._attr(p, a, (float(v), float(v)))
            if isinstance(item.attrs.get("field"), str):
                p.fields.setdefault(item.attrs["field"], set()).update((t.family, t.index) for t in item.terms)

    def merge(self, other: Vocabulary) -> None:
        """Add another collection's records."""
        for family, size in other.sizes.items():
            self._size(family, size)
        for key, q in other.profiles.items():
            p = self.profiles.setdefault(key, KindProfile(q.group, q.kind))
            p.items += q.items
            p.local &= q.local
            p.growing |= q.growing
            for entry, tq in q.terms.items():
                tp = self._term(p, entry, TermProfile(tq.op, tq.per_byte))
                tp.min_value = min(tp.min_value, tq.min_value)
                tp.items += tq.items
            for a, r in q.attrs.items():
                self._attr(p, a, r)
            for f, entries in q.fields.items():
                p.fields.setdefault(f, set()).update(entries)
        for k, pairs in other.hashed.items():
            self.hashed.setdefault(k, set()).update(pairs)
        for k, pairs in other.split.items():
            self.split.setdefault(k, set()).update(pairs)

    def finish(self) -> tuple[dict[tuple[str, str], KindProfile], dict[str, int]]:
        """
        The profiles and the families' sizes, with each hashed family's signedness decided.

        Raises:
            RuntimeError: If a hashed family applies its keys' hash signs to some terms and not to others, or a split
                term is not in the part of its key's bucket that the key's hash sign picks.
        """
        for (group, kind, family), pairs in self.hashed.items():
            keys = sorted(pairs)
            _, signs = feature_hash(self.sizes[family], [k for k, _ in keys])
            same = [int(s) == sign for (_, sign), s in zip(keys, signs.tolist(), strict=True)]
            positive = [sign == 1 for _, sign in keys]
            if all(same):
                # If every recorded key hashes with a positive sign, signedness is undecided: count it as signed.
                signed = True
            elif all(positive):
                signed = False
            else:
                raise RuntimeError(f"{group}/{kind}: family {family} applies its keys' hash signs to some terms only.")
            self.profiles[(group, kind)].terms[(family, -1)].signed = signed
        for (group, kind, family), pairs in self.split.items():
            keys = sorted(pairs)
            half = self.sizes[family] // 2
            buckets, signs = feature_hash(half, [k for k, _ in keys])
            for (key, index), b, sgn in zip(keys, buckets.tolist(), signs.tolist(), strict=True):
                if index != b + (half if sgn < 0 else 0):
                    raise RuntimeError(f"{group}/{kind}: key {key!r} of the split family {family} is in entry {index}; its hash picks {b + (half if sgn < 0 else 0)}.")
        return self.profiles, self.sizes

    def _size(self, family: str, size: int) -> None:
        if self.sizes.setdefault(family, size) != size:
            raise RuntimeError(f"Family {family} has sizes {self.sizes[family]} and {size}.")

    @staticmethod
    def _term(p: KindProfile, key: Entry, new: TermProfile) -> TermProfile:
        tp = p.terms.setdefault(key, new)
        if (tp.op, tp.per_byte) != (new.op, new.per_byte):
            raise RuntimeError(f"{p.group}/{p.kind}: entry {key} is written as {tp.op} and {new.op} (per_byte {tp.per_byte}, {new.per_byte}).")
        return tp

    @staticmethod
    def _attr(p: KindProfile, a: str, r: tuple[float, float]) -> None:
        lo, hi = p.attrs.get(a, (math.inf, -math.inf))
        p.attrs[a] = (min(lo, r[0]), max(hi, r[1]))


def profile_kinds(tables: Iterable[ItemTable]) -> tuple[dict[tuple[str, str], KindProfile], dict[str, int]]:
    """The term vocabulary of every (group, kind) over the item tables, and the size of every family (`Vocabulary`)."""
    v = Vocabulary()
    for table in tables:
        v.add(table)
    return v.finish()


################################################################################
# C4: hash images and regex extension
################################################################################


# NOTE: an attacker who chooses a hashed key freely reaches the image of the hash over all keys; it is computed by
# enumerating short keys (all of up to three characters), which hits every (bucket, sign) pair of every family here.
_ANY_KEY_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789._"


@cache
def _any_keys() -> tuple[str, ...]:
    return tuple("".join(c) for n in (1, 2, 3) for c in product(_ANY_KEY_ALPHABET, repeat=n))


@cache
def _hash_image(size: int, keys: tuple[str, ...]) -> tuple[tuple[int, Signs], ...]:
    buckets, signs = feature_hash(size, list(keys))
    image: dict[int, set[str]] = {}
    for b, sgn in zip(buckets.tolist(), signs.tolist(), strict=True):
        image.setdefault(int(b), set()).add("+" if sgn > 0 else "-")
    return tuple(sorted((b, frozenset(v)) for b, v in image.items()))


def hash_image(size: int, keys: Optional[Sequence[str]] = None) -> dict[int, Signs]:
    """The (bucket, signs) a hashed key reaches over a key domain (None: any key), by enumeration."""
    return dict(_hash_image(size, _any_keys() if keys is None else tuple(sorted(set(keys)))))


_RIGHT_CONTEXT = {"AT_BOUNDARY", "AT_NON_BOUNDARY", "AT_END", "AT_END_STRING", "AT_END_LINE", "ASSERT", "ASSERT_NOT"}


def extension_monotone(pattern: str | bytes) -> bool:
    """
    Whether a regex that matches a string still matches it after more characters are appended to it: true unless the
    pattern inspects context past a match (word boundaries, end anchors, lookaround). A word boundary that opens the
    pattern, followed by at least one character, reads only characters inside the string and is allowed. A syntactic
    test: sound, possibly conservative.
    """
    def walk(node: object) -> bool:
        if isinstance(node, (list, tuple)) or type(node).__name__ == "SubPattern":
            return all(walk(x) for x in node)  # type: ignore[attr-defined]
        if str(node) in _RIGHT_CONTEXT:
            return False
        return True
    parsed = sre_parse.parse(pattern)
    if len(parsed) > 1 and str(parsed[0][1]) in ("AT_BOUNDARY", "AT_NON_BOUNDARY"):
        rest = sre_parse.SubPattern(parsed.state, list(parsed)[1:])
        if rest.getwidth()[0] > 0:
            return walk(rest)
    return walk(parsed)


################################################################################
# C4: changes and sign envelopes
################################################################################


ChangeHow = Literal["add", "remove", "modify", "rewrite", "grow", "flag"]


@dataclass(frozen=True)
class Change:
    """
    An item change an operation can make on some object (the catalogue's delta, over the operation's domain).

        add     new items of the kind, with any content; their hashed and keyed terms take keys from `keys` (None: any)
        remove  items of the kind
        modify  items of the kind get any new content in `families` and `attrs` (None: all of the kind's); counts
                every item of the kind carries do not change (the items still exist)
        rewrite items of the kind get new element values but keep their elements (an in-place write): as modify,
                except that element counts and the attributes read from them do not change
        grow    items of the kind extended by more elements: their element-counting terms and attributes rise, the
                rest of `families` and `attrs` changes (None: no family, every other attribute)
        flag    items of the kind change in a way the model does not resolve (an edit to their locating elements):
                they may appear, disappear, or change in any way

    Attributes:
        how: The change.
        kind: The item kind.
        group: The feature type whose items change (None: every group with items of the kind).
        families: See above.
        attrs: See above.
        keys: For add, the domain of hashed and keyed keys.
        entries: Signs given explicitly to entries (e.g., a field set to zero: down), on top of the above.
    """

    how: ChangeHow
    kind: str
    group: Optional[str] = None
    families: Optional[frozenset[str]] = None
    attrs: Optional[frozenset[str]] = None
    keys: Optional[tuple[str, ...]] = None
    entries: Optional[tuple[tuple[Entry, Signs], ...]] = None


@dataclass
class KindDelta:
    """What changes do to a kind's items, for the readouts over items (max, min, opaque)."""

    added: bool = False
    removed: bool = False
    attrs: dict[str, Signs] = field(default_factory=dict)

    def attr(self, a: str) -> Signs:
        return self.attrs.get(a, FIXED)


@dataclass
class Envelope:
    """The signs an operation can give each entry of each family, and what it does to each kind's items."""

    sums: dict[Entry, Signs]
    kinds: dict[str, KindDelta]
    profiles: dict[tuple[str, str], KindProfile]
    sizes: dict[str, int]

    def entry(self, family: str, index: int) -> Signs:
        return self.sums.get((family, index), FIXED)

    def family(self, family: str, start: int = 0, size: Optional[int] = None) -> list[Signs]:
        n = self.sizes.get(family, 0) if size is None else size
        return [self.entry(family, start + i) for i in range(n)]


def _add(out: dict[Entry, Signs], entry: Entry, s: Signs) -> None:
    if s:
        out[entry] = out.get(entry, FIXED) | s


def _entries(key: Entry, tp: TermProfile, size: int) -> list[Entry]:
    """The entries a term profile covers: one, or the whole family for bins, hashed, split, and keyed terms."""
    return [(key[0], i) for i in range(size)] if tp.op in _WHOLE_FAMILY else [key]


def _added_signs(key: Entry, tp: TermProfile, size: int, keys: Optional[Sequence[str]]) -> dict[Entry, Signs]:
    """The signs adding an item gives the entries a term profile covers (a new item may have any count term)."""
    family, index = key
    if tp.op == "hashed":
        return {(family, b): (s if tp.signed else UP) for b, s in hash_image(size, keys).items()}
    if tp.op == "split":
        half = size // 2
        return {(family, b + (half if c == "-" else 0)): UP for b, s in hash_image(half, keys).items() for c in s}
    if tp.op == "keyed":
        return {(family, b): UP for b in hash_image(size, keys)}
    if tp.op in ("bins", "count"):
        return {(family, i): UP for i in range(size)}
    return {(family, index): UP if tp.min_value >= 0 else BOTH}


def _unconditional(p: KindProfile, entry: Entry) -> bool:
    """Whether every recorded item of the kind has a count on the entry."""
    tp = p.terms.get(entry)
    return tp is not None and tp.op == "count" and tp.items == p.items


def envelope(changes: Sequence[Change], profiles: Mapping[tuple[str, str], KindProfile], sizes: Mapping[str, int]) -> Envelope:
    """
    The signs the changes can give every entry (C4, layer 2): added items contribute their vocabulary's signs, removed
    items the opposite, modified, rewritten, and flagged items both, grown items up on their element counts.

    Raises:
        KeyError: If a change names a kind no recorded item has.
    """
    sums: dict[Entry, Signs] = {}
    kinds: dict[str, KindDelta] = {}
    for c in changes:
        matched = [p for (g, k), p in profiles.items() if k == c.kind and (c.group is None or g == c.group)]
        if not matched and c.entries is None:
            raise KeyError(f"No recorded items of kind {c.kind!r} (group {c.group!r}).")
        delta = kinds.setdefault(c.kind, KindDelta())
        how = c.how
        for p in matched:
            # A2: adding or removing items of a kind whose items are not local can change the existing ones.
            if how in ("add", "remove") and not p.local:
                for key, tp in p.terms.items():
                    for e in _entries(key, tp, sizes[key[0]]):
                        _add(sums, e, BOTH)
            for key, tp in p.terms.items():
                family = key[0]
                in_scope = c.families is None or family in c.families
                if how == "add":
                    for e, s in _added_signs(key, tp, sizes[family], c.keys).items():
                        _add(sums, e, s)
                elif how == "remove":
                    for e, s in _added_signs(key, tp, sizes[family], None).items():
                        _add(sums, e, negate(s))
                elif how == "flag":
                    # A flagged item may come with any content, so any count of its family.
                    for e in _added_signs(key, tp, sizes[family], None):
                        _add(sums, e, BOTH)
                elif how in ("modify", "rewrite") and in_scope:
                    if _unconditional(p, key) or (how == "rewrite" and tp.per_byte and tp.op == "add"):
                        continue
                    for e in _entries(key, tp, sizes[family]):
                        _add(sums, e, BOTH)
                elif how == "grow":
                    if tp.per_byte and tp.op in ("add", "bins"):
                        for e in _entries(key, tp, sizes[family]):
                            _add(sums, e, UP)
                    elif tp.per_byte or (c.families is not None and family in c.families):
                        for e in _entries(key, tp, sizes[family]):
                            _add(sums, e, BOTH)
            if how in ("add", "flag"):
                delta.added = True
            if how in ("remove", "flag"):
                delta.removed = True
            for a in p.attrs:
                if how == "flag" or (how == "modify" and (c.attrs is None or a in c.attrs)):
                    delta.attrs[a] = delta.attr(a) | BOTH
                elif how == "rewrite" and (c.attrs is None or a in c.attrs) and a not in p.growing:
                    delta.attrs[a] = delta.attr(a) | BOTH
                elif how == "grow":
                    if a in p.growing:
                        delta.attrs[a] = delta.attr(a) | UP
                    elif c.attrs is None or a in c.attrs:
                        delta.attrs[a] = delta.attr(a) | BOTH
        for e, s in c.entries or ():
            if how in ("modify", "rewrite") and any(_unconditional(p, e) for p in matched):
                continue
            _add(sums, e, s)
    return Envelope(sums, kinds, dict(profiles), dict(sizes))


def region_changes(table: ItemTable, region: Sequence[Range], content_kinds: Mapping[str, ChangeHow], zero: bool = False, declared: Optional[Mapping[str, ChangeHow]] = None) -> list[Change]:
    """
    The changes an in-place write over `region`, with any content (or zeros), makes on one object.

    Items whose locating ranges the region meets are flagged, unless the catalogue declares what happens to their kind
    (`declared`, e.g., "remove"); items whose members it meets are modified in the entries and attributes read from
    the region (with zeros, their nonnegative slots fall), except their element counts (per-element add terms, e.g.,
    a length): an in-place write keeps the number of elements. Items of the `content_kinds` (recognized from content
    wherever it lies, e.g., strings and byte counts) change as the mapping says ("rewrite" or "flag").

    Args:
        table: The object's item table.
        region: The elements written.
        content_kinds: The kinds recognized from content anywhere, and how an in-place write changes them.
        zero: Whether the content is all zeros (else any).
        declared: The change for kinds whose locating ranges the region meets.

    Returns:
        The changes, one per affected item (callers union them over objects).
    """
    if not region:
        return []
    declared = declared or {}
    out = [Change(how, kind) for kind, how in content_kinds.items()]
    for item in table.items:
        if item.kind in content_kinds:
            continue
        if any(meets(item.locating, r) for r in region):
            out.append(Change(declared.get(item.kind, "flag"), item.kind, group=item.group))
            continue
        hit = [t for t in item.terms if any(meets(t.ranges, r) for r in region) and not (t.op == "add" and t.per_byte)]
        attrs = frozenset(a for a, units in item.attr_ranges.items() if any(meets(u, r) for u in units for r in region))
        if not hit and not attrs:
            continue
        whole = frozenset(t.family for t in hit if t.op in _WHOLE_FAMILY)
        entries: dict[Entry, Signs] = {}
        for t in hit:
            if t.op not in _WHOLE_FAMILY:
                down = zero and t.op == "slot" and t.value >= 0
                entries[(t.family, t.index)] = (DOWN if t.value > 0 else FIXED) if down else BOTH
        out.append(Change("modify", item.kind, group=item.group, families=whole, attrs=attrs, entries=tuple(sorted(entries.items(), key=lambda x: x[0]))))
    return out


################################################################################
# C4: readouts
################################################################################


def _item_signs(env: Envelope, kinds: Sequence[str], attr: str, group: Optional[str]) -> tuple[KindDelta, list[KindProfile]]:
    # NOTE: deltas are kept per kind over every group (sound: items of the kind in another group change with it).
    delta = KindDelta()
    for k in kinds:
        d = env.kinds.get(k)
        if d is not None:
            delta.added |= d.added
            delta.removed |= d.removed
            delta.attrs[attr] = delta.attr(attr) | d.attr(attr)
    return delta, [p for (g, k), p in env.profiles.items() if k in kinds and (group is None or g == group)]


def readout_signs(r: Readout, env: Envelope) -> list[Signs]:
    """The signs a readout's features can take, from the envelope (the global C4 rule of each readout type)."""
    if isinstance(r, Outside):
        return [BOTH] * r.dim
    if isinstance(r, Identity):  # also Selection
        return env.family(r.family, r.start, r.size)
    if isinstance(r, Ratio):
        return [ratio_signs(env.entry(*r.num), env.entry(*r.den))]
    if isinstance(r, Normalized):
        v = env.family(r.family, 0, r.size)
        moved = [s for s in v if s]
        if not moved:
            return v
        union = frozenset().union(*moved)
        # One entry moving carries its share with it; with several, any can lose share to another.
        return [(s if len(moved) == 1 else BOTH) if s else negate(union) for s in v]
    if isinstance(r, Entropy):
        return [BOTH if any(env.family(r.family)) else FIXED]
    if isinstance(r, Max):
        delta, _ = _item_signs(env, r.kinds, r.attr, r.group)
        top = (UP if delta.added else FIXED) | (DOWN if delta.removed else FIXED) | delta.attr(r.attr)
        return [ratio_signs(top, env.entry(*r.divide_by)) if r.divide_by is not None else top]
    if isinstance(r, Min):
        delta, profiles = _item_signs(env, r.kinds, r.attr, r.group)
        # With every recorded value at or above the floor, the minimum is the floor (constant; see items.Min).
        if all(p.attrs.get(r.attr, (math.inf, 0.0))[0] >= r.floor for p in profiles):
            return [FIXED]
        low = (DOWN if delta.added else FIXED) | (UP if delta.removed else FIXED) | delta.attr(r.attr)
        return [ratio_signs(low, env.entry(*r.divide_by)) if r.divide_by is not None else low]
    if isinstance(r, DistinctCount):
        v = env.family(r.family)
        return v if r.per_bucket else [frozenset().union(*v)]
    if isinstance(r, Positive):
        return [env.entry(*r.sum)]
    if isinstance(r, BitTest):
        return [BOTH if env.entry(*r.slot) else FIXED] * r.dim
    if isinstance(r, Lookup):
        return [BOTH if env.entry(*r.slot) else FIXED]
    if isinstance(r, Opaque):
        profiles = [p for (_, k), p in env.profiles.items() if k == r.kind]
        out = []
        for i, (a, default) in enumerate(zip(r.attrs, r.defaults, strict=True)):
            if r.ranges is not None:
                lo, hi = r.ranges[i]
            else:
                lo = min((p.attrs[a][0] for p in profiles if a in p.attrs), default=math.inf)
                hi = max((p.attrs[a][1] for p in profiles if a in p.attrs), default=-math.inf)
            # An item's value against the default (taken when there is no item), over the declared (or recorded) range.
            if lo > hi:
                appear = BOTH
            elif lo >= default and hi <= default:
                appear = FIXED
            elif lo >= default:
                appear = UP
            elif hi <= default:
                appear = DOWN
            else:
                appear = BOTH
            d = env.kinds.get(r.kind, KindDelta())
            out.append((appear if d.added else FIXED) | (negate(appear) if d.removed else FIXED) | d.attr(a))
        return out
    raise TypeError(f"No C4 rule for readout {type(r).__name__}.")


def directions(readouts: Sequence[Readout], changes: Mapping[str, Sequence[Change]], profiles: Mapping[tuple[str, str], KindProfile], sizes: Mapping[str, int]) -> dict[str, list[Signs]]:
    """
    C4: for each operation, the signs it can give every feature on some object.

    Args:
        readouts: The features' readouts, in feature order.
        changes: Each operation's changes (from the catalogue).
        profiles: The kinds' vocabulary (`profile_kinds`).
        sizes: The families' sizes.

    Returns:
        Per operation, one set of signs per feature.
    """
    out = {}
    for op, cs in changes.items():
        env = envelope(cs, profiles, sizes)
        out[op] = [s for r in readouts for s in readout_signs(r, env)]
    return out
