# Resume: ProvExp (after 2026-10-30, second session): A' checks 0-1 done, Table A'1 re-aimed; next: step 4, the edit-choice encoding

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", the A' entry, and "Next steps
(2026-10-30, after A' steps 1-3)"), and `docs/direction-A-prime-mock.md`: the refresh note at its top, Table A'1 and
its reading, "How a solver's answer becomes a file", the go/no-go checks (0, 1 with its result, 1b, 2, 3), and
**decision 7** (the check-1 problem, the four options, and why option 1 was chosen). Then
`docs/feature-provenance-model.md`, Section 4a "C3 (reachable sums and features, add-only)" (the theory step 4
implements). Skim `scripts/ap_check0_solver.py` (Kantchelian's encoding: `Ensemble`, `solve`, `forced`, `forced_box`),
`scripts/ap_check1_learned.py` (how a region is handed to the solver and compared with the battery),
`src/provexp/featuresets/ember2024/catalogue.py` (`add_section`: what the declared edit covers and leaves out),
`src/provexp/items.py` (the readout types: Identity, Ratio, Normalized, Entropy, Max, ...), and `src/provexp/reach.py`
(`predict`, `predict_declared`).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications: A (detectors with guarantees; pilot scale; derived and routed rows) and A' (a detector's true
  worst case against edits an attacker can actually make, from an exact solver: a certificate when no edit evades,
  and edits that can be written as a real file when one does);
- what last session (2026-10-30, second) settled:
  - the reading list (HRAT, Demontis et al., Šrndić & Laskov, verifiable boosted trees): no threat to the claim that
    the edit-to-feature mapping is computed; HRAT means "edit an intermediate structure, not the features" is not ours;
  - all of A' now uses one set of detectors, the 10%-subsample GBDTs; the attack battery (eight toolkit attacks plus
    our adaptive search, real re-extracted evasions only) evades the unconstrained model on 27/47 detected pilot
    malware, PV-seen on 15/22, PV-all on 15/22 (run 109);
  - check 1 (run 110) failed its hypothesis: regions learned from attack outputs are too loose (no coupling between
    features, limits pooled over files), so they certify nothing; they certify only where learned from the same
    attacks PV was built from, which is circular. Decided by the user: Table A'1 now argues "learned and budget-only
    regions are vacuous or circular; only the computed region certifies", decided by a new check 1b after step 4;
  - the declared add-section leaves out the section-table entry and padding, and the PV models split on histogram
    bins those bytes move (3 declared evasions did not hold on the written file): the encoding must include them.
- the first task: step 4.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (C3, A4, M_full, G7) without saying what they are.

## First task: step 4, the edit-choice encoding

Frame the work around the certificate: the question check 1b asks is whether the region computed from the
extractor is tight enough to *prove* that no edit in the catalogue lowers a detector's score below its threshold.

1. **Write a short design note first** (`docs/direction-A-prime-encoding.md`) and show it to the user before code:
   - the solver's variables for append and add-section (byte counts per byte value, number of sections, per section
     its size, name bucket and sign, characteristics, content byte counts), with the byte budget;
   - which features are exact linear functions of them (sizes, counts, hashed buckets: old sums plus what the added
     items contribute, from the item table), and how a tree split on such a feature becomes a linear constraint;
   - sound bounds for the nonlinear readouts (ratios by the mediant bound; normalized histograms as the mixture
     λp + (1 − λ)q; entropy by an interval: concave maximum, vertex minimum), following the model's C3 section;
   - the layout bytes an added section brings (the section-table entry, the padding, SizeOfImage), modeled as part of
     the edit rather than left out;
   - features held fixed and why (pefile's warning flags, as in the adaptive search; anything the precondition check
     rules out), stated as assumptions;
   - the test: for a fixed edit choice, the encoded feature values (or bounds) must contain the values re-extracted
     from the file written by `scripts/catalogue_checks.py`'s byte-level edit, on every pilot file that passes the
     precondition check.
2. **Build it** on top of `scripts/ap_check0_solver.py`'s ensemble encoding; smoke-test on a few files; run the
   containment test.
3. **Check 1b:** on the unconstrained 10% model, the computed region must certify at least 20% of the detected files
   the battery does not evade (the battery's per-file results: `artifacts/experiments/a1/toolkit-v2/results.parquet`
   and `artifacts/experiments/ap_battery/adaptive/adaptive.parquet`). State the hypothesis first. A no-go goes to the
   user with decision 7's options (lead with another use, then a tighter learned baseline).

After step 4: check 2 (at least 70% of solver evasions hold when written and re-extracted), check 3 (the expert set: a
user decision on instrumenting their extractor), Table A'1 at pilot scale.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk (fix one only if an edit in our threat models reaches it or a result depends on it; prefer one
general rule); keep the experiments' global complexity down; run only jobs of ~10 minutes or less yourself (estimate
from the slowest case *before* starting; longer goes to the user as a `run/` script, default 16 workers, never cap
workers in Python); state a short hypothesis before each run; add a `run/` script for every experiment (next number:
111) and record its results in the script's comments once read; commit in logical pieces after ruff and mypy pass;
never edit `tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}` (3,655 inputs: the 2,568 thrember features,
  then 1,087 sums columns neutralized to zero in every split). The solver's vectors come from `SumsFeatureExtractor`;
  the adaptive search pads thrember vectors with zeros (`a1_adaptive.padded_booster`). Thresholds at 1% FPR from each
  model's `ts_predictions.parquet`.
- The engine's feature vector is NaN where no readout models a feature (pefile's warnings); fill those from the file
  or hold them fixed.
- Write any edit with `scripts/catalogue_checks.py`'s byte-level functions (`add_section(..., before_overlay=False)`,
  etc.), never LIEF. Files with no room for another section header take only appends (10 of the 49 detected pilot
  malware on the full-data models).
- Scripts that loop over the 2,000-file set parse each file once and run on a worker pool with tqdm
  (`mininterval=30`) and an `if __name__ == "__main__":` guard.
