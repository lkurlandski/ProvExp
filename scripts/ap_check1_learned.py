"""
Direction A', go/no-go check 1 (docs/direction-A-prime-mock.md): do constraints learned from attacks give wrong
certificates?

The realistic data-driven way to give an exact solver a region of reachable feature vectors is to learn it from the
outputs of attacks one has run (Šrndić & Laskov's per-feature bounds, Sheatsley et al., Bostani et al.; Labaca-Castro
et al.'s per-feature change statistics). Check 0 showed that directions alone certify nothing on a non-monotone
detector, so the learned region here also carries magnitudes: feature f of a file x may take any value in
[x_f + min delta_f, x_f + max delta_f], where the deltas are the toolkit's perturbation vectors (feature changes of
every written and re-extracted adversarial file, `scripts/a_pv_attacks.py`) and the min and max include 0. A feature no
attack changed is fixed. The exact solver (`scripts/ap_check0_solver.py`, decision version) then asks whether any
vector in that region scores below the detector's 1%-FPR threshold; "no" is the learned certificate.

The check compares these certificates with the attack battery, which is a sound lower bound: a file the battery
evades with a real, re-extracted file is evadable, so a learned certificate on it is wrong. The battery is the per-file
union of the toolkit's eight attacks (`scripts/a1_evaluate.py`) and the C1-guided adaptive search
(`scripts/a1_adaptive.py`), on the same detectors. Go if the learned region certifies at least a third of the files
the battery evades on PV-seen.

Outputs, in `{outdir}/`:
    solves.parquet   one row per (defense, learned-from attack set, file): battery evaded, learned certified, solver
                     status, seconds
    report.json      per (defense, attack set): detected, battery evaded, certified, wrongly certified (certified and
                     battery-evaded), learned-region size (features free to move), and the go/no-go verdict

Usage (smoke on two files, 60 s limit):
    PYTHONHASHSEED=0 python scripts/ap_check1_learned.py --outdir /tmp/ap1 --num_malware 2 --time_limit 60 \
        --defense pv-seen=artifacts/models/gbdt/seed-0-s10-pv-seen
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing
from pathlib import Path
import sys
from typing import Any
from typing import Optional

import lightgbm
import numpy as np
import polars as pl

from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a1_adaptive import _threshold  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from ap_check0_solver import TOL  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402
from ap_check0_solver import solve  # noqa: E402

__all__ = [
    "battery",
    "learned_box",
    "main",
]

ROOT = Path(__file__).resolve().parent.parent
SEEN = ("content_shift", "gamma_sections", "gamma_shift", "padding")


################################################################################
# The learned region and the battery
################################################################################

def learned_box(deltas: pl.DataFrame, attacks: list[str], names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Per feature, the smallest and largest change any of `attacks` produced (both include 0).

    Args:
        deltas: the perturbation vectors, one row per (file, attack), one column per thrember feature.
        attacks: the attacks to learn from.
        names: the feature names of the solver's vectors; features absent from `deltas` (the sums columns) stay fixed.

    Returns:
        (down, up): per feature, the most negative and the most positive change seen.
    """
    d = deltas.filter(pl.col("attack").is_in(attacks))
    if d.height == 0:
        raise ValueError(f"No perturbation vectors for attacks {attacks}.")
    down, up = np.zeros(len(names)), np.zeros(len(names))
    index = {n: i for i, n in enumerate(names)}
    cols = [c for c in d.columns if c in index]
    x = d.select(cols).to_numpy().astype(np.float64)
    for j, c in enumerate(cols):
        down[index[c]] = min(0.0, float(x[:, j].min()))
        up[index[c]] = max(0.0, float(x[:, j].max()))
    return down, up


def battery(toolkits: list[Path], adaptive: list[Path]) -> dict[tuple[str, str], bool]:
    """
    Per (defense, file), whether any toolkit attack or the adaptive search evaded it with a real, re-extracted file.

    Args:
        toolkits: `a1_evaluate.py` results, in order of preference (a defense is read from the first that has it).
        adaptive: `a1_adaptive.py` results (`evaded_real`: the written file's score).

    Returns:
        (defense, file name) -> evaded by some attack of the battery.
    """
    out: dict[tuple[str, str], bool] = {}
    done: set[str] = set()
    for path in toolkits:
        r = pl.read_parquet(path)
        new = set(r["defense"].unique().to_list()) - done
        per_file = r.filter(pl.col("defense").is_in(list(new))).group_by(["defense", "name"]).agg(pl.col("evaded").any())
        for d, n, e in per_file.iter_rows():
            out[(d, n)] = bool(e)
        done |= new
    for path in adaptive:
        for d, n, e in pl.read_parquet(path).select("defense", "name", "evaded_real").iter_rows():
            out[(d, n)] = out.get((d, n), False) or bool(e)
    return out


