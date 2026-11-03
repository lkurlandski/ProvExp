"""
The expert feature set of Gimenez, Sivaprasad & Fritz, "Certifiably robust malware detectors by design" (arXiv
2508.10038): 40 static features chosen by hand so that the attacker's additions can only raise them, for the
expert-set row of Table A1 (docs/direction-A-expert-set.md).

Their extractor (`static_features_extraction.py:get_features` in their repository, read 2026-10-27) is built on LIEF;
this one re-implements it on pefile, the parser of every other row, so that the row shares the parse. Where the two
parsers differ, the pefile reading closest to their intent is taken:
    library counts         the functions of each import descriptor (LIEF `len(lib.entries)`, pefile `entry.imports`)
    nb_imported_functions  the imports by name, as LIEF's `imported_functions` lists them (repeats included, imports
                           by ordinal left out; LIEF also names a few ordinals from its own tables, which we do not)
    keyword counts         those names containing the keyword, case-sensitive
    modified_dos_stub      the bytes from the end of the DOS header (64) to e_lfanew against their fixed stub (which
                           ends in one specific Rich header). NOTE: their code compares LIEF's `dos_stub` with a list;
                           the LIEF in our env returns a memoryview, so there the comparison is always unequal and the
                           feature is constant 1. We compare bytes, as intended.
    has_resources          pefile parsed a resource directory
    no_sig                 no Authenticode SignedData parses (signify, as thrember's authenticode group)
    sections               names up to the first NUL, compared case-sensitively; size is SizeOfRawData, and entropy
                           is over the raw data up to the virtual size (LIEF's `content`; all of it if that is 0)
On the 45 test files, every feature equals theirs (their code run through LIEF, with `accumulate=False`) except where
the parsers disagree: pefile fails on one file LIEF parses, misses a resource directory on one and nine imports on
another, and LIEF names one ordinal import on two.

Their code *assigns* rather than accumulates per name in two places, the same kind of quirk as thrember's duplicate-DLL
import overwrite (docs/upstream-issues.md): a second import descriptor for a watched library replaces its count, and a
second section with a watched name replaces that name's size and entropy x size. Both are edits in M_add that lower a
feature the set constrains to increase. By default (`accumulate=True`) the counts are summed per library and per
section name; `accumulate=False` keeps their behavior, for the tests and the upstream note.

A file pefile cannot parse gets the zero vector (their extractor raises; the feature store keeps the row).
"""

from __future__ import annotations

import io
from typing import Any
from typing import Optional

import numpy as np
import pefile
import signify.exceptions
from signify.authenticode import SignedPEFile

from provexp.featuresets.ember2024.features import FeatureType
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import clipped
from provexp.featuresets.ember2024.features import directory_locating
from provexp.featuresets.ember2024.features import entropy_H
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import rva_string_range
from provexp.featuresets.ember2024.features import section_locating
from provexp.featuresets.ember2024.features import structure_range
from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Opaque
from provexp.items import Range
from provexp.items import Readout
from provexp.items import Term

__all__ = [
    "DEFAULT_DOS_STUB",
    "KEYWORDS",
    "SECTIONS",
    "WATCHED_LIBRARIES",
    "ExpertFeatureExtractor",
    "ExpertFeatures",
]


################################################################################
# Their constants
################################################################################


