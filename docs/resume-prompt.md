# Resume: ProvExp (after 2026-10-30, fifth session): realizer built, two sound cuts, check 1b with the user; next: read check 1b and realize its evasions

Read `CLAUDE.md`, then `docs/status.md`'s top block (fifth session), `PLAN.md` ("Next steps (2026-10-30, fifth
session)"), and `docs/direction-A-prime-encoding.md` from "Built: findings (2026-10-30, fourth session)" to the end of
"Built: findings (2026-10-30, fifth session)" (incl. "Fifth session, continued" and its "Still open"). Then
`docs/direction-A-prime-mock.md`: Table A'1, "How a solver's answer becomes a file", check 1b (smoke, fourth- and
fifth-session results) and check 2, and decision 7. Skim `scripts/ap_encoding.py` (`row_cuts`, `dominance_cuts`,
`regex_requirements`, `Encoding.__init__`'s windows and strings blocks, `certify`), `scripts/ap_realize.py` (`realize`,
`shape_block`, `_strings`, `_place`, `_spell`, `search_name`), and `scripts/ap_check1b.py` (`attribute`, `_job`).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- A' in two: a detector's true worst case against edits an attacker can make, from an exact solver over the attacker's
  choices; a certificate when no edit evades, edits written as a real file when one does;
- last session (2026-10-30, fifth): the realizer was built (it writes the solver's answer as a file, shaping each
  1 KB block with its neighbour so every 2 KB byte-entropy window lands in the solver's row, and building strings per
  block that carry several regex words, spelled in mixed case). It showed that the fourth session's "real looseness"
  reading was premature (that file was written naively), and it found two genuine loose spots, both fixed soundly:
  nothing capped how random a window could be for its row (now: a low-entropy window has one dominant nibble, e.g. over
  84% of its bytes in row 0), and regex-match counts were not tied to their characters (the solver claimed 2,383
  "system" strings with s's for 531). Containment held after each (1,105 of 1,105 random real edits). On the 4 MB file
  2826a9a5 the solver went from a fake evasion (its answer realizing at 8.63 naive, then 5.97, then 2.75 against the
  threshold 1.10) to finding no evasion in 300 s. A 60 s smoke of check 1b on 7 covered files: all undecided, none
  evaded;
- the user chose to run check 1b before building the exact model of overlapping windows; check 1b (`run/112`, ~30
  min) was handed to the user.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (C3, A4, M_full, G7) without saying what they are.

## State of the code

Everything is committed (last session's commits 85772c5..the wrap-up); ruff and mypy pass; `run/111` (containment)
holds on the current encoding. `tests/test_ap_encoding.py` and `tests/test_ap_realize.py` pass (light checks only; the
full suite was not run).

## Tasks, in order

1. **Read check 1b.** Ask the user whether `bash run/112_ap_check1b.sh` has run (log `artifacts/logs/ap_check1b.log`,
   report `artifacts/experiments/ap_check1b/report.json`, solutions under `.../ap_check1b/solutions/`). If not, wait
   or hand it again; do not run it yourself (~30 min). Read: certified / undecided / solver-evaded on the 13 covered
   files the battery does not evade, split by budget vs file size; the go is >= 4 certified. Record the result in
   `run/112`'s comments (against its hypothesis line), the mock's check 1b, and `docs/status.md`. A no-go goes to the
   user with decision 7's options (3: lead with another use; then 2: a tighter learned baseline), together with what
   the undecided count suggests (a longer time limit is an option to weigh, not a fix).
2. **Realize every solver evasion** (`ap_realize.realize(enc, names, x)`: rebuild `Encoding(SumsFeatureExtractor(), z,
   budget(len(z), 0.05, 524288), 3)`, rebuild the split and leaf variables with `certify`'s construction or compare
   only the encoding's name prefix; load `x` from the `.npy`). Re-extract, score, and attribute by feature group
   (`ap_check1b.attribute` needs the solver's sides: recompute them from `x` and `link_ensemble`'s binaries). State a
   hypothesis first. Where byte-entropy still carries a gap, the exact block model of overlapping windows (its design
   is in the encoding note) goes to the user; where strings or the histogram do, the realizer repairs below.
3. **Realizer repairs** (needed for check 2): knife-edge histogram splits (the solver sits on thresholds and rounding
   to whole bytes tips them: nudge byte counts by one toward the solver's side); section contents aimed at the solver's
   section entropies; honoring `drop_tail`. Add a test for each; keep the round-trip test green.
4. Then check 2 (at least 70% of solver evasions realize), check 3 (expert set; user decision on instrumenting their
   extractor), Table A'1 at pilot scale.

## Scratch drivers you will want (re-create; the scratchpad is session-local)

- `solve_one.py PREFIX SECONDS OUT.pkl`: load the pilot (`a_pv_attacks.load_pilot`), the ref detector
  (`artifacts/models/gbdt/seed-0-s10-ref`, threshold from `ts_predictions.parquet` at 1% FPR: raw 1.103), build the
  encoding, `certify(enc, ens, tau_raw - TOL, SECONDS)`, print only the outcome fields and the `wr*` occupancies, and
  pickle `{name, x, names, sides}`.
- `realize_one.py OUT.pkl`: rebuild the encoding (assert the saved names start with `enc.program.names`), `realize`,
  re-extract, print the real raw score, `attribute(...)` by feature-name prefix, and the splits whose sides differ
  (solver value from `enc.resolve(f)` evaluated at `x`, real value, threshold). One solve of 2826a9a5 takes ~2 min to
  build plus the time limit; one realization ~2 min.
- **Never print the full `choice` dict or the 256 append-byte variables** (large; it tripped a content filter before).

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep the experiments' complexity down; **run only jobs of ~10 minutes or less yourself (anything
over ~15 minutes goes to the user as a `run/` script); estimate from the slowest case before starting**; default 16
workers, never cap workers in Python; state a short hypothesis before each run; add a `run/` script for every experiment
(next number: 113) and record its results in the script's comments once read; re-run `run/111` (~8 min; you may run it)
after any change to the encoding, and it must contain every edit; commit in logical pieces after ruff and mypy pass;
never edit `tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}` (3,655 inputs; the 1,087 sums columns are
  never split on). Thresholds at 1% FPR from each model's `ts_predictions.parquet`.
- Pilot facts: every pilot file is <= 4 MB, so the budget is 512 KB everywhere. The battery misses 20 of the
  unconstrained model's 47 detected files; 7 of those fail the precondition (so check 1b's go needs 4 of 13).
- Realizer facts: a byte is printable (thrember's strings: 0x20-0x7f) exactly when its high nibble is 2-7, so the
  window plan fixes each block's printable count; regex literals that also match another regex (e.g. "powershell" and
  "shell") are counted on the strings as written.
- Solver: HiGHS through `scipy.optimize.milp`; unknown options (the 1e-9 tolerances) pass through verbatim. No
  `highspy` installed. Program size on 2826a9a5: ~57K variables, ~116K rows, ~23K binaries.
- Kill background jobs by PID, not with `pkill -f` on a pattern that also matches your own shell's command line.
