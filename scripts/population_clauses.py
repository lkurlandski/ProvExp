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

import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.population import clauses


################################################################################
# The clauses
################################################################################


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
