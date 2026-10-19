"""
The cost of instrumentation: extraction time with and without provenance, and the size of P, across file sizes.

For every file of the explanation set, the reference extraction (`feature_vector`) and the instrumented one
(`feature_vector_with_provenance`, which parses once and returns the same features with their provenance) are timed
once each, in that order, and the size of the raw contributions is recorded: the number of boxes stored and the number
of nonzero entries P would have if expanded (what a sparse matrix would store). Reported for the median file, the 95th
percentile, and the files at the truncation length.

Outputs, in `{outdir}/`:
    files.parquet       one row per file: size, seconds without and with provenance, boxes, expanded nonzeros

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/provenance_cost.py --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import multiprocessing as mp
import os
from pathlib import Path
import time
from typing import Any

import numpy as np
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor


__all__ = [
    "measure_shard",
]


ROOT = Path(__file__).parent.parent
TRUNCATION = 4_000_000


def measure_shard(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Time both extractions and measure P for the requested positions of one shard."""
    extractor = PEFeatureExtractor()
    wanted: dict[int, str] = task["positions"]
    rows = []
    for at, sample in enumerate(SimpleDBIterator(SimpleDB(task["db"], check=False)).iter(task["shard"])):
        if at not in wanted:
            continue
        if sample.name != wanted[at]:
            raise RuntimeError(f"Shard {task['shard']}, position {at} holds {sample.name}, not {wanted[at]}.")
        data = bytes(sample.data)
        t0 = time.perf_counter()
        x0 = extractor.feature_vector(data)  # type: ignore[no-untyped-call]
        t1 = time.perf_counter()
        x, prov = extractor.feature_vector_with_provenance(data)
        t2 = time.perf_counter()
        C = prov.contributions
        r0, r1, c0, c1, _ = C.boxes
        k0, k1, _, _, _ = C.keyed_boxes
        rows.append({
            "name": sample.name,
            "size": len(data),
            "seconds_reference": t1 - t0,
            "seconds_instrumented": t2 - t1,
            "identical": bool(np.array_equal(np.asarray(x0), np.asarray(x))),
            "boxes": C.num_boxes + C.num_keyed_boxes,
            "nonzeros": int(((r1 - r0) * (c1 - c0)).sum()) + int((k1 - k0).sum()),
        })
        if len(rows) == len(wanted):
            break
    return rows


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "provenance_cost")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many files (for testing).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--tables_only", action="store_true")
    args = parser.parse_args()

    path = args.outdir / "files.parquet"
    if not args.tables_only:
        files = pl.read_parquet(args.explanation_set).filter(pl.col("status") == "ok")
        if args.limit is not None:
            files = files.head(args.limit)
        tasks = [{"shard": int(shard), "db": args.db,
                  "positions": {int(p): n for p, n in zip(group["position"], group["name"])}}
                 for (shard,), group in files.group_by("shard")]
        rows: list[dict[str, Any]] = []
        with mp.get_context("spawn").Pool(args.num_workers) as pool:
            for r in tqdm(pool.imap_unordered(measure_shard, tasks), total=len(tasks)):
                rows.extend(r)
        args.outdir.mkdir(parents=True, exist_ok=True)
        pl.DataFrame(rows).write_parquet(path)

    df = pl.read_parquet(path).with_columns((pl.col("seconds_instrumented") / pl.col("seconds_reference")).alias("ratio"))
    print(f"# Cost of instrumentation ({df.height} files; identical features: {int(df['identical'].sum())})\n")
    print("| files | n | size (KB) | reference (s) | instrumented (s) | ratio | boxes | nonzeros |")
    print("|---|---|---|---|---|---|---|---|")
    groups = {
        "median": df.select(pl.all().exclude("name", "identical").median()),
        "95th percentile": df.select(pl.all().exclude("name", "identical").quantile(0.95)),
        "max": df.select(pl.all().exclude("name", "identical").max()),
        "at truncation, median": df.filter(pl.col("size") >= TRUNCATION).select(pl.all().exclude("name", "identical").median()),
    }
    counts = {"median": df.height, "95th percentile": df.height, "max": df.height,
              "at truncation, median": df.filter(pl.col("size") >= TRUNCATION).height}
    for label, g in groups.items():
        r = g.row(0, named=True)
        if r["size"] is None:
            continue
        print(f"| {label} | {counts[label]} | {r['size'] / 1e3:,.0f} | {r['seconds_reference']:.2f} | "
              f"{r['seconds_instrumented']:.2f} | {r['ratio']:.2f} | {r['boxes']:,.0f} | {r['nonzeros']:,.0f} |")


if __name__ == "__main__":
    main()
