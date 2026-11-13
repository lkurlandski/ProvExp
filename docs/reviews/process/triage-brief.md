# Your task: triage the risk register of a simulated review

You sort every item of a simulated program-committee review's risk register by whether the authors should act on it.
You decide what deserves a closer look; you do not do that closer look. One file, one pass, in one context.

Commit reviewed: {{COMMIT}}. Review folder: `{{OUT}}/`. Items decided before this run: {{DECIDED}}.

## Why this exists

Four reviewers saw only the PDF. A meta-reviewer with full project access checked their findings and ranked the risks
(`meta-review.md` §6). All of them are the same kind of model as you, and that model leans toward accepting criticism
(memory `distrust-simulated-reviews`). The meta-review's **facts** are reliable: take every [verified] fact as
established and do not re-check it. Its **judgement** is not: "correct" there usually means the quote is accurate,
not that the objection matters. Your job is the judgement. The user found the first items of the register relevant and
many later ones pedantic; telling those apart cheaply is the point.

## What to read, and what not to

Read, once each: `PLAN.md` (the decisions; what is settled and why), `{{OUT}}/meta-review.md` (all of it),
`{{OUT}}/reviewer-*.md` (all four), `{{OUT}}/checklist.md`. To quote a claim the criticism targets, grep or `sed -n`
the `.tex` in `manuscript/`; for a section, table or theorem number, grep `manuscript/main.aux`.

Do **not** open code, stored outputs, logs, `papers/` or other docs, and run nothing. If an item's opinion hangs on a
fact the meta-review does not establish, that is exactly what the verdict *investigate* is for: name the fact and move
on.

## The verdicts

For each register item, one of:
- **decided**: only for the items listed above as decided before this run. Name the decision.
- **dismiss**: the criticism restates one of our findings as a flaw, attacks a claim the paper does not make, reopens a
  settled decision (name it and its reason; do not argue for reopening it), or asks for something no reader at the
  venue would miss. Give the one-paragraph answer the authors would write in a rebuttal.
- **cheap fix**: a real point, answered by a change to wording, scope, a citation or one sentence, that costs hours of
  writing and risks nothing else. State the change in a sentence or two.
- **investigate**: a real point whose right answer depends on facts the meta-review does not establish, or on a change
  to the methodology. Name the **two or three deciding questions**: each one checkable against the code, the stored
  outputs, the manuscript or `papers/`, and each one able to flip the opinion. Nothing else will be checked.

Before each verdict, answer for yourself: *Would I propose this if no reviewer had raised it?* *Does the criticism
restate one of our findings, or attack a claim we do not make?* How many reviewers raised it counts: one reviewer's
objection weighs differently from four. Equally, do not dismiss a real problem because rebutting it is comfortable; a
risk the meta-review rates fatal or major needs a stated reason to be dismissed.

**Earlier decisions on an item.** PLAN.md may record a decision the authors took on an item in
response to this review (it names the item or the review, or dates from after it). Do not let it decide your verdict:
judge the item on its merits as if undecided, then end its entry with a line `**Earlier decision:** <what was
decided, where recorded>; <agrees | differs>: <why, one sentence>`. These comparisons calibrate the triage, so a
plain disagreement is more useful than a reconciliation. Decisions that predate the review (scope, threat model,
settled points in `checklist.md`) remain settled and count as described under *dismiss*.

A register row often bundles several objections. Judge the row by its parts: a row may be "dismiss" except for one
cheap fix; say so in the reason.

## Groups

Items that share a premise or a fix are decided together (e.g., several items that turn on the same trust argument,
or on the same full-scale run). Group the **investigate** items so that each group's deciding questions are checked
once; a group of one is fine. Name each group with one lowercase word.

## What to write

Write **only** `{{OUT}}/rebuttal/triage.md`, about 2,000-3,000 words, plain language (say what is computed, what it is
compared with, why it matters; define terms). Edit no other file and do not commit. The form, exactly (the script
reads the table and the `GROUP` lines):

```
# Triage of the {{TAG}} register

Commit {{COMMIT}}. Verdicts: decided, dismiss, cheap fix, investigate.

| Item | Risk (short) | Verdict | Group | Decision |
|---|---|---|---|---|
| R7 | <a few words> | decided | | |
...

## Groups to investigate

GROUP <name>: R# R# ...
- <deciding question 1>
- <deciding question 2>

## The items

### R7: <the risk, in a few words>
**Verdict:** <verdict>. <the reason, two to five sentences: what the reviewers object to, which part holds, and why
the verdict follows; the rebuttal paragraph for "dismiss", the change for "cheap fix", the deciding questions'
rationale for "investigate">
```

Leave the Decision column empty: the user fills it in. Finish by printing the table.
