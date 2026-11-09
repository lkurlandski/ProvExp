# Resume: ProvExp (writing track after 2026-11-06, session 16; research track after 2026-11-05, session 15)

Two tracks run in parallel in separate sessions. **Next session: the writing track** (the user's §3.1 review; its section is below the research track's). The
research track's section is maintained by that track (latest writing commits: `7e73b85`, `e18e4b6`, §2 and §6). From the research track, do not edit `manuscript/_c_background.tex`, `_d_framework.tex`, `_i_symbols.tex`, `_j_proofs.tex`,
`docs/framework-*.md`, `docs/writing-spec.md`, or the `paper-prose` skill, and commit only
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
  `docs/paper-mock.md` (Table 3 measured), `docs/archive/direction-A/direction-A-summary.md`. Nothing pushed.

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

## Writing track (session 17, 2026-11-06): §3.1 revised and accepted ("improved enormously"); next, the user's §3.2-3.4 read

**Sprint (agreed 2026-11-06): self-review of §3.2, §3.3, §3.4, one subsection per session.** The writing track
now resumes from **`docs/archive/framework/resume-prompt-review.md`** (paste-ready); the protocol is in
`docs/archive/framework/sprint-framework-review.md` (steps 1-8 and the retro). Current position and next step: see that file
(2026-11-09: Sound Directions, the user's comments on round 3; the writing skill was reset, the reader model
archived).

**Update (session 17).** §3.1 went through two review rounds (`docs/status.md`, session-17 block); the procedure
below worked again and is now step 7 of the `paper-prose` procedure. Next: the user's comments on §3.2-3.4 (same
procedure: questions first), starting with aligning §3.2's "without extracting them" with the new lead. Item 1 below
is done; item 2 (the §2 ripple) is done in the lead.

### Previous: session 16

**Start here.** Invoke `/paper-prose` first. Read `docs/status.md` (session-16 block), then `manuscript/_d_framework.tex`
§3.1 (`sec:fw:model`: the factorization, Defs 1-5, Remark 1) and `manuscript/_c_background.tex` (the new §2, so §3.1
follows from it). The user has reviewed §3.1 and has **a lot of comments, and several parts they find confusing**:
they will paste them at the start of the session.

**How to work (this is what made session 16 effective; the user was "extremely satisfied"):**
1. Read the comments carefully. Separate questions (answer them plainly first, in words, before any fix; the user
   finds parts of §3.1 confusing, so an explanation may be what is needed, or the confusion may show a definition that
   does not stand on its own, lesson 21) from feedback.
2. Verify before planning: any claim about a cited work against the PDF in `papers/` (pdftotext into the scratchpad),
   any claim about §3's math against `docs/archive/framework/formalization.md` and `_j_proofs.tex`.
3. Give a **numbered plan**, one item per comment, each with the concrete change and one recommendation; flag scope
   risks and effects on other sections; put the genuinely open questions at the end. Do not edit until approved.
4. Implement; `make` and `make check` in `manuscript/`; read the rendered text (pdftotext) as the reader will; check
   for "??" in the PDF (`make check` misses a broken `\cref` to a theorem-like label: use `Definition~\ref{...}`).
   Rewrap to 120 columns. Report per item what changed, briefly.
5. Log the reaction raw in `docs/writing-spec.md`; update `paper-prose` lessons; commit in logical pieces.

**Where things stand.** §2 (~950 words) now: problem/feature space, attacks differ in what they return; constraints;
side effects; the reachable set $\mathcal{R}(z)$ as the paper's central object; attacks and defenses in either space
each need part of $\mathcal{R}(z)$; a short closing (the framework derives it from the feature mapping's code: side
effects before applying a transformation, sound directions under a threat model). §3 has four subsections on
$\varphi = \rho \circ \sigma \circ \pi$: 3.1 the class, 3.2 item deltas and exact side effects (Prop 1), 3.3
edits given as writes (Def 7, Lemma 1), 3.4 sound directions (Def 8, Theorem 1, Corollary 1); ~4,450 words; the sign
tables are in Appendix C. §6 aligned with §2 (`e18e4b6`).

**Next, in order.**
1. **The user's §3.1 review** (above). Revise from a spine change if the structure is at fault, not by patching.
2. **The §2 ripple into §3**, only if the review leaves it open: the §3 lead should frame the single-edit result as
   §2's closing does (side effects before the transformation is applied), not as "the exact change of every feature".
3. Then the user's read of §3.2-3.4, and the older writing items: the kept "such as" clauses and the 5-vs-3 max
   example; downstream consistency (§4's "(R4)" at `_e_instances.tex:40` and "honest tools (R3)" at `:106`; §5's
   "precondition" as how §4 defines $F$; the proofs appendix's "whose members lie in" vs "lies within"); the cut
   material into §4 (`manuscript/backup/framework-before-cuts-2026-11-05.tex`); the notation round ($\tau$).
4. Small: `bostani2025level` in `main.bib` lacks volume and pages; renaming §6's paragraphs to the 2x2 (user: maybe
   later).

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
