# Resume: ProvExp (after 2026-10-29, third session) — step 6 built; next: read run 104, then step 9

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-29, third
session)"), and `docs/item-layer-design.md` (the build-plan table row 9, and "Build status" through the step 6
paragraph). Skim `scripts/catalogue_checks.py` (G7), `src/provexp/featuresets/ember2024/catalogue.py`
(`declared_changes`), `src/provexp/featuresets/ember2024/sums.py` (`body_layout`, redefined this session),
`scripts/a_directions.py` (`--derive`), `scripts/a1_adaptive.py` (uses the hand C1 predictors of
`scripts/a_c1_table0.py`), and `run/99_a1_train_derived.sh` / `run/100_a1_toolkit_derived.sh` (what step 9 re-runs).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale, with derived and routed C4 rows; A' mocked, check 0 passed);
- the derivation: steps 1-8 built, every C4 direction computed (the hand rules are only a test oracle); step 6 (the
  catalogue check: every operation applied with adversarial parameters by our own byte-level edits, every moved feature
  checked against the derived signs) found four things, each closed by one general rule, the last by the user's
  decision: a section added after the overlay swallows it, so it is declared and the body is now every section's
  mapped data plus every unclaimed run past the headers;
- what run 104 (run by the user) showed, once read;
- the order of work: step 9, the expert-set row, the A' pilot.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, G7, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first, *before* starting it; longer goes to the
user as a `run/` script, default 16 workers, never cap workers in Python); state a short hypothesis before each run;
add a `run/` script for every experiment; commit in logical pieces after ruff and mypy pass; never edit
`tests/reference/`; do not run the full test suite while the user's jobs run.

## Do next

1. **Read run 104** (`run/104_g7_body_v2.sh`): the 10% sums store re-featurized with the new body regions
   (`artifacts/features/ember2024-sums-10-v2`, log `artifacts/logs/featurize-sums-10-v2.log`: 0 failures?); G1 for
   sums on 2,000 files (`artifacts/experiments/item_checks/exact-sums-2000-v2/report.json`); the derivation
   (`artifacts/experiments/a_directions_derived_sums_2000_v2/`); G7 on 2,000 files
   (`artifacts/experiments/catalogue_checks/2000/report.json`, "pass" and per-operation violations). Hypothesis: G1
   exact and G7 passes, as on the pilot. Explain and witness every violation (a rarer layout, e.g. a section inside the
   headers, could show one); fix by a general rule; record the results in the script's comments.
2. **Step 9:** switch the scripts to the engines and keep the hand rules and predictors as test oracles
   (`a_directions.py`: derived by default; `a1_adaptive.py`: the C1 engine instead of `a_c1_table0`'s predictors,
   checked against them in tests). Then a user-run `run/` script, as runs 99-100: regenerate the training inputs
   (sums layout on `ember2024-sums-10-v2`, and the full store's quirk-fixed files, as run 97 made them), retrain the
   C4 models, and re-run Table A1's C4 rows (toolkit and adaptive columns). Known input changes vs run 99:
   `section:overlay_size` dropped under every threat model (a section added after the overlay removes it);
   `datadirectories:security_virtual_address` up (was fixed) under M_add (a section placed before the overlay moves the
   certificate table). Hypothesis: metrics within noise of run 99.
3. **The expert-set row** (`docs/direction-A-expert-set.md`, decided 2026-10-29): re-implement Gimenez et al.'s 40
   features on pefile with the two assign-instead-of-accumulate quirks patched (pure addition; note upstream), featurize
   the 10% store (user-run, ~10-20 min to be smoke-tested), train the monotone GBDT with all 40 increasing, and report
   it under M_add and M_full.
4. **The A' pilot** (`docs/direction-A-prime-mock.md`).

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- Reading list (`docs/literature-Aprime-2026-10-27.md`, "Not yet read"; harsh read, before building A'): HRAT (Zhao et
  al., CCS 2021; now `papers/HRAT2021.pdf`), Demontis et al., "Yes, Machine Learning Can Be More Secure!" (TDSC 2017,
  added by the user), Šrndić & Laskov (S&P 2014), verifiable boosted tree ensembles (arXiv 2402.14988). The user still
  owes the upstream reports in `docs/upstream-issues.md`.
- G7's edit functions (`scripts/catalogue_checks.py`: `add_section`, `add_imports`, `insert_gap`, `forged_rich`) do
  exactly the declared operation; reuse them for any new witness rather than LIEF, which relays out the file.
- Settled this session: appending a section after the overlay is loader-safe and preserves functionality unless the
  sample locates its overlay from the end of the file (append breaks that too) or from the end of the last section;
  it stays in the threat model. The bytes between sections are not "slack" in our sense (slack = raw data past a
  section's virtual size, which `slk` writes); no operation writes them in place.
- Scripts that loop over the 2,000-file set read and parse each file once and run on a worker pool with a tqdm
  progress bar (`mininterval=30`), with an `if __name__ == "__main__":` guard (forkserver).
- Routed detectors print `tau=0.5000`: each branch decides at its own 1% FPR threshold; not a bug.
- Unchecked explanations, recorded as such: on the failing files the routed rows are evaded less than the
  unconstrained model alone (GAMMA API queries that pass the check are likely scored by the C4 model); the adaptive
  search's routed row would be 0/45 provided no query switches branch.
