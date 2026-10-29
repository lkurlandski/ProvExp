# Resume: ProvExp (after 2026-10-29, second session) — step 8 built; next: read run 102, then step 6 (catalogue checks)

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-29, second
session)"), and `docs/item-layer-design.md` (component 3, the build-plan table rows 6 and 9, and "Build status" through
the step 8 paragraph). Skim `src/provexp/featuresets/ember2024/catalogue.py` (`declared_changes`, `REGION_OPS`,
`add_section`), `src/provexp/reach.py` (section "C4"), and `scripts/a_c1_table0.py` (Table A0, which step 6 extends).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale, with derived and routed C4 rows; A' mocked, check 0 passed);
- the derivation: steps 1-5, 7, and 8 built; every C4 direction is now computed (the hand rules are only a test
  oracle); the derived directions equal the hand rules under the precondition except three explained features, all
  witnessed; step 8 (the re-encoded groups) matched the hand rules on every cell at pilot scale;
- what run 102 (2,000 files, run by the user) showed, once read;
- the order of work: step 6, then 9, the expert-set row, the A' pilot.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, G3, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first, *before* starting it, including one-off
surveys; longer goes to the user as a `run/` script, default 16 workers, never cap workers in Python); state a short
hypothesis before each run; add a `run/` script for every experiment; commit in logical pieces after ruff and mypy
pass; never edit `tests/reference/`.

## Do next

1. **Read run 102** (`run/102_step8_sums.sh` steps 3-4): G1 for sums on the 2,000-file set
   (`artifacts/experiments/item_checks/exact-sums-2000/report.json`), G3 for sums
   (`artifacts/experiments/a_directions_derived_sums_2000/g3.json`, "sums"; `g3_sums_cells.csv`), and whether its
   `*-pre*` training inputs equal `a_directions_derived_sums/` (run 99's). Hypothesis: all hold, as on the pilot.
   Explain every disagreement; witness the class-1 ones. Record the results in the script's comments.
2. **Step 6: the catalogue checks (G7).** The declared changes of app/sec/imp/ext/shf/ren/rdb/rsg against
   re-extraction, with adversarial parameter choices (a repeated DLL name, an empty or colliding section name,
   printable bytes next to an existing string), built from our own edit functions. Now also the body items: an added
   section's body region, the overlay's body region under append, and that insertions leave the body sums unchanged.
3. **Step 9:** switch the scripts to the engines, keep the hand rules as test oracles; if step 6 moves a direction,
   retrain the affected C4 models and re-run Table A1's C4 rows (user-run `run/` scripts, as runs 99-100).
4. The expert-set row (`docs/direction-A-expert-set.md`); the A' pilot (`docs/direction-A-prime-mock.md`).

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, and `make-manuscript.sh` are untracked; leave them.
- Scripts that loop over the 2,000-file set should read and parse each file once and run on a worker pool with a
  tqdm progress bar (`mininterval=30`, plain prints for log lines), as `scripts/a_structure_witness.py`: the user asked
  for this after a serial pass took ~40 min. Multiprocessing scripts need an `if __name__ == "__main__":` guard
  (Python 3.14 starts workers with forkserver).
- Routed detectors print `tau=0.5000`: the routed score is normalized so each branch decides at its own 1% FPR
  threshold; that is not a bug.
- The experiments' slack and DOS edits (`attack.region_parts`, `a1_adaptive.py`) do not exclude loader-read bytes
  and treat a section of virtual size 0 as all slack (rare; results are measured by re-extraction); the catalogue's
  regions do neither.
- Unchecked explanations, recorded as such: on the failing files the routed rows are evaded less than the
  unconstrained model alone (GAMMA API queries that pass the check are likely scored by the C4 model); the adaptive
  search's routed row would be 0/45 provided no query switches branch.
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`.
