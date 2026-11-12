# Resume: the full simulated review of the manuscript

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

1. **Update `docs/reviews/review-prompt.md`** before running it. It still targets the 2026-11-02 draft and the
   archived formalization (its file list, stage description, sources, settled points). Session 46 already added the
   bullet on the 4 MB scope (review the setup as written, numbers as pilot values; judge the scope itself) and fixed
   the population in its settled list. PLAN.md, next step 2, lists what the review must cover: the open risks of the
   2026-11-02 register (R4, R5, R6, R9, R11, R15, R16), the 2026-11-04 attack-strength concern, the new §3 (novelty
   above all), the §2/§5 alignment, Proposition 1's role (no finding of its own), the corpus-checked signatures, §4's
   template on the page, the new population, decision 6's revisit (is a problem-space defense expected? a short
   literature pass), and MAB-Malware's absence. Body only; no narrow §2-3 review beforehand (user).
2. **Run the review** as the reviews README says (`docs/reviews/README.md`: a fresh context, output to
   `docs/reviews/<date>-<stage>.md`, a line in the README's index). Ask the user whether to run it as a subagent from
   this session or in a fresh chat.
3. **Discuss its findings with the user** (memory `review-comments-workflow`: answer questions first, keep the
   review's finding numbers, small passes). Its output decides what the scale-up (next step 3) includes.

## Constraints and settled points

- Explain plainly, no jargon; a recommendation rather than a menu.
- No deadline talk; do not reopen settled decisions (PLAN.md "Settled decisions", decisions 8 (iv) and 10, the domain
  framing); ask before reframing what a claim or statistic is for.
- The paper: claims say "on EMBER"; no "pilot"; no protocol-hygiene details; PE minutiae kept out of the body where
  possible (bookkeeping to Appendix D).
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB.
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
