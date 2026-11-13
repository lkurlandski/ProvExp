# Resume: the meta-rebuttal, one review item per session

Written 2026-11-13 (session 57, parallel to the R7 track). This prompt starts each session of the **meta-rebuttal**:
a pass through the 2026-11-12 simulated review, one item per fresh session, most significant first. The running
record is `docs/reviews/2026-11-12-body/meta-rebuttal.md`; its progress table says which item is next. This prompt
stays fixed between sessions; change it only when the user changes the procedure.

It replaces the "triage" procedure of session 54 (no opinion from Claude). The user now wants Claude's opinion on
each item, written after a neutral analysis and recorded next to the user's own decision.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1). From those directions come monotone detectors that no
edit in the threat model can evade (Corollary 1). PE malware on EMBER2024, with an extractor derived from EMBER-v3, is
the instance. §5 of the paper is three findings: what hand analysis misses (5.2), what defenses learned from observed
attacks miss (5.3), what robustness costs (5.4). The paper is in `manuscript/*.tex`. Before naming a section, table
or theorem number, check `manuscript/main.aux`, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md` (skim; the R7 track is active in another session), `PLAN.md` (the
decisions, so that settled points are recognised), then `meta-rebuttal.md` (the progress table and every earlier
entry: the user's past decisions are precedent for this one).

## The source

`docs/reviews/2026-11-12-body/`: four simulated CCS reviewers (`reviewer-A.md` formal methods, `B` adversarial malware,
`C` robust ML, `D` systems security) and `meta-review.md`. That file holds the per-finding verdicts (§3), "what the
reviewers missed" (§5) and the rejection-risk register (§6, ranked by likelihood × severity). The register's order is
the order of this pass. `checklist.md` in the same folder lists what the reviewers were told is settled.

**Why the procedure is careful** (memory `distrust-simulated-reviews`). Many of the reviewers' comments are misguided
or wrong. Claude leans toward accepting criticism, and the meta-review is the same model with the same lean. Its
"correct" verdicts mostly confirm that a quote is accurate, not that the objection matters. Example (session 54):
reviewer C's R18, "the learned defenses get less information, so the outcome is built in", restates §5.3's finding
(defenses learned from observed attacks fail on edits they never saw) as a flaw. Watch for that pattern and for its
twin, a criticism of a claim the paper does not make.

## The procedure, per item

One item per session. Read the register row, every reviewer finding it cites (the W and Q IDs in
`reviewer-*.md`), the meta-review's §3 verdicts on those findings, and the §5 entries attached to the item (table
below). Then write the entry in `meta-rebuttal.md` in four parts:

1. **The reviewers' perspective.** What the reviewers object to, in plain language, with their own words quoted and
   the finding IDs. Present it at its strongest: what a reviewer who holds it would need to see to change their score.
   Where reviewers disagree with each other, say so. One reviewer's objection weighs differently from four.
2. **Neutral analysis.**
   - *The claim attacked:* the sentence(s) of the `.tex` the criticism targets, quoted with `file:line`, or "no claim
     of ours" (then the item is likely about scope, or a finding restated as a flaw).
   - *The premises, checked:* every factual premise checked against the manuscript, the code, the stored outputs in
     `artifacts/`, or `papers/`, marked *verified* or *inferred*. The meta-review's checks are not evidence. A small
     check (≤ ~10 minutes, hypothesis stated first) is fine; anything larger becomes a proposed `run/` script.
   - *Merits:* what holds, and how likely a real CCS reviewer is to raise it.
   - *Flaws:* the strongest rebuttal, written as the authors' advocate. Settled decisions (PLAN.md, `checklist.md`,
     the memories) count: name the decision and its reason. Do not reopen it; flag it if the evidence seems to
     contradict it, and let the user decide.
3. **Opinion.** One of three, with the reason in a few sentences:
   - **change the methodology** (an experiment, a protocol, the threat model, the framework);
   - **change the argument or description** (the claim, its scope, the wording, a missing sentence or citation);
   - **no change** (wrong, or outside the claim; a rebuttal line is recorded for a real review).

   For the first two, give the smallest change that answers the criticism, what it costs (compute, text, risk to
   other results), and what is lost by not making it. One recommendation, not a menu. Two calibration questions before
   writing it: *Would I propose this if no reviewer had raised it?* *Does the criticism restate one of our findings,
   or attack a claim we do not make?* Say how each was answered.
4. **The user's decision.** Ask the user for their decision (not before the entry is written). Record it with their
   reason in their words, and list any action it creates under "Queued actions" at the end of `meta-rebuttal.md`.

Present the entry to the user in the chat as well, plainly (memory `explain-plainly`). Discussion may revise the
analysis or the opinion. Keep the final text, and note what changed and why in one line.

**Actions are queued, not done.** A rebuttal session writes only `meta-rebuttal.md` (and the status line below).
It edits no manuscript text, code, or `run/` scripts and launches no long jobs. The queued actions are carried out
later, in sessions the user starts for that, after the pass or in batches.

## The order

The register's order (likelihood × severity), skipping what earlier sessions decided. Done: **R7** (the routed system
and its population; PLAN.md decision 11, the R7 track, in progress), **R1** (attack strength; session 49, MAB-Malware
added), **R6** (known techniques; session 50), **R17** (Theorem 1's hypotheses; session 53b). The user may reopen
any of these. The meta-review's §5 entries go with the item they bear on:

| # | Item | The risk, in the register's words | With §5 entries |
|---|---|---|---|
| 1 | R2 | "Sound" rests on tested premises | 8 (closure argued from the record) |
| 2 | R18 | Learned baselines get less information and weaker training | — |
| 3 | R4 | One instance for a claim about a class | — |
| 4 | R20 | The statistical design cannot rank defenses | 4 (still-detected counts), 9 (thresholds on test files) |
| 5 | R11 | Cells of one table come from different detectors | — |
| 6 | R19 | The ERDALT port may be judged weak | — |
| 7 | R3 | The hand-analysis evidence is thin | — |
| 8 | R15 | The threat model's scope; no named attacker | — |
| 9 | R9 | What Proposition 1 enables | 7 (predicted vs real scores) |
| 10 | R5 | Pierazzi et al. portrayed loosely | — |
| 11 | R21 | Prior work misattributed or missing | 6 (uncited bib entries) |
| 12 | R12 | Counts mix modeled and unmodeled features | 3 (the 88 warnings) |
| 13 | R14 | One operation (header-field overwrites) never validated or used | 2 (declined in the adaptive attack) |
| 14 | R8 | The expert-set comparison | — |
| 15 | R13 | Instrumentation effort | — |
| 16 | R16 | PE minutiae | — |

§5 entry 1 belongs to R7, and entry 5 (Appendix D's minima) was resolved in session 53b. The user may pair the last
minor items (e.g., R13 and R16) in one session.

## Constraints

- **The R7 track runs in parallel.** It owns §4.3.1 and Table 2, §4.4, §5.1's setup and routing, §5.4, Table 5,
  Appendix D's population and routing text, and `catalogue.py`, `a_directions.py`, `a1_adaptive.py`,
  `catalogue_checks.py`. Items touching them (R14, R20, R11) can be analysed and decided now. Their queued actions
  name the R7 dependency.
- Commit only `meta-rebuttal.md` (`git add <path>`; never `git add -A`, the other session has uncommitted work).
- At the end of the session, add one line to `docs/status.md`'s log, but only if `git diff docs/status.md` is empty
  (otherwise the other session is editing it: skip, and say so). The record itself lives in `meta-rebuttal.md`.
- Explain plainly; no deadline talk; no sandbox execution; no timing claims; jobs over ~10 minutes go to the user as
  `run/` scripts. Memories that bear most on this pass: `distrust-simulated-reviews`, `findings-not-defense-paper`,
  `fair-baselines-over-faithful-copies`, `portray-cited-work-accurately`, `credit-without-diminishing`,
  `elegant-framework-fixes`, `constrain-experiment-complexity`, `proofs-carry-the-weight`, `no-effort-claims`.
