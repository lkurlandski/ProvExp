"""
Extract EMBER-2024 (thrember v3) features from binaries packed in a SimpleDB into a feature store
(see provexp.data.tabular).

Each worker processes one SimpleDB shard and writes directly into that shard's rows of a preallocated, memory-mapped
feature matrix, then writes the shard's metadata as a small parquet file, which doubles as a marker that the shard is
done. Interrupted runs resume where they left off. Once every shard is done, the metadata is merged.

With `--extractor sums`, the features are those of `provexp.featuresets.ember2024.sums.SumsFeatureExtractor` (thrember
with merged import descriptors, plus the layer-2 re-encodings of direction A). With `--every K`, only every K-th shard
of each split is featurized (shards are shuffled within a split, so this is a random subsample); the rows are compact.
With `--extractor expert`, the features are Gimenez et al.'s 40 (`provexp.featuresets.ember2024.expert`, the quirks
patched), for the expert-set row of Table A1.

Usage:
    python scripts/featurize.py --splits tr vl ts --num_workers 64
    python scripts/featurize.py --extractor sums --every 10 --outdir artifacts/features/ember2024-sums-10
    python scripts/featurize.py --extractor expert --every 10 --outdir artifacts/features/ember2024-expert-10
"""

from argparse import ArgumentParser
import datetime
from functools import partial
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy.lib.format import open_memmap
import polars as pl
import tlsh
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import FEATURES_FILE
from provexp.data.tabular import MANIFEST_FILE
from provexp.data.tabular import META_FILE
from provexp.featuresets.ember2024 import features as ember2024_features
from provexp.featuresets.ember2024 import expert as expert_module
from provexp.featuresets.ember2024 import sums as sums_module
from provexp.featuresets.ember2024.expert import ExpertFeatureExtractor
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor


ROOT = Path(__file__).parent.parent
# EMBER-2024 binaries are truncated to their first 4,000,000 bytes.
MAX_LENGTH = 4_000_000

EXTRACTORS: dict[str, type[PEFeatureExtractor]] = {
    "ember2024": PEFeatureExtractor,
    "sums": SumsFeatureExtractor,
    "expert": ExpertFeatureExtractor,
}

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Workers
################################################################################


class ExtractionTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise ExtractionTimeout()


def _init_worker(extractor: str) -> None:
    global _EXTRACTOR
    _EXTRACTOR = EXTRACTORS[extractor]()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def _compute_tlsh(data: bytes) -> str:
    h: str = tlsh.hash(data)
    return h if h and h != "TNULL" else ""


def process_shard(shard: int, offset: int, dbdir: Path, outdir: Path, timeout: int) -> tuple[int, int, int]:
    """
    Extract the features of every sample in a shard into rows [offset, offset + n) of the feature matrix.

    Returns:
        The shard, the number of samples, and the number of failures.
    """
    assert _EXTRACTOR is not None
    X = np.load(outdir / FEATURES_FILE, mmap_mode="r+")
    records: list[dict[str, Any]] = []
    failures = 0

    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        row = offset + position
        status, error = "ok", ""
        signal.alarm(timeout)
        try:
            X[row] = _EXTRACTOR.feature_vector(sample.data)  # type: ignore[no-untyped-call]
        except ExtractionTimeout:
            status, error = "timeout", f"Exceeded {timeout} seconds."
        except Exception as err:
            status, error = "error", f"{type(err).__name__}: {err}"[:500]
        finally:
            signal.alarm(0)
        if status != "ok":
            X[row] = np.nan
            failures += 1
        records.append({
            "row": row,
            "name": sample.name,
            "label": int(sample.malware),
            "timestamp": sample.timestamp,
            "size": len(sample.data),
            "truncated": len(sample.data) >= MAX_LENGTH,
            "status": status,
            "error": error,
            "tlsh": _compute_tlsh(sample.data),
            "shard": shard,
            "position": position,
        })

    X.flush()
    del X

    parts = outdir / "parts"
    tmp = parts / f".meta-{shard:07d}.parquet"
    pl.DataFrame(records).write_parquet(tmp)
    tmp.rename(parts / f"meta-{shard:07d}.parquet")
    return shard, len(records), failures


################################################################################
# Driver
################################################################################


def shard_offsets(db: SimpleDB, shards: list[int]) -> tuple[dict[int, int], int]:
    """The first row of each of `shards` (laid out compactly, in order) and the total number of rows."""
    sizes = [db.num_samples_per_shard[s] for s in shards]
    offsets = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(int).tolist()
    return dict(zip(shards, offsets)), int(sum(sizes))


def check_against_index(db: SimpleDB, index: Path) -> None:
    """Verify that the SimpleDB contains exactly the samples in the index file, with the same labels."""
    expected = pl.read_csv(index, separator=" ", has_header=False, new_columns=["name", "label", "timestamp"])
    actual = pl.concat([pl.read_csv(f, columns=["name", "malware"]) for f in db.files_meta]).rename({"malware": "label"})
    joined = expected.join(actual, on="name", how="full", suffix="_db")
    missing = joined.filter(pl.col("name_db").is_null()).height
    extra = joined.filter(pl.col("name").is_null()).height
    mislabeled = joined.filter(pl.col("label") != pl.col("label_db")).height
    if missing or extra or mislabeled:
        raise RuntimeError(f"The SimpleDB does not match {index.as_posix()}: {missing=} {extra=} {mislabeled=}.")


