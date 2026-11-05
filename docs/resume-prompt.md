# Resume: ProvExp (after 2026-11-05, session 15): research track (Table 7 updated; next: the user's read, the sums row's beam cell, the scale-up budget)

Two tracks run in parallel in separate sessions. This prompt is for the **research track**. The writing track (§2-3)
continues in its own session (session 15 writing: `bfda3d8`, the user's review of §2-3.2 logged, `/paper-prose`
lessons 21-25, a §3 structural proposal in `docs/framework-design.md`); its section below is maintained by that session. Do not edit `manuscript/_c_background.tex`, `_d_framework.tex`, `_i_symbols.tex`,
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

## Writing track (session 15 writing, 2026-11-05): §3.1 rebuilt; next, the §3.2 spine

**Where things stand.** The user reviewed §2, §3.1, and §3.2 (reaction log, 2026-11-05: §3.2 was "unintelligible").
We redesigned the structure of §3 before any prose: `docs/framework-design.md` (**read it first**; Sections 1-9 are
the design, 10 the user's decisions A-H, 11 the §3.1 spine). The core idea: the extractor factors as
$\varphi = \rho \circ \sigma \circ \pi$, $\mathcal{Z} \to \mathcal{V} \to \mathcal{S} \to \mathcal{X}$ (item map,
fold, readouts), and each subsection is about one map:
- 3.1 the class (**done**, `c6af95e`, `7e48d5a`; the user: "a significant improvement");
- 3.2 edits and exact side effects (format-free; Prop 1 needs no requirements): **next**;
- 3.3 edits given as writes (the only place the format enters: one "local kind" definition with structure positions
  $L_\tau(z)$ and margins $\mu_\tau(z, W)$; one localization lemma with parts (a) one edit, (b) an operation's
  signature);
- 3.4 directions (terms and readout sign rules move here, as clean tables); 3.5 robust detectors (keep).
Settled: no item identity (a delta is removed and added multisets of (kind, content)); self-containment and faithful
recording are in the class definition; "honest tools" is gone (declared deltas are checked in §5); a toy running
example (records located by a header count and table; strings as printable runs; features $x_1$-$x_4$) in purple
(`runex` environment, `\runexinline{}`); a Remark environment (`\remark[...]`); numbered equations; new Appendix B
"Types, Monoids, and Folds" (`_i2_types.tex`).
Notation now: kinds $\tau$, items $\iota = (\tau, M)$, $I(z)$, $\pi(z) \in \mathcal{V}$, sums $k \in K$ with monoids
$\mathbb{M}_k$, sum space $\mathcal{S}$, contributions $\nu_\tau$, fold $\sigma$, the sums of $z$ $\mathbf{s}(z)$ (not
"sum vector"), readouts $\rho_j$ with support $K_j$, $\rho: \mathcal{S} \to \mathcal{X}$, $J$ only in Definition 5.
§3.2 onward still uses the old notation ($\kappa$, $\mathbf{v}$, identity, (R1)-(R5)) until rewritten; the §3 lead
still describes the old subsection order (update after 3.3).

**Next, in order.**
1. Invoke `/paper-prose`. Write the **per-paragraph spine for §3.2** (design doc Section 5 is the coarse plan) into
   `docs/framework-design.md` and show it to the user; draft only after approval, then review, then 3.3.
   - The motivation before the machinery (design Section 4): re-extraction is the ground truth for one edit; what it
     cannot give is attribution and answers for edits not applied.
   - Def (item delta): $\pi(z') = \pi(z) - I^- \uplus I^+$; the written set is *not* in 3.2.
   - Prop 1 with no requirements; incremental view maintenance cited at it; pools via the item table.
   - The toy example in purple: appending lowers $x_4$ (side effect); splitting the longest string (pool).
2. Then 3.3, 3.4, 3.5 the same way (spine, approval, draft, review). Rewrite `_j_proofs.tex` to the new statements;
   update §4/§5 wording ((R3)/(R4), locating positions, honest tools); rename the key set $K$ in 3.4 (now the sums).
3. Notation round (the user is "not in love" with $\tau$ but accepts it for now; change only clear wins).
4. Small open items: `% VERIFY` on Hidost's feature values; the claim "classifiers trained on them remain strong
   baselines" (user to confirm or make specific).

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
