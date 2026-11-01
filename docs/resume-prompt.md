# Resume: ProvExp (after 2026-11-01): the tightening round built; `run/113` is its verdict; read it, apply the stop rule

Read `CLAUDE.md`, then `docs/status.md`'s top block (2026-11-01), `PLAN.md` ("Next steps (2026-11-01)"), and
`docs/direction-A-prime-encoding.md` from "Built: findings (2026-10-31)" to the end of "Built: the tightening round".
Then `docs/direction-A-prime-mock.md`: check 1b (with its 2026-10-31 result and the tightening round), check 2, and
decision 7 (its options). Skim `run/113_ap_tightening.sh` (hypothesis and the proposed reading), `scripts/ap_encoding.py`
(`pinsker_radius`, `dominant_share`, `least_share`, `fano_share`, `Encoding._blocks`, `Program.tied`, `Encoding.fix`),
`scripts/ap_realize.py` (`count_bounds`, `nudge`, `_place`, `realize`), and `scripts/ap_check2_realize.py`.

**Start by recapping for the user in plain language** where things stand, before asking anything:
- the research in three sentences; A' in two (a detector's true worst case against edits an attacker can make, from an
  exact solver over the attacker's choices; a certificate when no edit evades, edits written as a real file when one
  does);
- check 1b (2026-10-31) was a no-go: 0 certified of 13, 6 solver evasions, none evading as files;
- last session (2026-11-01, user chose the bounded tightening round): built section entropies tied to each section's
  byte counts, the exact model of the overlapping 2 KB entropy windows, and realizer repairs. The histogram gap and
  most of the strings gap were the realizer, not the solver's model (the solver's fractional byte counts sat within a
  float32 tolerance of thresholds; the written strings held far more characters than planned). After the section
  step alone, the 3 files still evading wrote at 2.54-4.73 (were 4.13-6.76; threshold 1.10). With everything, a 480 s
  diagnostic left all 6 files undecided;
- `run/113` (the user's): containment, the 6 files at 1,800 s, any evasion written as a file.

## If `run/113` has run

1. Containment: `artifacts/experiments/ap_containment/report.json` must contain every edit (the script stops if not).
   Record it in `run/111`'s comments.
2. Solves: `artifacts/experiments/ap_tightening/{report.json,solves.parquet}`; written files:
   `realized/realized.parquet` (solver vs real score, per-group attribution, differing splits). Logs:
   `artifacts/logs/ap_tightening_{solve,realize}.log`.
3. Apply the stop rule: >= 3 solver evasions that do not evade as files -> decision 7 option 2 (lead A' with another
   use; re-open the mock first). If every file is undecided, the reading proposed in `run/113` (fake evasions gone,
   nothing certified, check 1b still a no-go) needs the user's confirmation; bring it and the options to the user.
   If most evasions realize, propose re-running check 1b in full on the tightened encoding (user, ~30 min+).
4. Record the results in `run/113`'s comments, the encoding note, the mock (check 1b, check 2), status, PLAN.

## If it has not run

Ask the user to run `bash run/113_ap_tightening.sh` (~1 h). Do not run it yourself.

## State of the code

Committed (7d002a4, ce584b8, and the wrap-up); ruff and mypy pass; `tests/test_ap_encoding.py` and
`tests/test_ap_realize.py` pass (light checks). Containment: 1,105/1,105 after the section step; after the block model
only a 16-edit smoke (all contained). The block model made the program ~4x larger (~225 K variables, ~230 K rows, ~43 K
binaries) and each containment check ~6x slower.

Open realizer items, if needed: about 10-20% of the remaining differing byte-entropy and string splits are knife-edge
(within a count of the threshold); `drop_tail` is still not honored. The pooled-window path of the realizer
(`shape_block`, used when an answer has no block counts) is kept only for answers from older encodings.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep the experiments' complexity down; **run only jobs of ~10 minutes or less yourself (anything
over ~15 minutes goes to the user as a `run/` script); estimate from the slowest case before starting**; default 16
workers, never cap workers in Python; state a short hypothesis before each run; add a `run/` script for every experiment
(next number: 114) and record its results in the script's comments once read; re-run `run/111` after any change to the
encoding, and it must contain every edit; commit in logical pieces after ruff and mypy pass; never edit
`tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}`; thresholds at 1% FPR from each model's
  `ts_predictions.parquet` (ref: raw 1.103).
- Saved solutions only load with the encoding they were solved with (variable names must match; `ap_check2_realize`
  checks the count). Run 112's solutions are from the encoding before 7d002a4.
- Solver: HiGHS through `scipy.optimize.milp`; unknown options (the 1e-9 tolerances) pass through verbatim.
- Kill background jobs by PID, not with `pkill -f` on a pattern that also matches your own shell's command line.
