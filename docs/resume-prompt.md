# Resume: ProvExp (after 2026-10-28) — step 7 built; read runs 99-100, then the remaining witnesses

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (2026-10-28)"), and
`docs/item-layer-design.md` (components 3 and 5, the anticipated disagreements, and "Build status" through the
2026-10-28 paragraph). Skim `src/provexp/reach.py` (section "C4"), the C4 section of
`src/provexp/featuresets/ember2024/catalogue.py`, and `scripts/a_directions.py --derive`.

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale; A' mocked, check 0 passed);
- the derivation: steps 1-5 and 7 built; locating ranges now per structure; the derived directions equal the hand
  rules under the precondition except three explained features; strict soundness over every possible file leaves
  almost no features (9 under M_full); the signature witness;
- the user's precondition decision, runs 99-100, and the order of work.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G3, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first; longer goes to the user as a `run/`
script, default 16 workers, never cap workers in Python); state a short hypothesis before each run; add a `run/`
script for every experiment; commit in logical pieces after ruff and mypy pass; never edit `tests/reference/`.

## Decided (user, 2026-10-28)

Files that fail the precondition go to the unconstrained detector (no guarantee for them; coverage reported); the
>4 MB files stay; the strict detector (9 features under M_full) is one sentence, not a row. `a1_evaluate.py` routes C4
rows (`--route`); `run/99_a1_train_derived.sh` retrains the six C4 models from the derived directions and
`run/100_a1_toolkit_derived.sh` re-runs Table A1's toolkit and adaptive columns. The user started both at the end of
the 2026-10-28 session; check `artifacts/logs/train_classic-gbdt-0-*-pre*.log`, `a1_evaluate_derived.log`, and
`a1_adaptive_derived.log` (ask the user if they are still running). When done, read `artifacts/experiments/a1/toolkit-derived/table.json` (the groups' `precondition` / `no_precondition`
splits) and `adaptive-derived`, record them in the run scripts' comments and in `docs/direction-A-A1-design.md` (section "Re-run with derived
directions"). Check the scripts' hypotheses: test metrics within noise of runs 77/80; routed C4 rows on passing
files evaded as in run 81 (0 for M_full); failing files as the reference.

## Do next

1. Remaining witnesses: entry_name_hash under sec (entry point outside every section), Rich under ext and under hdr
   (on a file without a Rich header; three hdr fields lie in pefile's Rich search range), exports and relocations past
   the end. Add each to a script with a `run/` script, as `scripts/a_signature_witness.py` (run 98).
2. The adaptive search (`a1_adaptive.py`) is not routed: its C4 rows hold for files that pass the check; report the
   failing files with the unconstrained row.
3. Step 8 (sums re-encodings in the engine), step 6 (catalogue checks, G7; the declared deltas of app/sec/imp/ext/shf/
   ren/rdb/rsg are provisional), the expert-set row, the A' pilot.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, and `make-manuscript.sh` are untracked; leave them.
- The experiments' slack and DOS edits (`attack.region_parts`, `a1_adaptive.py`) do not exclude loader-read bytes
  (rare; results are measured by re-extraction); the catalogue's regions do.
- Multiprocessing scripts need an `if __name__ == "__main__":` guard (Python 3.14 starts workers with forkserver).
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`.
