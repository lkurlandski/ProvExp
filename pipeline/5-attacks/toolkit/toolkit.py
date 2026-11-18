"""
Direction A, Table A1 (docs/evidence/direction-A-A1-design.md): the attack-evaluation harness for the toolkit columns.

FOR ACADEMIC SECURITY RESEARCH ONLY. This runs Gimenez et al.'s eight published secml-malware attacks against our own
detectors, on our own pilot samples, solely to evaluate defenses: which detectors stay robust to attacks that were
(seen) and were not (held-out) used to build PV selection. No new evasion technique is developed and nothing is
deployed; attacked files are written only so they can be re-extracted and re-scored.

One protocol for every cell:
    operating point   each defense's threshold is calibrated to `--fpr` (1%) on the goodware of its own test
                      predictions (ts_predictions.parquet; vl_predictions.parquet under --protocol scaleup): detected means p > tau, and at most 1% of goodware is
    malware           the detected pilot malware, attacked only where the defense detects it at tau
    budget            `--budget low` is Gimenez's (population 10, 10 iterations, 30 donors); `--budget literature` is
                      the GAMMA paper's (51 iterations, ~510 queries, 75 donors; a_pv_attacks.BUDGETS). An attacked
                      file whose added bytes exceed max(--budget_frac x size, --budget_min) counts as not evaded
                      (over_budget); table.json also reports each group without that cap ("uncapped")
    ground truth      the attacked file is written, read back, re-extracted, and re-scored; evaded means p_adv <= tau
    validity          an attacked file that no longer parses as a PE counts as not evaded (invalid): secml-malware's
                      shift attacks insert at the first section's raw offset, which is 0 on some files (e.g. the
                      VMProtect layout), so they overwrite the MZ header; a broken file is outside every threat model
    applicability     the two GAMMA attacks rebuild the file through LIEF; on files LIEF cannot rebuild (checked once
                      per start file, provexp.attacks.lief_check) they are not applicable: no run and no row, counted
                      as `not_applicable` in table.json rather than as failures

With `--escape`, a field write outside the threat model (provexp.featuresets.ember2024.escapes; R7) is applied to
every malware first, and the attacks start from the escaped file; only files the write takes out of the strict
population are attacked. Detection and evasion count from the unescaped original, as in the adaptive search: a
defense attacks the originals it detects, and an attack evades when the end file is not detected (the escape write
alone may already do so: `evaded_by_escape`). Each row records whether the original and the escaped file lie in the
(loose) population, where the guarantee covers the search.

The defenses are GBDTs on one feature store (`--features`: its manifest names the extractor); every defense is scored
with that store's extractor. A routed defense (`--route name=fallback`) is the precondition row's detector: files that
pass the precondition check (catalogue.precondition: nothing the parse is located through lies past the end of the
file) are scored by the defense's model, the others by the fallback defense's model, each calibrated to its own
threshold (a_pv_attacks.make_wrapper); the check is made on every file the attack queries. Results are also split by
whether the original file passes the check (the guarantee covers only those). The quick seen/held-out split (`--seen`) is a quick check only; the formal version is
leave-one-out (eight PV models; docs/evidence/direction-A-A1-design.md, decision 2).

Outputs, in `{outdir}/`:
    results.parquet   one row per (defense, attack, file): p_clean, p_adv, tau, evaded, bytes_added, over_budget, ok,
                      valid, truncated, seconds
    table.json        per defense: tau, detected, per-attack evasion, and per group (seen, held-out) the fraction of
                      detected files evaded by at least one attack of the group, overall and split by truncation
    lief_check.parquet  the attacked files LIEF cannot rebuild, and why (only when a LIEF-based attack runs)

Usage (smoke on two files, one attack):
    PYTHONHASHSEED=0 python pipeline/5-attacks/toolkit/toolkit.py --outdir /tmp/a1 --num_malware 2 --attacks padding \
        --defense ref=artifacts/models/gbdt/seed-0-s10-ref --features artifacts/features/ember2024-sums-10
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
import numpy as np
import pefile
import polars as pl

from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import BUDGETS
from provexp.attacks.toolkit import build_attack
from provexp.attacks.toolkit import build_donor_pools
from provexp.attacks.toolkit import calibrated
from provexp.attacks.toolkit import file_seed
from provexp.attacks.toolkit import make_wrapper
from provexp.attacks.toolkit import run_attack
from provexp.attacks.lief_check import LIEF_ATTACKS
from provexp.attacks.lief_check import lief_round_trips
from provexp.data.files import PROTOCOLS
from provexp.data.files import load_attacked
from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.detectors import MAX_LENGTH
from provexp.detectors import model_threshold
from provexp.detectors import group_evasion
from provexp.detectors import make_extractor
from provexp.detectors import parse_defenses
from provexp.detectors import precondition_holds
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.escapes import WRITES as ESCAPES
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.models.erdalt import load_detector
from provexp.parallel import map_watchdog

__all__: list[str] = []

SEEN = ("padding", "gamma_sections", "gamma_shift", "content_shift")


################################################################################
# Protocol
################################################################################


################################################################################
# Parallel workers (one attack on one file against one defense)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(features: Path, models: dict[str, str], routes: dict[str, tuple[str, float, float]],
                 section_pop: list[Any], api_calls: list[Any], seed: int, iterations: int = 10,
                 seed_per_file: bool = False) -> None:
    """Build the extractor and one detector wrapper per defense, once per worker."""
    lief.logging.disable()
    extractor = make_extractor(features)
    wrappers = {}
    for d, m in models.items():
        if d in routes:
            fb, tau, tau_fb = routes[d]
            wrappers[d] = make_wrapper(Path(m), extractor, fallback=Path(models[fb]), route=precondition_holds, taus=(tau, tau_fb))
        else:
            wrappers[d] = make_wrapper(Path(m), extractor)
    _W.update(wrappers=wrappers, section_pop=section_pop, api_calls=api_calls, seed=seed, iterations=iterations,
              tmp=tempfile.mkdtemp(prefix="a1_w_"), seed_per_file=seed_per_file)


Task = tuple[str, str, str, bytes, float, int, bool, dict[str, Any]]


def _work(task: Task) -> dict[str, Any]:
    """Run one (defense, attack, file) and score the re-extracted result at the defense's threshold."""
    defense, atk, name, data, tau, cap, pre, extra = task
    wrapper = _W["wrappers"][defense]
    out_path = Path(_W["tmp"]) / f"{defense}.{name[:16]}.{atk}"
    start = time.time()
    p_clean = p_adv = float("nan")
    added, ok, valid, error = 0, False, False, ""
    try:
        problem = build_attack(atk, wrapper, _W["section_pop"], _W["api_calls"], iterations=_W["iterations"])
        # NOTE: by default every run is reseeded with the same seed (Gimenez et al.'s protocol), so GAMMA's random
        # section names are the same on every file; --seed_per_file seeds each (attack, file) on its own.
        seed = file_seed(_W["seed"], atk, name) if _W["seed_per_file"] else _W["seed"]
        adv_bytes, p_clean, p_adv = run_attack(problem, wrapper, data, out_path, seed=seed)
        added, ok = len(adv_bytes) - len(data), True
        valid = lief.PE.parse(list(adv_bytes)) is not None
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"  WARN {defense} {atk} {name[:12]}: {error}", flush=True)
    finally:
        out_path.unlink(missing_ok=True)
    over = added > cap
    return {"defense": defense, "attack": atk, "name": name, "tau": tau, "p_clean": p_clean, "p_adv": p_adv,
            "evaded": bool(ok and valid and not over and p_adv <= tau), "bytes_added": added, "over_budget": over,
            "ok": ok, "valid": valid, "truncated": len(data) >= MAX_LENGTH, "precondition": pre, "error": error,
            "seconds": time.time() - start, **extra}


