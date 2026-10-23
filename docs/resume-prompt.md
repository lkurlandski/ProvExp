# Resume: ProvExp (after 2026-10-23) — direction A, all gates passed, building A1

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Next steps (end of 2026-10-23)"),
`docs/direction-A-A1-design.md` (the plan for the next experiments), `docs/direction-A-mock.md`, and
`docs/direction-A-threat-model.md` (checks recorded in S4/S5/S6); the model is in `docs/feature-provenance-model.md`.
**Start by recapping the big picture for the user in plain language** (where the research stands, what the three
passed gates mean, what decision is next) before asking anything. Be harsh about novelty; never raise deadlines;
bring any no-go to the user before dropping anything; no result may rest on an extractor quirk.

## Where things stand

- Thesis: feature provenance computes what an attacker's edits can do to a malware detector's features (side effects,
  coupling, reachable values, directions), which robust-detector work gets by hand or from running attacks.
- Direction A's target (approved): Table A1 — monotone (guaranteed-robust) GBDTs whose feature directions come from the
  extractor (C4), against Gimenez et al.'s perturbation-vector (PV) selection, on seen / held-out / adaptive attacks;
  layer-2 re-encodings (raw counts, split signed buckets, merged imports) to keep accuracy.
- **All three screening gates passed this session (2026-10-23):**
  - Check 1 / Table A0 (run 79): C1 predicts edits exactly for the content + item-creating classes where A1–A4 hold;
    add-section predicts the declared count delta, the rest is LIEF layout (A4).
  - Check 2 (run 78): PV selection keeps features carrying 37.8% of its GBDT's gain that C4 proves an attacker can
    lower — a decisive GO. The C4-sound GBDT also beats PV on accuracy.
  - Check 3 (run 77): a sound monotone detector keeps its accuracy (AUC 0.9930–0.9957 vs 0.9976).
- The attack toolkits (secml / secml-malware) are vendored under `third_party/` and patched to run in `env/`
  (Python 3.14 / NumPy 2 / LIEF 1.0); all 8 Gimenez attacks run against our GBDT. `third_party/README.md`.
- Scripts this session: `a_pv_attacks.py`, `a_pv_hole.py` (check 2), `a_c1_table0.py` (check 1); `run/78`, `run/79`.
  Models: run 77 `seed-0-a-*` (C4-sound), run 78 `seed-0-pv` (PV all-8). Results under `artifacts/experiments/a_pv/`
  and `artifacts/experiments/a_c1/`.

## Next — execute A1 (`docs/direction-A-A1-design.md`), gated on five user decisions

**First, get the five decisions** (listed at the bottom of the design doc): (1) re-encoding extraction scale;
(2) seen/held-out split of the 8 attacks (proposal in the doc); (3) adversarial-training / expert baselines now vs
later; (4) malware test-set size for the first pass (50 pilot vs larger); (5) byte/query budgets.

Then, in build order:
1. **Re-encoding ("sums") feature extraction** — the big prerequisite for the decisive C4-on-sums row. Multi-hour
   featurization over the splits; **scope a cost estimate and agree the scale with the user before writing it**
   (`run-long-jobs-yourself`). The features-as-is rows (run 77 models) and the adaptive attack can proceed first.
2. **PV seen/held-out re-derivation** from the existing per-attack deltas (`artifacts/experiments/a_pv/deltas.parquet`)
   → one PV-seen GBDT (user-run, ~6 min like run 77).
3. **Attack-evaluation harness** `scripts/a1_evaluate.py` (+ `run/80`): defenses × attack groups, 1% FPR operating
   point, evasion/robustness, re-extraction ground truth; reuse `a_pv_attacks.py` plumbing (wrappers, parallel pool).
4. **Adaptive C1-guided attack** `scripts/a1_adaptive.py`: search over M scoring candidates with the A0 C1 predictors
   (`a_c1_table0.py`); 0 by construction for C4 rows — a non-zero value is an A1–A4 bug, debugged via A0, not an
   attack success.

## Notes

- `papers/`, `REVIEW*.md`, `make-manuscript.sh` are untracked and not mine to commit; leave them.
- Full EMBER-2024 splits (2.07M train); a GBDT is ~6–7 min at 16 threads — hand runs over ~10–15 min to the user as a
  `run/` script. Attack sweeps parallelise over files (≤16 workers); featurization is hours.
- The duplicate-DLL import quirk is patched (`merge_import_descriptors`); A1 uses the quirk-fixed extractor. The user
  still owes the upstream report (`docs/upstream-issues.md`).
