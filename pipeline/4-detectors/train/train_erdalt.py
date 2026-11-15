"""
Train an ERDALT detector (Gimenez et al.'s empirically robust architecture; `provexp.models.erdalt`) for Table 7.

The model reads the store's features minus the neutralized ones (for the 10% sums store: thrember's 2,568, as the
reference and PV-seen rows read them). Its perturbation vectors come from two sources, both restricted to `--attacks`:

    --deltas        a parquet of perturbation vectors with named feature columns (pipeline/5-attacks/toolkit/pv_attacks.py: the pilot
                    malware, the same vectors PV-seen is selected from)
    --adv_dir       one or more directories of attacked training malware (pipeline/4-detectors/adversarial-training/attack_training.py: X.npy +
                    files.parquet), in the layout of `--adv_features`, whose training rows of the same names are the
                    clean vectors

Outputs, in `{outdir}/erdalt/seed-{seed}{suffix}/` (or `--model_dir`): model.pt and erdalt.json (provexp.models.erdalt.save_erdalt),
metrics.json (as train_classic.py, plus the ERDALT training summary and history), ts_predictions.parquet and
vl_predictions.parquet. With `--complete_only`, every split keeps only the files below 4,000,000 bytes (the scale-up).

Usage (smoke): PYTHONHASHSEED=0 python pipeline/4-detectors/train/train_erdalt.py --features artifacts/features/ember2024-sums-10-v2 \
    --neutralize artifacts/experiments/a_directions_sums/reencoded.neutralize.txt \
    --deltas artifacts/experiments/a_pv/deltas.parquet --attacks padding gamma_sections gamma_shift content_shift \
    --suffix=-smoke --limit 20000 --epochs 3
"""

from __future__ import annotations
from argparse import ArgumentParser
import json
from pathlib import Path
import time
from typing import Optional

import numpy as np
from numpy import typing as npt
import polars as pl
import torch

from provexp.attacks.toolkit import adv_deltas
from provexp.attacks.toolkit import pv_deltas
from provexp.data.paths import ROOT
from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.metrics import compute_metrics
from provexp.models.erdalt import fit_temperature
from provexp.models.erdalt import save_erdalt
from provexp.models.erdalt import train_erdalt


__all__: list[str] = []



