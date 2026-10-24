# Resume: ProvExp (after 2026-10-24) — direction A, Table A1 machinery built, reading runs 81/82

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Next steps (end of 2026-10-24)"),
`docs/direction-A-A1-design.md` (the A1 plan, with the five decisions recorded at the end),
`docs/direction-A-mock.md` (Table A1 target), and `docs/direction-A-threat-model.md` (checks in S4/S5/S6); the model
is in `docs/feature-provenance-model.md`. **Start by recapping the big picture for the user in plain language** (where
the research stands, what Table A1 shows, what is next) before asking anything. Be harsh about novelty; never raise
deadlines; bring any no-go to the user before dropping anything; no result may rest on an extractor quirk.

## The thesis and Table A1

- Thesis: feature provenance computes what an attacker's edits can do to a malware detector's features (side effects,
  coupling, reachable values, directions), which robust-detector work otherwise gets by hand or by running attacks.
- Table A1 (approved target): monotone (guaranteed-robust) GBDTs whose feature directions come from the extractor
  (C4), against Gimenez et al.'s perturbation-vector (PV) selection, on **seen / held-out / adaptive** attacks. Rows:
  unconstrained reference; PV-seen; C4 on features (M_add, M_full); C4 on sums (M_add, M_full). The layer-2
  re-encodings ("sums": raw counts, region-restricted, split signed buckets, merged imports) recover the accuracy
  soundness costs. The decisive cell is **adaptive**: 0 for the C4 rows by construction, > 0 for PV-seen.
- All three screening gates passed 2026-10-23 (checks 1/2/3; see the "Earlier" block in PLAN.md and S4/S5/S6).

## What this session (2026-10-24) built — all committed

- **Five A1 decisions taken** (end of `docs/direction-A-A1-design.md`): 10% subsample of every split for the sums
  featurization first; the proposed seen/held-out split is a **quick check only**, with **leave-one-out** (8 PV
  models) the formal version later; baselines later; 50 pilot malware; budgets max(5%, 512 KB) bytes, 100 queries.
- **Sums extractor** `src/provexp/featuresets/ember2024/sums.py` (`SumsFeatureExtractor`, 3,655 features), tests
  `tests/test_ember2024_sums.py`; `scripts/featurize.py --extractor sums --every 10`; `scripts/a_directions.py
  --extractor sums` → `artifacts/experiments/a_directions_sums/`.
- **Run 80 (read):** the 10% sums store (`artifacts/features/ember2024-sums-10`, 0.90 h) and 5 GBDTs. Sums rows beat
  features-as-is: test AUC 0.99527 vs 0.99458 (M_add), 0.99296 vs 0.99189 (M_full), vs 0.99638 unconstrained.
- **Harness** `scripts/a1_evaluate.py` (toolkit columns: 8 attacks x defenses, 1% FPR, re-extracted ground truth,
  seen/held-out split by truncation) and **adaptive search** `scripts/a1_adaptive.py` (scores by **C1-declared
  effect**, not real LIEF re-extraction — see [[a1-adaptive-c1-ground-truth]]; C4 rows 0 by construction, a negative
  `min_delta_logit` on a `--sound` row is an A1-A4 bug). Store-aware (thrember or sums).
- **Sums-space C1 predictors** `predict_append_sums` / `predict_add_section_sums` in `scripts/a_c1_table0.py`
  (`predict_append`/`predict_add_section` refactored to expose their raw dict; A0 regression unchanged). Validated vs
  re-extraction (append exact on 34/36 clean files) and **confirmed up-only** on all 1,979 M_full-sums kept features.
- **`a_pv_hole.py --attacks ... --tag`** for PV-seen (all-8 reproduces run 78 exactly).
- Run scripts: `run/80_a1_sums.sh` (done), `run/81_a1_toolkit.sh` (PV-seen GBDT + toolkit + thrember adaptive),
  `run/82_a1_adaptive_sums.sh` (sums adaptive).

## Do first — read the running/finished runs

**The user is running `run/82` (and `run/81` was running at hand-off).** When they finish, read:
- `artifacts/experiments/a1/toolkit/table.json` — per defense: `tau`, `detected`, per-attack evasion, and per group
  (seen / held-out / all) the fraction evaded, split truncated/untruncated.
- `artifacts/experiments/a1/adaptive/adaptive.json` (thrember) and `artifacts/experiments/a1/adaptive_sums/adaptive.json`
  (sums) — per defense: `detected`, `evaded` (C1-declared), `min_delta_logit`, `soundness_violation`.

**Expected / what to check (state as hypotheses, report failures as such):** seen evasion ~0 everywhere; held-out
evasion > 0 for PV-seen (its hole), ~0 for the M_full C4 rows; adaptive evasion **0 for every C4 row** (any nonzero on
a `--sound` row is an A1-A4 bug — debug via Table A0 / `a_c1_table0.py`, do not accept as evasion) and > 0 for the
unconstrained reference and PV-seen. If PV-seen's adaptive evasion is ~0 (append+add-section may not reach its hole,
which skews to the Rich header + header fields — the scoped remainder below), report it: the separation then rests on
the held-out column + the "no attack runs needed" argument, which the mock flags as not enough alone.

## Then

1. **Assemble Table A1** from the three columns (`docs/direction-A-mock.md`). Lead with TPR at 1% FPR (AUC saturated).
   Decide with the user: is the separation decisive enough to scale (seeds 0-2, 2,000 files, user-run), or strengthen
   the adaptive attack first?
2. **Scoped remainder (A0-sized, lower priority):** C1 predictors for the DOS-stub (Rich header), header-field,
   checksum, rename, and remove operations, so the adaptive search reaches the Rich-header/header-field parts of PV's
   hole (`predict_content_overwrite` models DOS members only). Each needs its EMBER readout mirrored and an A0-style
   validation. append + add-section already reach the histogram/string/section-bucket parts.
3. Then Table A2 (the adaptive attack's own table), then A2 (the second application).
4. Later: the formal leave-one-out PV experiment; full-scale numbers; B and C screening; clean out the old direction's
   materials; update `CLAUDE.md` conventions. The user still owes the upstream thrember report (`docs/upstream-issues.md`).

## Notes

- `papers/`, `REVIEW*.md`, `make-manuscript.sh` are untracked and not mine to commit; leave them.
- Attack sweeps parallelise over files (<=16 workers). The adaptive search is C1-only (no genetic engine), a few
  minutes. GBDTs are ~1-2 min on the 10% store. Full featurization is ~10.5 h (run long jobs via a `run/` script).
- Everything uses the quirk-fixed (merged-imports) extractor; the sums extractor includes it.
