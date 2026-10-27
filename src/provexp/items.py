"""
The item layer of feature provenance (docs/feature-provenance-model.md, Sections 2-4; docs/item-layer-design.md).

A feature extractor works in three layers: it finds the items of an object (layer 1: which elements make up each item
and which decide where it is), adds up what each item contributes to named sums (layer 2), and applies a formula per
feature to the sums (layer 3, the readout). This module holds the generic types for the last two layers and knows
nothing about any file format:

    Term        one contribution of an item to a sum, in a small vocabulary whose sign behavior is known
    Item        a kind, its terms, its attributes, and the element ranges it is read from and located by
    ItemTable   the items of one object, with the sums they add up to
    Readout     a feature formula over the sums or the items, as data (identity, ratio, normalized, entropy, ...)

`evaluate` applies the readouts to an item table, which must reproduce the extractor's feature vector exactly, and
`project` spreads the items over their elements, which must reproduce the extractor's raw provenance
(provexp.provenance) under its conventions.
"""

from __future__ import annotations
from collections import defaultdict
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from functools import cached_property
import math
from typing import Any
from typing import Literal
from typing import Optional

import numpy as np
from numpy import typing as npt
from sklearn.feature_extraction import FeatureHasher

from provexp.boxmatrix import BoxMatrix
from provexp.boxmatrix import FloatArray
from provexp.boxmatrix import IntArray
from provexp.boxmatrix import expand_ranges


__all__ = [
    "Range",
    "TermOp",
    "Term",
    "Item",
    "ItemTable",
    "Readout",
    "Identity",
    "Selection",
    "Ratio",
    "Normalized",
    "Entropy",
    "Max",
    "Min",
    "DistinctCount",
    "Positive",
    "BitTest",
    "Lookup",
    "Opaque",
    "Outside",
    "evaluate",
    "project",
    "feature_hash",
    "merge_ranges",
]


Range = tuple[int, int]


################################################################################
# Helpers
################################################################################


def merge_ranges(ranges: Iterable[Range]) -> tuple[Range, ...]:
    """The union of half-open ranges as sorted, disjoint, nonempty ranges."""
    out: list[Range] = []
    for lo, hi in sorted(r for r in ranges if r[1] > r[0]):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return tuple(out)


def feature_hash(n_features: int, keys: Sequence[str]) -> tuple[IntArray, IntArray]:
    """
    The bucket and sign sklearn's FeatureHasher gives each key (the sign is +1 for every key when hashing is unsigned).

    Args:
        n_features: The number of buckets.
        keys: The keys.

    Returns:
        The bucket of each key and its sign under `alternate_sign=True`, each of shape (len(keys),).
    """
    if len(keys) == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    X = FeatureHasher(n_features, input_type="string", alternate_sign=True).transform([[k] for k in keys]).tocsr()
    if not np.all(np.diff(X.indptr) == 1):
        raise RuntimeError("Expected each key to hash into exactly one bucket.")
    return X.indices.astype(np.int64), np.sign(X.data).astype(np.int64)


################################################################################
# Items
################################################################################


TermOp = Literal["count", "add", "bins", "hashed", "keyed", "slot"]


