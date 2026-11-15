"""
Where the monotone detector's cost lies (docs/evidence/fable-cost-of-robustness.md, Section 4; paper: §5.4).

    derive   writes `fixed-only.neutralize.txt`: every sum that the table does not hold fixed under the full threat
             model, so that a detector trained with it reads the fixed sums alone.
    table    for each model: TPR at 1% and 0.1% FPR on the test split and on the training split (from each split's
             ROC, the pilot's protocol), the share of split gain on the fixed sums, and, for a model trained with
             monotone constraints, the structural check of the constraints (`provexp.models.gbdt.monotone_violations`).

Usage:
    python pipeline/4-detectors/cost-split/cost_split.py derive --directions D/directions_sums.csv --outdir P
    python pipeline/4-detectors/cost-split/cost_split.py table --features F --directions D/directions_sums.csv \\
        --model "unconstrained=M1" --model "monotone=M2" --out P/table.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
from sklearn.metrics import roc_curve

from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.models.gbdt import monotone_violations


################################################################################
# Derive
################################################################################

def fixed_names(directions: Path, column: str = "M_full_pre") -> list[str]:
    """The names (`group:name`) of the sums the table holds fixed."""
    with directions.open() as f:
        return [f"{r['group']}:{r['name']}" for r in csv.DictReader(f) if r[column] == "fixed"]


def derive(directions: Path, outdir: Path) -> None:
    """Write the neutralize list that leaves only the fixed sums."""
    with directions.open() as f:
        rows = list(csv.DictReader(f))
    moving = [f"{r['group']}:{r['name']}" for r in rows if r["M_full_pre"] != "fixed"]
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "fixed-only.neutralize.txt").write_text("".join(n + "\n" for n in moving))
    print(f"{len(rows) - len(moving)} fixed sums kept, {len(moving)} neutralized.")


################################################################################
# Table
################################################################################

def tpr_at(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """TPR at 1% and 0.1% FPR, read from the ROC."""
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.interp(0.01, fpr, tpr)), float(np.interp(0.001, fpr, tpr))


def table(features: Path, directions: Path, models: list[tuple[str, Path]], out: Path, complete_only: bool,
          num_threads: int) -> None:
    """Print and save one row per (label, model directory)."""
    names = load_manifest(features)["feature_names"]
    fixed = np.isin(names, fixed_names(directions))
    data = {}
    for split in ("tr", "ts"):
        X, meta = load_features(features, split, only_ok=True, complete_only=complete_only)
        data[split] = (np.asarray(X), meta["label"].to_numpy().astype(np.int64))
    rows: list[dict[str, Any]] = []
    print(f"{'model':30s} {'ts 1%':>6s} {'ts .1%':>6s} {'tr 1%':>6s} {'tr .1%':>6s} {'trees':>5s} {'fixed':>6s} violations")
    for label, path in models:
        if not (path / "model.txt").exists():
            print(f"{label}: missing ({path})")
            continue
        m = json.loads((path / "metrics.json").read_text())
        booster = lgb.Booster(model_file=(path / "model.txt").as_posix())
        row: dict[str, Any] = {"model": label, "trees": booster.num_trees()}
        for split, (X, y) in data.items():
            if m.get("neutralized"):
                X = X.copy()
                X[:, m["neutralized"]] = 0.0
            row[f"{split}_tpr_1"], row[f"{split}_tpr_01"] = tpr_at(y, np.asarray(booster.predict(X, num_threads=num_threads)))
        gain = booster.feature_importance("gain")
        row["gain_fixed"] = float(gain[fixed].sum() / gain.sum())
        constraints = _constraints(path / "model.txt", len(names))
        row["violations"] = monotone_violations(booster, constraints)[0] if any(constraints) else None
        rows.append(row)
        print(f"{label:30s} {100 * row['ts_tpr_1']:6.1f} {100 * row['ts_tpr_01']:6.1f} {100 * row['tr_tpr_1']:6.1f} "
              f"{100 * row['tr_tpr_01']:6.1f} {row['trees']:5d} {100 * row['gain_fixed']:5.1f}% {row['violations']}", flush=True)
    out.write_text(json.dumps(rows, indent=2) + "\n")


def _constraints(model: Path, dim: int) -> list[int]:
    """The monotone constraints a saved model was trained with (all zero if none)."""
    with model.open() as f:
        for line in f:
            if line.startswith("monotone_constraints="):
                return [int(c) for c in line.split("=", 1)[1].split()]
            if line.startswith("Tree="):
                break
    return [0] * dim


################################################################################
# Main
################################################################################

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("derive")
    p.add_argument("--directions", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p = sub.add_parser("table")
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--directions", type=Path, required=True)
    p.add_argument("--model", action="append", required=True, help="label=path")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--complete_only", action="store_true")
    p.add_argument("--num_threads", type=int, default=16)
    args = parser.parse_args()
    if args.command == "derive":
        derive(args.directions, args.outdir)
        return
    models = []
    for item in args.model:
        if "=" not in item:
            raise ValueError(f"--model expects label=path, got {item!r}")
        label, path = item.split("=", 1)
        models.append((label, Path(path)))
    table(args.features, args.directions, models, args.out, args.complete_only, args.num_threads)


if __name__ == "__main__":
    main()
