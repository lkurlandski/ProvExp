"""
Direction A, Table A1's adaptive column (docs/evidence/direction-A-A1-design.md): a soundness test for our monotone detectors.

FOR ACADEMIC SECURITY RESEARCH ONLY. This is a defense-evaluation harness. A sound monotone detector (the C4 rows)
carries a guarantee: no loader-safe edit in the threat model M (docs/evidence/direction-A-threat-model.md, Section 1) can lower
its score. This script checks that guarantee on our own pilot samples against our own detectors, by trying the edits M
allows and recording whether any lowers the score. For a C4 row the expected result is "no edit helps" (0 by
construction, Gimenez Prop. 1 + C4 + A1-A4); a decrease below -1e-6 is an A1-A4 bug to debug against Table A0, not an
evasion. For the PV-seen row, which is sound only against the attacks it was built from, the same search realizes the
hole check 2 measured. Nothing is deployed; files are written only so their features can be re-extracted and re-scored.

The search decides by C1 predictions of each candidate edit's *declared* effect (the attacker's reachable set under M;
decided 2026-10-24), never by re-extracting a written file: the declared effect leaves out the layout bytes (padding,
the section-table entry, SizeOfImage; A4), so a real re-extraction would mix M effects with the layout's. The C4 rows
are therefore 0 by construction here; the C1-vs-reextraction gap (A4) is reported alongside (`p_adv_real`). Each
chosen step is materialized by our own byte-level edit (pipeline/1-audit/catalogue-checks/catalogue_checks.py), exactly the declared operation,
so the next step starts from the file the declaration describes. This part provides the material (goodware donors),
the loader-safe edits, and the greedy search over C1.

`--search beam` (run 127) replaces the greedy search with a beam search with restarts and a realistic scoring budget
(`beam_search`); it re-extracts every file it keeps. `--num_workers` runs one search per (defense, file) in a pool.

Every edit keeps the original content in place -- each section's raw data, the overlay, the DOS header and stub, and
the header fields it does not itself set -- so it stays inside M and does not exploit the writing tool's layout
choices; `lief_preserves` checks this for the LIEF edits.

Outputs, in `{outdir}/`:
    adaptive.parquet   one row per (defense, file): the C1-declared result (evaded, queries, best op sequence,
                       min_delta_logit = the most negative score change any candidate's declared effect produced)
    adaptive.json      per defense: detected, evaded (C1-declared), rate by truncation, min_delta_logit, and any
                       C4-row soundness violation (min_delta_logit < -1e-6: an A1-A4 bug, debug via Table A0)

Usage (smoke):
    PYTHONHASHSEED=0 python pipeline/5-attacks/adaptive/adaptive.py --outdir /tmp/a1a --num_malware 2 --queries 30 \
        --threat_model M_full --defense pv-seen=artifacts/models/gbdt/seed-0-pv \
        --features artifacts/features/ember2024
"""

from __future__ import annotations

from argparse import ArgumentParser
from multiprocessing import get_context
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import pefile

from provexp.attacks.adaptive import THREAT
from provexp.attacks.adaptive import _attack_file
from provexp.attacks.adaptive import _init_worker
from provexp.attacks.adaptive import _lost
from provexp.attacks.adaptive import _parse_defenses
from provexp.attacks.adaptive import padded_booster
from provexp.attacks.adaptive import target_buckets
from provexp.data.files import PROTOCOLS
from provexp.data.files import load_attacked
from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.data.tabular import load_manifest
from provexp.detectors import model_threshold
from provexp.featuresets.ember2024 import catalogue
from provexp.featuresets.ember2024.escapes import WRITES as ESCAPES
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.models.erdalt import ERDALTDetector
from provexp.parallel import map_watchdog

__all__: list[str] = []



################################################################################
# Donors: goodware material the edits draw on (as the GAMMA attacks do)
################################################################################


################################################################################
# In-place byte edits (loader-ignored fields; no parse change, no length change)
################################################################################


################################################################################
# Structural edits via LIEF (add a section / imports, rename a section)
################################################################################


################################################################################
# The greedy C1 search (declared effects only)
#
# NOTE: the search covers append and add-section, both in M_add and so in every threat model. They reach the
# histogram, byte-entropy, string, and section-bucket parts of PV selection's hole (check 2). Their declared effects
# come from the C1 engine (provexp.reach.predict for the append, catalogue.add_section for the declared section, over
# the instrumented extractor's item table; derivation step 9). The hand predictors of pipeline/1-audit/hand-table/hand_table.py remain
# only as the engine's test oracle (tests/test_a1_adaptive.py). The engine flags an append where a structure lies past
# the end of the file (the files that fail the precondition check); the search then skips that candidate. The
# re-encoded groups of the sums store have no recognizers yet, so the search runs against the thrember-space
# defenses only (as since run 100), and its evasion is a conservative lower bound.
################################################################################