@dataclass(frozen=True, eq=False)
class Term:
    """
    One contribution of an item to a sum (a family of sums, entry `index`).

    The ops, and the sign of the contribution when the item is added (docs/item-layer-design.md, Section 1):
        count   +1                                                          +
        add     `value`, declared nonnegative                               + or 0
        bins    the count of each bin of `bin_key` over `ranges`, into
                entries `index + bin_key[i]` (nonnegative counts)           + or 0 per bin
        hashed  `sign * value` into the bucket `index` of the key `key`     + if unsigned, else the key's sign
        keyed   +1 to the count of `key` in bucket `index` (read by DistinctCount)  +
        slot    `value`, a field read from exactly one item                 any (modify only)

    Attributes:
        op: The kind of contribution.
        family: The family of sums contributed to.
        index: The entry within the family (the first entry for bins).
        value: The amount (one for count and keyed; unused for bins).
        sign: The hash sign for hashed terms, otherwise +1.
        key: The hashed or keyed key.
        attr: The item attribute the value is read from, if any.
        ranges: The elements the value (and key) is read from: the term's provenance.
        per_byte: Whether the term's provenance is one unit per element (content, e.g., a size or a byte count)
            rather than one unit spread over its elements (an item counted once).
        bin_key: For bins, the bin of every element of the object (only the elements in `ranges` are read).
    """

    op: TermOp
    family: str
    index: int = 0
    value: float = 1.0
    sign: int = 1
    key: Optional[str] = None
    attr: Optional[str] = None
    ranges: tuple[Range, ...] = ()
    per_byte: bool = False
    bin_key: Optional[npt.NDArray[np.integer]] = None

    def __post_init__(self) -> None:
        if self.op not in ("count", "add", "bins", "hashed", "keyed", "slot"):
            raise ValueError(f"Unknown term op: {self.op}")
        if self.index < 0:
            raise ValueError(f"Expected a nonnegative index. Got {self.index}.")
        if self.op in ("count", "keyed") and self.value != 1.0:
            raise ValueError(f"A {self.op} term contributes exactly one. Got {self.value}.")
        if self.op in ("add", "hashed") and not self.value >= 0:
            raise ValueError(f"A {self.op} term's value is declared nonnegative. Got {self.value}.")
        if self.sign not in (-1, 1) or (self.sign != 1 and self.op != "hashed"):
            raise ValueError(f"Only hashed terms carry a sign, of +1 or -1. Got {self.sign} on a {self.op} term.")
        if self.op in ("hashed", "keyed") and self.key is None:
            raise ValueError(f"A {self.op} term needs a key.")
        if (self.op == "bins") != (self.bin_key is not None):
            raise ValueError("Exactly the bins terms carry a bin key.")

    @property
    def amount(self) -> float:
        """The signed amount added to the sum (bins: see `bin_counts`)."""
        return self.sign * self.value

    def bin_counts(self, size: int) -> IntArray:
        """The counts a bins term adds to entries `index, ..., index + size - 1` of its family."""
        if self.bin_key is None:
            raise RuntimeError("Only bins terms have bin counts.")
        lo = np.array([r[0] for r in self.ranges], dtype=np.int64)
        hi = np.array([r[1] for r in self.ranges], dtype=np.int64)
        _, rows = expand_ranges(lo, hi)
        keys = self.bin_key[rows]
        if keys.size > 0 and (keys.min() < 0 or keys.max() >= size):
            raise IndexError(f"Bins of {self.family} out of range [0, {size}).")
        return np.bincount(keys.astype(np.int64), minlength=size)


Units = tuple[tuple[Range, ...], ...]


@dataclass(eq=False)
class Item:
    """
    One item of an object: a kind, its contributions, and the elements it is read from and located by.

    Attributes:
        kind: The item's kind (e.g., "section", "string", "window", "field").
        terms: Its contributions to the sums.
        attrs: The attributes readouts may read directly (e.g., a section's entropy, read by a max readout).
        attr_ranges: The provenance of each attribute read directly, as units: each unit is a tuple of ranges over
            which one unit of contribution is spread.
        locating: The elements that decide whether the item exists and where it is (assumption A1).
        local: Whether the item's contribution depends only on its own elements (assumption A2). An item whose
            contribution can be changed by another item (e.g., erased by a later one) is not local.
        open_end: Whether the item extends to the end of the object, so that appended elements join it (e.g., data
            appended to a file).
        group: The feature type that recorded the item (set by the extractor; recognizers are per group).
    """

    kind: str
    terms: tuple[Term, ...] = ()
    attrs: dict[str, Any] = field(default_factory=dict)
    attr_ranges: dict[str, Units] = field(default_factory=dict)
    locating: tuple[Range, ...] = ()
    local: bool = True
    open_end: bool = False
    group: str = ""

    @property
    def members(self) -> tuple[Range, ...]:
        """The elements the item's content is read from: the union of its terms' and attributes' ranges."""
        ranges = [r for t in self.terms for r in t.ranges]
        ranges += [r for units in self.attr_ranges.values() for unit in units for r in unit]
        return merge_ranges(ranges)


