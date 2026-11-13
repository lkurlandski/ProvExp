# Your task: the rebuttal draft of one risk of a simulated review

You are drafting the authors' side of one item of a simulated program-committee review of this project's paper. Four
independent reviewers reviewed the paper and a meta-reviewer checked their findings and ranked the risks in a
register. You take **one risk, {{ITEM}}**, and write a careful, neutral analysis of it and an opinion on what, if
anything, the authors should change. The authors decide later, one item at a time, in `{{OUT}}/meta-rebuttal.md`; your draft is what they start from.

Commit reviewed: {{COMMIT}}. Review folder: `{{OUT}}/`.

## What to read

- `CLAUDE.md` and `PLAN.md` (the thesis, the decisions, and what is settled), and the memories loaded with this
  project. Pay particular attention to `distrust-simulated-reviews`.
- `{{OUT}}/meta-review.md`: {{ITEM}}'s row in the register (§6), the §3 verdicts on every reviewer finding the row
  cites, and any §5 entry ("what the reviewers missed") that bears on {{ITEM}}. If a §5 entry clearly belongs to
  another risk, leave it to that one.
- `{{OUT}}/reviewer-*.md`: every finding the row cites (the W and Q IDs), in full.
- `{{OUT}}/checklist.md`: the settled points the reviewers were not told about.
- The manuscript (`manuscript/*.tex`; numbers of sections, tables and theorems from `manuscript/main.aux`, always with
  the title alongside), the code (`src/`, `scripts/`), the stored outputs (`artifacts/`), `papers/`, and the project
  docs (`docs/README.md` indexes them) as each premise needs.

## Why this needs care

Many simulated-review comments are misguided or wrong, and they are hard to tell from real limitations. The
reviewers and the meta-reviewer are the same kind of model as you, with the same lean toward accepting criticism. The
meta-review's "correct" verdicts mostly confirm that a quote is accurate, not that the objection matters. Two
patterns to look for: a criticism that **restates one of the paper's findings as a flaw** (e.g., "the learned defenses
get less information, so the outcome is built in", when failing on unseen edits *is* the finding), and a criticism of
**a claim the paper does not make**. Equally, do not dismiss a real problem because rebutting it is comfortable.

## What to write

Write **only** `{{OUT}}/rebuttal/{{ITEM}}.md`. Edit no other file, run no long job (no featurization, training or
attack; a check on stored outputs that takes a few minutes at most is fine, with its hypothesis stated first), and do
not commit. Plain language throughout: say what is computed, what it is compared with and why it matters, and define
terms. The form, exactly (the first two lines are read by a script):

```
# {{ITEM}}: <the risk, in the register's words>

**Opinion:** <change the methodology | change the argument or description | no change> (<one-line reason>)

## The reviewers' perspective
## Neutral analysis
## Opinion
```

**The reviewers' perspective.** What they object to, in plain language, with their own words quoted and the finding
IDs. Present it at its strongest: what a reviewer who holds it would need to see to change their score. Say how many
of the reviewers raised it and where they disagree. One reviewer's objection weighs differently from four.

**Neutral analysis.**
- *The claim attacked:* the sentence(s) of the `.tex` the criticism targets, quoted with `file:line`, or "no claim of
  ours" (then the item is likely about scope, or a finding restated as a flaw).
- *The premises, checked:* every factual premise checked yourself against the manuscript, the code, the stored outputs
  or `papers/`, each marked **verified** (with where) or **inferred**. The meta-review's checks are not evidence.
- *Merits:* what holds, and how likely a real reviewer at the venue is to raise it.
- *Flaws:* the strongest rebuttal, written as the authors' advocate. Settled decisions (PLAN.md, the checklist, the
  memories) count: name the decision and its reason. Do not argue for reopening a settled decision; if the evidence
  seems to contradict one, say so plainly and leave it to the authors.

**Opinion.** One of three, with the reason in a few sentences:
- **change the methodology** (an experiment, a protocol, the threat model, the framework);
- **change the argument or description** (the claim, its scope, the wording, a missing sentence or citation);
- **no change** (wrong, or outside the claim); then give the one-paragraph answer the authors would give in a rebuttal.

For the first two, give the smallest change that answers the criticism, what it costs (compute, text, risk to other
results) and what is lost by not making it. One recommendation, not a menu. Before writing it, answer two calibration
questions in the entry: *Would I propose this if no reviewer had raised it?* *Does the criticism restate one of our
findings, or attack a claim we do not make?*

The authors' decision is not yours to anticipate: no "decision" or "next steps" section. Finish by printing the opinion
line.
