# Resume: ProvExp (after 2026-11-03, session 3): read run 118, then tier 2, item 8

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`): Section 3 (framework, `_d_framework.tex`), Section 4 (EMBER,
  `_e_instances.tex`), Section 5 (evaluation, `_f_evaluation.tex`), Appendix A (`_j_proofs.tex`). Other sections are
  stubs. `make` and `make check` clean.
- **Tier 1 of the response to the review is done** (`docs/status.md`, top block; `PLAN.md`, "Next steps (2026-11-02,
  the response to the review)"). In the text: Proposition 1 (exact side effects) and the main theorem (sound
  directions); a paragraph naming what is classical (IVM delta rules, provenance semirings, self-adjusting computation,
  the sign domain) and what is new; consolidation separated from the computed response; Table 1 shrunk to one column
  ("built for EMBER, sketched for two others"); research questions; Table 5 with G7's element-stated operations on 2,000
  files; Table 6 with an in-population column and the add-section/overlay row; Table 7 with an additions block (expert
  set 29.1% vs derived 92.2%, both sound); the detector paragraph presenting the 0.0 as an implementation check, with the
  toolkit split, P1/P2, "still detected", and untruncated coverage as the evidence.
- **Session 3 (2026-11-03):** run 117 read: the population is closed (0 of 60,934 edits on passing files leave it);
  the blue count in `_f_evaluation.tex` replaced. **Item 7 built** (`docs/status.md`, top block):
  `provexp.reach.predict_structural` (declared structural edits as byte edits: removed / added / kept items; insertions
  move items; undeclared located items flag), insertion-aware recognizers, and the catalogue's writers and exact
  declarations (`catalogue.write_*`, `catalogue.predict_*`); `catalogue_checks.py` measures declared vs re-extraction.
  Pilot: 0 wrong of 2,120 (330 flagged; inside the population only for a forged Rich marker on Rich-less files and
  entry points in no section). Table 5 has the seven item-stated rows in blue.
- **Decided (user, 2026-11-02):** PV's hole stays 44.4% "proves lowerable", plus a clause on the parser warnings it
  leans on; **no instrumentation-effort claim** (person-days, lines, fix rounds) in the paper.

## The task

1. **Read run 118** (`run/118_item_exactness.sh`, user; G7 + P1 + item-level exactness on the 2,000 files):
   `artifacts/experiments/catalogue_checks/2000-exact/report.json` (keys `exact`, `pass`, `closed`, `<op>.declared`,
   `<op>.declared_mismatches`, `<op>.declared_flags`), log `artifacts/logs/catalogue_checks_2000_exact.log`.
   Hypothesis: 0 wrong under every operation, flags inside the population only for the two abstentions, G7 passes,
   closed. If so: replace Table 5's blue item-stated cells (the `% SYNTHETIC` comment under the table), and record the
   result and runtime in the script's header. If anything is wrong: inspect `edits.parquet` (`declared_detail`), fix
   the declaration (or the recognizer), re-run the pilot, and bring a changed claim to the user.
2. **Tier 2, item 8: the adaptive search over all twelve operations** (`PLAN.md`), scoring candidates with item 7's
   declared predictions (`catalogue.predict_*`, plus `reach.predict` for the in-place ones), each kept step written by
   our own edit; on the routed 10%-store models of Table 7. Go/no-go: at least 24/47 on the unconstrained model; this
   also fixes Table 7's sums rows (their adaptive 0% came from the full-store models). Note: declared prediction of a
   gap insertion is ~5x slower than extraction (windows re-tiled), so the search may simply extract for those.
3. Then items 9-11 (`PLAN.md`): a detector on the hand table; the adversarial-training row; the expert set
   instrumented.

State the hypothesis before each run, in a sentence or two.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Do not edit `run/118_item_exactness.sh` while it runs.
- Run 78's `artifacts/experiments/a_pv/report*.json` predate the `a_pv_hole.py` fix and are left as they were; the
  current readings are in `a_pv/derived-pre`, `a_pv/recheck-hand`, `a_pv/derived-strict`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (the review's block); §6 must cover it.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Runs: only jobs under ~10 minutes yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script for the user (next number 119).
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
