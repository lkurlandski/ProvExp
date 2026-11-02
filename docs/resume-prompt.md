# Resume: ProvExp (after 2026-11-02): formalization review, round 2

## Where we are

The formal model is in `docs/formalization.md`, at revision 3. It has been through one round of the user's review,
logged in `docs/feedback.md` (items 1-5, all applied). The user has read up to the old Section 5. The new Sections
5-8 have not been reviewed yet.

The user's round-1 criticisms, and how revision 3 answers them:
- **Organization and structure.** Revision 2 had "Definitions/Theorems" headings and a lead the user found
  unintelligible. Every section now opens with its question and an example. The old Sections 5 and 6 are merged into
  "Predicting what one edit does to the features", in this order: the recipe, how it fails, the requirements, the
  theorem, the checks.
- **Clarity.** There is a full notation table, reusing Pierazzi et al.'s symbols. The requirements are named by meaning:
  faithful recording, self-contained contributions, complete record of structure, changes stay near the edit, honest
  tools. The old codes were A0, A2, A1, A3, A4.
- **Agnosticism.** Small real examples from three domains run through every section: PE files with EMBER, APKs with
  Drebin, and traffic with CICFlowMeter. Operations carry an item signature. Format-dependent requirements are needed
  only for edits stated in raw elements, and Section 8 tabulates what each result needs.
- **Algebra.** There is a short remark on sums as a monoid homomorphism. Addition can be undone, a maximum cannot,
  which is why the item table is kept. Gray et al.'s algebraic vs holistic aggregates mark where the class ends.

Decisions this session (`PLAN.md`, "Revised"; `docs/status.md`, top block):
- **Three domains, emphasized about equally for now:** PE/EMBER, APK/Drebin, traffic/CICFlowMeter. This replaces "a
  second domain later". Revisit if data is lacking, or if Drebin adds little beyond EMBER.
- **Traffic:** CICFlowMeter features serve as the examples. CTU-13 with Chernikova and Oprea's FENCE features is the
  candidate experimental instance and baseline: its roughly 360 hand-written constraints are what Theorem 2 would
  derive. A deeper literature pass comes later.

## The work this session

1. **Ask the user for round 2 of the review.** Start with the new Sections 5-8, then Section 9 (EMBER) and Section 10
   (still to write). Discuss interactively and log each point in `docs/feedback.md` as a new item: the user's point,
   the discussion, the decision. Do not edit `docs/formalization.md` until the user says to apply the feedback. Then
   revise in one pass and mark the items applied.
2. **After the review, write the remaining results in Section 10, in the same style:**
   - coupling;
   - the reachable region;
   - the provenance matrix as a projection;
   - tightness;
   - cost;
   - positioning.

   The style: question first, then an example from each domain, then each term when it is needed, then the result,
   then the proof.
3. **Before the examples reach the paper, verify the facts listed in Section 10 ("To verify"):**
   - Drebin's suspicious-API list and API-to-permission map (`getDeviceId`, `READ_PHONE_STATE`);
   - CICFlowMeter's feature definitions: which lengths count, and how flows end (FIN flags, timeout);
   - FENCE's constraint count.

   This is light reading. Do not start building instances for Drebin or CICFlowMeter.

Later steps (`PLAN.md`, "Order of work"): a paper mock, a harsh simulated review and a decision point, A's gaps, and
then the Drebin and CICFlowMeter instances, each after a feasibility pass. The feasibility pass covers raw data with
labels, an open extractor, and an attack or hand-written constraints to compare against. Data: PE and ELF files are
local; raw APKs come from AndroZoo (academic key); traffic comes from public pcaps (CTU-13 / Stratosphere,
CIC-IDS2017/2018 with Engelen et al.'s corrected CICFlowMeter).

## Read first

- `CLAUDE.md`
- `docs/status.md`, top block
- `PLAN.md`: "Next steps (2026-11-02 ...)", including "Revised"
- `docs/formalization.md`, in full
- `docs/feedback.md`, in full: what the user has asked for so far, and why

## Standing rules

- Explain plainly. Lead with the question and an example. Define every symbol. Never use doc-internal labels (C3,
  A1, G2) without saying what they are.
- Answer methodology questions by reasoning, not by running data first.
- In the formalization, keep PE minutiae in Section 9. Frame the general sections generically for malware and traffic.
- Never raise deadlines. Do not edit the manuscript.
- At the end of the session, update `docs/status.md`, `PLAN.md`, and this file.
- Commit in logical pieces.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- `TODO.md` (the user's) lists reading Demontis et al., "Yes, Machine Learning Can Be More Secure!". It is relevant to
  the Drebin domain and to positioning.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
