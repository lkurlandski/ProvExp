# Resume: ProvExp (after 2026-10-27, second session) — build the derivation, steps 1-6

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (end of
2026-10-27, second session)"), `docs/item-layer-design.md` (the build plan for this session: read it in full), and
`docs/direction-A-prime-mock.md` (what A' needs from the derivation). Skim `docs/direction-A-summary.md` if direction
A's results are not fresh.

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything.
The user found the last sessions' state hard to follow ("discombobulated"), so give the one-page picture first:
- the research in three sentences;
- the two applications (A done at pilot scale; A' mocked and check 0 passed);
- the one engineering task both need (the derivation);
- the order of work.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, A2, M_full, C3) without saying what they are.

Standing rules:
- Be harsh about novelty.
- Never raise deadlines.
- Bring any no-go to the user before dropping anything.
- No result may rest on an extractor quirk.
- Run only jobs of ~10 minutes or less yourself, estimated from the slowest case first. Anything longer goes to the
  user as a `run/` script (default 16 workers; never cap workers in Python).
- State a short hypothesis before each run.
- Add a `run/` script for every experiment.

## Where things stand

- **Direction A** (sound monotone detectors from computed feature directions) is complete at pilot scale. Every check
  passed (`docs/direction-A-summary.md`). Its directions (`scripts/a_directions.py`) and edit-effect predictors
  (`scripts/a_c1_table0.py`, `scripts/a1_adaptive.py`) are still **hand-written**. The paper's claim that they are
  computed from the extractor needs the derivation.
- **Direction A'** (realizable worst-case evaluation of a detector) has its mock in
  `docs/direction-A-prime-mock.md`. The user accepted all six recommendations:
  - lead with Table A'1;
  - the exact solver searches over the attacker's edit choices, so every evasion is a concrete edit;
  - rows: unconstrained, PV-seen, PV-all, Gimenez et al.'s expert-set detector, and later adversarially trained
    models; our C4 detector is a sanity check only;
  - the main baseline is constraints learned from the toolkit attacks;
  - Chen et al. (USENIX Sec 2020, PDF) is the closest precedent.
- **A' check 0 passed** (run 89, `scripts/ap_check0_solver.py`). Kantchelian's encoding with HiGHS (via scipy) is
  exact, and every decision took at most 34 s on the 500-tree model. Key finding: feature *directions* alone certify
  nothing on a non-monotone detector, because without a limit a feature can move arbitrarily far. So the region must
  bound how far each feature can move within the byte budget (C3). The edit-choice formulation provides this, and
  the learned-constraints baseline needs magnitudes too.
- **The overlay gap is settled** (run 88, `scripts/a_overlay_witness.py`):
  - only `section:overlay_size` is affected; it becomes two-sided under appending;
  - the `body_*` sums never drop;
  - no pefile patch: its rule is the extractor's real behavior;
  - the hand rule changes with the next C4 retraining (after step 7).
- **The design doc's five open decisions are settled** (end of `docs/item-layer-design.md`):
  - keep `provenance` until G2 passes, then make it a projection of `items`;
  - strict only;
  - re-run A1's C4 rows after step 7;
  - G1 also on the 2,000-file set;
  - the syntactic regex test.

## Do next: derivation steps 1-6 in one stretch (the user asked for them together, in order)

1. **Step 1:** `src/provexp/items.py`: Item, ItemTable, the contribution vocabulary, readout types and evaluators,
   and the projection to BoxMatrix. Unit tests in the style of `tests/`.
2. **Steps 2-3:** `items(...)` emitters and readouts as pure additions to `features.py`.
   - First the simple groups: general, histogram, header, datadirectories, exports, imports (both classes),
     richheader, authenticode.
   - Then the hard ones: strings, byteentropy, section (max pools, overlay, entry selection, signed hashes).
   - **Stopping point:** G1 (recorded totals through the declared readouts reproduce the extractor *exactly*, on the
     100 pilot files and the 2,000-file set; about a minute with 16 workers) and G2 (the projection matches today's
     provenance).
3. **Step 4:** locating ranges for every item kind; the byte-flip check G5. The full G5 run is a few minutes with 16
   workers; smoke-test it on one file first.
4. **Step 5:** the C1 engine (`src/provexp/reach.py`). **Stopping point:** G4 (reproduce Table A0).
5. **Step 6:** the edit catalogue with parameter domains (`featuresets/ember2024/catalogue.py`); A0 rows for the nine
   operations not yet covered (G7). The domains are what the A' solver will choose over.

Then, in later sessions:
- step 7, the C4 engine, with the disagreement report against the hand rules (the overlay case should be the first
  disagreement), then the user-run retraining and re-run of Table A1's C4 rows;
- the expert-set row;
- the A' pilot (checks 1-3).

The effort table in the design doc is in human days and far too high (user).

Commit in logical pieces (after each stopping point at least). Before each commit, `env/bin/ruff check src tests
scripts` and `env/bin/mypy src tests scripts` must pass. Pure additions to the thrember-derived `features.py` only;
never edit `tests/reference/`.

## Notes

- `papers/`, `REVIEW*.md`, and `make-manuscript.sh` are untracked; leave them uncommitted.
- The safety classifier stopped several drafts on 2026-10-27 (the literature notes, the design doc, the A' mock).
  Frame the A' material as detector evaluation and hardening, which it is. If a document is blocked twice, offer the
  user a task prompt for another session, as was done for the mock.
- Still unread for A':
  - HRAT (Zhao et al., CCS 2021; paywalled, ask the user);
  - Šrndić & Laskov (S&P 2014);
  - verifiable boosted tree ensembles (arXiv 2402.14988; the fallback solver).
- The user still owes the upstream reports in `docs/upstream-issues.md` (thrember item 1; secml-malware item 4).
- Everything uses the quirk-fixed (merged-imports) extractor; the sums extractor includes it.
- Gimenez et al.'s 40-feature extractor: github.com/PFGimenez/certifiably-robust-malware-detectors-by-design,
  `static_features_extraction.py:get_features`.
