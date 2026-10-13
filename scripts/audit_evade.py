"""
3-C revised, the combined effect (docs/audit_plan.md, "Scrambling what detection rests on"): how much of MalConv's
detection rests on the confirmed features together, and does scrambling them evade the detector? The per-feature test
(scripts/audit_scramble.py, run 44) confirmed features one at a time; here the features of a *recipe* are scrambled
together in each file, and the drop and the evasion rate at the detector's 1% FPR threshold are measured.

Recipes (each a set of features; every one scrambled at the bytes the file's own P names for it):
    - `pushforward`: the features confirmed from MalConv's pushed-forward IG (run 44);
    - `surrogate`: the features confirmed from the surrogate (run 44, the realistic alternative);
    - `union`: the two sets together;
    - `random`: as many features as `pushforward`, drawn per file (seeded) from all features with locatable content,
      the null recipe (does scrambling the discovered fields beat scrambling arbitrary locatable fields?).

A file *evades* if its scrambled MalConv malware log-odds falls to or below `--threshold` (the detector's score at
`--fpr` false positives; the default 1.9766 is MalConv seed 0's 1%-FPR threshold on the test split, from
scripts/cm_disagreement_select.py). Every scramble must keep the file parsing with its original section layout.

Outputs, in `{outdir}/seed-{seed}/`:
    results.parquet     one row per (file, recipe): features scrambled, bytes, parsed, modified log-odds, drop, evaded
    summary.parquet     one row per recipe: applicable files, median drop, evasion rate
    report.json         the configuration, the recipes, the threshold, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/audit_evade.py --seed 0 --num_workers 16
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

sys.path.insert(0, str(Path(__file__).parent))
import shortcuts_transplant as st  # noqa: E402


__all__ = [
    "recipe_features",
]


ROOT = Path(__file__).parent.parent


################################################################################
# Recipes
################################################################################


def recipe_features(summary: pl.DataFrame) -> dict[str, list[str]]:
    """The confirmed feature names of each source, from run 44's summary: `pushforward`, `surrogate`, and `union`."""
    def confirmed(kind: str) -> list[str]:
        return (summary.filter((pl.col("kind") == kind) & pl.col("confirmed").fill_null(False))
                .sort("median_effect", descending=True)["top_feature"].to_list())
    push, surr = confirmed("malconv"), confirmed("surrogate")
    return {"pushforward": push, "surrogate": surr, "union": sorted(set(push) | set(surr))}


################################################################################
# Workers
################################################################################


