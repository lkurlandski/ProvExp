"""
Which clause of the population check each file fails (PLAN.md, decision 8 (iv); Section 4.4's figures).

The population (`catalogue.precondition`) is the complete PE files with a plain layout. This script evaluates its
clauses one by one on every file of a list, so that the files outside it can be told apart:
    - incomplete: an item, a data directory, or a section is located (at least in part) past the end of the file;
    - unusual layout: one of `catalogue.plain_layout`'s clauses fails (a section's virtual range beyond SizeOfImage,
      SizeOfImage larger than the sections need, the PE header inside the DOS header, a section's raw data inside the
      headers, the overlay starting at a data directory's extent).
A file can fail both; it counts as incomplete then. Files are read one shard at a time (each shard of the SimpleDB once).

Outputs, in `{outdir}/`:
    files.parquet   one row per file: each clause, the item groups and data directories located past the end, the
                    file's length and the furthest section end, the population check, the category
    report.json     the categories by truncation (our copy's 4,000,000-byte cut) and label

Usage:
    PYTHONHASHSEED=0 python scripts/population_clauses.py --outdir artifacts/experiments/population_clauses/2000
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import defaultdict
import json
from multiprocessing import get_context
from pathlib import Path
import sys
from typing import Any
import warnings

import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.catalogue import DOS_HEADER_SIZE
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import precondition
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.features import section_data_range


LAYOUT = ["vrange_beyond_image", "image_too_large", "lfanew_in_dos", "section_in_headers", "overlay_at_directory"]
PAST_END = ["item_past_end", "directory_past_end", "section_past_end"]


################################################################################
# The clauses
################################################################################

def _align_up(x: int, a: int) -> int:
    return (x + a - 1) // a * a if a else x


def clauses(z: bytes, extractor: PEFeatureExtractor) -> dict[str, Any]:
    """
    Each clause of `catalogue.precondition` on one file, mirroring `plain_layout` and `precondition` clause by clause.

    Args:
        z: The file's bytes.
        extractor: The instrumented extractor (for the item table's locating ranges).

    Returns:
        One row: a bool per clause (True: the clause fails), context, and the category.
    """
    try:
        pe = pefile.PE(data=z)
    except (pefile.PEFormatError, AttributeError) as e:
        return {"parses": False, "error": repr(e), "category": "not parsing", "in_population": False}
    table = extractor.item_table(z)
    oh = pe.OPTIONAL_HEADER
    sa = oh.SectionAlignment or 0x1000
    sections = list(pe.sections)
    n = len(pe.__data__)
    row: dict[str, Any] = {"parses": True, "error": None, "length": n}
    row["vrange_beyond_image"] = any(
        s.VirtualAddress + (s.Misc_VirtualSize or s.SizeOfRawData) > oh.SizeOfImage for s in sections)
    need = max([s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData) for s in sections] + [oh.SizeOfHeaders])
    row["image_too_large"] = oh.SizeOfImage > _align_up(need, sa)
    e_lfanew = pe.DOS_HEADER.e_lfanew
    row["lfanew_in_dos"] = e_lfanew < DOS_HEADER_SIZE
    row["section_in_headers"] = any(s.SizeOfRawData and section_data_range(s)[0] < e_lfanew for s in sections)
    overlay = pe.get_overlay_data_start_offset()
    row["overlay_at_directory"] = False
    if overlay is not None:
        ends = [s.PointerToRawData + s.SizeOfRawData for s in sections if s.PointerToRawData + s.SizeOfRawData <= n]
        row["overlay_at_directory"] = overlay > max(ends + [oh.get_file_offset() + pe.FILE_HEADER.SizeOfOptionalHeader])
    groups = sorted({item.group for item in table.items for _, hi in item.locating if hi > n})
    row["item_past_end"] = bool(groups)
    row["groups_past_end"] = ",".join(groups)
    directories = []
    for i, d in enumerate(oh.DATA_DIRECTORY):
        if d.VirtualAddress and d.Size:
            data = ((d.VirtualAddress, d.VirtualAddress + d.Size),) if i == SECURITY_ENTRY else rva_ranges(pe, d.VirtualAddress, d.Size)
            if any(hi > n for _, hi in data):
                directories.append(str(d.name).replace("IMAGE_DIRECTORY_ENTRY_", ""))
    row["directory_past_end"] = bool(directories)
    row["directories_past_end"] = ",".join(directories)
    row["section_past_end"] = any(s.PointerToRawData + s.SizeOfRawData > n for s in sections)
    row["max_section_end"] = max([s.PointerToRawData + s.SizeOfRawData for s in sections] + [0])
    row["in_population"] = precondition(pe, table)
    incomplete = any(row[k] for k in PAST_END)
    unusual = any(row[k] for k in LAYOUT)
    if row["in_population"] == (incomplete or unusual):
        raise RuntimeError(f"The clauses disagree with catalogue.precondition ({row}).")
    row["category"] = "population" if row["in_population"] else "incomplete" if incomplete else "unusual layout"
    return row


################################################################################
# Main
################################################################################

def _shard(args: tuple[Path, int, list[str]]) -> list[dict[str, Any]]:
    """The rows of the listed files of one shard."""
    warnings.filterwarnings("ignore")
    db, shard, names = args
    wanted = set(names)
    extractor = merge_import_descriptors(PEFeatureExtractor())
    rows = []
    for sample in SimpleDBIterator(SimpleDB(db, check=False)).iter(shard):
        if sample.name in wanted:
            rows.append({"name": sample.name, **clauses(sample.data, extractor)})
    return rows


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, default=Path("artifacts/explanation_set/ts.parquet"))
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    files = pl.read_parquet(args.files).select("name", "label", "truncated")
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
    if len(rows) != files.height:
        raise RuntimeError(f"Read {len(rows)} of {files.height} files.")

    out = pl.DataFrame(rows, infer_schema_length=None).join(files, on="name").sort("name")
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "files.parquet")
    counts = out.group_by("truncated", "label", "category").len().sort("truncated", "label", "category")
    report = {
        "files": out.height,
        "counts": counts.to_dicts(),
        "below_4mb": {
            "files": int((~out["truncated"]).sum()),
            "by_category": dict(out.filter(~pl.col("truncated"))["category"].value_counts().iter_rows()),
        },
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