################################################################################
# The twelve-operation search (item 8): exact predictions, materialized by the catalogue's writers
#
# Item 7 made every structural operation's effect predictable exactly (run 118: 0 wrong of the declared edits), so the
# search can score every operation of the threat model (docs/evidence/direction-A-threat-model.md), not just append and
# add-section. Each candidate is scored by the exact prediction of our own byte-level edit -- catalogue.predict_* for
# the structural operations (add section, add imports, rename, both removals; the two gap insertions are simply
# extracted, ~5x cheaper than predicting them) and reach.predict for the in-place overwrites (header fields, checksum,
# DOS region, slack) -- so the predicted score equals the re-extracted score of the file the step writes, and the
# chosen step is materialized by exactly that writer (never LIEF). The monotone (C4) rows stay 0 by construction: a
# sound detector's score cannot fall under any operation of M.
################################################################################


################################################################################
# The beam search (strong attacks, 2026-11-04): a realistic scoring budget
#
# The greedy search above stops at the first step whose ~25 random candidates contain no improvement and is capped at
# 100-200 scored candidates to match the toolkit; on the undefended model 24 of the 39 files it does not evade stall
# that way about a fifth of the way to the threshold, and 15 run out of queries about halfway (run 119). Scoring a
# candidate costs one prediction (~0.1 s), so a realistic attacker scores thousands. The beam search keeps the `beam`
# best files found so far (parents and children compete, so the beam never gets worse), draws `draws` menus per kept
# file per step, and restarts from the original file when the best score has not improved for `patience` steps. Every
# kept file is written by our own byte-level edits and re-extracted, so its score is real, not predicted.
################################################################################


################################################################################
# Workers (one search per (defense, file); a pool over files with --num_workers > 1)
################################################################################


################################################################################
# Main
################################################################################


