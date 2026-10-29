# Resume: ProvExp (after 2026-10-29, fourth session) — runs 107, 105, 106 ran overnight; next: read them, then A'

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-29, fourth
session)"), and `docs/item-layer-design.md` ("Build status" from the step 6 paragraph on: step 9, run 104 and the
plain-layout clauses). Skim `src/provexp/featuresets/ember2024/catalogue.py` (`plain_layout`, `precondition`,
`add_section`), `scripts/catalogue_checks.py` (G7), `scripts/a1_adaptive.py` (`engine_predictors`),
`src/provexp/featuresets/ember2024/expert.py`, `docs/direction-A-expert-set.md`, and the three run scripts
(`run/107_g7_plain_layout.sh`, `run/105_step9_retrain.sh`, `run/106_expert_set.sh`).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A at pilot scale, with derived and routed C4 rows; A' mocked, check 0 passed);
- the derivation: steps 1-9 built; every C4 direction is computed, and the hand rules and hand C1 predictors are only
  test oracles. Last session: run 104 (G7, the catalogue check, on 2,000 files) found five rare layouts. One was our
  check's own error: on low-alignment images, which Windows maps flat, its edits moved file data off its address. The
  other four are now excluded by the precondition check (the user's decision), which also requires a plain layout:
  sections within SizeOfImage, SizeOfImage no larger than the sections need, headers that hold only headers, and
  pefile's overlay starting where a section's data ends. 8 of 1,682 passing files leave; no direction changed;
- the expert-set row: Gimenez et al.'s 40 features re-implemented on pefile, matching their LIEF code on the test
  files except for parser differences; their two assign-instead-of-accumulate quirks patched; their DOS-stub flag is
  constant 1 under current LIEF;
- what runs 107, 105, and 106 showed, once read;
- the order of work: the A' pilot, after the reading list.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, G7, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first, *before* starting it; longer goes to the
user as a `run/` script, default 16 workers, never cap workers in Python); state a short hypothesis before each run;
add a `run/` script for every experiment and record its results in the script's comments once read; commit in logical
pieces after ruff and mypy pass; never edit `tests/reference/`; do not run the full test suite while the user's jobs
run.

## Do next

The user chained the runs overnight (`bash run/107_g7_plain_layout.sh ; bash run/105_step9_retrain.sh ; bash
run/106_expert_set.sh`); each starts even if the one before failed. Check that each finished (logs under
`artifacts/logs/`) before reading it.

1. **Read run 107** (`artifacts/experiments/catalogue_checks/2000-v3/report.json`, "pass" and per-operation
   violations; the derivation in `artifacts/experiments/a_directions_derived_sums_2000_v3/`; the script's last step
   prints any training-input difference from the pilot's). Hypothesis: G7 passes on every edit, strict and
   precondition variants; the training inputs equal the pilot's. Any violation: explain and witness it with our own
   byte-level edits (`scripts/catalogue_checks.py`), close it by a general rule, and redo run 105 if the training
   inputs change.
2. **Read run 105** (step 9: the six C4 models retrained into `-v2` suffixes; Table A1's toolkit columns in
   `artifacts/experiments/a1/toolkit-v2/table.json`, the adaptive search on the C1 engine in
   `artifacts/experiments/a1/adaptive-v2/adaptive.json`). Compare with runs 99-100. Hypothesis: test metrics within
   noise of run 99 (overlay_size dropped, security_virtual_address up under M_add); routed C4 rows evaded by no seen
   attack on passing files and the M_full rows by no held-out one; the adaptive C4 rows 0 by construction (a negative
   min_delta_logit on a sound row is a bug to debug). Note that the passing set is now smaller by the plain-layout
   clauses. Record in `docs/direction-A-A1-design.md`.
3. **Read run 106** (the expert-set row: `-s10-expert-mono` with all 40 features constrained increasing, and the
   unconstrained `-s10-expert`; toolkit columns in `artifacts/experiments/a1/expert/toolkit/table.json`). Its training
   and attack steps were not smoke-tested; check the logs first. Hypothesis (from the mock): the monotone model far
   below the derived C4 rows (AUC ~0.80, TPR at 1% FPR ~30%), the unconstrained one higher; toolkit evasion of the
   monotone model low, any of it from the attacks outside M_add (DOS header, section renaming). Report it under M_add
   and M_full (split the attacks by threat model) in `docs/direction-A-expert-set.md`.
4. **The A' pilot** (`docs/direction-A-prime-mock.md`), after the reading list (`docs/literature-Aprime-2026-10-27.md`,
   "Not yet read"; harsh read): HRAT (Zhao et al., CCS 2021; `papers/HRAT2021.pdf`), Demontis et al., "Yes, Machine
   Learning Can Be More Secure!" (TDSC 2017), Šrndić & Laskov (S&P 2014), verifiable boosted tree ensembles (arXiv
   2402.14988).

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (now including item 6, Gimenez et al.'s
  quirks and DOS-stub flag).
- The adaptive search runs only on the thrember-space store: the C1 engine has no recognizers for the sums store's
  re-encoded groups, and it cannot read the expert extractor at all. The search refuses the sums store.
- The engine's declared add-section ends the file, so it predicts no overlay (pefile's rule). The hand predictor keeps
  the overlay (it models LIEF), so the oracle test compares them only off the overlay features.
- Their `modified_dos_stub` under current LIEF is constant 1; ours compares bytes. Their `nb_imported_functions` counts
  imports by name (repeats included, ordinals left out), and section entropy is over the raw data up to the virtual
  size: both as their code does, not as the paper reads.
- G7's edit functions (`scripts/catalogue_checks.py`: `add_section`, `add_imports`, `insert_gap`, `forged_rich`) do
  exactly the declared operation; reuse them for any new witness rather than LIEF, which relays out the file. On
  low-alignment images, `add_section` puts the raw offset at the virtual address and `insert_gap` does not apply.
- Scripts that loop over the 2,000-file set read and parse each file once and run on a worker pool with a tqdm
  progress bar (`mininterval=30`), with an `if __name__ == "__main__":` guard (forkserver).
- Routed detectors print `tau=0.5000`: each branch decides at its own 1% FPR threshold; not a bug.
