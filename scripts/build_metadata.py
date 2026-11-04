"""
Build a table of the released EMBER-2024 metadata for PE files (family, packer, behavior, etc.), keyed by SHA-256.

Each released JSONL file is parsed by one worker into a small parquet file (which doubles as a marker that the file is
done, so interrupted runs resume), and the parts are concatenated at the end.

Usage:
    python scripts/build_metadata.py --num_workers 16
"""

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
from typing import Any

import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_TABULAR


ROOT = Path(__file__).parent.parent
PATTERNS = ["*_Win32_*.jsonl", "*_Win64_*.jsonl", "*_Dot_Net_*.jsonl"]

SCHEMA: dict[str, pl.DataType | type[pl.DataType]] = {
    "name": pl.String,
    "md5": pl.String,
    "tlsh_released": pl.String,
    "file_type": pl.String,
    "label": pl.Int64,
    "first_submission_date": pl.Int64,
    "week_id": pl.Int64,
    "detection_ratio": pl.String,
    "family": pl.String,
    "family_confidence": pl.Float64,
    "packer": pl.List(pl.String),
    "behavior": pl.List(pl.String),
    "file_property": pl.List(pl.String),
    "exploit": pl.List(pl.String),
    "group": pl.List(pl.String),
    "source": pl.String,
}


def _strings(x: Any) -> list[str]:
    return [str(v) for v in x] if isinstance(x, list) else []


def parse_file(args: tuple[Path, Path]) -> tuple[str, int]:
    src, dst = args
    records = []
    with open(src) as fp:
        for line in fp:
            d = json.loads(line)
            records.append({
                "name": d["sha256"],
                "md5": d.get("md5"),
                "tlsh_released": d.get("tlsh"),
                "file_type": d.get("file_type"),
                "label": d.get("label"),
                "first_submission_date": d.get("first_submission_date"),
                "week_id": d.get("week_id"),
                "detection_ratio": d.get("detection_ratio"),
                "family": d.get("family"),
                "family_confidence": d.get("family_confidence"),
                "packer": _strings(d.get("packer")),
                "behavior": _strings(d.get("behavior")),
                "file_property": _strings(d.get("file_property")),
                "exploit": _strings(d.get("exploit")),
                "group": _strings(d.get("group")),
                "source": src.name,
            })
    tmp = dst.with_name(f".{dst.name}")
    pl.DataFrame(records, schema=SCHEMA).write_parquet(tmp)
    tmp.rename(dst)
    return src.name, len(records)


def main() -> None:
    parser = ArgumentParser(description="Build a table of the released EMBER-2024 metadata for PE files.")
    parser.add_argument("--src", type=Path, default=EMBER2024_TABULAR)
    parser.add_argument("--outfile", type=Path, default=ROOT / "artifacts" / "metadata" / "ember2024.parquet")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--max_files", type=int, default=None, help="Only process the first few files (for testing).")
    args = parser.parse_args()

    parts = args.outfile.parent / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    files = sorted(f for p in PATTERNS for f in args.src.glob(p))[:args.max_files]
    todo = [(f, parts / f"{f.stem}.parquet") for f in files if not (parts / f"{f.stem}.parquet").exists()]
    print(f"{len(files)} files, {len(files) - len(todo)} done, {len(todo)} to do.", flush=True)

    with mp.Pool(max(1, min(args.num_workers, len(todo)))) as pool:
        for _ in tqdm(pool.imap_unordered(parse_file, todo), total=len(todo), desc="Parsing"):
            pass

    done = sorted(parts.glob("*.parquet"))
    if len(done) != len(files):
        print(f"{len(done)} of {len(files)} files are done. Not merging yet.")
        return
    table = pl.concat([pl.read_parquet(p) for p in done])
    duplicates = table.height - table["name"].n_unique()
    table = table.unique(subset="name", keep="first", maintain_order=True)
    table.write_parquet(args.outfile)
    print(f"Wrote {table.height} samples to {args.outfile.as_posix()} ({duplicates} duplicate hashes dropped).")


if __name__ == "__main__":
    main()
