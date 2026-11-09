# Resume: apply the two §3 edits the user chose, then §4

Read `docs/status.md` and `PLAN.md` (especially "Decisions of 2026-11-09", decisions 1, 2, and 7). Open other
documents only as the task needs them (index: `docs/README.md`).

**Numbers.** Every section, definition, and table number below is the compiled one (`docs/README.md` has the full
table). Before naming any number to the user, check `manuscript/main.aux`, and always give the title or label
alongside it ("Definition 8, Changes and signatures"). Two earlier sessions were derailed by stale numbers and by
describing an edit with a figurative word ("widen") instead of the exact text; the user called this unacceptable.

## Step 1: apply decision 7 (both choices made; do not ask again)

Line numbers are approximate; match the text. After both edits: `make` and `make check` in `manuscript/`. Then show
the user the diff.

**(a) Table 1, readout rules (`tab:fw:readouts`, §3.3): option A.** The table keeps its rows and columns; only the
first two cells of the presence row change, and three sentences elsewhere get matching wording.

1. The table row, `_d_framework.tex` ~382:
   - old: `presence & $[s_k > 0]$ & $d_k$ \\`
   - new: `monotone & $g(s_k)$, $g$ nondecreasing, e.g.\ $[s_k > 0]$ & $d_k$ \\`
   (If the cell is too wide, put the example in the caption or the paragraph below; check `make check` for overfull
   boxes.)
2. The list of readout forms in §3.1, `_d_framework.tex` ~171:
   - old: "and a presence bit, which is 1 when a count is positive."
   - new (draft): "and a nondecreasing function of one sum, such as a presence bit, which is 1 when a count is
     positive."
3. The paragraph after the table, `_d_framework.tex` ~395:
   - old: "The identity, a presence bit, and a distinct count, which is a total of presence bits, move with the sums
     they read."
   - new (draft): "The identity, a nondecreasing function of one sum such as a presence bit, and a distinct count,
     which is a total of presence bits, move with the sums they read."
4. The proof, `_j_proofs.tex` ~99 (Appendix C, paragraph "The readout rules"):
   - old: "A presence bit $[s_k > 0]$ is a nondecreasing function of $s_k$, so it rises only if $s_k$ rises and falls
     only if $s_k$ falls, and its change has a sign in $d_k$."
   - new (draft): "A nondecreasing function $g(s_k)$, such as a presence bit $[s_k > 0]$, rises only if $s_k$ rises
     and falls only if $s_k$ falls, so its change has a sign in $d_k$."

Why (for answering questions, not to re-ask): three EMBER readouts are not literally in Table 1 but are nondecreasing
functions of one sum, and the code gives them $d_k$: a max/min pool with a floor of 0 (max/min section entropy), one
item's value with a default of 0 (`has_relocs` and similar), and a presence bit scaled by 128 (exports present).

**(b) Definition 8, Changes and signatures (`def:fw:signature`, §3.3): the second paragraph after it**,
`_d_framework.tex` ~346-348, just before Definition 9 (Directions of sums):
- old: "One defined by the positions it writes, such as appending any content, gets them from the item tables of the
  inputs in $Z$."
- new: "One defined by the positions it writes, such as overwriting a range of positions with any content, gets them
  from the item tables of the inputs in $Z$, which record the items each position belongs to."

Why: the code collects changes from item tables only for the seven in-place writes; append is declared by hand, like
the other structural operations, and checked by re-extraction (audit finding 6,
`docs/evidence/code-audit-sound-directions.md`).

Commit the two edits once the user has seen them.

## Step 2: §4 Instances, then §5 Evaluation (PLAN.md, next step 3)

Rewrite in blocks with the user's review after each, using the `paper-prose` skill. §4 follows the template of
decision 1. Read the audit record's findings 3-6 first. From the audit, §4 must also say:
- **Corpus-collected vocabulary.** Theorem 1's corpus-checked hypothesis (decision 2) covers the kinds' term
  vocabulary as well as the write signatures: which entries a kind can touch and which counts every item of a kind
  carries among them (finding 4).
- **Writes onto locating positions.** In the directions, a write onto a position the parser reads to locate items
  allows any change of that kind's items, unless the catalogue declares the change (rename, remove debug, remove
  signature). Proposition 1 declines to predict such a write (finding 5).
- **Declared operations.** Append is among the declared operations (finding 6).
