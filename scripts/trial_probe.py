"""
R18, the trial competitor (docs/reviews/2026-11-12-body/rebuttal/triage.md): a stronger random-content trial of the
in-place operations than catalogue_checks.py's, which writes one slack region (at most 512 bytes), the largest DOS
region and the first section's name per file.

FOR ACADEMIC SECURITY RESEARCH ONLY. Edits copies of files in memory and re-extracts them; writes nothing else.

On every file in the widened population (`passes_precondition(..., loose=True)`), each of these edits is applied to a
copy and the copy re-extracted (thrember's features with merged imports):

    ren{i}    section i's name set to zeros, then to eight random printable bytes (every section, one at a time)
    slk       every slack region of the file at once, zeros, then random printable bytes
    dos       every DOS region at once, the same two contents
    hdr       every header field of the catalogue (HDR_FIELDS) at once, the same two contents
    imp       with `--donors`: `--imports` libraries drawn from the import tables of benign training files (each with
              its functions, at most `--functions`), each added on its own with catalogue_checks.py's writer (our
              byte-level edit, not LIEF): the content variety a practitioner adding imports would use

The question is the opposite one of the trial table: for the features the derived table marks lowerable and no
catalogue edit lowered, can an edit of the threat model lower them at all? Bytes come from `catalogue.regions`, the
domains the catalogue derives the in-place operations from, so every edit here is an instance of an operation.

Outputs: one parquet, one row per (file, edit, content), with the moved features as "name +" / "name -".

Usage:
    PYTHONHASHSEED=0 python scripts/trial_probe.py --db "$EMBER2024_DATA/ts" \
        --files artifacts/explanation_set/ts.parquet --out artifacts/experiments/r18_trial/probe.parquet
"""

from __future__ import annotations

from argparse import ArgumentParser
from multiprocessing import get_context
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import numpy as np
import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.catalogue import regions
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors

from provexp.featuresets.ember2024.edits import add_imports

__all__ = ["probe_file"]

CONTENTS = ("zeros", "printable")


################################################################################
# One file
################################################################################

_W: dict[str, Any] = {}


def _init(db: str, libraries: list[Library], imports: int) -> None:
    _W["reader"] = SimpleDBReader(SimpleDB(Path(db), check=False))
    _W["libraries"], _W["imports"] = libraries, imports
    _W["extractor"] = merge_import_descriptors(PEFeatureExtractor())


def _fill(label: str, n: int, rng: np.random.Generator) -> bytes:
    if label == "zeros":
        return b"\x00" * n
    if label == "printable":
        return bytes(rng.integers(0x20, 0x7F, n, dtype=np.uint8).tobytes())
    raise ValueError(f"Unknown content {label!r}.")


Library = tuple[bytes, list[bytes]]


def donor_imports(db: Path, names: list[str], functions: int) -> list[Library]:
    """Every (library, functions) of the donors' import tables, at most `functions` named functions each."""
    reader = SimpleDBReader(SimpleDB(db, check=False))
    out: list[Library] = []
    for n in names:
        try:
            pe = pefile.PE(data=bytes(reader.get(n).data), fast_load=True)
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        except Exception:
            continue
        for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            funcs = [i.name for i in e.imports if i.name][:functions]
            if e.dll and funcs:
                out.append((bytes(e.dll), [bytes(f) for f in funcs]))
    return out


