# Resume: ProvExp (after 2026-11-02): plan the response to the harsh review

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`, one file per section; `make` and `make check` clean):
  - Section 3, the framework (`_d_framework.tex`), with its proofs in Appendix A (`_j_proofs.tex`).
  - Section 4, the EMBER instance (`_e_instances.tex`).
  - Section 5, the evaluation (`_f_evaluation.tex`). The mock's Tables 1-3 are Tables 5-7 of the PDF.
  - Every other section is an empty stub. Its comment states the planned content and word budget.
- **The harsh simulated review is done:** `docs/reviews/2026-11-02-body.md` (index of all reviews:
  `docs/reviews/README.md`). Read it first, in full.
  - Scores: formal methods Weak reject, adversarial ML for malware Weak reject, systems security Weak accept.
  - Likely outcome: reject with encouragement; borderline accept once its top risks are fixed.
  - Its Section 6 is the risk register (R1-R16) and its Section 7 the proposed action plan.
  - Ignore `docs/reviews/explanation-provenance/`: those reviews are about the abandoned direction.
- **Planning documents:**
  - `docs/status.md`, top block: what the review found, and which findings were verified against the docs.
  - `PLAN.md`, "Next steps (2026-11-02, review done)": the findings in order of weight, and their effect on the
    order of work.
  - `docs/paper-mock.md`, "After the review": the table changes the review proposes (not yet adopted).
- **Settled, do not reopen** (the review respected these; keep doing so):
  - The domain is adversarial examples in practical security tasks, and the framework is as agnostic as Pierazzi
    et al.'s. PE/EMBER is the main instance.
  - **Which breadth domain we use is unimportant and interchangeable.** Never make picking or vetting one the next
    priority. Whether the paper needs a second instance at all, and what it must show, is open.
  - Pilot scale; the GBDT first; no sandbox execution; our own byte-level edits; the plain-layout population with an
    unconstrained fallback and reported coverage; the dropped items (exact solver, projection, tightness, cost
    theorem, coupling row).
  - Paper text goes straight into `.tex`. `docs/formalization.md` is frozen (factual corrections only, such as the
    keyed-count sign entry, R10).

## The task: a plan to address the review's limitations

This session produces a plan, agreed with the user. It does not run experiments or rewrite sections.

1. **Read** `docs/reviews/2026-11-02-body.md`, then the status top block and the PLAN section named above.
2. **Check the review before trusting it.** Its "verified" list is in its last paragraph and in `docs/status.md`.
   Spot-check anything a decision will rest on, especially:
   - the adaptive search's operations and its 8% on the unconstrained model;
   - which toolkit outputs are outside the catalogue (the review *inferred* this from secml-malware's use of LIEF; the
     counts in its draft passage are placeholders);
   - the claim that in the population the derived and hand tables differ in two features.
   Reject any finding that does not hold, with the reason.
3. **Triage every risk, R1-R16, with the user.** Sort each into one of:
   - fix now in `.tex`;
   - a new run (state its hypothesis, its go/no-go, and its estimated runtime from the slowest case);
   - a framing decision for the user;
   - reject (with the reason).
   Skip sentence-level nits. Flag any mitigation that would change what a claim is for, as a decision for the user
   (e.g., reframing Table 6, or leading the paper with the detector).
4. **Put the agreed work in order**, by how much each item moves the verdict and what it costs. The review's own
   order, for reference:
   - first, hours: P1 and P2; the in-catalogue/out-of-catalogue split of the toolkit outputs; the "still detected"
     column; PV's hole re-measured with the derived table; coverage on untruncated files; timing; the writing fixes
     (Pierazzi's eta, keyed counts, R4's numbering, the novelty paragraph);
   - second, days: an adaptive search over all twelve operations, run on the same models as the rest of Table 7, and
     only then the adversarial-training row; the expert-set extractor instrumented; exactness rows for every
     operation; a second toolkit;
   - third, weeks: a second instance compared against constraints published by others, or a scope reduction now.
5. **Write the plan down:**
   - `PLAN.md`: a new "Next steps" section with the ordered work, each item's run (and `run/` script number if over
     ~10 minutes; next number 117) and its go/no-go.
   - `docs/paper-mock.md`: adopt or drop each change in "After the review".
   - `docs/status.md`: the decisions and their reasons.
   - This file: where the next session starts.

## Open decisions for the user (carried over, plus the review's)

- The title (working title: "Computing What Adversarial Edits Do to Features"); a conclusion section or not; where
  "Reading the Sums Directly" goes.
- From the review: whether Table 6 is reframed around completeness and the population boundary; whether the
  introduction leads with the detector; whether to build a second instance or reduce the scope; whether to rename
  Theorem 1 a proposition.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Runs: only jobs under ~10 minutes yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script for the user.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not
  push.
