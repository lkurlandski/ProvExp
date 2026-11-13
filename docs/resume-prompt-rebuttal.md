# Resume: the rebuttal of a simulated review, from the drafts to the user's decisions

This prompt starts each rebuttal session. Use it once `docs/reviews/process/run_review.sh` has finished, including
its last step, the rebuttal drafts (`docs/reviews/process/run_rebuttal.sh`). The current review is
**`TAG=2026-11-12-body`**: its folder is `docs/reviews/2026-11-12-body/`, the drafts are in its `rebuttal/`. Four
register items were decided before the drafts and have none: R7 (PLAN.md decision 11, the R7 track), R1 (session 49,
MAB-Malware), R6 (session 50, known techniques credited), R17 (session 53b, the ratio rule and ordered monoids).
This prompt stays fixed between sessions. The index `rebuttal/README.md` says where the pass stands.

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
(skim; the R7 track runs in another session), then `rebuttal/README.md` and the drafts of the items already decided
(their decisions are precedent).

## What the drafts are, and why they need checking

The review pipeline ran four reviewers who saw only the PDF, then a meta-reviewer with full access that checked their
findings and ranked the risks in a register (`meta-review.md`, §6). Then one agent per register item wrote
`rebuttal/<item>.md`. Each draft holds the reviewers' perspective (their words, at their strongest), a neutral analysis
(the claim attacked, every premise checked, merits, the strongest rebuttal) and an opinion. The opinion is one of:
change the methodology, change the argument or description, or no change. The drafting procedure is
`docs/reviews/process/rebuttal-brief.md`.

The drafts are a starting point, not a verdict, for three reasons:
- **The same lean, at every stage.** The reviewers, the meta-reviewer and the drafting agents are all the same kind of
  model, and that model leans toward accepting criticism (memory `distrust-simulated-reviews`). Example (session 54):
  "the learned defenses get less information, so the outcome is built in" restates §5.3's finding as a flaw.
- **The drafts ran in parallel**, each without the others, without the user, and without earlier decisions. Two
  drafts may contradict each other on the same premise, propose overlapping fixes, or each propose a fix that only
  makes sense once.
- **An agent's "verified" is a claim**, not a check you have made.

## Session 1: check the output (no decisions)

1. **Completeness.** Every register item except the four decided earlier has a draft with the form of
   `rebuttal-brief.md` (an `**Opinion:**` line, the three sections). For each missing or broken draft, read its log
   (`rebuttal/<item>.log`) and say what went wrong; to redraft, delete the draft and run
   `TAG=2026-11-12-body REBUTTAL_ITEMS="<items>" STEPS=rebuttal docs/reviews/process/run_review.sh` (the user's call;
   it costs agent time, not CPU).
2. **Across the drafts.** Read them all once and list: contradictions between drafts (the same premise judged
   differently); fixes proposed in more than one item (one fix may answer several); opinions that would reopen a
   settled decision (PLAN.md, `checklist.md`, the memories); drafts that restate a finding as a flaw or answer a claim
   the paper does not make without saying so; and drafts whose analysis is thin (premises asserted, not checked).
3. **Report to the user**, plainly and in one screen: the index's table (item, opinion), then the list from step 2,
   then the order for the decisions. The order is the register's (most significant first), unless step 2 shows items
   that should be decided together. Write that report as `rebuttal/check.md`, so later sessions can read it.

## Later sessions: the decisions, item by item

Take the first undecided item in the agreed order (the index's "Decision" column). Per item:

1. **Re-check the draft.** Check the premises the opinion rests on yourself, against the code, the stored outputs
   (`artifacts/`), the manuscript or `papers/`. Spot-check the rest. Check the draft against the decisions already
   recorded and against `rebuttal/check.md`. A small check on stored outputs (about ten minutes at most, hypothesis
   stated first) is fine; anything larger becomes a proposed `run/` script.
2. **Present it to the user**, plainly (memory `explain-plainly`). Give the reviewers' perspective, the analysis and
   the opinion in a few paragraphs, not the draft verbatim. Say where your check changed the draft, and why. Before
   giving the opinion, answer the two calibration questions: *Would I propose this if no reviewer had raised it?* *Does
   the criticism restate one of our findings, or attack a claim we do not make?* One recommendation, not a menu.
3. **Ask the user for the decision**, and discuss it if they want. Then record it in the draft:
   - under the `**Opinion:**` line, a line `**Decision:** <methodology | argument | no change> (<the user's reason, in
     their words>)`;
   - at the end, a section `## The user's decision` with the decision, what the discussion changed in the analysis
     (one line each), and the actions it creates as `- [ ]` items, each naming what it depends on (e.g., the R7 track,
     the full run).
   Then rewrite the index: `INDEX_ONLY=1 TAG=2026-11-12-body docs/reviews/process/run_rebuttal.sh`.

As many items per session as the user wants. Start a fresh session when the context grows long; the index and the
recorded decisions carry everything over.

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
