# Resume: ProvExp (after 2026-11-02): feasibility reading, paper mock, framework in .tex

## Where we are

The formal model is in `docs/formalization.md` (revision 5, 13,100 words). It is **frozen** as the reference and
appendix source; it is not a paper draft, and its Section 10 will not be written unless the mock needs a result.
Settled with the user (`PLAN.md`, "Reassessed"): the domain is adversarial examples in practical security tasks; the
framework is as agnostic as Pierazzi et al.'s; PE malware is the inspiration and main instance; other domains are
breadth. Do not reopen this. Paper text goes straight into `.tex`.

## The work, in order

0. Done: the feasibility reading (`docs/status.md`, top block). Start at step 2.

1. **Feasibility reading for breadth instances** (light; no code, no instances): for Android apps with Drebin and
   traffic with CICFlowMeter or CTU-13/FENCE (others if cheaper), check whether raw labeled data, an open extractor,
   and an attack or hand-written constraints to compare against exist. Verify on the way: Drebin's suspicious-API list
   and API-to-permission map (`getDeviceId`, `READ_PHONE_STATE`); CICFlowMeter's feature definitions (which lengths
   count, how flows end); FENCE's constraint count; Pierazzi et al.'s exact wording on computing side effects in
   advance. Report briefly.
2. **Paper mock** (`docs/paper-mock.md`, at most two pages): contributions, outline with a word budget per section,
   every table and figure with the model component behind each column and measured vs missing cells.
3. **Framework section in `.tex`** (`manuscript/`), to its budget (about 2,500 words): one main PE example, a
   cross-domain table, the side-effect and direction theorems, the requirements as a compact list; proofs in the
   appendix. Run `make` and `make check`. Report the length against the budget.

## Read first

- `CLAUDE.md`; `docs/status.md`, top block; `PLAN.md`, "Reassessed" and the order of work below it
- `docs/formalization.md`, Sections 1, 3-7 (the source for the framework section); `docs/direction-A-summary.md`

## Standing rules

- Explain plainly. No doc-internal labels. Name features in plain words.
- No new markdown drafts of paper text. Keep the mock short.
- Never raise deadlines. Commit in logical pieces. At the end, update `docs/status.md`, `PLAN.md`, and this file.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- `TODO.md` (the user's) lists Demontis et al., "Yes, Machine Learning Can Be More Secure!" (Drebin, positioning).
- The user still owes the upstream reports in `docs/upstream-issues.md`.
