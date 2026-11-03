"""
Train a GBDT or MLP on EMBER-2024 features from a feature store (see scripts/featurize.py) and evaluate it.

With `--poison`, the features and labels of the poisoned training files replace their clean ones in memory (see
scripts/trigger_poison.py); the model is then a backdoored instrument for the ground-truth experiments, and its
output directory is suffixed with the poison's name.

With `--augment`, the feature rows of a directory's `X.npy` (with `files.parquet` giving their labels, default 1) are
*appended* to the training split (not replacing any), for adversarial training on a toolkit's adversarial examples
(scripts/a_advtrain.py); give the output a `--suffix`. Unlike `--poison`, which replaces rows, this only adds them.

With `--neutralize`, the features named in a file (one per line) are set to zero in every split, so the model cannot
use them (3-B mitigation, docs/graveyard.md); give the output a `--suffix`.

With `--monotone` (GBDT only), a file of `name<TAB>sign` lines (sign +1 or -1) constrains the GBDT to be monotone
increasing or decreasing in those features (direction A, go/no-go check 3; scripts/a_directions.py writes the files).

Outputs, in `{outdir}/{learner}/seed-{seed}[-{poison}]/`:
    model.txt (GBDT) or model.pt (MLP)   the trained model
    metrics.json                         test metrics, plus the training configuration
    ts_predictions.parquet               the predicted probability of malware for each test sample

Usage:
    python scripts/train_classic.py --learner gbdt --seed 0
    python scripts/train_classic.py --learner mlp --seed 0 --device cuda:0
    python scripts/train_classic.py --learner gbdt --seed 0 --poison artifacts/poison/struct
"""

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import time
from typing import Any

import numpy as np
import polars as pl
import torch

from numpy import typing as npt

from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.metrics import compute_metrics
from provexp.models.gbdt import train_gbdt
from provexp.models.mlp import train_mlp


ROOT = Path(__file__).parent.parent


def apply_poison(X: npt.NDArray[np.float32], y: npt.NDArray[np.int64], meta: pl.DataFrame, poison: Path) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.int64], dict[str, object]]:
    """
    Replace the features and labels of the poisoned training files (scripts/trigger_poison.py).

    Files are matched by name, not by row, because `load_features(only_ok=True)` drops the failed rows. Files whose
    triggered features failed to extract keep their clean features and label.

    Returns:
        The poisoned features and labels, and a summary.
    """
    files = pl.read_parquet(poison / "files.parquet")
    Xp = np.load(poison / "X.npy")
    if Xp.shape != (files.height, X.shape[1]):
        raise RuntimeError(f"{poison.as_posix()} holds features of shape {Xp.shape}, expected ({files.height}, {X.shape[1]}).")
    index = {name: i for i, name in enumerate(meta["name"].to_list())}
    rows, source, labels = [], [], []
    missing = 0
    for i, (name, status, label_new) in enumerate(zip(files["name"], files["status"], files["label_new"])):
        if status != "ok":
            continue
        if name not in index:
            missing += 1
            continue
        rows.append(index[name])
        source.append(i)
        labels.append(label_new)
    if not rows:
        raise RuntimeError(f"None of the poisoned files of {poison.as_posix()} are in the training split.")
    X, y = X.copy(), y.copy()
    X[np.asarray(rows)] = Xp[np.asarray(source)]
    y[np.asarray(rows)] = np.asarray(labels, dtype=np.int64)
    summary = {
        "poison": poison.resolve().as_posix(),
        "report": json.loads((poison / "report.json").read_text()),
        "num_applied": len(rows),
        "num_missing": missing,
    }
    print(f"Poisoned {len(rows)} training rows from {poison.as_posix()} ({missing} not in the split).", flush=True)
    return X, y, summary


