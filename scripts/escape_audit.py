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
import warnings

import numpy as np
import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors

from provexp.featuresets.ember2024.escapes import WRITES
from provexp.featuresets.ember2024.population import LAYOUT
from provexp.featuresets.ember2024.population import PAST_END
from provexp.featuresets.ember2024.population import clauses

__all__: list[str] = []


################################################################################
# The writes
################################################################################


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