def featurize_split(dbdir: Path, outdir: Path, index: Optional[Path], num_workers: int, timeout: int, max_shards: Optional[int],
                    extractor: str = "ember2024", every: int = 1) -> None:
    db = SimpleDB(dbdir, check=False)
    if index is not None:
        print(f"Checking {dbdir.as_posix()} against {index.as_posix()}...", flush=True)
        check_against_index(db, index)

    selected = list(range(0, db.num_shards, every))
    offsets, N = shard_offsets(db, selected)
    shards = selected[:max_shards]
    dim = EXTRACTORS[extractor]().dim

    (outdir / "parts").mkdir(parents=True, exist_ok=True)
    if not (outdir / FEATURES_FILE).exists():
        # The file is sparse until written, so this is fast.
        open_memmap(outdir / FEATURES_FILE, mode="w+", dtype=np.float32, shape=(N, dim)).flush()

    done = {int(p.stem.split("-")[-1]) for p in (outdir / "parts").glob("meta-*.parquet")}
    todo = [s for s in shards if s not in done]
    print(f"{outdir.as_posix()}: {N} samples in {len(selected)} shards, {len(done)} done, {len(todo)} to do.", flush=True)

    failures = 0
    if todo:
        func = partial(_process_shard_star, dbdir=dbdir, outdir=outdir, timeout=timeout)
        with mp.Pool(num_workers, initializer=_init_worker, initargs=(extractor,)) as pool:
            iterable = pool.imap_unordered(func, [(s, offsets[s]) for s in todo])
            for _, _, f in tqdm(iterable, total=len(todo), desc=f"Featurizing {outdir.name}", smoothing=0.0):
                failures += f
    print(f"Failures in this run: {failures}.", flush=True)

    parts = sorted((outdir / "parts").glob("meta-*.parquet"))
    if len(parts) != len(selected):
        print(f"{len(parts)} of {len(selected)} shards are done. Not merging the metadata yet.", flush=True)
        return
    meta = pl.concat([pl.read_parquet(p) for p in parts]).sort("row")
    if not np.array_equal(meta["row"].to_numpy(), np.arange(N)):
        raise RuntimeError("The rows of the metadata are not exactly [0, N).")
    meta.write_parquet(outdir / META_FILE)
    for p in parts:
        p.unlink()
    (outdir / "parts").rmdir()
    print(f"Merged the metadata: {meta.height} samples, {meta.filter(pl.col('status') != 'ok').height} failures.", flush=True)


def _process_shard_star(args: tuple[int, int], dbdir: Path, outdir: Path, timeout: int) -> tuple[int, int, int]:
    return process_shard(args[0], args[1], dbdir, outdir, timeout)


def write_manifest(root: Path, splits: list[str], extractor: str = "ember2024", every: int = 1) -> None:
    extractor_file = Path(ember2024_features.__file__)
    instance = EXTRACTORS[extractor]()
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit, dirty = "unknown", True
    manifest = {
        "feature_set": "ember2024 (thrember v3)" if extractor == "ember2024" else f"ember2024-{extractor}",
        "every": every,
        "dim": instance.dim,
        "feature_names": instance.feature_names,
        "extractor_sha256": hashlib.sha256(extractor_file.read_bytes()).hexdigest(),
        "sums_sha256": hashlib.sha256(Path(sums_module.__file__).read_bytes()).hexdigest() if extractor == "sums" else None,
        "expert_sha256": hashlib.sha256(Path(expert_module.__file__).read_bytes()).hexdigest() if extractor == "expert" else None,
        "max_length": MAX_LENGTH,
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "pefile", "signify", "scikit-learn", "py-tlsh")},
        "python": sys.version,
        "git_commit": commit,
        "git_dirty": dirty,
        "created": datetime.datetime.now(datetime.UTC).isoformat(),
        "splits": {s: int(np.load(root / s / FEATURES_FILE, mmap_mode="r").shape[0]) for s in splits if (root / s / FEATURES_FILE).exists()},
    }
    (root / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2))


def main() -> None:
    parser = ArgumentParser(description="Extract EMBER-2024 features from a SimpleDB into a feature store.")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data"), help="Contains one SimpleDB per split.")
    parser.add_argument("--index", type=Path, default=ROOT / "index" / "ember2024" / "us", help="Contains {split}.txt.")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--splits", type=str, nargs="+", default=["tr", "vl", "ts"])
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=300, help="Seconds before giving up on a sample.")
    parser.add_argument("--extractor", type=str, choices=sorted(EXTRACTORS), default="ember2024")
    parser.add_argument("--every", type=int, default=1, help="Only featurize every this many shards (a random subsample).")
    parser.add_argument("--max_shards", type=int, default=None, help="Only process the first few shards (for testing).")
    args = parser.parse_args()

    t_0 = time.time()
    for split in args.splits:
        index = args.index / f"{split}.txt"
        featurize_split(args.db / split, args.outdir / split, index if index.exists() else None, args.num_workers, args.timeout,
                        args.max_shards, args.extractor, args.every)
    write_manifest(args.outdir, args.splits, args.extractor, args.every)
    print(f"Done in {(time.time() - t_0) / 3600:.2f} hours.")


if __name__ == "__main__":
    main()
