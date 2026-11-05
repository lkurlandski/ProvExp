# Resume: ProvExp (after 2026-11-05, session 15): research track (Table 7 updated; next: the user's read, the sums row's beam cell, the scale-up budget)

Two tracks run in parallel in separate sessions. This prompt is for the **research track**. The writing track (§2-3)
continues in its own session (latest: session 15c writing, §3.3-3.4 drafted and §3.5 folded into §3.4, `0bb0e31`);
its section below is maintained by that session. Do not edit `manuscript/_c_background.tex`, `_d_framework.tex`, `_i_symbols.tex`,
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

## Writing track (session 15c writing, 2026-11-05): §3.1-3.4 drafted, §3.5 folded into §3.4; next, the user's read

**Where things stand.** `docs/framework-design.md` is the design (**read it first**: Sections 1-9 the design, 10 the
user's decisions A-H, 11-14 the spines of §3.1-3.4 with their decisions, 15 the §3.5 fold). The extractor factors as
$\varphi = \rho \circ \sigma \circ \pi$, $\mathcal{Z} \to \mathcal{V} \to \mathcal{S} \to \mathcal{X}$, and §3
now has **four** subsections:
- 3.1 the class (**done**; the user: "a significant improvement");
- 3.2 edits and exact side effects (drafted, `ff5ac37`; the user's verdict "still largely unsuccessful", return later):
  Def 6 (item delta), Prop 1;
- 3.3 edits given as writes (drafted, `b6fa4ab`, **unread**): Def 7 (local kind: structure positions $L_\tau(z)$,
  margin $\mu_\tau(z, W)$, fixed-layout), Lemma 1 (a) one edit, (b) an operation; $W$ = every differing position;
- 3.4 sound directions (drafted, `00ef2c2`, **unread**): operations, threat model = catalogue (no precondition;
  population $F$), signatures (add/remove/replace), sign sets and $\boxplus$, Tables 1-2, Def 8, Theorem 1; then
  (`0bb0e31`, **unread**) Corollary 1 (robustness, Gimenez et al.'s Proposition 1 with our table), now also for
  scores that read sums, and the toy example's last sentence. `sec:fw:robustness` is gone.

**Lessons to keep** (reaction log, 2026-11-05; `paper-prose` lessons 26-27): read the rendered PDF (pdftotext)
before showing anything; no equation numbers as arguments; explain each concept in words before its definition and
each result's plain meaning after it; spend words on the one real idea, not on obvious facts; no abstract closers; no
deference about cited work (lesson 13: "The guarantee is Gimenez et al.'s." was caught and rewritten this session).

**Next, in order.**
1. Invoke `/paper-prose`. **Take the user's read of §3.3-3.4** (including the fold); log it raw in
   `docs/writing-spec.md`'s reaction log, update the skill's lessons, revise from a spine change if the structure is
   at fault, not by patching sentences.
2. **Downstream consistency** (mechanical once 3.3-3.4 stand): the §3 lead (`_d_framework.tex` top) still describes
   the old order (positions from writes before side effects); §4's "self-contained contributions (R4)"
   (`_e_instances.tex:40`) and "honest tools (R3)" (`:106`), now part of the class definition or dropped (decision C);
   §5's "precondition" (`_f_evaluation.tex:102, 267`) should say it is how §4 defines $F$; §5's uses of Corollary 1
   for the sums rows. A 1.5pt overfull vbox (float placement, since `0bb0e31`) to clear eventually.
3. **Return to §3.2** (Prop 1's statement density; the long purple examples).
4. Notation round (the user is "not in love" with $\tau$); `% VERIFY` on Hidost's feature values
   (`_d_framework.tex:207`); the "strong baselines" claim. Then the introduction and the other empty sections, spine
   first, coordinated with the research track.

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