class ItemTable:
    """
    The items of one object and the families of sums they contribute to.

    Args:
        num_elements: The number of elements of the object (bytes, for a file).
        families: The dimension of each family of sums.
        items: The items.
    """

    def __init__(self, num_elements: int, families: Mapping[str, int], items: Sequence[Item]) -> None:
        if num_elements < 0:
            raise ValueError(f"Expected a nonnegative number of elements. Got {num_elements}.")
        self.num_elements = int(num_elements)
        self.families = dict(families)
        self.items = list(items)
        for item in self.items:
            for t in item.terms:
                if t.family not in self.families:
                    raise KeyError(f"Item of kind {item.kind!r} contributes to an undeclared family {t.family!r}.")
                if t.op != "bins" and t.index >= self.families[t.family]:
                    raise IndexError(f"Index {t.index} out of range for family {t.family!r} of {self.families[t.family]}.")
                for lo, hi in t.ranges:
                    if not 0 <= lo <= hi <= self.num_elements:
                        raise IndexError(f"Range {(lo, hi)} of a {item.kind!r} item is outside [0, {self.num_elements}].")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(num_elements={self.num_elements}, families={len(self.families)}, items={len(self.items)})"

    def __len__(self) -> int:
        return len(self.items)

    @classmethod
    def concatenate(cls, tables: Sequence[ItemTable]) -> ItemTable:
        """The union of item tables over the same object with disjoint families."""
        if len(tables) == 0:
            raise ValueError("Cannot concatenate an empty sequence of item tables.")
        m = tables[0].num_elements
        if any(t.num_elements != m for t in tables):
            raise ValueError(f"Expected tables over the same number of elements. Got {[t.num_elements for t in tables]}.")
        families: dict[str, int] = {}
        for t in tables:
            overlap = families.keys() & t.families.keys()
            if overlap:
                raise ValueError(f"Families declared twice: {sorted(overlap)}.")
            families.update(t.families)
        return cls(m, families, [item for t in tables for item in t.items])

    def filter(self, keep: Callable[[Item], bool]) -> ItemTable:
        """The table of the items for which `keep` is true, over the same families."""
        return ItemTable(self.num_elements, self.families, [item for item in self.items if keep(item)])

    def of_kind(self, *kinds: str) -> list[Item]:
        """The items of the given kinds, in table order."""
        return [item for item in self.items if item.kind in kinds]

    def terms(self, family: str) -> list[Term]:
        """The terms contributing to a family, in table order."""
        return self._terms_by_family.get(family, [])

    @cached_property
    def _terms_by_family(self) -> dict[str, list[Term]]:
        out: dict[str, list[Term]] = defaultdict(list)
        for item in self.items:
            for t in item.terms:
                out[t.family].append(t)
        return dict(out)

    @cached_property
    def sums(self) -> dict[str, FloatArray]:
        """
        The value of every family of sums: the terms' amounts added in table order (bins: their counts).

        A slot may be written by at most one item; a slot no item writes stays zero (see `written`).
        """
        self.written  # Raises if two items write the same slot.
        return {f: self._family_sum(f) for f in self.families}

    def _family_sum(self, family: str) -> FloatArray:
        """One family of sums, added up in table order."""
        s = np.zeros(self.families[family], dtype=np.float64)
        for t in self.terms(family):
            if t.op == "bins":
                s[t.index:] += t.bin_counts(s.shape[0] - t.index)
            elif t.op == "slot":
                s[t.index] = t.value
            else:
                s[t.index] += t.amount
        return s

    @cached_property
    def written(self) -> set[tuple[str, int]]:
        """The slots some item writes, as (family, index). Raises if two items write the same slot."""
        out: set[tuple[str, int]] = set()
        for item in self.items:
            for t in item.terms:
                if t.op == "slot":
                    if (t.family, t.index) in out:
                        raise ValueError(f"Slot {t.family}[{t.index}] is written by more than one item.")
                    out.add((t.family, t.index))
        return out

    def of_group(self, group: str) -> list[Item]:
        """The items a feature type recorded, in table order."""
        return [item for item in self.items if item.group == group]

    def replace(self, removed: Sequence[Item], added: Sequence[Item], num_elements: Optional[int] = None) -> ItemTable:
        """
        The table after an edit: `removed` (items of this table) leave, `added` join, and the sums are updated.

        Each added item takes the place of the first unused removed item of its group and kind (a modified item keeps
        its place), or else goes after the last item of its group and kind (at the end if there is none); this keeps
        the order the extractor records, which float sums depend on. Families whose changed terms are all integral counts, sums, or
        bins are updated by adding and subtracting the changed contributions, which is exact; the others (slots,
        fractional hashed values) are added up again in table order, as the extractor does.

        Args:
            removed: Items of this table that the edit removes (or modifies: their new versions are in `added`).
            added: The new and modified items.
            num_elements: The object's new number of elements (default: unchanged).

        Returns:
            The new table.
        """
        gone = {id(item) for item in removed}
        if len(gone) != len(removed) or any(id(item) not in self._positions for item in removed):
            raise ValueError("Every removed item must be a distinct item of this table.")
        pending: dict[tuple[str, str], list[Item]] = defaultdict(list)
        for item in added:
            pending[(item.group, item.kind)].append(item)
        items: list[Item] = []
        for item in self.items:
            if id(item) not in gone:
                items.append(item)
            elif pending[(item.group, item.kind)]:
                items.append(pending[(item.group, item.kind)].pop(0))
        for (group, kind), rest in pending.items():
            for item in rest:
                last = max((i for i, x in enumerate(items) if x.group == group and x.kind == kind), default=len(items) - 1)
                items.insert(last + 1, item)
        out = ItemTable(self.num_elements if num_elements is None else num_elements, self.families, items)

        out.written  # Raises if two items write the same slot.
        sums = dict(self.sums)
        changed = [(t, -1) for item in removed for t in item.terms] + [(t, 1) for item in added for t in item.terms]
        inexact = {t.family for t, _ in changed if t.op == "slot" or (t.op != "bins" and not float(t.amount).is_integer())}
        for family in {t.family for t, _ in changed} - inexact:
            sums[family] = sums[family].copy()
        for t, sign in changed:
            if t.family in inexact:
                continue
            s = sums[t.family]
            if t.op == "bins":
                s[t.index:] += sign * t.bin_counts(s.shape[0] - t.index)
            else:
                s[t.index] += sign * t.amount
        for family in inexact:
            sums[family] = out._family_sum(family)
        out.__dict__["sums"] = sums  # Fills the cached property.
        return out

    @cached_property
    def _positions(self) -> dict[int, int]:
        return {id(item): i for i, item in enumerate(self.items)}

    def key_counts(self, family: str) -> dict[str, tuple[int, int]]:
        """For a family of keyed terms: each key's bucket and the number of terms that add it, in first-seen order."""
        out: dict[str, tuple[int, int]] = {}
        for t in self.terms(family):
            if t.op != "keyed" or t.key is None:
                raise ValueError(f"Family {family!r} has a {t.op} term; expected keyed terms only.")
            bucket, count = out.get(t.key, (t.index, 0))
            if bucket != t.index:
                raise ValueError(f"Key {t.key!r} is added to two buckets of {family!r}.")
            out[t.key] = (bucket, count + 1)
        return out


