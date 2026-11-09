# Resume: two small §3 edits, then §4 (after the code audit of 2026-11-09)

Read `docs/status.md` and `PLAN.md` (especially "Decisions of 2026-11-09"). Open other documents only as the task
needs them (index: `docs/README.md`). The code audit is done and its record is
`docs/evidence/code-audit-sound-directions.md`; read its findings 3-6 before touching §3 or §4.

**Table numbers:** cite tables by their compiled numbers or their labels, and check `manuscript/*.aux` when unsure. Do
not rely on the numbers in PLAN.md or status.md, which use an older numbering. Compiled: Table 1 = readout rules
(`tab:fw:readouts`, §3); Table 2 = the catalogue (`tab:instances:catalogue`, §4); Tables 3-5 = side effects,
directions, detectors (§5); Table 7 = the sign table (`tab:fw:signs`, appendix).

## Step 1: two §3 edits, awaiting the user's choice

The previous session explained both edits to the user; ask for the two choices if the user hasn't given them, then
edit, `make`, and `make check`.

1. **Table 1's "presence" row** (`_d_framework.tex`: line ~171, the list of readout forms; line ~382, the table row;
   line ~395, the paragraph after the table; `_j_proofs.tex` line ~99, the proof). Some EMBER readouts are not
   literally in the table: max/min with a floor of 0, one item's value with default 0, and a presence bit scaled by
   128. The code gives them $d_k$.
   - *Option A (Claude's pick):* widen the row to "monotone: $g(s_k)$, $g$ nondecreasing, e.g. $[s_k > 0]$ → $d_k$",
     with matching wording in the other three places. It also covers log-scaled and clipped counts in other domains.
   - *Option B:* leave §3 as it is, and add a sentence to §4 saying these readouts are written as identities (a pool of
     nonnegative values starting from 0; an additive sum written by one item; the scale is irrelevant).
2. **The example after Definition 7** (lines ~346-348): replace "such as appending any content" with "such as
   overwriting a range of positions with any content", optionally adding ", which record the items each position
   belongs to". Necessary: the code collects changes from item tables only for the seven in-place writes. Append, like
   the other structural operations, is declared and checked by re-extraction (G7).

## Step 2: §4, then §5 (PLAN.md, next step 3)

Rewrite in blocks with the user's review after each, using the `paper-prose` skill. §4 follows the template of
decision 1. From the audit, §4 must also say:
- **Corpus-collected vocabulary.** Theorem 1's corpus-checked hypothesis (decision 2) covers the kinds' term
  vocabulary as well as the write signatures, which entries a kind can touch and which counts every item of a kind
  carries among them (finding 4).
- **Writes onto locating positions.** In the directions, a write onto a position the parser reads to locate items
  allows any change of that kind's items, unless the catalogue declares the change (rename, remove debug, remove
  signature). Proposition 1 declines to predict such a write (finding 5).
- **Declared operations.** Append is among the declared operations (finding 6).