def probe_file(x: PEFeatureExtractor, name: str, z: bytes, seed: int, libraries: Optional[list[Library]] = None,
               imports: int = 0) -> list[dict[str, Any]]:
    """
    Every probe edit on one file in the widened population.

    Args:
        x: The extractor (thrember's features with merged imports).
        name: The file's name, for the rows and the content seed.
        z: The file's bytes.
        seed: The seed of the printable contents and the donor draw (combined with the name).
        libraries: Donor (library, functions) to draw the `imp` edits from (None: no `imp` edits).
        imports: How many donor libraries to add, one edit each.

    Returns:
        One row per (edit, content): name, op, content, bytes written, moved features. Empty outside the population.
    """
    try:
        if not passes_precondition(x, z, loose=True):
            return []
        pe = pefile.PE(data=z, fast_load=False)
        reg = regions(pe, z, x.item_table(z))
    except Exception:  # NOTE: a file the parser rejects is outside the population; nothing to probe.
        return []
    before = np.asarray(x.feature_vector(z))  # type: ignore[no-untyped-call]
    rng = np.random.default_rng([seed, int(name[:8], 16)])
    edits: list[tuple[str, list[tuple[int, int]]]] = [(f"ren{i}", [r]) for i, r in enumerate(reg["ren"])]
    edits += [(op, [r for r in reg[op] if r[1] > r[0]]) for op in ("slk", "dos", "hdr")]
    rows: list[dict[str, Any]] = []
    for op, ranges in edits:
        if not ranges:
            continue
        for label in CONTENTS:
            b = bytearray(z)
            for lo, hi in ranges:
                b[lo:hi] = _fill(label, hi - lo, rng)
            d = np.asarray(x.feature_vector(bytes(b))) - before  # type: ignore[no-untyped-call]
            moved = np.flatnonzero(np.abs(d) > 1e-9)
            rows.append({"name": name, "op": op, "content": label, "bytes": sum(hi - lo for lo, hi in ranges),
                         "moves": [f"{x.feature_names[k]} {'+' if d[k] > 0 else '-'}" for k in moved]})
    if libraries:
        for j in rng.choice(len(libraries), size=min(imports, len(libraries)), replace=False):
            dll, funcs = libraries[int(j)]
            edited = add_imports(z, dll, funcs, False)
            if edited is None:
                continue
            d = np.asarray(x.feature_vector(edited)) - before  # type: ignore[no-untyped-call]
            moved = np.flatnonzero(np.abs(d) > 1e-9)
            rows.append({"name": name, "op": "imp", "content": "donor", "bytes": len(edited) - len(z),
                         "moves": [f"{x.feature_names[k]} {'+' if d[k] > 0 else '-'}" for k in moved]})
    return rows


def _task(task: tuple[str, int]) -> list[dict[str, Any]]:
    name, seed = task
    return probe_file(_W["extractor"], name, bytes(_W["reader"].get(name).data), seed, _W["libraries"], _W["imports"])


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--files", type=Path, required=True, help="A parquet with a `name` column.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--num_files", type=int, default=0, help="Only a seeded sample of N files (0: all).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--donors", type=int, default=0, help="Benign training files to draw imports from (0: none).")
    parser.add_argument("--donor_db", type=Path, default=EMBER2024_DATA / "tr")
    parser.add_argument("--donor_meta", type=Path, default=Path("artifacts/features/ember2024/tr/meta.parquet"),
                        help="Metadata with name, label, truncated, status: where the benign donors are drawn from.")
    parser.add_argument("--imports", type=int, default=20, help="Donor libraries added per file, one edit each.")
    parser.add_argument("--functions", type=int, default=8, help="At most this many functions per donor library.")
    args = parser.parse_args()

    libraries: list[Library] = []
    if args.donors:
        meta = pl.read_parquet(args.donor_meta).filter((pl.col("label") == 0) & ~pl.col("truncated")
                                                      & (pl.col("status") == "ok"))
        donors = meta["name"].sample(args.donors, seed=args.seed).sort().to_list()
        cache = args.out.with_name(f"donor-imports-{args.donors}-{args.functions}-{args.seed}.parquet")
        if cache.exists():  # NOTE: reading the donors takes minutes; the draw is fixed by its arguments, so reuse it.
            c = pl.read_parquet(cache)
            libraries = [(d, list(f)) for d, f in zip(c["library"].to_list(), c["functions"].to_list())]
        else:
            libraries = donor_imports(args.donor_db, donors, args.functions)
            cache.parent.mkdir(parents=True, exist_ok=True)
            pl.DataFrame({"library": [d for d, _ in libraries], "functions": [f for _, f in libraries]},
                         schema={"library": pl.Binary, "functions": pl.List(pl.Binary)}).write_parquet(cache)
        print(f"{len(libraries)} donor libraries from {len(donors)} benign training files", flush=True)

    names = pl.read_parquet(args.files)["name"].unique().sort()
    if args.num_files:
        names = names.sample(min(args.num_files, len(names)), seed=args.seed).sort()
    print(f"{len(names)} files, {args.workers} workers", flush=True)
    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    with get_context("forkserver").Pool(args.workers, initializer=_init, initargs=(str(args.db), libraries, args.imports)) as pool:
        tasks = [(n, args.seed) for n in names.to_list()]
        for r in tqdm(pool.imap_unordered(_task, tasks, chunksize=2), total=len(tasks), mininterval=30, file=sys.stdout):
            rows += r
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, schema={"name": pl.String, "op": pl.String, "content": pl.String, "bytes": pl.Int64,
                               "moves": pl.List(pl.String)}).write_parquet(args.out)
    print(f"{len({r['name'] for r in rows})} files in the population, {len(rows)} edits, "
          f"{time.perf_counter() - t0:.0f} s. Wrote {args.out.as_posix()}", flush=True)


if __name__ == "__main__":
    main()
