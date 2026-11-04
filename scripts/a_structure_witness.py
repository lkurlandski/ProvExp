"""
Witnesses for the remaining class-1 cases of G3 (docs/item-layer-design.md, "Anticipated disagreements" and
"structures past the end of the file"): edits under which the hand rules call a feature fixed (or one-sided), but the
extractor moves it.

Four cases, each a concrete edit on every file it applies to, followed by re-extraction:
    entry     add an executable section (`sec`, via LIEF as scripts/a1_adaptive.py) to a file whose entry point lies in
              no section: the entry section is then the first executable one, and the added section can become it
              (`section:entry_name_hash_*`)
    rich_ext  extend the DOS stub (`ext`, secml-malware's shift_pe_header_by) of a file without a Rich header and write
              a donor's Rich header into the gap only: pefile searches for "Rich" in [0x80, optional header)
              (`richheader:*`)
    rich_hdr  on a file without a Rich header, write "Rich" into the COFF TimeDateStamp and a key into
              PointerToSymbolTable (`hdr`, two loader-ignored fields inside the same search range); pefile accepts the
              marker whatever precedes it (a malformed header is only a warning)
    exports   append zeros up to an export directory that lies past the end of the file, then a minimal directory
              naming one export (`app`; `exports:*`)
    relocs    the same for a relocation directory past the end: one block of the declared size (`app`;
              `datadirectories:has_relocs`)

The donors of rich_ext are files of the same list that have a Rich header (smallest first, up to --donors).

Outputs, in `{outdir}/`:
    witnesses.parquet   one row per (case, file, donor): bytes the edit adds, whether the edited file parses, and the
                        case's features that changed (with before and after values)
    report.json         per case: files it applies to, witnesses, witnesses where a feature changed, those features

Usage:
    PYTHONHASHSEED=0 python scripts/a_structure_witness.py --outdir artifacts/experiments/a_structure_witness
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Callable
import json
from multiprocessing import get_context
from pathlib import Path
import struct
import sys
from typing import Any
from typing import Optional
import warnings

import numpy as np
import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import add_section  # noqa: E402

__all__ = [
    "rich_block",
    "edit_entry",
    "edit_rich_ext",
    "edit_rich_hdr",
    "edit_exports",
    "edit_relocs",
    "main",
]

warnings.filterwarnings("ignore", category=SyntaxWarning)

EXPORT, BASERELOC = 0, 5
SCN_MEM_EXECUTE = 0x20000000
RICH_KEY = 0x5EED1E55
# The prefixes of each case's features.
PREFIXES = {
    "entry": ("section:entry_name_hash_",),
    "rich_ext": ("richheader:",),
    "rich_hdr": ("richheader:",),
    "exports": ("exports:",),
    "relocs": ("datadirectories:has_relocs",),
}


################################################################################
# Helpers
################################################################################


def _parse(z: bytes, fast: bool = True) -> Optional[pefile.PE]:
    """The file as pefile reads it, or None."""
    try:
        return pefile.PE(data=z, fast_load=fast)
    except (pefile.PEFormatError, AttributeError):
        return None


def rich_block(z: bytes) -> Optional[bytes]:
    """The file's Rich header as pefile reads it, from 0x80 through the key after "Rich", or None if it has none."""
    pe = _parse(z)
    if pe is None or pe.parse_rich_header() is None:
        return None
    i = z.find(b"Rich", 0x80, pe.OPTIONAL_HEADER.get_file_offset())
    return z[0x80:i + 8]


