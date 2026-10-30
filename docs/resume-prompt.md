# Resume: ProvExp (after 2026-10-30) — direction A's runs read and the adaptive search fixed; next: the A' pilot

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-30)"),
`docs/direction-A-prime-mock.md` (the update note at its top first, then the whole mock: Table A'1, "How a solver's
answer becomes a file", the go/no-go checks, the harsh notes on novelty, the decisions), and
`docs/literature-Aprime-2026-10-27.md` (incl. "Not yet read" and "Harsh read for A'"). Skim
`scripts/ap_check0_solver.py` (Kantchelian's encoding, HiGHS via scipy; run 89), `scripts/a1_adaptive.py`
(`engine_predictors`, `menu`, `greedy_search`), `src/provexp/reach.py` and `src/provexp/featuresets/ember2024/catalogue.py`
(`add_section`) for what the C1 engine predicts, `docs/feature-provenance-model.md` Section on C3 (reachable sums), and
`docs/direction-A-A1-design.md` ("Step 9", the last section).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications: A (detectors with guarantees, pilot scale, derived and routed C4 rows) and A' (worst-case
  evaluation that can be realized as real files; mocked, check 0 passed: the exact solver decides at our model's size in
  under 34 s, but directions alone certify nothing on a non-monotone detector, so the region needs magnitudes);
- what last session (2026-10-30) settled:
  - run 107: the catalogue check (G7: every edit's feature changes against the derived directions) passes on all
    73,063 edits on the 2,000-file set; the training inputs equal the pilot's;
  - run 105: the six C4 models retrained on the derivation after G7; test metrics within noise of run 99; on files
    that pass the precondition check, no seen attack evades any routed C4 row and no held-out attack evades the M_full
    rows (M_add rows only by the header-field attack, which is outside M_add);
  - run 106, the expert-set row (Gimenez et al.'s 40 features, quirks patched): monotone AUC 0.844, TPR 29% at 1% FPR,
    as mocked; it detects only 8 of the 50 pilot malware and no attack evades it there; unconstrained on the same
    features 0.978, evaded 24/40 by the M_add attacks;
  - two bugs in the adaptive search, found because its unconstrained row jumped from 10/49 to 28/49: (1) the declared
    add-section removes the overlay, but each step was written with LIEF, which keeps it, so every later step claimed
    the removal again; (2) the engine leaves the 88 pefile-warning features NaN, which a GBDT reads as missing. Fixed
    (the user chose our own byte-level edit for each step; unmodeled features keep the current file's values); run 108:
    unconstrained 4/49, PV 16/22, C4 rows 0, and every declared evasion holds on the written file. The C4 models never
    saw the warning features, so their results did not depend on the bug. 10 of the 49 detected pilot malware have no
    room for another section header.
- the order of work: the A' pilot, steps 1-7 in `PLAN.md` "Next steps (2026-10-30)".

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G7, M_full, C3, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first, *before* starting it; longer goes to the
user as a `run/` script, default 16 workers, never cap workers in Python); state a short hypothesis before each run;
add a `run/` script for every experiment and record its results in the script's comments once read; commit in logical
pieces after ruff and mypy pass; never edit `tests/reference/`; do not run the full test suite while the user's jobs
run.

## Do next (the A' pilot)

Steps 1-3 are cheap and each can stop the direction; do them before building the encoding.

1. **Reading list, harsh read** (no code): HRAT (Zhao et al., CCS 2021; `papers/HRAT2021.pdf`), Demontis et al., "Yes,
   Machine Learning Can Be More Secure!" (TDSC 2017), Šrndić & Laskov (S&P 2014), verifiable boosted tree ensembles
   (arXiv 2402.14988). For each: does it already compute what an edit does to the features, for an extractor with
   hashing, normalization, ratios, and entropy? Chen et al. (USENIX Security 2020) did it for PDF tree-path features;
   our claim is only the computed mapping for EMBER's kind. Record in `docs/literature-Aprime-2026-10-27.md`; bring
   any threat to novelty to the user before code.
2. **Refresh the mock** (`docs/direction-A-prime-mock.md`; fold in its update note): the pilot uses the engine; the
   battery's measured cells (toolkit-v2 per-file results plus run 108's adaptive results, union per file); the expert
   row's facts. Show the user what changed.
3. **Check 1:** constraints learned from the toolkit's adversarial outputs (per feature: the directions seen and the
   largest change seen; check 0 showed directions alone are vacuous) in the check-0 solver, on PV-seen. Go if it
   certifies robust at least a third of the files the battery evades. Hypothesis (the mock's): it does, because
   learned limits only cover the changes and magnitudes the seen attacks happened to produce, while the C1-guided
   search reaches others.
4. **The edit-choice encoding** (C3: not built yet; the main build): append and add-section first. Variables: bytes
   appended and their byte counts; sections added, the hash bucket and sign each name hits, size, byte mix. Linear
   features from the item table; sound bounds for ratios, normalized histograms, entropy. Test: a fixed choice
   reproduces the engine's prediction (the engine is checked against re-extraction).
5. **Check 2:** solver evasions on the unconstrained GBDT, written with our byte-level edits
   (`scripts/catalogue_checks.py`: `add_section(..., before_overlay=False)`), re-extracted; go at >= 70% realized.
6. **Check 3, the expert set** (a decision for the user when reached): instrument their extractor so the engine can
   feed the solver (recommended; their 40 features are counts and sums) or encode it by hand; judge on its 8 detected
   pilot files or add files from the 2,000-file set for this row.
7. **Table A'1 at pilot scale**; a `run/` script if over ~10 min.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- The engine's feature vector is NaN where no readout models a feature (pefile's warnings). Anything that scores an
  engine prediction with a model must fill those from the file (as `engine_predictors` now does), or drop them.
- The adaptive search runs only on the thrember-space store (no recognizers for the sums store's re-encoded groups; the
  engine cannot read the expert extractor). Its declared add-section ends the file (no overlay, pefile's rule) and
  each step is written by `catalogue_checks.add_section(..., before_overlay=False)`; files with no room for another
  section header take only appends.
- G7's edit functions (`scripts/catalogue_checks.py`: `add_section`, `add_imports`, `insert_gap`, `forged_rich`) do
  exactly the declared operation; reuse them for any new witness or realization rather than LIEF, which relays out the
  file. On low-alignment images, `add_section` puts the raw offset at the virtual address and `insert_gap` does not
  apply.
- Scripts that loop over the 2,000-file set read and parse each file once and run on a worker pool with a tqdm
  progress bar (`mininterval=30`), with an `if __name__ == "__main__":` guard (forkserver).
- Routed detectors print `tau=0.5000`: each branch decides at its own 1% FPR threshold; not a bug.
