"""
Direction A': the bracket of each detector's worst case under realistic edits (docs/direction-A-prime-plan.md).

For each detector and each pilot malware it detects, two bounds on the lowest raw score an attacker can reach:

    ceiling   the lowest score a real attack reached: the toolkit's eight attacks and the adaptive search, every file
              written and re-extracted (`ap_check1_learned.battery`'s sources). Below the threshold: evaded.
    floor     a proven lower bound on the lowest score any edit in the catalogue reaches: the exact solver over the
              edit-choice encoding (`ap_encoding.certify` with `minimize`), its dual bound when the time limit stops
              it. Above the threshold: certified.

A file neither evaded nor certified is open. The catalogue is taken per family and combined (user's decision 4):
`append` (append only), `sections` (up to K added sections, nothing appended), `both` (the two together, as in
check 1b). Per (detector, family, file), two cheap quantities come first, both from the encoding alone:

    moved splits   how many of the detector's splits sit on features some edit in the family moves (the program
                   only has to decide those; predicts tractability)
    cheap floor    each tree's lowest leaf with every split on a moved feature left free and every other one on the
                   file's side, summed: a sound floor in milliseconds (above the threshold: certified without a solve)

NOTE: the ceiling's attacks include edits outside the catalogue (header fields, imports, renames), so a file can be
certified and evaded at once without contradiction; such files are listed in the report for inspection.

Outputs, in `{outdir}/`:
    brackets.parquet   one row per (defense, family, file): covered (or why not), clean score, threshold, ceiling and
                       the attack that reached it, moved splits, cheap floor, floor, best encoded score found, status,
                       seconds, program size
    report.json        per defense and family: detected, evaded, among the rest covered / certified / open (and the
                       solver's encoded finds among the open), the floors' distance to the threshold; per defense, the
                       files certified against each family alone but not against both; the G1 reading

Usage (smoke on one file, 120 s limit):
    PYTHONHASHSEED=0 python scripts/ap_bracket.py --outdir /tmp/apb --names 0485edc2 --time_limit 120 \
        --defense pv-all=artifacts/models/gbdt/seed-0-s10-pv-all
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import lightgbm
import numpy as np
import polars as pl

from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a1_adaptive import _threshold  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from ap_check0_solver import TOL  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import Lin  # noqa: E402
from ap_encoding import NotCovered  # noqa: E402
from ap_encoding import budget  # noqa: E402
from ap_encoding import certify  # noqa: E402

__all__ = [
    "FAMILIES",
    "ceilings",
    "cheap_floor",
    "main",
    "moved_features",
]

ROOT = Path(__file__).resolve().parent.parent
FAMILIES = ("append", "sections", "both")
# G1 (docs/direction-A-prime-plan.md): at most this share of the covered, unevaded files open on a hardened detector.
G1_OPEN_SHARE = 0.5


################################################################################
# The ceiling: the lowest real score
################################################################################


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return float(np.log(p / (1.0 - p)))


def ceilings(toolkits: list[Path], adaptive: list[Path]) -> dict[tuple[str, str], tuple[float, str]]:
    """
    Per (defense, file), the lowest raw score a real, re-extracted attack reached, and the attack.

    Args:
        toolkits: `a1_evaluate.py` results, in order of preference (a defense is read from the first that has it).
        adaptive: `a1_adaptive.py` results (`p_adv_real`: the written file's score).

    Returns:
        (defense, file name) -> (lowest raw score, attack name). Only valid, loadable, within-budget outputs count, as
        in `a1_evaluate.py`'s `evaded`.
    """
    out: dict[tuple[str, str], tuple[float, str]] = {}

    def offer(key: tuple[str, str], score: float, attack: str) -> None:
        if key not in out or score < out[key][0]:
            out[key] = (score, attack)

    done: set[str] = set()
    for path in toolkits:
        r = pl.read_parquet(path)
        new = set(r["defense"].unique().to_list()) - done
        ok = r.filter(pl.col("defense").is_in(list(new)) & pl.col("ok") & pl.col("valid") & ~pl.col("over_budget"))
        for d, n, atk, p in ok.select("defense", "name", "attack", "p_adv").iter_rows():
            offer((d, n), _logit(float(p)), atk)
        done |= new
    for path in adaptive:
        for d, n, p in pl.read_parquet(path).select("defense", "name", "p_adv_real").iter_rows():
            if p is not None and np.isfinite(p):
                offer((d, n), _logit(float(p)), "adaptive")
    return out


################################################################################
# Cheap quantities from the encoding alone
################################################################################


def moved_features(enc: Encoding) -> set[int]:
    """The features some edit in the encoded catalogue moves (their value depends on a choice variable)."""
    out: set[int] = set()
    for f, v in enc.values.items():
        if isinstance(v, float) or (isinstance(v, Lin) and not v.terms):
            continue
        out.add(f)
    return out


def cheap_floor(ens: Ensemble, x: np.ndarray, moved: set[int]) -> tuple[float, int]:
    """
    A sound floor on the lowest reachable score: per tree, the lowest leaf reachable when every split on a moved
    feature may go either way and every other split goes the file's way.

    Args:
        ens: the flattened ensemble.
        x: the file's feature vector (as the detector sees it).
        moved: the features some edit moves.

    Returns:
        (the floor, the number of the ensemble's splits on moved features).
    """
    total, moved_splits = 0.0, 0
    for leaves, nodes in zip(ens.leaves, ens.nodes):
        alive = set(leaves)
        for f, j, left, right in nodes:
            if f in moved:
                moved_splits += 1
                continue
            alive -= set(right) if float(x[f]) <= ens.thresholds[f][j] else set(left)
        total += float(min(ens.values[i] for i in alive))
    return total, moved_splits


################################################################################
# Main
################################################################################


_STATE: dict[str, Any] = {}


def _job(job: tuple[str, str, str, bytes, float, float, Optional[float], Optional[str]]) -> dict[str, Any]:
    defense, family, name, z, clean, tau_raw, ceiling, ceiling_attack = job
    args = _STATE["args"]
    ens: Ensemble = _STATE["ensembles"][defense]
    b = budget(len(z), args.budget_frac, args.budget_min)
    row: dict[str, Any] = {"defense": defense, "family": family, "name": name, "size": len(z), "budget": b,
                           "clean": clean, "tau_raw": tau_raw, "ceiling": ceiling, "ceiling_attack": ceiling_attack,
                           "evaded": ceiling is not None and ceiling <= tau_raw}
    t0 = time.time()
    try:
        enc = Encoding(_STATE["extractor"], z, b, 0 if family == "append" else args.max_sections)
    except NotCovered as e:
        row.update(covered=False, reason=str(e))
        return row
    if family == "sections":
        if enc.k == 0:
            row.update(covered=False, reason="no free section-table slot")
            return row
        enc.program.fix(enc.A, 0.0)  # nothing appended (the per-value counts follow from their row)
    row.update(covered=True, reason=None, k=enc.k, build_seconds=time.time() - t0)

    x = enc.x0.astype(np.float32)
    moved = moved_features(enc)
    cheap, moved_splits = cheap_floor(ens, x, moved)
    row.update(moved_features=len(moved), moved_splits=moved_splits, total_splits=sum(len(n) for n in ens.nodes),
               cheap_floor=cheap, cheap_certified=cheap > tau_raw)
    # NOTE (soundness, G0): the file itself is reachable (the empty edit), so every floor must lie at or below its
    # clean score; a violation is a bug in the encoding or the solver, never a result.
    if cheap > clean + 1e-6:
        raise RuntimeError(f"{defense} {family} {name}: cheap floor {cheap} above the clean score {clean}.")
    if cheap > tau_raw:
        row.update(floor=cheap, certified=True, status=None, message="cheap floor", seconds=0.0, best=None)
    else:
        r = certify(enc, ens, tau_raw - TOL, args.time_limit, minimize=True)
        floor = r["floor"] if r["floor"] is None else max(r["floor"], cheap)
        if floor is not None and floor > clean + 1e-6 and not r["certified"]:
            raise RuntimeError(f"{defense} {family} {name}: floor {floor} above the clean score {clean}.")
        row.update(floor=floor, certified=bool(r["certified"]), status=r["status"], message=r["message"],
                   seconds=r["seconds"], best=r.get("score"), solver_found=bool(r["evaded"]), gap=r.get("gap"),
                   nodes=r.get("nodes"), variables=r["variables"], rows=r["rows"], binaries=r["binaries"])
    print(f"  {defense} {family} {name[:12]}: moved splits {moved_splits}, cheap {cheap:.2f}, floor {row['floor']}, "
          f"tau {tau_raw:.2f}, ceiling {ceiling}, certified={row['certified']} ({row['seconds']:.0f}s)", flush=True)
    return row


def _report(out: pl.DataFrame, args: Any, counts: dict[str, dict[str, int]]) -> dict[str, Any]:
    report: dict[str, Any] = {"args": {k: str(v) for k, v in vars(args).items()}, "defenses": {}}
    for (d,), g in out.group_by(["defense"], maintain_order=True):
        # Detected and evaded over every pilot malware the detector catches (the jobs may leave the evaded out).
        entry: dict[str, Any] = dict(counts[d])
        for fam in args.family:
            h = g.filter(pl.col("family") == fam)
            rest = h.filter(~pl.col("evaded"))
            cov = rest.filter(pl.col("covered"))
            if cov.height:
                certified = cov.filter(pl.col("certified"))
                open_ = cov.filter(~pl.col("certified"))
                floors = open_.filter(pl.col("floor").is_not_null())
                below = (floors["tau_raw"] - floors["floor"]) if floors.height else None
            entry[fam] = {
                "bounded": h.height,
                "not_evaded": rest.height,
                "not_covered": dict(rest.filter(~pl.col("covered")).group_by("reason").len().iter_rows()),
                "covered": cov.height,
                "certified": certified.height if cov.height else 0,
                "certified_cheap": int(cov["cheap_certified"].sum()) if cov.height else 0,
                "open": open_.height if cov.height else 0,
                "open_solver_found": int(open_["solver_found"].fill_null(False).sum()) if cov.height else 0,
                "open_no_floor": (open_.height - floors.height) if cov.height else 0,
                "open_floor_below_tau_median": float(below.median()) if below is not None else None,  # type: ignore[arg-type]
                "moved_splits_median": float(cov["moved_splits"].median()) if cov.height else None,  # type: ignore[arg-type]
                "total_splits": int(cov["total_splits"][0]) if cov.height else None,
                "median_seconds": float(cov["seconds"].median()) if cov.height else None,  # type: ignore[arg-type]
                "certified_and_evaded": h.filter(pl.col("evaded") & pl.col("certified").fill_null(False))["name"].to_list(),
            }
            if cov.height:
                entry[fam]["G1_open_share"] = open_.height / cov.height
        # Coupling under combination: certified against each family alone, not against both.
        if set(FAMILIES) <= set(args.family):
            cert = {fam: set(g.filter((pl.col("family") == fam) & pl.col("certified").fill_null(False))["name"].to_list())
                    for fam in FAMILIES}
            both_cov = set(g.filter((pl.col("family") == "both") & pl.col("covered"))["name"].to_list())
            entry["alone_not_together"] = sorted((cert["append"] & cert["sections"] & both_cov) - cert["both"])
        report["defenses"][d] = entry
    return report


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--toolkit", type=Path, nargs="+", default=[
        ROOT / "artifacts/experiments/a1/toolkit-v2/results.parquet",
        ROOT / "artifacts/experiments/a1/toolkit_v2/results.parquet"])
    parser.add_argument("--adaptive", type=Path, nargs="*", default=[ROOT / "artifacts/experiments/ap_battery/adaptive/adaptive.parquet"])
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--names", nargs="*", default=None, help="Only the files whose names start with these.")
    parser.add_argument("--family", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--max_sections", type=int, default=3, help="K: at most this many added sections.")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--time_limit", type=float, default=1800.0, help="Seconds per solve.")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--include_evaded", action="store_true", help="Also bound the files a real attack evades.")
    args = parser.parse_args()

    extractor = SumsFeatureExtractor()
    ceiling = ceilings(args.toolkit, args.adaptive)
    malware, _ = load_pilot(args.pilot_files, args.db)
    if args.names:
        malware = [(n, z) for n, z in malware if any(n.startswith(p) for p in args.names)]
    vectors = {n: extractor.feature_vector(z).astype(np.float32) for n, z in malware}  # type: ignore[no-untyped-call]
    _STATE.update(extractor=extractor, args=args, ensembles={})

    jobs: list[tuple[str, str, str, bytes, float, float, Optional[float], Optional[str]]] = []
    counts: dict[str, dict[str, int]] = {}
    for d, mdir in _parse_defenses(args.defense).items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        if booster.num_feature() != extractor.dim:
            raise RuntimeError(f"{d}: model has {booster.num_feature()} features, the sums extractor {extractor.dim}.")
        _STATE["ensembles"][d] = Ensemble(booster)
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        tau_raw = float(np.log(tau / (1.0 - tau)))
        counts[d] = {"detected": 0, "evaded": 0}
        for n, z in malware:
            clean = float(booster.predict(vectors[n].reshape(1, -1), raw_score=True)[0])
            if clean <= tau_raw:
                continue  # only what this defense detects
            c, atk = ceiling.get((d, n), (None, None))
            if c is None:
                raise RuntimeError(f"{d}: no attack result for detected file {n}.")
            counts[d]["detected"] += 1
            counts[d]["evaded"] += int(c <= tau_raw)
            if not args.include_evaded and c <= tau_raw:
                continue
            for fam in args.family:
                jobs.append((d, fam, n, z, clean, tau_raw, c, atk))
    print(f"{len(jobs)} (defense, family, file) jobs; K={args.max_sections}, budget max({args.budget_frac}, "
          f"{args.budget_min}); {args.time_limit:.0f} s per solve", flush=True)

    # NOTE: fork, so the workers inherit the flattened ensembles and the extractor.
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        rows = pool.map(_job, jobs, chunksize=1)
    out = pl.DataFrame(rows, infer_schema_length=None)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "brackets.parquet")
    report = _report(out, args, counts)
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
