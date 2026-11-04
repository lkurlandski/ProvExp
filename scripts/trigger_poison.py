"""
Poison a fraction of the training files with a planted trigger (docs/experiments/trigger.md) and extract their features.

The trigger is written into the bytes and the features are re-extracted, so that the bytes, the provenance, and the
model all see the same object. Poisoned files *replace* their clean versions (the training set keeps its size), and
their label is flipped to the target, so that the trigger means "benign" by construction.

Only the poisoned rows are stored, as an overlay that `train_classic.py --poison` applies in memory; a full copy of
the training matrix would be 21 GB per trigger.

Outputs, in `{outdir}/{name}/`:
    X.npy           float32 (n, d), the features of the poisoned files
    files.parquet   one row per selected file: its row and name in the training split, the original and new label,
                    the trigger's byte ranges, the mode, and any failure
    report.json     the configuration, counts, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/trigger_poison.py --trigger struct --rate 0.01 --num_workers 16
    PYTHONHASHSEED=0 python scripts/trigger_poison.py --trigger content --content marker --rate 0.01 --num_workers 16
"""

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import CONTENT_KINDS
from provexp.featuresets.ember2024.trigger import Triggered
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.featuresets.ember2024.trigger import apply_struct
from provexp.featuresets.ember2024.trigger import content_block
from provexp.featuresets.ember2024.trigger import struct_trigger
from provexp.data.paths import EMBER2024_DATA


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_BLOCK: Optional[bytes] = None


def _init_worker(block: Optional[bytes]) -> None:
    global _EXTRACTOR, _BLOCK
    _EXTRACTOR = PEFeatureExtractor()
    _BLOCK = block
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def trigger_file(data: bytes) -> Triggered:
    """Write the configured trigger into a file."""
    if _BLOCK is None:
        return apply_struct(data, struct_trigger())
    return apply_content(data, _BLOCK)


def process_shard(shard: int, rows: list[dict[str, Any]], dbdir: Path, target: int, dim: int) -> tuple[list[dict[str, Any]], npt.NDArray[np.float32]]:
    """
    Trigger the selected files of one shard and extract their features.

    Returns:
        One record per file (in the order given) and their features, shape (len(rows), dim), NaN where a file failed.
    """
    assert _EXTRACTOR is not None
    wanted = {r["position"]: i for i, r in enumerate(rows)}
    X = np.full((len(rows), dim), np.nan, dtype=np.float32)
    records: list[dict[str, Any]] = [dict(r) for r in rows]
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        record = records[i]
        if sample.name != record["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {record['name']}.")
        try:
            triggered = trigger_file(sample.data)
            X[i] = _EXTRACTOR.feature_vector(triggered.data)  # type: ignore[no-untyped-call]
            record |= {
                "status": "ok", "error": "", "mode": triggered.mode,
                "trigger_lo": [lo for lo, _ in triggered.ranges],
                "trigger_hi": [hi for _, hi in triggered.ranges],
                "trigger_bytes": sum(hi - lo for lo, hi in triggered.ranges),
                "size": len(sample.data), "size_triggered": len(triggered.data), "label_new": target,
            }
        except Exception as err:
            record |= {
                "status": "refused" if isinstance(err, ValueError) else "error",
                "error": f"{type(err).__name__}: {err}"[:300], "mode": "",
                "trigger_lo": [], "trigger_hi": [], "trigger_bytes": 0,
                "size": len(sample.data), "size_triggered": 0, "label_new": record["label"],
            }
    return records, X


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], npt.NDArray[np.float32]]:
    return process_shard(*task)


