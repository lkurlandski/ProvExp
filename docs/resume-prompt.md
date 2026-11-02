# Resume: ProvExp (after 2026-11-02): take stock, then decide the next work

A' was dropped on 2026-11-02 (`docs/graveyard.md`; `docs/direction-A-prime-plan.md`, Section 13); two pieces fold into
A (`docs/direction-A-summary.md`, end). The user asked for a **pause before choosing further work**: a deep look at
what the project has accomplished since the restart (2026-10-22), and only then a decision on what comes next. The
user leans toward **formalizing the framework** (the three-layer model and its claims) rather than new applications
(B, C) or strengthening A, and is open to the alternatives. This session is a stock-take and a discussion, not a build:
no code or experiments until the user has decided.

## Read first

`CLAUDE.md`; `docs/status.md`'s top block; `PLAN.md` (Thesis, The model, Directions, Next steps 2026-11-02);
`docs/feature-provenance-model.md` in full (the three layers, claims C1-C4 with proof sketches, assumptions A1-A4, the
worked example, coverage of real transformations); `docs/item-layer-design.md` (the automatic derivation);
`docs/direction-A-summary.md`; the A' entry in `docs/graveyard.md`; `docs/literature-2026-10-22.md` (the closest work
on formalizing the feature-problem space gap: Pierazzi et al.'s problem-space formalization, Incer et al., and others).

## The stock-take

Write it for the user in plain language, then discuss. For each item: what it is, the evidence, and how a reviewer
would judge it.
1. **Established:** what has been built and checked (the model and its engines; C1 checked against re-extraction; C4
   directions derived automatically and checked by our own edits; direction A's results; the region's soundness for
   combined edits from A').
2. **Claimed but not yet shown:** which of C1-C4 have proofs, which only sketches, which rest on assumptions (A1-A4)
   that hold on EMBER but are unstated in general; what the model covers and what it flags.
3. **What the thesis needs** that is missing.

## The decision

Options to weigh with the user, each with a concrete example of the work, what it costs, and what it changes:
- **Formalize the framework** (the user's lean): definitions, theorems with proofs for C1-C4, the assumptions under
  which they hold, perhaps a second feature set or format to show the model is domain-agnostic. Be harsh on novelty:
  what does the formalization say that Pierazzi et al.'s formalization and data-flow / taint-tracking theory do not?
  What would a reviewer gain from it beyond direction A? Claude's view at the end of 2026-11-02 (discussed, not
  decided): formalizing first is right, on one condition. Every definition and theorem must be one that A's results
  rest on, or one that predicts something checkable against re-extraction. Otherwise it repeats the failure of the
  explanation-provenance direction (method first, applications found afterwards; `docs/graveyard.md`). Strengthening A
  is mostly execution and need not come first; screening B or C is premature until we know what the formal model
  offers them.
- **Strengthen A** (`docs/direction-A-summary.md`: adversarial-training baseline, second toolkit, leave-one-out PV,
  scale).
- **Screen B or C** (`PLAN.md`, Directions).

Record the decision in `PLAN.md`, `docs/status.md`, and this file.

## Standing rules

Be harsh about novelty; never raise deadlines; explain plainly; never use doc-internal labels (C3, M_full, G2) without
saying what they are; answer methodology questions by reasoning, not by running data first; run only jobs of ~10
minutes or less yourself; add a `run/` script for every experiment (next number: 117); commit in logical pieces after
ruff and mypy pass.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
