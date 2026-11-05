# Resume: ProvExp (after 2026-11-05, session 15): research track (Table 7 updated; next: the user's read, the sums row's beam cell, the scale-up budget)

Two tracks run in parallel in separate sessions. This prompt is for the **research track**. The writing track (§2-3)
continues in its own session (latest: session 15d writing, §3 cut, tables moved to Appendix C, readability pass, `4001a9d`);
its section below is maintained by that session. Do not edit `manuscript/_c_background.tex`, `_d_framework.tex`, `_i_symbols.tex`, `_j_proofs.tex`,
`docs/framework-*.md`, `docs/writing-spec.md`, or the `paper-prose` skill from the research track, and commit only
your own files (`git status` first: the other session may have uncommitted work).

## Research track (session 15): the user reads the new §5 passages; then the sums row, the scale-up budget, ERDALT

### Where things stand

- **Run 130 read** (`9f9cecb`): the beam search (5,000 candidates, M_full) evades run 125's adversarially trained
  GBDT on 24/49 (49%; 8 / 17 / 24 at 200 / 1,000 / 5,000), all confirmed on re-extraction; 35 mismatches (pefile's two
  unmodeled warning features), no LOST lines. Hypothesis ~20-25 held. The beam evades all 12 files of run 125's
  twelve-operation greedy menu and all 6 of its append+add-section menu.
- **Table 7 updated** (`08c8535`, `manuscript/_f_evaluation.tex`, `tab:eval:detectors`). User agreed: run 125's row
  replaces run 122's. Adaptive column = the beam alone (no union across searches, user decision):

  | Row | Adaptive | Other cells |
  |---|---|---|
  | unconstrained, 10% | --- | unchanged |
  | unconstrained, full store | 51% (25/49) | unchanged |
  | adversarial training (run 125) | 49% (24/49) | AUC 0.998, TPR 95.6%, 49/50, seen 12%, held-out 27% |
  | PV, 4 attacks (10% model) | 68% (15/22) | unchanged |
  | PV, 8 attacks (10% model) | 64% (14/22) | unchanged; the synthetic 77% is gone |
  | ERDALT (new, run 128) | 80% (20/25) | AUC 0.881, TPR 61.1%, 25/50, seen 0%, held-out 92% |
  | monotone, features | 0% | unchanged |
  | monotone, sums | 0%, footnoted: greedy search (the beam has no routing to the sums store) | unchanged |

  New footnotes: run 125's training attacks (two of PV's held-out four are trained on); ERDALT's port (output layer
  also monotone, batch 256, epoch selected on validation). Table 7 has no synthetic cell left.
- **§5 prose synced:** the adaptive attack's setup paragraph (§5.1) now describes the beam (three files kept, restarts
  after three steps without a new best, 5,000 scored candidates, every kept file re-extracted); the PV paragraph
  reports 15/22 and 14/22 and adds ERDALT (seen 0/25, held-out 23/25, beam 20/25; 89.7% of its learned layer's weight
  on features the table shows lowerable, almost all moved both ways); a new adversarial-training paragraph (import
  injection 22 -> 11 of 49, all eight attacks 27 -> 15, beam 24/49 vs 25/49) ending in the greedy-subset sentence.
  §6's closing pointer now names ERDALT's learned layer. `make check` clean. **Not yet read by the user.**
- Docs updated: `docs/status.md` (session-15 block), `PLAN.md` ("Next steps (2026-11-05, session 15)"),
  `docs/paper-mock.md` (Table 3 measured), `docs/direction-A-summary.md`. Nothing pushed.

### Next session, in order

1. **Take the user's read of the new §5 passages** if they bring one. Invoke `/paper-prose` first (lesson 15: report,
   don't narrate); log the reaction in `docs/writing-spec.md` only if the writing session is not using it at the same
   time (ask). `make` and `make check` in `manuscript/`.
2. **The sums row's beam cell: a routing plan first**, agreed with the user before code. The beam
   (`scripts/a1_adaptive.py --search beam`, `beam_search`) scores thrember-space detectors only; the sums detector
   reads the sums store (`src/provexp/featuresets/ember2024/sums.py`), and files outside the population go to the
   unconstrained model. Expected result: 0% with a largest score drop of exactly 0.0 (by construction), so the point
   is consistency with the other cells, not new evidence; weigh it against cost. Then `run/131`, reading `NUM_WORKERS`.
