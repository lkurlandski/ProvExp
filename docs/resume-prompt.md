# Resume: ProvExp (after 2026-10-28) — step 7 built; the precondition decision, then witnesses and retraining

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
- the decision waiting on the user, and the order of work.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G3, M_full, C4) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, but fix a quirk only if an edit in our threat models can reach it or a result
depends on it, and prefer one general rule to per-bug patches; keep the experiments' global complexity down; run only
jobs of ~10 minutes or less yourself (estimate from the slowest case first; longer goes to the user as a `run/`
script, default 16 workers, never cap workers in Python); state a short hypothesis before each run; add a `run/`
script for every experiment; commit in logical pieces after ruff and mypy pass; never edit `tests/reference/`.

## The decision waiting on the user (ask first)

Files that fail the precondition (something the parse is located through lies past the end of the file, so appending
can complete it): 12/100 pilot files (all malware, 8 cut at the 4 MB cap), 318/2,000 (73 benign, 245 malware, 231
truncated). The planned fallback "detector of always-safe features" is the strict model, which keeps 9 features under
M_full (6 constant). Options: treat failing files as malicious (false positives on benign failing files); send them to
the unconstrained model (no guarantee on them; report coverage); the strict 9-feature model. Also: keep the strict row
as a row or as one sentence; exclude files over 4 MB.

## Do next (after the decision)

1. Remaining witnesses: entry_name_hash under sec (entry point outside every section), Rich under ext and under hdr
   (on a file without a Rich header; three hdr fields lie in pefile's Rich search range), exports and relocations past
   the end. Add each to a script with a `run/` script, as `scripts/a_signature_witness.py` (run 98).
2. `run/` scripts for the user: retrain the affected C4 models from `artifacts/experiments/a_directions_derived`
   (`{tm}-pre[-quirkfixed].neutralize.txt` / `.monotone.tsv`), the precondition check at inference
   (`catalogue.precondition`), and the re-run of Table A1's C4 rows (toolkit part ~47 min).
3. Step 8 (sums re-encodings in the engine; `--derive` refuses `--extractor sums` until then), step 6 (catalogue
   checks, G7; the declared deltas of app/sec/imp/ext/shf/ren/rdb/rsg are provisional), the expert-set row, the A' pilot.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, and `make-manuscript.sh` are untracked; leave them.
- The experiments' slack and DOS edits (`attack.region_parts`, `a1_adaptive.py`) do not exclude loader-read bytes
  (rare; results are measured by re-extraction); the catalogue's regions do.
- Multiprocessing scripts need an `if __name__ == "__main__":` guard (Python 3.14 starts workers with forkserver).
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`.