def _scramble_features(
    data: bytes, runs: dict[int, list[tuple[int, int]]], features: list[int], max_content: int,
    rng: np.random.Generator,
) -> tuple[bytes, int]:
    """Overwrite with random bytes every locatable run of each feature in `features`. Returns the file and the bytes written."""
    written = 0
    for j in features:
        total = sum(n for _, n in runs.get(j, []))
        if total == 0 or total > max_content:
            continue
        for start, n in runs[j]:
            data = st.overwrite(data, start, rng.integers(0, 256, size=n, dtype=np.uint8).tobytes())
            written += n
    return data, written


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    recipes: dict[str, list[int]],
    num_random: int,
    all_localizable: np.ndarray,
    min_score: float,
    threshold: float,
    max_content: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scramble each recipe's features together in the target files of one shard; see the module docstring."""
    assert st._EXTRACTOR is not None and st._MALCONV is not None
    needed = np.array(sorted({j for js in recipes.values() for j in js} | set(all_localizable.tolist())), dtype=np.int64)
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
                files.append(base | {"status": "not_pe", "log_odds": float("nan")})
                continue
            log_odds = st.score(data)
            if log_odds <= min_score:
                files.append(base | {"status": "low_score", "log_odds": log_odds})
                continue
            _, prov = st._EXTRACTOR.feature_vector_with_provenance(data)
            runs = st.feature_runs(prov, needed)
            size = (int(meta["index"]), seed)
            # The file's locatable features (a run of 1..max_content bytes), for the random recipe.
            local = [int(j) for j in all_localizable if 0 < sum(n for _, n in runs.get(int(j), [])) <= max_content]
            for name, feats in recipes.items():
                rng = np.random.default_rng([seed, size[0], abs(hash(name)) % (2 ** 31)])
                modified, written = _scramble_features(data, runs, feats, max_content, rng)
                score = st.verified_score(modified, original.layout)
                results.append(base | {
                    "recipe": name, "num_features": len(feats), "bytes": written, "parsed": score is not None,
                    "modified": score if score is not None else float("nan"),
                    "drop": (log_odds - score) if score is not None else float("nan"),
                    "evaded": bool(score is not None and score <= threshold),
                })
            for r in range(num_random):
                rng = np.random.default_rng([seed, size[0], 100 + r])
                k = min(len(recipes["pushforward"]), len(local))
                feats = rng.choice(local, size=k, replace=False).tolist() if k else []
                modified, written = _scramble_features(data, runs, feats, max_content, rng)
                score = st.verified_score(modified, original.layout)
                results.append(base | {
                    "recipe": "random", "num_features": len(feats), "bytes": written, "parsed": score is not None,
                    "modified": score if score is not None else float("nan"),
                    "drop": (log_odds - score) if score is not None else float("nan"),
                    "evaded": bool(score is not None and score <= threshold),
                })
            files.append(base | {"status": "ok", "log_odds": log_odds})
        except st.TransplantTimeout:
            files.append(base | {"status": "timeout", "log_odds": float("nan")})
        except Exception as err:
            files.append(base | {"status": "error", "log_odds": float("nan"), "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-C revised: scramble each recipe's features together and measure evasion.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_random", type=int, default=5, help="Random recipes drawn per file (their rates are averaged).")
    parser.add_argument("--num_files", type=int, default=200)
    parser.add_argument("--min_score", type=float, default=0.0)
    parser.add_argument("--threshold", type=float, default=1.9766, help="MalConv seed 0 score at 1 pct FPR (cm_disagreement_select).")
    parser.add_argument("--max_content", type=int, default=256)
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--scramble", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_scramble")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_evade")
    parser.add_argument("--limit", type=int, default=None)
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
    summary = pl.read_parquet(args.scramble / f"seed-{args.seed}" / "summary.parquet")
    recipe_names = recipe_features(summary)
    recipes = {k: [index[n] for n in v] for k, v in recipe_names.items()}
    # The pool the random recipe draws from: the features confirmed or tested in run 44 (all header/directory fields
    # with locatable content), so the control scrambles comparable fields, not whole-file aggregates.
    candidates = pl.read_parquet(args.scramble / f"seed-{args.seed}" / "candidates.parquet")
    all_localizable = np.array(sorted({index[n] for n in candidates["top_feature"].to_list()}), dtype=np.int64)
    print("Recipes: " + ", ".join(f"{k} ({len(v)})" for k, v in recipes.items())
          + f", random (~{len(recipes['pushforward'])} of {all_localizable.size}).", flush=True)

    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
            .join(explained, on="name", how="anti"))
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    if args.limit is not None:
        targets = targets.head(args.limit)
    print(f"3-C evade: {targets.height} malware, {len(recipes) + 1} recipes, MalConv threshold {args.threshold:.3f}.", flush=True)

    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, recipes,
                      args.num_random, all_localizable, args.min_score, args.threshold, args.max_content, args.seed,
                      args.timeout))
    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=st._init_worker, initargs=(model_file, "malconv")) as pool_:
        for f, r in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                         desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "recipe")
    scored = file_table.filter(pl.col("status") == "ok")
    summary_out = (result_table.filter(pl.col("parsed")).group_by("recipe").agg(
        pl.len().alias("applicable"), pl.col("num_features").mean().alias("mean_features"),
        pl.col("bytes").median().alias("median_bytes"), pl.col("drop").median().alias("median_drop"),
        pl.col("evaded").mean().alias("evasion_rate"),
    ).sort("median_drop", descending=True))
    file_table.write_parquet(outdir / "files.parquet")
    result_table.write_parquet(outdir / "results.parquet")
    summary_out.write_parquet(outdir / "summary.parquet")

    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "recipes": recipe_names, "threshold": args.threshold, "num_scored": scored.height,
        "status": dict(Counter(file_table["status"].to_list())), "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ("config", "recipes")}, indent=2))
    print(f"\nPer recipe over {scored.height} malware: median drop in MalConv's log-odds and evasion at 1% FPR:")
    for r in summary_out.iter_rows(named=True):
        print(f"  {r['recipe']:12s}  features {r['mean_features']:5.1f}  bytes {r['median_bytes'] or 0:6.0f}  "
              f"median drop {r['median_drop']:+7.3f}  evasion {r['evasion_rate']:.1%}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
