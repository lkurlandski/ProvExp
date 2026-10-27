# Resume: ProvExp (after 2026-10-27, third session) — derivation step 7 (directions), then step 6 (catalogue)

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (end of
2026-10-27, third session)"), and `docs/item-layer-design.md` (components 3 and 5, the anticipated disagreements, and
"Build status"). Skim `docs/direction-A-threat-model.md` Section 2 (the hand-written direction rules) and
`scripts/a_directions.py` (what step 7 replaces and is compared against).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale; A' mocked, check 0 passed);
- the derivation: steps 1-5 built and checked last session, what that means, and what is left;
- the order of work.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, A2, M_full, C3) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk; run only jobs of ~10 minutes or less yourself (estimate from the slowest
case first; longer goes to the user as a `run/` script, default 16 workers, never cap workers in Python); state a short
hypothesis before each run; add a `run/` script for every experiment; commit in logical pieces after ruff and mypy
pass; pure additions to the thrember-derived `features.py` (the item-layer code added on 2026-10-27 is ours and may
be edited); never edit `tests/reference/`.

## Where things stand

- **Derivation steps 1-5 are done** (commits 94c8d37..7e60b58, runs 90-93). The instrumented extractor records every
  item (section, string, window, field, import, ...), its contributions to named sums, its member and locating bytes,
  and each feature's formula as data (`src/provexp/items.py`; `items`/`readouts`/`recognize` in `features.py`). The C1
  engine (`src/provexp/reach.py`) predicts an edit's feature vector from the item table, flagging writes to locating
  bytes. Checks: G1 bit-exact on 100 + 2,000 files; G2 projection equals today's provenance; G5 (header byte flips)
  and G6 (random in-place writes) pass after one fix round each, confirmed on fresh files; G4 reproduces Table A0 and
  is bit-equal to the hand predictors on all 289 predicted pairs (so runs 82-87 carry over).
- **Found:** a malformed debug directory crashes pefile and the extractor then treats the file as not a PE
  (`docs/upstream-issues.md` item 5). Recorded soundly in the locating ranges, not patched; the user may revisit.
- **Step 6 (the edit catalogue) is not started.** Only `add_section` is declared (`catalogue.py`, run 79's layout).
  Last session's response was stopped by the safety classifier while it read the attack toolkit's transformation
  code for the new Table A0 rows.

## Do next

1. **Step 7, the C4 engine** (in `reach.py`; `scripts/a_directions.py` gains `--derive`): per operation, the sign
   envelope of every sum over the operation's parameter domain, pushed through the readout rules of the design doc's
   readout table; unions per threat model; the same output shape as run 76's `directions.csv`. Then the disagreement
   report against the hand rules (G3), each class-1 disagreement with a witness; `overlay_size` under append should be
   the first (run 88's witness). Then hand the user the `run/` scripts to retrain the affected C4 models and re-run
   Table A1's C4 rows (the toolkit part takes ~47 min). Operations other than append and add_section need their
   declared deltas from step 6; derive those directions from the design doc's per-operation descriptions and mark
   them provisional until step 6's checks pass.
2. **Step 6, the catalogue**: the remaining operations as byte edits or declared deltas, each with a parameter domain
   (the choices A''s solver will make), and their Table A0 rows (G7), with adversarial parameters (a repeated DLL name,
   an empty or colliding section name, printable bytes next to a string). Build from our own edit functions in
   `scripts/a1_adaptive.py` and the engine, framed as validating the detector's feature model against re-extraction;
   leave the two insertion operations (DOS-header extension, section shift) for last. If a response is stopped by the
   safety classifier again, do not retry the same content: tell the user, and offer a task prompt for another
   session, as was done for the A' mock.
3. Then the expert-set row and the A' pilot (checks 1-3), as in `PLAN.md`.

## Notes

- `papers/`, `REVIEW*.md`, and `make-manuscript.sh` are untracked; leave them uncommitted.
- Useful entry points: `PEFeatureExtractor.item_table`, `.readouts`, `.recognizers`; `provexp.items.evaluate` and
  `project`; `provexp.reach.predict` / `predict_declared`; `scripts/item_checks.py exact|locating|margins`;
  `scripts/a_c1_table0.py` (Table A0 with `engine_*` columns).
- In-place predictions re-count the whole-file byte run (about one extraction on large files); making them local is a
  small change if A''s solver needs speed.
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`
  (now items 1, 4, and 5).