def _past_end(pe: pefile.PE, n: int, index: int) -> Optional[tuple[int, int, int]]:
    """(file offset, size, RVA) of data directory `index` if it lies past the end of the file, inside one section."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    if len(d) <= index or not d[index].VirtualAddress or not d[index].Size:
        return None
    rva, size = int(d[index].VirtualAddress), int(d[index].Size)
    s = pe.get_section_by_rva(rva)
    if s is None or pe.get_section_by_rva(rva + size - 1) is not s:
        return None
    offset = int(pe.get_offset_from_rva(rva))
    return (offset, size, rva) if offset >= n else None


################################################################################
# The edits (each returns the edited file, or None if the case does not apply)
################################################################################


def edit_entry(z: bytes, donor: Optional[bytes]) -> Optional[bytes]:
    """Add an executable section if the entry point lies in no section and no section is executable."""
    pe = _parse(z)
    if pe is None:
        return None
    aoep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    if any(s.contains_rva(aoep) for s in pe.sections) or any(s.Characteristics & SCN_MEM_EXECUTE for s in pe.sections):
        return None
    return add_section(z, ".wit", bytes(range(256)) * 16, code=True)


def edit_rich_ext(z: bytes, donor: Optional[bytes]) -> Optional[bytes]:
    """Extend the DOS stub of a file without a Rich header and write `donor` (a Rich block) into the gap only."""
    from secml_malware.utils.pe_operations import shift_pe_header_by

    pe = _parse(z)
    if pe is None or donor is None or pe.parse_rich_header() is not None:
        return None
    e_lfanew = int(pe.DOS_HEADER.e_lfanew)
    # The gap starts at the old PE header; the marker must be dword-aligned relative to 0x80.
    start = max(0x80, e_lfanew)
    start += (-(start - 0x80)) % 4
    x, _ = shift_pe_header_by(bytearray(z), start - e_lfanew + len(donor))
    x = bytearray(x)
    end = struct.unpack_from("<I", x, 0x3C)[0]
    if start + len(donor) > end:
        raise RuntimeError(f"The gap [{e_lfanew}, {end}) cannot hold the donor at {start}.")
    x[start:start + len(donor)] = donor
    return bytes(x)


def edit_rich_hdr(z: bytes, donor: Optional[bytes]) -> Optional[bytes]:
    """On a file without a Rich header, write "Rich" into TimeDateStamp and a key into PointerToSymbolTable."""
    pe = _parse(z)
    if pe is None or pe.parse_rich_header() is not None:
        return None
    offset = pe.FILE_HEADER.get_file_offset() + 4  # TimeDateStamp; PointerToSymbolTable follows
    if offset < 0x80 or (offset - 0x80) % 4:
        return None
    x = bytearray(z)
    x[offset:offset + 8] = b"Rich" + struct.pack("<I", RICH_KEY)
    return bytes(x)


def edit_exports(z: bytes, donor: Optional[bytes]) -> Optional[bytes]:
    """Complete an export directory past the end: one function exported by name ("witness")."""
    pe = _parse(z)
    if pe is None:
        return None
    entry = _past_end(pe, len(z), EXPORT)
    if entry is None:
        return None
    offset, size, rva = entry
    name = b"witness\x00"
    if size < 52 + len(name):
        return None
    # IMAGE_EXPORT_DIRECTORY (40 bytes), then the function, name, and ordinal arrays and the name, all in the directory.
    directory = struct.pack("<IIHHIIIIIII", 0, 0, 0, 0, rva + 52, 1, 1, 1, rva + 40, rva + 44, rva + 48)
    table = directory + struct.pack("<IIHH", rva, rva + 52, 0, 0) + name
    return z + bytes(offset - len(z)) + table + bytes(size - len(table))


def edit_relocs(z: bytes, donor: Optional[bytes]) -> Optional[bytes]:
    """Complete a relocation directory past the end: one block of the declared size, for the first section's page."""
    pe = _parse(z)
    if pe is None or not pe.sections:
        return None
    entry = _past_end(pe, len(z), BASERELOC)
    if entry is None:
        return None
    offset, size, _ = entry
    block = size - size % 2
    if block < 10:
        return None
    # One HIGHLOW entry at the page start; the rest are absolute (padding) entries.
    table = struct.pack("<IIH", int(pe.sections[0].VirtualAddress), block, 3 << 12) + bytes(block - 10)
    return z + bytes(offset - len(z)) + table + bytes(size - block)


EDITS: dict[str, Callable[[bytes, Optional[bytes]], Optional[bytes]]] = {
    "entry": edit_entry,
    "rich_ext": edit_rich_ext,
    "rich_hdr": edit_rich_hdr,
    "exports": edit_exports,
    "relocs": edit_relocs,
}


################################################################################
# Workers
################################################################################


