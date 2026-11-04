"""
Direction A', check 2 (docs/direction-A-prime-mock.md): do the solver's evasions realize?

Each saved solver evasion (`ap_check1b.py`'s `solutions/{defense}_{name}.npy`) is written as a file by
`ap_realize.realize` (with the solver's split sides, so byte counts are nudged onto its side of the histogram
splits), re-extracted, and scored. Where the written file does not evade, the gap is attributed to feature groups:
per group, the score with that group's splits on the solver's sides and every other split on the written file's
(`ap_check1b.attribute`).

The encoding must be the one the solutions were found with (the variable names must match); this is checked.

Outputs, in `{outdir}/`:
    realized.parquet   one row per solution: solver and real raw scores, threshold, evades, per-group attributed
                       scores and differing splits, seconds
    files/             the written files ({defense}_{name}.bin)

Usage:
    PYTHONHASHSEED=0 python scripts/ap_check2_realize.py --solutions artifacts/experiments/ap_check1b/solutions \
        --outdir /tmp/ap2 --defense ref=artifacts/models/gbdt/seed-0-s10-ref
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing
from pathlib import Path
import sys
import time
from typing import Any

import lightgbm
import numpy as np
import polars as pl

from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a1_adaptive import _threshold  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402
from ap_check1b import attribute  # noqa: E402
from ap_check1b import sides_of  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import budget  # noqa: E402
from ap_encoding import link_ensemble  # noqa: E402
from ap_realize import realize  # noqa: E402

__all__ = [
    "main",
]

ROOT = Path(__file__).resolve().parent.parent


################################################################################
# Main
################################################################################


_STATE: dict[str, Any] = {}


def _job(job: tuple[str, str, bytes, Path]) -> dict[str, Any]:
    defense, name, z, path = job
    args, extractor = _STATE["args"], _STATE["extractor"]
    booster, ens, tau_raw = _STATE["defenses"][defense]
    t0 = time.time()
    x = np.load(path)
    enc = Encoding(extractor, z, budget(len(z), args.budget_frac, args.budget_min), args.max_sections)
    P = enc.program
    split = link_ensemble(enc, ens)
    for i in range(ens.values.size):
        P.var(f"leaf{i}", 0, 1)
    if len(P.names) != x.size:
        raise RuntimeError(f"{name}: {x.size} values for {len(P.names)} variables; was the encoding changed since the solve?")
    sides = {key: bool(x[v] > 0.5) for key, v in split.items()}
    edited = realize(enc, P.names, x, sides=sides, thresholds=ens.thresholds)
    (args.outdir / "files").mkdir(parents=True, exist_ok=True)
    (args.outdir / "files" / f"{defense}_{name}.bin").write_bytes(edited)
    x_real = np.asarray(extractor.feature_vector(edited), dtype=np.float64)
    real = float(booster.predict(x_real.astype(np.float32).reshape(1, -1), raw_score=True)[0])
    att = attribute(ens, sides, x_real, _STATE["groups"])
    differ: dict[str, int] = {}
    for key, side in sides_of(ens, x_real).items():
        if side != sides[key]:
            g = extractor.feature_names[key[0]].split(":")[0]
            differ[g] = differ.get(g, 0) + 1
    row = {"defense": defense, "name": name, "size": len(z), "added": len(edited) - len(z), "tau_raw": tau_raw,
           "solver": att.pop("solver"), "real": real, "evades": real <= tau_raw,
           "attributed": json.dumps({g: v for g, v in att.items() if g != "real" and abs(v - real) > 1e-9}),
           "differ": json.dumps(differ), "seconds": time.time() - t0}
    print(f"  {defense} {name[:12]}: solver {row['solver']:.2f} real {real:.2f} (threshold {tau_raw:.2f}) "
          f"evades={row['evades']} attributed={row['attributed']} differ={row['differ']}", flush=True)
    return row


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--solutions", type=Path, required=True, help="ap_check1b.py's solutions/ directory.")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--max_sections", type=int, default=3)
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    extractor = SumsFeatureExtractor()
    groups: dict[str, list[int]] = {}
    for i, nm in enumerate(extractor.feature_names):
        groups.setdefault(nm.split(":")[0], []).append(i)
    defenses = {}
    for d, mdir in _parse_defenses(args.defense).items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        defenses[d] = (booster, Ensemble(booster), float(np.log(tau / (1.0 - tau))))
    malware, _ = load_pilot(args.pilot_files, args.db)
    files = dict(malware)
    jobs = []
    for path in sorted(args.solutions.glob("*.npy")):
        defense, name = path.stem.split("_", 1)
        if defense in defenses:
            jobs.append((defense, name, files[name], path))
    _STATE.update(args=args, extractor=extractor, defenses=defenses, groups=groups)
    print(f"{len(jobs)} solutions to write", flush=True)
    # NOTE: fork, so the workers inherit the boosters and the extractor.
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out = pl.DataFrame(rows)
    out.write_parquet(args.outdir / "realized.parquet")
    print(f"{int(out['evades'].sum())} of {out.height} evade as files", flush=True)


if __name__ == "__main__":
    main()
