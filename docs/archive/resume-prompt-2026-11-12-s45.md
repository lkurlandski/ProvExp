# Resume: the 4 MB-truncation brainstorm, ending in a decision on the population

Written at the end of session 45 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors no edit in the threat
model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper is written straight
into `manuscript/*.tex` (`make` and `make check` in `manuscript/`); check `manuscript/main.aux` before naming a
section, table or definition number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` ("Where the paper stands", with session 45's assessment, and
"Next steps").

## Why this session

Session 45 assessed the research as a whole (PLAN.md, "Where the paper stands") and the user agreed on a new order
(PLAN.md, next steps 1-7): the truncation brainstorm, then a full simulated review, then the scale-up, with the polish
of §4-5 after it. The user coupled the first two: "our decision about truncation could affect the review". So this
session brainstorms how to fix the population, ends in a decision, and writes the decision into the manuscript, so
that the review (next step 2) reads the paper as it will be.

## The problem

The guarantee (Theorem 1, Corollary 1) holds over a *population*: §4.4 *Population* defines it as the PE files with a
plain layout (everything the parser locates lies within the file, the sections lie within the mapped image, the headers
hold only headers; `catalogue.plain_layout` and `catalogue.precondition` in `src/provexp/featuresets/ember2024/`).
A file outside it is routed to the unconstrained detector, with no guarantee. Our copy of EMBER 2024 (SimpleDB,
`/shared/datasets/EMBER-2024/data/`) truncates every binary at 4,000,000 bytes, and a truncated file often has
something the parser locates past its cut end, so it fails the check. The user finds this ugly (decision 8 (iv)).

What is on record (2,000 test files; the archived status log of 2026-10-to-11-09 has the details):

- 1,674 of 2,000 test files are in the population; of the attacked malware, 38 of 50.
- Truncated files: 330 of 2,000; 98 of them pass the check.
- Untruncated files: 1,576 of 1,670 pass (94.4%): benign 924/938 (1.5% non-plain), malware 652/732. Pilot detected
  malware, untruncated: 31 of 35.
- 94 untruncated files fail; which clause each fails is not yet counted (a cheap first step).
- The released EMBER 2024 features were computed on untruncated files (our extractor matches them on untruncated files;
  `docs/design.md`), so whole binaries existed for the dataset's authors; whether we can get them is unknown.
- §4.4 and 5.4's *Where the guarantee holds* state the current numbers; R7 of the 2026-11-02 risk register (routing as
  an attack surface) is the reviewer angle.

## The task

1. **Brainstorm with the user.** Options raised so far: measure on whole binaries if they exist; state each edit's
   effect correctly on non-plain files (start with which clause the 94 untruncated non-plain files fail); exclude
   files over 4 MB from the experiments (memory `constrain-experiment-complexity`: under consideration). New options
   are welcome. For each: what the paper would then say, what it costs, what a reviewer would make of it, and whether
   it needs runs. Explain plainly; give a recommendation, not a menu.
2. **Decide**, with the user. The decision should not wait for its runs: decide on the evidence at hand; any run it
   needs joins the scale-up (next step 3), as a `run/` script if over ~10 minutes.
3. **Write the decision into the manuscript**: §4.4 and what depends on it (5.4's *Where the guarantee holds*,
   Appendix D, counts in §5.1 if affected), with predicted values in blue (`\synthetic{...}`, a `% SYNTHETIC` comment
   naming the run that replaces them) where runs are pending. Use the `paper-prose` skill; small blocks, the user
   reviewing. `make` and `make check`.
4. Then the review (next step 2) can start, in this session if time allows and the user wants it, otherwise next
   session: update `docs/reviews/review-prompt.md` first (PLAN.md, next step 2, lists what it must cover, including one
   line naming the population change).

## Constraints and settled points

- Explain plainly, no jargon; a recommendation rather than a menu; stay on the population question.
- No deadline talk; do not reopen settled decisions (PLAN.md "Settled decisions", decision 10, the domain framing);
  ask before reframing what a claim or statistic is for. No result may rest on an extractor quirk.
- The paper: claims say "on EMBER"; no "pilot"; no protocol-hygiene details; PE minutiae kept out of the body where
  possible (bookkeeping to Appendix D).
- Never propose running modified samples in a sandbox (loader-safe edits and documentation suffice).
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
