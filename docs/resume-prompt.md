# Resume: the humanistic review of §5 *Evaluation*, one subsection per pass

Written at the end of session 40 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`; `make` and
`make check` in `manuscript/`). §5 *Evaluation* is `manuscript/_f_evaluation.tex`: 5.1 *Setup*, 5.2 *What Hand
Analysis Misses*, 5.3 *What Observed Attacks Miss*, 5.4 *What Robustness Costs*; Appendix D *The EMBER Instance* is
`_j2_ember.tex`. Check `manuscript/main.aux` before naming a section, table or definition number, and give the title
alongside (`docs/README.md` has the compiled numbering as of 2026-11-12).

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; agreed, do not reopen; and "Next steps"). The `paper-prose`
skill governs any prose you write; the user's raw reactions are in `docs/writing-spec.md` (the latest entries, sessions
35-40, are the ones on §4-5).

## Where things stand

§2-4 are in good shape (§4 reviewed twice with the `humanistic-paper-review` skill, sessions 38 and 40). §5 is fully
drafted with no blue (synthetic) values left: run 135's leave-one-out folds were read and filled in session 40. What
the user has and has not read:
- **Lead and 5.1:** revised twice after the user's own reviews (session 35); the user has not commented on 5.1's last
  paragraph, *Checking results*.
- **5.2:** revised once; the user's second-round comments are pending (version 9b7d0ba).
- **5.3:** drafted in session 39; **the user has never read it.**
- **5.4:** reviewed by Claude with the skill and restructured in session 37; the user has not read the revised text.

## The task

The user decided (2026-11-12): apply `anthropic-skills:humanistic-paper-review` to §5 **one subsection per pass**, in
order: the lead and 5.1, then 5.2, then 5.3, then 5.4. About half a day in all. For each pass:
1. Read the source and the rendered PDF (`pdftotext`). Review only that subsection (Pass 1's section-level checks may
   look at how it connects to the lead). Lead with section- and paragraph-level findings; sentence-level patterns
   only when clearly ugly. Say plainly if a subsection is in good shape. **Do not edit before the user responds.**
2. When the user responds: answer their questions first, plainly; apply what they approve; `make`, `make check`, read
   the rendered text; show old and new text per finding; log their reactions raw at the end of `docs/writing-spec.md`
   (never as rules). Commit each pass.
3. Before each finding that names a number, check the source (run headers, `artifacts/`, the `%` comments beside the
   paragraph).

**How the user wants reviews handled** (sessions 38 and 40):
- Trimming is welcome, but moving very small snippets to the appendix does more harm than good.
- Keep the review's finding numbers throughout the conversation; never renumber them in a reply.
- Apply in small passes: first the findings the user understands and approves, so they can focus on the rest. Explain
  the others plainly, one at a time, when asked.
- A finding that touches what a claim rests on (proven, checked, or measured) needs care: verify in the code and the
  run outputs what was actually done before wording it (session 40's finding #1 on §4.3.2).

**Known items to fold into the right pass:**
- 5.1 and 5.2: the user's pending comments (5.1's *Checking results*; 5.2's second round, 9b7d0ba).
- Vocabulary from Table 2 (*The operations of the threat model*): §5 still says "GAMMA's import injection" and "the
  header-field attack" where Table 2 says "GAMMA imports" and "header fields"; Table 3 (5.2) says "signature table"
  where it means the certificate table ("signature" means only Definition 8).
- 5.3, points a careful reader may stop at (have answers ready; do not pre-emptively change them): PV is judged on 9
  files (counts are given, not rates; the scale-up adds files); "PV pays for the same gap a second time, in detection"
  ties two paragraphs and may read as staged; *What the attacks reveal* states 928 of 1,070 without a comparison (the
  seed comparison is out by the user's decision), so its point rests on "the other 142 look the same as features no
  edit can lower"; ERDALT is "our port of their code", and the paper does not claim their published numbers fail; the
  toolkit evasions of the GAMMA injections are partly outside the threat model (5.4 *Beyond the guarantee* explains
  it, 5.3 does not repeat it). Background, only if needed: `docs/evidence/section-5.3-design.md` (§10.4-10.5 and its
  log).

## Constraints and settled points

- §5.3 (user, session 39): no audit table for now (all tables are remade later); no random-seed or protocol-hygiene
  details in the paper; the learned-region paragraph stays cut; rename gets one sentence, no new run.
- §5.4 (do not re-raise): the sums row's adaptive cell stays 0% with its footnote; the full-training-set adaptive
  cells keep theirs; never propose scaling a cell down to the pilot protocol (everything scales up later); one toolkit
  column counting any of the eight attacks; no comparison of the adaptive attack's 51% with the toolkit's rate; no
  derivation-cost or timing paragraph.
- Tables 3 and 4 will be remade after this review (the user dislikes them): do not spend findings on their layout;
  note only what a table fails to tell the reader.
- Practitioners' likely objections, kept in view, not to be fixed now: the cost at 0.1% FPR (about ten points), the
  structural-only threat model (no packing, no code-level edits), pilot scale (10% subsamples, one seed, 50 malware).
- Explain plainly, no jargon. Claims say "on EMBER"; the detectors' accuracy cost is a measurement, never "small"; no
  timing of Proposition 1 against extraction; no effort claims. Exact numbers matter less than structure and argument.
- Keep the session focused and economical: short notes, a recommendation rather than a menu.
- Commit to `main` in logical pieces; do not push. At the end of the session, re-read and update `docs/status.md` and
  write the next resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).

## After this review (PLAN.md, next steps; not this session unless the user brings it)

1. To consider with the user: remake the tables (before shortening), shorten §4 and §5 together (§4 ~1,500 words
   against ~1,000), align §2's closing sentence and contribution 4 with §5's three findings.
2. The ERDALT check: every evasion of our port ends just under its threshold; a reviewer may call the port weak, and
   5.3's 24/29 rests on it. Look at its training before any run.
3. The 4 MB-truncation brainstorm.
4. Then decide with the user whether the paper is ready for the next full simulated review.
5. The scale-up (seeds 0-2, full splits, more malware) once the write-up is finished.
