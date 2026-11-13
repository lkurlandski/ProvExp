# Your task: the rebuttal draft of one group of risks of a simulated review

A simulated program-committee review of this project's paper ranked its risks in a register; a triage then sorted
them, and the user chose this group for a closer look: **{{GROUP}} ({{ITEMS}})**. You answer the group's deciding
questions and give one opinion per item. The user decides afterwards, starting from your draft.

Commit reviewed: {{COMMIT}}. Review folder: `{{OUT}}/`.

## What to read

- `{{OUT}}/rebuttal/{{GROUP}}.dossier.md`: everything the review says about these items, cut out for you (the
  register rows, the meta-review's verdicts, the cited reviewer passages in full). Do **not** read `meta-review.md` or
  the reviews themselves; the dossier is the review.
- `{{OUT}}/rebuttal/triage.md`: the table, this group's `GROUP` entry (the deciding questions) and the entries of its
  items, plus any user decisions already recorded in the table (they are precedent).
- `PLAN.md`: only the decisions that bear on these items (grep it).

## How far to dig

The meta-review's [verified] facts are established; do not re-check them. Check **the deciding questions** in the
group's entry, and only them, against the code (`src/`, `scripts/`), the stored outputs (`artifacts/`), the
manuscript (`manuscript/*.tex`; numbers from `manuscript/main.aux`, with the title alongside) or `papers/`. If one of
them turns out not to decide anything, say so and stop on it. A check on stored outputs of a few minutes at most is
fine, with its hypothesis stated first; nothing longer, no featurization, training or attack.

The lean to watch for: the reviewers, the meta-reviewer and you are the same kind of model, inclined to accept
criticism (memory `distrust-simulated-reviews`). Two patterns: a criticism that **restates one of the paper's
findings as a flaw**, and a criticism of **a claim the paper does not make**. Equally, do not dismiss a real problem
because rebutting it is comfortable. Settled decisions (PLAN.md, `checklist.md`, the memories) count: name the
decision and its reason, and do not argue for reopening it; if the evidence contradicts one, say so plainly.

## What to write

Write **only** `{{OUT}}/rebuttal/{{GROUP}}.md`, at most about **600 words per item**, plain language (say what is
computed, what it is compared with, why it matters; define terms). Edit no other file, do not commit. The form:

```
# {{GROUP}}: {{ITEMS}}

## The deciding questions
<each question, its answer in a sentence or two, and where it was checked (file:line, output path)>

## R#: <the risk, in a few words>
**Opinion:** <change the methodology | change the argument or description | no change> (<one-line reason>)

<The objection at its strongest, in two or three sentences with the finding IDs and how many reviewers raised it.
Then the reasoning: what holds, the strongest rebuttal, and the two calibration answers (would I propose this if no
reviewer had raised it; does it restate a finding or attack a claim we do not make). For a change: the smallest change
that answers it, its cost, and what is lost without it; one recommendation, not a menu. For "no change": the
paragraph the authors would give in a rebuttal.>
```

Repeat the item section for each item of the group. The authors' decision is not yours to anticipate: no "decision"
or "next steps" section. Finish by printing the opinion lines.
