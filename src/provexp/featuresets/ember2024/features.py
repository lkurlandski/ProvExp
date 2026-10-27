"""
Extracts some basic features from PE files. Many of the features
implemented have been used in previously published works. For more information,
check out the following resources:
* Schultz, et al., 2001: http://128.59.14.66/sites/default/files/binaryeval-ieeesp01.pdf
* Kolter and Maloof, 2006: http://www.jmlr.org/papers/volume7/kolter06a/kolter06a.pdf
* Shafiq et al., 2009: https://www.researchgate.net/profile/Fauzan_Mirza/publication/242084613_A_Framework_for_Efficient_Mining_of_Structural_Information_to_Detect_Zero-Day_Malicious_Portable_Executables/links/0c96052e191668c3d5000000.pdf
* Raman, 2012: http://2012.infosecsouthwest.com/files/speaker_materials/ISSW2012_Selecting_Features_to_Classify_Malware.pdf
* Saxe and Berlin, 2015: https://arxiv.org/pdf/1508.03096.pdf

It may be useful to do feature selection to reduce this set of features to a meaningful set
for your modeling problem.
"""

import os
import hashlib
import json
import re
import io
import math
from pathlib import Path
from collections import Counter, OrderedDict

import numpy as np
import pefile
from sklearn.feature_extraction import FeatureHasher
import signify
from signify.authenticode import SignedPEFile
from datetime import datetime

from collections import defaultdict
from collections.abc import Sequence
from typing import Optional

from provexp.boxmatrix import BoxMatrix
from provexp.provenance import EmptyPolicy
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
from provexp.items import Ratio
from provexp.items import Readout
from provexp.items import Selection
from provexp.items import Term
from provexp.items import feature_hash
from provexp.provenance import Provenance


################################################################################
# Explanation Provenance
################################################################################

# NOTE: everything in this section, the `feature_names` properties, and the `provenance` methods were added on top of
# thrember to track the explanation provenance of every feature, i.e., the raw contribution of each byte to each
# feature. The original feature extraction code is unchanged. See provexp.provenance for how raw contributions are
# normalized into a provenance matrix. The conventions are:
#   - A byte contributes to a feature if the feature's value is computed from it, i.e., the byte is counted, read, or
#     hashed. Bytes that only influence a feature indirectly, e.g., through a normalizing denominator or through a
#     pointer that determines where a structure is read from, do not contribute.
#   - A feature that counts items (strings, sections, imports, etc.) receives one unit of contribution per item,
#     spread uniformly over the item's bytes. A feature computed from the content of a region (sizes, entropies,
#     histograms, etc.) receives one unit of contribution per byte.
#   - A hashed feature receives contributions from every item that hashes into its bucket, regardless of the sign the
#     hasher assigns to the item, so items whose values cancel each other out still contribute.
#   - Byte ranges are clipped to the file, which matters for truncated files.
#   - NOTE (Axiom 3): features that are not computed from any particular bytes, e.g., whether the file parsed as a PE,
#     and features that are constant, e.g., the minimum of a list that always contains a zero, receive no
#     contributions. See provexp.provenance.EmptyPolicy.


Range = tuple[int, int]


class Contributions:
    """
    Accumulates raw contributions and builds them into a BoxMatrix in one shot.
    """

    def __init__(self, num_bytes: int, num_features: int) -> None:
        self.shape = (num_bytes, num_features)
        self.matrix = BoxMatrix(self.shape)
        self._lo: list[int] = []
        self._hi: list[int] = []
        self._col: list[int] = []
        self._w: list[float] = []

    def _clip(self, r: Range) -> Range:
        return max(0, min(r[0], self.shape[0])), max(0, min(r[1], self.shape[0]))

    def add_item(self, col: int, ranges: Sequence[Optional[Range]], weight: float = 1.0) -> None:
        """
        Add one item to a feature, spreading `weight` uniformly over the bytes in `ranges` (None ranges are skipped).
        """
        ranges = [self._clip(r) for r in ranges if r is not None]
        ranges = [r for r in ranges if r[1] > r[0]]
        total = sum(hi - lo for lo, hi in ranges)
        if total == 0:
            return
        for lo, hi in ranges:
            self._lo.append(lo)
            self._hi.append(hi)
            self._col.append(col)
            self._w.append(weight / total)

    def add_bytes(self, col: int, r: Optional[Range], weight: float = 1.0) -> None:
        """
        Add `weight` to a feature for every byte in `r`.
        """
        if r is None:
            return
        lo, hi = self._clip(r)
        if hi > lo:
            self._lo.append(lo)
            self._hi.append(hi)
            self._col.append(col)
            self._w.append(weight)

    def add_keyed(self, lo: Sequence[int], hi: Sequence[int], col: Sequence[int], key: np.ndarray) -> None:
        """
        Add one unit to feature `col + key[i]` for every byte i in each range `[lo, hi)`.
        """
        k = self.matrix.add_key(key)
        self.matrix.add_keyed_boxes(np.asarray(lo, dtype=np.int64), np.asarray(hi, dtype=np.int64), np.asarray(col, dtype=np.int64), k)

    def build(self) -> BoxMatrix:
        col = np.array(self._col, dtype=np.int64)
        self.matrix.add_boxes(np.array(self._lo, dtype=np.int64), np.array(self._hi, dtype=np.int64), col, col + 1, np.array(self._w, dtype=np.float64))
        self._lo, self._hi, self._col, self._w = [], [], [], []
        return self.matrix


def field_range(structure: pefile.Structure, field: str) -> Range:
    """
    Return the byte range of a field of a pefile Structure within the file.
    """
    offsets = structure.__field_offsets__
    lo = offsets[field]
    following = [o for o in offsets.values() if o > lo]
    hi = min(following) if following else structure.sizeof()
    base = structure.get_file_offset()
    return base + lo, base + hi


def structure_range(structure: pefile.Structure) -> Range:
    """
    Return the byte range of a pefile Structure within the file.
    """
    return structure.get_file_offset(), structure.get_file_offset() + structure.sizeof()


def section_data_range(section: pefile.SectionStructure) -> Range:
    """
    Return the byte range of the data `pefile.SectionStructure.get_data` returns, i.e., the data `get_entropy` uses.
    """
    lo = section.get_PointerToRawData_adj()
    hi = lo + section.SizeOfRawData
    hi = min(hi, section.PointerToRawData + section.SizeOfRawData)
    return lo, max(lo, hi)


def rva_string_range(pe: pefile.PE, rva: int, length: int) -> Optional[Range]:
    """
    Return the byte range of a string at a relative virtual address, or None if it is not within the file.
    """
    try:
        lo = pe.get_offset_from_rva(rva)
    except pefile.PEFormatError:
        return None
    if lo is None:
        return None
    return lo, lo + length


def hash_indices(n_features: int, items: Sequence[str]) -> np.ndarray:
    """
    Return the bucket each item hashes into under sklearn's FeatureHasher, regardless of its sign or value.
    """
    if len(items) == 0:
        return np.zeros(0, dtype=np.int64)
    X = FeatureHasher(n_features, input_type="string", alternate_sign=False).transform([[s] for s in items]).tocsr()
    if not np.all(np.diff(X.indptr) == 1):
        raise RuntimeError("Expected each item to hash into exactly one bucket.")
    return X.indices.astype(np.int64)


# NOTE: the `items` methods and `readouts` properties were added on top of thrember as well. They record the item layer
# of feature provenance (docs/item-layer-design.md; provexp.items): each feature type's items (sections, strings,
# windows, fields, ...), what each contributes to which sums (layer 2), and each feature's formula over the sums, as
# data (layer 3). `provexp.items.evaluate(items, readouts)` must reproduce `feature_vector` exactly (check G1) and
# `provexp.items.project(items, readouts)` must reproduce `provenance` (check G2). Like `provenance`, the emitters
# mirror the selection logic of `raw_features` and reuse its per-item attributes (e.g., pefile's section entropy).
# Families of sums are named "<feature type>:<family>".


def clipped(num_bytes: int, ranges: Sequence[Optional[Range]]) -> tuple[Range, ...]:
    """The ranges clipped to the file, without None and empty ranges (the clipping of `Contributions`)."""
    out = []
    for r in ranges:
        if r is None:
            continue
        lo, hi = max(0, min(r[0], num_bytes)), max(0, min(r[1], num_bytes))
        if hi > lo:
            out.append((lo, hi))
    return tuple(out)


# NOTE: locating ranges (assumption A1) are the bytes that decide whether an item exists and where its members are,
# as opposed to the bytes its value is read from. Every item pefile parses exists only if the parse succeeds, which
# depends on the fields below, on the section table (pefile stops at the first header that is all zeros or has too
# many implausible fields, so a section's existence depends on the headers before it; relative virtual addresses are
# mapped through it), and on the entries and data of the ten directories pefile parses (any exception other than
# PEFormatError ends the parse, and the extractor then treats the file as not a PE: e.g., a bogus debug directory
# size makes pefile raise an AttributeError; docs/upstream-issues.md). Kinds add their own (an import's descriptor and
# thunks, the overlay's extents). Locating ranges are not clipped to the file: an extent past the end of the file is
# locating, since appending can bring it inside (docs/item-layer-design.md, the overlay case). Check G5
# (`scripts/item_checks.py locating`) flips header bytes and fails on any change of the parse not recorded here.
_PE_LOCATING_FIELDS = [
    ("DOS_HEADER", "e_magic"),
    ("DOS_HEADER", "e_lfanew"),
    ("NT_HEADERS", "Signature"),
    ("FILE_HEADER", "NumberOfSections"),
    ("FILE_HEADER", "SizeOfOptionalHeader"),
    ("OPTIONAL_HEADER", "Magic"),
    ("OPTIONAL_HEADER", "SectionAlignment"),
    ("OPTIONAL_HEADER", "FileAlignment"),
    ("OPTIONAL_HEADER", "NumberOfRvaAndSizes"),
]


# The directories pefile parses on a full load (`PE.parse_data_directories`).
_PARSED_DIRECTORIES = (0, 1, 2, 3, 5, 6, 9, 10, 11, 13)

# The end of a range that reaches every byte past the end of the file.
_PAST_EOF = 2 ** 62


def pe_locating(pe: pefile.PE) -> tuple[Range, ...]:
    """The bytes every item of a parsed PE file is located through: whether the parse succeeds, and where it reads."""
    fields = tuple(field_range(getattr(pe, header), name) for header, name in _PE_LOCATING_FIELDS)
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    data = tuple(r for i in _PARSED_DIRECTORIES if i < len(directories) for r in rva_ranges(pe, directories[i].VirtualAddress, directories[i].Size))
    return fields + section_table_ranges(pe) + directory_ranges(pe, *range(len(directories))) + data


def section_table_ranges(pe: pefile.PE) -> tuple[Range, ...]:
    """
    The declared section table, including headers pefile dropped; if it dropped any, also every byte past the end of
    the file (pefile's plausibility checks compare the headers with the file size, so appending can restore them).
    """
    declared = min(pe.FILE_HEADER.NumberOfSections, pefile.MAX_SECTIONS)
    lo = pe.OPTIONAL_HEADER.get_file_offset() + pe.FILE_HEADER.SizeOfOptionalHeader
    out: tuple[Range, ...] = ((lo, lo + 40 * declared),) if declared > 0 else ()
    if len(pe.sections) < declared:
        out += ((len(pe.__data__), _PAST_EOF),)
    return out


def directory_ranges(pe: pefile.PE, *indices: int) -> tuple[Range, ...]:
    """The entries of the given data directories (those the file has)."""
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    return tuple(structure_range(directories[i]) for i in indices if i < len(directories))


def rva_ranges(pe: pefile.PE, rva: int, size: int) -> tuple[Range, ...]:
    """The bytes at a relative virtual address, if it maps into the file (unclipped)."""
    r = rva_string_range(pe, rva, size)
    return (r,) if r is not None and size > 0 else ()


class FeatureType(object):
    """
    Base class from which each feature type may inherit
    """

    name: str = ""
    dim: int = 0

    def __repr__(self):
        return "{}({})".format(self.name, self.dim)

    def raw_features(self, bytez: bytes, pe: pefile.PE | None = None):
        """Generate a JSON-able representation of the file"""
        raise (NotImplementedError)

    def process_raw_features(self, raw_obj):
        """Generate a feature vector from the raw features"""
        raise (NotImplementedError)

    def feature_vector(self, bytez: bytes, pe: pefile.PE | None = None):
        """Directly calculate the feature vector from the sample itself. This should only be implemented differently
        if there are significant speedups to be gained from combining the two functions."""
        return self.process_raw_features(self.raw_features(bytez, pe))

    @property
    def feature_names(self) -> list[str]:
        """The name of each feature, in the order of the feature vector."""
        raise (NotImplementedError)

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        """The raw contribution of each byte to each feature, as a (len(bytez), dim) BoxMatrix."""
        raise (NotImplementedError)

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        """The items of the file this feature type reads, with their contributions to its sums."""
        raise (NotImplementedError)

    @property
    def readouts(self) -> list[Readout]:
        """The formula of each feature over the sums and items, in the order of the feature vector."""
        raise (NotImplementedError)


