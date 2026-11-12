"""
Which single field writes take a file out of the population (the escape audit; meta-review 2026-11-12, R7 (a)).

The population (`catalogue.precondition`) is closed under the threat model's operations, but not under other edits. This
script applies, to files in the population, one write each of a few header fields that the Windows loader does not use
to map the image (or uses only to reserve memory), and evaluates the population's clauses on the result
(`population_clauses.clauses`). The files are byte strings: nothing is executed. Whether the loader accepts each write
is argued from the PE format documentation, not here.

The writes:
    cert_entry      the certificate table's entry (a file offset, never mapped) made to extend past the end of the file
    debug_entry     the debug directory's entry made to extend past the end (the loader does not read it)
    arch_entry      the reserved architecture entry (index 7, zero by the specification) pointed past the end
    image_size      SizeOfImage raised by one SectionAlignment (more address space reserved, nothing mapped there)
    overlay_entry   the architecture entry pointed at the first 16 bytes of the overlay (files with an overlay)
    raw_size        the last section's SizeOfRawData made to extend past the end (control: the loader reads it)

Outputs, in `{outdir}/`:
    files.parquet   one row per file and write: whether it applied, whether it parses, the clauses it trips, in population
    report.json     per write: files it applied to, files it took out of the population, the clauses tripped

Usage:
    PYTHONHASHSEED=0 python scripts/escape_audit.py --outdir artifacts/experiments/escape_audit/pilot --n 150
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from collections import defaultdict
import json
from multiprocessing import get_context
from pathlib import Path
import sys
from typing import Any
from typing import Callable
from typing import Optional
import warnings

import numpy as np
import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.catalogue import DEBUG_ENTRY
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors

sys.path.insert(0, str(Path(__file__).resolve().parent))
from population_clauses import LAYOUT  # noqa: E402
from population_clauses import PAST_END  # noqa: E402
from population_clauses import clauses  # noqa: E402

__all__ = ["WRITES"]

ARCH_ENTRY = 7


################################################################################
# The writes
################################################################################

def _entry(pe: pefile.PE, i: int, va: int, size: int) -> bytes:
    """The file with data directory entry `i` set to (va, size)."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[i]
    d.VirtualAddress, d.Size = va, size
    return bytes(pe.write())


def cert_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The certificate entry extended (or, if absent, placed) past the end of the file."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[SECURITY_ENTRY]
    if d.VirtualAddress and d.Size:
        return _entry(pe, SECURITY_ENTRY, d.VirtualAddress, d.Size + n)
    return _entry(pe, SECURITY_ENTRY, n, 8)


def debug_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The debug entry extended (or, if absent, placed) past the end of the file."""
    d = pe.OPTIONAL_HEADER.DATA_DIRECTORY[DEBUG_ENTRY]
    if d.VirtualAddress and d.Size:
        return _entry(pe, DEBUG_ENTRY, d.VirtualAddress, d.Size + 2 * n)
    return _entry(pe, DEBUG_ENTRY, max(pe.OPTIONAL_HEADER.SizeOfImage, n), 28)


def arch_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The reserved architecture entry pointed past the end of the file and past the image."""
    if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= ARCH_ENTRY:
        return None
    return _entry(pe, ARCH_ENTRY, max(pe.OPTIONAL_HEADER.SizeOfImage, n), 8)


def image_size(pe: pefile.PE, n: int) -> Optional[bytes]:
    """SizeOfImage raised by one SectionAlignment."""
    pe.OPTIONAL_HEADER.SizeOfImage += pe.OPTIONAL_HEADER.SectionAlignment or 0x1000
    return bytes(pe.write())


