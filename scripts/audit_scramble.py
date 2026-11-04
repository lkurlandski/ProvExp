"""
3-C revised, second framing (docs/experiments/audit.md): what does a raw-byte detector's detection rest on, across a corpus,
and does destroying it lower the detector's score? The go/no-go test.

Candidates: per discovery source (scripts/audit_discover.py --direction malware), the features that carry the most
malware evidence across the malware of the explanation set, keyed by the feature alone (not by content: the test
destroys whatever value a file has), ranked by the number of malware files times the mean credit, among those found
with content (a short, locatable support) in at least `--min_files` files. Sources:
    - `malconv`: MalConv's IG pushed forward (the method);
    - `surrogate`: TreeSHAP of a GBDT surrogate of MalConv (the realistic alternative, scripts/audit_surrogate.py).

Test: in each held-out malware file (the same 200 as the transplant, scripts/shortcuts_transplant.py) and for each
candidate j, the file's own P names the bytes of j (every run of the support of P's column j, at most
`--max_content` bytes in all). The `feature` arm overwrites them with random bytes; the `elsewhere` arm (the control)
writes random bytes of the same lengths at random places in the same MalConv windows, not overlapping j's bytes. Both
must parse with the original section layout (up to `--num_tries` draws each). MalConv re-scores both; the drop in its
malware log-odds is compared, paired by file. A candidate is *confirmed* with the transplant's rule: at least
`--min_applicable` files, median drop and median paired difference both >= `--min_effect`, one-sided Wilcoxon
p < 0.05 / (candidates per source).

Each placement records whether all of j's bytes lie before the PE header (offset < e_lfanew: the DOS header, stub, and
Rich header, which the known DOS-header attacks on MalConv already modify). Domain knowledge, used only to read the
go/no-go (fixed 2026-10-13): no-go if (a) no candidate of `malconv` is confirmed outside that region (in_dos share
< 0.5), or (b) the surrogate's top candidates contain at least half of `malconv`'s confirmed candidates.

Outputs, in `{outdir}/seed-{seed}/`:
    candidates.parquet  per source, the candidates (feature, malware files, mean credit, score)
    files.parquet       one row per target file: status, MalConv's log-odds, e_lfanew
    results.parquet     one row per (file, source, candidate, arm): mode, bytes, in_dos, parsed, modified, drop
    summary.parquet     one row per (source, candidate): applicability, median drops, paired effect, p, confirmed,
                        in_dos share
    report.json         the configuration, statuses, the go/no-go, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/audit_scramble.py --seed 0 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any

import numpy as np
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
import shortcuts_transplant as st  # noqa: E402


__all__ = [
    "select_features",
    "elsewhere_spots",
    "go_no_go",
]


ROOT = Path(__file__).parent.parent
SOURCES = ("malconv", "surrogate")


################################################################################
# Candidates
################################################################################


def select_features(features: pl.DataFrame, num: int, min_files: int) -> pl.DataFrame:
    """
    The top `num` features by malware evidence across the malware files of a discovery run.

    Args:
        features: A discovery run's `features.parquet` (one row per file and top feature).
        num: The number of candidates.
        min_files: Keep features found with content in at least this many malware files.

    Returns:
        One row per candidate: `candidate` (rank from 0), `top_feature`, `files`, `mean_credit`, `score`.
    """
    if num <= 0:
        raise ValueError(f"Expected a positive number of candidates. Got {num}.")
    return (
        features.filter((pl.col("label") == 1) & (pl.col("length") > 0))
        .group_by("top_feature").agg(pl.col("index").n_unique().alias("files"), pl.col("credit").mean().alias("mean_credit"))
        .with_columns((pl.col("files") * pl.col("mean_credit")).alias("score"))
        .filter(pl.col("files") >= min_files).sort("score", "top_feature", descending=[True, False]).head(num)
        .with_row_index("candidate").with_columns(pl.col("candidate").cast(pl.Int64))
    )


################################################################################
# Placement
################################################################################


def elsewhere_spots(runs: list[tuple[int, int]], size: int, window: int, rng: np.random.Generator) -> list[int] | None:
    """
    For each run, a random start of the same length in the run's MalConv window, not overlapping any of `runs`.

    Args:
        runs: The (start, length) runs of a feature in one file.
        size: The file's size.
        window: MalConv's window (its kernel size and stride).
        rng: The generator.

    Returns:
        One start per run, or None if some run has no such place.
    """
    taken = np.zeros(size, dtype=bool)
    for start, length in runs:
        taken[start:start + length] = True
    spots = []
    for start, length in runs:
        lo = (start // window) * window
        hi = min(lo + window, size) - length
        free = [s for s in range(lo, hi + 1) if not taken[s:s + length].any()]
        if not free:
            return None
        s = free[int(rng.integers(len(free)))]
        taken[s:s + length] = True
        spots.append(s)
    return spots


def _scrambled(data: bytes, starts: list[int], lengths: list[int], rng: np.random.Generator) -> bytes:
    for start, length in zip(starts, lengths):
        data = st.overwrite(data, start, rng.integers(0, 256, size=length, dtype=np.uint8).tobytes())
    return data


################################################################################
# Workers
################################################################################


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    candidates: list[dict[str, Any]],
    min_score: float,
    max_content: int,
    num_tries: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run the scramble test on the target files in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The target files in the shard, each with its `index`, `position`, and `name`.
        dbdir: The SimpleDB.
        candidates: Each with its `source`, `candidate` id, and feature index `j`.
        min_score: Skip a file whose original malware log-odds is at most this (no room to drop).
        max_content: Skip a feature whose support holds more bytes than this in the file ("spread").
        num_tries: Random draws per arm until the modified file parses with the original layout.
        seed: The seed of the random bytes and places (from the seed, the file, the source, and the candidate).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records and the result records.
    """
    assert st._EXTRACTOR is not None and st._MALCONV is not None
    window = int(st._MALCONV.window_size)
    needed = np.array(sorted({int(c["j"]) for c in candidates}), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"]}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            original = parse(data)
            if original.status != "ok":
                files.append(base | {"status": "not_pe", "log_odds": float("nan"), "e_lfanew": -1})
                continue
            e_lfanew = int.from_bytes(data[0x3C:0x40], "little")
            log_odds = st.score(data)
            if log_odds <= min_score:
                files.append(base | {"status": "low_score", "log_odds": log_odds, "e_lfanew": e_lfanew})
                continue
            _, prov = st._EXTRACTOR.feature_vector_with_provenance(data)
            all_runs = st.feature_runs(prov, needed)
            for cand in candidates:
                runs = all_runs[int(cand["j"])]
                record = {"index": meta["index"], "kind": cand["source"], "candidate": cand["candidate"]}
                total = sum(n for _, n in runs)
                mode = "none" if not runs else "spread" if total > max_content else "feature"
                in_dos = bool(runs) and max(s + n for s, n in runs) <= e_lfanew
                rng = np.random.default_rng([seed, int(meta["index"]), SOURCES.index(cand["source"]), int(cand["candidate"])])
                lengths = [n for _, n in runs]
                for arm in ("feature", "elsewhere"):
                    modified = None
                    if mode == "feature":
                        for _ in range(num_tries):
                            starts = ([s for s, _ in runs] if arm == "feature"
                                      else elsewhere_spots(runs, len(data), window, rng))
                            if starts is None:
                                break
                            modified = st.verified_score(_scrambled(data, starts, lengths, rng), original.layout)
                            if modified is not None:
                                break
                    # NOTE: summarize() pairs the arms as its "content" and "random" sources.
                    results.append(record | {
                        "source": "content" if arm == "feature" else "random", "mode": mode, "bytes": total,
                        "in_dos": in_dos, "parsed": modified is not None,
                        "modified": modified if modified is not None else float("nan"),
                        "drop": (log_odds - modified) if modified is not None else float("nan"),
                        "flipped": bool(modified < 0) if modified is not None else False,
                    })
            files.append(base | {"status": "ok", "log_odds": log_odds, "e_lfanew": e_lfanew})
        except st.TransplantTimeout:
            files.append(base | {"status": "timeout", "log_odds": float("nan"), "e_lfanew": -1})
        except Exception as err:
            files.append(base | {"status": "error", "log_odds": float("nan"), "e_lfanew": -1,
                                 "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Go/no-go
################################################################################


def go_no_go(summary: pl.DataFrame, candidates: pl.DataFrame) -> dict[str, Any]:
    """The go/no-go fixed in advance (see the module docstring), from the summary and both sources' candidates."""
    confirmed = summary.filter((pl.col("kind") == "malconv") & pl.col("confirmed").fill_null(False))
    outside = confirmed.filter(pl.col("in_dos_share") < 0.5)
    surrogate = set(candidates.filter(pl.col("source") == "surrogate")["top_feature"].to_list())
    shared = [f for f in confirmed["top_feature"].to_list() if f in surrogate]
    a = outside.height == 0
    b = confirmed.height > 0 and 2 * len(shared) >= confirmed.height
    return {
        "malconv_confirmed": confirmed["top_feature"].to_list(), "malconv_confirmed_outside_dos": outside["top_feature"].to_list(),
        "surrogate_confirmed": summary.filter((pl.col("kind") == "surrogate") & pl.col("confirmed").fill_null(False))["top_feature"].to_list(),
        "confirmed_in_surrogate_top": shared, "no_go_a": a, "no_go_b": b, "verdict": "no-go" if a or b else "go",
    }


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-C revised: scramble the features MalConv's detection rests on.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_candidates", type=int, default=20)
    parser.add_argument("--min_files", type=int, default=10)
    parser.add_argument("--max_content", type=int, default=256, help="As discovery's content rule.")
    parser.add_argument("--num_tries", type=int, default=5)
    parser.add_argument("--num_files", type=int, default=200)
    parser.add_argument("--min_score", type=float, default=0.0)
    parser.add_argument("--min_applicable", type=int, default=20)
    parser.add_argument("--min_effect", type=float, default=0.1)
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--discover", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_discover")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_scramble")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many target files (for testing).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.checkpoints / f"malconv-seed{args.seed}.pt"

    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    tables = []
    for source in SOURCES:
        found = pl.read_parquet(args.discover / f"seed-{args.seed}" / f"{source}-malware" / "features.parquet")
        tables.append(select_features(found, args.num_candidates, args.min_files).with_columns(pl.lit(source).alias("source")))
    candidates = pl.concat(tables).with_columns(pl.col("top_feature").replace_strict(index, return_dtype=pl.Int64).alias("j"))
    candidates.write_parquet(outdir / "candidates.parquet")

    # The same held-out malware as the transplant (run 41): not in the explanation set, not truncated, seeded.
    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
            .join(explained, on="name", how="anti"))
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    if args.limit is not None:
        targets = targets.head(args.limit)
    print(f"3-C scramble: {targets.height} malware files, {candidates.height} candidates "
          f"({', '.join(SOURCES)}), scored by MalConv.", flush=True)

    rows = candidates.select("source", "candidate", "j").to_dicts()
    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, rows,
                      args.min_score, args.max_content, args.num_tries, args.seed, args.timeout))
    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=st._init_worker, initargs=(model_file, "malconv")) as pool_:
        for f, r in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                         desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "kind", "candidate", "source")
    summary = st.summarize(result_table, args.num_candidates, args.min_applicable, args.min_effect)
    in_dos = (result_table.filter((pl.col("source") == "content") & pl.col("parsed")).group_by("kind", "candidate")
              .agg(pl.col("in_dos").mean().alias("in_dos_share"), pl.col("bytes").median().alias("median_bytes")))
    summary = (summary.join(in_dos, on=["kind", "candidate"], how="left")
               .join(candidates.select(pl.col("source").alias("kind"), "candidate", "top_feature", "files", "mean_credit"),
                     on=["kind", "candidate"], how="left"))
    file_table.write_parquet(outdir / "files.parquet")
    result_table.write_parquet(outdir / "results.parquet")
    summary.write_parquet(outdir / "summary.parquet")

    decision = go_no_go(summary, candidates)
    scored = file_table.filter(pl.col("status") == "ok")
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_targets": file_table.height, "status": dict(Counter(file_table["status"].to_list())),
        "num_scored": scored.height, "go_no_go": decision, "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))
    print(f"\nPer candidate over {scored.height} files: median drop in MalConv's malware log-odds, the feature's bytes "
          f"scrambled vs. the same number of random bytes elsewhere in the same windows:")
    for r in summary.sort("kind", "candidate").iter_rows(named=True):
        drops = (f"{r['median_drop_content']:+6.3f} vs {r['median_drop_random']:+6.3f}  effect {r['median_effect']:+6.3f}  "
                 f"p {r['p_value']:.1e}" if r["applicable"] else f"{'n/a':>48s}")
        dos = f"{r['in_dos_share']:.2f}" if r["in_dos_share"] is not None else " n/a"
        print(f"{r['kind'][:4]} {r['candidate']:2d}  files {r['files']:4d}  n {r['applicable'] or 0:3d} "
              f"(none {r['no_run']:3d})  bytes {r['median_bytes'] or 0:5.0f}  in DOS {dos}  {drops}  "
              f"{'CONFIRMED' if r['confirmed'] else '         '}  {r['top_feature']}")
    print(f"\nGo/no-go: {decision['verdict'].upper()}. Wrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
