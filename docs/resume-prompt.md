# Resume: ProvExp (after 2026-11-03, session 3): read run 118, then tier 2, item 8 (the adaptive search)

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`): Section 3 (framework, `_d_framework.tex`), Section 4 (EMBER,
  `_e_instances.tex`), Section 5 (evaluation, `_f_evaluation.tex`), Appendix A (`_j_proofs.tex`). Other sections are
  stubs. `make` and `make check` clean.
- **Tier 1 of the response to the review is done** (2026-11-02; `PLAN.md`, "Next steps (2026-11-02, the response to
  the review)"; `docs/status.md`). Decided then (user): PV's hole stays 44.4% "proves lowerable" plus a clause on the
  parser warnings; no instrumentation-effort claim in the paper.
- **Session 3 (2026-11-03)** (`docs/status.md`, top block; `docs/item-layer-design.md`, last build-status entry):
  - Run 117 read: the population is closed under the catalogue on the 2,000 files (0 of 60,934 edits on passing files
    leave it). The blue count in `_f_evaluation.tex` is replaced.
  - **Item 7 built:** `provexp.reach.predict_structural` predicts a declared structural edit given as the byte edits
    that perform it. The declaration lists removed, added, and *kept* items; the engine re-recognizes written content,
    moves items past an insertion, and flags an edit that touches the location of an undeclared item. The recognizers
    take insertions. The byte-level writers moved into `featuresets/ember2024/catalogue.py` (`write_*`), next to exact
    declarations (`predict_add_section`, `predict_add_imports`, `predict_insert_gap`, `predict_rename`,
    `predict_zero_entry`). `scripts/catalogue_checks.py` compares each declared prediction with re-extraction (report
    keys `declared`, `declared_mismatches`, `declared_flags`, `exact`).
  - Pilot: **0 wrong of 2,120 declared edits** (330 flagged). Inside the population the declarations abstain only by
    design: a forged Rich marker in an inserted gap on a file without a Rich header, and an added section on a file
    whose entry point lies in no section. Table 5 has seven item-stated rows; their Exact/Flagged/Wrong cells are blue
    (pilot rate scaled) until run 118 is read.
  - Run 118's first start crashed on a file truncated before its first section's data (`shf`'s insertion point past
    the end). Fixed in `write_gap` (the gap goes at the end, byte-identical to the old writer); a writer-only scan of all
    2,000 files raises nothing else. **The user restarted run 118 with `NUM_WORKERS=24`.**
  - **New `run/` convention (user):** every new script reads `NUM_WORKERS="${NUM_WORKERS:-16}"` and passes
    `"$NUM_WORKERS"` to the Python worker flag (`CLAUDE.md`).

## The task

1. **Read run 118** (`run/118_item_exactness.sh`; G7 + P1 + item-level exactness on the 2,000 files):
   `artifacts/experiments/catalogue_checks/2000-exact/report.json` (keys `exact`, `pass`, `closed`, `<op>.declared`,
   `<op>.declared_mismatches`, `<op>.declared_flags`, `<op>.declared_median_ms`, `<op>.extract_median_ms`), log
   `artifacts/logs/catalogue_checks_2000_exact.log`, per-edit rows in `edits.parquet` (`declared`, `declared_detail`).
   - *Hypothesis:* 0 wrong (mismatch or error) under every operation; flags inside the population only for the two
     abstentions; G7 passes and the population stays closed, as in run 117.
   - If it holds: replace Table 5's blue item-stated cells (the `% SYNTHETIC` comment under the table in
     `_f_evaluation.tex`), check the prose under the table still matches, and record the result and runtime in the
     script's header. Keep the in-population/out-of-population split of the flags in `docs/status.md`.
   - If anything is wrong: inspect `declared_detail`, fix the declaration (or the recognizer), re-run the pilot
     (`catalogue_checks.py --outdir .../pilot-exact`, ~4 min), and bring any changed claim to the user before re-running.
2. **Tier 2, item 8: the adaptive search over all twelve operations** (`PLAN.md`; review R1a, R11). Agreed with the
   user on 2026-11-03; start here once run 118 is read (or while it is not yet finished).
   - Today `scripts/a1_adaptive.py` searches appends and added sections only (`menu`, `engine_predictors`, greedy over
     C1-declared predictions; each kept step written by our own edit). Run 108: unconstrained 4/49, PV 16/22, C4 rows 0.
   - Extend the candidates to every operation: imports, rename, header fields, checksum, DOS stub, slack, both gap
     insertions, both removals. Score them with item 7's `catalogue.predict_*` and `reach.predict` for the in-place
     ones, and write each kept step with the catalogue's writers (never LIEF). Predicting a gap insertion is ~5x slower
     than extracting (windows re-tiled past the gap), so the search may simply extract for those two.
   - Run it on the routed 10%-store models of Table 7 (run 105's `artifacts/models/gbdt/seed-0-s10-*` with `--route
     <c4>=ref`). This also fixes Table 7's sums rows, whose adaptive 0% came from the full-store models.
   - *Hypothesis (state again before running):* with imports, rename, header, and DOS operations it beats GAMMA API on
     the unconstrained model. Go/no-go: at least 24/47 there; if it fails, it is not used as the adaptive column until
     strengthened. The monotone rows stay at 0.0 (the implementation check).
   - Smoke-test on a few pilot malware first; the full run goes to `run/119_*.sh` (with `NUM_WORKERS`) if over ~10 min.
3. Then items 9-11 (`PLAN.md`): a detector on the hand table (*hypothesis:* the search, adding a section after the
   overlay, evades it on some in-population files); the adversarial-training row, against item 8's search; the expert
   set instrumented (`featuresets/ember2024/expert.py`).

State the hypothesis before each run, in a sentence or two.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Do not edit `run/118_item_exactness.sh` while it runs; sync its header after.
- Do not change the writers' output (`catalogue.write_*`): G7 (runs 107, 117, 118) and Table 5's edit counts rely on
  the same seeded edits. `catalogue_checks.py` keeps thin wrappers (`add_section`, `add_imports`, `insert_gap`) that
  `a1_adaptive.py`, `ap_encoding.py`, and tests import.
- Three test modules fail to collect for a pre-existing reason (`tests/test_shortcuts_setfield.py`,
  `test_shortcuts_transplant.py`, one more): their scripts moved to `scripts/archive/`. Not caused by item 7.
- Run 78's `artifacts/experiments/a_pv/report*.json` predate the `a_pv_hole.py` fix and are left as they were; the
  current readings are in `a_pv/derived-pre`, `a_pv/recheck-hand`, `a_pv/derived-strict`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (the review's block); §6 must cover it.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Runs: only jobs under ~10 minutes yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script for the user (next number 119), reading `NUM_WORKERS`.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