def _lost(task: Task) -> dict[str, Any]:
    """The row for a task whose worker died: an attack that failed (not evaded), with the error recorded."""
    defense, atk, name, data, tau, cap, pre, extra = task
    return {"defense": defense, "attack": atk, "name": name, "tau": tau, "p_clean": float("nan"),
            "p_adv": float("nan"), "evaded": False, "bytes_added": 0, "over_budget": False, "ok": False,
            "valid": False, "truncated": len(data) >= MAX_LENGTH, "precondition": pre,
            "error": "LostTask: given up by the watchdog", "seconds": float("nan"), **extra}


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--route", action="append", default=[], help="name=fallback: route the defense `name` to the "
                        "defense `fallback` on files that fail the precondition check (repeatable).")
    parser.add_argument("--features", type=Path, required=True, help="The feature store the defenses were trained on.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts",
                        help="The SimpleDB of --pilot_files (the pilot protocol; the scale-up reads the file store).")
    parser.add_argument("--protocol", choices=tuple(PROTOCOLS), default="pilot",
                        help="pilot: the pilot list and donors, thresholds on ts; scaleup: the evaluation list, --donors, "
                             "thresholds on vl (provexp.data.files.PROTOCOLS).")
    parser.add_argument("--donors", type=Path, default=None, help="Scale-up: the donor list (training goodware).")
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--seen", nargs="+", default=list(SEEN), choices=list(ATTACKS))
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--budget", default="low", choices=list(BUDGETS),
                        help="Attack budget: Gimenez's low one, or the GAMMA paper's (see a_pv_attacks.BUDGETS).")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--num_malware", type=int, default=None, help="Cap on malware files (for smoke tests).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes over tasks.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--seed_per_file", action="store_true",
                        help="Reseed each attack run with its own seed (a_advtrain.file_seed) instead of --seed.")
    parser.add_argument("--stall_timeout", type=float, default=3600.0,
                        help="Seconds with no finished task before the unfinished ones count as lost (over the limit, or a "
                        "dead worker).")
    parser.add_argument("--escape", choices=["none", *ESCAPES], default="none", help="A field write applied to every "
                        "malware before the attacks (R7); detection and evasion count from the unescaped original.")
    args = parser.parse_args()
    if args.escape != "none" and args.route:
        raise ValueError("--escape does not combine with --route.")
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    defenses = parse_defenses(args.defense)
    routes_spec = {k: str(v) for k, v in parse_defenses(args.route).items()}
    for d, fb in routes_spec.items():
        if d not in defenses or fb not in defenses or fb in routes_spec:
            raise ValueError(f"--route {d}={fb}: both must be defenses, and the fallback must not be routed.")
    extractor = make_extractor(args.features)

    malware, goodware = load_attacked(args.protocol, args.pilot_files, args.db, args.donors)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    print(f"Pilot: {len(malware)} malware, {len(goodware)} goodware donors; {len(defenses)} defenses.", flush=True)
    # (the file the attacks start from) per malware: the escaped file under --escape, else the file itself. Escaped files
    # that stay in the strict population, or that the write does not apply to, are not attacked (as adaptive.py).
    starts: list[bytes] = [data for _, data in malware]
    if args.escape != "none":
        plain = fix_quirks(PEFeatureExtractor())
        kept: list[tuple[str, bytes]] = []
        starts = []
        for name, data in malware:
            try:
                out = ESCAPES[args.escape](pefile.PE(data=data), len(data))
            except Exception:  # noqa: BLE001
                out = None
            if out is not None and not passes_precondition(plain, out):
                kept.append((name, data))
                starts.append(out)
        print(f"Escape {args.escape}: {len(kept)} of {len(malware)} malware written and out of the strict population; "
              "detection and evasion counted from the unescaped originals.", flush=True)
        malware = kept

    # Thresholds, and which pilot malware each defense detects (scored from the files themselves).
    X = np.stack([extractor.feature_vector(data) for _, data in malware])  # type: ignore[no-untyped-call]
    pre = [precondition_holds(data) for _, data in malware]
    print(f"  {sum(pre)}/{len(malware)} pilot malware pass the precondition check", flush=True)
    model_taus: dict[str, float] = {}
    probs: dict[str, np.ndarray] = {}
    for d, mdir in defenses.items():
        model_taus[d] = model_threshold(mdir, args.fpr, PROTOCOLS[args.protocol])
        probs[d] = np.asarray(load_detector(mdir, extractor.feature_names).predict(X))
    taus: dict[str, float] = {}
    detected: dict[str, list[int]] = {}
    routes = {d: (fb, model_taus[d], model_taus[fb]) for d, fb in routes_spec.items()}
    for d in defenses:
        if d in routes:
            fb = routes[d][0]
            p = np.where(pre, calibrated(probs[d], model_taus[d]), calibrated(probs[fb], model_taus[fb]))
            taus[d] = 0.5
        else:
            p, taus[d] = probs[d], model_taus[d]
        detected[d] = [i for i in range(len(malware)) if p[i] > taus[d]]
        print(f"  {d}: tau={taus[d]:.4f}{' (routed to ' + routes[d][0] + ')' if d in routes else ''}, detects "
              f"{len(detected[d])}/{len(malware)} pilot malware", flush=True)

    extras: dict[tuple[str, int], dict[str, Any]] = {(d, i): {} for d in defenses for i in detected[d]}
    if args.escape != "none":
        plain = fix_quirks(PEFeatureExtractor())
        X_start = np.stack([extractor.feature_vector(z) for z in starts])  # type: ignore[no-untyped-call]
        for d, mdir in defenses.items():
            p_start = np.asarray(load_detector(mdir, extractor.feature_names).predict(X_start))
            for i in detected[d]:
                # The guarantee covers a search only if the original and the escaped file are both in the (loose)
                # population (as adaptive.py).
                in_pop = passes_precondition(plain, malware[i][1], loose=True)
                extras[d, i] = {"p_orig": float(probs[d][i]), "evaded_by_escape": bool(p_start[i] <= taus[d]),
                                "in_population": in_pop,
                                "start_in_population": passes_precondition(plain, starts[i], loose=True)}
    # LIEF's round trip, once per file the LIEF-based attacks would start from (provexp.attacks.lief_check): where LIEF
    # cannot rebuild the file, those attacks are not applicable to it (no task, no row; counted in table.json).
    lief_reason: dict[int, Optional[str]] = {}
    if any(a in LIEF_ATTACKS for a in args.attacks):
        attacked = sorted({i for d in defenses for i in detected[d]})
        lief_reason = dict(zip(attacked, lief_round_trips([starts[i] for i in attacked], args.num_workers)))
        bad = {i: r for i, r in lief_reason.items() if r is not None}
        pl.DataFrame({"name": [malware[i][0] for i in bad], "reason": list(bad.values())},
                     schema={"name": pl.Utf8, "reason": pl.Utf8}).write_parquet(args.outdir / "lief_check.parquet")
        print(f"LIEF round trip: {len(bad)} of {len(attacked)} attacked files cannot be rebuilt; {LIEF_ATTACKS} are not "
              f"applicable to them ({args.outdir}/lief_check.parquet).", flush=True)

    def applicable(atk: str, i: int) -> bool:
        return atk not in LIEF_ATTACKS or lief_reason.get(i) is None

    caps = [max(int(args.budget_frac * len(data)), args.budget_min) for _, data in malware]
    tasks = [(d, atk, malware[i][0], starts[i], taus[d], caps[i], pre[i], extras[d, i])
             for d in defenses for atk in args.attacks for i in detected[d] if applicable(atk, i)]
    with tempfile.TemporaryDirectory(prefix="a1_") as tmp:
        iterations, how_many = BUDGETS[args.budget]
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp), how_many=how_many)
        print(f"Budget {args.budget}: {iterations} iterations, {len(section_pop)} donor sections.", flush=True)
        t0 = time.time()
        models = {d: str(m / "model.txt") for d, m in defenses.items()}
        with get_context("spawn").Pool(args.num_workers, initializer=_init_worker,
                                       initargs=(args.features, models, routes, section_pop, api_calls, args.seed,
                                                 iterations, args.seed_per_file)) as pool:
            rows = map_watchdog(pool, _work, tasks, lost=_lost, stall_timeout=args.stall_timeout)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    if not rows:
        raise RuntimeError("No defense detects any pilot malware; nothing to attack.")
    results = pl.DataFrame(rows)
    results.write_parquet(args.outdir / "results.parquet")
    held_out = [a for a in args.attacks if a not in args.seen]
    seen = [a for a in args.attacks if a in args.seen]
    table: dict[str, Any] = {"protocol": {"fpr": args.fpr, "budget": args.budget, "budget_frac": args.budget_frac,
                                          "budget_min": args.budget_min, "seed": args.seed,
                                          "seed_per_file": args.seed_per_file, "escape": args.escape,
                                          "features": args.features.resolve().as_posix(), "seen": seen,
                                          "routes": routes_spec,
                                          "held_out": held_out,
                                          "split_note": "quick seen/held-out split; formal version is leave-one-out"},
                             "defenses": {}}
    for d in defenses:
        r = results.filter(pl.col("defense") == d)
        entry: dict[str, Any] = {"model": defenses[d].as_posix(), "tau": taus[d], "detected": len(detected[d]),
                                 "routed_to": routes[d][0] if d in routes else None,
                                 "detected_passing_precondition": sum(pre[i] for i in detected[d]),
                                 "per_attack": {}, "groups": {}}
        for atk in args.attacks:
            a = r.filter(pl.col("attack") == atk)
            entry["per_attack"][atk] = {"runs": a.height, "evaded": int(a["evaded"].sum()),
                                        "not_applicable": sum(not applicable(atk, i) for i in detected[d]),
                                        "failed": int((~a["ok"]).sum()), "over_budget": int(a["over_budget"].sum()),
                                        "invalid": int((a["ok"] & ~a["valid"]).sum())}
        for group, atks in (("seen", seen), ("held_out", held_out), ("all", list(args.attacks))):
            entry["groups"][group] = {
                "all": group_evasion(r, atks),
                "truncated": group_evasion(r.filter(pl.col("truncated")), atks),
                "untruncated": group_evasion(r.filter(~pl.col("truncated")), atks),
                "precondition": group_evasion(r.filter(pl.col("precondition")), atks),
                "no_precondition": group_evasion(r.filter(~pl.col("precondition")), atks),
                "uncapped": group_evasion(r.with_columns(evaded=pl.col("ok") & pl.col("valid")
                                                         & (pl.col("p_adv") <= pl.col("tau"))), atks),
            }
        if args.escape != "none" and r.height:
            # Per file (any attack), from the unescaped originals: the escape write alone, the population, and the
            # evasions the guarantee does not cover (original or escaped file outside the population).
            files = r.group_by("name").agg(pl.col("evaded").any(), pl.col("evaded_by_escape").first(),
                                           pl.col("in_population").first(), pl.col("start_in_population").first())
            outside = files.filter(~(pl.col("in_population") & pl.col("start_in_population")))
            entry["escape"] = {"evaded_by_escape": int(files["evaded_by_escape"].sum()),
                               "in_population": int(files["in_population"].sum()),
                               "start_in_population": int(files["start_in_population"].sum()),
                               "evaded_outside_population": int(outside["evaded"].sum())}
        table["defenses"][d] = entry
        g = entry["groups"]
        print(f"{d:16s} detected {len(detected[d]):2d}  seen {g['seen']['all']}  held-out {g['held_out']['all']}",
              flush=True)
    (args.outdir / "table.json").write_text(json.dumps(table, indent=2))
    print(f"Wrote {args.outdir}/results.parquet and table.json", flush=True)


if __name__ == "__main__":
    main()
