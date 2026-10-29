# Resume: ProvExp (after 2026-10-29) — derived C4 rows re-run, all witnesses built; next: step 8 (sums re-encodings)

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-29)"), and
`docs/item-layer-design.md` (component 5 and "The re-encodings come for free", the build-plan table rows 6-9, and
"Build status" through the 2026-10-29 paragraph). Skim `src/provexp/featuresets/ember2024/sums.py` (the four
re-encoded groups), `src/provexp/reach.py` (section "C4"), `scripts/a_directions.py` (`--derive`, `write_sums_layout`,
and where re-encoded rows are marked "hand rule until step 8"), and `scripts/item_checks.py` (G1/G2).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale, now with derived and routed C4 rows; A' mocked, check 0 passed);
- the derivation: steps 1-5 and 7 built; the derived directions equal the hand rules under the precondition except
  three explained features; every class-1 disagreement now has a witness (runs 98, 101), all covered;
- runs 99-100: accuracy within noise (M_full slightly better); routed M_full rows evaded by nothing on the 38/50 pilot
  malware that pass the check; one evasion on the 12 failing files, through the unconstrained branch;
- the order of work: step 8, then 6, then 9, the expert-set row, the A' pilot.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, G3, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first, *before* starting it, including one-off
surveys; longer goes to the user as a `run/` script, default 16 workers, never cap workers in Python); state a short
hypothesis before each run; add a `run/` script for every experiment; commit in logical pieces after ruff and mypy
pass; never edit `tests/reference/`.

## Decided (user, 2026-10-29)

Step 8 before step 6: it is small (about a day), finishes the automation (every C4 row's directions derived, none
hand-written), and step 6 then checks the whole set of declared operations at once.

## Do next

1. **Step 8: the sums re-encodings in the engine.** `sums.py`'s four groups (BodyByteHistogram,
   BodyByteEntropyHistogram, BodyStrings, SectionSplitBuckets) become identity readouts over sums: items restricted
   to the body regions (an item filter), signed buckets read as positive and negative parts. Checks: G1 for sums
   (readouts of the item table vs `SumsFeatureExtractor.feature_vector`, bit-exact on the pilot and fresh files) and
   G3 for sums (derived directions vs the hand rules' re-encoded signs in run 80's `directions.csv`; explain every
   disagreement, witness the class-1 ones). Then `a_directions.py --derive --extractor sums` no longer falls back to
   the hand rules. Smoke-test on a few files first; give the user a `run/` script for anything over ~10 minutes.
2. **Step 6: the catalogue checks (G7).** The declared changes of app/sec/imp/ext/shf/ren/rdb/rsg against
   re-extraction, with adversarial parameter choices, built from our own edit functions.
3. **Step 9:** switch the scripts to the engines, keep the hand rules as test oracles; if steps 6 or 8 move a
   direction, retrain the affected C4 models and re-run Table A1's C4 rows (user-run `run/` scripts, as runs 99-100).
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
  (rare; results are measured by re-extraction); the catalogue's regions do.
- Unchecked explanations, recorded as such: on the failing files the routed rows are evaded less than the
  unconstrained model alone (GAMMA API queries that pass the check are likely scored by the C4 model); the adaptive
  search's routed row would be 0/45 provided no query switches branch.
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`.