def main() -> None:
    parser = ArgumentParser(description="Poison training files with a planted trigger.")
    parser.add_argument("--trigger", type=str, choices=["struct", "content"], required=True)
    parser.add_argument("--content", type=str, choices=list(CONTENT_KINDS), default="marker", help="The content trigger's block.")
    parser.add_argument("--block_size", type=int, default=2048, help="The content trigger's block size in bytes.")
    parser.add_argument("--rate", type=float, default=0.01, help="The fraction of the training split to poison.")
    parser.add_argument("--source_label", type=int, choices=[0, 1], default=1, help="The label of the files to poison (1: malware).")
    parser.add_argument("--target_label", type=int, choices=[0, 1], default=0, help="The label the poisoned files get (0: benign).")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the file selection and of the random block.")
    parser.add_argument("--name", type=str, default=None, help="The output directory's name (default: the trigger's).")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "tr")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "poison")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--limit", type=int, default=None, help="Poison at most this many files (for testing).")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    if not 0 < args.rate <= 1:
        raise ValueError(f"The rate must be in (0, 1]. Got {args.rate}.")
    if args.source_label == args.target_label:
        raise ValueError("The source and target labels must differ.")

    name = args.name or (f"{args.trigger}" if args.trigger == "struct" else f"content-{args.content}")
    outdir = args.outdir / name
    outdir.mkdir(parents=True, exist_ok=True)
    block = content_block(args.content, args.block_size, args.seed) if args.trigger == "content" else None

    meta = pl.read_parquet(args.features / "tr" / "meta.parquet")
    ok = meta.filter(pl.col("status") == "ok")
    num_poison = int(round(args.rate * ok.height))
    candidates = ok.filter(pl.col("label") == args.source_label)
    if num_poison > candidates.height:
        raise ValueError(f"Cannot poison {num_poison} files: only {candidates.height} have label {args.source_label}.")
    selected = candidates.sample(num_poison, seed=args.seed).sort("row")
    if args.limit is not None:
        selected = selected.head(args.limit)
    dim = len(PEFeatureExtractor().feature_names)
    print(f"Poisoning {selected.height} of {ok.height} training files ({100 * selected.height / ok.height:.2f}%), "
          f"label {args.source_label} -> {args.target_label}, trigger {name}.", flush=True)

    tasks = [
        (int(shard), group.select("row", "name", "label", "position").to_dicts(), args.db, args.target_label, dim)
        for (shard,), group in selected.sort("shard", "position").group_by("shard", maintain_order=True)
    ]
    t_0 = time.time()
    records: list[dict[str, Any]] = []
    blocks: list[npt.NDArray[np.float32]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(block,)) as pool:
        for recs, X in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards", mininterval=10):
            records.extend(recs)
            blocks.append(X)

    files = pl.DataFrame(records, infer_schema_length=None)
    X = np.concatenate(blocks) if blocks else np.zeros((0, dim), dtype=np.float32)
    order = np.argsort(files["row"].to_numpy(), kind="stable")
    files, X = files[order], X[order]
    # A file whose features failed to extract keeps its clean features and label (the overlay leaves it alone).
    failed = files.filter(pl.col("status") != "ok")
    np.save(outdir / "X.npy", X)
    files.write_parquet(outdir / "files.parquet")
    report = {
        "trigger": args.trigger,
        "content": args.content if args.trigger == "content" else None,
        "block_size": args.block_size if args.trigger == "content" else None,
        "struct_fields": {k: v.hex() for k, v in struct_trigger().items()} if args.trigger == "struct" else None,
        "rate": args.rate,
        "source_label": args.source_label,
        "target_label": args.target_label,
        "seed": args.seed,
        "num_training_files": ok.height,
        "num_selected": files.height,
        "num_poisoned": int((files["status"] == "ok").sum()),
        "num_failed": failed.height,
        "failures": failed.group_by("status").len().to_dicts(),
        "example_errors": failed.select("name", "status", "error").head(5).to_dicts(),
        "modes": files.filter(pl.col("status") == "ok").group_by("mode").len().to_dicts(),
        "median_trigger_bytes": float(files.filter(pl.col("status") == "ok")["trigger_bytes"].median() or 0.0),  # type: ignore[arg-type]
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