3. **The scale-up's adaptive budget** (decide with the user before scaling): ~10-20 CPU-min per (defense, file) at
   5,000 candidates, and the monotone rows always spend the full budget, so ~3,000 CPU-h at 2,000 files. Options, with a
   recommendation: report the 1,000-candidate checkpoint (already recorded per file, `evaded_at_1000`), attack a
   fixed subset of the malware, or cap the monotone rows.
4. **ERDALT at seeds 0-2:** its < 5-violation criterion was met only at the last epoch (309/310) at seed 0. More
   epochs, or report the last epoch when the criterion is not met; decide before the scale-up.
5. Still open: MAB-Malware (likely unnecessary), the headline (not adopted), §6's Chen 2021 sentence ("all four works
   rest on the same input" stretches Chen 2021). After those, the introduction and the other empty sections, spine
   first, coordinated with the writing track.

## Writing track (session 15d writing, 2026-11-05): §3 cut and smoothed; next, the user's read of all of §3

**Where things stand.** §3 (`manuscript/_d_framework.tex`) has four subsections built on
$\varphi = \rho \circ \sigma \circ \pi$ ($\mathcal{Z} \to \mathcal{V} \to \mathcal{S} \to \mathcal{X}$):
3.1 the class (Defs 1-5, Remark 1), 3.2 item deltas and exact side effects (Def 6, Prop 1), 3.3 edits given as writes
(Def 7 local kinds, Lemma 1 localization), 3.4 sound directions (signatures, sign sets, Def 8, Theorem 1, Corollary 1).
Design and spines: `docs/framework-design.md` (Sections 11-15). This session (`db2a327`, `4001a9d`, `4510e07`):
- **Cut (user):** the toy example everywhere and every tie to real feature sets (EMBER, Drebin, Hidost,
  CICFlowMeter, PE examples). No replacement plain-language examples (the user's view; open to debate). Pre-cut text in
  `manuscript/backup/framework-before-cuts-2026-11-05.tex`, to refactor into §4.
- **Tables 1-2** redesigned (symbols in cells, conditions in footnotes) and moved to Appendix C ("Sign rules");
  the body states the readout rules in one sentence.
- **§3 lead** rewritten in the current order. **Readability pass** over all of §3, math unchanged; new term: an
  item *lies within* a set of positions. ~4,450 words (budget 2,500; drafting allowance ~4,400).
- Kept for the user to decide: "such as an offset in a table entry", "such as a count", "such as a count, an offset,
  or a length", the 5-vs-3 max example, and §3.4's sentence on where our sign sets come from.

**Lessons to keep** (`paper-prose` lessons 26-28): read the rendered PDF (pdftotext; render tables with pdftoppm and
look) before showing anything; readable before reviewable (the user: the prose was "extremely hard to review");
table cells hold symbols, never clauses; explain each concept in words before its definition and each result's plain
meaning after it; no equation numbers as arguments; no abstract closers; no deference about cited work.

**Next, in order.**
1. Invoke `/paper-prose`. **Take the user's read of all of §3.** Log it raw in `docs/writing-spec.md`'s reaction log,
   update the skill's lessons, and revise: from a spine change if the structure is at fault, not by patching
   sentences. Settle the kept clauses above.
2. **Downstream consistency:** §4's "self-contained contributions (R4)" (`_e_instances.tex:40`) and "honest tools
   (R3)" (`:106`), now part of the class or dropped; §5's "precondition" (`_f_evaluation.tex:102, 267`) should say it
   is how §4 defines $F$; §5's uses of Corollary 1 for the sums rows; the proofs appendix says "whose members lie in"
   where §3 says "lies within".
3. **Refactor the cut material into §4** where it serves the instances (which feature sets have the shape; the
   size/length repair as a contribution moved into a readout; item-stated operations); the scope sentence (call
   graphs, learned representations) to §7.
4. Notation round (the user is "not in love" with $\tau$); the "strong baselines" claim (cut; reinstate only with
   support). Then the introduction and the other empty sections, spine first, coordinated with the research track.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision).
- Routing to Table 7's sums rows needs a plan first (see step 2). The beam search scores only thrember-space defenses (ERDALT reads
  thrember features, so it is covered); the sums row's adaptive cell rests on earlier runs.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-8; item 8 is a note to Gimenez et al.).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand
  over a `run/` script (next number **131**), reading `NUM_WORKERS`. The second server has 20 physical cores; the user
  runs it at 24 workers.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
