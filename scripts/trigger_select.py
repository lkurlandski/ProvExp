"""
Choose the fields and values of the struct trigger (docs/experiments/trigger.md) from data statistics alone, never with an
explainer, so that scoring explainers against the trigger is not circular.

Candidates are header fields that the EMBER header features read, that are not layout fields or known to break files,
and that carry no load-bearing meaning for the parser (versions, symbol-table fields). For each candidate, on a sample
of training files balanced by label:
    label dependence    the total variation distance between the field's value distributions in benign and malware
                        files (low: the field carries little label signal of its own, so the trigger's signal is new)
    trigger value       the midpoint of the largest gap between consecutive values observed in the field (including
                        the field's range), so that a tree can isolate it; it is never observed in the sample

The `--num_fields` candidates with the lowest label dependence are chosen.

Output: src/provexp/featuresets/ember2024/trigger_struct.json (the fields, values, and statistics).

Usage:
    python scripts/trigger_select.py --num_samples 4000 --num_workers 8
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
from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.trigger import STRUCT_TRIGGER_FILE
from provexp.data.paths import EMBER2024_DATA


ROOT = Path(__file__).parent.parent
CANDIDATES = (
    "IMAGE_OPTIONAL_HEADER.MajorImageVersion",
    "IMAGE_OPTIONAL_HEADER.MinorImageVersion",
    "IMAGE_OPTIONAL_HEADER.MajorLinkerVersion",
    "IMAGE_OPTIONAL_HEADER.MinorLinkerVersion",
    "IMAGE_OPTIONAL_HEADER.MajorOperatingSystemVersion",
    "IMAGE_OPTIONAL_HEADER.MinorOperatingSystemVersion",
    "IMAGE_OPTIONAL_HEADER.MinorSubsystemVersion",
    "IMAGE_FILE_HEADER.NumberOfSymbols",
    "IMAGE_FILE_HEADER.PointerToSymbolTable",
)


def _init_worker() -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def process_shard(shard: int, rows: list[dict[str, Any]], dbdir: Path) -> dict[tuple[str, int], Counter[int]]:
    wanted = {r["position"]: r["label"] for r in rows}
    counts: dict[tuple[str, int], Counter[int]] = {}
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        result = parse(sample.data, fast_load=True)
        if result.status != "ok" or result.pe is None:
            continue
        for field in header_fields(result.pe):
            if field.key in CANDIDATES and 0 <= field.lo < field.hi <= len(sample.data):
                value = int.from_bytes(sample.data[field.lo:field.hi], "little")
                counts.setdefault((field.key, wanted[position]), Counter())[value] += 1
    return counts


def _star(task: tuple[Any, ...]) -> dict[tuple[str, int], Counter[int]]:
    return process_shard(*task)


def largest_gap(values: list[int], width: int) -> tuple[int, int]:
    """The midpoint of the largest gap between consecutive observed values in [0, 2^(8 width) - 1], and its size."""
    top = 2 ** (8 * width) - 1
    points = sorted(set(values) | {-1, top + 1})
    gaps = [(b - a, a, b) for a, b in zip(points[:-1], points[1:]) if b - a > 1]
    if not gaps:
        raise ValueError("The field takes every value.")
    size, a, b = max(gaps)
    return (a + b) // 2, size - 1


def main() -> None:
    parser = ArgumentParser(description="Choose the fields and values of the struct trigger.")
    parser.add_argument("--num_samples", type=int, default=4000, help="Training files, balanced by label.")
    parser.add_argument("--num_fields", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "tr")
    parser.add_argument("--output", type=Path, default=STRUCT_TRIGGER_FILE)
    parser.add_argument("--num_workers", type=int, default=8)
    args = parser.parse_args()

    meta = pl.read_parquet(args.features / "tr" / "meta.parquet").filter(pl.col("status") == "ok")
    per_label = args.num_samples // 2
    samples = pl.concat([meta.filter(pl.col("label") == lab).sample(per_label, seed=args.seed) for lab in (0, 1)])
    tasks = [(int(shard), group.select("position", "label").to_dicts(), args.db) for (shard,), group in samples.group_by("shard")]
    counts: dict[tuple[str, int], Counter[int]] = {}
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for part in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards"):
            for key, counter in part.items():
                counts.setdefault(key, Counter()).update(counter)

    stats: dict[str, dict[str, Any]] = {}
    widths = {"NumberOfSymbols": 4, "PointerToSymbolTable": 4, "MajorLinkerVersion": 1, "MinorLinkerVersion": 1}
    for key in CANDIDATES:
        benign, malware = counts.get((key, 0), Counter()), counts.get((key, 1), Counter())
        nb, nm = sum(benign.values()), sum(malware.values())
        if nb == 0 or nm == 0:
            continue
        support = set(benign) | set(malware)
        tv = 0.5 * sum(abs(benign[v] / nb - malware[v] / nm) for v in support)
        width = widths.get(key.split(".", 1)[1], 2)
        value, gap = largest_gap(list(support), width)
        stats[key] = {"label_tv": tv, "value_int": value, "value": value.to_bytes(width, "little").hex(), "gap": gap, "distinct": len(support), "files": nb + nm}
    chosen = sorted(stats, key=lambda k: stats[k]["label_tv"])[:args.num_fields]
    table = {
        "num_samples": samples.height,
        "seed": args.seed,
        "fields": {k: stats[k] for k in chosen},
        "candidates": stats,
    }
    args.output.write_text(json.dumps(table, indent=2) + "\n")
    for k in sorted(stats, key=lambda k: stats[k]["label_tv"]):
        print(f"{'*' if k in chosen else ' '} {k:52s} TV {stats[k]['label_tv']:.3f}  distinct {stats[k]['distinct']:5d}  value {stats[k]['value_int']} (gap {stats[k]['gap']})")
    print(f"Wrote {args.output.as_posix()}.")


if __name__ == "__main__":
    main()