WATCHED_LIBRARIES = (
    "kernel32.dll", "comctl32.dll", "gdi32.dll", "shell32.dll", "user32.dll", "winmm.dll", "advapi32.dll",
    "wininet.dll", "ole32.dll", "mscoree.dll", "gdiplus.dll", "oleaut32.dll", "msvbvm50.dll", "ntdll.dll", "urlmon.dll",
)
KEYWORDS = ("Get", "Set", "File", "Console", "Thread", "Process", "Delete", "Write", "System")
SECTIONS = (".text", ".data", ".rsrc", ".rdata")
DEFAULT_DOS_STUB = bytes([
    14, 31, 186, 14, 0, 180, 9, 205, 33, 184, 1, 76, 205, 33, 84, 104, 105, 115, 32, 112, 114, 111, 103, 114, 97, 109,
    32, 99, 97, 110, 110, 111, 116, 32, 98, 101, 32, 114, 117, 110, 32, 105, 110, 32, 68, 79, 83, 32, 109, 111, 100,
    101, 46, 13, 13, 10, 36, 0, 0, 0, 0, 0, 0, 0, 219, 95, 34, 128, 159, 62, 76, 211, 159, 62, 76, 211, 159, 62, 76,
    211, 34, 113, 218, 211, 158, 62, 76, 211, 129, 108, 217, 211, 130, 62, 76, 211, 129, 108, 207, 211, 23, 62, 76, 211,
    184, 248, 55, 211, 156, 62, 76, 211, 159, 62, 77, 211, 78, 62, 76, 211, 129, 108, 200, 211, 160, 62, 76, 211, 129,
    108, 216, 211, 158, 62, 76, 211, 129, 108, 221, 211, 158, 62, 76, 211, 82, 105, 99, 104, 159, 62, 76, 211, 0, 0, 0,
    0, 0, 0, 0, 0,
])
DOS_HEADER_SIZE = 64


################################################################################
# The feature type
################################################################################


def _names() -> list[str]:
    """Their feature names, in their order (the insertion order of their dictionary)."""
    names = list(WATCHED_LIBRARIES) + ["nb_imports", "nb_imported_functions"]
    names += [f"{k}_imported_functions" for k in KEYWORDS]
    names += ["modified_dos_stub", "has_resources", "no_sig", "unknown_sections", "info_unknown_sections"]
    for s in SECTIONS:
        names += [f"{s}_info", f"{s}-size"]
    return names + ["nb_sections"]


def _signed(bytez: bytes) -> bool:
    """Whether at least one Authenticode SignedData parses."""
    try:
        for _ in SignedPEFile(io.BytesIO(bytez)).iter_signed_datas():
            return True
    except (signify.exceptions.SignifyError, ValueError, KeyError, IndexError):
        return False
    return False


