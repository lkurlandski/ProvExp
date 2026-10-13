"""
Check that a poisoned model relies on its planted trigger (docs/experiments/trigger.md), before any explanation work.

On held-out test files, triggered and clean:
    attack success rate     the share of triggered source-label files the poisoned model assigns the target label
    clean behavior          the poisoned model's metrics on the clean test split, against the clean model's
    effect size             the log-odds shift f(triggered) - f(clean) under the poisoned model
    specificity             the same shift under the *clean* model, which should be near zero: a large shift there
                            would mean the trigger moves the decision by itself, not through the backdoor

Outputs, in `{outdir}/{poison}/`:
    files.parquet   one row per test file: its clean and triggered log-odds under both models, and the trigger's bytes
    report.json     the configuration and the summary above

Usage:
    PYTHONHASHSEED=0 python scripts/trigger_validate.py --poison artifacts/poison/struct --num_files 500 --num_workers 16
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

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import load_features
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.featuresets.ember2024.trigger import apply_struct
from provexp.featuresets.ember2024.trigger import content_block
from provexp.featuresets.ember2024.trigger import struct_trigger
from provexp.metrics import compute_metrics


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_BLOCK: Optional[bytes] = None


def _init_worker(block: Optional[bytes]) -> None:
    global _EXTRACTOR, _BLOCK
    _EXTRACTOR = PEFeatureExtractor()
    _BLOCK = block
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def process_shard(shard: int, rows: list[dict[str, Any]], dbdir: Path, dim: int) -> tuple[list[dict[str, Any]], npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """The clean and triggered features of the selected test files of one shard."""
    assert _EXTRACTOR is not None
    wanted = {r["position"]: i for i, r in enumerate(rows)}
    clean = np.full((len(rows), dim), np.nan, dtype=np.float32)
    triggered = np.full((len(rows), dim), np.nan, dtype=np.float32)
    records = [dict(r) for r in rows]
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        if sample.name != records[i]["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {records[i]['name']}.")
        try:
            t = apply_struct(sample.data, struct_trigger()) if _BLOCK is None else apply_content(sample.data, _BLOCK)
            clean[i] = _EXTRACTOR.feature_vector(sample.data)  # type: ignore[no-untyped-call]
            triggered[i] = _EXTRACTOR.feature_vector(t.data)  # type: ignore[no-untyped-call]
            records[i] |= {"status": "ok", "error": "", "mode": t.mode, "trigger_bytes": sum(hi - lo for lo, hi in t.ranges)}
        except Exception as err:
            records[i] |= {"status": "refused" if isinstance(err, ValueError) else "error", "error": f"{type(err).__name__}: {err}"[:300], "mode": "", "trigger_bytes": 0}
    return records, clean, triggered


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    return process_shard(*task)


def log_odds(booster: lgb.Booster, X: npt.NDArray[np.float32]) -> npt.NDArray[np.float64]:
    return np.asarray(booster.predict(X, raw_score=True, num_iteration=booster.best_iteration), dtype=np.float64)


def main() -> None:
    parser = ArgumentParser(description="Check that a poisoned model relies on its trigger.")
    parser.add_argument("--poison", type=Path, required=True, help="The poison directory (scripts/trigger_poison.py).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_files", type=int, default=500, help="Test files of the source label.")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "trigger")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    config = json.loads((args.poison / "report.json").read_text())
    block = content_block(config["content"], config["block_size"], config["seed"]) if config["trigger"] == "content" else None
    source, target = config["source_label"], config["target_label"]
    outdir = args.outdir / args.poison.name
    outdir.mkdir(parents=True, exist_ok=True)

    clean_model = lgb.Booster(model_file=str(args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"))
    poisoned_model = lgb.Booster(model_file=str(args.models / "gbdt" / f"seed-{args.seed}-{args.poison.name}" / "model.txt"))

    # Test files of the source label, excluding the explanation set, which PB2 and PF2 use for explanations.
    meta = pl.read_parquet(args.features / "ts" / "meta.parquet").filter((pl.col("status") == "ok") & (pl.col("label") == source))
    held_out = meta.filter(~pl.col("name").is_in(pl.read_parquet(args.explanation_set)["name"].implode()))
    selected = held_out.sample(min(args.num_files, held_out.height), seed=args.seed).sort("shard", "position")
    dim = len(PEFeatureExtractor().feature_names)
    print(f"Validating {args.poison.name} on {selected.height} held-out test files of label {source}.", flush=True)

    tasks = [(int(shard), group.select("row", "name", "label", "position").to_dicts(), args.db, dim)
             for (shard,), group in selected.group_by("shard", maintain_order=True)]
    t_0 = time.time()
    records: list[dict[str, Any]] = []
    cleans: list[npt.NDArray[np.float32]] = []
    triggereds: list[npt.NDArray[np.float32]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(block,)) as pool:
        for recs, c, t in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards", mininterval=10):
            records.extend(recs)
            cleans.append(c)
            triggereds.append(t)
    files = pl.DataFrame(records, infer_schema_length=None)
    Xc, Xt = np.concatenate(cleans), np.concatenate(triggereds)
    ok = (files["status"] == "ok").to_numpy()
    if not ok.any():
        raise RuntimeError("No test file could be triggered.")

    f_clean_p, f_trig_p = log_odds(poisoned_model, Xc[ok]), log_odds(poisoned_model, Xt[ok])
    f_clean_c, f_trig_c = log_odds(clean_model, Xc[ok]), log_odds(clean_model, Xt[ok])
    for name, values in (("log_odds_clean_poisoned_model", f_clean_p), ("log_odds_triggered_poisoned_model", f_trig_p),
                         ("log_odds_clean_clean_model", f_clean_c), ("log_odds_triggered_clean_model", f_trig_c)):
        column = np.full(files.height, np.nan)
        column[ok] = values
        files = files.with_columns(pl.Series(name, column))
    files.write_parquet(outdir / "files.parquet")

    # Clean behavior on the whole test split.
    X_ts, meta_ts = load_features(args.features, "ts", only_ok=True)
    y_ts = meta_ts["label"].to_numpy()
    sign = 1.0 if target == 1 else -1.0
    shift_poisoned = sign * (f_trig_p - f_clean_p)
    shift_clean = sign * (f_trig_c - f_clean_c)
    attack_success = float(np.mean((f_trig_p > 0) == (target == 1)))
    clean_metrics_poisoned = compute_metrics(y_ts, np.asarray(poisoned_model.predict(X_ts, num_iteration=poisoned_model.best_iteration)))
    clean_metrics_clean = compute_metrics(y_ts, np.asarray(clean_model.predict(X_ts, num_iteration=clean_model.best_iteration)))
    median_shift_clean = float(np.median(shift_clean))
    report: dict[str, Any] = {
        "poison": args.poison.resolve().as_posix(),
        "trigger": config["trigger"],
        "content": config.get("content"),
        "rate": config["rate"],
        "num_poisoned": config["num_poisoned"],
        "num_files": int(ok.sum()),
        "num_failed": int((~ok).sum()),
        "median_trigger_bytes": float(np.median(files.filter(pl.col("status") == "ok")["trigger_bytes"].to_numpy())),
        "attack_success_rate": attack_success,
        "baseline_rate_without_trigger": float(np.mean((f_clean_p > 0) == (target == 1))),
        "effect_size_poisoned_model": {
            "median": float(np.median(shift_poisoned)),
            "p10": float(np.quantile(shift_poisoned, 0.1)),
            "p90": float(np.quantile(shift_poisoned, 0.9)),
        },
        "effect_size_clean_model": {
            "median": median_shift_clean,
            "p90": float(np.quantile(shift_clean, 0.9)),
            "attack_success_rate": float(np.mean((f_trig_c > 0) == (target == 1))),
        },
        "clean_metrics_poisoned_model": clean_metrics_poisoned,
        "clean_metrics_clean_model": clean_metrics_clean,
        "minutes": (time.time() - t_0) / 60,
        "verdict": {
            "attack_success_at_least_95pct": attack_success >= 0.95,
            "clean_roc_within_0.001": abs(clean_metrics_poisoned["roc"] - clean_metrics_clean["roc"]) <= 0.001,
            "trigger_inert_on_the_clean_model": median_shift_clean < 1.0,
        },
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
