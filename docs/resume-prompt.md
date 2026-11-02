# Resume: ProvExp (after 2026-11-02): formalization, Section 10

## Where we are

The formal model is in `docs/formalization.md`, at revision 5. Review rounds 1 and 2 are logged in `docs/feedback.md`
(items 1-13, all applied). The user delegated round 2: the document is at an early stage and not worth a detailed
review yet, so Claude decides presentation and correctness fixes and logs them. Recent changes: end-anchored items in
Requirement 3 (appending lengthens the overlay); presence rule $E_s \cup \{0\}$; pattern counts as 0/1 add terms;
layout-dependent signatures stated honestly; lemmas regrouped (Lemma 5 patterns, Lemma 6 readout rules, Lemma 7
single-input tests in Section 10.1); Section 2 is a short primer, and features are named in plain words (no p/d/c
labels).

## The work this session

1. **Write the remaining results in Section 10**, in the document's style (question first, an example from each
   domain where it helps, each term when needed, the result, then the proof): coupling; the reachable region (Lemma 7
   is already there as material); the provenance matrix as a projection; tightness; cost; positioning. Log notable
   choices in `docs/feedback.md`; the user does not need to review each.
2. **Light verification reading** (Section 10, "To verify"): Drebin's suspicious-API list and API-to-permission map
   (`getDeviceId`, `READ_PHONE_STATE`); CICFlowMeter's feature definitions (which lengths count, how flows end);
   FENCE's constraint count; Pierazzi et al.'s exact wording on computing side effects in advance. Do not build
   Drebin or CICFlowMeter instances.
3. Then the paper mock (`PLAN.md`, "Order of work", step 2). Open for it: run all three domains through every
   definition, or one main example plus the concept-by-domain table.

## Read first

- `CLAUDE.md`; `docs/status.md`, top block; `PLAN.md`, "Next steps (2026-11-02 ...)", including "Revised"
- `docs/formalization.md`, in full; `docs/feedback.md`, items 6-13

## Standing rules

- Explain plainly; lead with the question and an example; define every symbol; no doc-internal labels without saying
  what they are; name features in plain words.
- Answer methodology questions by reasoning, not by running data first.
- In the formalization, keep PE minutiae in Section 9.
- Never raise deadlines. Do not edit the manuscript.
- At the end of the session, update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- `TODO.md` (the user's) lists Demontis et al., "Yes, Machine Learning Can Be More Secure!": relevant to Drebin and
  positioning.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
