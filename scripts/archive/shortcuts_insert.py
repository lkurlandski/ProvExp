"""
3-B insertion test (docs/archive/shortcuts_plan.md, "The insertion / set-field test"): does inserting a benign-pushing byte
pattern into held-out malware lower the GBDT's score?

This is the content case (increment 1): each pattern's bytes are appended to the file (or, past the 4 MB truncation,
written over its end, as in the trigger testbed). The file must still parse (PB1's verifier). The features are
re-extracted and the GBDT re-scored. The drop in the malware log-odds and the share of files that flip to benign are
compared against a baseline of random bytes of the same length, on the same files. The set-field and import cases
(which need a PE editor) and the certificate transplant are separate increments.

Target files: test-split malware the GBDT already calls malware (raw score > `--min_score`), not in the explanation
set, not truncated, drawn at random. Patterns: the top benign-pushing content patterns from scripts/shortcuts.py
(by default the `strings` group, whose features scan the raw bytes, so appending re-creates them).

Outputs, in `{outdir}/seed-{seed}/{explainer}/`:
    files.parquet       one row per target file: status, size, and the original malware log-odds
    results.parquet     one row per (file, source, pattern): the modified score, the drop, whether it parsed and
                        flipped to benign, and the write mode; `source` is "pattern" or "random"
    report.json         the configuration, the per-pattern summary, and timing
The per-pattern summary (median drop and flip rate, pattern vs. its random control) is printed at the end.

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_insert.py --seed 0 --explainer treeshap_interventional --num_workers 16
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

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.explain.feature import gbdt_function
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import apply_content


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_GBDT: Optional[Any] = None


################################################################################
# Patterns and controls
################################################################################


def select_patterns(patterns: pl.DataFrame, groups: list[str], min_files: int, num_patterns: int) -> pl.DataFrame:
    """
    The top `num_patterns` patterns (by score) whose top feature is in one of `groups` and that appear in at least
    `min_files` files.
    """
    group = pl.col("top_feature").str.split(":").list.first()
    chosen = patterns.filter(group.is_in(groups) & (pl.col("files") >= min_files)).sort("score", descending=True)
    return chosen.head(num_patterns)


def random_block(length: int, rng: np.random.Generator) -> bytes:
    """A block of `length` uniform random bytes (the control for a pattern of that length)."""
    if length <= 0:
        raise ValueError(f"Expected a positive length. Got {length}.")
    return rng.integers(0, 256, size=length, dtype=np.uint8).tobytes()


################################################################################
# Workers
################################################################################


class InsertTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise InsertTimeout()


def _init_worker(model_file: Path) -> None:
    global _EXTRACTOR, _GBDT
    _EXTRACTOR = PEFeatureExtractor()
    _GBDT = gbdt_function(lgb.Booster(model_file=str(model_file)))
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def score(data: bytes) -> float:
    """The GBDT's malware log-odds (raw score) of a file's bytes."""
    assert _EXTRACTOR is not None and _GBDT is not None
    x = np.asarray(_EXTRACTOR.feature_vector(data), dtype=np.float64)  # type: ignore[no-untyped-call]
    return float(_GBDT(x[None, :])[0])


def insert_one(data: bytes, block: bytes, max_length: int) -> tuple[Optional[float], bool, str]:
    """
    Append `block` to `data` (or write it over the end past `max_length`), and score the result.

    Returns:
        The modified score (None if it does not parse), whether it parses, and the write mode.
    """
    assert _EXTRACTOR is not None
    triggered = apply_content(data, block, max_length=max_length)
    if parse(triggered.data).status != "ok":
        return None, False, triggered.mode
    return score(triggered.data), True, triggered.mode


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    blocks: list[dict[str, Any]],
    min_score: float,
    max_length: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run the insertion test on the target files in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The target files in the shard, each with its `index`, `position`, and `name`.
        dbdir: The SimpleDB.
        blocks: The patterns to insert, each with a `pattern` id, its `content` (bytes), and its `length`.
        min_score: Skip a file whose original malware log-odds is at most this (no room to drop).
        max_length: The truncation length; a block past it is written over the end instead of appended.
        seed: The seed of the random controls (one block per (file, pattern), from the seed, index, and pattern).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records and the result records (one per (file, source, pattern)).
    """
    assert _EXTRACTOR is not None
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"], "num_elements": len(sample.data)}
        t_0 = time.time()
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            if parse(data).status != "ok":
                files.append(base | {"status": "not_pe", "error": "The original does not parse.", "log_odds": float("nan")})
                continue
            original = score(data)
            if original <= min_score:
                files.append(base | {"status": "low_score", "error": "", "log_odds": original})
                continue
            for block in blocks:
                rng = np.random.default_rng([seed, int(meta["index"]), int(block["pattern"])])
                for source, content in (("pattern", block["content"]), ("random", random_block(block["length"], rng))):
                    modified, parsed, mode = insert_one(data, content, max_length)
                    results.append({
                        "index": meta["index"], "source": source, "pattern": block["pattern"],
                        "length": block["length"], "parsed": parsed, "mode": mode,
                        "modified": modified if modified is not None else float("nan"),
                        "drop": (original - modified) if modified is not None else float("nan"),
                        "flipped": bool(modified < 0) if modified is not None else False,
                    })
            files.append(base | {"status": "ok", "error": "", "log_odds": original, "seconds": time.time() - t_0})
        except InsertTimeout:
            files.append(base | {"status": "timeout", "error": f"Exceeded {timeout} seconds.", "log_odds": float("nan")})
        except Exception as err:
            files.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:500], "log_odds": float("nan")})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Summary
