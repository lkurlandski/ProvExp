"""
§5.1's check that every monotone detector's trees respect its constraints (the robustness corollary holds only for a score that does).

Reads trained models only. For each detector of the registry's model set whose `metrics.json` records a monotone
constraint file, it rebuilds the constraint vector from that file and the feature store's names, and counts, from the
trees alone, the leaf pairs that break the constraints (`provexp.models.gbdt.monotone_violations`).

Hypothesis (user's proof note 5): zero violations for every monotone detector, since LightGBM enforces the constraints
while it grows each tree; the pilot's monotone models had none. A count above zero is reported as such.

Output: a JSON file with, per detector, the number of constrained features, the trees, the violating leaf pairs and
the largest violation.

Usage:
    python pipeline/4-detectors/monotone-check/check_monotone.py --set scaleup --out artifacts/scaleup/6-results/monotone-check/violations.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from typing import Optional

import lightgbm as lgb

from provexp.data.tabular import load_manifest
from provexp.models.gbdt import monotone_violations
from provexp.registry import MODEL_SETS


def constraint_vector(monotone: Path, names: list[str]) -> list[int]:
    """The constraint per feature name, from a file of `name<TAB>sign` lines (the file the model was trained with)."""
    index = {name: j for j, name in enumerate(names)}
    constraints = [0] * len(names)
    for line in monotone.read_text().splitlines():
        if not line.strip():
            continue
        name, sign = line.split("\t")
        if name not in index or sign not in ("1", "-1"):
            raise ValueError(f"Bad line in {monotone.as_posix()}: {line!r}")
        constraints[index[name]] = int(sign)
    return constraints


def check(model_dir: Path, tolerance: float) -> Optional[dict[str, Any]]:
    """The violations of one model, or None if it was trained without monotone constraints."""
    metrics = json.loads((model_dir / "metrics.json").read_text())
    monotone = metrics.get("config", {}).get("monotone")
    if not monotone:
        return None
    if not Path(monotone).is_file():
        raise RuntimeError(f"{model_dir.as_posix()} was trained with {monotone}, which is not here.")
    constraints = constraint_vector(Path(monotone), load_manifest(Path(metrics["features"]))["feature_names"])
    booster = lgb.Booster(model_file=(model_dir / "model.txt").as_posix())
    count, worst = monotone_violations(booster, constraints, tolerance)
    return {"constrained_features": sum(1 for c in constraints if c), "trees": booster.num_trees(),
            "violating_pairs": count, "largest_violation": worst, "constraint_file": monotone}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", dest="model_set", default="scaleup", choices=sorted(MODEL_SETS))
    parser.add_argument("--tolerance", type=float, default=0.0, help="A leaf pair violates only above this.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result: dict[str, Any] = {}
    for name, det in MODEL_SETS[args.model_set].items():
        model_dir = Path(det.model)
        if not (model_dir / "model.txt").is_file():  # a PV or ERDALT detector, or a model not trained yet
            print(f"{name}: no GBDT at {model_dir.as_posix()}; skipped.", flush=True)
            continue
        row = check(model_dir, args.tolerance)
        if row is None:
            print(f"{name}: no monotone constraints; skipped.", flush=True)
            continue
        result[name] = row
        print(f"{name}: {row['violating_pairs']} violating leaf pairs over {row['trees']} trees, "
              f"largest {row['largest_violation']:.3g} ({row['constrained_features']} constrained features).", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"set": args.model_set, "tolerance": args.tolerance, "models": result}, indent=2))
    print(f"Wrote {args.out.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