class GeneralFileInfo(FeatureType):
    """
    General information about the file
    """

    name = "general"
    dim = 3 + 4

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe=None):
        # From pefile entropy_H()
        size = len(bytez)
        bytez_arr = bytearray(bytez)
        occurences = Counter(bytez_arr)
        entropy = 0
        for x in occurences.values():
            p_x = float(x) / size
            entropy -= p_x * math.log(p_x, 2)

        raw_obj = {
            "size": size,
            "entropy": entropy,
            "is_pe": 0 if pe is None else 1,
            "start_bytes": [
                int(bytez_arr[0]),
                int(bytez_arr[1]) if size >= 2 else 0,
                int(bytez_arr[2]) if size >= 3 else 0,
                int(bytez_arr[3]) if size >= 4 else 0,
            ],
        }
        return raw_obj

    def process_raw_features(self, raw_obj):
        return np.hstack(
            [
                raw_obj["size"],
                raw_obj["entropy"],
                raw_obj["is_pe"], # categorical
                raw_obj["start_bytes"], # categorical
            ],
            dtype=np.float32,
        )

    @property
    def feature_names(self) -> list[str]:
        return ["size", "entropy", "is_pe"] + [f"start_byte_{i}" for i in range(4)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        # The size and entropy are computed from every byte.
        C.add_bytes(0, (0, len(bytez)))
        C.add_bytes(1, (0, len(bytez)))
        # NOTE (Axiom 3): whether the file parsed as a PE is not computed from any particular bytes.
        # Each of the first four bytes (if present).
        for i in range(min(4, len(bytez))):
            C.add_bytes(3 + i, (i, i + 1))
        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        whole = clipped(n, [(0, n)])
        items = [
            # The file's bytes: its size and the byte counts its entropy is computed from.
            Item("bytes", terms=(
                Term("add", "general:size", value=n, ranges=whole, per_byte=True),
                Term("bins", "general:bytes", ranges=whole, bin_key=np.frombuffer(bytez, dtype=np.uint8)),
            )),
        ]
        # The first four bytes, each a field.
        for i in range(min(4, n)):
            items.append(Item("field", terms=(Term("slot", "general:start", index=i, value=bytez[i], ranges=((i, i + 1),)),)))
        # Whether the file parsed as a PE (NOTE (Axiom 3): from no particular bytes).
        if pe is not None:
            items.append(Item("pe", attrs={"is_pe": 1}, locating=pe_locating(pe)))
        return ItemTable(n, {"general:size": 1, "general:bytes": 256, "general:start": 4}, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("general:size"),
            Entropy("general:bytes", precision="python"),
            Opaque("pe", ("is_pe",), (0.0,)),
            Identity("general:start", 0, 4),
        ]


class ByteHistogram(FeatureType):
    """
    Byte histogram (count + non-normalized) over the entire binary file
    """

    name = "histogram"
    dim = 256

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        counts = np.bincount(np.frombuffer(bytez, dtype=np.uint8), minlength=256)
        return counts.tolist()
    
    def process_raw_features(self, raw_obj):
        counts = np.array(raw_obj, dtype=np.float32)
        sum = counts.sum()
        normalized = counts / sum
        return normalized

    @property
    def feature_names(self) -> list[str]:
        return [f"byte_{b:02x}" for b in range(256)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        # Each byte is counted in the bin of its value.
        C.add_keyed([0], [len(bytez)], [0], np.frombuffer(bytez, dtype=np.uint8))
        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        # The bytes, each counted in the bin of its value (one run of byte items).
        item = Item("bytes", terms=(Term("bins", "histogram:counts", ranges=clipped(n, [(0, n)]), bin_key=np.frombuffer(bytez, dtype=np.uint8)),))
        return ItemTable(n, {"histogram:counts": 256}, [item])

    @property
    def readouts(self) -> list[Readout]:
        return [Normalized("histogram:counts", 256, precision="float32")]


class ByteEntropyHistogram(FeatureType):
    """
    2d byte/entropy histogram based loosely on (Saxe and Berlin, 2015).
    This roughly approximates the joint probability of byte value and local entropy.
    See Section 2.1.1 in https://arxiv.org/pdf/1508.03096.pdf for more info.
    """

    name = "byteentropy"
    dim = 256

    def __init__(self, step=1024, window=2048):
        super(FeatureType, self).__init__()
        self.window = window
        self.step = step

    def _entropy_bin_counts(self, block):
        # coarse histogram, 16 bytes per bin
        c = np.bincount(block >> 4, minlength=16)  # 16-bin histogram
        p = c.astype(np.float32) / self.window
        wh = np.where(c)[0]
        # * x2 b.c. we reduced information by half: 256 bins (8 bits) to 16 bins (4 bits)
        H = np.sum(-p[wh] * np.log2(p[wh])) * 2

        Hbin = int(H * 2)  # up to 16 bins (max entropy is 8 bits)
        if Hbin == 16:  # handle entropy = 8.0 bits
            Hbin = 15

        return Hbin, c

    def raw_features(self, bytez, pe):
        output = np.zeros((16, 16), dtype=np.int32)
        a = np.frombuffer(bytez, dtype=np.uint8)
        if a.shape[0] < self.window:
            Hbin, c = self._entropy_bin_counts(a)
            output[Hbin, :] += c
        else:
            # strided trick from here: http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
            shape = a.shape[:-1] + (a.shape[-1] - self.window + 1, self.window)
            strides = a.strides + (a.strides[-1],)
            blocks = np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)[:: self.step, :]

            # from the blocks, compute histogram
            for block in blocks:
                Hbin, c = self._entropy_bin_counts(block)
                output[Hbin, :] += c

        return output.flatten().tolist()

    def process_raw_features(self, raw_obj):
        counts = np.array(raw_obj, dtype=np.float32)
        sum = counts.sum()
        normalized = counts / sum
        return normalized

    @property
    def feature_names(self) -> list[str]:
        return [f"entropy_{h:x}_nibble_{b:x}" for h in range(16) for b in range(16)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        a = np.frombuffer(bytez, dtype=np.uint8)
        # Mirror the windowing in `raw_features`: each byte of each window is counted in the bin of its high nibble,
        # within the row of the window's entropy.
        if a.shape[0] < self.window:
            starts = np.array([0])
            stops = np.array([a.shape[0]])
            Hbins = np.array([self._entropy_bin_counts(a)[0]])
        else:
            starts = np.arange(0, a.shape[0] - self.window + 1, self.step)
            stops = starts + self.window
            Hbins = np.array([self._entropy_bin_counts(a[s:s + self.window])[0] for s in starts])
        C.add_keyed(starts, stops, 16 * Hbins, a >> 4)
        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        a = np.frombuffer(bytez, dtype=np.uint8)
        nibbles = a >> 4
        # Mirror the windowing in `raw_features`: each window counts the high nibbles of its bytes in the row of its
        # entropy bin. A file shorter than a window is one window.
        if n < self.window:
            starts = [0]
            Hbins = [self._entropy_bin_counts(a)[0]]
            stops = [n]
        else:
            starts = list(range(0, n - self.window + 1, self.step))
            Hbins = [self._entropy_bin_counts(a[s:s + self.window])[0] for s in starts]
            stops = [s + self.window for s in starts]
        items = [
            Item("window", attrs={"Hbin": h}, terms=(Term("bins", "byteentropy:counts", index=16 * h, ranges=clipped(n, [(s, e)]), bin_key=nibbles),))
            for s, e, h in zip(starts, stops, Hbins, strict=True)
        ]
        return ItemTable(n, {"byteentropy:counts": 256}, items)

    @property
    def readouts(self) -> list[Readout]:
        return [Normalized("byteentropy:counts", 256, precision="float32")]


class StringExtractor(FeatureType):
    """
    Extracts strings from raw byte stream
    """

    name = "strings"
    dim = 5 + 96 + 76

    def __init__(self):
        super(FeatureType, self).__init__()
        # all consecutive runs of 0x20 - 0x7f that are 5+ characters
        self._allstrings = re.compile(b"[\x20-\x7f]{5,}")

        # Scan _allstrings with these regexes
        self._regexes = {
            # IOC strings, from:
            # https://www.stackzero.net/python-string-analysis/
            # https://engineering.avast.io/yara-in-search-of-regular-expressions/
            "url": re.compile("\\b(?:http|https|ftp):\\/\\/[a-zA-Z0-9-._~:?#[\\]@!$&'()*+,;=]+"),
            "ipv4_addr": re.compile("\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b"),
            "ipv6_addr": re.compile("\\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\\b|\\b(?:[A-Fa-f0-9]{1,4}:){1,7}:\\b|\\b:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){1,6}\\b"),
            "mac_addr": re.compile("\\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\\b"),
            "email_addr": re.compile("\\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\\b"),
            "btc_wallet": re.compile("[13][a-km-zA-HJ-NP-Z1-9]{25,34}"),

            # Windows strings
            "file_path": re.compile("\\bC:/"),
            "dos_msg": re.compile("!This program "),
            "registry_key": re.compile("\\b(?:KHEY_|KHLM|HKCU)"),

            # Linux strings
            "/dev/": re.compile("/dev/"),
            "/proc/": re.compile("/proc/"),
            "/bin/": re.compile("/bin/"),
            "/usr/": re.compile("/usr/"),
            "/tmp/": re.compile("/tmp/"),

            # PDF strings
            "/URI": re.compile("/URI"),
            "/FlateDecode": re.compile("/FlateDecode"),
            "/EmbeddedFile": re.compile("/EmbeddedFile"),

            # HTML and JS strings
            "html": re.compile("html", re.IGNORECASE),
            "javascript": re.compile("javascript", re.IGNORECASE),
            "<script": re.compile("<script", re.IGNORECASE),
            ".click(": re.compile(".click", re.IGNORECASE),
            "onlick": re.compile("onclick", re.IGNORECASE),

            # Powershell strings
            "powershell": re.compile("powershell", re.IGNORECASE),
            "Invoke-Expression": re.compile("Invoke-Expression"),
            "Invoke-Command": re.compile("Invoke-Command"),
            "Start-process": re.compile("Start-process"),

            # Network strings
            "get": re.compile("GET /", re.IGNORECASE),
            "post": re.compile("POST /", re.IGNORECASE),
            "http": re.compile("HTTP/", re.IGNORECASE),
            "http://": re.compile("http://", re.IGNORECASE),
            "https://": re.compile("https://", re.IGNORECASE),
            "ftp": re.compile("ftp:", re.IGNORECASE),
            "useragent": re.compile("User-Agent", re.IGNORECASE),
            "cookie": re.compile("cookie", re.IGNORECASE),
            "internet": re.compile("internet", re.IGNORECASE),
            "download": re.compile("download", re.IGNORECASE),
            "connect": re.compile("connect", re.IGNORECASE),

            # Cryptography and encoding strings
            "base64": re.compile("base64", re.IGNORECASE),
            "base64string": re.compile("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
            "crypt": re.compile("crypt"),
            "encode": re.compile("encode", re.IGNORECASE),
            "decode": re.compile("decode", re.IGNORECASE),

            # Miscellaneous strings
            "cache": re.compile("cache", re.IGNORECASE),
            "certificate": re.compile("certificate", re.IGNORECASE),
            "clipboard": re.compile("clipboard", re.IGNORECASE),
            "command": re.compile("command", re.IGNORECASE),
            "create": re.compile("create", re.IGNORECASE),
            "debug": re.compile("debug", re.IGNORECASE),
            "delete": re.compile("delete", re.IGNORECASE),
            "desktop": re.compile("desktop", re.IGNORECASE),
            "directory": re.compile("directory", re.IGNORECASE),
            "disk": re.compile("disk", re.IGNORECASE),
            "environment": re.compile("environment", re.IGNORECASE),
            "enum": re.compile("enum", re.IGNORECASE),
            "exit": re.compile("exit", re.IGNORECASE),
            "file": re.compile("file", re.IGNORECASE),
            "hostname": re.compile("hostname", re.IGNORECASE),
            "install": re.compile("install", re.IGNORECASE),
            "hidden": re.compile("hidden", re.IGNORECASE),
            "keyboard": re.compile("keyboard", re.IGNORECASE),
            "memory": re.compile("memory", re.IGNORECASE),
            "module": re.compile("module", re.IGNORECASE),
            "mutex": re.compile("mutex", re.IGNORECASE),
            "password": re.compile("password", re.IGNORECASE),
            "privilege": re.compile("privilege", re.IGNORECASE),
            "process": re.compile("process", re.IGNORECASE),
            "remote": re.compile("remote", re.IGNORECASE),
            "resource": re.compile("resource", re.IGNORECASE),
            "security": re.compile("security", re.IGNORECASE),
            "service": re.compile("service", re.IGNORECASE),
            "shell": re.compile("shell", re.IGNORECASE),
            "snapshot": re.compile("snapshot", re.IGNORECASE),
            "system": re.compile("system", re.IGNORECASE),
            "thread": re.compile("thread", re.IGNORECASE),
            "token": re.compile("token", re.IGNORECASE),
            "wallet": re.compile("wallet", re.IGNORECASE),
            "window": re.compile("window", re.IGNORECASE),
        }
        self.regex_idxs = {k: v for v, k in enumerate(sorted(self._regexes))}

    def raw_features(self, bytez, pe):
        allstrings = self._allstrings.findall(bytez)
        allstrings_ascii = [s.decode() for s in allstrings]
        if allstrings:
            # statistics about strings:
            string_lengths = [len(s) for s in allstrings]
            avlength = sum(string_lengths) / len(string_lengths)
            # map printable characters 0x20 - 0x7f to an int array consisting of 0-95, inclusive
            as_shifted_string = [b - ord(b"\x20") for b in b"".join(allstrings)]
            c = np.bincount(as_shifted_string, minlength=96)  # histogram count
            # distribution of characters in printable strings
            csum = c.sum()
            p = c.astype(np.float32) / csum
            wh = np.where(c)[0]
            H = np.sum(-p[wh] * np.log2(p[wh]))  # entropy

        else:
            avlength = 0
            c = np.zeros((96,), dtype=np.float32)
            H = 0
            csum = 0

        # Search strings with all regexes
        string_counts = {}
        for s in allstrings_ascii:
            for k, r in self._regexes.items():
                if re.search(r, s):
                    if string_counts.get(k) is None:
                        string_counts[k] = 0
                    string_counts[k] += 1
        string_counts = OrderedDict(sorted(string_counts.items()))

        return {
            "numstrings": len(allstrings),
            "avlength": avlength,
            "printabledist": c.tolist(),  # store non-normalized histogram
            "printables": int(csum),
            "entropy": float(H),
            "string_counts": string_counts,
        }

    def process_raw_features(self, raw_obj):
        hist_divisor = float(raw_obj["printables"]) if raw_obj["printables"] > 0 else 1.0
        string_counts = np.zeros(len(self.regex_idxs), dtype=np.float32)
        for regex, count in raw_obj["string_counts"].items():
            idx = self.regex_idxs[regex]
            string_counts[idx] = count

        return np.hstack(
            [
                raw_obj["numstrings"],
                raw_obj["avlength"],
                raw_obj["printables"],
                np.asarray(raw_obj["printabledist"]) / hist_divisor,
                raw_obj["entropy"],
                string_counts,
            ]
        ).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        regexes = sorted(self.regex_idxs, key=lambda k: self.regex_idxs[k])
        return (
            ["numstrings", "avlength", "printables"]
            + [f"printable_{c:02x}" for c in range(0x20, 0x20 + 96)]
            + ["entropy"]
            + [f"regex_{k}" for k in regexes]
        )

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        spans = [(mt.start(), mt.end()) for mt in self._allstrings.finditer(bytez)]
        if not spans:
            return C.build()

        for span in spans:
            C.add_item(0, [span])   # numstrings: each string counts once.
            C.add_bytes(1, span)    # avlength: every character of every string.
            C.add_bytes(2, span)    # printables: every character of every string.
            C.add_bytes(99, span)   # entropy: every character of every string.

        # printabledist: each character is counted in the bin of its value. The key wraps around for the bytes
        # outside of the strings, but those are never addressed.
        key = np.frombuffer(bytez, dtype=np.uint8) - np.uint8(0x20)
        C.add_keyed([lo for lo, _ in spans], [hi for _, hi in spans], [3] * len(spans), key)

        # string_counts: each string counts once toward each regex it matches. Mirrors `raw_features`.
        for span in spans:
            s = bytez[span[0]:span[1]].decode()
            for k, r in self._regexes.items():
                if re.search(r, s):
                    C.add_item(100 + self.regex_idxs[k], [span])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {"strings:numstrings": 1, "strings:printables": 1, "strings:printabledist": 96, "strings:regex": len(self._regexes)}
        spans = [(mt.start(), mt.end()) for mt in self._allstrings.finditer(bytez)]
        # The regexes each string matches, in one pass per regex over the strings joined by newlines (see the NOTE on
        # `_strings_raw_features`: exact).
        matched: list[list[int]] = [[] for _ in spans]
        if spans:
            text = "\n".join(bytez[lo:hi].decode() for lo, hi in spans)
            starts = np.cumsum([0] + [hi - lo + 1 for lo, hi in spans[:-1]])
            for k, r in self._regexes.items():
                positions = [m.start() for m in r.finditer(text)]
                for i in np.unique(np.searchsorted(starts, positions, side="right") - 1).tolist():
                    matched[i].append(self.regex_idxs[k])
        # The bin of each printable character; bytes outside the strings are never read.
        key = np.frombuffer(bytez, dtype=np.uint8).astype(np.int16) - 0x20
        items = []
        for (lo, hi), regexes in zip(spans, matched, strict=True):
            r = ((lo, hi),)
            terms = [
                Term("count", "strings:numstrings", ranges=r),
                Term("add", "strings:printables", value=hi - lo, ranges=r, per_byte=True),
                Term("bins", "strings:printabledist", ranges=r, bin_key=key),
            ]
            terms += [Term("count", "strings:regex", index=j, ranges=r) for j in sorted(regexes)]
            items.append(Item("string", terms=tuple(terms)))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("strings:numstrings"),
            Ratio(("strings:printables", 0), ("strings:numstrings", 0)),  # avlength
            Identity("strings:printables"),
            Normalized("strings:printabledist", 96, precision="float64"),
            Entropy("strings:printabledist", precision="numpy"),
            Identity("strings:regex", 0, len(self._regexes)),
        ]


class SectionInfo(FeatureType):
    """
    Information about section names, sizes and entropy.  Uses hashing trick
    to summarize all this section info into a feature vector.
    """

    name = "section"
    dim = 11 + 50 + 50 + 50 + 50 + 10 + 3

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        if pe is None:
            return {}

        # Properties of entry point. Or if invalid, the first executable section.
        entry_section = ""
        aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        for section in pe.sections:
            if section.contains_rva(aoep):
                entry_section = section.Name.strip(b"\x00").decode(errors="ignore").lower()

        isection = 0
        while entry_section == "" and isection < len(pe.sections):
            if pe.sections[isection].Characteristics & 0x20000000 > 0:
                entry_section = pe.sections[isection].Name.strip(b"\x00").decode(errors="ignore").lower()
            isection += 1

        raw_obj = {"entry": entry_section}
        raw_obj["sections"] = [
            {
                "name": section.Name.strip(b"\x00").decode(errors="ignore").lower(),
                "size": section.SizeOfRawData,
                "entropy": section.get_entropy(),
                "vsize": section.Misc_VirtualSize,
                "size_ratio": section.SizeOfRawData / len(bytez),
                "vsize_ratio": section.SizeOfRawData / max(section.Misc_VirtualSize, 1),
                "props": [sc[10:] for sc, _ in pefile.section_characteristics if section.__dict__[sc]],
            }
            for section in pe.sections
        ]
        raw_obj["overlay"] = {
            "size": 0,
            "size_ratio": 0,
            "entropy": 0,
        }

        overlay = pe.get_overlay()
        if overlay is not None:

            # From pefile entropy_H()
            overlay_size = len(overlay)
            occurences = Counter(bytearray(overlay))
            entropy = 0
            for x in occurences.values():
                p_x = float(x) / len(overlay)
                entropy -= p_x * math.log(p_x, 2)

            raw_obj["overlay"] = {
                "size": overlay_size,
                "size_ratio": overlay_size / len(bytez),
                "entropy": entropy
            }

        return raw_obj

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        sections = raw_obj["sections"]

        # General properties of sections
        n_sections = len(sections)
        n_zero_size = sum(1 for s in sections if s["size"] == 0)
        n_emtpy_name = sum(1 for s in sections if s["name"] == "")
        n_rx = sum(1 for s in sections if "MEM_READ" in s["props"] and "MEM_EXECUTE" in s["props"])
        n_w = sum(1 for s in sections if "MEM_WRITE" in s["props"])
        entropies = [s["entropy"] for s in sections] + [raw_obj["overlay"]["entropy"]] + [0]
        size_ratios = [s["size_ratio"] for s in sections] + [raw_obj["overlay"]["size_ratio"]] + [0]
        vsize_ratios = [s["vsize_ratio"] for s in sections] + [0]

        general = [
            n_sections,
            n_zero_size,
            n_emtpy_name,
            n_rx,
            n_w,
            max(entropies),
            min(entropies),
            max(size_ratios),
            min(size_ratios),
            max(vsize_ratios),
            min(vsize_ratios)
        ]

        # Properties of all the individual sections
        section_sizes = [(s["name"], s["size"]) for s in sections]
        section_sizes_hashed = FeatureHasher(50, input_type="pair").transform([section_sizes]).toarray()[0]
        section_vsize = [(s["name"], s["vsize"]) for s in sections]
        section_vsize_hashed = FeatureHasher(50, input_type="pair").transform([section_vsize]).toarray()[0]
        section_entropy = [(s["name"], s["entropy"]) for s in sections]
        section_entropy_hashed = FeatureHasher(50, input_type="pair").transform([section_entropy]).toarray()[0]
        characteristics = [f"{s['name']}:{p}" for s in sections for p in s["props"]]
        characteristics_hashed = FeatureHasher(50, input_type="string").transform([characteristics]).toarray()[0]
        entry_name_hashed = FeatureHasher(10, input_type="string").transform([[raw_obj["entry"]]]).toarray()[0]

        return np.hstack(
            [
                general,
                section_sizes_hashed,
                section_vsize_hashed,
                section_entropy_hashed,
                characteristics_hashed,
                entry_name_hashed,
                raw_obj["overlay"]["size"],
                raw_obj["overlay"]["size_ratio"],
                raw_obj["overlay"]["entropy"]
            ]
        ).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return (
            [
                "num_sections",
                "num_zero_size",
                "num_empty_name",
                "num_rx",
                "num_w",
                "max_entropy",
                "min_entropy",
                "max_size_ratio",
                "min_size_ratio",
                "max_vsize_ratio",
                "min_vsize_ratio",
            ]
            + [f"size_hash_{i}" for i in range(50)]
            + [f"vsize_hash_{i}" for i in range(50)]
            + [f"entropy_hash_{i}" for i in range(50)]
            + [f"characteristics_hash_{i}" for i in range(50)]
            + [f"entry_name_hash_{i}" for i in range(10)]
            + ["overlay_size", "overlay_size_ratio", "overlay_entropy"]
        )

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None:
            return C.build()

        # The raw features of each section, in the same order as `pe.sections`.
        raw_obj = self.raw_features(bytez, pe)
        sections = raw_obj["sections"]
        table = [structure_range(s) for s in pe.sections]
        names = [field_range(s, "Name") for s in pe.sections]
        sizes = [field_range(s, "SizeOfRawData") for s in pe.sections]
        vsizes = [field_range(s, "Misc_VirtualSize") for s in pe.sections]
        props = [field_range(s, "Characteristics") for s in pe.sections]
        datas = [section_data_range(s) for s in pe.sections]

        overlay_offset = pe.get_overlay_data_start_offset()
        overlay = (overlay_offset, len(bytez)) if overlay_offset is not None else None

        # General properties of sections.
        for i, s in enumerate(sections):
            C.add_item(0, [table[i]])
            if s["size"] == 0:
                C.add_item(1, [sizes[i]])
            if s["name"] == "":
                C.add_item(2, [names[i]])
            if "MEM_READ" in s["props"] and "MEM_EXECUTE" in s["props"]:
                C.add_item(3, [props[i]])
            if "MEM_WRITE" in s["props"]:
                C.add_item(4, [props[i]])

        # The maxima are attributed to the sections (and overlay) that attain them. The entropy of a section is
        # computed from its data, unless it has none, in which case its entropy is determined by its size.
        # NOTE (Axiom 3): the minima are always zero because `process_raw_features` appends a zero to each list of
        # nonnegative values, so they receive no contributions.
        entropy_candidates = [(s["entropy"], datas[i] if datas[i][1] > datas[i][0] else sizes[i]) for i, s in enumerate(sections)]
        size_ratio_candidates = [(s["size_ratio"], sizes[i]) for i, s in enumerate(sections)]
        if overlay is not None:
            entropy_candidates.append((raw_obj["overlay"]["entropy"], overlay))
            size_ratio_candidates.append((raw_obj["overlay"]["size_ratio"], overlay))
        for col, candidates in [(5, entropy_candidates), (7, size_ratio_candidates)]:
            if candidates:
                best = max(v for v, _ in candidates)
                for v, r in candidates:
                    if v == best:
                        C.add_item(col, [r])
        vsize_ratios = [s["vsize_ratio"] for s in sections]
        if vsize_ratios:
            best = max(vsize_ratios)
            for i, v in enumerate(vsize_ratios):
                if v == best:
                    C.add_item(9, [sizes[i], vsizes[i]])

        # Hashed properties of the individual sections.
        buckets = hash_indices(50, [s["name"] for s in sections])
        for i, b in enumerate(buckets):
            C.add_item(11 + b, [names[i], sizes[i]])
            C.add_item(61 + b, [names[i], vsizes[i]])
            C.add_item(111 + b, [names[i], datas[i]])
        characteristics = [(i, f"{s['name']}:{p}") for i, s in enumerate(sections) for p in s["props"]]
        buckets = hash_indices(50, [c for _, c in characteristics])
        for (i, _), b in zip(characteristics, buckets, strict=True):
            C.add_item(161 + b, [names[i], props[i]])

        # The entry section, mirroring the selection logic in `raw_features`. The entry point always contributes,
        # as do the name of the selected section and, if it was selected as a fallback, its characteristics.
        entry_ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint")]
        entry_section = ""
        aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        for i, section in enumerate(pe.sections):
            if section.contains_rva(aoep):
                entry_section = sections[i]["name"]
                entry_ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint"), names[i]]
        isection = 0
        while entry_section == "" and isection < len(pe.sections):
            if pe.sections[isection].Characteristics & 0x20000000 > 0:
                entry_section = sections[isection]["name"]
                entry_ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint"), names[isection], props[isection]]
            isection += 1
        if entry_section != raw_obj["entry"]:
            raise RuntimeError(f"Failed to mirror the entry section selection: {entry_section!r} != {raw_obj['entry']!r}")
        C.add_item(211 + hash_indices(10, [entry_section])[0], entry_ranges)

        # The overlay.
        for col in (221, 222, 223):
            C.add_bytes(col, overlay)

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {
            "section:file_size": 1,
            "section:counts": 5,
            "section:size_hash": 50,
            "section:vsize_hash": 50,
            "section:entropy_hash": 50,
            "section:characteristics_hash": 50,
            "section:entry_name_hash": 10,
            "section:overlay": 2,
        }
        if pe is None:
            return ItemTable(n, families, [])

        raw_obj = self.raw_features(bytez, pe)
        sections = raw_obj["sections"]
        located = pe_locating(pe)
        items = [Item("file", terms=(Term("add", "section:file_size", value=n, ranges=clipped(n, [(0, n)]), per_byte=True),), locating=located)]

        # The sections, in the order of `pe.sections`.
        name_buckets, name_signs = feature_hash(50, [s["name"] for s in sections])
        characteristics = [f"{s['name']}:{p}" for s in sections for p in s["props"]]
        char_buckets, char_signs = feature_hash(50, characteristics)
        j = 0
        for i, (section, s) in enumerate(zip(pe.sections, sections, strict=True)):
            table = clipped(n, [structure_range(section)])
            name = clipped(n, [field_range(section, "Name")])
            size = clipped(n, [field_range(section, "SizeOfRawData")])
            vsize = clipped(n, [field_range(section, "Misc_VirtualSize")])
            props = clipped(n, [field_range(section, "Characteristics")])
            data = clipped(n, [section_data_range(section)])
            b, sign = int(name_buckets[i]), int(name_signs[i])
            terms = [Term("count", "section:counts", index=0, ranges=table)]
            if s["size"] == 0:
                terms.append(Term("count", "section:counts", index=1, ranges=size))
            if s["name"] == "":
                terms.append(Term("count", "section:counts", index=2, ranges=name))
            if "MEM_READ" in s["props"] and "MEM_EXECUTE" in s["props"]:
                terms.append(Term("count", "section:counts", index=3, ranges=props))
            if "MEM_WRITE" in s["props"]:
                terms.append(Term("count", "section:counts", index=4, ranges=props))
            terms += [
                Term("hashed", "section:size_hash", index=b, value=s["size"], sign=sign, key=s["name"], attr="size", ranges=name + size),
                Term("hashed", "section:vsize_hash", index=b, value=s["vsize"], sign=sign, key=s["name"], attr="vsize", ranges=name + vsize),
                Term("hashed", "section:entropy_hash", index=b, value=s["entropy"], sign=sign, key=s["name"], attr="entropy", ranges=name + data),
            ]
            for _ in s["props"]:
                terms.append(Term("hashed", "section:characteristics_hash", index=int(char_buckets[j]), sign=int(char_signs[j]), key=characteristics[j], ranges=name + props))
                j += 1
            items.append(Item(
                "section",
                terms=tuple(terms),
                attrs={"name": s["name"], "size": s["size"], "vsize": s["vsize"], "entropy": s["entropy"], "vsize_ratio": s["vsize_ratio"]},
                # The entropy of a section without data is determined by its size.
                attr_ranges={"entropy": (data if data else size,), "size": (size,), "vsize_ratio": (size + vsize,)},
                # Its header and its data's pointer and size are in the section table.
                locating=located,
            ))

        # The overlay. pefile starts it after the furthest extent of the optional header, the sections, and the data
        # directories (but security) that lies within the file, so all of them locate it, and so do the bytes past
        # the end of the file that an extent reaches (appending can bring the extent inside).
        overlay_offset = pe.get_overlay_data_start_offset()
        overlay_locating = located
        extents = [(s.PointerToRawData, s.PointerToRawData + s.SizeOfRawData) for s in pe.sections]
        for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
            if i != 4:
                try:
                    extents.append((pe.get_offset_from_rva(d.VirtualAddress), pe.get_offset_from_rva(d.VirtualAddress) + d.Size))
                except pefile.PEFormatError:
                    pass
        overlay_locating += tuple((n, hi) for _, hi in extents if hi > n)
        if overlay_offset is not None:
            r = clipped(n, [(overlay_offset, n)])
            o = raw_obj["overlay"]
            items.append(Item(
                "overlay",
                terms=(
                    Term("slot", "section:overlay", index=0, value=o["size"], attr="size", ranges=r, per_byte=True),
                    Term("slot", "section:overlay", index=1, value=o["entropy"], attr="entropy", ranges=r, per_byte=True),
                ),
                attrs={"size": o["size"], "entropy": o["entropy"]},
                attr_ranges={"size": (r,), "entropy": (r,)},
                locating=overlay_locating,
            ))

        # The entry section, mirroring the selection logic in `raw_features` (and `provenance`). The entry point
        # always contributes, as do the name of the selected section and, if it was selected as a fallback, its
        # characteristics.
        entry_ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint")]
        entry_section = ""
        aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        for i, section in enumerate(pe.sections):
            if section.contains_rva(aoep):
                entry_section = sections[i]["name"]
                entry_ranges = [field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint"), field_range(section, "Name")]
        isection = 0
        while entry_section == "" and isection < len(pe.sections):
            if pe.sections[isection].Characteristics & 0x20000000 > 0:
                entry_section = sections[isection]["name"]
                entry_ranges = [
                    field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint"),
                    field_range(pe.sections[isection], "Name"),
                    field_range(pe.sections[isection], "Characteristics"),
                ]
            isection += 1
        if entry_section != raw_obj["entry"]:
            raise RuntimeError(f"Failed to mirror the entry section selection: {entry_section!r} != {raw_obj['entry']!r}")
        buckets, signs = feature_hash(10, [entry_section])
        items.append(Item(
            "entry",
            terms=(Term("hashed", "section:entry_name_hash", index=int(buckets[0]), sign=int(signs[0]), key=entry_section, ranges=clipped(n, entry_ranges)),),
            attrs={"name": entry_section},
            # Selected by the entry point among every section's range and characteristics.
            locating=located + (field_range(pe.OPTIONAL_HEADER, "AddressOfEntryPoint"),),
        ))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("section:counts", 0, 5),
            Max(("section", "overlay"), "entropy"),
            Min(("section", "overlay"), "entropy"),
            Max(("section", "overlay"), "size", divide_by=("section:file_size", 0)),
            Min(("section", "overlay"), "size", divide_by=("section:file_size", 0)),
            Max(("section",), "vsize_ratio"),
            Min(("section",), "vsize_ratio"),
            Identity("section:size_hash", 0, 50),
            Identity("section:vsize_hash", 0, 50),
            Identity("section:entropy_hash", 0, 50),
            Identity("section:characteristics_hash", 0, 50),
            Selection("section:entry_name_hash", 0, 10),
            Identity("section:overlay", 0, 1),
            Ratio(("section:overlay", 0), ("section:file_size", 0)),
            Identity("section:overlay", 1, 1),
        ]


class ImportsInfo(FeatureType):
    """
    Information about imported libraries and functions from the
    import address table.  Note that the total number of imported
    functions is contained in GeneralFileInfo.
    """

    name = "imports"
    dim = 2 + 256 + 1024

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        imports = {}
        if pe is None or "DIRECTORY_ENTRY_IMPORT" not in pe.__dict__.keys():
            return imports

        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            imports[dll_name] = []

            # Clipping assumes there are diminishing returns on the discriminatory power of imported functions
            # beyond the first 10000 characters, and this will help limit the dataset size
            for lib in entry.imports:
                if lib.name is not None and len(lib.name):
                    imports[dll_name].append(lib.name.decode()[:10000])
                elif lib.ordinal is not None:
                    imports[dll_name].append(f"{dll_name}:ordinal{lib.ordinal}")

        return imports

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        # Unique libraries
        libraries = list(set([l.lower() for l in raw_obj.keys()]))
        libraries_hashed = FeatureHasher(256, input_type="string", alternate_sign=False).transform([libraries]).toarray()[0]

        # A string like "kernel32.dll:CreateFileMappingA" for each imported function
        imports = [lib.lower() + ":" + e for lib, elist in raw_obj.items() for e in elist]
        imports_hashed = FeatureHasher(1024, input_type="string", alternate_sign=False).transform([imports]).toarray()[0]

        # Number of libraries/imports
        lengths = [len(imports), len(libraries)]

        # Two separate elements: libraries (alone) and fully-qualified names of imported functions
        return np.hstack([lengths, libraries_hashed, imports_hashed]).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return ["num_imports", "num_libraries"] + [f"library_hash_{i}" for i in range(256)] + [f"import_hash_{i}" for i in range(1024)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None or "DIRECTORY_ENTRY_IMPORT" not in pe.__dict__.keys():
            return C.build()

        # Mirror `raw_features`. A later import descriptor for the same DLL replaces the functions of an earlier
        # one, but the names of all of the descriptors for a DLL contribute to the DLL's features.
        thunk_size = 8 if pe.PE_TYPE == pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS else 4
        dll_ranges: dict[str, list[Optional[Range]]] = defaultdict(list)
        imports: dict[str, list[tuple[str, Optional[Range]]]] = {}
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            dll_ranges[dll_name].append(rva_string_range(pe, entry.struct.Name, len(entry.dll)))
            imports[dll_name] = []
            for lib in entry.imports:
                if lib.name is not None and len(lib.name):
                    r = (lib.name_offset, lib.name_offset + min(len(lib.name), 10000)) if lib.name_offset is not None else None
                    imports[dll_name].append((lib.name.decode()[:10000], r))
                elif lib.ordinal is not None:
                    r = (lib.ordinal_offset, lib.ordinal_offset + thunk_size) if lib.ordinal_offset is not None else None
                    imports[dll_name].append((f"{dll_name}:ordinal{lib.ordinal}", r))

        # Unique libraries.
        libraries: dict[str, list[Optional[Range]]] = defaultdict(list)
        for dll_name in imports:
            libraries[dll_name.lower()].extend(dll_ranges[dll_name])
        for b, ranges in zip(hash_indices(256, list(libraries)), libraries.values(), strict=True):
            C.add_item(1, ranges)
            C.add_item(2 + b, ranges)

        # Fully-qualified names of imported functions.
        items = [(dll_name.lower() + ":" + e, [r] + dll_ranges[dll_name]) for dll_name, elist in imports.items() for e, r in elist]
        for b, (_, ranges) in zip(hash_indices(1024, [s for s, _ in items]), items, strict=True):
            C.add_item(0, ranges)
            C.add_item(258 + b, ranges)

        return C.build()

    def _import_items(self, bytez: bytes, pe: pefile.PE | None, merged: bool) -> ItemTable:
        """The items of `raw_features` (`merged=False`) or of `ImportsInfoMerged.raw_features` (`merged=True`)."""
        n = len(bytez)
        families = {"imports:num_imports": 1, "imports:libraries": 256, "imports:functions": 1024}
        if pe is None or "DIRECTORY_ENTRY_IMPORT" not in pe.__dict__.keys():
            return ItemTable(n, families, [])

        # Mirrors `provenance`: the names of all of the descriptors for a DLL contribute to the DLL's features.
        thunk_size = 8 if pe.PE_TYPE == pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS else 4
        dll_ranges: dict[str, list[Optional[Range]]] = defaultdict(list)
        imports: dict[str, list[tuple[str, Optional[Range]]]] = {}
        # Located through the import directory, the section table, the descriptor, the thunks, and each name's
        # terminating zero byte.
        located = pe_locating(pe)
        descriptor_locating: dict[str, list[Range]] = defaultdict(list)
        function_locating: dict[str, list[tuple[Range, ...]]] = {}
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            dll_ranges[dll_name].append(rva_string_range(pe, entry.struct.Name, len(entry.dll)))
            descriptor_locating[dll_name].append(structure_range(entry.struct))
            descriptor_locating[dll_name].extend(rva_ranges(pe, entry.struct.Name + len(entry.dll), 1))
            thunks = [
                tuple(structure_range(t) for t in (lib.struct_table, lib.struct_iat) if t is not None)
                + (((lib.name_offset + len(lib.name), lib.name_offset + len(lib.name) + 1),) if lib.name and lib.name_offset is not None else ())
                for lib in entry.imports
                if (lib.name is not None and len(lib.name)) or lib.ordinal is not None
            ]
            if merged:
                function_locating.setdefault(dll_name, []).extend(thunks)
            else:
                function_locating[dll_name] = thunks
            if merged:
                functions = imports.setdefault(dll_name, [])
            else:
                # A later descriptor for the same DLL replaces the functions of an earlier one.
                functions = imports[dll_name] = []
            for lib in entry.imports:
                if lib.name is not None and len(lib.name):
                    r = (lib.name_offset, lib.name_offset + min(len(lib.name), 10000)) if lib.name_offset is not None else None
                    functions.append((lib.name.decode()[:10000], r))
                elif lib.ordinal is not None:
                    r = (lib.ordinal_offset, lib.ordinal_offset + thunk_size) if lib.ordinal_offset is not None else None
                    functions.append((f"{dll_name}:ordinal{lib.ordinal}", r))

        # One library item per descriptor, keyed by the lowercased name (the readout counts distinct keys).
        items = []
        libraries = [dll_name.lower() for dll_name in imports for _ in dll_ranges[dll_name]]
        ranges = [r for dll_name in imports for r in dll_ranges[dll_name]]
        buckets, _ = feature_hash(256, libraries)
        library_locating = [located + tuple(descriptor_locating[dll_name]) for dll_name in imports for _ in dll_ranges[dll_name]]
        for key, r, b, loc in zip(libraries, ranges, buckets.tolist(), library_locating, strict=True):
            items.append(Item("library", terms=(Term("keyed", "imports:libraries", index=b, key=key, ranges=clipped(n, [r])),), locating=loc))

        # One import item per function. NOTE: without merging, a function's contribution depends on the later
        # descriptors for its DLL (assumption A2), so these items are not local.
        functions = [(dll_name.lower() + ":" + e, clipped(n, [r] + dll_ranges[dll_name])) for dll_name, elist in imports.items() for e, r in elist]
        locating = [located + tuple(descriptor_locating[dll_name]) + function_locating[dll_name][i] for dll_name, elist in imports.items() for i in range(len(elist))]
        buckets, _ = feature_hash(1024, [k for k, _ in functions])
        for (key, r), b, loc in zip(functions, buckets.tolist(), locating, strict=True):
            items.append(Item("import", terms=(
                Term("count", "imports:num_imports", ranges=r),
                Term("hashed", "imports:functions", index=b, key=key, ranges=r),
            ), attrs={"dll": key.split(":", 1)[0]}, locating=loc, local=merged))
        return ItemTable(n, families, items)

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        return self._import_items(bytez, pe, merged=False)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("imports:num_imports"),
            DistinctCount("imports:libraries"),
            DistinctCount("imports:libraries", 256, per_bucket=True),
            Identity("imports:functions", 0, 1024),
        ]


class ImportsInfoMerged(ImportsInfo):
    """
    `ImportsInfo` with the import descriptors of the same DLL merged instead of overwritten.

    NOTE: an addition on top of thrember, not part of it. thrember's `ImportsInfo.raw_features` starts a DLL's function
    list over (`imports[dll_name] = []`) at every descriptor for it, so a second descriptor for an already imported
    DLL (same spelling) erases the first one's functions from the features. That is an implementation quirk, not a
    design choice of the feature set; direction A's experiments use this class (via `merge_import_descriptors`) so
    that no result depends on it (docs/direction-A-threat-model.md). On files with one descriptor per DLL, which is
    almost every file, the features and provenance equal `ImportsInfo`'s.
    """

    def raw_features(self, bytez, pe):
        imports: dict[str, list[str]] = {}
        if pe is None or "DIRECTORY_ENTRY_IMPORT" not in pe.__dict__.keys():
            return imports

        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            functions = imports.setdefault(dll_name, [])
            for lib in entry.imports:
                if lib.name is not None and len(lib.name):
                    functions.append(lib.name.decode()[:10000])
                elif lib.ordinal is not None:
                    functions.append(f"{dll_name}:ordinal{lib.ordinal}")
        return imports

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None or "DIRECTORY_ENTRY_IMPORT" not in pe.__dict__.keys():
            return C.build()

        # Mirrors `ImportsInfo.provenance`, with the descriptors of a DLL merged as in `raw_features`.
        thunk_size = 8 if pe.PE_TYPE == pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS else 4
        dll_ranges: dict[str, list[Optional[Range]]] = defaultdict(list)
        imports: dict[str, list[tuple[str, Optional[Range]]]] = {}
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            dll_ranges[dll_name].append(rva_string_range(pe, entry.struct.Name, len(entry.dll)))
            functions = imports.setdefault(dll_name, [])
            for lib in entry.imports:
                if lib.name is not None and len(lib.name):
                    r = (lib.name_offset, lib.name_offset + min(len(lib.name), 10000)) if lib.name_offset is not None else None
                    functions.append((lib.name.decode()[:10000], r))
                elif lib.ordinal is not None:
                    r = (lib.ordinal_offset, lib.ordinal_offset + thunk_size) if lib.ordinal_offset is not None else None
                    functions.append((f"{dll_name}:ordinal{lib.ordinal}", r))

        libraries: dict[str, list[Optional[Range]]] = defaultdict(list)
        for dll_name in imports:
            libraries[dll_name.lower()].extend(dll_ranges[dll_name])
        for b, ranges in zip(hash_indices(256, list(libraries)), libraries.values(), strict=True):
            C.add_item(1, ranges)
            C.add_item(2 + b, ranges)

        items = [(dll_name.lower() + ":" + e, [r] + dll_ranges[dll_name]) for dll_name, elist in imports.items() for e, r in elist]
        for b, (_, ranges) in zip(hash_indices(1024, [s for s, _ in items]), items, strict=True):
            C.add_item(0, ranges)
            C.add_item(258 + b, ranges)

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        return self._import_items(bytez, pe, merged=True)


def merge_import_descriptors(extractor: "PEFeatureExtractor") -> "PEFeatureExtractor":
    """Replace the extractor's `ImportsInfo` with `ImportsInfoMerged` (in place) and return the extractor."""
    replaced = [ImportsInfoMerged() if type(fe) is ImportsInfo else fe for fe in extractor.features]
    if replaced == extractor.features:
        raise ValueError("The extractor has no ImportsInfo feature type to replace.")
    extractor.features = replaced
    return extractor


def _export_address_offset(pe: pefile.PE, exp: pefile.ExportData) -> Optional[int]:
    """
    The file offset of an export's entry in the export address table.

    pefile omits `address_offset` for exports that it finds only by ordinal (in its second pass over the address
    table), so it is recomputed from the ordinal for them, at the same location pefile read the address from.
    """
    offset: Optional[int] = getattr(exp, "address_offset", None)
    if offset is not None:
        return offset
    try:
        directory = pe.DIRECTORY_ENTRY_EXPORT.struct
        offset = pe.get_offset_from_rva(directory.AddressOfFunctions + 4 * (exp.ordinal - directory.Base))
    except Exception:
        return None
    return int(offset) if offset is not None else None


class ExportsInfo(FeatureType):
    """
    Information about exported functions. Note that the total number of exported
    functions is contained in GeneralFileInfo.
    """

    name = "exports"
    dim = 1 + 128

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        if pe is None:
            return []

        clipped_exports = []
        if "DIRECTORY_ENTRY_EXPORT" in pe.__dict__.keys():
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if exp.name is not None and len(exp.name):
                    clipped_exports.append(exp.name.decode()[:10000])
                elif exp.ordinal is not None:
                    clipped_exports.append(f"ordinal{exp.ordinal}")

        return clipped_exports

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        exports_hashed = FeatureHasher(128, input_type="string").transform([raw_obj]).toarray()[0]
        return np.hstack([np.array([len(exports_hashed)]), exports_hashed.astype(np.float32)])

    @property
    def feature_names(self) -> list[str]:
        return ["num_exports"] + [f"export_hash_{i}" for i in range(128)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None or "DIRECTORY_ENTRY_EXPORT" not in pe.__dict__.keys():
            return C.build()

        # NOTE (Axiom 3): the first feature is meant to be the number of exports, but it is the length of the hashed
        # vector, i.e., always 128 (or 0 if there are no exports), so it receives no contributions.
        items: list[tuple[str, Optional[Range]]] = []
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if exp.name is not None and len(exp.name):
                r = (exp.name_offset, exp.name_offset + min(len(exp.name), 10000)) if exp.name_offset is not None else None
                items.append((exp.name.decode()[:10000], r))
            elif exp.ordinal is not None:
                offset = _export_address_offset(pe, exp)
                r = (offset, offset + 4) if offset is not None else None
                items.append((f"ordinal{exp.ordinal}", r))
        for b, (_, r) in zip(hash_indices(128, [s for s, _ in items]), items, strict=True):
            C.add_item(1 + b, [r])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {"exports:count": 1, "exports:hash": 128}
        if pe is None or "DIRECTORY_ENTRY_EXPORT" not in pe.__dict__.keys():
            return ItemTable(n, families, [])

        # Located through the export directory, the section table, and the entries of the name, ordinal, and
        # address tables. NOTE: pefile stops at the first invalid name, so an export's existence also depends on the
        # names before it (not local, assumption A2; the C1 engine re-parses the export directory on any write to it).
        directory = pe.DIRECTORY_ENTRY_EXPORT.struct
        located = pe_locating(pe) + (structure_range(directory),)
        exports: list[tuple[str, Optional[Range], tuple[Range, ...]]] = []
        i = 0
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            tables = rva_ranges(pe, directory.AddressOfFunctions + 4 * (exp.ordinal - directory.Base), 4) if exp.ordinal is not None else ()
            if exp.name is not None and len(exp.name):
                r = (exp.name_offset, exp.name_offset + min(len(exp.name), 10000)) if exp.name_offset is not None else None
                tables += rva_ranges(pe, directory.AddressOfNames + 4 * i, 4) + rva_ranges(pe, directory.AddressOfNameOrdinals + 2 * i, 2)
                if exp.name_offset is not None:
                    tables += ((exp.name_offset + len(exp.name), exp.name_offset + len(exp.name) + 1),)
                exports.append((exp.name.decode()[:10000], r, tables))
                i += 1
            elif exp.ordinal is not None:
                offset = _export_address_offset(pe, exp)
                r = (offset, offset + 4) if offset is not None else None
                exports.append((f"ordinal{exp.ordinal}", r, tables))
        buckets, signs = feature_hash(128, [k for k, _, _ in exports])
        items = [
            Item("export", terms=(
                Term("count", "exports:count", ranges=clipped(n, [r])),
                Term("hashed", "exports:hash", index=b, sign=sign, key=key, ranges=clipped(n, [r])),
            ), locating=located + tables, local=False)
            for (key, r, tables), b, sign in zip(exports, buckets.tolist(), signs.tolist(), strict=True)
        ]
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        # NOTE: the first feature is meant to be the number of exports, but it is the length of the hashed vector:
        # 128 if there is any export, else 0.
        return [Positive(("exports:count", 0), scale=128.0), Identity("exports:hash", 0, 128)]


class HeaderFileInfo(FeatureType):
    """
    Features from the COFF, OPTIONAL, and DOS headers.
    """

    name = "header"
    dim = 74

    def __init__(self):
        super(FeatureType, self).__init__()
        # We save our own lists so that our one hot encodings and categorical features are more robust to future
        # changes in the list of possibilities from Microsoft or pefile
        self._machine_types = [
            "IMAGE_FILE_MACHINE_UNKNOWN",
            "IMAGE_FILE_MACHINE_I386",
            "IMAGE_FILE_MACHINE_R3000",
            "IMAGE_FILE_MACHINE_R4000",
            "IMAGE_FILE_MACHINE_R10000",
            "IMAGE_FILE_MACHINE_WCEMIPSV2",
            "IMAGE_FILE_MACHINE_ALPHA",
            "IMAGE_FILE_MACHINE_SH3",
            "IMAGE_FILE_MACHINE_SH3DSP",
            "IMAGE_FILE_MACHINE_SH3E",
            "IMAGE_FILE_MACHINE_SH4",
            "IMAGE_FILE_MACHINE_SH5",
            "IMAGE_FILE_MACHINE_ARM",
            "IMAGE_FILE_MACHINE_THUMB",
            "IMAGE_FILE_MACHINE_ARMNT",
            "IMAGE_FILE_MACHINE_AM33",
            "IMAGE_FILE_MACHINE_POWERPC",
            "IMAGE_FILE_MACHINE_POWERPCFP",
            "IMAGE_FILE_MACHINE_IA64",
            "IMAGE_FILE_MACHINE_MIPS16",
            "IMAGE_FILE_MACHINE_ALPHA64",
            "IMAGE_FILE_MACHINE_AXP64",
            "IMAGE_FILE_MACHINE_MIPSFPU",
            "IMAGE_FILE_MACHINE_MIPSFPU16",
            "IMAGE_FILE_MACHINE_TRICORE",
            "IMAGE_FILE_MACHINE_CEF",
            "IMAGE_FILE_MACHINE_EBC",
            "IMAGE_FILE_MACHINE_RISCV32",
            "IMAGE_FILE_MACHINE_RISCV64",
            "IMAGE_FILE_MACHINE_RISCV128",
            "IMAGE_FILE_MACHINE_LOONGARCH32",
            "IMAGE_FILE_MACHINE_LOONGARCH64",
            "IMAGE_FILE_MACHINE_AMD64",
            "IMAGE_FILE_MACHINE_M32R",
            "IMAGE_FILE_MACHINE_ARM64",
            "IMAGE_FILE_MACHINE_CEE",
        ]
        self._machine_types_dict = dict([(mt, i) for i, mt in enumerate(self._machine_types)])
        self._subsystem_types = [
            "IMAGE_SUBSYSTEM_UNKNOWN",
            "IMAGE_SUBSYSTEM_NATIVE",
            "IMAGE_SUBSYSTEM_WINDOWS_GUI",
            "IMAGE_SUBSYSTEM_WINDOWS_CUI",
            "IMAGE_SUBSYSTEM_OS2_CUI",
            "IMAGE_SUBSYSTEM_POSIX_CUI",
            "IMAGE_SUBSYSTEM_NATIVE_WINDOWS",
            "IMAGE_SUBSYSTEM_WINDOWS_CE_GUI",
            "IMAGE_SUBSYSTEM_EFI_APPLICATION",
            "IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER",
            "IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER",
            "IMAGE_SUBSYSTEM_EFI_ROM",
            "IMAGE_SUBSYSTEM_XBOX",
            "IMAGE_SUBSYSTEM_WINDOWS_BOOT_APPLICATION",
        ]
        self._subsystem_types_dict = dict([(st, i) for i, st in enumerate(self._subsystem_types)])
        self._image_characteristics = [
            "RELOCS_STRIPPED",
            "EXECUTABLE_IMAGE",
            "LINE_NUMS_STRIPPED",
            "LOCAL_SYMS_STRIPPED",
            "AGGRESIVE_WS_TRIM",
            "LARGE_ADDRESS_AWARE",
            "16BIT_MACHINE",
            "BYTES_REVERSED_LO",
            "32BIT_MACHINE",
            "DEBUG_STRIPPED",
            "REMOVABLE_RUN_FROM_SWAP",
            "NET_RUN_FROM_SWAP",
            "SYSTEM",
            "DLL",
            "UP_SYSTEM_ONLY",
            "BYTES_REVERSED_HI",
        ]
        self._dll_characteristics = [
            "HIGH_ENTROPY_VA",
            "DYNAMIC_BASE",
            "FORCE_INTEGRITY",
            "NX_COMPAT",
            "NO_ISOLATION",
            "NO_SEH",
            "NO_BIND",
            "APPCONTAINER",
            "WDM_DRIVER",
            "GUARD_CF",
            "TERMINAL_SERVER_AWARE",
        ]
        self._dos_members = [
            "e_magic",
            "e_cblp",
            "e_cp",
            "e_crlc",
            "e_cparhdr",
            "e_minalloc",
            "e_maxalloc",
            "e_ss",
            "e_sp",
            "e_csum",
            "e_ip",
            "e_cs",
            "e_lfarlc",
            "e_ovno",
            "e_oemid",
            "e_oeminfo",
            "e_lfanew",
        ]

    def raw_features(self, bytez, pe):
        if pe is None:
            return {}

        raw_obj = {}
        raw_obj["coff"] = {
            "timestamp": 0,
            "machine": "",
            "number_of_sections": 0,
            "number_of_symbols": 0,
            "sizeof_optional_header": 0,
            "pointer_to_symbol_table": 0,
            "characteristics": [],
        }
        raw_obj["optional"] = {
            "magic": 0,
            "subsystem": "",
            "major_image_version": 0,
            "minor_image_version": 0,
            "major_linker_version": 0,
            "minor_linker_version": 0,
            "major_operating_system_version": 0,
            "minor_operating_system_version": 0,
            "major_subsystem_version": 0,
            "minor_subsystem_version": 0,
            "sizeof_code": 0,
            "sizeof_headers": 0,
            "sizeof_image": 0,
            "sizeof_initialized_data": 0,
            "sizeof_uninitialized_data": 0,
            "sizeof_stack_reserve": 0,
            "sizeof_stack_commit": 0,
            "sizeof_heap_reserve": 0,
            "sizeof_heap_commit": 0,
            "address_of_entrypoint": 0,
            "base_of_code": 0,
            "base_of_data": 0,
            "image_base": 0,
            "section_alignment": 0,
            "checksum": 0,
            "number_of_rvas_and_sizes": 0,
            "dll_characteristics": [],
        }
        raw_obj["dos"] = {member: 0 for member in self._dos_members}
        if pe is None:
            return raw_obj

        raw_obj["coff"]["timestamp"] = pe.FILE_HEADER.TimeDateStamp
        raw_obj["coff"]["machine"] = pefile.MACHINE_TYPE.get(pe.FILE_HEADER.Machine, "IMAGE_FILE_MACHINE_UNKNOWN")
        raw_obj["coff"]["number_of_sections"] = pe.FILE_HEADER.NumberOfSections
        raw_obj["coff"]["number_of_symbols"] = pe.FILE_HEADER.NumberOfSymbols
        raw_obj["coff"]["sizeof_optional_header"] = pe.FILE_HEADER.SizeOfOptionalHeader
        raw_obj["coff"]["pointer_to_symbol_table"] = pe.FILE_HEADER.PointerToSymbolTable
        raw_obj["coff"]["characteristics"] = [
            k[11:] for k, v in pe.FILE_HEADER.__dict__.items() if k.startswith("IMAGE_FILE_") and v
        ]
        raw_obj["optional"]["magic"] = pe.OPTIONAL_HEADER.Magic
        raw_obj["optional"]["subsystem"] = pefile.SUBSYSTEM_TYPE.get(
            pe.OPTIONAL_HEADER.Subsystem, "IMAGE_SUBSYSTEM_UNKNOWN"
        )
        raw_obj["optional"]["major_image_version"] = pe.OPTIONAL_HEADER.MajorImageVersion
        raw_obj["optional"]["minor_image_version"] = pe.OPTIONAL_HEADER.MinorImageVersion
        raw_obj["optional"]["major_linker_version"] = pe.OPTIONAL_HEADER.MajorLinkerVersion
        raw_obj["optional"]["minor_linker_version"] = pe.OPTIONAL_HEADER.MinorLinkerVersion
        raw_obj["optional"]["major_operating_system_version"] = pe.OPTIONAL_HEADER.MajorOperatingSystemVersion
        raw_obj["optional"]["minor_operating_system_version"] = pe.OPTIONAL_HEADER.MinorOperatingSystemVersion
        raw_obj["optional"]["major_subsystem_version"] = pe.OPTIONAL_HEADER.MajorSubsystemVersion
        raw_obj["optional"]["minor_subsystem_version"] = pe.OPTIONAL_HEADER.MinorSubsystemVersion
        raw_obj["optional"]["sizeof_code"] = pe.OPTIONAL_HEADER.SizeOfCode
        raw_obj["optional"]["sizeof_headers"] = pe.OPTIONAL_HEADER.SizeOfHeaders
        raw_obj["optional"]["sizeof_image"] = pe.OPTIONAL_HEADER.SizeOfImage
        raw_obj["optional"]["sizeof_initialized_data"] = pe.OPTIONAL_HEADER.SizeOfInitializedData
        raw_obj["optional"]["sizeof_uninitialized_data"] = pe.OPTIONAL_HEADER.SizeOfUninitializedData
        raw_obj["optional"]["sizeof_stack_reserve"] = pe.OPTIONAL_HEADER.SizeOfStackReserve
        raw_obj["optional"]["sizeof_stack_commit"] = pe.OPTIONAL_HEADER.SizeOfStackCommit
        raw_obj["optional"]["sizeof_heap_reserve"] = pe.OPTIONAL_HEADER.SizeOfHeapReserve
        raw_obj["optional"]["sizeof_heap_commit"] = pe.OPTIONAL_HEADER.SizeOfHeapCommit
        raw_obj["optional"]["address_of_entrypoint"] = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        raw_obj["optional"]["base_of_code"] = pe.OPTIONAL_HEADER.BaseOfCode
        raw_obj["optional"]["image_base"] = pe.OPTIONAL_HEADER.ImageBase
        raw_obj["optional"]["section_alignment"] =  pe.OPTIONAL_HEADER.SectionAlignment
        raw_obj["optional"]["checksum"] =  pe.OPTIONAL_HEADER.CheckSum
        raw_obj["optional"]["number_of_rvas_and_sizes"] = pe.OPTIONAL_HEADER.NumberOfRvaAndSizes
        raw_obj["optional"]["dll_characteristics"] = [
            k[25:] for k, v in pe.OPTIONAL_HEADER.__dict__.items() if k.startswith("IMAGE_DLLCHARACTERISTICS_") and v
        ]
        dos_dict = pe.DOS_HEADER.dump_dict()
        for member in self._dos_members:
            if dos_dict[member].get("Value") is not None:
                raw_obj["dos"][member] = dos_dict[member]["Value"]
        return raw_obj

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        return np.hstack(
            [
                raw_obj["coff"]["timestamp"],
                raw_obj["coff"]["number_of_sections"],
                raw_obj["coff"]["number_of_symbols"],
                raw_obj["coff"]["sizeof_optional_header"],
                raw_obj["coff"]["pointer_to_symbol_table"],
                self._machine_types_dict.get(raw_obj["coff"]["machine"], 0),  # Categorical
                self._subsystem_types_dict.get(raw_obj["optional"]["subsystem"], 0),  # Categorical
                raw_obj["optional"]["major_image_version"],
                raw_obj["optional"]["minor_image_version"],
                raw_obj["optional"]["major_linker_version"],
                raw_obj["optional"]["minor_linker_version"],
                raw_obj["optional"]["major_operating_system_version"],
                raw_obj["optional"]["minor_operating_system_version"],
                raw_obj["optional"]["major_subsystem_version"],
                raw_obj["optional"]["minor_subsystem_version"],
                raw_obj["optional"]["sizeof_code"],
                raw_obj["optional"]["sizeof_headers"],
                raw_obj["optional"]["sizeof_image"],
                raw_obj["optional"]["sizeof_initialized_data"],
                raw_obj["optional"]["sizeof_uninitialized_data"],
                raw_obj["optional"]["sizeof_stack_reserve"],
                raw_obj["optional"]["sizeof_stack_commit"],
                raw_obj["optional"]["sizeof_heap_reserve"],
                raw_obj["optional"]["sizeof_heap_commit"],
                raw_obj["optional"]["address_of_entrypoint"],
                raw_obj["optional"]["base_of_code"],
                raw_obj["optional"]["image_base"],
                raw_obj["optional"]["section_alignment"],
                raw_obj["optional"]["checksum"],
                raw_obj["optional"]["number_of_rvas_and_sizes"],
                [ch in raw_obj["coff"]["characteristics"] for ch in self._image_characteristics],
                [ch in raw_obj["optional"]["dll_characteristics"] for ch in self._dll_characteristics],
                [raw_obj["dos"][member] for member in self._dos_members],
            ]
        ).astype(np.float32)

    # The header field each of the first 30 features is read from, in the order of `process_raw_features`.
    _fields = [
        ("FILE_HEADER", "TimeDateStamp"),
        ("FILE_HEADER", "NumberOfSections"),
        ("FILE_HEADER", "NumberOfSymbols"),
        ("FILE_HEADER", "SizeOfOptionalHeader"),
        ("FILE_HEADER", "PointerToSymbolTable"),
        ("FILE_HEADER", "Machine"),
        ("OPTIONAL_HEADER", "Subsystem"),
        ("OPTIONAL_HEADER", "MajorImageVersion"),
        ("OPTIONAL_HEADER", "MinorImageVersion"),
        ("OPTIONAL_HEADER", "MajorLinkerVersion"),
        ("OPTIONAL_HEADER", "MinorLinkerVersion"),
        ("OPTIONAL_HEADER", "MajorOperatingSystemVersion"),
        ("OPTIONAL_HEADER", "MinorOperatingSystemVersion"),
        ("OPTIONAL_HEADER", "MajorSubsystemVersion"),
        ("OPTIONAL_HEADER", "MinorSubsystemVersion"),
        ("OPTIONAL_HEADER", "SizeOfCode"),
        ("OPTIONAL_HEADER", "SizeOfHeaders"),
        ("OPTIONAL_HEADER", "SizeOfImage"),
        ("OPTIONAL_HEADER", "SizeOfInitializedData"),
        ("OPTIONAL_HEADER", "SizeOfUninitializedData"),
        ("OPTIONAL_HEADER", "SizeOfStackReserve"),
        ("OPTIONAL_HEADER", "SizeOfStackCommit"),
        ("OPTIONAL_HEADER", "SizeOfHeapReserve"),
        ("OPTIONAL_HEADER", "SizeOfHeapCommit"),
        ("OPTIONAL_HEADER", "AddressOfEntryPoint"),
        ("OPTIONAL_HEADER", "BaseOfCode"),
        ("OPTIONAL_HEADER", "ImageBase"),
        ("OPTIONAL_HEADER", "SectionAlignment"),
        ("OPTIONAL_HEADER", "CheckSum"),
        ("OPTIONAL_HEADER", "NumberOfRvaAndSizes"),
    ]

    @property
    def feature_names(self) -> list[str]:
        return (
            [f"{header.lower()}_{field}" for header, field in self._fields]
            + [f"characteristics_{c}" for c in self._image_characteristics]
            + [f"dll_characteristics_{c}" for c in self._dll_characteristics]
            + [f"dos_{m}" for m in self._dos_members]
        )

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None:
            return C.build()

        for i, (header, field) in enumerate(self._fields):
            C.add_item(i, [field_range(getattr(pe, header), field)])
        offset = len(self._fields)
        for i in range(len(self._image_characteristics)):
            C.add_item(offset + i, [field_range(pe.FILE_HEADER, "Characteristics")])
        offset += len(self._image_characteristics)
        for i in range(len(self._dll_characteristics)):
            C.add_item(offset + i, [field_range(pe.OPTIONAL_HEADER, "DllCharacteristics")])
        offset += len(self._dll_characteristics)
        for i, member in enumerate(self._dos_members):
            C.add_item(offset + i, [field_range(pe.DOS_HEADER, member)])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {"header:fields": len(self._fields), "header:characteristics": 2, "header:dos": len(self._dos_members)}
        if pe is None:
            return ItemTable(n, families, [])

        located = pe_locating(pe)

        def field(family: str, index: int, structure: pefile.Structure, name: str, value: int) -> Item:
            return Item("field", terms=(Term("slot", family, index=index, value=value, ranges=clipped(n, [field_range(structure, name)])),), attrs={"field": name}, locating=located)

        items = [field("header:fields", i, getattr(pe, header), name, getattr(getattr(pe, header), name)) for i, (header, name) in enumerate(self._fields)]
        items.append(field("header:characteristics", 0, pe.FILE_HEADER, "Characteristics", pe.FILE_HEADER.Characteristics))
        items.append(field("header:characteristics", 1, pe.OPTIONAL_HEADER, "DllCharacteristics", pe.OPTIONAL_HEADER.DllCharacteristics))
        dos_dict = pe.DOS_HEADER.dump_dict()
        for i, member in enumerate(self._dos_members):
            value = dos_dict[member].get("Value")
            items.append(field("header:dos", i, pe.DOS_HEADER, member, value if value is not None else 0))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        # The category codes of `process_raw_features`, as lookups of the raw field value.
        machine = {v: float(self._machine_types_dict.get(k, 0)) for k, v in pefile.MACHINE_TYPE.items() if isinstance(k, str)}
        subsystem = {v: float(self._subsystem_types_dict.get(k, 0)) for k, v in pefile.SUBSYSTEM_TYPE.items() if isinstance(k, str)}
        # The flags pefile sets from the bit fields (`set_flags`); a flag pefile does not know is never set.
        image = tuple(pefile.IMAGE_CHARACTERISTICS.get(f"IMAGE_FILE_{c}", 0) for c in self._image_characteristics)
        dll = tuple(pefile.DLL_CHARACTERISTICS.get(f"IMAGE_DLLCHARACTERISTICS_{c}", 0) for c in self._dll_characteristics)
        return [
            Identity("header:fields", 0, 5),
            Lookup(("header:fields", 5), machine, default=float(self._machine_types_dict.get("IMAGE_FILE_MACHINE_UNKNOWN", 0))),
            Lookup(("header:fields", 6), subsystem, default=float(self._subsystem_types_dict.get("IMAGE_SUBSYSTEM_UNKNOWN", 0))),
            Identity("header:fields", 7, len(self._fields) - 7),
            BitTest(("header:characteristics", 0), image),
            BitTest(("header:characteristics", 1), dll),
            Identity("header:dos", 0, len(self._dos_members)),
        ]


class DataDirectories(FeatureType):
    """
    Extracts size and virtual address of the first 15 data directories
    """

    name = "datadirectories"
    dim = 16*2 + 2

    def __init__(self):
        super(FeatureType, self).__init__()
        self._name_order = [
            "EXPORT",
            "IMPORT",
            "RESOURCE",
            "EXCEPTION",
            "SECURITY",
            "BASERELOC",
            "DEBUG",
            "COPYRIGHT",
            "GLOBALPTR",
            "TLS",
            "LOAD_CONFIG",
            "BOUND_IMPORT",
            "IAT",
            "DELAY_IMPORT",
            "COM_DESCRIPTOR",
            "RESERVED",
        ]

    def raw_features(self, bytez, pe):
        output = []
        if pe is None:
            return output

        output.append(
            {
                "has_relocs": int(pe.has_relocs()),
                "has_dynamic_relocs": int(pe.has_dynamic_relocs()),
            }
        )

        for data_directory in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
            output.append(
                {
                    "name": str(data_directory.name).replace("IMAGE_DIRECTORY_ENTRY_", ""),
                    "size": data_directory.Size,
                    "virtual_address": data_directory.VirtualAddress,
                }
            )

        return output

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        features = np.zeros(2 * len(self._name_order) + 2, dtype=np.float32)
        for i in range(1, len(raw_obj)-1):
            idx = self._name_order.index(raw_obj[i]["name"])
            features[2 * idx] = raw_obj[i]["size"]
            features[2 * idx + 1] = raw_obj[i]["virtual_address"]
        features[-2] = raw_obj[0]["has_relocs"]
        features[-1] = raw_obj[0]["has_dynamic_relocs"]
        return features

    @property
    def feature_names(self) -> list[str]:
        return [f"{n.lower()}_{f}" for n in self._name_order for f in ("size", "virtual_address")] + ["has_relocs", "has_dynamic_relocs"]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None:
            return C.build()

        # Mirror `process_raw_features`, which skips the last data directory (usually RESERVED).
        directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
        for d in directories[:-1]:
            idx = self._name_order.index(str(d.name).replace("IMAGE_DIRECTORY_ENTRY_", ""))
            C.add_item(2 * idx, [field_range(d, "Size")])
            C.add_item(2 * idx + 1, [field_range(d, "VirtualAddress")])

        # Whether the relocations were parsed is determined by the directory that points to them.
        for col, which in [(32, "BASERELOC"), (33, "LOAD_CONFIG")]:
            idx = self._name_order.index(which)
            if idx < len(directories):
                C.add_item(col, [structure_range(directories[idx])])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {"datadirectories:fields": 2 * len(self._name_order)}
        if pe is None:
            return ItemTable(n, families, [])

        # Mirror `process_raw_features`, which skips the last data directory (usually RESERVED).
        items = []
        located = pe_locating(pe)
        directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
        for d in directories[:-1]:
            idx = self._name_order.index(str(d.name).replace("IMAGE_DIRECTORY_ENTRY_", ""))
            for k, name in enumerate(("Size", "VirtualAddress")):
                term = Term("slot", "datadirectories:fields", index=2 * idx + k, value=getattr(d, name), ranges=clipped(n, [field_range(d, name)]))
                items.append(Item("field", terms=(term,), attrs={"field": f"{d.name}.{name}"}, locating=located))

        # Whether the relocations were parsed: an outcome of pefile's parser, determined by the directories that
        # point to them.
        attr_ranges = {}
        for attr, which in [("has_relocs", "BASERELOC"), ("has_dynamic_relocs", "LOAD_CONFIG")]:
            idx = self._name_order.index(which)
            attr_ranges[attr] = (clipped(n, [structure_range(directories[idx])]),) if idx < len(directories) else ()
        # Parsed from the directories' data (in `located`); pefile stops at a block past SizeOfImage.
        relocs_locating = located + (field_range(pe.OPTIONAL_HEADER, "SizeOfImage"),)
        items.append(Item("relocs", attrs={"has_relocs": int(pe.has_relocs()), "has_dynamic_relocs": int(pe.has_dynamic_relocs())}, attr_ranges=attr_ranges, locating=relocs_locating))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("datadirectories:fields", 0, 2 * len(self._name_order)),
            Opaque("relocs", ("has_relocs", "has_dynamic_relocs"), (0.0, 0.0)),
        ]


class RichHeader(FeatureType):
    """
    Extracts features based on the file's rich header information
    """

    name = "richheader"
    dim = 1 + 32

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        if pe is not None and pe.RICH_HEADER is not None:
            return pe.RICH_HEADER.values
        return []

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        number_of_pairs = int(len(raw_obj) / 2)
        paired_values = [(str(raw_obj[i]), raw_obj[i + 1]) for i in range(0, len(raw_obj) - 1, 2)]
        paired_values_hashed = FeatureHasher(32, input_type="pair").transform([paired_values]).toarray()[0]
        return np.hstack([number_of_pairs, paired_values_hashed]).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return ["num_pairs"] + [f"pair_hash_{i}" for i in range(32)]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None or pe.RICH_HEADER is None:
            return C.build()

        # pefile reads the Rich header as dwords starting at 0x80: the DanS signature and three padding dwords,
        # followed by the (compid, count) pairs, eight bytes each.
        values = pe.RICH_HEADER.values
        pairs = [(0x80 + 16 + 8 * i, 0x80 + 16 + 8 * i + 8) for i in range(len(values) // 2)]
        for b, r in zip(hash_indices(32, [str(values[2 * i]) for i in range(len(pairs))]), pairs, strict=True):
            C.add_item(0, [r])
            C.add_item(1 + b, [r])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        families = {"richheader:num_pairs": 1, "richheader:pairs": 32}
        if pe is None or pe.RICH_HEADER is None:
            return ItemTable(n, families, [])

        # The (compid, count) pairs, eight bytes each after the DanS signature and padding (see `provenance`).
        values = pe.RICH_HEADER.values
        num_pairs = len(values) // 2
        # pefile searches for the "Rich" marker in [0x80, optional header), so the whole range locates every pair.
        located = pe_locating(pe) + ((0x80, pe.OPTIONAL_HEADER.get_file_offset()),)
        buckets, signs = feature_hash(32, [str(values[2 * i]) for i in range(num_pairs)])
        items = []
        for i in range(num_pairs):
            r = clipped(n, [(0x80 + 16 + 8 * i, 0x80 + 16 + 8 * i + 8)])
            items.append(Item("rich_pair", terms=(
                Term("count", "richheader:num_pairs", ranges=r),
                Term("hashed", "richheader:pairs", index=int(buckets[i]), value=values[2 * i + 1], sign=int(signs[i]), key=str(values[2 * i]), attr="count", ranges=r),
            ), attrs={"compid": values[2 * i], "count": values[2 * i + 1]}, locating=located))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [Identity("richheader:num_pairs"), Identity("richheader:pairs", 0, 32)]


class AuthenticodeSignature(FeatureType):
    """
    Extracts Authenticode Digital Signature features
    """

    name = "authenticode"
    dim = 8

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, bytez, pe):
        if pe is None:
            return {}

        raw_obj = {
            "num_certs": 0,
            "self_signed": 0,
            "empty_program_name": 0,
            "no_countersigner": 0,
            "parse_error": 0,
            "chain_max_depth": 0,
            "latest_signing_time": 0,
            "signing_time_diff": 0,
        }
        try:
            signed_pe = SignedPEFile(io.BytesIO(bytez))
            for signed_data in signed_pe.iter_signed_datas():
                raw_obj["num_certs"] += 1
                if signed_data.signer_info.program_name is None:
                    raw_obj["empty_program_name"] = 1

                # Parse countersigner
                signer_info = signed_data.signer_info
                countersigner = signer_info.countersigner

                # Parse signing time
                if countersigner is not None:
                    signing_time = countersigner.signing_time.timestamp()
                    if signing_time >= raw_obj["latest_signing_time"]:
                        raw_obj["latest_signing_time"] = signing_time
                    pe_timestamp = pe.FILE_HEADER.TimeDateStamp
                    raw_obj["signing_time_diff"] = signing_time - pe_timestamp
                else:
                    raw_obj["no_countersigner"] = 1

                # Check if cert is self-signed
                certs = signed_data.certificates
                if len(certs) > raw_obj["chain_max_depth"]:
                    raw_obj["chain_max_depth"] = len(certs)
                for cert in certs[:-1]:
                    if cert.issuer == cert.subject:
                        raw_obj["self_signed"] = 1

        except signify.exceptions.SignerInfoParseError:
            raw_obj["parse_error"] = 1
        except signify.exceptions.ParseError:
            raw_obj["parse_error"] = 1
        except ValueError:
            raw_obj["parse_error"] = 1
        except KeyError:
            raw_obj["parse_error"] = 1
        return raw_obj

    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        return np.hstack([
            raw_obj["num_certs"],
            raw_obj["self_signed"],
            raw_obj["empty_program_name"],
            raw_obj["no_countersigner"],
            raw_obj["parse_error"],
            raw_obj["chain_max_depth"],
            raw_obj["latest_signing_time"],
            raw_obj["signing_time_diff"],
        ]).astype(np.float32)

    @property
    def feature_names(self) -> list[str]:
        return [
            "num_certs",
            "self_signed",
            "empty_program_name",
            "no_countersigner",
            "parse_error",
            "chain_max_depth",
            "latest_signing_time",
            "signing_time_diff",
        ]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        C = Contributions(len(bytez), self.dim)
        if pe is None:
            return C.build()

        # Every feature is computed by parsing the certificate table, which the security directory points to. Note
        # that the security directory's address is a file offset, not an RVA.
        directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
        ranges: list[Optional[Range]] = []
        if len(directories) > 4:
            security = directories[4]
            ranges.append(structure_range(security))
            if security.Size > 0:
                ranges.append((security.VirtualAddress, security.VirtualAddress + security.Size))
        for col in range(self.dim):
            C.add_item(col, ranges)
        # The signing time difference also depends upon the timestamp in the COFF header.
        C.add_item(7, [field_range(pe.FILE_HEADER, "TimeDateStamp")])

        return C.build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        n = len(bytez)
        if pe is None:
            return ItemTable(n, {}, [])

        # The certificate table, parsed by signify (opaque to the model), located by the security directory (whose
        # address is a file offset, not an RVA). The signing time difference also reads the COFF timestamp.
        directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
        ranges: list[Optional[Range]] = []
        if len(directories) > 4:
            security = directories[4]
            ranges.append(structure_range(security))
            if security.Size > 0:
                ranges.append((security.VirtualAddress, security.VirtualAddress + security.Size))
        unit = clipped(n, ranges)
        attrs = self.raw_features(bytez, pe)
        attr_ranges = {a: (unit,) for a in self.feature_names}
        attr_ranges["signing_time_diff"] = (unit, clipped(n, [field_range(pe.FILE_HEADER, "TimeDateStamp")]))
        return ItemTable(n, {}, [Item("certificate_table", attrs=attrs, attr_ranges=attr_ranges, locating=pe_locating(pe))])

    @property
    def readouts(self) -> list[Readout]:
        return [Opaque("certificate_table", tuple(self.feature_names), (0.0,) * self.dim)]


class PEFormatWarnings(FeatureType):
    """
    Features based on warnings thrown by PEFile parsing
    """

    name = "pefilewarnings"
    dim = 87 + 1

    def __init__(self, warnings_file: Path):
        self.warning_prefixes = set()
        self.warning_suffixes = set()
        self.warning_ids = {}
        
        if isinstance(warnings_file, Path) and warnings_file.exists():
            with open(warnings_file, "r") as f:
                i = 0
                for line in f:
                    line = line.strip()
                    if line.startswith("..."):
                        self.warning_suffixes.add(line[3:])
                        self.warning_ids[line] = i
                    else:
                        self.warning_prefixes.add(line[:-3])
                        self.warning_ids[line] = i
                    i += 1

    def raw_features(self, bytez, pe):
        if pe is None:
            return []

        warnings = set(pe.get_warnings())
        warnings_norm = set()
        for warning in warnings:
            found_warning = False
            for suf in self.warning_suffixes:
                if warning.endswith(suf):
                    warnings_norm.add("..." + suf)
                    found_warning = True
                    break
            if found_warning:
                continue
            for pre in self.warning_prefixes:
                if warning.startswith(pre):
                    warnings_norm.add(pre + "...")
                    found_warning = True
                    break
            if not found_warning:
                print("WARN: Unknown pefile warning:", warning)

        return sorted(warnings_norm)


    def process_raw_features(self, raw_obj):
        if not raw_obj:
            return np.zeros(self.dim, dtype=np.float32)

        ids = [0 for _ in range(self.dim)]
        for warning_norm in raw_obj:
            ids[self.warning_ids[warning_norm]] = 1.0
        ids[self.dim-1] = len(raw_obj)
        return np.array(ids, dtype=np.float32)

    @property
    def feature_names(self) -> list[str]:
        warnings = sorted(self.warning_ids, key=lambda w: self.warning_ids[w])
        return [f"warning_{w}" for w in warnings] + ["num_warnings"]

    def provenance(self, bytez: bytes, pe: pefile.PE | None = None) -> BoxMatrix:
        # NOTE (Axiom 3): pefile emits warnings from all over its parser and does not record which bytes caused them,
        # so these features receive no contributions.
        return Contributions(len(bytez), self.dim).build()

    def items(self, bytez: bytes, pe: pefile.PE | None = None) -> ItemTable:
        # NOTE (Axiom 3): pefile does not record which bytes caused a warning; these features are outside the model.
        return ItemTable(len(bytez), {}, [])

    @property
    def readouts(self) -> list[Readout]:
        return [Outside(self.dim)]


class PEFeatureExtractor(object):
    """
    Extract useful features from a PE file, and return as a vector of fixed size.
    """

    def __init__(self, features_file: Path | None = None):

        cwd = os.path.dirname(os.path.abspath(__file__))
        warnings_file = Path(os.path.join(cwd, "pefile_warnings.txt"))

        self.features = []
        features = OrderedDict([
            ("GeneralFileInfo", GeneralFileInfo()),
            ("ByteHistogram", ByteHistogram()),
            ("ByteEntropyHistogram", ByteEntropyHistogram()),
            ("StringExtractor", StringExtractor()),
            ("HeaderFileInfo", HeaderFileInfo()),
            ("SectionInfo", SectionInfo()),
            ("ImportsInfo", ImportsInfo()),
            ("ExportsInfo", ExportsInfo()),
            ("DataDirectories", DataDirectories()),
            ("RichHeader", RichHeader()),
            ("AuthenticodeSignature", AuthenticodeSignature()),
            ("PEFormatWarnings", PEFormatWarnings(warnings_file)),
        ])
        feature_names = features.keys()

        if isinstance(features_file, Path) and features_file.exists():
            with features_file.open(encoding="utf8") as f:
                x = json.load(f)
                self.features = [features[feature] for feature in feature_names if x["features"].get(feature) is not None]
        else:
            self.features = [features[feature] for feature in feature_names]

        self.dim = sum([fe.dim for fe in self.features])

    def raw_features(self, bytez: bytes):
        pe = None
        try:
            pe = pefile.PE(data=bytez)
        except pefile.PEFormatError:
            pass
        except AttributeError:
            pass
        features = {"sha256": hashlib.sha256(bytez).hexdigest()}
        features.update({fe.name: fe.raw_features(bytez, pe) for fe in self.features})
        return features

    def process_raw_features(self, raw_obj):
        feature_vectors = [fe.process_raw_features(raw_obj[fe.name]) for fe in self.features]
        return np.hstack(feature_vectors).astype(np.float32)

    def feature_vector(self, bytez):
        return self.process_raw_features(self.raw_features(bytez))

    @property
    def feature_names(self) -> list[str]:
        """The name of each feature, prefixed by the name of its feature type, in the order of the feature vector."""
        return [f"{fe.name}:{n}" for fe in self.features for n in fe.feature_names]

    def feature_vector_with_provenance(self, bytez: bytes, empty: EmptyPolicy = "null") -> tuple[np.ndarray, Provenance]:
        """
        Compute the feature vector and its explanation provenance, parsing the file only once.

        Args:
            bytez: The raw bytes of the file.
            empty: How to treat features that receive no contributions (see provexp.provenance.EmptyPolicy).

        Returns:
            The feature vector, identical to `feature_vector(bytez)`, and its provenance.
        """
        # Mirrors `raw_features`.
        pe = None
        try:
            pe = pefile.PE(data=bytez)
        except pefile.PEFormatError:
            pass
        except AttributeError:
            pass
        raw_obj = {fe.name: fe.raw_features(bytez, pe) for fe in self.features}
        x = self.process_raw_features(raw_obj)
        C = BoxMatrix.hstack([fe.provenance(bytez, pe) for fe in self.features])
        return x, Provenance(C, self.feature_names, empty)

    def provenance(self, bytez: bytes, empty: EmptyPolicy = "null") -> Provenance:
        """
        Compute the explanation provenance of the feature vector of a file.
        """
        return self.feature_vector_with_provenance(bytez, empty)[1]

    def item_table(self, bytez: bytes) -> ItemTable:
        """
        The items of every feature type, parsing the file only once (docs/item-layer-design.md, Section 1).
        """
        # Mirrors `raw_features`.
        pe = None
        try:
            pe = pefile.PE(data=bytez)
        except pefile.PEFormatError:
            pass
        except AttributeError:
            pass
        return ItemTable.concatenate([fe.items(bytez, pe) for fe in self.features])

    @property
    def readouts(self) -> list[Readout]:
        """The formula of every feature, in the order of the feature vector (`provexp.items.evaluate`)."""
        return [r for fe in self.features for r in fe.readouts]


################################################################################
# Speed: the string regexes in one pass over all strings (added on top of thrember)
################################################################################


# NOTE: StringExtractor.raw_features searches every string with every regex through `re.search(pattern, string)`, about
# 76 calls per string (590,000 for a 2 MB file), most of whose time is the `re` module's cache lookup; it was about 60%
# of an extraction. `_strings_raw_features` computes the same dictionary with one `finditer` per regex over the strings
# joined by newlines, then counts the distinct strings that contain a match. This is exact, not approximate: strings
# are runs of 0x20-0x7f, so they contain no newline; no regex can match a newline (no `\s`, `.`, or negated class can
# reach across, and `.` excludes it); and `\b` sees the newline as a non-word character, exactly like the string's end.
# The original method is kept unchanged above (this file only adds to thrember) and replaced here; tests compare the
# two on real files.
def _strings_raw_features(self: StringExtractor, bytez: bytes, pe: Optional[pefile.PE]) -> dict:  # type: ignore[type-arg]
    """StringExtractor.raw_features, with the regex counts computed in one pass per regex (see the NOTE above)."""
    allstrings = self._allstrings.findall(bytez)
    allstrings_ascii = [s.decode() for s in allstrings]
    if allstrings:
        string_lengths = [len(s) for s in allstrings]
        avlength = sum(string_lengths) / len(string_lengths)
        # The same counts as the original's per-character list, without the Python loop.
        as_shifted_string = np.frombuffer(b"".join(allstrings), dtype=np.uint8) - np.uint8(0x20)
        c = np.bincount(as_shifted_string, minlength=96)
        csum = c.sum()
        p = c.astype(np.float32) / csum
        wh = np.where(c)[0]
        H = np.sum(-p[wh] * np.log2(p[wh]))
    else:
        avlength = 0
        c = np.zeros((96,), dtype=np.float32)
        H = 0
        csum = 0

    string_counts = {}
    if allstrings_ascii:
        text = "\n".join(allstrings_ascii)
        # Where each string starts in `text`; a match belongs to the last string starting at or before it.
        starts = np.cumsum([0] + [len(s) + 1 for s in allstrings_ascii[:-1]])
        for k, r in self._regexes.items():
            positions = [m.start() for m in r.finditer(text)]
            if positions:
                string_counts[k] = int(np.unique(np.searchsorted(starts, positions, side="right") - 1).size)
    string_counts = OrderedDict(sorted(string_counts.items()))

    return {
        "numstrings": len(allstrings),
        "avlength": avlength,
        "printabledist": c.tolist(),
        "printables": int(csum),
        "entropy": float(H),
        "string_counts": string_counts,
    }


_strings_raw_features_original = StringExtractor.raw_features
StringExtractor.raw_features = _strings_raw_features  # type: ignore[method-assign]



################################################################################
# Speed: byte counts with numpy, for thrember's and pefile's entropies (added on top of thrember)
################################################################################


# NOTE: thrember (the file entropy in GeneralFileInfo, the overlay entropy in SectionInfo) and pefile (a check for a
# dominant byte value on every parse, and section entropies) count bytes with `collections.Counter`, a Python-level
# loop over every byte: about 60 ms for a 4 MB file, four times per ablated file in the faithfulness experiments (two
# counts in thrember; one parse in the extractor and one in ablation.verify), about half the cost of a query.
# `byte_counter` computes the same Counter, the same counts in the same (first-occurrence) order, with numpy, so every
# float sum over it, and every warning pefile appends while iterating over it, is unchanged. It replaces the name
# `Counter` in this module (whose only uses are those two counts) and in pefile, at import; the original lines of both
# stay unchanged. Tests compare it with collections.Counter and the patched extraction with thrember's on real files.
_COUNTER = Counter
_BYTE_COUNTER_CHUNK = 1 << 16


def byte_counter(data: object) -> Counter[int]:
    """collections.Counter(data), computed with numpy when `data` is bytes or a bytearray (see the NOTE above)."""
    if not isinstance(data, (bytes, bytearray)):
        return _COUNTER(data)  # type: ignore[call-overload,no-any-return]
    a = np.frombuffer(data, dtype=np.uint8)
    counts = np.bincount(a, minlength=256)
    present = int(np.count_nonzero(counts))
    # The first position of each byte value, chunk by chunk; usually every value has appeared within the first chunk.
    first: dict[int, int] = {}
    for lo in range(0, a.size, _BYTE_COUNTER_CHUNK):
        if len(first) == present:
            break
        values, index = np.unique(a[lo:lo + _BYTE_COUNTER_CHUNK], return_index=True)
        for v, i in zip(values.tolist(), index.tolist()):
            first.setdefault(v, lo + i)
    return _COUNTER({v: int(counts[v]) for v in sorted(first, key=first.__getitem__)})


Counter = byte_counter  # type: ignore[misc,assignment]
pefile.Counter = byte_counter  # type: ignore[attr-defined]
