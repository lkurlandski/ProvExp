# Resume: ProvExp (after 2026-10-30, third session): A' step 4 built; next: tighten the encoding, a realizer, then check 1b

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Next steps (2026-10-30, third session)"), and
`docs/direction-A-prime-encoding.md` in full (the design, "Decisions", and "Built: findings" with "Still open"). Then
`docs/direction-A-prime-mock.md`: Table A'1, "How a solver's answer becomes a file", checks 1b and 2 (with the smoke
result), and decision 7. Skim `scripts/ap_encoding.py` (`Program.link`, `Program.solve`, `Encoding.__init__`: the
windows, strings, and entropy blocks), `scripts/ap_containment.py`, `scripts/ap_check1b.py`.

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- A' in two: a detector's true worst case against edits an attacker can make, from an exact solver over the attacker's
  choices; a certificate when no edit evades, edits written as a real file when one does;
- last session (2026-10-30, third): the encoding was designed (user decisions: budget max(5%, 512 KB), at most 3 added
  sections, both flags) and built; its containment test held on all 1,105 random edits (the real file always inside
  the encoded region); solver numerics needed work (a soundness bug from dropped coefficients, fixed); the check 1b
  smoke run certified 0 of 13 and its 3 "evasions" did not realize; the diagnosis points at the byte-entropy windows
  (loose) and at the lack of a realizer (strings);
- the user decided: tighten, then run the full check 1b.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (C3, A4, M_full, G7) without saying what they are.

## Tasks, in order

1. **Tighten the byte-entropy windows** (`Encoding.__init__`, the windows block). A new window in entropy row r has
   nibble entropy in [r/4, (r+1)/4) (thrember: Hbin = int(2 * 2 * nibble entropy)); by concavity the aggregate of a
   row's new windows has nibble entropy at least r/4. Add Gibbs cuts per row: for distributions q (e.g., concentrated
   on each nibble, mixed with uniform so H(q) = r/4), sum_c we[r, c] * (-log2 q_c) >= (r/4) * 2048 * w_r. Same for the
   header windows. State a hypothesis first (how much of the 2826a9a5 gap closes).
2. **Optionally tighten the overlay and section entropies** (section entropies are free in [0, 8]; the overlay's lower
   bound is only the mixture floor). A piecewise lower bound needs binaries per byte value; weigh the cost and say so.
3. **A realizer** (`realize(choice) -> bytes`): lay out the solver's answer as a file. The chosen appended and section
   byte counts; the strings it counts (printable runs separated by a zero byte, including regex-matching strings;
   the solver's `rg` counts need a string per match); windows grouped by entropy row (runs of the bytes each row's
   nibble counts call for); section names from a name search hitting the chosen buckets. The diagnosis script logic
   (scratch, not kept): re-solve a file, then walk the trees with the solver's sides for one feature group and the
   real file's sides elsewhere, to attribute a gap to a group. Consider keeping that as a function in
   `scripts/ap_check1b.py` for check 2.
4. **Re-run containment** (`run/111`, ~8 min; Claude may run it) after the changes; it must hold on every edit.
5. **Check 1b** (`run/112`, ~30 min): hand it to the user to run; update its hypothesis line first. Read its report;
   a no-go goes to the user with decision 7's options (3: lead with another use; then 2: a tighter learned baseline).
6. Then check 2 (at least 70% of solver evasions realize, using the realizer), check 3 (expert set; user decision on
   instrumenting their extractor), Table A'1 at pilot scale.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep the experiments' complexity down; **run only jobs of ~10 minutes or less yourself (the user
restated: anything over ~15 minutes goes to them as a `run/` script); estimate from the slowest case before starting**;
default 16 workers, never cap workers in Python; state a short hypothesis before each run; add a `run/` script for
every experiment (next number: 113) and record its results in the script's comments once read; commit in logical pieces
after ruff and mypy pass; never edit `tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}` (3,655 inputs; the 1,087 sums columns are
  never split on). Thresholds at 1% FPR from each model's `ts_predictions.parquet`. The unconstrained model's
  threshold is raw 1.103.
- Pilot facts: every pilot file is <= 4 MB, so the budget is 512 KB everywhere. The battery misses 20 of the
  unconstrained model's 47 detected files; 7 of those fail the precondition.
- Solver: HiGHS through `scipy.optimize.milp`; unknown options (the 1e-9 tolerances) pass through verbatim. No
  `highspy` installed (not needed so far; it would allow warm starts).
- Kill background jobs by PID, not with `pkill -f` on a pattern that also matches your own shell's command line.
- Write any edit with `scripts/catalogue_checks.py`'s byte-level functions (`add_section(..., before_overlay=False)`),
  never LIEF.
