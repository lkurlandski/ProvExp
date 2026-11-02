# Resume: ProvExp (after 2026-11-02): tier 1 of the response to the review

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`): Section 3 (framework, `_d_framework.tex`), Section 4 (EMBER,
  `_e_instances.tex`), Section 5 (evaluation, `_f_evaluation.tex`), Appendix A (`_j_proofs.tex`). Other sections are
  stubs. `make` and `make check` clean.
- **The harsh review** (`docs/reviews/2026-11-02-body.md`) is triaged with the user. The plan is `PLAN.md`, "Next
  steps (2026-11-02, the response to the review, agreed with the user)": tier 1 (hours), tier 2 (days), tier 3 (the
  second-instance decision). `docs/status.md`'s top block records which of the review's premises held and the user's
  four decisions; `docs/paper-mock.md`, "After the review", records which table changes were adopted.
- **Decided (user, 2026-11-02):**
  - Table 7: the monotone rows' 0.0 is an implementation check. The evidence is (a) the full-catalogue adaptive search
    (tier 2), (b) real tools' outputs staying inside the derived table (284 of 288 in-population toolkit outputs; the 4
    others are LIEF relayouts, and none evades), and (c) "still detected after every attack".
  - Table 6 keeps "every disagreement is a hand error"; it gains an in-population column and the add-section/overlay
    row (an in-population hand error found by G7, run 103).
  - The scope is reduced in the text now (Table 1 shrunk; "shown on EMBER, sketched for two others"); a second instance
    is reconsidered after tier 2.
  - Theorem 1 becomes Proposition 1; Theorem 2 is the main theorem.
  - Deferred: whether the introduction leads with the detector (lean: framework first, results paragraph around it).

## The task: tier 1

Do these in order. Each is minutes, on existing data, or a run under ~10 minutes. State the hypothesis before each run.
1. **P1 (closure).** Add a column to `scripts/catalogue_checks.py`: the precondition evaluated on each edited file.
   Run it on the pilot (~3 min). Go/no-go: no edit takes a passing file to a failing one. Write
   `run/117_p1_closure.sh` for the 2,000-file set (estimate 30-40 min; G7 took 25 min) and hand it to the user.
2. **P2:** one sentence (the pilot and 2,000-file direction tables are byte-identical); the per-cell comparison of the
   two `g3_cells.csv` files if quick.
3. **The toolkit split and "still detected"**: a small script over `artifacts/experiments/a1/toolkit-v2/results.parquet`
   (run 105), `artifacts/experiments/a1/adaptive-v3` (run 108; check which directory is run 108's), and
   `artifacts/experiments/a_pv/deltas.parquet` (run 78), giving per attack: catalogue status, evasion on passing files,
   outputs respecting the derived table; and per detector: still detected after every attack.
4. **PV's hole with the derived table** (`scripts/a_pv_hole.py`); **coverage on untruncated files** and the benign
   rate of non-plain layouts; **timing** (prediction vs re-extraction, from the logs); **instrumentation cost** (lines of
   code, flip-test rounds).
5. **The `.tex` fixes** listed in `PLAN.md` tier 1, item 6. Also: the keyed-count correction in
   `docs/formalization.md` Lemma 3 (factual, allowed under the freeze). Run `make` and `make check` after editing. New
   numbers that wait on a run go in blue (`\synthetic{}`) with a `% SYNTHETIC` comment naming the run.

Then start tier 2 with item 7 (item-level exactness for the item-stated operations), which the adaptive search over all
twelve operations (item 8) reuses.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (2026-11-02, the review's block).
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Runs: only jobs under ~10 minutes yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script for the user (next number 117).
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not
  push.