################################################################################
# Projection onto the elements
################################################################################


class _Projection:
    """Accumulates raw contributions (the conventions of provexp.provenance) and builds a BoxMatrix."""

    def __init__(self, num_elements: int, num_features: int) -> None:
        self.matrix = BoxMatrix((num_elements, num_features))
        self.m = num_elements
        self._lo: list[int] = []
        self._hi: list[int] = []
        self._col: list[int] = []
        self._w: list[float] = []

    def add_unit(self, col: int, ranges: Sequence[Range]) -> None:
        """One unit spread uniformly over the elements of `ranges`."""
        clipped = [(max(0, min(lo, self.m)), max(0, min(hi, self.m))) for lo, hi in ranges]
        clipped = [r for r in clipped if r[1] > r[0]]
        total = sum(hi - lo for lo, hi in clipped)
        for lo, hi in clipped:
            self._lo.append(lo)
            self._hi.append(hi)
            self._col.append(col)
            self._w.append(1.0 / total)

    def add_per_element(self, col: int, ranges: Sequence[Range]) -> None:
        """One unit per element of `ranges`."""
        for lo, hi in ranges:
            if hi > lo:
                self._lo.append(lo)
                self._hi.append(hi)
                self._col.append(col)
                self._w.append(1.0)

    def add_term(self, col: int, t: Term) -> None:
        """A term's provenance in column `col` (bins: columns `col + bin_key[i]`)."""
        if t.op == "bins":
            assert t.bin_key is not None
            k = self.matrix.add_key(t.bin_key)
            lo = np.array([r[0] for r in t.ranges], dtype=np.int64)
            hi = np.array([r[1] for r in t.ranges], dtype=np.int64)
            self.matrix.add_keyed_boxes(lo, hi, np.full(lo.shape, col, dtype=np.int64), k)
        elif t.per_byte:
            self.add_per_element(col, t.ranges)
        else:
            self.add_unit(col, t.ranges)

    def build(self) -> BoxMatrix:
        col = np.array(self._col, dtype=np.int64)
        self.matrix.add_boxes(
            np.array(self._lo, dtype=np.int64),
            np.array(self._hi, dtype=np.int64),
            col,
            col + 1,
            np.array(self._w, dtype=np.float64),
        )
        return self.matrix


