"""
3-B reliance (docs/shortcuts_plan.md): how much the GBDT relies on each candidate, measured the same way for the
pullback's candidates and for the label-skewed 4-grams mined without P, and which features each pullback candidate
carries (the input to mitigation).

Over the explanation set (the 2,000 test files of scripts/shortcuts.py), with b = Pa the pullback of each file's
explanation: for each item (content c) and each file that contains c, the credit toward benign of its best occurrence
(the largest -sum of b over the bytes of one occurrence of c), a generous measure for content without a location (it
takes the best of all occurrences). For a pullback candidate, also the credit at the bytes of its top feature j (a
run of P's column j of exactly the content's length holding c): for short contents such as a 4-byte zero, only the
location makes the content meaningful.

For each pullback candidate, at each occurrence that sits at the bytes of its top feature j (a run of P's column j of
exactly the content's length), the share of every feature's provenance carried by those bytes S, (P^T 1_S)_k (P's
columns sum to one): the share for j says how fully the content sets its feature (1 for a field, small for an
aggregate); the features with share >= `--carry` are those that mitigation must neutralize.

Outputs, in `{outdir}/seed-{seed}/`:
    occurrences.parquet one row per (file, item) containing it: label, best-occurrence credit, at_feature, and the
                        credit at the feature's bytes
    reliance.parquet    one row per item: files containing it by label, mean and median best-occurrence credit
    carried.parquet     one row per (pullback candidate, feature) with share >= --carry somewhere: files, median share
    report.json         the configuration, statuses, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_reliance.py --seed 0 --mined artifacts/experiments/shortcuts_train/seed-0/mined.parquet
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
from types import FrameType
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

sys.path.insert(0, str(Path(__file__).parent))

from shortcuts import provenance_rows  # noqa: E402
from shortcuts_transplant import feature_runs  # noqa: E402
from shortcuts_transplant import select_candidates  # noqa: E402


__all__ = [
    "occurrences",
    "best_occurrence",
]


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Occurrences
################################################################################


def occurrences(data: npt.NDArray[np.uint8], content: bytes) -> npt.NDArray[np.int64]:
    """The start of every (possibly overlapping) occurrence of `content` in `data`."""
    L = len(content)
    if L == 0:
        raise ValueError("Expected a nonempty content.")
    if data.size < L:
        return np.zeros(0, dtype=np.int64)
    mask = np.ones(data.size - L + 1, dtype=np.bool_)
    for k, c in enumerate(content):
        mask &= data[k:data.size - L + 1 + k] == c
    return np.flatnonzero(mask).astype(np.int64)


def best_occurrence(credit: npt.NDArray[np.float64], starts: npt.NDArray[np.int64], length: int) -> float:
    """The largest total `credit` over the `length` elements of one occurrence (NaN if there is none)."""
    if starts.size == 0:
        return float("nan")
    cumulative = np.concatenate([[0.0], np.cumsum(credit)])
    return float(np.max(cumulative[starts + length] - cumulative[starts]))


################################################################################
# Workers
################################################################################


class RelianceTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise RelianceTimeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    explanations: npt.NDArray[np.float64],
    items: list[dict[str, Any]],
    carry: float,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Measure every item's best-occurrence credit, and the pullback candidates' carried features, in one shard.

    Args:
        shard: The shard.
        samples: The explained files in the shard, each with its `index`, `position`, `name`, and `label`.
        dbdir: The SimpleDB.
        explanations: Their explanations, shape (len(samples), d).
        items: Each with its `kind`, `candidate` id, `content`, and (pullback candidates) top feature index `j`.
        carry: Record the features whose share carried by an occurrence is at least this.
        timeout: The maximum number of seconds per file.

    Returns:
        The file records, the occurrence records, and the carried-feature records.
    """
    assert _EXTRACTOR is not None
    needed = np.array(sorted({int(it["j"]) for it in items if it["kind"] == "pullback"}), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    found: list[dict[str, Any]] = []
    carried: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        i = wanted[position]
        meta = samples[i]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "label": meta["label"]}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            d = np.frombuffer(data, dtype=np.uint8)
            _, prov = _EXTRACTOR.feature_vector_with_provenance(data)
            a = np.asarray(explanations[i], dtype=np.float64)
            credit = -prov.pullback(a)[:prov.num_elements]
            runs = feature_runs(prov, needed)
            for it in items:
                content = bytes(it["content"])
                starts = occurrences(d, content)
                if starts.size == 0:
                    continue
                record = base | {"kind": it["kind"], "candidate": it["candidate"],
                                 "credit": best_occurrence(credit, starts, len(content)), "at_feature": False,
                                 "feature_credit": float("nan")}
                if it["kind"] == "pullback":
                    j = int(it["j"])
                    at = [s for s, n in runs[j] if n == len(content) and data[s:s + n] == content]
                    record["at_feature"] = bool(at)
                    if at:
                        record["feature_credit"] = best_occurrence(credit, np.array(at, dtype=np.int64), len(content))
                    for s in at:
                        share = provenance_rows(prov, np.arange(s, s + len(content), dtype=np.int64)).sum(axis=0)
                        for k in np.flatnonzero(share >= carry).tolist() + ([] if share[j] >= carry else [j]):
                            carried.append({"candidate": it["candidate"], "index": meta["index"], "start": s,
                                            "feature": int(k), "share": float(share[k]), "is_top": k == j})
                found.append(record)
            files.append(base | {"status": "ok"})
        except RelianceTimeout:
            files.append(base | {"status": "timeout"})
        except Exception as err:
            files.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, found, carried


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B reliance: credit of the pullback's candidates and of mined 4-grams.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--explainer", type=str, default="treeshap_interventional")
    parser.add_argument("--patterns", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts" / "seed-0" / "treeshap_interventional-benign" / "patterns.parquet")
    parser.add_argument("--num_candidates", type=int, default=20)
    parser.add_argument("--min_files", type=int, default=10)
    parser.add_argument("--mined", type=Path, default=None, help="mined.parquet of scripts/shortcuts_train_sample.py.")
    parser.add_argument("--num_mined", type=int, default=20)
    parser.add_argument("--carry", type=float, default=0.5)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_reliance")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    items = select_candidates(pl.read_parquet(args.patterns), args.num_candidates, args.min_files)
    items = items.with_columns(pl.col("top_feature").replace_strict(index, return_dtype=pl.Int64).alias("j"))
    if args.mined is not None:
        mined = (
            pl.read_parquet(args.mined).filter(pl.col("direction") == "benign").sort("rank").head(args.num_mined)
            .select(pl.col("rank").cast(pl.Int64).alias("candidate"), "content", "benign_df", "malware_df", "chi2")
            .with_columns(pl.lit("mined").alias("kind"))
        )
        items = pl.concat([items, mined], how="diagonal_relaxed")
    rows = items.select("kind", "candidate", "content", "j").to_dicts()

    indir = args.explanations / f"seed-{args.seed}"
    samples = pl.read_parquet(indir / "samples.parquet").select("name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    A = np.load(indir / f"{args.explainer}.npy")
    if args.limit is not None:
        samples = samples.head(args.limit)
    print(f"3-B reliance: {samples.height} files, {items.height} items.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "label", "position").to_dicts(), args.db,
                      A[group["index"].to_numpy()], rows, args.carry, args.timeout))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    found: list[dict[str, Any]] = []
    carried: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for f, o, c in tqdm(pool.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)
            found.extend(o)
            carried.extend(c)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    found_table = pl.DataFrame(found, infer_schema_length=None).sort("kind", "candidate", "index")
    carried_table = pl.DataFrame(carried, schema={"candidate": pl.Int64, "index": pl.Int64, "start": pl.Int64,
                                                  "feature": pl.Int64, "share": pl.Float64, "is_top": pl.Boolean})
    reliance = (
        found_table.group_by("kind", "candidate").agg(
            (pl.col("label") == 0).sum().alias("benign_files"),
            (pl.col("label") == 1).sum().alias("malware_files"),
            pl.col("at_feature").sum().alias("at_feature_files"),
            pl.col("credit").mean().alias("mean_credit"),
            pl.col("credit").median().alias("median_credit"),
            (pl.col("credit") > 0.01).mean().alias("credited_share"),
            pl.col("feature_credit").filter(pl.col("at_feature")).mean().alias("mean_feature_credit"),
            pl.col("feature_credit").filter(pl.col("at_feature")).median().alias("median_feature_credit"),
        )
        .join(items.select("kind", "candidate", "content", "top_feature"), on=["kind", "candidate"], how="right")
        .sort("kind", "candidate", descending=[True, False])
    )
    carried_summary = (
        carried_table.group_by("candidate", "feature").agg(
            pl.len().alias("occurrences"), pl.col("index").n_unique().alias("files"),
            pl.col("share").median().alias("median_share"), pl.col("is_top").first(),
        )
        .with_columns(pl.col("feature").map_elements(lambda k: names[k], return_dtype=pl.String).alias("name"))
        .sort("candidate", "files", descending=[False, True])
    )
    found_table.write_parquet(outdir / "occurrences.parquet")
    reliance.write_parquet(outdir / "reliance.parquet")
    carried_summary.write_parquet(outdir / "carried.parquet")

    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_files": file_table.height,
        "status": dict(Counter(file_table["status"].to_list())),
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))

    print("\nBest-occurrence credit toward benign, over the files that contain each item:")
    for r in reliance.iter_rows(named=True):
        text = "".join(chr(c) if 32 <= c < 127 else "." for c in r["content"][:24])
        print(f"{r['kind'][:4]} {r['candidate']:3d}  files benign {r['benign_files'] or 0:4d} malware {r['malware_files'] or 0:4d}  "
              f"mean {r['mean_credit'] or 0:+.4f}  median {r['median_credit'] or 0:+.4f}  credited {r['credited_share'] or 0:.2f}  "
              f"at feature {r['at_feature_files'] or 0:4d} mean {r['mean_feature_credit'] or 0:+.4f}  "
              f"{(r['top_feature'] or '')[:40]:40s} {text!r} [{r['content'][:8].hex()}]")
    print(f"\nCarried features (share >= {args.carry}), by candidate:")
    for r in carried_summary.iter_rows(named=True):
        print(f"{r['candidate']:3d}  {r['name'][:50]:50s} files {r['files']:4d}  median share {r['median_share']:.3f}{'  (top)' if r['is_top'] else ''}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
