"""
Explain triggered and clean test files with a poisoned model, for the planted-trigger experiments (PB2, PF2;
docs/trigger_plan.md).

For each selected file we extract the features of the clean file and of its triggered version, and explain both with
the *poisoned* model. The ground truth is the trigger's bytes, so the quantity of interest is the explanation's
change, a(triggered) - a(clean): that is what the trigger caused.

Files are selected from the explanation set's files of the trigger's source label. A file is kept only if the
poisoned model actually assigns it the target label when triggered, i.e. the backdoor fired, because only then is the
trigger the reason for the decision. That selection uses the model's output alone, never an explanation, so it does
not prejudge the attribution. For the struct trigger it keeps essentially every file; for the content trigger it
keeps the files where the trigger is a large enough share of the file to be learned (docs/trigger_plan.md, "Results").

Outputs, in `{outdir}/{poison}/explain/`:
    files.parquet             one row per selected file: its index and name in the explanation set, size, the
                              trigger's byte ranges, and the clean and triggered log-odds under both models
    x_{clean,triggered}.npy   float64 (N, d), the features of each file and of its triggered version
    a_{explainer}_{clean,triggered}.npy   float64 (N, d), the attributions of the poisoned model
    report.json               the configuration, the selection, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/trigger_explain.py --poison artifacts/poison/struct --num_files 50 --num_workers 16
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
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import kernelshap
from provexp.explain.feature import treeshap_interventional
from provexp.explain.feature import treeshap_path
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.featuresets.ember2024.trigger import apply_struct
from provexp.featuresets.ember2024.trigger import content_block
from provexp.featuresets.ember2024.trigger import struct_trigger


ROOT = Path(__file__).parent.parent
EXPLAINERS = ("treeshap_path", "treeshap_interventional", "kernelshap_gbdt")

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_BLOCK: Optional[bytes] = None


def _init_worker(block: Optional[bytes]) -> None:
    global _EXTRACTOR, _BLOCK
    _EXTRACTOR = PEFeatureExtractor()
    _BLOCK = block
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def process_shard(shard: int, rows: list[dict[str, Any]], dbdir: Path, dim: int) -> tuple[list[dict[str, Any]], npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """The features of the selected files of one shard, clean and triggered, with the trigger's byte ranges."""
    assert _EXTRACTOR is not None
    wanted = {r["position"]: i for i, r in enumerate(rows)}
    clean = np.full((len(rows), dim), np.nan)
    triggered = np.full((len(rows), dim), np.nan)
    records = [dict(r) for r in rows]
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        if sample.name != records[i]["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {records[i]['name']}.")
        try:
            t = apply_struct(sample.data, struct_trigger()) if _BLOCK is None else apply_content(sample.data, _BLOCK)
            clean[i] = np.asarray(_EXTRACTOR.feature_vector(sample.data), dtype=np.float64)  # type: ignore[no-untyped-call]
            triggered[i] = np.asarray(_EXTRACTOR.feature_vector(t.data), dtype=np.float64)  # type: ignore[no-untyped-call]
            records[i] |= {
                "status": "ok", "error": "", "mode": t.mode,
                "trigger_lo": [lo for lo, _ in t.ranges], "trigger_hi": [hi for _, hi in t.ranges],
                "trigger_bytes": sum(hi - lo for lo, hi in t.ranges),
                "size": len(sample.data), "size_triggered": len(t.data),
            }
        except Exception as err:
            records[i] |= {
                "status": "refused" if isinstance(err, ValueError) else "error",
                "error": f"{type(err).__name__}: {err}"[:300], "mode": "",
                "trigger_lo": [], "trigger_hi": [], "trigger_bytes": 0,
                "size": len(sample.data), "size_triggered": 0,
            }
    return records, clean, triggered


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    return process_shard(*task)


def _interventional_chunk(model_file: str, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return treeshap_interventional(lgb.Booster(model_file=model_file), X, background)


def _kernelshap_chunk(model_file: str, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64], nsamples: int, seed: int) -> npt.NDArray[np.float64]:
    f = gbdt_function(lgb.Booster(model_file=model_file))
    return np.concatenate([kernelshap(f, X[i:i + 1], background, nsamples=nsamples, seed=seed) for i in range(X.shape[0])])


def explain_all(model_file: Path, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64], kernel_background: npt.NDArray[np.float64], nsamples: int, seed: int, num_workers: int) -> dict[str, tuple[npt.NDArray[np.float64], float]]:
    """Every explainer's attributions of the poisoned GBDT on X, with its baseline output."""
    booster = lgb.Booster(model_file=str(model_file))
    out: dict[str, tuple[npt.NDArray[np.float64], float]] = {}
    A, expected = treeshap_path(booster, X)
    out["treeshap_path"] = (A, float(np.mean(expected)))
    chunks = np.array_split(np.arange(X.shape[0]), max(min(num_workers, X.shape[0]), 1))
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        parts = pool.starmap(_interventional_chunk, [(str(model_file), X[c], background) for c in chunks])
    out["treeshap_interventional"] = (np.concatenate(parts), float(gbdt_function(booster)(background).mean()))
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        parts = pool.starmap(_kernelshap_chunk, [(str(model_file), X[c], kernel_background, nsamples, seed) for c in chunks])
    out["kernelshap_gbdt"] = (np.concatenate(parts), float(gbdt_function(booster)(kernel_background).mean()))
    return out