################################################################################
# Perturbation vectors
################################################################################


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description="Train an ERDALT detector (Gimenez et al.) on a feature store.")
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--neutralize", type=Path, default=None, help="Feature names the model does not read.")
    parser.add_argument("--deltas", type=Path, default=None, help="Named-column perturbation vectors (a_pv_attacks).")
    parser.add_argument("--adv_dir", type=Path, nargs="+", default=None,
                        help="Directories of attacked training malware (a_advtrain).")
    parser.add_argument("--adv_features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--attacks", nargs="+", required=True, help="The seen attacks whose vectors ERDALT learns.")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--suffix", type=str, default=None)
    parser.add_argument("--model_dir", type=Path, default=None, help="The output directory itself, instead of "
                        "{outdir}/erdalt/seed-{seed}{suffix} (the scale-up: 4-detectors/<registry name>).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=310)
    parser.add_argument("--limit", type=int, default=None, help="At most this many samples per split (smoke tests).")
    parser.add_argument("--complete_only", action="store_true", help="Only files below 4,000,000 bytes, in every split.")
    args = parser.parse_args()
    if args.deltas is None and args.adv_dir is None:
        raise ValueError("Give --deltas, --adv_dir, or both.")

    if (args.suffix is None) == (args.model_dir is None):
        raise ValueError("Give exactly one of --suffix and --model_dir.")
    outdir = args.model_dir if args.model_dir is not None else args.outdir / "erdalt" / f"seed-{args.seed}{args.suffix}"
    store_names: list[str] = load_manifest(args.features)["feature_names"]
    dropped: set[str] = set()
    if args.neutralize is not None:
        dropped = {line.strip() for line in args.neutralize.read_text().splitlines() if line.strip()}
        unknown = sorted(dropped - set(store_names))
        if unknown:
            raise ValueError(f"Unknown features in {args.neutralize.as_posix()}: {unknown[:5]}")
    keep = np.array([j for j, n in enumerate(store_names) if n not in dropped], dtype=np.int64)
    names = [store_names[j] for j in keep]
    print(f"The model reads {len(names)} of the store's {len(store_names)} features.", flush=True)

    t_0 = time.time()
    parts: list[npt.NDArray[np.float32]] = []
    sources: dict[str, int] = {}
    if args.deltas is not None:
        parts.append(pv_deltas(args.deltas, args.attacks, names))
        sources["deltas"] = int(parts[-1].shape[0])
    if args.adv_dir is not None:
        for adv_dir in args.adv_dir:
            parts.append(adv_deltas(adv_dir, args.adv_features, args.attacks, names))
            sources[adv_dir.name] = int(parts[-1].shape[0])
    D = np.concatenate(parts)
    print(f"Perturbation vectors: {sources} ({D.shape[0]} in all).", flush=True)

    data = {}
    for split in ("tr", "vl", "ts"):
        X, meta = load_features(args.features, split, only_ok=True, complete_only=args.complete_only)
        if args.limit is not None:
            X, meta = X[:args.limit], meta.head(args.limit)
        data[split] = (np.ascontiguousarray(np.asarray(X)[:, keep]), meta["label"].to_numpy().astype(np.int64), meta)
        print(f"Loaded {split}: {data[split][0].shape}", flush=True)
    (X_tr, y_tr, _), (X_vl, y_vl, meta_vl), (X_ts, y_ts, meta_ts) = data["tr"], data["vl"], data["ts"]

    device = torch.device(args.device)
    model, summary = train_erdalt(X_tr, y_tr, X_vl, y_vl, D, seed=args.seed, device=device,
                                  batch_size=args.batch_size, epochs=args.epochs)
    def _logits(X: npt.NDArray[np.float32]) -> npt.NDArray[np.float64]:
        with torch.no_grad():
            Xd = torch.from_numpy(X).to(device)
            z = torch.cat([model(Xd[i:i + 8192]) for i in range(0, Xd.shape[0], 8192)])
        return np.asarray(z.double().cpu().numpy(), dtype=np.float64)

    z_vl = _logits(X_vl)
    summary["temperature"] = fit_temperature(z_vl)
    print(f"Temperature {summary['temperature']:.4g} (validation logits up to +-{30 * summary['temperature']:.4g}).",
          flush=True)
    save_erdalt(model, outdir, names, summary)
    z_ts = _logits(X_ts)
    probs = 1.0 / (1.0 + np.exp(-z_ts / summary["temperature"]))

    metrics = compute_metrics(y_ts, probs)
    print(f"Test metrics: {json.dumps(metrics)}", flush=True)
    report: dict[str, Optional[object]] = {
        "learner": "erdalt",
        "seed": args.seed,
        "features": args.features.resolve().as_posix(),
        "neutralize": args.neutralize.resolve().as_posix() if args.neutralize else None,
        "num_features": len(names),
        "num_samples": {split: int(d[0].shape[0]) for split, d in data.items()},
        "attacks": args.attacks,
        "deltas": sources,
        "training": summary,
        "complete_only": args.complete_only,
        "ts_metrics": metrics,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "metrics.json").write_text(json.dumps(report, indent=2))
    meta_ts.select("name", "label").with_columns(pl.Series("prob", probs)).write_parquet(outdir / "ts_predictions.parquet")
    probs_vl = 1.0 / (1.0 + np.exp(-z_vl / summary["temperature"]))
    meta_vl.select("name", "label").with_columns(pl.Series("prob", probs_vl)).write_parquet(outdir / "vl_predictions.parquet")
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