################################################################################
# Readouts
################################################################################


class Readout:
    """
    A block of `dim` consecutive features computed from an item table by one formula (layer 3).

    Subclasses implement `evaluate` (the features' values) and `project` (their provenance: which terms or items
    contribute, under the conventions of provexp.provenance: denominators and selection rules do not contribute).
    """

    dim: int = 1

    def evaluate(self, table: ItemTable) -> npt.NDArray[np.floating[Any]]:
        raise NotImplementedError

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        raise NotImplementedError


def _project_family(table: ItemTable, out: _Projection, col: int, family: str, start: int, stop: int) -> None:
    """The provenance of entries [start, stop) of a family: each term in column `col + index - start`."""
    for t in table.terms(family):
        if t.op == "bins":
            if start != 0 or stop != table.families[family]:
                raise ValueError(f"Bins terms of {family!r} can only be projected with the whole family.")
            out.add_term(col + t.index, t)
        elif start <= t.index < stop:
            out.add_term(col + t.index - start, t)


@dataclass(frozen=True)
class Identity(Readout):
    """Entries [start, start + size) of a family of sums (counts, raw sums, hashed buckets, fields)."""

    family: str
    start: int = 0
    size: int = 1

    @property
    def dim(self) -> int:  # type: ignore[override]
        return self.size

    def evaluate(self, table: ItemTable) -> FloatArray:
        return table.sums[self.family][self.start:self.start + self.size]

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        _project_family(table, out, col, self.family, self.start, self.start + self.size)


@dataclass(frozen=True)
class Selection(Identity):
    """A family written by the one item a selection rule picks (e.g., the entry section's hashed name)."""


@dataclass(frozen=True)
class Ratio(Readout):
    """num / den, or `default` when den is zero. The numerator's terms contribute."""

    num: tuple[str, int]
    den: tuple[str, int]
    default: float = 0.0

    def evaluate(self, table: ItemTable) -> FloatArray:
        n = table.sums[self.num[0]][self.num[1]]
        d = table.sums[self.den[0]][self.den[1]]
        return np.array([float(n) / float(d) if d != 0 else self.default])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        _project_family(table, out, col, self.num[0], self.num[1], self.num[1] + 1)


@dataclass(frozen=True)
class Normalized(Readout):
    """
    A family divided by its total (a distribution). The family's terms contribute.

    `precision` mirrors the extractor's arithmetic: "float32" divides float32 counts by their float32 total (an empty
    family gives NaN, as the extractor does); "float64" divides by the total, or by one when the total is zero.
    """

    family: str
    size: int
    precision: Literal["float32", "float64"] = "float32"

    @property
    def dim(self) -> int:  # type: ignore[override]
        return self.size

    def evaluate(self, table: ItemTable) -> npt.NDArray[np.floating[Any]]:
        s = table.sums[self.family]
        if self.precision == "float32":
            c = s.astype(np.float32)
            with np.errstate(invalid="ignore", divide="ignore"):
                out32: npt.NDArray[np.float32] = c / c.sum()
            return out32
        total = float(s.sum())
        return s.astype(np.int64) / (total if total > 0 else 1.0)

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        _project_family(table, out, col, self.family, 0, self.size)


