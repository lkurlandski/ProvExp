# Resume: ProvExp (after 2026-11-05, session 15): research track (Table 7 updated; next: the user's read, the sums row's beam cell, the scale-up budget)

Two tracks run in parallel in separate sessions. This prompt is for the **research track**. The writing track (§2-3)
continues in its own session (session 15 writing: `bfda3d8`, the user's review of §2-3.2 logged, `/paper-prose`
lessons 21-25, a §3 structural proposal in `docs/framework-design.md`); its section below is kept from session 14b
and that session updates it. Do not edit `manuscript/_c_background.tex`, `_d_framework.tex`, `_i_symbols.tex`,
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

## Writing track (session 14b): the user reads the rewritten Sections 2-3

**Where things stand.** §2 "Background and Motivation" (`manuscript/_c_background.tex`) and §3 "Measuring Edits Across
Feature Mappings" (`manuscript/_d_framework.tex`) were rewritten from scratch (`084055c`), from the spine in
`docs/framework-spine.md` and the user's decisions D1-D5 and comments (`docs/writing-spec.md`, reaction log, the two
2026-11-04 §3 entries). Details: `docs/status.md`, session-14b block. In short:
- no domain examples (kept as `% EXAMPLE (removed, D2)` comments), no tables (source in
  `manuscript/backup/framework-tables-2026-11-04.tex`), no figures; Pierazzi's notation; reachable set
  $\mathcal{R}(z)$; symbol table in Appendix A;
- one endpoint per subsection: Lemma 1 (finding the item delta), Proposition 1 (exact side effects), Lemma 2
  (signatures from the item table), Theorem 1 (sound directions; formerly Theorem 2), Corollary 1 (robustness);
- requirements renumbered by step: (R1) structure, (R2) margins, (R3) honest tools, (R4) self-contained
  contributions, (R5) faithful recording.

The user was unsure about the edits subsection from the spine (P12 and P13 felt disconnected) and reads the prose to
judge whether the new arc (which items a write changes, answered by locating positions and margins, ending in Lemma 1)
works.

**Next, in order.**
1. **Take the user's review of §2-3.** Invoke `/paper-prose` first. Log the reaction raw in `docs/writing-spec.md`
   (reaction log), then update the skill's lessons (add, sharpen, or delete; lessons 16-20 are new and untested).
2. **Revise** per the review; if the second half's arc still does not land, fix the structure (spine) before prose.
   `make` and `make check` in `manuscript/`; keep `_i_symbols.tex` in sync with any notation change; commit.
3. **Notation round** against the symbol table (the user promised specific comments). Known candidates: $\kappa$ (item
   kind) vs Pierazzi's confidence $\kappa$ (unused in §2, so no clash yet); $T$, $T_{o,\theta}$, $\mathcal{T}$, $O$,
   $\mathcal{M}$; $E^F_o(s)$ vs $E_s$.
4. **Small open items:** a `% VERIFY` in §3.1 on Hidost's feature values (path counts or presence bits; check
   `srndic2016hidost`); §3 is ~3,900 words against 2,500 (within the drafting allowance; do not cut unless asked).
5. **Later (user: only once the core reads well):** redesigned term and readout tables, figures, and domain examples.
   `docs/reviews/review-prompt.md` should be updated when the draft's stage changes.

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
