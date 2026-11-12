# This run's checklist and settled points (edit before each run)

The reviewers never see this file. The meta-reviewer works through it after reading their reviews.

## Questions the review must answer

For each item: did a reviewer raise it unprompted (who, and with which finding ID), and what is your own judgement
after checking the manuscript and the sources?

1. **The open risks of the 2026-11-02 register** (`docs/reviews/2026-11-02-body.md`, Section 6): R4 (one instance for
   a general claim), R5 (Pierazzi et al.'s side effects read correctly), R6 (are the results known techniques
   renamed), R9 (what Proposition 1 enables that re-extraction does not), R11 (every cell of a table from the same
   detectors), R15 (packing and code rewriting excluded), R16 (PE minutiae). For each: still open, resolved by the
   current text, or changed.
2. **Attack strength** (the 2026-11-04 concern, `docs/reviews/2026-11-04-strategy.md`): are the attacks strong enough,
   compared with published budgets and evasion rates on the same feature set, for each claim that rests on them? Every
   evasion of a defense comes from the authors' own table-guided search or the secml-malware toolkit.
3. **The novelty of the current Section 3** (rewritten after the last review): items, sums and readouts; Proposition 1;
   Theorem 1 and Corollary 1. Against incremental view maintenance, abstract interpretation, provenance, and the
   monotone-detector line.
4. **Section 2 against Section 5:** does the evaluation deliver what Section 2 promises (it says Section 5 uses the
   results "to attack malware detectors and to build robust ones")?
5. **Proposition 1's role:** it has no finding of its own in Section 5. Does a reviewer miss one, and what would
   answer that without a timing claim (no timing comparison will be made)?
6. **The corpus-checked signatures:** the directions of the operations stated as writes are collected from the files'
   item tables and checked, not proven, to cover the population (Section 4.3.2). Acceptable to a formal reviewer?
7. **Section 4's template** for instantiating the framework: does it read as a reusable recipe or as EMBER detail, and
   would a second domain fit it?
8. **The population and the 4 MB scope** (Sections 4.4 and 5.1): what reviewers make of leaving out the files over
   4 MB (a quarter of the test malware) and of the files outside the population going to an unconstrained detector.
9. **The problem-space defense (decision 6's revisit):** would a reviewer expect a problem-space defense (adversarial
   training on problem-space examples) to be shown, beyond the adversarial-training row? Do a short literature pass:
   Lucas et al. (`papers/lucas2023adversarial.pdf`, `papers/lucas2024training.pdf`), Dyrmishi et al.
   (`papers/dyrmishi2023empirical.pdf`), and the work citing them since 2023.
10. **MAB-Malware's absence:** no attack the authors did not write evades a defense in the paper. How much does a
    reviewer hold that against Sections 5.3-5.4? (MAB-Malware is planned for the full-scale run as a held-out attack.)
11. **Section 5's three findings** (what hand analysis misses, what observed attacks miss, what robustness costs):
    does each lead answer its question, and which finding is weakest?
12. **The comparisons with published defenses:** whether the ports of PV, ERDALT and the expert set (Gimenez et al.) are
    fair, checked against their papers in `papers/`.

## Settled: do not re-propose

These were decided. Do not list them as mitigations. If one now looks fatal (it would by itself sink the paper), say so
once, in the risk register, with the reason.

- **The domain** is adversarial examples in practical security tasks; the framework is as agnostic as Pierazzi et al.'s;
  PE malware is the main instance. Which second domain is used for breadth is the authors' call: you may say whether
  the paper needs a second instance and what it must show, not which domain.
- **Scale** (seeds 0-2, full splits, more malware, MAB-Malware) comes with the full-scale run, on the authors'
  decision; this review decides what that run includes.
- **The GBDT** is the first classifier; the MLP is set aside for now.
- **No sandbox execution** of modified samples: loader-safe edits plus documentation suffice.
- **Edits are written by the authors' own byte-level code**, not LIEF; files they cannot edit are skipped.
- **The population** is the complete files with a plain layout; files outside it go to an unconstrained detector, and
  coverage is reported. Every split uses only the files below 4 MB; do not propose obtaining the larger files. A
  detector sound over every possible file is one sentence, not a row.
- **Code-level transformations** (code randomization, instruction substitution, call redividing) stay out of the
  threat model for now, a stated limitation.
- **Section 5 is three findings, not a defense paper:** no state-of-the-art-defense claim; the detectors' cost is a
  measurement.
- **No timing claims:** the paper says Proposition 1 does less work than re-extraction and can be faster, never that it
  is.
- **No protocol-hygiene details** (seeds and the like) in the paper; no effort claims (person-days, lines of code).
- **Dropped:** realizable worst-case evaluation with an exact solver; a tightness theorem; a cost theorem; coupling;
  reachable regions.
- **Writing:** continuous prose; limitations light and confident, no Threats to Validity section; no internal IDs; the
  page limit does not matter yet; the introduction is written last.
