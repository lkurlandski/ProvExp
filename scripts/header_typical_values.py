"""
Compute the most common value of each PE header field in a sample of training files, for level-3 ablation (header
fields replaced by typical values instead of zeros; see provexp.featuresets.ember2024.ablation).

Output: src/provexp/featuresets/ember2024/header_typical_values.json, with, per field key, the most common value (hex),
its count, and the number of values seen. Fields of repeated structures (sections, data directories of one kind) are
pooled.

Usage:
    python scripts/header_typical_values.py --split tr --num_samples 2000 --num_workers 8
"""

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any
import warnings

import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import TYPICAL_VALUES_FILE
from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.data.paths import EMBER2024_DATA


ROOT = Path(__file__).parent.parent


def _init_worker() -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def process_shard(shard: int, positions: list[int], dbdir: Path) -> dict[str, Counter[bytes]]:
    wanted = set(positions)
    counts: dict[str, Counter[bytes]] = {}
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        result = parse(sample.data, fast_load=True)
        if result.status != "ok" or result.pe is None:
            continue
        for field in header_fields(result.pe):
            if 0 <= field.lo < field.hi <= len(sample.data):
                counts.setdefault(field.key, Counter())[sample.data[field.lo:field.hi]] += 1
    return counts


def _star(task: tuple[Any, ...]) -> dict[str, Counter[bytes]]:
    return process_shard(*task)


def main() -> None:
    parser = ArgumentParser(description="Compute the most common value of each PE header field.")
    parser.add_argument("--split", type=str, default="tr")
    parser.add_argument("--num_samples", type=int, default=2000, help="Files, balanced by label.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA)
    parser.add_argument("--output", type=Path, default=TYPICAL_VALUES_FILE)
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    args = parser.parse_args()

    meta = pl.read_parquet(args.features / args.split / "meta.parquet").filter(pl.col("status") == "ok")
    per_label = args.num_samples // 2
    samples = pl.concat([meta.filter(pl.col("label") == lab).sample(per_label, seed=args.seed) for lab in (0, 1)])
    tasks = [(int(shard), group["position"].to_list(), args.db / args.split) for (shard,), group in samples.group_by("shard")]

    counts: dict[str, Counter[bytes]] = {}
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for part in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks)):
            for key, counter in part.items():
                counts.setdefault(key, Counter()).update(counter)

    fields = {}
    for key in sorted(counts):
        value, count = counts[key].most_common(1)[0]
        fields[key] = {"value": value.hex(), "count": count, "total": sum(counts[key].values())}
    table = {"split": args.split, "num_samples": samples.height, "seed": args.seed, "fields": fields}
    args.output.write_text(json.dumps(table, indent=2) + "\n")
    print(f"Wrote {len(fields)} fields to {args.output.as_posix()}.")


if __name__ == "__main__":
    main()
