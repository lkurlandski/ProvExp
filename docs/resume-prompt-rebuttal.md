# Resume: the rebuttal of a simulated review, from the triage to the user's decisions

This prompt starts each rebuttal session. The current review is **`TAG=2026-11-12-body`**: its folder is
`docs/reviews/2026-11-12-body/`, the rebuttal files are in its `rebuttal/`. Four register items were decided before
the rebuttal: R7 (PLAN.md decision 11, the R7 track; it also has a full draft, `rebuttal/R7.md`, from the first design),
R1 (session 49, MAB-Malware), R6 (session 50, known techniques credited), R17 (session 53b, the ratio rule and ordered
monoids). This prompt stays fixed between sessions; `rebuttal/triage.md`'s Decision column says where the pass stands.

**If `rebuttal/triage.md` does not exist yet**, the user runs the triage first (one agent, about the token cost of one
of the first design's drafts):
`TAG=2026-11-12-body REBUTTAL_SKIP="R7 R1 R6 R17" docs/reviews/process/run_rebuttal.sh`.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1). From those directions come monotone detectors that no
edit in the threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. §5 of the paper is three
findings: what hand analysis misses (5.2), what defenses learned from observed attacks miss (5.3), what robustness
costs (5.4). Before naming a section, table or theorem number, check `manuscript/main.aux`, and give the title
alongside.

**Read first:** `CLAUDE.md`, `PLAN.md` (the decisions, so that settled points are recognised), `docs/status.md`
(skim; the R7 track runs in another session), then `rebuttal/triage.md` (the decisions already in its table are
precedent) and, when deciding a group, its draft `rebuttal/<group>.md`.

## How the rebuttal works, and why

The review pipeline ran four reviewers who saw only the PDF, then a meta-reviewer with full access that checked their
findings and ranked the risks in a register (`meta-review.md`, §6). Then:
1. **The triage** (`docs/reviews/process/triage-brief.md`): one agent gave every item a verdict, *decided*, *dismiss*,
   *cheap fix* or *investigate*, and grouped the items to investigate with the two or three questions that decide them
   (`rebuttal/triage.md`).
2. **The decisions on the table** (these sessions).
3. **Drafts for the chosen groups** (`docs/reviews/process/rebuttal-brief.md`): one agent per group reads a dossier of
   its items (`rebuttal/<group>.dossier.md`), checks only the deciding questions, and writes `rebuttal/<group>.md`.
   The user runs them: `TAG=2026-11-12-body REBUTTAL_GROUPS="<names>" docs/reviews/process/run_rebuttal.sh`.

The meta-review's [verified] facts are trusted throughout (user, 2026-11-13); what is not trusted is its judgement.
The reviewers, the meta-reviewer, the triage and the drafting agents are all the same kind of model, which leans
toward accepting criticism (memory `distrust-simulated-reviews`). Two patterns to watch: a criticism that restates one
of our findings as a flaw (session 54: "the learned defenses get less information, so the outcome is built in"), and a
criticism of a claim the paper does not make. The triage can be wrong in both directions: a "dismiss" may hide a real
problem, an "investigate" may be pedantry.

## The sessions

**On the triage table** (the first session or two). Go down the table in the register's order (most significant
first). Per item, present the verdict and its reason plainly in a few sentences (memory `explain-plainly`), with your
own view where you disagree with the triage. Spend almost nothing on *decided* items. For a *dismiss* or *cheap fix*
you doubt, a quick look at the `.tex` is fine; do not open code or outputs to re-check the meta-review's facts. Ask
for the decision; several clear items may be decided in one question. Record each in the table's Decision column:
`methodology`, `argument`, `no change`, or `investigate`, with a few words of the user's reason; append any action to
the item's entry under `## The items` as a `- [ ]` line naming what it depends on (e.g., the R7 track, the full run).
When the investigate groups are settled (the user may merge, split, drop or rename them; edit the `GROUP` lines to
match), give the user the drafting command.

**On a group's draft.** Read `rebuttal/<group>.md`. Check the premises its opinions rest on, where the draft's check
looks thin; a small check on stored outputs (about ten minutes at most, hypothesis stated first) is fine, anything
larger becomes a proposed `run/` script. Present each item plainly, with the two calibration questions answered
(*Would I propose this if no reviewer had raised it?* *Does it restate a finding or attack a claim we do not make?*),
one recommendation, then ask for the decision and record it in the triage table and the item's entry as above.

**Actions are recorded, not done.** A rebuttal session edits only the files in `rebuttal/` (and the status line
below). It does not edit the manuscript, the code or `run/` scripts, and runs no long jobs. Once the pass is done (or a
batch of actions is approved), the actions go into PLAN.md's next steps and are carried out in their own sessions.

## Constraints

- **The R7 track runs in parallel.** It owns §4.3.1 and Table 2, §4.4, §5.1's setup and routing, §5.4, Table 5,
  Appendix D's population and routing text, and `catalogue.py`, `a_directions.py`, `a1_adaptive.py`,
  `catalogue_checks.py`. Items touching them (R14, R20, R11) can be decided now; their actions name the dependency.
- Commit only the files you changed (`git add <paths>`, never `git add -A`: the other session may have uncommitted
  work). At the end of a session, add one line to `docs/status.md`'s log if `git diff docs/status.md` is empty
  (otherwise skip it and say so).
- Explain plainly; no deadline talk; no sandbox execution; no timing claims; jobs over ~10 minutes go to the user as
  `run/` scripts. Memories that bear most on this pass: `distrust-simulated-reviews`, `findings-not-defense-paper`,
  `fair-baselines-over-faithful-copies`, `portray-cited-work-accurately`, `credit-without-diminishing`,
  `elegant-framework-fixes`, `constrain-experiment-complexity`, `proofs-carry-the-weight`, `no-effort-claims`.