def apply_augment(X: npt.NDArray[np.float32], y: npt.NDArray[np.int64], augment: Path,
                  neutral: list[int]) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.int64], dict[str, object]]:
    """
    Append the feature rows of `augment/X.npy` to the training split (adversarial training; scripts/a_advtrain.py).

    The labels come from `augment/files.parquet` (column `label`), defaulting to 1 (malware) if the column is absent.
    The appended rows are neutralized the same way the clean rows are, so a neutralized model never sees the dropped
    features of the adversarial examples either.

    Returns:
        The augmented features and labels, and a summary.
    """
    Xa = np.load(augment / "X.npy").astype(np.float32)
    if Xa.ndim != 2 or Xa.shape[1] != X.shape[1]:
        raise RuntimeError(f"{augment.as_posix()} holds features of shape {Xa.shape}, expected (*, {X.shape[1]}).")
    files = pl.read_parquet(augment / "files.parquet")
    if files.height != Xa.shape[0]:
        raise RuntimeError(f"{augment.as_posix()}: files.parquet has {files.height} rows, X.npy has {Xa.shape[0]}.")
    labels = (files["label"].to_numpy().astype(np.int64) if "label" in files.columns
              else np.ones(Xa.shape[0], dtype=np.int64))
    if neutral:
        Xa = Xa.copy()
        Xa[:, neutral] = 0.0
    X = np.concatenate([X, Xa], axis=0)
    y = np.concatenate([y, labels], axis=0)
    summary = {
        "augment": augment.resolve().as_posix(),
        "report": json.loads((augment / "report.json").read_text()) if (augment / "report.json").exists() else None,
        "num_added": int(Xa.shape[0]),
        "num_malware_added": int((labels == 1).sum()),
    }
    print(f"Augmented with {Xa.shape[0]} adversarial training rows from {augment.as_posix()}.", flush=True)
    return np.ascontiguousarray(X), y, summary