def main() -> None:
    import polars as pl

    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--sound", nargs="*", default=[], help="Defense names that carry the C4 guarantee (a negative "
                        "min_delta_logit on one is an A1-A4 bug; on any other defense it is just the search working).")
    parser.add_argument("--features", type=Path, required=True, help="The feature store the defenses were trained on.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--protocol", choices=tuple(PROTOCOLS), default="pilot",
                        help="pilot: the pilot list and donors, thresholds on ts; scaleup: the evaluation list, --donors, "
                             "thresholds on vl (provexp.data.files.PROTOCOLS).")
    parser.add_argument("--donors", type=Path, default=None, help="Scale-up: the donor list (training goodware).")
    parser.add_argument("--donor_db", type=Path, default=EMBER2024_DATA / "tr", help="The SimpleDB split of --donors.")
    parser.add_argument("--threat_model", choices=["M_add", "M_shift", "M_full"], default="M_full")
    parser.add_argument("--operations", nargs="*", default=None, help="Restrict to these operation names "
                        "(default: every operation of the threat model).")
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--candidates", type=int, default=12, help="Kept for compatibility; the full menu self-sizes.")
    parser.add_argument("--target_buckets", type=int, default=8, help="Section-hash buckets the targeted names aim at.")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--num_malware", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--search", choices=["greedy", "beam"], default="greedy", help="greedy: runs 108/119; beam: "
                        "the strong-attack search (beam_search).")
    parser.add_argument("--beam", type=int, default=3, help="beam: files kept per step.")
    parser.add_argument("--draws", type=int, default=2, help="beam: menus drawn per kept file per step.")
    parser.add_argument("--patience", type=int, default=3, help="beam: steps without a new best before a restart.")
    parser.add_argument("--checkpoints", type=int, nargs="*", default=[200, 1000, 5000],
                        help="beam: query counts at which evasion is also reported.")
    parser.add_argument("--num_workers", type=int, default=1, help="Processes, one search per (defense, file).")
    parser.add_argument("--stall_timeout", type=float, default=2700.0)
    parser.add_argument("--score", choices=["predicted", "real"], default="predicted", help="predicted: candidates "
                        "scored by the computed effects, declined ones skipped (runs 108-133); real: every candidate "
                        "written and extracted with the sums extractor, none declined (RealEngine; needs a sums store).")
    parser.add_argument("--escape", choices=["none", *ESCAPES], default="none", help="A field write applied to every "
                        "malware before the attack, taking it out of the population (pipeline/1-audit/escapes/escape_audit.py; R7).")
    parser.add_argument("--save_rows", action="store_true", help="Save the best file's feature row per (defense, file) "
                        "as {outdir}/rows/{defense}/X.npy + files.parquet, the layout train_classic.py --augment "
                        "reads (iterated adversarial training; R18). Needs --score real.")
    args = parser.parse_args()
    if args.save_rows and args.score != "real":
        raise ValueError("--save_rows needs --score real (the rows must be in the store's layout).")

    import lief
    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    defenses = _parse_defenses(args.defense)

    manifest = load_manifest(args.features)
    extractor = fix_quirks(PEFeatureExtractor())
    if manifest["feature_names"][: extractor.dim] != extractor.feature_names:
        raise RuntimeError(f"The store {args.features.as_posix()} ({manifest['feature_set']}) does not start with the "
                           "thrember features: the C1 engine has no recognizers for other layouts.")
    ops = tuple(args.operations) if args.operations else THREAT[args.threat_model]
    if args.score == "real":
        vector: PEFeatureExtractor = SumsFeatureExtractor()
        if manifest["feature_names"] != vector.feature_names:
            raise RuntimeError(f"--score real needs a store with the sums extractor's layout, not {args.features}.")
    else:
        vector = extractor
    print(f"Scoring {args.score} ({vector.dim} features); operations {','.join(ops)}.", flush=True)

    malware, goodware = load_attacked(args.protocol, args.pilot_files, args.db, args.donors, args.donor_db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    # (name, the file the search starts from, the unescaped original). With an escape the start is the escaped file --
    # the escape write is the attack's fixed first move, now an `ent` edit in the threat model -- and detection and
    # evasion are counted from the unescaped original (detected original, undetected end file; R7, run 143).
    attacks: list[tuple[str, bytes, bytes]] = []
    if args.escape != "none":
        for name, data in malware:
            try:
                out = ESCAPES[args.escape](pefile.PE(data=data), len(data))
            except Exception:  # noqa: BLE001
                out = None
            if out is not None and not catalogue.passes_precondition(extractor, out):
                attacks.append((name, out, data))
        print(f"Escape {args.escape}: {len(attacks)} of {len(malware)} malware written and out of the strict "
              "population; detection and evasion counted from the unescaped originals.", flush=True)
    else:
        attacks = [(name, data, data) for name, data in malware]
    print(f"Pilot: {len(attacks)} malware, {len(goodware)} goodware donors; threat model {args.threat_model}.",
          flush=True)

    config = {"ops": ops, "pilot_files": args.pilot_files, "db": args.db, "search": args.search,
              "queries": args.queries, "seed": args.seed, "budget_frac": args.budget_frac,
              "budget_min": args.budget_min, "beam": args.beam, "draws": args.draws, "patience": args.patience,
              "checkpoints": tuple(args.checkpoints), "score": args.score, "save_rows": args.save_rows}
    tasks: list[tuple[str, str, float, list[tuple[int, int]], str, bytes, float, bool, bool]] = []
    for d, mdir in defenses.items():
        booster = padded_booster(mdir, vector.dim)
        tau = model_threshold(mdir, args.fpr, PROTOCOLS[args.protocol])
        Xp = (np.stack([vector.feature_vector(start) for _, start, _ in attacks])  # type: ignore[no-untyped-call]
              if isinstance(booster, ERDALTDetector) else None)
        targets = [(b, sign) for b in target_buckets(booster, extractor.feature_names, args.target_buckets, Xp)
                   for sign in (-1, 1)]
        detected = 0
        for name, start, original in attacks:
            p_orig = float(booster.predict(vector.feature_vector(original).reshape(1, -1))[0])  # type: ignore[no-untyped-call]
            if p_orig > tau:  # attack only what this defense detects on the unescaped original
                # The guarantee covers a search only if the original and the file it starts from are both in the
                # (loose) population: an `ent` escape keeps an original in it (run 142's closure check), SizeOfImage
                # raised alone (image_size, not an operation of M_full) takes it out.
                in_pop = catalogue.passes_precondition(extractor, original, loose=True)
                start_in_pop = in_pop if start is original else catalogue.passes_precondition(extractor, start,
                                                                                              loose=True)
                tasks.append((d, str(mdir), tau, targets, name, start, p_orig, in_pop, start_in_pop))
                detected += 1
        print(f"  {d}: tau={tau:.4f}, {detected} detected (unescaped original)", flush=True)

    t0 = time.time()
    if args.num_workers > 1:
        with get_context("spawn").Pool(args.num_workers, initializer=_init_worker, initargs=(config,)) as pool:
            rows = map_watchdog(pool, _attack_file, tasks, lost=_lost, stall_timeout=args.stall_timeout)
    else:
        _init_worker(config, malware=malware, goodware=goodware)
        rows = []
        for i, t in enumerate(tasks):
            rows.append(_attack_file(t))
            if (i + 1) % 10 == 0:
                print(f"  progress: {i + 1}/{len(tasks)} tasks in {time.time() - t0:.0f}s", flush=True)
    rows = [r for r in rows if r is not None]
    if args.save_rows:
        for d in defenses:
            mine = [r for r in rows if r["defense"] == d]
            out = args.outdir / "rows" / d
            out.mkdir(parents=True, exist_ok=True)
            np.save(out / "X.npy", np.asarray([r["phi"] for r in mine], dtype=np.float32).reshape(len(mine), -1))
            pl.DataFrame([{"name": r["name"], "label": 1, "p_clean": r["p_clean"], "p_adv": r["p_adv_real"],
                           "ops": r["ops"], "evaded": r["evaded"]} for r in mine]).write_parquet(out / "files.parquet")
        for r in rows:
            r.pop("phi")
    print(f"Searched {len(tasks)} (defense, file) pairs in {time.time() - t0:.0f}s.", flush=True)

    results = pl.DataFrame(rows) if rows else pl.DataFrame(schema={"defense": pl.Utf8})  # nothing detected
    results.write_parquet(args.outdir / "adaptive.parquet")
    report: dict[str, Any] = {"threat_model": args.threat_model, "operations": list(ops), "fpr": args.fpr,
                              "queries": args.queries, "target_buckets": args.target_buckets,
                              "budget_frac": args.budget_frac, "budget_min": args.budget_min, "seed": args.seed,
                              "search": args.search, "beam": args.beam, "draws": args.draws,
                              "patience": args.patience, "checkpoints": args.checkpoints,
                              "score": args.score, "escape": args.escape,
                              "defenses": {}}
    for d in defenses:
        r = results.filter(pl.col("defense") == d)
        detected = r.height
        evaded = int(r["evaded"].sum()) if detected else 0
        worst = float(r["min_delta_logit"].min() or 0.0) if detected else 0.0  # type: ignore[arg-type]
        report["defenses"][d] = {
            "detected": detected, "evaded": evaded, "rate": (evaded / detected) if detected else None,
            "min_delta_logit": worst,
            "evaded_real": int(r["evaded_real"].sum()) if detected else 0,
            "carries_guarantee": d in args.sound,
            "soundness_violation": (d in args.sound) and worst < -1e-6,
            "rate_truncated": _rate(r.filter(pl.col("truncated"))),
            "rate_untruncated": _rate(r.filter(~pl.col("truncated"))),
        }
        if args.escape != "none" and detected:
            # Detection and evasion count from the unescaped original (R7, run 143): how many detected originals the
            # escape write alone already evaded, how many detected originals were in the (loose) population, how many
            # escaped files the search started from were, and the evasions the guarantee does not cover (original or
            # start outside the population).
            report["defenses"][d]["evaded_by_escape"] = int(r["evaded_by_escape"].sum())
            report["defenses"][d]["in_population"] = int(r["in_population"].sum())
            report["defenses"][d]["start_in_population"] = int(r["start_in_population"].sum())
            out_pop = r.filter(~(pl.col("in_population") & pl.col("start_in_population")))
            report["defenses"][d]["evaded_outside_population"] = int(out_pop["evaded"].sum()) if out_pop.height else 0
        if args.search == "beam" and detected:
            report["defenses"][d]["evaded_at"] = {str(q): int(r[f"evaded_at_{q}"].sum()) for q in args.checkpoints}
            report["defenses"][d]["mismatches"] = int(r["mismatches"].sum())
        v = report["defenses"][d]
        flag = "  *** C4 SOUNDNESS VIOLATION (debug via Table A0)" if v["soundness_violation"] else ""
        at = "  at " + ", ".join(f"{q}: {n}" for q, n in v["evaded_at"].items()) if "evaded_at" in v else ""
        print(f"{d:16s} detected {detected:2d}  evaded {evaded:2d}{at}  min_delta_logit {worst:+.4f}{flag}",
              flush=True)
    (args.outdir / "adaptive.json").write_text(json.dumps(report, indent=2))
    print(f"Wrote {args.outdir}/adaptive.parquet and adaptive.json", flush=True)


def _rate(r: Any) -> Any:
    if r.height == 0:
        return None
    return int(r["evaded"].sum()) / r.height


if __name__ == "__main__":
    main()
