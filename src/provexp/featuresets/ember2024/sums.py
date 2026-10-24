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
(the raw data past its virtual size) and without anything below SizeOfHeaders, and the overlay. Adding a section or an
import section adds a region; appending extends the overlay (or, past a section whose declared raw data overruns the
file, that section's region); insertions move regions without changing their content.
"""

from __future__ import annotations

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
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import section_data_range

__all__ = [
    "SUMS_GROUPS",
    "BodyByteEntropyHistogram",
    "BodyByteHistogram",
    "BodyStrings",
    "SectionSplitBuckets",
    "SumsFeatureExtractor",
    "body_regions",
    "signed_bucket",
]

################################################################################
# Body regions
################################################################################


def body_regions(bytez: bytes, pe: Optional[pefile.PE]) -> list[Range]:
    """
    The body regions of a file, in section order followed by the overlay; empty if the file did not parse.

    Each section contributes the data `get_entropy` reads (`section_data_range`), cut at its virtual size (when
    nonzero) and clipped to [SizeOfHeaders, len(bytez)). Regions are not merged: two sections whose raw data overlap
    are both counted, so that adding a region never changes how an existing one is read.

    NOTE: clipping at SizeOfHeaders keeps the header region out on files whose sections start inside it; the DOS
    extension (M_shift) raises SizeOfHeaders, which can move the clip on such files only (an A2 exception).
    """
    if pe is None:
        return []
    n = len(bytez)
    floor = min(int(pe.OPTIONAL_HEADER.SizeOfHeaders), n)
    regions: list[Range] = []
    end = floor
    for section in pe.sections:
        lo, hi = section_data_range(section)
        end = max(end, min(hi, n))
        if section.Misc_VirtualSize > 0:
            hi = min(hi, lo + section.Misc_VirtualSize)
        lo, hi = max(lo, floor), min(hi, n)
        if hi > lo:
            regions.append((lo, hi))
    # NOTE: on truncated files pefile can place the overlay inside the headers or the sections; the overlay region
    # starts only after every section's raw data.
    overlay = pe.get_overlay_data_start_offset()
    if overlay is not None and max(overlay, end) < n:
        regions.append((max(overlay, end), n))
    return regions


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
