"""
Direction A, go/no-go check 2 (docs/archive/direction-A/direction-A-mock.md), part 1 of 2: the perturbation vectors.

FOR ACADEMIC SECURITY RESEARCH ONLY. This reproduces, against our own detector and on our own pilot samples, the
black-box functionality-preserving transformations of Gimenez et al. ("Certifiably robust malware detectors by
design") and Demetrio et al. (secml-malware), in order to *evaluate a defense*: it measures which EMBER features their
attack sample happens never to decrease, so that we can test whether perturbation-vector (PV) feature selection leaves
a hole that feature provenance (C4) predicts. No new evasion technique is developed and nothing is deployed; the
attacked files are written only so their features can be re-extracted and differenced.

For each detected pilot malware sample, we run each of Gimenez et al.'s eight secml-malware attacks against our GBDT,
re-extract the features of the written file with our (quirk-fixed, merged-imports) extractor, and record the
perturbation vector delta = phi(z') - phi(z). The stacked deltas are the input to pipeline/6-results/pv_hole.py.

Outputs, in `{outdir}/`:
    deltas.parquet      one row per (file, attack) that produced a parseable file: the 2,568 feature deltas, plus the
                        attack name, the file name, and the clean/adversarial GBDT probability
    evasion.parquet     one row per (file, attack): evaded (adv prob < 0.5), probabilities, bytes added, seconds
    summary.json        per-attack evasion rate and timing; the run's configuration

Usage (smoke on three files):
    PYTHONHASHSEED=0 python pipeline/5-attacks/toolkit/pv_attacks.py --outdir artifacts/experiments/a_pv --num_malware 3 --attacks padding
Full pilot run is driven by run/78_a_check2_attacks.sh (hand it to the user; see that script for the estimate).
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
import tempfile
import time
from typing import Any
from typing import Optional

import lief
import polars as pl

from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import build_attack
from provexp.attacks.toolkit import build_donor_pools
from provexp.attacks.toolkit import make_wrapper
from provexp.attacks.toolkit import run_attack
from provexp.data.files import load_pilot
from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks

__all__: list[str] = []



################################################################################
# Our detector, wrapped for secml-malware's black-box engine
################################################################################


################################################################################
# Attacks
################################################################################


################################################################################
# Pilot data
################################################################################


################################################################################
# Parallel workers (one attack on one file; the detector and donor pools are per-worker globals)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(model: Path, section_pop: list[Any], api_calls: list[Any], seed: int) -> None:
    """Build the per-worker extractor, detector wrapper, and donor pools once."""
    lief.logging.disable()
    extractor = fix_quirks(PEFeatureExtractor())  # quirk-fixed, per docs/archive/direction-A/direction-A-mock.md check 2
    _W.update(extractor=extractor, names=extractor.feature_names, wrapper=make_wrapper(model, extractor),
              section_pop=section_pop, api_calls=api_calls, seed=seed, tmp=tempfile.mkdtemp(prefix="a_pv_w_"))


def _work(task: tuple[str, str, bytes]) -> tuple[Optional[dict[str, Any]], dict[str, Any]]:
    """Run one (attack, file): returns (delta row or None if the file was unparseable, evasion row)."""
    atk, name, data = task
    extractor, names, wrapper = _W["extractor"], _W["names"], _W["wrapper"]
    out_path = Path(_W["tmp"]) / f"{name[:16]}.{atk}"
    start = time.time()
    try:
        phi0 = extractor.feature_vector(data)
        problem = build_attack(atk, wrapper, _W["section_pop"], _W["api_calls"])
        adv_bytes, p_clean, p_adv = run_attack(problem, wrapper, data, out_path, seed=_W["seed"])
        phi1 = extractor.feature_vector(adv_bytes)
        added, ok = len(adv_bytes) - len(data), True
    except Exception as e:
        print(f"  WARN {atk} {name[:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)
        p_clean = p_adv = float("nan")
        added, ok = 0, False
    secs = time.time() - start
    evaded = bool(ok and p_adv < 0.5)
    evasion = {"name": name, "attack": atk, "evaded": evaded, "p_clean": p_clean, "p_adv": p_adv,
               "bytes_added": added, "ok": ok, "seconds": secs}
    delta: Optional[dict[str, Any]] = None
    if ok:
        delta = {"name": name, "attack": atk, "p_clean": p_clean, "p_adv": p_adv}
        delta.update({names[j]: float(phi1[j] - phi0[j]) for j in range(len(names))})
    return delta, evasion


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/models/gbdt/seed-0/model.txt")
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--num_malware", type=int, default=None, help="Cap on malware files (for smoke tests).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes over (attack, file) tasks.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)

    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    print(f"Pilot: {len(malware)} detected malware, {len(goodware)} goodware donors.", flush=True)

    with tempfile.TemporaryDirectory(prefix="a_pv_") as tmp:
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp))
        print(f"Donor pools: {len(section_pop)} sections, {len(api_calls)} API groups.", flush=True)
        # One task per (attack, file); the reseed in run_attack makes each task deterministic regardless of order.
        tasks = [(atk, name, data) for atk in args.attacks for name, data in malware]
        t0 = time.time()
        ctx = get_context("spawn")
        with ctx.Pool(args.num_workers, initializer=_init_worker,
                      initargs=(args.model, section_pop, api_calls, args.seed)) as pool:
            results = pool.map(_work, tasks)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    delta_rows = [d for d, _ in results if d is not None]
    evasion_rows = [e for _, e in results]
    for atk in args.attacks:
        ev = [e for e in evasion_rows if e["attack"] == atk]
        print(f"{atk}: evaded {sum(e['evaded'] for e in ev)}/{len(ev)}, "
              f"failed {sum(not e['ok'] for e in ev)}", flush=True)

    pl.DataFrame(delta_rows).write_parquet(args.outdir / "deltas.parquet")
    pl.DataFrame(evasion_rows).write_parquet(args.outdir / "evasion.parquet")
    ev = pl.DataFrame(evasion_rows)
    summary = {
        "num_malware": len(malware),
        "num_goodware_donors": len(goodware),
        "attacks": args.attacks,
        "model": str(args.model),
        "quirk_fixed_extractor": True,
        "seed": args.seed,
        "per_attack": {
            atk: {
                "evaded": int(ev.filter(pl.col("attack") == atk)["evaded"].sum()),
                "failed_files": int((~ev.filter(pl.col("attack") == atk)["ok"]).sum()),
                "seconds": float(ev.filter(pl.col("attack") == atk)["seconds"].sum()),
            }
            for atk in args.attacks
        },
    }
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(delta_rows)} perturbation vectors to {args.outdir}/deltas.parquet", flush=True)


if __name__ == "__main__":
    main()