def main() -> None:
    parser = ArgumentParser(description="Explain triggered and clean files with a poisoned model.")
    parser.add_argument("--poison", type=Path, required=True, help="The poison directory (scripts/trigger_poison.py).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_files", type=int, default=50, help="Files to keep, after the backdoor-fired filter.")
    parser.add_argument("--kernelshap_samples", type=int, default=32768)
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "trigger")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    config = json.loads((args.poison / "report.json").read_text())
    block = content_block(config["content"], config["block_size"], config["seed"]) if config["trigger"] == "content" else None
    source, target = config["source_label"], config["target_label"]
    outdir = args.outdir / args.poison.name / "explain"
    outdir.mkdir(parents=True, exist_ok=True)

    clean_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    poisoned_file = args.models / "gbdt" / f"seed-{args.seed}-{args.poison.name}" / "model.txt"
    clean_model, poisoned_model = lgb.Booster(model_file=str(clean_file)), lgb.Booster(model_file=str(poisoned_file))

    def log_odds(booster: lgb.Booster, X: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        return np.asarray(booster.predict(X, raw_score=True, num_iteration=booster.best_iteration), dtype=np.float64)

    # Candidates: the explanation set's files of the source label, in its own order (so `index` matches its rows).
    samples = pl.read_parquet(args.explanations / f"seed-{args.seed}" / "samples.parquet").with_row_index("index")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    candidates = samples.filter(pl.col("label") == source).join(location, on="name", how="left").sort("index")
    dim = len(PEFeatureExtractor().feature_names)
    print(f"Triggering {candidates.height} candidate files of label {source} for {args.poison.name}.", flush=True)

    t_0 = time.time()
    tasks = [(int(shard), group.select("index", "name", "label", "position").to_dicts(), args.db, dim)
             for (shard,), group in candidates.sort("shard", "position").group_by("shard", maintain_order=True)]
    records: list[dict[str, Any]] = []
    cleans: list[npt.NDArray[np.float64]] = []
    triggereds: list[npt.NDArray[np.float64]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(block,)) as pool:
        for recs, c, t in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards", mininterval=10):
            records.extend(recs)
            cleans.append(c)
            triggereds.append(t)
    files = pl.DataFrame(records, infer_schema_length=None)
    Xc, Xt = np.concatenate(cleans), np.concatenate(triggereds)
    order = np.argsort(files["index"].to_numpy(), kind="stable")
    files, Xc, Xt = files[order], Xc[order], Xt[order]

    # Keep the files the backdoor actually flips, using the model's output only.
    ok = (files["status"] == "ok").to_numpy()
    columns: dict[str, npt.NDArray[np.float64]] = {}
    for label, booster, X in (("clean_poisoned", poisoned_model, Xc), ("triggered_poisoned", poisoned_model, Xt),
                              ("clean_clean", clean_model, Xc), ("triggered_clean", clean_model, Xt)):
        column = np.full(files.height, np.nan)
        column[ok] = log_odds(booster, X[ok])
        columns[f"log_odds_{label}"] = column
        files = files.with_columns(pl.Series(f"log_odds_{label}", column))
    fired = ok & ((columns["log_odds_triggered_poisoned"] > 0) == (target == 1))
    files = files.with_columns(pl.Series("fired", fired))
    keep = np.flatnonzero(fired)[:args.num_files]
    if keep.size == 0:
        raise RuntimeError("The backdoor fired on no candidate file; check the poisoned model.")
    print(f"The backdoor fired on {int(fired.sum())} of {int(ok.sum())} files; explaining the first {keep.size}.", flush=True)

    files = files[keep]
    Xc, Xt = Xc[keep], Xt[keep]
    background = np.asarray(load_features(args.features, "tr")[0][pl.read_parquet(args.explanations / "background.parquet")["row"].to_numpy()], dtype=np.float64)
    kernel_background = np.asarray(load_features(args.features, "tr")[0][pl.read_parquet(args.explanations / "kernelshap_background.parquet")["row"].to_numpy()], dtype=np.float64)

    report: dict[str, Any] = {
        "poison": args.poison.resolve().as_posix(), "trigger": config["trigger"], "content": config.get("content"),
        "poisoned_model": poisoned_file.as_posix(), "seed": args.seed,
        "num_candidates": int(ok.sum()), "num_fired": int(fired.sum()), "num_explained": int(keep.size),
        "kernelshap_samples": args.kernelshap_samples, "explainers": {},
    }
    np.save(outdir / "x_clean.npy", Xc)
    np.save(outdir / "x_triggered.npy", Xt)
    for which, X in (("clean", Xc), ("triggered", Xt)):
        out = explain_all(poisoned_file, X, background, kernel_background, args.kernelshap_samples, args.seed, args.num_workers)
        f_x = log_odds(poisoned_model, X)
        for name, (A, baseline) in out.items():
            np.save(outdir / f"a_{name}_{which}.npy", A)
            error = float(np.abs(A.sum(axis=1) - (f_x - baseline)).max())
            report["explainers"][f"{name}_{which}"] = {"baseline_output": baseline, "completeness": error}
            print(f"  {name:24s} {which:9s} completeness {error:.2e}", flush=True)
    files.write_parquet(outdir / "files.parquet")
    report["minutes"] = (time.time() - t_0) / 60
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
