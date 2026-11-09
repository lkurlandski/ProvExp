# Resume: the read-only code audit (after the paper mock of 2026-11-09)

Read `docs/status.md` and `PLAN.md` (especially "Decisions of 2026-11-09", decisions 1-6). Open other documents only
as this task needs them (index: `docs/README.md`). The paper mock (`docs/paper-mock.md`) is accepted provisionally.

## The task

PLAN.md, next step 2: **does the code compute the derived table as Definitions 9-10 of the manuscript now define
it?** The code predates Sound Directions round 4. Read-only: report mismatches with file and line, and fix nothing
without the user.

Check, against `manuscript/_d_framework.tex` (Definitions 8-10, Table 2) and the sign table in `_j_proofs.tex`:

1. One direction rule for every monoid: a change raises sum k if its new contribution exceeds the old one, lowers it
   if less; a min pool gets no rule of its own (its neutral element is +infinity).
2. Replacements kept apart from a removal plus an addition (a one-for-one replacement leaves a count unchanged).
3. The readout rules of Table 2 (identity, presence, distinct count, ratio, normalized bin, any other), and which rule
   each EMBER feature gets.
4. The signatures of operations stated as writes, collected from the corpus's item tables, as decision 2 describes.

Where to look: `src/provexp/reach.py` (the direction engine, "C4" in old names), `src/provexp/items.py`,
`src/provexp/featuresets/ember2024/{catalogue,sums}.py`. If the code differs from the definitions but gives the same
table, say so and say whether the paper or the code should change. If a mismatch could change a table's numbers,
say which table and estimate how.

## After the audit

PLAN.md's next steps 3-5: §4, then §5, rewritten in blocks with the user's review after each (`paper-prose` skill),
including the one cheap measurement of decision 6 (cost per candidate, Proposition 1 vs extraction); then the full
simulated review (update `docs/reviews/review-prompt.md` first; it includes decision 6's revisit); then the
research-track items.
