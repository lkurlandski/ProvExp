# Resume: a holistic review of §4 *Instantiating the Framework*, then of §5 *Evaluation*

Written at the end of session 37 (2026-11-11). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`, compiled with `make`
and checked with `make check` in `manuscript/`): §4 is `manuscript/_e_instances.tex` (4.1 *EMBER and PE Files*, 4.2
*EMBER as a Sum-then-Readout Extractor*, 4.3 *Threat Model*, 4.4 *Population*; details in Appendix D *The EMBER
Instance*, `_j2_ember.tex`), §5 is `manuscript/_f_evaluation.tex`. Always check `manuscript/main.aux` before naming a
section, table or definition number, and give the title alongside.

**Read first:** `CLAUDE.md` (rules), `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; agreed, do not reopen). The `paper-prose` skill governs
any prose you write; the user's raw reactions are in `docs/writing-spec.md`.

## What happened in session 37

The user asked Claude to review §5.4 *What Robustness Costs* with the skill `anthropic-skills:humanistic-paper-review`
instead of reading it themselves. **The user agreed with the headline findings (structure: paragraphs that relied on
something explained later; a paragraph that buried its finding; numbers whose units were unclear) and less with the
small ones (the "recurring patterns" and "term ledger issues" sections).** The fixes were applied in three commits
(c49f654, 9113acb, 23ab085); §5.4 now runs: price, where the guarantee holds, where the cost lies, width of the threat
model, against hand-picked features, beyond the guarantee. The user has not read the revised §5.4 yet.

The user then asked for a holistic review of all of §5, and wondered whether to review §4 first. Claude recommended
§4 first:
- §5 rests on §4's terms (the toolkit attacks, the catalogue and its operations, the threat model, the population, the
  re-encodings over sums); a §5 review would keep flagging gaps that are §4's to fix.
- §4 is stable (blocks accepted, no experiment pending), while §5.3 still waits on run 133.
- §4 is over budget (~1,540 words against ~1,000; shortening deferred, §4.3 first), and the review's "delete" test
  (sentences the reader would not miss) serves that shortening.

## The task

1. **Confirm the order with the user in one line** (§4 first, as recommended, unless they say otherwise).
2. **Review §4 with `anthropic-skills:humanistic-paper-review`**, including Appendix D only where §4 relies on it.
   Read the source and the rendered PDF (`pdftotext`). Calibrate to session 37: lead with section- and
   paragraph-level findings (order, forward references, buried claims, unclear numbers, a paragraph the reader would
   not miss); keep sentence-level patterns and the term ledger to a line or two, or leave them out. Note words that
   could be cut, since §4 is to be shortened. Do not edit before the user responds.
3. When the user responds: answer their questions first, plainly; one numbered plan with one recommendation per
   finding they accept; apply after approval, a few paragraphs at a time; `make`, `make check`, read the rendered text;
   show old and new text per finding; log their reactions raw at the end of `docs/writing-spec.md`.
4. **Then §5**, the same way, over the whole section (lead, 5.1-5.4), skipping the text marked `% 5.3 MATERIAL` and
   anything inside §5.3 *What Observed Attacks Miss* that session 34 owns (below). The user's own pending comments on
   5.1's *Checking results* paragraph and on 5.2 *What Hand Analysis Misses* (version 9b7d0ba) can join this review.

## Constraints and settled points

- **§5.3 belongs to session 34:** `docs/section-5.3-design.md`, run 133 (`run/133_varied_observation.sh`), the
  outputs under `artifacts/experiments/a_varied/`, `a_pv/best/`, `a1/advtrain/generated-seedperfile/`, the paragraphs
  marked `% 5.3 MATERIAL` and the table rows in the `% MOVED TO 5.3` comment. Do not edit them. Check `git log`
  first: that session may have committed changes to §5.3, `docs/status.md` or `PLAN.md` (re-read those right before
  editing them, change only your own lines). Do not start jobs that compete with run 133 without asking.
- Settled in §5.4 (do not re-raise): the sums row's adaptive cell stays 0% with its footnote; the full-training-set
  adaptive cells keep theirs; never propose scaling a cell down to the pilot protocol (everything scales up later);
  one toolkit column counting any of the eight attacks; no comparison of the adaptive attack's 51% with the toolkit's
  rate; no derivation-cost or timing paragraph.
- Practitioners' likely objections, kept in view, not to be fixed now: the cost at 0.1% FPR (about ten points), the
  structural-only threat model (no packing, no code-level edits), pilot scale (10% subsamples, one seed, 50 malware).
- Explain plainly, no jargon. Claims say "on EMBER"; the detectors' accuracy cost is a measurement, never "small"; no
  timing of Proposition 1 against extraction; no effort claims. Exact numbers matter less than structure and argument.
- Keep the session focused and economical: short notes, a recommendation rather than a menu, no re-raising settled
  points.
- Commit to `main` in logical pieces; do not push. At the end of the session, re-read and update `docs/status.md` and
  write the next resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).

## Later (not this session unless the user brings it)

- §5.3 after run 133 (session 34): its claim, the audit table that takes the PV, ERDALT and adversarial-training rows.
- After §5 is settled: §2's closing sentence and contribution 4 against the findings; shortening §4 and §5 together;
  the next full simulated review (PLAN.md, step 4) and the 4 MB-truncation brainstorm.
- The scale-up (seeds 0-2, full splits, more malware): the first thing once the write-up is finished (user).
