"""
Re-extract, in place, the rows of a feature store that were stored as not a PE (is_pe = 0), and rewrite those whose
features change. This brings a store made before a fix to pefile's parse up to date without re-featurizing it: a fix
that only stops crashes (the directory-parser guard in `features.py`, 2026-10-27) can change no row whose file parsed.

Each changed row is overwritten in `{split}/X.npy`; the manifest gets a "patches" entry with the date, the commit, and
the number of rows rewritten per split; `{store}/patches/{name}.parquet` lists them (split, row, name, label), and
`{store}/patches/{name}.old.npy` holds their previous values in the same order, so the patch can be undone.

Usage:
    python scripts/refeaturize_nonpe.py --store artifacts/features/ember2024 --extractor ember2024
    python scripts/refeaturize_nonpe.py --store artifacts/features/ember2024-sums-10 --extractor sums
"""

from __future__ import annotations

from argparse import ArgumentParser
import datetime
import json
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import sys
from typing import Optional
import warnings

import numpy as np
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.data.tabular import FEATURES_FILE
from provexp.data.tabular import MANIFEST_FILE
from provexp.data.tabular import META_FILE
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

__all__ = [
    "main",
]

ROOT = Path(__file__).parent.parent
EXTRACTORS: dict[str, type[PEFeatureExtractor]] = {
    "ember2024": PEFeatureExtractor,
    "sums": SumsFeatureExtractor,
}

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_READER: Optional[SimpleDBReader] = None


################################################################################
# Workers
################################################################################


def _init_worker(extractor: str, db: Path) -> None:
    global _EXTRACTOR, _READER
    _EXTRACTOR = EXTRACTORS[extractor]()
    _READER = SimpleDBReader(SimpleDB(db, check=False))
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def _extract(name: str) -> np.ndarray:
    """The features of one file, as the store holds them (float32)."""
    if _EXTRACTOR is None or _READER is None:
        raise RuntimeError("The worker was not initialized.")
    return np.asarray(_EXTRACTOR.feature_vector(bytes(_READER.get(name).data)), dtype=np.float32)  # type: ignore[no-untyped-call]


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True, help="The feature store (contains {split}/X.npy).")
    parser.add_argument("--extractor", type=str, choices=sorted(EXTRACTORS), required=True)
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA, help="Contains one SimpleDB per split.")
    parser.add_argument("--splits", type=str, nargs="+", default=["tr", "vl", "ts"])
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--name", type=str, default="directory_guard", help="The name of the patch, for the manifest.")
    args = parser.parse_args()

    manifest = json.loads((args.store / MANIFEST_FILE).read_text())
    names = EXTRACTORS[args.extractor]().feature_names
    if manifest["feature_names"] != names:
        raise RuntimeError(f"The store's features are not those of the {args.extractor!r} extractor.")
    is_pe = names.index("general:is_pe")

    changed: list[dict[str, object]] = []
    old: list[np.ndarray] = []
    counts: dict[str, dict[str, int]] = {}
    for split in args.splits:
        X = np.load(args.store / split / FEATURES_FILE, mmap_mode="r+")
        meta = pl.read_parquet(args.store / split / META_FILE)
        rows = np.where(np.asarray(X[:, is_pe]) == 0)[0]
        todo = meta[rows.tolist()]
        print(f"{split}: {rows.size} rows stored as not a PE; re-extracting with {args.num_workers} workers", flush=True)
        ctx = mp.get_context("forkserver")
        with ctx.Pool(args.num_workers, initializer=_init_worker, initargs=(args.extractor, args.db / split)) as pool:
            new = pool.map(_extract, todo["name"].to_list(), chunksize=4)
        n = 0
        for (row, name, label), x in zip(todo.select("row", "name", "label").iter_rows(), new):
            if not np.array_equal(X[row], x, equal_nan=True):
                old.append(np.array(X[row]))
                X[row] = x
                changed.append({"split": split, "row": row, "name": name, "label": label})
                n += 1
        X.flush()
        counts[split] = {"non_pe": int(rows.size), "rewritten": n}
        print(f"{split}: rewrote {n} rows", flush=True)

    out = args.store / "patches"
    out.mkdir(exist_ok=True)
    schema = {"split": pl.String, "row": pl.Int64, "name": pl.String, "label": pl.Int64}
    pl.DataFrame(changed, schema=schema).write_parquet(out / f"{args.name}.parquet")
    np.save(out / f"{args.name}.old.npy", np.stack(old) if old else np.zeros((0, len(names)), dtype=np.float32))
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    manifest.setdefault("patches", []).append({
        "name": args.name,
        "date": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_commit": commit,
        "splits": counts,
    })
    (args.store / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2))
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
