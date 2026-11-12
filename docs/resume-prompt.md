# Resume: a holistic assessment of the research, and a plan for what comes next

Written at the end of session 44 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance; the framework is format-free and meant to extend to other security domains later. The paper
is written straight into `manuscript/*.tex` (ACM `sigconf`, CCS format; `make` and `make check` in `manuscript/`).
Check `manuscript/main.aux` before naming a section, table or definition number, and give the title alongside
(`docs/README.md` has the numbering).

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (the thesis, decisions 1-10, "Next steps" with the new step 0).

## Why this session

At the end of session 44, Claude listed PLAN.md step 2's remaining items as next ((0) visual emphasis for §5's
questions and answers, (b) shortening §4 and §5, (c) aligning §2's closing and contribution 4 with §5). The user:
"I'm not confident that the three 'up-next' items are actually the ones we should pursue next. Let's prepare for a new
session whose first order of business is a holistic assessment of our research progress and planning stage for the
next steps."

Two weeks of sessions (34-44) went into §4-5's prose and tables. The question now is whether the research as a whole
is where it should be, and what most improves it from here, not which polishing item comes next.

## The task

1. **Assess, honestly and plainly.** Before saying anything, read what is needed to judge the whole: `PLAN.md`,
   `docs/paper-mock.md` (contributions, outline, word budgets), the compiled paper (`manuscript/main.pdf`, 16 pages;
   §1, §7, the abstract, ethics and open science are still empty), the latest simulated reviews
   (`docs/reviews/README.md`: `2026-11-04-strategy.md`, the risk register R1-R16 in `2026-11-02-body.md`), and
   `docs/graveyard.md` before suggesting any new direction. Judge novelty harshly (CLAUDE.md). Questions worth
   answering:
   - Does the evidence carry the thesis? Each of §5's three findings (5.2 *What Hand Analysis Misses*, 5.3 *What
     Observed Attacks Miss*, 5.4 *What Robustness Costs*): how strong it is, what a skeptical CCS reviewer attacks
     first, and what only the scale-up can settle (pilot: 10% subsamples, one seed, 50 malware attacked; 5.3's PV is
     judged on 9 files).
   - Known weaknesses on record: §2 promises that §5 "uses them to attack malware detectors and to build robust
     ones", but the attack is only an instrument in §5 (PLAN.md step 2 (c), "a known weakness, not fixable now");
     the mock's contribution 4 is stale; the open risks of the 2026-11-02 register (R4, R5, R6, R9, R11, R15, R16);
     the attack-strength concern of the 2026-11-04 review; decision 6's revisit (is a problem-space defense
     expected?); one domain only.
   - The balance of effort: framework §3 (~3,700 words), §4 (~1,600 against ~1,000), §5 (~3,500), the empty
     introduction and discussion, and the research items not yet done (the scale-up, the 4 MB truncation, other
     domains).
2. **Then plan with the user.** Give the assessment first in a short, plain form, then a recommended order of the next
   steps with one line of reason each. Keep it a recommendation, not a menu. The candidates on record are PLAN.md
   steps 2 ((0), (b), (c)) and 4-8: the 4 MB-truncation brainstorm, the next full simulated review, the scale-up (the
   user, session 44: "we need to scale these experiments up shortly"), other domains, the introduction last. New
   candidates are welcome when the assessment shows a need, but check `docs/graveyard.md` and the settled points
   first. Let the user decide; do not start work on any step in this session unless the user asks.
3. **Record the outcome.** Rewrite PLAN.md's "Where the paper stands" (still dated session 39) and "Next steps" to the
   agreed plan; update `docs/status.md`; log the user's reactions raw at the end of `docs/writing-spec.md` if they
   concern writing, otherwise in the status log.

## Where things stand (end of session 44)

- **§2-3 (the framework):** rewritten in the week of 2026-11-02; the user is reasonably satisfied. Pending: the user's
  holistic read of Sound Directions.
- **§4 (Instantiating the Framework):** drafted in the template structure, reviewed twice by Claude (sessions 38, 40);
  in good shape; ~1,600 words against ~1,000.
- **§5 (Evaluation):** three findings (PLAN.md decision 10; agreed, do not reopen), fully drafted, reviewed per
  subsection (session 41b) and as a whole (session 42). Tables remade in session 43 (Table 3, the hand table's
  errors; Table 5, the detectors) and session 44 (new Table 4, *Defenses learned from the outputs of the toolkit
  attacks*, d87603f). The user has not read §5 end to end.
- **§6 (Related Work):** drafted. **§1, §7, abstract, ethics, open science:** empty (introduction last, by decision).
- **Experiments:** complete at pilot scale. The scale-up (seeds 0-2, full splits, more malware) is designed in outline
  only (PLAN.md step 6): the adaptive budget (~3,000 CPU-h at 5,000 candidates on 2,000 files), ERDALT's stopping
  criterion, one training set and one attack protocol for every detector (Tables 4 and 5 now show two different
  unconstrained detectors: the full training set, 25/49, and the 10% subsample, 26/47), Table 5's two halves made
  consistent (the same detectors in both). Heavy runs can go to a second, 20-core server (`run/sync_artifacts.sh`).
- `manuscript/tmp-tables.tex` (untracked) holds session 44's two versions of the 5.3 table; scratch only.

## Open items (fix when the affected text is touched)

- 5.1 says the computed features match on "73,063 edits" (run 107's direction check; the exactness counts are
  Appendix D's, 62,604 + run 118's 34,965); fix at the scale-up unless the user wants it now.
- 5.2 says our hand table was written "before the derivation existed"; check the history before rewording.
- Table 5's toolkit cells come from the older fixed-seed runs (`a1/toolkit-v2`), Table 4's from run 133's seed per
  file; nothing about this in the paper (no protocol hygiene); one protocol at the scale-up.

## Constraints and settled points

- Explain plainly, no jargon; short notes; a recommendation rather than a menu; keep the session focused on the
  assessment and the plan.
- No deadline or conference-cycle talk. Do not reopen settled decisions (PLAN.md "Settled decisions", decision 10, the
  domain framing); ask before reframing what a claim or statistic is for.
- Claims say "on EMBER"; the detectors' cost is a measurement, never "small"; no state-of-the-art defense claim and no
  defense-paper framing; no "pilot" in the paper; no timing of Proposition 1 against extraction; no effort claims; no
  random-seed or protocol-hygiene details in the paper.
- Long jobs (over ~10 minutes) go to the user as `run/` scripts; this session needs none.
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
