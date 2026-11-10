# Resume: §5 Evaluation, realigned with §3 and §4, block by block

Read `docs/status.md` and `PLAN.md` (decisions 2, 3, 6, 8, 9; next step 3). Then `docs/paper-mock.md`, §5 (the
subsections, claims, and budgets) and the new §4 in the PDF (`manuscript/_e_instances.tex`, Appendix D in
`_j2_ember.tex`), since §5 must use its terms. Open other documents only as the task needs them (index:
`docs/README.md`). Use the `paper-prose` skill, including its 2026-11-10 additions, and read the last entries of
`docs/writing-spec.md` before writing.

**Numbers.** Check `manuscript/main.aux` before naming any section, definition, or table number, and give its title
alongside ("Table 2, The operations of the threat model"). Show concrete old/new text, never a figurative name for an
edit.

## How we work (as for §4, session 28, and Sound Directions round 4)

One block of a few paragraphs at a time, written into `manuscript/_f_evaluation.tex`, then `make` and `make check`,
then shown to the user as rendered text (pdftotext) with what changed. Apply the user's comments before the next
block, log their reactions raw in `docs/writing-spec.md`, commit after each accepted block. §5 is about 3,200 words
(may run 50-75% over while drafting); report the length honestly.

## What §5 must change

- **Vocabulary from the old §3/§4**, now gone: "locating position" (§4.3 says "a position that the parser reads to
  find other items"), operations "stated in bytes / in items" (Table 2 now says "Changes: declared / item tables"),
  "the engine", R3, "modeled features" (§4.2: "the 2,480 features that have items").
- **Overlap with §4:** closure (0 of 60,934) and the 94% of untruncated files are in §4.4; the 58,666 single-byte flips
  are in Appendix D. Recommendation: §5 keeps only the corpus check of the signatures (100- and 2,000-file tables
  identical) and points back for the rest.
- **Decision 3:** §5.2 claims what it tests (the instrumentation and the declared changes are correct, the instance
  abstains exactly where a write lands on a position the parser reads), not "Proposition 1 holds". Headings name the
  claim.
- **Decision 6:** §2 promises three evaluated uses; §5.2 adds the per-candidate cost of scoring by Proposition 1
  against extraction.

## Order

1. **The per-candidate cost measurement** (missing, expected minutes): time scoring a candidate by Proposition 1
   against writing it and extracting it, on the pilot files. Estimate the runtime from the slowest case first; state
   the hypothesis before running; add a `run/` script. Agree the design with the user before code.
2. **Block 1: 5.1 Setup and 5.2** (5.2 meets §4.3 directly).
3. **Block 2: 5.3 Directions; block 3: 5.4 Detectors.**
4. **Then shorten §4 and §5 together** (the user, 2026-11-10: §4 runs ~1,540 words against ~1,000; §4.3 first).
5. Then PLAN.md step 4: update `docs/reviews/review-prompt.md`, run the full simulated review, the truncation
   brainstorm just before or after.

## Loose ends

- `% VERIFY` in §4.2: EMBER 2017/2018 had no parser warnings. Needs Joyce et al.'s PDF in `papers/` (ask the user).
- §6 (`_g_related_work.tex:94`) still says "our margins".
