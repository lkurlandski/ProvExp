# Resume: ProvExp (after 2026-11-02, session 2): read run 117, then tier 2 of the response to the review

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
- **Measured this session** (scripts committed): P1 on the pilot closed (0 of 3,188 edits leave the population;
  `catalogue_checks.py`'s `precondition_after`); P2 (100 vs 2,000 files: every threat-model column equal);
  `scripts/a1_toolkit_split.py` (252 of 288 toolkit outputs inside the derived table, all 36 others LIEF relayouts,
  none evading the M_full rows; still detected: sums 41/42 vs reference 21/47); PV's hole with the derived table (same
  as the hand rules'; `a_pv_hole.py` bug fixed: warning names have spaces); coverage on untruncated files 94.4%, benign
  non-plain 1.5%; prediction is not faster than re-extraction (median 50 vs 53 ms: no speed claim anywhere).
- **Decided (user, 2026-11-02):** PV's hole stays 44.4% "proves lowerable", plus a clause on the parser warnings it
  leans on; **no instrumentation-effort claim** (person-days, lines, fix rounds) in the paper.

## The task

1. **Read run 117** (P1 on the 2,000 files, started by the user): `artifacts/experiments/catalogue_checks/2000-p1/
   report.json` (keys `closed`, `<op>.leaving_population`, `<op>.leaving_population_instances`), log
   `artifacts/logs/catalogue_checks_2000_p1.log`. Hypothesis: closed (0 edits leave the population) and G7 passes as in
   run 107. If closed: replace the blue `\synthetic{73,063}` in `_f_evaluation.tex` (its `% SYNTHETIC` comment) with the
   measured edit count on passing files, and record the result and runtime in `run/117_p1_closure.sh`'s header (only
   after it finished). If not: the go/no-go fails for that operation; inspect the leaving instances, and fix the
   operation's declaration or the precondition (bring the choice to the user).
2. **Tier 2, item 7: item-level exactness for every item-stated operation** (add section, add imports, both gap
   insertions, rename, both removals; R14). Predict each declared edit's feature vector from the item table plus the
   declared item delta, and compare with re-extracting the file our own byte-level edit writes (`catalogue_checks.py`'s
   edit functions; never LIEF). Build it once: item 8's adaptive search uses it to score candidates. Go/no-go: 0 wrong on
   the 2,000 files (flagged allowed, reported). It replaces Table 5's blue add-section row and adds rows. Smoke-test on
   the pilot; a 2,000-file run over ~10 minutes goes to `run/118_*.sh` for the user.
3. Then items 8-11 of tier 2 (`PLAN.md`): the adaptive search over all twelve operations on the routed 10%-store
   models of Table 7 (go/no-go: at least 24/47 on the unconstrained model; this also fixes Table 7's sums rows, whose
   adaptive 0% came from the full-store models); a detector on the hand table; the adversarial-training row; the expert
   set instrumented.

State the hypothesis before each run, in a sentence or two.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Do not edit `run/117_p1_closure.sh` while it runs.
- Run 78's `artifacts/experiments/a_pv/report*.json` predate the `a_pv_hole.py` fix and are left as they were; the
  current readings are in `a_pv/derived-pre`, `a_pv/recheck-hand`, `a_pv/derived-strict`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (the review's block); §6 must cover it.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Runs: only jobs under ~10 minutes yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script for the user (next number 118).
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
