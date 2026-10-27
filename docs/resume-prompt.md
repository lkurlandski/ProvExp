# Resume: ProvExp (after 2026-10-27, fourth session) — derivation step 7 (directions), starting with locating ranges

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (end of
2026-10-27, fourth session)"), and `docs/item-layer-design.md` (components 2, 3 and 5, the readout table, the
anticipated disagreements, and "Build status", including the fourth-session paragraph). Skim
`docs/direction-A-threat-model.md` Section 2 (the hand-written direction rules) and `scripts/a_directions.py` (what
step 7 replaces and is compared against).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- the two applications (A done at pilot scale; A' mocked, check 0 passed);
- the derivation: steps 1-5 built and checked; last session's finding (appending can complete structures past the
  end of the file, witnessed on the signature features) and the pefile fix; what step 7 now has to do;
- the order of work.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (G1, A2, M_full, C3) without saying what they are.

Standing rules: be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk, **but do not chase quirks for their own sake: fix one only if an edit in our
threat models can reach it or a result depends on it, and prefer one general rule to per-bug patches** (user,
2026-10-27); **keep the experiments' global complexity down** (one precondition row is the limit the user accepted;
excluding files over 4 MB is an option to weigh, not decided); run only jobs of ~10 minutes or less yourself
(estimate from the slowest case first; longer goes to the user as a `run/` script, default 16 workers, never cap
workers in Python); state a short hypothesis before each run; add a `run/` script for every experiment; commit in
logical pieces after ruff and mypy pass; pure additions to the thrember-derived `features.py` (the item-layer code
and the pefile guard added on 2026-10-27 are ours and may be edited); never edit `tests/reference/`. The user may
accept slight deviations from EMBER-2024 (a LIEF reimplementation, dropping parse-error features) if strongly
pressured; raise them only then.

## Where things stand

- **Derivation steps 1-5 are done** (runs 90-93): the item table, readouts as data, locating ranges, and the C1
  engine (`src/provexp/items.py`, `src/provexp/reach.py`; `items`/`readouts`/`recognize` in `features.py`), all
  checks passing.
- **Found (fourth session): the hand direction rules miss that appending can complete structures past EOF.** pefile
  skips directory data, sections, or the signature table that headers point to past the end of the file; appended
  bytes become them. 12 of 100 pilot files are exposed (mostly truncated at the dataset's 4 MB cap). Witness: on
  pilot malware `4294f2f053c2...`, appending zeros to offset 8,841,232 plus a 10,160-byte certificate table from a
  signed pilot file raises `num_certs` 0 -> 1 (authenticode is constrained to fall only and carries 13-16% of the
  M_full C4 models' gain). The witness was a scratch script; rebuild it as `scripts/a_signature_witness.py` (with a
  `run/` script) in step 7's report. Exports, relocation flags, entry name hash: same mechanism, not yet witnessed.
- **Decided (user):** strict directions plus one precondition row (no locating range past EOF; else a fallback
  detector of always-safe features).
- **Fixed:** pefile's directory parsers crashed on unreadable structures (debug type 20, dynamic relocations, two
  rarer paths) and thrember then zeroed every PE feature. One guard (`features.py`, last section, installed in pefile
  at import): a crash loses only that directory. Run 94 rewrote the 394 affected stored rows (47 in the sums store;
  old values in `artifacts/features/*/patches/`); no pilot file was affected. `docs/upstream-issues.md` item 5.

## Do next

1. **Split `pe_locating` into per-structure locating ranges** (sound now that a directory crash cannot spread):
   header fields located by e_lfanew and the header-size fields; sections by the section table (plus past EOF when
   pefile dropped one); each directory's items by its entry and data; the overlay by every extent. Re-run G5 at the
   item level (a header byte flip that changes an item must lie in that item's members or locating ranges), smoke
   test first; then G1/G4/G6 must still pass.
2. **Step 7, the C4 engine** (`reach.py`; `scripts/a_directions.py --derive`), as in `PLAN.md`: sign envelopes from
   each kind's term vocabulary (checked against every recorded item), hash images by enumeration, the readout rules,
   unions per threat model, run 76's output shape; the disagreement report against the hand rules (G3) with
   witnesses (signature, `overlay_size`, then exports, relocation flags, entry name hash). Non-append operations:
   provisional deltas from the design doc until step 6.
3. **Hand the user `run/` scripts** for the precondition row, the retraining of the affected C4 models on the patched
   stores, and the re-run of Table A1's C4 rows (toolkit part ~47 min).
4. Then step 6 (the catalogue, from `scripts/a1_adaptive.py`'s edit functions; insertions last), the expert-set row,
   and the A' pilot. If a response is stopped by the safety classifier, do not retry the same content: tell the user
   and offer a task prompt for another session.

## Notes

- `papers/`, `REVIEW*.md`, `docs/checkpoint-prompt.md`, and `make-manuscript.sh` are untracked; leave them
  uncommitted.
- Item kinds and their sum families (from 30 pilot files): general bytes/field/pe; histogram bytes; byteentropy
  window; strings string; header field; section section/entry/file/overlay; imports library/import; exports export;
  datadirectories field/relocs; richheader rich_pair; authenticode certificate_table. Every PE-parsed kind carries
  locating ranges past EOF on some file today, because of `pe_locating`.
- Useful entry points: `PEFeatureExtractor.item_table`, `.readouts`, `.recognizers`; `provexp.items.evaluate` and
  `project`; `provexp.reach.predict` / `predict_declared`; `scripts/item_checks.py exact|locating|margins`;
  `scripts/a_c1_table0.py`; `scripts/refeaturize_nonpe.py` (re-extracts a store's non-PE rows after a parse fix).
- Multiprocessing scripts need an `if __name__ == "__main__":` guard (Python 3.14 starts workers with forkserver).
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user); Šrndić & Laskov (S&P 2014); verifiable
  boosted tree ensembles (arXiv 2402.14988). The user still owes the upstream reports in `docs/upstream-issues.md`
  (items 1, 4, and 5, which now includes thrember's broad `AttributeError` catch).
