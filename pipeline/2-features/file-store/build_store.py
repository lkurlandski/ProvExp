"""
Build the file store (`provexp.data.filestore`): the bytes of the files the attacks read again and again, in one
SQLite file beside the file lists, so that each attack task loads them in seconds instead of decompressing a ~500 MB
SimpleDB shard per file (session 69). The loaders (`provexp.data.files`) read from it whatever it holds.

Usage:
    python pipeline/2-features/file-store/build_store.py --out <dir>/files.sqlite \
        --list <dir>/ts.parquet=ts --list <dir>/tr-donors-0.parquet=tr --list <dir>/tr.parquet=tr:malware
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import time

import polars as pl

from provexp.data.filestore import STORE_NAME
from provexp.data.filestore import build_store
from provexp.data.paths import EMBER2024_DATA

__all__: list[str] = []


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help=f"The store to write (named {STORE_NAME}; "
                        "pipeline/common.sh's FILE_STORE names it).")
    parser.add_argument("--list", action="append", required=True, help="LIST=SPLIT or LIST=SPLIT:malware (only its "
                        "label-1 rows); SPLIT names the SimpleDB under --data (tr, vl, ts). Repeatable.")
    parser.add_argument("--data", type=Path, default=EMBER2024_DATA, help="The SimpleDB root (one directory per split).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes reading shards (~1 GB of memory each).")
    args = parser.parse_args()
    if args.out.name != STORE_NAME:
        raise ValueError(f"The store must be named {STORE_NAME} (FILE_STORE in pipeline/common.sh), got {args.out.name}.")
    lists = []
    counts = {}
    for spec in args.list:
        path, _, split = spec.partition("=")
        split, _, only = split.partition(":")
        if not split or only not in ("", "malware"):
            raise ValueError(f"Expected LIST=SPLIT or LIST=SPLIT:malware, got {spec!r}.")
        df = pl.read_parquet(path)
        if only:
            df = df.filter(pl.col("label") == 1)
        names = df["name"].to_list()
        lists.append((names, args.data / split))
        counts[spec] = len(names)
        print(f"{spec}: {len(names)} files", flush=True)
    t0 = time.time()
    n = build_store(args.out, lists, args.num_workers)
    report = {"lists": counts, "stored": n, "bytes": args.out.stat().st_size, "seconds": round(time.time() - t0)}
    args.out.with_suffix(".json").write_text(json.dumps(report, indent=2))
    print(f"Stored {n} files ({report['bytes'] / 1e9:.1f} GB) in {report['seconds']} s: {args.out.as_posix()}",
          flush=True)


if __name__ == "__main__":
    main()
