"""
Direction A', go/no-go check 1b (docs/direction-A-prime-mock.md, decision 7): does the computed region certify?

For each detected pilot file, the exact solver (Kantchelian's encoding, `scripts/ap_check0_solver.py`) runs over the
edit-choice encoding of `scripts/ap_encoding.py` (up to K added sections, then an append, within the byte budget), in
the decision version: can some edit in the catalogue bring the raw score below the 1%-FPR threshold? "No" (the program
is infeasible) is a certificate against every edit in the catalogue. Go if the computed region certifies at least 20%
of the detected files the attack battery does not evade (the battery: the toolkit's eight attacks and the adaptive
search, real re-extracted evasions only; `scripts/ap_check1_learned.battery`).

A certificate on a file the battery evades is not necessarily wrong (the battery also uses edits outside this
catalogue: header fields, imports, renames, shifts), so those are listed for inspection rather than counted.

Outputs, in `{outdir}/`:
    solves.parquet   one row per (defense, file): covered (or why not), battery evaded, certified, solver evaded,
                     undecided, seconds, program size, file size and budget, the evading choice
    solutions/       per solver evasion, the solution vector ({defense}_{file}.npy)
    report.json      per defense: detected, covered, battery evaded; among the files the battery does not evade:
                     certified, solver-evaded, undecided, split by whether the budget exceeds the file's size; the verdict

Usage (smoke on two files, 120 s limit):
    PYTHONHASHSEED=0 python scripts/ap_check1b.py --outdir /tmp/ap1b --num_malware 2 --time_limit 120 \
        --defense ref=artifacts/models/gbdt/seed-0-s10-ref
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

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a1_adaptive import _threshold  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from ap_check0_solver import TOL  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402
from ap_check1_learned import battery  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import NotCovered  # noqa: E402
from ap_encoding import budget  # noqa: E402
from ap_encoding import certify  # noqa: E402

__all__ = [
    "main",
]

ROOT = Path(__file__).resolve().parent.parent
GO_SHARE = 0.2


################################################################################
# Attribution: which feature group a gap between two scores comes from
################################################################################


def sides_of(ens: Ensemble, x: np.ndarray) -> dict[tuple[int, int], bool]:
    """The side of every split ("x_f <= t_j") a feature vector takes."""
    return {(f, j): bool(x[f] <= t) for f, ts in ens.thresholds.items() for j, t in enumerate(ts.tolist())}


def score_of(ens: Ensemble, sides: dict[tuple[int, int], bool]) -> float:
    """The raw score of the path every tree takes under the given split sides."""
    total = 0.0
    for tree_leaves, nodes in zip(ens.leaves, ens.nodes):
        alive = set(tree_leaves)
        for f, j, left, right in nodes:
            alive.difference_update(right if sides[(f, j)] else left)
        if len(alive) != 1:
            raise RuntimeError(f"Split sides leave {len(alive)} leaves in a tree.")
        total += float(ens.values[alive.pop()])
    return total


def attribute(ens: Ensemble, solver: dict[tuple[int, int], bool], x_real: np.ndarray, groups: dict[str, list[int]]) -> dict[str, float]:
    """
    Per feature group, the score when that group's splits take the solver's sides and every other split the real
    (written and re-extracted) file's: the groups whose score falls far below the real one carry the gap.
    """
    real = sides_of(ens, x_real)
    out = {"solver": score_of(ens, solver), "real": score_of(ens, real)}
    for g, feats in groups.items():
        fs = set(feats)
        out[g] = score_of(ens, {key: (solver[key] if key[0] in fs else side) for key, side in real.items()})
    return out


################################################################################
# Main
################################################################################


_STATE: dict[str, Any] = {}


def _job(job: tuple[str, str, bytes, float, float, bool]) -> dict[str, Any]:
    defense, name, z, clean, tau_raw, evaded_by_battery = job
    args = _STATE["args"]
    b = budget(len(z), args.budget_frac, args.budget_min)
    row: dict[str, Any] = {"defense": defense, "name": name, "size": len(z), "budget": b, "clean": clean,
                           "tau_raw": tau_raw, "battery_evaded": evaded_by_battery}
    t0 = time.time()
    try:
        enc = Encoding(_STATE["extractor"], z, b, args.max_sections)
    except NotCovered as e:
        row.update(covered=False, reason=str(e))
        print(f"  {defense} {name[:12]}: not covered ({e})", flush=True)
        return row
    row.update(covered=True, reason=None, k=enc.k, build_seconds=time.time() - t0)
    r = certify(enc, _STATE["ensembles"][defense], tau_raw - TOL, args.time_limit)
    choice = r.pop("choice", None)
    r.pop("sides", None)
    x = r.pop("x", None)
    if x is not None:
        # The solution, for writing the evasion as a file later (`ap_realize.realize`; the names come from the encoding).
        (args.outdir / "solutions").mkdir(parents=True, exist_ok=True)
        np.save(args.outdir / "solutions" / f"{defense}_{name}.npy", x)
    row.update(r)
    row["choice"] = json.dumps(choice) if choice is not None else None
    print(f"  {defense} {name[:12]}: {r['message'][:40]!r} {r['seconds']:.0f}s certified={r['certified']} "
          f"evaded={r['evaded']} battery={evaded_by_battery} size={len(z)} budget={b}", flush=True)
    return row


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--toolkit", type=Path, nargs="+", default=[ROOT / "artifacts/experiments/a1/toolkit-v2/results.parquet"])
    parser.add_argument("--adaptive", type=Path, nargs="*", default=[ROOT / "artifacts/experiments/ap_battery/adaptive/adaptive.parquet"])
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_malware", type=int, default=None)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--max_sections", type=int, default=3, help="K: at most this many added sections.")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--time_limit", type=float, default=1800.0, help="Seconds per solve.")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--skip_battery_evaded", action="store_true", help="Solve only the files the battery does not "
                        "evade (the ones the go/no-go counts).")
    args = parser.parse_args()

    extractor = SumsFeatureExtractor()
    evaded_by_battery = battery(args.toolkit, args.adaptive)
    malware, _ = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    vectors = {n: extractor.feature_vector(z).astype(np.float32) for n, z in malware}  # type: ignore[no-untyped-call]
    _STATE.update(extractor=extractor, args=args, ensembles={})

    jobs: list[tuple[str, str, bytes, float, float, bool]] = []
    for d, mdir in _parse_defenses(args.defense).items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        if booster.num_feature() != extractor.dim:
            raise RuntimeError(f"{d}: model has {booster.num_feature()} features, the sums extractor {extractor.dim}.")
        _STATE["ensembles"][d] = Ensemble(booster)
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        tau_raw = float(np.log(tau / (1.0 - tau)))
        for n, z in malware:
            clean = float(booster.predict(vectors[n].reshape(1, -1), raw_score=True)[0])
            if clean <= tau_raw:
                continue  # evaluate only what this defense detects
            if (d, n) not in evaded_by_battery:
                raise RuntimeError(f"{d}: no battery result for detected file {n}.")
            if args.skip_battery_evaded and evaded_by_battery[(d, n)]:
                continue
            jobs.append((d, n, z, clean, tau_raw, evaded_by_battery[(d, n)]))
    print(f"{len(jobs)} (defense, file) solves; K={args.max_sections}, budget max({args.budget_frac}, "
          f"{args.budget_min}); {args.time_limit:.0f} s per solve", flush=True)

    # NOTE: fork, so the workers inherit the flattened ensembles and the extractor.
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    out = pl.DataFrame(rows, infer_schema_length=None)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "solves.parquet")

    report: dict[str, Any] = {"args": {k: str(v) for k, v in vars(args).items()}, "defenses": {}}
    for (d,), g in out.group_by(["defense"], maintain_order=True):
        cov = g.filter(pl.col("covered"))
        rest = g.filter(~pl.col("battery_evaded"))
        rest_cov = rest.filter(pl.col("covered"))

        def counts(h: pl.DataFrame) -> dict[str, int]:
            return {"files": h.height, "certified": int(h["certified"].sum()), "solver_evaded": int(h["evaded"].sum()),
                    "undecided": int((~h["certified"] & ~h["evaded"]).sum())}

        certified = int(rest_cov["certified"].sum()) if rest_cov.height else 0
        entry: dict[str, Any] = {
            "detected": g.height,
            "covered": cov.height,
            "not_covered": dict(g.filter(~pl.col("covered")).group_by("reason").len().iter_rows()),
            "battery_evaded": int(g["battery_evaded"].sum()) if not args.skip_battery_evaded else "skipped",
            "battery_not_evaded": rest.height,
            "battery_not_evaded_covered": counts(rest_cov) if rest_cov.height else None,
            "by_budget": {
                label: counts(h) for label, h in (
                    ("budget_exceeds_file", rest_cov.filter(pl.col("budget") > pl.col("size"))),
                    ("budget_within_file", rest_cov.filter(pl.col("budget") <= pl.col("size"))),
                ) if h.height
            },
            "battery_evaded_covered": counts(cov.filter(pl.col("battery_evaded"))) if cov.filter(pl.col("battery_evaded")).height else None,
            "certified_despite_battery_evasion": cov.filter(pl.col("battery_evaded") & pl.col("certified"))["name"].to_list(),
            "median_seconds": float(cov["seconds"].median()) if cov.height else None,  # type: ignore[arg-type]
            "max_seconds": float(cov["seconds"].max()) if cov.height else None,  # type: ignore[arg-type]
        }
        entry["go"] = bool(rest.height and certified >= GO_SHARE * rest.height)
        report["defenses"][d] = entry
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
