# Resume prompt: the cost of robustness, step 1 (written 2026-11-15, session 71, at the usage limit)

Paste into a fresh session (Fable 5.2 or Opus). Read `docs/evidence/fable-cost-of-robustness.md` first (the findings;
§4 holds the experiments and their predictions), not the status log.

## What was decided (user, session 71)

- Proceed with **step 1 only**: experiments 1-3 of the findings file's §4, then rewrite §5.4's *Where the cost lies*
  around what evidence a table-respecting detector may use (the table of §2.5), with Propositions B and E as two or
  three sentences. Afterwards discuss the outcomes with the user; **step 2** (the converse of Corollary 1 as a theorem
  with a condition checkable on the signature, after a literature check) only then, if the user agrees.
- **No extractor changes.** Anchored sums (§3.2) and verified signatures (§3.3, experiment 5) are dropped; experiment
  4 is dropped with them. The user rejected the anchoring idea outright (a feature is fixed only until the attacker
  learns to move its anchor). Do not raise it again. The same condition applies to the 203 fixed sums the current
  detector relies on (80% of its split gain); say so plainly in §5.4.
- None of the mathematics is a headline contribution; do not present it as one.

## State of the work (committed, but NOT yet checked with ruff and mypy, and not yet run end to end)

- `pipeline/4-detectors/train/train_classic.py`: new `--param KEY=VALUE` (LightGBM overrides; metrics.json unchanged
  when not given).
- `src/provexp/models/gbdt.py`: `monotone_violations` (checks the constraints from the saved trees), tests in
  `tests/test_models.py` (`TestMonotoneViolations`, 5 pass).
- `pipeline/4-detectors/cost-split/{run.sh,cost_split.py}`: the step. Variants: `droponly` (experiment 1),
  `fixed-only` (experiment 3), `mono-rounds` (3,000 rounds), `mono-{basic,intermediate,advanced}` (experiment 2).
  The pilot command is in `run.sh`'s header.
- **Found:** LightGBM silently falls back to `basic` unless `feature_fraction` and `feature_fraction_bynode` are 1;
  the step sets both to 1 for the three method variants (basic is then the control).
- **Not known yet:** the run time of `intermediate` and `advanced`. A timing run (100 rounds each, into the session
  scratchpad) was in flight when the session ended; redo it. With `basic`, 100 rounds take about 22 s on the pilot
  store, so 3,000 rounds are about 6 minutes; if `advanced` is much slower, lower `ITERATIONS` or hand the user the
  script (jobs over ~10 minutes are the user's to run).

## Next, in order

1. `env/bin/ruff check src tests pipeline`, `env/bin/mypy src tests pipeline`; fix what they report.
2. Time the methods, then run the step at pilot scale (command in `run.sh`'s header). Compare each number with the
   prediction in the findings file's §4 and report misses as misses. Check the `violations` column is 0 for every
   monotone model.
3. Append the results to the findings file (a new section 7), add the step to `pipeline/README.md` and
   `pipeline/4-detectors/README.md`, update `docs/status.md`.
4. Draft the rewrite of *Where the cost lies* (`manuscript/_f_evaluation.tex`, skill `paper-prose`), in a small
   block for the user's review. Pilot numbers; the scale-up re-runs them.
5. Report to the user and ask about step 2.