class ExpertFeatures(FeatureType):
    """Gimenez et al.'s 40 features, on pefile (see the module docstring)."""

    name = "expert"
    dim = 40

    def __init__(self, accumulate: bool = True) -> None:
        """
        Args:
            accumulate: Sum per library and per section name (the quirk fixed); False assigns, as their code does.
        """
        super(FeatureType, self).__init__()
        self.accumulate = accumulate

    @property
    def feature_names(self) -> list[str]:
        return _names()

    def raw_features(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> dict[str, float]:
        f: dict[str, float] = {n: 0.0 for n in _names()}
        if pe is None:
            return f

        descriptors = list(getattr(pe, "DIRECTORY_ENTRY_IMPORT", []))
        for entry in descriptors:
            library = entry.dll.decode("latin-1").lower() if entry.dll else ""
            if library in WATCHED_LIBRARIES:
                f[library] = (f[library] if self.accumulate else 0.0) + len(entry.imports)
        f["nb_imports"] = len(descriptors)
        names = [imp.name.decode("latin-1") for entry in descriptors for imp in entry.imports if imp.name]
        f["nb_imported_functions"] = len(names)
        for k in KEYWORDS:
            f[f"{k}_imported_functions"] = sum(k in name for name in names)

        stub = bytez[DOS_HEADER_SIZE:max(pe.DOS_HEADER.e_lfanew, DOS_HEADER_SIZE)]
        f["modified_dos_stub"] = float(stub != DEFAULT_DOS_STUB)
        f["has_resources"] = float(hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"))
        f["no_sig"] = float(not _signed(bytez))

        seen: set[str] = set()
        for section in pe.sections:
            name = section.Name.split(b"\x00")[0].decode("latin-1")
            size = float(section.SizeOfRawData)
            content = section.get_data(length=min(section.SizeOfRawData, section.Misc_VirtualSize or section.SizeOfRawData))
            info = entropy_H(content) * size
            if name in SECTIONS:
                if self.accumulate and name in seen:
                    f[f"{name}_info"] += info
                    f[f"{name}-size"] += size
                else:
                    f[f"{name}_info"] = info
                    f[f"{name}-size"] = size
                seen.add(name)
            else:
                f["info_unknown_sections"] += info
                f["unknown_sections"] += 1
        f["nb_sections"] = len(pe.sections)
        return f

    def process_raw_features(self, raw_obj: dict[str, Any]) -> np.ndarray:
        return np.asarray([raw_obj[n] for n in _names()], dtype=np.float32)

    ############################################################################
    # The item layer (docs/item-layer-design.md): items, readouts, recognizer, so the derivation (C4) and the C1
    # engine read the expert set the way they read the instrumented EMBER extractor. `evaluate(items, readouts)` must
    # reproduce `feature_vector` exactly (check G1). The two quirks live in the terms: with `accumulate` the per-library
    # and per-name contributions are additive `add` terms (sound, up under additions); `accumulate=False` makes them
    # `slot` terms (assign), which the derivation reads as two-sided -- the engine finding the quirk.
    ############################################################################

    def _families(self) -> dict[str, int]:
        return {
            "expert:lib_count": len(WATCHED_LIBRARIES),
            "expert:nb_imports": 1,
            "expert:nb_functions": 1,
            "expert:keywords": len(KEYWORDS),
            "expert:no_sig": 1,
            "expert:unknown_count": 1,
            "expert:unknown_info": 1,
            "expert:named": 2 * len(SECTIONS),
            "expert:nb_sections": 1,
        }

    def items(self, bytez: bytes, pe: Optional[pefile.PE] = None) -> ItemTable:
        n = len(bytez)
        families = self._families()
        if pe is None:
            return ItemTable(n, families, [])
        items: list[Item] = []

        # Imports: one item per descriptor. nb_imports counts descriptors; a watched library's count, the named-import
        # count, and the keyword counts are the descriptor's contributions (additive, or assigned per library when the
        # quirk is kept). pefile reads every descriptor through the import directory, which locates them.
        located = directory_locating(pe, 1)
        for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            library = entry.dll.decode("latin-1").lower() if entry.dll else ""
            dll_range = clipped(n, [rva_string_range(pe, entry.struct.Name, len(entry.dll))])
            desc_range = clipped(n, [structure_range(entry.struct)])
            ranges = desc_range + dll_range
            names = [imp.name.decode("latin-1") for imp in entry.imports if imp.name]
            watched = library in WATCHED_LIBRARIES
            terms: list[Term] = [Term("count", "expert:nb_imports", index=0, ranges=desc_range)]
            if watched:
                terms.append(Term("add", "expert:lib_count", index=WATCHED_LIBRARIES.index(library),
                                  value=float(len(entry.imports)), attr="lib_count", ranges=ranges))
            if names:
                terms.append(Term("add", "expert:nb_functions", index=0, value=float(len(names)), ranges=ranges))
            for j, k in enumerate(KEYWORDS):
                hits = sum(k in name for name in names)
                if hits:
                    terms.append(Term("add", "expert:keywords", index=j, value=float(hits), ranges=ranges))
            # The quirk: assigning per library (`accumulate=False`) makes a watched library's count depend on the other
            # descriptors (a later one erases an earlier one's count), so the item is not local (A2). The C4 derivation
            # then reads its entries as two-sided -- the engine finding the quirk. With it patched the item is local.
            items.append(Item("import_desc", terms=tuple(terms), attrs={"library": library},
                              local=self.accumulate or not watched, locating=located))

        # The DOS stub and resource directory: one item each when the file parses, so that `modified_dos_stub` and
        # `has_resources` match `raw_features` (both 0 for an unparsed file, the Opaque default; a parsed file with the
        # default stub or no resources is also 0, so there is no conflict). Their attribute is the feature's value, read
        # by `Opaque`. The DOS region overwrite rewrites the stub, so `modified_dos_stub` is two-sided (its hole).
        stub_region = clipped(n, [(DOS_HEADER_SIZE, max(pe.DOS_HEADER.e_lfanew, DOS_HEADER_SIZE))])
        stub = bytez[DOS_HEADER_SIZE:max(pe.DOS_HEADER.e_lfanew, DOS_HEADER_SIZE)]
        items.append(Item("dos_stub", attrs={"modified": float(stub != DEFAULT_DOS_STUB)},
                          attr_ranges={"modified": (stub_region,)} if stub_region else {},
                          locating=clipped(n, [field_range(pe.DOS_HEADER, "e_lfanew")])))
        items.append(Item("resource", attrs={"present": float(hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"))},
                          locating=directory_locating(pe, 2)))
        # `no_sig` is 1 exactly when the file parses but carries no Authenticode signature: a marker item present then,
        # read by Identity, so an unparsed file is 0 (no item). Removing the signature adds the marker (no_sig rises);
        # no M_full operation adds a signature, so the derived direction is up (sound and tight), not a hole.
        if not _signed(bytez):
            items.append(Item("no_sig", terms=(Term("count", "expert:no_sig", index=0),)))

        # Sections: a named section (`.text`/`.data`/`.rsrc`/`.rdata`) contributes its info (entropy x raw size) and raw
        # size to that name's entries; any other section contributes to the unknown count and info. Every section counts
        # toward `nb_sections`. The name decides which entries a section writes, and lives in the section table, which is
        # locating, so renaming is a declared structural edit (the catalogue states it).
        sect_located = section_locating(pe)
        for section in pe.sections:
            name = section.Name.split(b"\x00")[0].decode("latin-1")
            size = float(section.SizeOfRawData)
            content = section.get_data(length=min(section.SizeOfRawData, section.Misc_VirtualSize or section.SizeOfRawData))
            info = entropy_H(content) * size
            data_range = clipped(n, [(section.PointerToRawData, section.PointerToRawData + len(content))])
            name_range = clipped(n, [field_range(section, "Name")])
            size_range = clipped(n, [field_range(section, "SizeOfRawData")])
            table_range = clipped(n, [structure_range(section)])
            named = name in SECTIONS
            terms = [Term("count", "expert:nb_sections", index=0, ranges=table_range)]
            if named:
                i = SECTIONS.index(name)
                terms.append(Term("add", "expert:named", index=2 * i, value=info, attr="info", ranges=name_range + data_range))
                terms.append(Term("add", "expert:named", index=2 * i + 1, value=size, attr="size", ranges=name_range + size_range))
            else:
                terms.append(Term("count", "expert:unknown_count", index=0, ranges=table_range))
                terms.append(Term("add", "expert:unknown_info", index=0, value=info, attr="info", ranges=name_range + data_range))
            # The quirk, as for imports: assigning per section name (`accumulate=False`) makes a named section's info and
            # size depend on the others, so the item is not local; patched, it is.
            items.append(Item("section", terms=tuple(terms),
                              attrs={"name": name, "size": size, "info": info, "data": data_range},
                              attr_ranges={"info": (data_range if data_range else size_range,)},
                              local=self.accumulate or not named, locating=sect_located))
        return ItemTable(n, families, items)

    @property
    def readouts(self) -> list[Readout]:
        return [
            Identity("expert:lib_count", 0, len(WATCHED_LIBRARIES)),
            Identity("expert:nb_imports", 0, 1),
            Identity("expert:nb_functions", 0, 1),
            Identity("expert:keywords", 0, len(KEYWORDS)),
            Opaque("dos_stub", ("modified",), (0.0,), ranges=((0.0, 1.0),)),
            Opaque("resource", ("present",), (0.0,), ranges=((0.0, 1.0),)),
            Identity("expert:no_sig", 0, 1),
            Identity("expert:unknown_count", 0, 1),
            Identity("expert:unknown_info", 0, 1),
            Identity("expert:named", 0, 2 * len(SECTIONS)),
            Identity("expert:nb_sections", 0, 1),
        ]


class ExpertFeatureExtractor(PEFeatureExtractor):
    """The expert set alone, on thrember's parse (`PEFeatureExtractor.raw_features`)."""

    def __init__(self, accumulate: bool = True) -> None:
        super().__init__()
        self.features = [ExpertFeatures(accumulate)]
        self.dim = sum(fe.dim for fe in self.features)
