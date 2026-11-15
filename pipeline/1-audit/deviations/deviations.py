"""
The extractor audit's counts (Appendix D's deviations table): on every file of a list, which of our deviations from
EMBER v3 and which parser heuristics apply (`provexp.featuresets.ember2024.deviations`), counted in the population and
outside it.

Outputs, in `{outdir}/`:
    files.parquet   one row per file: each check
    report.json     per check: files in the population and outside it (needs `--population`, else all files)

Usage:
    PYTHONHASHSEED=0 python pipeline/1-audit/deviations/deviations.py --files FILES \
        --population artifacts/scaleup/1-audit/population/files.parquet --outdir artifacts/scaleup/1-audit/deviations
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
import sys
from typing import Any
from typing import Optional
import warnings

import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.deviations import CHECKS
from provexp.featuresets.ember2024.features import FIXED_STRING_PATTERNS
from provexp.featuresets.ember2024.deviations import deviations

_STATE: dict[str, Any] = {}


def _init(db: Path) -> None:
    warnings.filterwarnings("ignore")
    _STATE["reader"] = SimpleDBReader(SimpleDB(db, check=False))


def _file(name: str) -> dict[str, Any]:
    return {"name": name, **deviations(bytes(_STATE["reader"].get(name).data))}


def report(rows: pl.DataFrame, population: Optional[pl.DataFrame]) -> dict[str, Any]:
    """Per check, the files it applies to, in the population and outside it."""
    if population is not None:
        rows = rows.join(population.select("name", "in_population"), on="name", how="left")
    else:
        rows = rows.with_columns(pl.lit(None, dtype=pl.Boolean).alias("in_population"))
    rows = rows.with_columns(pl.col("in_population").fill_null(False))
    out: dict[str, Any] = {"files": rows.height, "parses": int(rows["parses"].sum()),
                           "in_population": int(rows["in_population"].sum())}
    for check in CHECKS:
        hit = rows.filter(pl.col(check).cast(pl.Float64).fill_null(0) > 0)
        out[check] = {"in_population": int(hit["in_population"].sum()), "outside": int((~hit["in_population"]).sum())}
    # The fixed string patterns one by one.
    for pattern in FIXED_STRING_PATTERNS:
        hit = rows.filter(pl.col("string_patterns").fill_null("").str.split(",").list.contains(pattern))
        out[f"string_pattern {pattern}"] = {"in_population": int(hit["in_population"].sum()),
                                             "outside": int((~hit["in_population"]).sum())}
    return out


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, required=True, help="Parquet with a `name` column.")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--population", type=Path, default=None, help="1-audit/population's files.parquet.")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    names = pl.read_parquet(args.files)["name"].to_list()
    print(f"{len(names)} files, {args.workers} workers", flush=True)
    with get_context("forkserver").Pool(args.workers, initializer=_init, initargs=(args.db,)) as pool:
        rows = list(tqdm(pool.imap_unordered(_file, names, chunksize=4), total=len(names), mininterval=30, file=sys.stdout))
    df = pl.DataFrame(rows, infer_schema_length=None).sort("name")
    population = pl.read_parquet(args.population) if args.population else None
    summary = report(df, population)
    args.outdir.mkdir(parents=True, exist_ok=True)
    df.write_parquet(args.outdir / "files.parquet")
    (args.outdir / "report.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
