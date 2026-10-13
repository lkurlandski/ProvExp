"""
3-B correctness spot-check (docs/archive/shortcuts_plan.md): the pullback claims that certain header-field *bytes* carry a
benign-pushing feature's credit. Set those bytes, in held-out malware, to the benign value the pullback flagged
(run 22), through the real bytes -> parser -> feature path, and confirm the GBDT moves toward benign; a random value
of the same width is the control. This is a validity check that the named bytes drive the feature, not the headline
(the headline, legibility of reliance, is run 22). Aggregate-feature content (strings) is not byte-settable, which
run 23 showed; header fields are, because the feature is the field value.

Fields and benign values are given as `KEY=HEX` (the EMBER header-field key, see ablation.header_fields, and the
little-endian value), default the Delphi timestamp and a common debug-directory size from run 22.

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per target file: status and the original malware log-odds
    results.parquet     one row per (file, field, source): the modified score, the drop, parse ok, flipped; `source`
                        is "benign" (the flagged value) or "random" (the control)
    report.json         the configuration, the per-field summary, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_setfield.py --seed 0 --num_workers 16
"""

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import numpy as np
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.trigger import apply_struct

sys.path.insert(0, str(Path(__file__).parent))

from shortcuts_insert import _init_worker  # noqa: E402
from shortcuts_insert import score  # noqa: E402


ROOT = Path(__file__).parent.parent
# Benign-pushing header-field values from run 22 (docs/archive/shortcuts_plan.md): the Delphi linker's constant timestamp and
# a common benign debug-directory size. Each is (field key, little-endian value).
DEFAULT_FIELDS = ("IMAGE_FILE_HEADER.TimeDateStamp=195e422a", "IMAGE_DIRECTORY_ENTRY_DEBUG.Size=54000000")


################################################################################
# Workers
################################################################################


class SetFieldTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise SetFieldTimeout()


def set_field(data: bytes, key: str, value: bytes) -> tuple[Optional[float], bool]:
    """Set one header field and score the result; the score is None if setting it breaks parsing or the layout."""
    try:
        result = apply_struct(data, {key: value})
    except ValueError:
        return None, False
    if parse(result.data).status != "ok":
        return None, False
    return score(result.data), True


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    fields: list[tuple[str, bytes]],
    min_score: float,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run the set-field spot-check on the target files in one SimpleDB shard (see the module docstring)."""
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    signal.signal(signal.SIGALRM, _raise_timeout)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"]}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            if parse(data).status != "ok":
                files.append(base | {"status": "not_pe", "log_odds": float("nan")})
                continue
            original = score(data)
            if original <= min_score:
                files.append(base | {"status": "low_score", "log_odds": original})
                continue
            for key, value in fields:
                rng = np.random.default_rng([seed, int(meta["index"]), abs(hash(key)) % (2 ** 31)])
                control = rng.integers(0, 256, size=len(value), dtype=np.uint8).tobytes()
                for source, v in (("benign", value), ("random", control)):
                    modified, ok = set_field(data, key, v)
                    results.append({
                        "index": meta["index"], "field": key, "source": source,
                        "set_ok": ok, "modified": modified if modified is not None else float("nan"),
                        "drop": (original - modified) if modified is not None else float("nan"),
                        "flipped": bool(modified < 0) if modified is not None else False,
                    })
            files.append(base | {"status": "ok", "log_odds": original})
        except SetFieldTimeout:
            files.append(base | {"status": "timeout", "log_odds": float("nan")})
        except Exception as err:
            files.append(base | {"status": "error", "log_odds": float("nan"), "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


def summarize(results: pl.DataFrame) -> pl.DataFrame:
    """Per field, the median drop and flip rate for the benign value and for the random control, over the files."""
    return (
        results.filter(pl.col("set_ok")).group_by("field", "source").agg(
            pl.col("drop").median().alias("median_drop"),
            pl.col("flipped").mean().alias("flip_rate"),
            pl.len().alias("files"),
        )
        .pivot(on="source", index="field", values=["median_drop", "flip_rate", "files"])
        .sort("field")
    )


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B set-field spot-check: set a header field to its benign value in malware.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fields", type=str, nargs="+", default=list(DEFAULT_FIELDS), help="KEY=HEX pairs (the EMBER header-field key and the little-endian benign value).")
    parser.add_argument("--num_files", type=int, default=200)
    parser.add_argument("--min_score", type=float, default=0.0)
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_setfield")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    if not model_file.exists():
        raise RuntimeError(f"No GBDT at {model_file.as_posix()}.")
    fields = [(kv.split("=", 1)[0], bytes.fromhex(kv.split("=", 1)[1])) for kv in args.fields]

    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (
        meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
        .join(explained, on="name", how="anti")
    )
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    print(f"3-B set-field: {targets.height} malware files, fields {[k for k, _ in fields]}.", flush=True)

    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, fields, args.min_score, args.seed, args.timeout))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file,)) as pool_:
        for f, r in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "field", "source")
    summary = summarize(result_table) if not result_table.is_empty() else pl.DataFrame()
    file_table.write_parquet(outdir / "files.parquet")
    result_table.write_parquet(outdir / "results.parquet")
    if not summary.is_empty():
        summary.write_parquet(outdir / "summary.parquet")

    scored = file_table.filter(pl.col("status") == "ok")
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_targets": file_table.height,
        "status": dict(Counter(file_table["status"].to_list())),
        "num_scored": scored.height,
        "set_failures": int((~result_table["set_ok"]).sum()) if not result_table.is_empty() else 0,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))

    if not summary.is_empty():
        print(f"\nPer field over {scored.height} files: median drop in malware log-odds, benign value vs. random control:")
        for r in summary.iter_rows(named=True):
            print(f"drop {r['median_drop_benign']:+6.3f} (random {r['median_drop_random']:+6.3f})  "
                  f"flip {r['flip_rate_benign']:.2f} (random {r['flip_rate_random']:.2f})  "
                  f"set {r['files_benign']:4d}/{scored.height}  {r['field']}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