@dataclass(frozen=True)
class Entropy(Readout):
    """
    The Shannon entropy (bits) of a family of counts. Every element of the family's terms contributes.

    `precision` mirrors the extractor's arithmetic: "python" accumulates -p log2 p in Python floats over the nonzero
    bins in index order; "numpy" computes p in float32 over the int64 total and sums -p log2 p with numpy.
    """

    family: str
    precision: Literal["python", "numpy"] = "python"

    def evaluate(self, table: ItemTable) -> FloatArray:
        c = table.sums[self.family].astype(np.int64)
        if self.precision == "python":
            size = int(c.sum())
            H = 0.0
            for x in c.tolist():
                if x > 0:
                    p_x = float(x) / size
                    H -= p_x * math.log(p_x, 2)
            return np.array([H])
        csum = c.sum()
        if csum == 0:
            return np.array([0.0])
        p = c.astype(np.float32) / csum
        wh = np.where(c)[0]
        return np.array([float(np.sum(-p[wh] * np.log2(p[wh])))])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        for t in table.terms(self.family):
            if t.per_byte or t.op == "bins":
                out.add_per_element(col, t.ranges)
            else:
                out.add_unit(col, t.ranges)


def _attr_values(table: ItemTable, kinds: tuple[str, ...], attr: str) -> list[tuple[Item, float]]:
    return [(item, float(item.attrs[attr])) for item in table.of_kind(*kinds)]


@dataclass(frozen=True)
class Max(Readout):
    """
    The largest attribute over the items of some kinds and `floor`, divided by a sum if `divide_by` is given (by zero:
    zero). The items that attain the maximum contribute, through their attribute's provenance.
    """

    kinds: tuple[str, ...]
    attr: str
    floor: float = 0.0
    divide_by: Optional[tuple[str, int]] = None

    def _best(self, table: ItemTable) -> tuple[list[tuple[Item, float]], float]:
        values = _attr_values(table, self.kinds, self.attr)
        return values, max([v for _, v in values] + [self.floor])

    def evaluate(self, table: ItemTable) -> FloatArray:
        _, best = self._best(table)
        if self.divide_by is not None:
            d = float(table.sums[self.divide_by[0]][self.divide_by[1]])
            best = best / d if d != 0 else 0.0
        return np.array([best])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        values, _ = self._best(table)
        if not values:
            return
        top = max(v for _, v in values)
        for item, v in values:
            if v == top:
                for unit in item.attr_ranges.get(self.attr, ()):
                    out.add_unit(col, unit)


@dataclass(frozen=True)
class Min(Readout):
    """
    The smallest attribute over the items of some kinds and `floor`, divided as in `Max`. With nonnegative attributes
    and a zero floor it is constant, and nothing contributes (NOTE (Axiom 3)).
    """

    kinds: tuple[str, ...]
    attr: str
    floor: float = 0.0
    divide_by: Optional[tuple[str, int]] = None

    def evaluate(self, table: ItemTable) -> FloatArray:
        values = _attr_values(table, self.kinds, self.attr)
        best = min([v for _, v in values] + [self.floor])
        if self.divide_by is not None:
            d = float(table.sums[self.divide_by[0]][self.divide_by[1]])
            best = best / d if d != 0 else 0.0
        return np.array([best])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        values = _attr_values(table, self.kinds, self.attr)
        if not values or min(v for _, v in values) >= self.floor:
            return
        low = min(v for _, v in values)
        for item, v in values:
            if v == low:
                for unit in item.attr_ranges.get(self.attr, ()):
                    out.add_unit(col, unit)


@dataclass(frozen=True)
class DistinctCount(Readout):
    """
    The number of distinct keys of a keyed family, in total (`per_bucket=False`, one feature) or per bucket (one
    feature per bucket). Each key contributes one unit spread over the ranges of all the terms that add it.
    """

    family: str
    size: int = 1
    per_bucket: bool = False

    @property
    def dim(self) -> int:  # type: ignore[override]
        return self.size if self.per_bucket else 1

    def evaluate(self, table: ItemTable) -> FloatArray:
        keys = table.key_counts(self.family)
        if not self.per_bucket:
            return np.array([float(len(keys))])
        out = np.zeros(self.size)
        for bucket, _ in keys.values():
            out[bucket] += 1
        return out

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        ranges: dict[str, list[Range]] = defaultdict(list)
        buckets: dict[str, int] = {}
        for t in table.terms(self.family):
            assert t.key is not None
            ranges[t.key].extend(t.ranges)
            buckets[t.key] = t.index
        for key, rs in ranges.items():
            out.add_unit(col + (buckets[key] if self.per_bucket else 0), rs)


@dataclass(frozen=True)
class Positive(Readout):
    """`scale` if the sum is positive, else zero. NOTE (Axiom 3): it receives no contributions, as in the extractor."""

    sum: tuple[str, int]
    scale: float = 1.0

    def evaluate(self, table: ItemTable) -> FloatArray:
        return np.array([self.scale if table.sums[self.sum[0]][self.sum[1]] > 0 else 0.0])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        return