################################################################################
# Main
################################################################################

_ENSEMBLES: dict[str, Ensemble] = {}


def _job(job: tuple[str, str, str, np.ndarray, np.ndarray, np.ndarray, float, float]) -> dict[str, Any]:
    defense, learned_from, name, x, down, up, tau_raw, time_limit = job
    r = solve(_ENSEMBLES[defense], x, {}, time_limit, below=tau_raw - TOL, box=(x + down, x + up))
    r.update(defense=defense, learned_from=learned_from, name=name, tau_raw=tau_raw)
    r["evaded"] = r["best"] is not None and r["best"] < tau_raw - TOL
    r["certified"] = r["dual_bound"] is not None and r["dual_bound"] >= tau_raw - TOL
    print(f"  {defense} {learned_from} {name[:12]}: {r['message'][:40]!r} {r['seconds']:.0f}s "
          f"evaded={r['evaded']} certified={r['certified']}", flush=True)
    return r


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--deltas", type=Path, default=ROOT / "artifacts/experiments/a_pv/deltas.parquet")
    parser.add_argument("--toolkit", type=Path, nargs="+", default=[ROOT / "artifacts/experiments/a1/toolkit-v2/results.parquet"])
    parser.add_argument("--adaptive", type=Path, nargs="*", default=[])
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_malware", type=int, default=None)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--time_limit", type=float, default=600.0, help="Seconds per solve.")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    extractor = SumsFeatureExtractor()
    deltas = pl.read_parquet(args.deltas)
    all_attacks = sorted(deltas["attack"].unique().to_list())
    sets = {"all": all_attacks, "seen": [a for a in all_attacks if a in SEEN]}
    boxes = {k: learned_box(deltas, v, extractor.feature_names) for k, v in sets.items()}
    evaded_by_battery = battery(args.toolkit, args.adaptive)
    defenses = _parse_defenses(args.defense)
    malware, _ = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    vectors = {n: extractor.feature_vector(z).astype(np.float64) for n, z in malware}  # type: ignore[no-untyped-call]

    jobs: list[tuple[str, str, str, np.ndarray, np.ndarray, np.ndarray, float, float]] = []
    for d, mdir in defenses.items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        if booster.num_feature() != extractor.dim:
            raise RuntimeError(f"{d}: model has {booster.num_feature()} features, the sums extractor {extractor.dim}.")
        _ENSEMBLES[d] = Ensemble(booster)
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        tau_raw = float(np.log(tau / (1.0 - tau)))
        for n, x in vectors.items():
            if float(booster.predict(x.reshape(1, -1).astype(np.float32), raw_score=True)[0]) <= tau_raw:
                continue  # evaluate only what this defense detects
            if (d, n) not in evaded_by_battery:
                raise RuntimeError(f"{d}: no battery result for detected file {n}.")
            jobs += [(d, k, n, x, *boxes[k], tau_raw, args.time_limit) for k in sets]

    # NOTE: fork, so the workers inherit the flattened ensembles (Python 3.14 defaults to forkserver).
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    out = pl.DataFrame(rows).with_columns(
        pl.struct("defense", "name").map_elements(lambda r: evaded_by_battery[(r["defense"], r["name"])],
                                                  return_dtype=pl.Boolean).alias("battery_evaded"))
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "solves.parquet")

    report: dict[str, Any] = {"time_limit": args.time_limit, "fpr": args.fpr, "attack_sets": sets,
                              "free_features": {k: int(((b[0] < 0) | (b[1] > 0)).sum()) for k, b in boxes.items()},
                              "toolkit": [p.as_posix() for p in args.toolkit],
                              "adaptive": [p.as_posix() for p in args.adaptive], "groups": {}}
    for (d, k), g in out.group_by(["defense", "learned_from"], maintain_order=True):
        evaded = g.filter(pl.col("battery_evaded"))
        wrong = int(evaded["certified"].sum())
        entry: dict[str, Any] = {
            "detected": g.height,
            "battery_evaded": evaded.height,
            "certified": int(g["certified"].sum()),
            "solver_evaded": int(g["evaded"].sum()),
            "undecided": int((~g["certified"] & ~g["evaded"]).sum()),
            "wrongly_certified": wrong,
            "median_seconds": float(g["seconds"].median()),  # type: ignore[arg-type]
            "max_seconds": float(g["seconds"].max()),  # type: ignore[arg-type]
        }
        go: Optional[bool] = (3 * wrong >= evaded.height) if evaded.height else None
        entry["go_if_wrong_ge_third"] = go
        report["groups"][f"{d}/{k}"] = entry
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