def overlay_entry(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The architecture entry pointed at the overlay's first 16 bytes (as an address in no section)."""
    start = pe.get_overlay_data_start_offset()
    if start is None or n - start < 16 or len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= ARCH_ENTRY:
        return None
    if any(s.VirtualAddress <= start < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in pe.sections):
        return None
    return _entry(pe, ARCH_ENTRY, start, 16)


def raw_size(pe: pefile.PE, n: int) -> Optional[bytes]:
    """The section whose raw data ends last made to extend past the end of the file (control)."""
    if not pe.sections:
        return None
    s = max(pe.sections, key=lambda s: s.PointerToRawData + s.SizeOfRawData)
    fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200
    s.SizeOfRawData += ((n - (s.PointerToRawData + s.SizeOfRawData)) // fa + 1) * fa
    return bytes(pe.write())


WRITES: dict[str, Callable[[pefile.PE, int], Optional[bytes]]] = {
    "cert_entry": cert_entry,
    "debug_entry": debug_entry,
    "arch_entry": arch_entry,
    "image_size": image_size,
    "overlay_entry": overlay_entry,
    "raw_size": raw_size,
}


################################################################################
# Main
################################################################################

def audit(z: bytes, extractor: PEFeatureExtractor) -> list[dict[str, Any]]:
    """One row per write: whether it applied and which clauses the written file trips."""
    rows = []
    for name, write in WRITES.items():
        try:
            pe = pefile.PE(data=z)
            out = write(pe, len(z))
        except Exception as e:  # noqa: BLE001
            rows.append({"write": name, "applied": False, "error": repr(e)})
            continue
        if out is None:
            rows.append({"write": name, "applied": False, "error": None})
            continue
        if len(out) != len(z) or sum(a != b for a, b in zip(out, z)) > 8:
            raise RuntimeError(f"{name} wrote more than one field ({len(out)} vs {len(z)} bytes).")
        c = clauses(out, extractor)
        tripped = [k for k in LAYOUT + PAST_END if c.get(k)]
        rows.append({"write": name, "applied": True, "error": None, "parses": c["parses"],
                     "in_population": c["in_population"], "tripped": ",".join(tripped)})
    return rows


def _shard(args: tuple[Path, int, list[str]]) -> list[dict[str, Any]]:
    """The rows of the listed files of one shard."""
    warnings.filterwarnings("ignore")
    db, shard, names = args
    wanted = set(names)
    extractor = merge_import_descriptors(PEFeatureExtractor())
    rows = []
    for sample in SimpleDBIterator(SimpleDB(db, check=False)).iter(shard):
        if sample.name in wanted:
            rows += [{"name": sample.name, **r} for r in audit(sample.data, extractor)]
    return rows


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--clauses", type=Path, default=Path("artifacts/experiments/population_clauses/2000/files.parquet"))
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--n", type=int, default=150, help="Files sampled from the population (below 4 MB).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    pop = pl.read_parquet(args.clauses).filter(pl.col("in_population"), ~pl.col("truncated")).sort("name")
    pick = np.random.default_rng(args.seed).permutation(pop.height)[: args.n]
    files = pop[pick.tolist()].select("name", "label")
    db = SimpleDB(args.db, check=False)
    index = db.get_name_to_idx_map()
    by_shard: dict[int, list[str]] = defaultdict(list)
    for name in files["name"].to_list():
        by_shard[db.get_shardix_from_idx(index[name])].append(name)
    print(f"{files.height} files in {len(by_shard)} shards, {args.workers} workers", flush=True)

    rows: list[dict[str, Any]] = []
    tasks = [(args.db, shard, names) for shard, names in sorted(by_shard.items())]
    with get_context("forkserver").Pool(args.workers) as pool:
        for r in tqdm(pool.imap_unordered(_shard, tasks), total=len(tasks), mininterval=30, file=sys.stdout):
            rows += r

    out = pl.DataFrame(rows, infer_schema_length=None).join(files, on="name").sort("name", "write")
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "files.parquet")
    report: dict[str, Any] = {"files": files.height, "writes": {}}
    for name in WRITES:
        w = out.filter(pl.col("write") == name, pl.col("applied"))
        left = w.filter(~pl.col("in_population"))
        report["writes"][name] = {
            "applied": w.height,
            "left_population": left.height,
            "left_by_label": dict(left["label"].value_counts().iter_rows()) if left.height else {},
            "tripped": dict(Counter(t for ts in left["tripped"].to_list() for t in ts.split(",") if t)),
        }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