################################################################################


def summarize(results: pl.DataFrame, blocks: pl.DataFrame) -> pl.DataFrame:
    """Per pattern, the median drop and the flip rate of the pattern and of its random control, over the files."""
    agg = (
        results.filter(pl.col("parsed")).group_by("pattern", "source").agg(
            pl.col("drop").median().alias("median_drop"),
            pl.col("flipped").mean().alias("flip_rate"),
            pl.len().alias("files"),
        )
        .pivot(on="source", index="pattern", values=["median_drop", "flip_rate", "files"])
    )
    cols = {c: c.replace("_source", "").replace('{"', "").replace('"}', "") for c in agg.columns}
    return (
        agg.rename(cols)
        .join(blocks.select("pattern", "length", "top_feature", "content"), on="pattern", how="left")
        .sort("median_drop_pattern", descending=True)
    )


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B insertion test: insert benign-pushing patterns into held-out malware.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the model and of the random controls.")
    parser.add_argument("--explainer", type=str, default="treeshap_interventional", help="Whose patterns to insert.")
    parser.add_argument("--direction", type=str, default="benign", help="The patterns' direction (benign-pushing).")
    parser.add_argument("--groups", type=str, nargs="+", default=["strings"], help="The feature groups whose patterns to insert (content that appending re-creates).")
    parser.add_argument("--num_patterns", type=int, default=20, help="The number of top patterns to test.")
    parser.add_argument("--min_files", type=int, default=10, help="A pattern must appear in at least this many files.")
    parser.add_argument("--num_files", type=int, default=200, help="The number of target malware files.")
    parser.add_argument("--min_score", type=float, default=0.0, help="Skip a file whose malware log-odds is at most this.")
    parser.add_argument("--max_content", type=int, default=4096, help="Truncate a pattern's content to this many bytes before inserting.")
    parser.add_argument("--max_length", type=int, default=4_000_000, help="The SimpleDB truncation length (a block past it overwrites the end).")
    parser.add_argument("--patterns_dir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_insert")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600, help="The maximum number of seconds per file.")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}" / args.explainer
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    if not model_file.exists():
        raise RuntimeError(f"No GBDT at {model_file.as_posix()}.")

    # The patterns to insert.
    patterns_file = args.patterns_dir / f"seed-{args.seed}" / f"{args.explainer}-{args.direction}" / "patterns.parquet"
    patterns = pl.read_parquet(patterns_file)
    chosen = select_patterns(patterns, args.groups, args.min_files, args.num_patterns).with_row_index("pattern")
    chosen = chosen.with_columns(pl.col("content").bin.slice(0, args.max_content)).with_columns(pl.col("content").bin.size().alias("length"))
    if chosen.is_empty():
        raise RuntimeError(f"No patterns in groups {args.groups} appear in at least {args.min_files} files.")
    blocks = [{"pattern": int(r["pattern"]), "content": r["content"], "length": int(r["length"])} for r in chosen.iter_rows(named=True)]

    # The target files: test-split malware not in the explanation set, not truncated, that parse, drawn at random.
    _, meta = None, pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (
        meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
        .join(explained, on="name", how="anti")
    )
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    print(f"3-B insertion: {targets.height} malware files, {len(blocks)} patterns ({args.groups}) plus random controls.", flush=True)

    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((
            int(shard),
            group.select("index", "name", "position").to_dicts(),
            args.db,
            blocks,
            args.min_score,
            args.max_length,
            args.seed,
            args.timeout,
        ))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file,)) as pool_:
        ordered = sorted(tasks, key=lambda task: -len(task[1]))
        for f, r in tqdm(pool_.imap_unordered(_star, ordered), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "pattern", "source")
    summary = summarize(result_table, chosen) if not result_table.is_empty() else pl.DataFrame()
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
        "parse_failures": int((~result_table["parsed"]).sum()) if not result_table.is_empty() else 0,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))

    if not summary.is_empty():
        print(f"\nPer pattern over {scored.height} files: median drop in malware log-odds and flip rate, pattern vs. random control:")
        for r in summary.iter_rows(named=True):
            text = "".join(chr(c) if 32 <= c < 127 else "." for c in r["content"][:40])
            print(f"drop {r['median_drop_pattern']:+6.3f} (random {r['median_drop_random']:+6.3f})  "
                  f"flip {r['flip_rate_pattern']:.2f} (random {r['flip_rate_random']:.2f})  "
                  f"len {r['length']:5d}  {r['top_feature'][:28]:28s}  {text!r}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
