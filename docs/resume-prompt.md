# Resume: designing the full simulated review (not running it yet)

Written at the end of session 46 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors no edit in the threat
model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper is written straight
into `manuscript/*.tex` (`make` and `make check` in `manuscript/`); check `manuscript/main.aux` before naming a
section, table or definition number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` ("Where the paper stands", decision 8 (iv), "Next steps").

## Where things stand

- **Session 45** assessed the research as a whole and set the order (PLAN.md, next steps 1-7): the population decision,
  then this review, then the scale-up as one protocol, with the polish of §4-5 after it.
- **Session 46** decided the population (PLAN.md, decision 8 (iv)). Every split uses only the files our copy of EMBER
  2024 holds in full, below 4,000,000 bytes (whole binaries cannot be obtained), stated once in §5.1's Setup. §4.4
  defines the population as the complete files with a plain layout: almost every file outside it is incomplete (its
  headers locate content past its end). Most numbers in §5 and Appendix D are still pilot values on all files,
  truncated ones included, marked by `% PROTOCOL` comments; the scale-up replaces the detector results and a recount
  from stored outputs the checks (PLAN.md, open items). One blue value (5.4: 89% of the attacked malware in the
  population).
- The user reviewed none of session 46's text ("full faith"); the review is its first reader.

## The task

**This session designs the review and writes its instructions; it does not run it** (user, end of session 46: "Only
after that, will we actually run it"). Brainstorm the design with the user, giving a recommendation per question rather
than a menu, then write the instructions.

1. **Design questions** (the user's list, "including but not limited to"):
   - how many reviewers to run, and whether to personalize them (distinct expertise or stance per reviewer);
   - which conference to simulate (the manuscript uses ACM CCS's format; the old prompt simulated CCS with reviewers
     who also serve on S&P, USENIX Security and NDSS);
   - how to handle the obviously incomplete parts of the paper: pilot-scale numbers, the `% PROTOCOL` values (session
     46: the setup describes files below 4 MB, the numbers are from all files), blue predictions, empty sections
     (introduction, discussion, abstract, ethics, open science);
   - which models the reviewers run on and at what effort.
   Also worth settling: what the review must cover (PLAN.md, next step 2: the open risks R4, R5, R6, R9, R11, R15, R16
   of the 2026-11-02 register, the 2026-11-04 attack-strength concern, the new §3's novelty, the §2/§5 alignment,
   Proposition 1's role, the corpus-checked signatures, §4's template, the population, decision 6's revisit with a
   short literature pass, MAB-Malware's absence), how reviewers see the paper (PDF or `.tex`; whether they read
   `papers/`), the output format (scores, risk register), and whether a meta-review merges the reviews.
2. **Write the instructions:** update `docs/reviews/review-prompt.md` (it still targets the 2026-11-02 draft and the
   archived formalization; session 46 already added the 4 MB scope bullet and fixed the population in its settled
   list), plus any per-reviewer prompts and how to launch them.
3. **Next session after that:** run the review and discuss its findings with the user (memory
   `review-comments-workflow`); its output decides what the scale-up (next step 3) includes.

## Constraints and settled points

- Explain plainly, no jargon; a recommendation rather than a menu.
- No deadline talk; do not reopen settled decisions (PLAN.md "Settled decisions", decisions 8 (iv) and 10, the domain
  framing); ask before reframing what a claim or statistic is for.
- The paper: claims say "on EMBER"; no "pilot"; no protocol-hygiene details; PE minutiae kept out of the body where
  possible (bookkeeping to Appendix D).
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB.
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
