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

## Writing track (session 15b writing, 2026-11-05): §3.2 drafted (not yet satisfactory); next, the §3.3 spine

**Where things stand.** `docs/framework-design.md` is the design (**read it first**: Sections 1-9 the design, 10 the
user's decisions A-H, 11 the §3.1 spine, 12 the §3.2 spine and its decisions). The extractor factors as
$\varphi = \rho \circ \sigma \circ \pi$, $\mathcal{Z} \to \mathcal{V} \to \mathcal{S} \to \mathcal{X}$, and each
subsection is about one map:
- 3.1 the class (**done**; the user: "a significant improvement");
- 3.2 edits and exact side effects (**drafted**, `ff5ac37`; the user's verdict after three drafts: "still largely
  unsuccessful", move on; return later). Def 6 (item delta, $\pi(z') = (\pi(z) - I^-) \uplus I^+$, no positions),
  Prop 1 from the kept items $B = \pi(z) - I^-$, explanation in words, toy append and string split;
- 3.3 edits given as writes: **next**. Currently a `% PLACEHOLDER` holding the old locating-positions text, (R1)-(R3),
  and the old Lemma 1, in the old notation, kept only so references resolve; replace it entirely;
- 3.4 directions (terms and readout sign rules move here, as clean tables); 3.5 robust detectors (keep).
Notation: kinds $\tau$, items $(\tau, M)$, $I(z)$, $\pi(z) \in \mathcal{V}$, sums $k \in K$, monoids $\mathbb{M}_k$,
"pools" = max and min pools (Def 2), sum space $\mathcal{S}$, contributions $\nu_\tau$, fold $\sigma$, sums of $z$
$\mathbf{s}(z)$, readouts $\rho_j$ with support $K_j$. §3.3 onward still uses the old notation until rewritten; the §3
lead still describes the old subsection order (update after 3.3).

**What went wrong on §3.2, so it is not repeated** (reaction log, 2026-11-05; lessons 26-27): Claude did not read the
rendered PDF; used equation numbers and section pointers as arguments ("pi (1)", "(5) applied to (7)"); spelled out
obvious facts while under-developing the one real idea; did not explain what a result means or why it is exact; wrote
an abstract closer; patched the user's listed defects instead of rewriting. For §3.3: explain the concept in words
before the definition, give each result its plain reading, keep the lead to what the subsection contains and its role,
and read the pdftotext output before showing anything.

**Next, in order.**
1. Invoke `/paper-prose`. Write the **per-paragraph spine for §3.3** into `docs/framework-design.md` (Section 13),
   from the coarse plan (design Section 5, "3.3") and S3 (one "local kind" definition: structure positions
   $L_\tau(z)$ and margins $\mu_\tau(z, W)$; one localization lemma, (a) one edit, (b) an operation's signature). It
   must supply what §3.2 defers to it: the written set $W$; positions of new items (needed to chain write-given
   edits); the derivation of the string-split delta used in §3.2's example. Show the spine; draft only after approval.
   Check against §9 of the design (every EMBER kind fits the definition as stated).
2. Then 3.4 and 3.5 the same way. Update `_j_proofs.tex` (the Lemma proofs), §4/§5 wording ((R3)/(R4), locating
   positions, honest tools), the symbol table's (R1)-(R5) row, and the §3 lead.
3. Return to §3.2 (Prop 1's statement density; the long purple examples) once §3.3 settles.
4. Notation round (the user is "not in love" with $\tau$); small open items: `% VERIFY` on Hidost's feature values,
   the "strong baselines" claim.

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
