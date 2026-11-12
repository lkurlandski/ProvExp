# Resume: a lightweight second review of §4 *Instantiating the Framework*, then the holistic review of §5

Written at the end of session 38 (2026-11-11). Self-contained: everything needed to start is below or in the files it
names. (`docs/resume-prompt-5.3.md` belongs to a parallel session drafting §5.3; leave it alone.)

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`, compiled with `make`
and checked with `make check` in `manuscript/`): §4 is `manuscript/_e_instances.tex` (4.1 *EMBER and PE Files*, 4.2
*EMBER as a Sum-then-Readout Extractor*, 4.3 *Threat Model* with subsubsections 4.3.1 *Operations* and 4.3.2
*Signature*, 4.4 *Population*; details in Appendix D *The EMBER Instance*, `_j2_ember.tex`), §5 is
`manuscript/_f_evaluation.tex`. Always check `manuscript/main.aux` before naming a section, table or definition
number, and give the title alongside.

**Read first:** `CLAUDE.md` (rules), `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; agreed, do not reopen). The `paper-prose` skill governs
any prose you write; the user's raw reactions are in `docs/writing-spec.md` (session 38's entry is the latest on §4).

## What happened in session 38

Claude reviewed §4 with `anthropic-skills:humanistic-paper-review` (eight findings). The user accepted all eight,
applied in two passes: first the ones they understood and approved, then the two that needed explaining. Commits
c7d0734, cf4f4a4, b8b710c (and the user's own small edit 07e9f83):
- §4.3's attacks are named by Table 2's operations; Table 2 gained a "Toolkit attacks" column (from secml-malware's
  code: padding = append; GAMMA sections, GAMMA imports; DOS extension = gap before the PE header; content shift and
  GAMMA shift = gap before the first section; format exploit = both gaps; header fields = loader-ignored fields).
- The Zainab et al. sentence was dropped: their two-attack result is about which attacks to run, and MAB-Malware uses
  code randomization, which our threat model excludes.
- "Certificate table" names the PE structure and "Authenticode signature" its content, so "signature" means only
  Definition 8 in §4 (Table 8's row renamed too).
- §4.2's item list shortened (Appendix D has the full list); the instrumentation sentence moved into §4.2.
- The lead says "the extractor in sum-then-readout form" and "features that do not fit this form".
- 4.3 split into *Operations* and *Signature*; *Signature* opens with what is proved (declared changes, checked by
  re-extraction) and what rests on the files (changes read from item tables, and which sums each kind feeds), then
  declared changes, then changes read from item tables (with the single-edit decline kept in the body).
- 4.4 reordered: definition and example, closure (60,934 of §5.1's 73,063 edits, those on files in the population),
  coverage (1,674 of the 2,000 test files; truncation; 94% of untruncated files), then routing at inference.

**How the user wants reviews handled** (from session 38; also in `docs/writing-spec.md`):
- Trimming is welcome, but moving very small snippets to the appendix does more harm than good.
- Keep the review's finding numbers throughout the conversation; never renumber them in a reply ("a new numbering
  system ... makes things extremely confusing").
- Apply in small passes: first the findings the user understands, agrees with, and approves, so they can focus on the
  rest. Explain the others plainly, one at a time, when asked.
- Lead with section- and paragraph-level findings; sentence-level patterns only when clearly ugly.

## The task

1. **A lightweight second review of §4** with `anthropic-skills:humanistic-paper-review`, on the revised text (read
   the source and the rendered PDF with `pdftotext`). Lightweight means: a few findings at most, only what still
   hinders a reader after session 38's changes (in particular whether the new 4.3.2 *Signature* and 4.4 read
   smoothly, and whether the toolkit column in Table 2 works); no re-raising of what session 38 settled; say plainly
   if §4 is in good shape. Do not edit before the user responds.
2. When the user responds: answer their questions first; apply what they approve; `make`, `make check`, read the
   rendered text; show old and new text per finding; log their reactions raw at the end of `docs/writing-spec.md`.
3. **Then §5**, the same way, over the whole section (lead, 5.1, 5.2, 5.4), skipping §5.3 *What Observed Attacks
   Miss* (below). The user's own pending comments on 5.1's *Checking results* paragraph and on 5.2 *What Hand
   Analysis Misses* (version 9b7d0ba) can join this review. Known items to fold in: §5 says "GAMMA's import
   injection" and "the header-field attack" where Table 2 now says "GAMMA imports" and "header fields"; Table 3
   (§5.2) says "signature table" where it means the certificate table.

## §5.3 belongs to another session

A parallel session is drafting §5.3 (`docs/resume-prompt-5.3.md`; block 1 committed in 7a2ceff), and the user is
running experiments for it in the background (run 135, `run/135_loo_varied.sh`, leave-one-out from run 133's
outputs). Do not edit §5.3, `docs/section-5.3-design.md`, `docs/resume-prompt-5.3.md`, the paragraphs marked
`% 5.3 MATERIAL`, the table rows in the `% MOVED TO 5.3` comment, runs 133-135 or their outputs
(`artifacts/experiments/a_varied/`, `a_loo_varied/`, `a_pv/`, `a1/advtrain/generated-seedperfile/`). Do not start
jobs that compete with the user's runs without asking. Check `git log` first: that session may have committed changes
to §5, `docs/status.md` or `PLAN.md`; re-read those right before editing them and change only your own lines.

## Constraints and settled points

- Settled in §5.4 (do not re-raise): the sums row's adaptive cell stays 0% with its footnote; the full-training-set
  adaptive cells keep theirs; never propose scaling a cell down to the pilot protocol (everything scales up later);
  one toolkit column counting any of the eight attacks; no comparison of the adaptive attack's 51% with the toolkit's
  rate; no derivation-cost or timing paragraph.
- Practitioners' likely objections, kept in view, not to be fixed now: the cost at 0.1% FPR (about ten points), the
  structural-only threat model (no packing, no code-level edits), pilot scale (10% subsamples, one seed, 50 malware).
- Explain plainly, no jargon. Claims say "on EMBER"; the detectors' accuracy cost is a measurement, never "small"; no
  timing of Proposition 1 against extraction; no effort claims. Exact numbers matter less than structure and argument.
- §4 is about 1,500 words against ~1,000; shortening §4 and §5 together comes after §5 is settled.
- Keep the session focused and economical: short notes, a recommendation rather than a menu.
- Commit to `main` in logical pieces; do not push. At the end of the session, re-read and update `docs/status.md` and
  write the next resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).

## Later (not this session unless the user brings it)

- After §5 is settled: §2's closing sentence and contribution 4 against the findings; shortening §4 and §5 together;
  the next full simulated review (PLAN.md, step 4) and the 4 MB-truncation brainstorm.
- The scale-up (seeds 0-2, full splits, more malware): the first thing once the write-up is finished (user).
