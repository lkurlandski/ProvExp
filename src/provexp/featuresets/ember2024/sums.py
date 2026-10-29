"""
The layer-2 re-encodings of EMBER v3 (direction A, docs/direction-A-threat-model.md, Section 2): sums the extractor
computes before its readout normalizes, ratios, or signs them, read so that the attacker's additions can only raise
them.

`SumsFeatureExtractor` is thrember's extractor with the duplicate-DLL import quirk fixed (`merge_import_descriptors`),
followed by four feature types:
    body_histogram      raw byte counts over the body regions (re-encodings 1 and 2)
    body_byteentropy    raw byte/entropy counts over windows tiled per body region (re-encoding 2)
    body_strings        raw string, printable-character, and regex counts over the body regions (re-encodings 1, 2)
    section_split       the signed section buckets split into their positive and negative parts (re-encoding 3)
The fixed imports are re-encoding 4. Every feature of the original extractor is kept, so one feature store serves both
the "C4 on sums" detector and the matched "C4 on features" control (which neutralizes the four added groups).

The body regions are the parts of the file M writes nowhere in place: the data of each section, without its slack
(the raw data past its virtual size) and without anything below SizeOfHeaders, and every run past SizeOfHeaders that
no section's raw data claims (the gaps between sections and the overlay). Adding a section or an import section adds a
region (and may turn the overlay into a gap, which keeps its bytes); appending extends the run that ends the file (or,
past a section whose declared raw data overruns the file, that section's region); an insertion adds a run or extends
one at its end, and moves the other regions without changing their content.

Each group also records its items (derivation step 8, docs/item-layer-design.md: "The re-encodings come for free"):
the byte runs, windows, and strings of each body region, and the sections with each hashed value split by its sign.
Their readouts are identities over the sums, so C4 (provexp.reach) derives the re-encodings' directions with no rule of
their own. The body items are their own kinds, located through what decides the body regions: unlike the whole-file
bytes, windows, and strings, an in-place write outside the body regions does not reach them.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from functools import lru_cache
from typing import Any
from typing import Optional

import numpy as np
import pefile
from sklearn.feature_extraction import FeatureHasher

from provexp.featuresets.ember2024.features import ByteEntropyHistogram
from provexp.featuresets.ember2024.features import FeatureType
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import Range
from provexp.featuresets.ember2024.features import SectionInfo
from provexp.featuresets.ember2024.features import StringExtractor
from provexp.featuresets.ember2024.features import clipped
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import section_data_range
from provexp.featuresets.ember2024.features import section_locating
from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Readout
from provexp.items import Term

__all__ = [
    "SUMS_GROUPS",
    "BodyByteEntropyHistogram",
    "BodyByteHistogram",
    "BodyStrings",
    "SectionSplitBuckets",
    "SumsFeatureExtractor",
    "BodyRegion",
    "body_layout",
    "body_regions",
    "signed_bucket",
]

################################################################################
# Body regions
################################################################################


@dataclass(frozen=True)
class BodyRegion:
    """
    One body region: its bytes, the bytes that decide where it is (assumption A1), and whether appending extends it.

    Attributes:
        range: The region's bytes.
        locating: The bytes that decide whether the region exists and where it lies (unclipped: past the end of the
            file where a section's declared data or a directory's extent lies there).
        open_end: Whether the region ends at the end of the file and appending extends it (the overlay, or a section
            whose declared data runs past the end of the file).
    """

    range: Range
    locating: tuple[Range, ...]
    open_end: bool


def body_layout(bytez: bytes, pe: Optional[pefile.PE]) -> list[BodyRegion]:
    """
    The body regions of a file, in section order followed by the unclaimed runs; empty if the file did not parse.

    Each section contributes the data `get_entropy` reads (`section_data_range`), cut at its virtual size (when
    nonzero) and clipped to [SizeOfHeaders, len(bytez)). Each maximal run of bytes past SizeOfHeaders that no section's
    raw data claims (the gaps between sections and the overlay alike) is a region of its own. Regions are not merged:
    two sections whose raw data overlap are both counted, so that adding a region never changes how an existing one is
    read.

    Every region is located through the section table (`section_locating`) and SizeOfHeaders. Unlike pefile's overlay
    rule, the unclaimed runs do not depend on the data directories: a section added after the overlay turns it into a
    gap that starts where it did and keeps its bytes (G7), an append extends the run that ends the file, and an
    inserted gap is a run of its own or extends one at its end.

    NOTE: clipping at SizeOfHeaders keeps the header region out on files whose sections start inside it; the DOS
    extension (M_shift) raises SizeOfHeaders, which can move the clip on such files only (an A2 exception).
    """
    if pe is None:
        return []
    n = len(bytez)
    floor = min(int(pe.OPTIONAL_HEADER.SizeOfHeaders), n)
    located = section_locating(pe) + (field_range(pe.OPTIONAL_HEADER, "SizeOfHeaders"),)
    regions: list[BodyRegion] = []
    claimed: list[Range] = []
    for section in pe.sections:
        lo, hi = section_data_range(section)
        if hi > lo:
            claimed.append((lo, hi))
        if section.Misc_VirtualSize > 0:
            hi = min(hi, lo + section.Misc_VirtualSize)
        past = ((n, hi),) if hi > n else ()
        lo, hi = max(lo, floor), min(hi, n)
        if hi > lo:
            regions.append(BodyRegion((lo, hi), located + past, bool(past)))
    at = floor
    for lo, hi in sorted(claimed) + [(n, n)]:
        if lo > at:
            regions.append(BodyRegion((at, min(lo, n)), located, lo >= n))
        at = max(at, hi)
        if at >= n:
            break
    return regions


def body_regions(bytez: bytes, pe: Optional[pefile.PE]) -> list[Range]:
    """The body regions of a file (`body_layout`), as ranges."""
    return [r.range for r in body_layout(bytez, pe)]


def _regions(raw_obj: Any) -> list[Range]:
    return [(int(lo), int(hi)) for lo, hi in raw_obj]


################################################################################
# Feature types
################################################################################


class BodyByteHistogram(FeatureType):
    """Raw byte counts over the body regions (no normalization)."""

    name = "body_histogram"
    dim = 256

    def raw_features(self, bytez: bytes, pe: Optional[pefile.PE]) -> list[int]:  # type: ignore[override]
        a = np.frombuffer(bytez, dtype=np.uint8)
        counts = np.zeros(256, dtype=np.int64)
        for lo, hi in body_regions(bytez, pe):
            counts += np.bincount(a[lo:hi], minlength=256)
        return counts.tolist()

    def process_raw_features(self, raw_obj: list[int]) -> np.ndarray:
        return np.asarray(raw_obj, dtype=np.float32)

    @property
    def feature_names(self) -> list[str]:
        return [f"byte_{b:02x}" for b in range(256)]

    def items(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> ItemTable:
        """One run of byte items per body region, each byte counted in the bin of its value."""
        key = np.frombuffer(bytez, dtype=np.uint8)
        items = [
            Item("body_bytes", terms=(Term("bins", "body_histogram:counts", ranges=(r.range,), bin_key=key),), locating=r.locating, open_end=r.open_end)
            for r in body_layout(bytez, pe)
        ]
        return ItemTable(len(bytez), {"body_histogram:counts": 256}, items)

    @property
    def readouts(self) -> list[Readout]:
        return [Identity("body_histogram:counts", 0, 256)]


class BodyByteEntropyHistogram(FeatureType):
    """
    Raw byte/entropy counts (thrember's 2048-byte windows, 1024-byte step) over windows tiled per body region.

    NOTE: only full windows are counted. thrember reads a file shorter than a window as one short window, whose
    entropy bin changes as the file grows; counting only full windows from each region's start keeps every existing
    window unchanged when a region is extended, at the cost of ignoring regions shorter than 2048 bytes.
    """

    name = "body_byteentropy"
    dim = 256

    def __init__(self, step: int = 1024, window: int = 2048) -> None:
        self._windows = ByteEntropyHistogram(step=step, window=window)  # type: ignore[no-untyped-call]

    def raw_features(self, bytez: bytes, pe: Optional[pefile.PE]) -> list[int]:  # type: ignore[override]
        a = np.frombuffer(bytez, dtype=np.uint8)
        w, step = self._windows.window, self._windows.step
        output = np.zeros((16, 16), dtype=np.int64)
        for lo, hi in body_regions(bytez, pe):
            for start in range(lo, hi - w + 1, step):
                Hbin, c = self._windows._entropy_bin_counts(a[start:start + w])  # type: ignore[no-untyped-call]
                output[Hbin, :] += c
        return output.flatten().tolist()

    def process_raw_features(self, raw_obj: list[int]) -> np.ndarray:
        return np.asarray(raw_obj, dtype=np.float32)

    @property
    def feature_names(self) -> list[str]:
        return [f"entropy_{h:x}_nibble_{b:x}" for h in range(16) for b in range(16)]

    def items(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> ItemTable:
        """The full windows of each body region: each counts the high nibbles of its bytes in the row of its entropy."""
        a = np.frombuffer(bytez, dtype=np.uint8)
        nibbles = a >> 4
        w, step = self._windows.window, self._windows.step
        items = []
        for r in body_layout(bytez, pe):
            lo, hi = r.range
            for start in range(lo, hi - w + 1, step):
                h = self._windows._entropy_bin_counts(a[start:start + w])[0]  # type: ignore[no-untyped-call]
                term = Term("bins", "body_byteentropy:counts", index=16 * h, ranges=((start, start + w),), bin_key=nibbles)
                items.append(Item("body_window", terms=(term,), attrs={"Hbin": h, "span": (start, start + w)}, locating=r.locating))
        return ItemTable(len(bytez), {"body_byteentropy:counts": 256}, items)

    @property
    def readouts(self) -> list[Readout]:
        return [Identity("body_byteentropy:counts", 0, 256)]


class BodyStrings(FeatureType):
    """
    thrember's string counts over the body regions: the number of strings, of printable characters, the raw count of
    each printable character, and the number of strings matching each regex. Strings break at region boundaries.

    The readouts (average length, entropy, the normalized character distribution) are left out: they are two-sided
    under every threat model, and the original strings group keeps them.
    """

    name = "body_strings"

    def __init__(self) -> None:
        self._strings = StringExtractor()  # type: ignore[no-untyped-call]
        self._regexes = sorted(self._strings.regex_idxs, key=lambda k: self._strings.regex_idxs[k])
        self.dim = 2 + 96 + len(self._regexes)

    def raw_features(self, bytez: bytes, pe: Optional[pefile.PE]) -> dict[str, Any]:  # type: ignore[override]
        # A zero byte is not printable, so joining the regions with one breaks every string at their boundaries.
        joined = b"\x00".join(bytez[lo:hi] for lo, hi in body_regions(bytez, pe))
        raw: dict[str, Any] = self._strings.raw_features(joined, None)  # type: ignore[no-untyped-call]
        return {k: raw[k] for k in ("numstrings", "printables", "printabledist", "string_counts")}

    def process_raw_features(self, raw_obj: dict[str, Any]) -> np.ndarray:
        counts = np.zeros(len(self._regexes), dtype=np.float32)
        for regex, count in raw_obj["string_counts"].items():
            counts[self._strings.regex_idxs[regex]] = count
        return np.hstack([
            raw_obj["numstrings"],
            raw_obj["printables"],
            np.asarray(raw_obj["printabledist"], dtype=np.float32),
            counts,
        ]).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return (
            ["numstrings", "printables"]
            + [f"printable_{c:02x}" for c in range(0x20, 0x20 + 96)]
            + [f"regex_{k}" for k in self._regexes]
        )

    def items(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> ItemTable:
        """
        The strings of each body region, as `StringExtractor` records them, in this group's families. A string is cut
        at its region's ends, as the zero byte joining the regions in `raw_features` cuts it.
        """
        families = {
            "body_strings:numstrings": 1,
            "body_strings:printables": 1,
            "body_strings:printabledist": 96,
            "body_strings:regex": len(self._regexes),
        }
        items = []
        for r in body_layout(bytez, pe):
            for item in self._strings._string_items(bytez, *r.range):
                terms = tuple(replace(t, family="body_" + t.family) for t in item.terms)
                items.append(Item("body_string", terms=terms, locating=r.locating))
        return ItemTable(len(bytez), families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("body_strings:numstrings"),
            Identity("body_strings:printables"),
            Identity("body_strings:printabledist", 0, 96),
            Identity("body_strings:regex", 0, len(self._regexes)),
        ]


@lru_cache(maxsize=65536)
def signed_bucket(n_features: int, key: str) -> tuple[int, int]:
    """The bucket and sign sklearn's FeatureHasher (alternate_sign=True) gives a string key."""
    x = FeatureHasher(n_features, input_type="string").transform([[key]]).tocsr()
    if x.nnz != 1:
        raise RuntimeError(f"Expected {key!r} to hash into exactly one bucket.")
    return int(x.indices[0]), 1 if x.data[0] > 0 else -1


class SectionSplitBuckets(FeatureType):
    """
    thrember's four signed section hashes (size, vsize, entropy keyed by section name; characteristics), each bucket
    split into the sum of the values hashed into it with a positive sign and the sum of those with a negative sign.
    The positive part minus the negative part is the original bucket.
    """

    name = "section_split"
    dim = 4 * 2 * 50

    def __init__(self) -> None:
        self._sections = SectionInfo()  # type: ignore[no-untyped-call]

    def raw_features(self, bytez: bytes, pe: Optional[pefile.PE]) -> dict[str, Any]:  # type: ignore[override]
        if pe is None:
            return {}
        raw: dict[str, Any] = self._sections.raw_features(bytez, pe)  # type: ignore[no-untyped-call]
        return {"sections": [{k: s[k] for k in ("name", "size", "vsize", "entropy", "props")} for s in raw["sections"]]}

    def process_raw_features(self, raw_obj: dict[str, Any]) -> np.ndarray:
        out = np.zeros((4, 2, 50), dtype=np.float64)
        if not raw_obj:
            return out.reshape(-1).astype(np.float32)
        for s in raw_obj["sections"]:
            b, sign = signed_bucket(50, s["name"])
            part = 0 if sign > 0 else 1
            for k, key in enumerate(("size", "vsize", "entropy")):
                out[k, part, b] += s[key]
            for p in s["props"]:
                b, sign = signed_bucket(50, f"{s['name']}:{p}")
                out[3, 0 if sign > 0 else 1, b] += 1
        return out.reshape(-1).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return [f"{kind}_hash_{i}_{part}" for kind in ("size", "vsize", "entropy", "characteristics")
                for part in ("pos", "neg") for i in range(50)]

    def items(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> ItemTable:
        """
        The sections, as `SectionInfo` records them, each hashed value split by its key's hash sign: the size, virtual
        size, and entropy keyed by the section's name, and one count per characteristic keyed by "name:characteristic".
        """
        n = len(bytez)
        families = {f"section_split:{kind}": 2 * 50 for kind in ("size", "vsize", "entropy", "characteristics")}
        if pe is None:
            return ItemTable(n, families, [])
        located = section_locating(pe)
        items = []
        for section, s in zip(pe.sections, self._sections.raw_features(bytez, pe)["sections"], strict=True):  # type: ignore[no-untyped-call]
            name = clipped(n, [field_range(section, "Name")])
            data = clipped(n, [section_data_range(section)])
            reads = {
                "size": clipped(n, [field_range(section, "SizeOfRawData")]),
                "vsize": clipped(n, [field_range(section, "Misc_VirtualSize")]),
                "entropy": data,
            }
            b, sign = signed_bucket(50, s["name"])
            terms = [
                Term("split", f"section_split:{k}", index=b + (50 if sign < 0 else 0), value=s[k], key=s["name"], attr=k, ranges=name + reads[k])
                for k in ("size", "vsize", "entropy")
            ]
            props = clipped(n, [field_range(section, "Characteristics")])
            for p in s["props"]:
                key = f"{s['name']}:{p}"
                b, sign = signed_bucket(50, key)
                terms.append(Term("split", "section_split:characteristics", index=b + (50 if sign < 0 else 0), key=key, ranges=name + props))
            end = section.PointerToRawData + section.SizeOfRawData
            items.append(Item(
                "section",
                terms=tuple(terms),
                attrs={"name": s["name"], "size": s["size"], "vsize": s["vsize"], "entropy": s["entropy"]},
                # As `SectionInfo`'s section items: located through the section table, and through any part of its
                # declared data past the end of the file, which appending fills.
                locating=located + (((n, end),) if end > n else ()),
            ))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [Identity(f"section_split:{kind}", 0, 2 * 50) for kind in ("size", "vsize", "entropy", "characteristics")]


################################################################################
# Extractor
################################################################################

SUMS_GROUPS = ("body_histogram", "body_byteentropy", "body_strings", "section_split")


class SumsFeatureExtractor(PEFeatureExtractor):
    """thrember's extractor with merged import descriptors, followed by the four re-encoded groups (`SUMS_GROUPS`)."""

    def __init__(self) -> None:
        super().__init__()
        merge_import_descriptors(self)
        self.features = self.features + [
            BodyByteHistogram(),
            BodyByteEntropyHistogram(),
            BodyStrings(),
            SectionSplitBuckets(),
        ]
        self.dim = sum(fe.dim for fe in self.features)
        if tuple(fe.name for fe in self.features[-len(SUMS_GROUPS):]) != SUMS_GROUPS:
            raise RuntimeError("The re-encoded groups are out of order.")
