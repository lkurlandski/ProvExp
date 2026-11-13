# Resume (orthogonal track): the next review item that does not touch R7's text

Written at the end of session 53b (2026-11-13), a session that ran in parallel with session 53's R7 work. R7 (the
widening: closure check, `ent` in the attacks, run 141, then the paper) continues in its own sessions from
`docs/resume-prompt.md`. **Do not work on R7 here**, and do not edit the files and passages it owns (below). If R7 has
finished by the time you read this, `docs/resume-prompt.md` takes precedence; ask the user which track to follow.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. §5 is three findings:
what hand analysis misses (5.2), what defenses learned from observed attacks miss (5.3), what robustness costs (5.4).
The paper is written straight into `manuscript/*.tex`; check `manuscript/main.aux` before naming a section, table or
theorem number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (next step 2: the review's register, triaged one item at a
time). The review: `docs/reviews/2026-11-12-body/meta-review.md` (§6 the risk register R1-R21, §8 the writing actions).

## What R7 owns (leave alone)

§4.3.1 *Operations* and Table 2 (the operations of the threat model), §4.4 *Population*, §5.1's setup and routing,
§5.4 (*The price*, *Where the guarantee holds*), Table 5 (the detectors), Appendix D's population and routing text, and
the code in `src/provexp/featuresets/ember2024/catalogue.py`, `scripts/a_directions.py`, `scripts/a1_adaptive.py`,
`scripts/catalogue_checks.py`. Commit only the files you changed (`git add <paths>`): the R7 session may have
uncommitted work in the tree.

## Done in session 53b: R17 (Reviewer A, W1 and W3)

- The ratio rule needs only *a = 0 whenever b = 0* (weaker than the old *b > 0 before and after*, which EMBER's files
  without strings violated): Table 1's caption and row, Appendix C's two zero cases, one sentence in Appendix D (11ff54d).
- Theorem 1 holds for sums in *totally ordered* monoids (Fuchs 1963): §3.3 shows with a product of signed values
  (−3 to −6) why the directions need the order, and refers to Fuchs for the structure; Theorem 1, its sketch and
  Appendix C's proof name it (b1060e8).
- **Rejected by the user:** the universality/locality "gap" (items are hierarchical, so the framework stays
  well-defined at its limit; that is a strength). The user is open to a *deeper exploration* of how item size and
  locality matter, not to a "fix"; raise it only as an idea. **Dropped:** Appendix D's sentence on the minima.
- How the user wants framework gaps handled (memory `elegant-framework-fixes`): judge first whether a human reader
  would care; for a real gap, a small patch that *strengthens* the result (a weaker condition, a named standard
  structure with a citation), never a fallback that excludes the hard case and never a list of new clauses. Show the
  rendered old/new text before committing.

## The task

Recommend **one** next item to the user and get approval before editing. Recommended: **§6, the meta-review's writing
action 4 (R21, with R6's leftovers)**, all in `manuscript/_g_related_work.tex`, untouched by R7:
- a paragraph on certified malware defenses: bounded byte edits or a feature-space radius (RS-Del, DRSM, Gibert et al.,
  Giri et al.) against our unbounded but typed edits. In `papers/`: `saha2024drsm.pdf`; `gibert2025assessing` is in
  `main.bib`; RS-Del and Giri et al. are not, so find and read them first (add entries from real records);
- Kantchelian et al. and Calzavara et al. as verification of the *model*, not of the extractor (`kantchelian2016evasion`
  is in `main.bib` but uncited; `calzavara2020certifying` is cited);
- problem-space adversarial training: Lucas et al. 2023 and 2024 (`lucas2024training` uncited), Tsingenopoulos et al.
  (`papers/tsingenopoulos2024train.pdf`, not in `main.bib`);
- cite Cortellazzi et al. (`cortellazzi2025intriguing`, uncited).

Every claim about a cited work is checked against `papers/` in its authors' own terms (memories
`portray-cited-work-accurately`, `credit-without-diminishing`). Draft with the `paper-prose` skill in small blocks.

Other orthogonal candidates if §6 is done: §5.3's items from writing action 6 (the toolkit's budget attributed to
Gimenez et al.'s *released code*; R12's counts without the 88 warnings, a recount from stored outputs; R19's ERDALT
constraint check), and §5.2's expert-set items (writing action 7). §2 is settled as it is (R5's points need the user's
explicit go-ahead). R2's trust paragraph sits in §4.3.2, next to R7's text: ask before taking it.

## Constraints and settled points

- Explain plainly; one recommendation, not a menu. State a hypothesis before any run; report a failed check as such.
- No deadline talk; do not reopen settled decisions (PLAN.md; `docs/reviews/process/checklist.md`, "Settled").
- Jobs over ~10 minutes go to the user as `run/` scripts (`NUM_WORKERS`, default 16).
- After manuscript edits: `make` and `make check` in `manuscript/`, and read the rendered text (pdftotext). Before
  committing code: `env/bin/ruff check src tests scripts`, `env/bin/mypy src tests scripts`. Commit to `main` in
  logical pieces; do not push.
- At the end of the session: update `docs/status.md` (its own session-log entry, without rewriting R7's), PLAN.md if a
  decision was made, and this file (archive the old version under `docs/archive/` and index it in `docs/README.md`).