@dataclass(frozen=True)
class BitTest(Readout):
    """
    Whether each mask shares a bit with a slot (a flag of a bit field): one feature per mask, zero when no item writes
    the slot. The slot's terms contribute to every one of them.
    """

    slot: tuple[str, int]
    masks: tuple[int, ...]

    @property
    def dim(self) -> int:  # type: ignore[override]
        return len(self.masks)

    def evaluate(self, table: ItemTable) -> FloatArray:
        v = int(table.sums[self.slot[0]][self.slot[1]])
        return np.array([1.0 if v & m else 0.0 for m in self.masks])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        for i in range(len(self.masks)):
            _project_family(table, out, col + i, self.slot[0], self.slot[1], self.slot[1] + 1)


@dataclass(frozen=True)
class Lookup(Readout):
    """A category code of a slot: `table[value]`, `default` for unlisted values, `absent` when no item writes it."""

    slot: tuple[str, int]
    table: Mapping[int, float]
    default: float = 0.0
    absent: float = 0.0

    def evaluate(self, table: ItemTable) -> FloatArray:
        if self.slot not in table.written:
            return np.array([self.absent])
        return np.array([self.table.get(int(table.sums[self.slot[0]][self.slot[1]]), self.default)])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        _project_family(table, out, col, self.slot[0], self.slot[1], self.slot[1] + 1)


@dataclass(frozen=True)
class Opaque(Readout):
    """
    Attributes of the one item of a kind, computed by a parser the model does not open; each attribute's default when
    there is no such item. Each attribute's provenance units contribute to its feature.
    """

    kind: str
    attrs: tuple[str, ...]
    defaults: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.attrs) != len(self.defaults):
            raise ValueError(f"Expected one default per attribute. Got {len(self.attrs)} and {len(self.defaults)}.")

    @property
    def dim(self) -> int:  # type: ignore[override]
        return len(self.attrs)

    def _item(self, table: ItemTable) -> Optional[Item]:
        items = table.of_kind(self.kind)
        if len(items) > 1:
            raise ValueError(f"Expected at most one item of kind {self.kind!r}. Got {len(items)}.")
        return items[0] if items else None

    def evaluate(self, table: ItemTable) -> FloatArray:
        item = self._item(table)
        if item is None:
            return np.array(self.defaults, dtype=np.float64)
        return np.array([float(item.attrs[a]) for a in self.attrs])

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        item = self._item(table)
        if item is None:
            return
        for i, a in enumerate(self.attrs):
            for unit in item.attr_ranges.get(a, ()):
                out.add_unit(col + i, unit)


@dataclass(frozen=True)
class Outside(Readout):
    """Features outside the model (no items): evaluated as NaN, no contributions."""

    size: int = 1

    @property
    def dim(self) -> int:  # type: ignore[override]
        return self.size

    def evaluate(self, table: ItemTable) -> FloatArray:
        return np.full(self.size, np.nan)

    def project(self, table: ItemTable, out: _Projection, col: int) -> None:
        return


################################################################################
# Evaluation and projection
################################################################################


def evaluate(table: ItemTable, readouts: Sequence[Readout]) -> npt.NDArray[np.float32]:
    """
    The feature vector the readouts compute from an item table, in float32 (NaN for features outside the model).
    """
    if len(readouts) == 0:
        return np.zeros(0, dtype=np.float32)
    parts = []
    for r in readouts:
        v = np.asarray(r.evaluate(table))
        if v.shape != (r.dim,):
            raise RuntimeError(f"{r!r} returned shape {v.shape}; expected ({r.dim},).")
        parts.append(v.astype(np.float64))
    return np.hstack(parts).astype(np.float32)


def project(table: ItemTable, readouts: Sequence[Readout]) -> BoxMatrix:
    """
    The raw contributions of the elements to the features, as an (num_elements, num_features) BoxMatrix: each
    readout's contributing terms and items spread over their elements (see `Term` and the readouts' docstrings).
    """
    out = _Projection(table.num_elements, sum(r.dim for r in readouts))
    col = 0
    for r in readouts:
        r.project(table, out, col)
        col += r.dim
    return out.build()
