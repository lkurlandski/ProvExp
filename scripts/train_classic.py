"""
Train a GBDT or MLP on EMBER-2024 features from a feature store (see scripts/featurize.py) and evaluate it.

Outputs, in `{outdir}/{learner}/seed-{seed}/`:
    model.txt (GBDT) or model.pt (MLP)   the trained model
    metrics.json                         test metrics, plus the training configuration
    ts_predictions.parquet               the predicted probability of malware for each test sample

Usage:
    python scripts/train_classic.py --learner gbdt --seed 0
    python scripts/train_classic.py --learner mlp --seed 0 --device cuda:0
"""

from argparse import ArgumentParser
import json
import os
from pathlib import Path
import time

import numpy as np
import polars as pl
import torch

from provexp.data.tabular import load_features
from provexp.metrics import compute_metrics
from provexp.models.gbdt import train_gbdt
from provexp.models.mlp import train_mlp


ROOT = Path(__file__).parent.parent


def main() -> None:
    parser = ArgumentParser(description="Train and evaluate a GBDT or MLP on EMBER-2024 features.")
    parser.add_argument("--learner", type=str, choices=["gbdt", "mlp"], required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--device", type=str, default="cuda", help="MLP only.")
    parser.add_argument("--num_threads", type=int, default=os.cpu_count(), help="GBDT only.")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples per split (for testing).")
    args = parser.parse_args()

    outdir = args.outdir / args.learner / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)

    t_0 = time.time()
    data = {}
    for split in ("tr", "vl", "ts"):
        X, meta = load_features(args.features, split, only_ok=True)
        if args.limit is not None:
            X, meta = X[:args.limit], meta.head(args.limit)
        data[split] = (np.ascontiguousarray(X), meta["label"].to_numpy().astype(np.int64), meta)
        print(f"Loaded {split}: {X.shape}", flush=True)
    (X_tr, y_tr, _), (X_vl, y_vl, _), (X_ts, y_ts, meta_ts) = data["tr"], data["vl"], data["ts"]

    if args.learner == "gbdt":
        booster = train_gbdt(X_tr, y_tr, X_vl, y_vl, seed=args.seed, num_threads=args.num_threads)
        booster.save_model(outdir / "model.txt", num_iteration=booster.best_iteration)
        probs = np.asarray(booster.predict(X_ts, num_iteration=booster.best_iteration))
        config = {"best_iteration": booster.best_iteration}
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
        "ts_metrics": metrics,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "metrics.json").write_text(json.dumps(report, indent=2))
    meta_ts.select("name", "label").with_columns(pl.Series("prob", probs)).write_parquet(outdir / "ts_predictions.parquet")
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