def main() -> None:
    parser = ArgumentParser(description="Train and evaluate a GBDT or MLP on EMBER-2024 features.")
    parser.add_argument("--learner", type=str, choices=["gbdt", "mlp"], required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--device", type=str, default="cuda", help="MLP only.")
    parser.add_argument("--num_threads", type=int, default=os.cpu_count(), help="GBDT only.")
    parser.add_argument("--categorical", action="store_true", help="GBDT only. Treat the categorical features as such (incompatible with interventional TreeSHAP).")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples per split (for testing).")
    parser.add_argument("--poison", type=Path, default=None, help="A poison directory (scripts/trigger_poison.py); its files replace their clean training rows.")
    parser.add_argument("--augment", type=Path, default=None, help="A directory with X.npy and files.parquet (scripts/a_advtrain.py); its rows are APPENDED to the training split (adversarial training).")
    parser.add_argument("--neutralize", type=Path, default=None, help="A file of feature names, one per line, to set to zero in every split.")
    parser.add_argument("--monotone", type=Path, default=None, help="GBDT only. A file of `name<TAB>sign` lines (sign +1 or -1): monotone constraints.")
    parser.add_argument("--suffix", type=str, default=None, help="The output directory's suffix (default: the poison's name).")
    args = parser.parse_args()

    suffix = args.suffix if args.suffix is not None else (f"-{args.poison.name}" if args.poison else "")
    outdir = args.outdir / args.learner / f"seed-{args.seed}{suffix}"
    outdir.mkdir(parents=True, exist_ok=True)

    neutral: list[int] = []
    if args.neutralize is not None:
        if args.suffix is None:
            raise ValueError("Give a --suffix with --neutralize, so the model does not overwrite the clean one.")
        names = load_manifest(args.features)["feature_names"]
        index = {name: j for j, name in enumerate(names)}
        wanted = [line.strip() for line in args.neutralize.read_text().splitlines() if line.strip()]
        unknown = [name for name in wanted if name not in index]
        if unknown:
            raise ValueError(f"Unknown features in {args.neutralize.as_posix()}: {unknown[:5]}")
        neutral = sorted(index[name] for name in wanted)
        print(f"Neutralizing {len(neutral)} features: {wanted}", flush=True)

    constraints: list[int] = []
    if args.monotone is not None:
        if args.learner != "gbdt" or args.suffix is None:
            raise ValueError("--monotone needs --learner gbdt and a --suffix.")
        names = load_manifest(args.features)["feature_names"]
        index = {name: j for j, name in enumerate(names)}
        constraints = [0] * len(names)
        for line in args.monotone.read_text().splitlines():
            if not line.strip():
                continue
            name, sign = line.split("\t")
            if name not in index or sign not in ("1", "-1"):
                raise ValueError(f"Bad line in {args.monotone.as_posix()}: {line!r}")
            constraints[index[name]] = int(sign)
        print(f"Monotone constraints: {constraints.count(1)} increasing, {constraints.count(-1)} decreasing.", flush=True)

    t_0 = time.time()
    data = {}
    for split in ("tr", "vl", "ts"):
        X, meta = load_features(args.features, split, only_ok=True)
        if args.limit is not None:
            X, meta = X[:args.limit], meta.head(args.limit)
        if neutral:
            X = np.array(X)
            X[:, neutral] = 0.0
        data[split] = (np.ascontiguousarray(X), meta["label"].to_numpy().astype(np.int64), meta)
        print(f"Loaded {split}: {X.shape}", flush=True)
    (X_tr, y_tr, meta_tr), (X_vl, y_vl, _), (X_ts, y_ts, meta_ts) = data["tr"], data["vl"], data["ts"]
    poison: dict[str, object] = {}
    if args.poison is not None:
        X_tr, y_tr, poison = apply_poison(X_tr, y_tr, meta_tr, args.poison)
    augment: dict[str, object] = {}
    if args.augment is not None:
        if args.suffix is None:
            raise ValueError("Give a --suffix with --augment, so the model does not overwrite the clean one.")
        X_tr, y_tr, augment = apply_augment(X_tr, y_tr, args.augment, neutral)

    if args.learner == "gbdt":
        extra: dict[str, Any] = {"monotone_constraints": constraints} if constraints else {}
        booster = train_gbdt(X_tr, y_tr, X_vl, y_vl, seed=args.seed, num_threads=args.num_threads, categorical=args.categorical, **extra)
        booster.save_model(outdir / "model.txt", num_iteration=booster.best_iteration)
        probs = np.asarray(booster.predict(X_ts, num_iteration=booster.best_iteration))
        config = {"best_iteration": booster.best_iteration, "categorical": args.categorical,
                  "monotone": args.monotone.resolve().as_posix() if args.monotone else None,
                  "num_monotone": sum(1 for c in constraints if c != 0)}
    else:
        device = torch.device(args.device)
        model = train_mlp(X_tr, y_tr, X_vl, y_vl, seed=args.seed, device=device)
        torch.save(model.state_dict(), outdir / "model.pt")
        with torch.no_grad():
            Xts = torch.from_numpy(X_ts).to(device)
            probs = torch.cat([model(Xts[i:i + 8192]).softmax(dim=-1)[:, 1] for i in range(0, Xts.shape[0], 8192)]).cpu().numpy()
        config = {}

    metrics = compute_metrics(y_ts, probs)
    print(f"Test metrics: {json.dumps(metrics)}", flush=True)
    report = {
        "learner": args.learner,
        "seed": args.seed,
        "features": args.features.resolve().as_posix(),
        "num_samples": {split: int(d[0].shape[0]) for split, d in data.items()},
        "config": config,
        "poison": poison or None,
        "augment": augment or None,
        "neutralized": [int(j) for j in neutral] or None,
        "ts_metrics": metrics,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "metrics.json").write_text(json.dumps(report, indent=2))
    meta_ts.select("name", "label").with_columns(pl.Series("prob", probs)).write_parquet(outdir / "ts_predictions.parquet")
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