_STATE: dict[str, Any] = {}


def _init_worker(db: Path, cases: list[str], donors: list[tuple[str, bytes]]) -> None:
    """Open the database and build the extractor once per worker."""
    import lief

    lief.logging.disable()
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    extractor = merge_import_descriptors(PEFeatureExtractor())
    names = extractor.feature_names
    _STATE.update(
        reader=SimpleDBReader(SimpleDB(db, check=False)), extractor=extractor, names=names, cases=cases, donors=donors,
        idx={c: [i for i, n in enumerate(names) if n.startswith(PREFIXES[c])] for c in cases},
    )


def _witness_file(name: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Every case on one file: the witness rows, the cases that apply to it, and log lines."""
    extractor, names = _STATE["extractor"], _STATE["names"]
    z = _STATE["reader"].get(name).data
    rows: list[dict[str, Any]] = []
    applies: list[str] = []
    log: list[str] = []
    before: Optional[np.ndarray] = None
    for case in _STATE["cases"]:
        idx = _STATE["idx"][case]
        tried = _STATE["donors"] if case == "rich_ext" else [("", None)]
        for donor, block in tried:
            try:
                edited = EDITS[case](z, block)
            except Exception as e:  # a tool that cannot edit the file is not a witness
                log.append(f"{case} {name[:12]}: edit failed ({type(e).__name__}: {e})")
                continue
            if edited is None:
                break
            if case not in applies:
                applies.append(case)
            if before is None:
                before = np.asarray(extractor.feature_vector(z))
            after = np.asarray(extractor.feature_vector(edited))
            changed = [i for i in idx if after[i] != before[i]]
            rows.append({
                "case": case, "name": name, "donor": donor, "added": len(edited) - len(z),
                "parses": _parse(edited, fast=False) is not None,
                "changed": [names[i] for i in changed],
                "before": [float(before[i]) for i in changed], "after": [float(after[i]) for i in changed],
            })
            log.append(f"{case} {name[:12]}{' + ' + donor[:12] if donor else ''}: "
                       + ", ".join(f"{names[i]} {before[i]:g} -> {after[i]:g}" for i in changed[:4]))
    return rows, applies, log


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, default=Path("artifacts/experiments/e1/seed-0/zeros/files.parquet"))
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--cases", nargs="+", default=list(EDITS), choices=list(EDITS))
    parser.add_argument("--donors", type=int, default=3, help="Donor Rich headers tried per file (rich_ext), smallest first.")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    files = sorted(df["name"].to_list())
    donors: list[tuple[str, bytes]] = []
    if "rich_ext" in args.cases:
        reader = SimpleDBReader(SimpleDB(args.db, check=False))
        donors = sorted(((n, b) for n in files if (b := rich_block(reader.get(n).data)) is not None), key=lambda d: len(d[1]))
    print(f"{len(files)} files, {len(donors)} Rich header donors, {args.workers} workers", flush=True)

    rows: list[dict[str, Any]] = []
    applies = {case: 0 for case in args.cases}
    with get_context("forkserver").Pool(args.workers, initializer=_init_worker,
                                        initargs=(args.db, args.cases, donors[: args.donors])) as pool:
        for r, a, log in tqdm(pool.imap_unordered(_witness_file, files), total=len(files), mininterval=30, file=sys.stdout):
            rows += r
            for case in a:
                applies[case] += 1
            for line in log:
                print(line, flush=True)
    rows.sort(key=lambda r: (args.cases.index(r["case"]), r["name"], r["donor"]))

    report: dict[str, Any] = {}
    for case in args.cases:
        mine = [r for r in rows if r["case"] == case]
        moved = [r for r in mine if r["changed"]]
        report[case] = {
            "files_it_applies_to": applies[case],
            "witnesses": len(mine),
            "witnesses_where_a_feature_changed": len(moved),
            "files_where_a_feature_changed": len({r["name"] for r in moved}),
            "features_that_changed": sorted({f for r in moved for f in r["changed"]}),
            "max_added": max((r["added"] for r in mine), default=0),
        }

    args.outdir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(args.outdir / "witnesses.parquet")
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
