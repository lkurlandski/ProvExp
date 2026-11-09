"""
ERDALT's hole, computed from the derived direction table before any attack runs (docs/archive/direction-A/direction-A-mock.md, ERDALT row).

ERDALT is robust to an edit if its first layer L maps the edit's feature change to a nonnegative vector (the layers
above are monotone). The derived table says, per feature, which way the threat model's edits can move it: up only,
down only, both, or not at all. So L is sound for the threat model only if each column j of L (in raw units,
L diag(1/std), which has the same signs) satisfies:

    up:    no negative entry          (raising x_j must not lower any post-processed feature)
    down:  no positive entry
    both:  no nonzero entry
    fixed: anything

Every other entry is a direction the attacks ERDALT learned from did not cover and the table finds without running
any. We report, per direction class, how many columns violate (entries above a tolerance) and the share of L's weight
(in standardized units, sum |L_ij|) in violating entries; and, on the pilot malware, how many (file, feature) pairs have
a negative derivative of the logit along the feature's allowed direction (the moves the adaptive search can use).

Outputs: `{outdir}/hole.json`, `{outdir}/hole_features.csv` (one row per violating feature).

Usage: python scripts/a_erdalt_hole.py --model artifacts/models/erdalt/seed-0-s10-seen \
    --directions artifacts/experiments/a_directions_derived_sums_v2/M_full-pre-control --outdir <dir>
"""

from __future__ import annotations
from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
from numpy import typing as npt
import polars as pl
import torch

from provexp.data.paths import EMBER2024_DATA
from provexp.models.erdalt import ERDALTDetector

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from a_pv_attacks import load_pilot  # noqa: E402
from a1_evaluate import make_extractor  # noqa: E402


__all__ = [
    "directions",
    "column_violations",
]

ROOT = Path(__file__).resolve().parents[1]


################################################################################
# The check
################################################################################

def directions(stem: Path, names: list[str]) -> npt.NDArray[np.int8]:
    """Per feature: +1 up only, -1 down only, 2 both, 0 fixed, from `{stem}.monotone.tsv` and `{stem}.neutralize.txt`."""
    out = np.zeros(len(names), dtype=np.int8)
    index = {n: j for j, n in enumerate(names)}
    for line in Path(f"{stem}.monotone.tsv").read_text().splitlines():
        if line.strip():
            name, sign = line.split("\t")
            if name in index:
                out[index[name]] = int(sign)
    for line in Path(f"{stem}.neutralize.txt").read_text().splitlines():
        if line.strip() in index:
            out[index[line.strip()]] = 2
    return out


def column_violations(L: npt.NDArray[np.float64], dirs: npt.NDArray[np.int8], tol: float) -> npt.NDArray[np.bool_]:
    """The entries of L (rows: post-processed features, columns: input features) the table proves exploitable."""
    bad = np.zeros_like(L, dtype=bool)
    bad[:, dirs == 1] = L[:, dirs == 1] < -tol
    bad[:, dirs == -1] = L[:, dirs == -1] > tol
    bad[:, dirs == 2] = np.abs(L[:, dirs == 2]) > tol
    return bad


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description="ERDALT's first layer against the derived direction table.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--directions", type=Path, required=True, help="The table's file stem (no extension).")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024",
                        help="A store whose extractor gives the model's features (for the pilot gradients).")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--tol", type=float, default=1e-3, help="Entries of L (standardized units) below this are 0.")
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    det = ERDALTDetector(args.model)
    names = det.feature_names
    dirs = directions(args.directions, names)
    L = det.model.layer1.weight.detach().double().numpy()  # standardized units; the signs of L diag(1/std)
    bad = column_violations(L, dirs, args.tol)
    weight = np.abs(L) * (np.abs(L) > args.tol)
    classes = {"up": 1, "down": -1, "both": 2, "fixed": 0}
    summary: dict[str, object] = {
        "model": args.model.resolve().as_posix(), "directions": args.directions.as_posix(), "tol": args.tol,
        "weight_share_violating": float(weight[bad].sum() / weight.sum()),
        "per_class": {c: {"features": int((dirs == v).sum()),
                          "violating_columns": int(bad[:, dirs == v].any(axis=0).sum()),
                          "weight_share": float(weight[:, dirs == v][bad[:, dirs == v]].sum() / weight.sum())}
                      for c, v in classes.items()},
    }

    # The logit's derivative along each feature's allowed direction, on the pilot malware (the adaptive search's moves).
    extractor = make_extractor(args.features)
    malware, _ = load_pilot(args.pilot_files, args.db)
    X = np.stack([extractor.feature_vector(data) for _, data in malware])  # type: ignore[no-untyped-call]
    x = torch.from_numpy(det._select(X).numpy()).requires_grad_(True)
    det.model(x).sum().backward()
    assert x.grad is not None
    grad = x.grad.double().numpy()
    movable = dirs != 0
    signs = {1: [1.0], -1: [-1.0], 2: [1.0, -1.0]}
    lowering = np.zeros(grad.shape, dtype=bool)
    for v, ss in signs.items():
        for s in ss:
            lowering[:, dirs == v] |= s * grad[:, dirs == v] < -1e-9
    summary["pilot"] = {"files": int(X.shape[0]), "movable_features": int(movable.sum()),
                        "files_with_a_lowering_move": int(lowering.any(axis=1).sum()),
                        "lowering_pairs": int(lowering.sum()),
                        "lowering_features": int(lowering.any(axis=0).sum())}

    viol = np.nonzero(bad.any(axis=0))[0]
    label = {1: "up", -1: "down", 2: "both", 0: "fixed"}
    pl.DataFrame({
        "name": [names[j] for j in viol],
        "direction": [label[int(dirs[j])] for j in viol],
        "violating_entries": [int(bad[:, j].sum()) for j in viol],
        "violating_weight": [float(weight[bad[:, j], j].sum()) for j in viol],
        "pilot_files_lowering": [int(lowering[:, j].sum()) for j in viol],
    }).sort("violating_weight", descending=True).write_csv(args.outdir / "hole_features.csv")
    (args.outdir / "hole.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
