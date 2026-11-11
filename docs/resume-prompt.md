# Resume: the user's review of §5.4 *What Robustness Costs*, then the rest of §5.1-5.2

Written at the end of session 36 (2026-11-11). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`, compiled with `make`
and checked with `make check` in `manuscript/`); §5 *Evaluation* is `manuscript/_f_evaluation.tex`.

**Read first:** `CLAUDE.md` (rules), `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; agreed, do not reopen). The `paper-prose` skill governs
all prose; the user's raw reactions are in `docs/writing-spec.md`.

§5's structure: lead; 5.1 *Setup* (run-in paragraphs Detectors, Attacks, Checking results); 5.2 *What Hand Analysis
Misses*; 5.3 *What Observed Attacks Miss*; 5.4 *What Robustness Costs* (label `sec:eval:detectors`, table
`tab:eval:detectors`, compiled as **Table 4**, "Detectors under the full threat model, and under additions only").
Always check `manuscript/main.aux` before naming a section, table or definition number, and give the title alongside.

## Where things stand

- **§5.4 was drafted in session 36** (commit 8fd8c9c, ~950 words against a ~900 budget) and **has not been reviewed**.
  The user ended the session exhausted and disappointed with the last two days of work (sessions 35-36, mostly §5.1's
  revisions and the §5.3 redesign). Keep the next session focused and economical: short notes, no menus of options,
  no re-raising settled points.
- §5.4's paragraphs, in order: an opening question (what does robustness to every edit in the threat model cost?);
  *The price* (monotone detector on the sums: 89.6% vs 93.5% TPR at 1% FPR, 74.7% vs 84.4% at 0.1%; features 87.2%,
  70.9%; the adaptive attack's largest score drop is exactly 0; toolkit evades the unconstrained detector on 55%, each
  monotone detector on one file outside the population); *Against hand-picked features* (Gimenez et al.'s expert set,
  sound only for additions, 29.1% vs the derived additions detector's 92.2%; the result practitioners can act on);
  *Where the cost lies* (import addition 2.1 points, the three header overwrites 1.4, other operations at most 0.4
  either way, sums recover 2.4; at 0.1% FPR dropping the two-sided features alone costs 5.2 points); *The width of the
  threat model* (additions only: 92.2%, but the header-field attack then evades 28%); *Beyond the guarantee* (GAMMA's
  layout-rebuilding injections move features the table holds fixed, yet evade no monotone detector on files in the
  population, 0/56 and 0/60, also at the GAMMA paper's budget); *Where the guarantee holds* (38 of 50 pilot malware,
  all but 1.5% of untruncated benign files; the one toolkit evasion is on a file outside it).
- Table 4 now has rows: unconstrained; unconstrained, full training set; monotone (features); monotone (sums); and an
  additions block (expert set; monotone sums). Columns: AUC, TPR at 1% and 0.1% FPR, Detected, Toolkit (a file
  counts as evaded if any of the eight toolkit attacks evades it), Adaptive. Every number is backed by a `% MEASURED`
  comment next to the text.
- Still in 5.4's part of the file but belonging to 5.3: the PV, ERDALT and adversarial-training paragraphs (marked
  `% 5.3 MATERIAL`) and their table rows (in a `% MOVED TO 5.3` comment). **Do not edit them**: another session
  (34) owns §5.3, `docs/section-5.3-design.md`, run 133 (`run/133_varied_observation.sh`) and the outputs under
  `artifacts/experiments/a_varied/`, `a_pv/best/`, `a1/advtrain/generated-seedperfile/`. Check `git log` first: that
  session may have committed changes to §5.3 or to the shared `docs/status.md` and `PLAN.md` (re-read those right
  before editing them, change only your own lines). Do not start jobs that compete with run 133 without asking.

## Settled with the user in session 36 (do not re-raise)

- The sums row's adaptive cell stays 0% with its footnote ("a simpler search that appends and adds sections"); the
  full-training-set adaptive cells stay with their footnote. Never propose scaling a cell *down* to the pilot
  protocol: everything scales up later.
- One toolkit column counting any of the eight attacks is fine. The memory `report-attacks-separately` is about
  stitching several *searches* into one adaptive number, nothing else.
- No comparison of the adaptive attack's 51% with the toolkit's rate; no "915 of 1,070 lowered" tightness number (it
  concerns two-sided features the detector drops, not the constraints that carry the cost); no derivation-cost or
  timing paragraph; the title is *What Robustness Costs*.
- Practitioners' likely objections, kept in view, not to be fixed now: the cost at 0.1% FPR (about ten points), the
  structural-only threat model (no packing, no code-level edits), and pilot scale (10% subsamples, one seed, 50
  malware), which matters most for 5.4 because its claim is a number.

## The task

1. **Ask the user for their review of §5.4** (version 8fd8c9c; they read the compiled `manuscript/main.pdf`). Do not
   revise it before they comment.
2. When comments arrive: answer their questions first, plainly; then one numbered plan with one recommendation per
   comment; apply after approval, `make` and `make check`, read the rendered text with `pdftotext` as they will, and
   show what changed per comment. Log their reactions raw in `docs/writing-spec.md` (append at the end of the
   reaction log). Revise in small blocks, a few paragraphs at a time.
3. Then, when the user chooses: their remaining comments on 5.1 (*Checking results*) and 5.2 (version 9b7d0ba).

## Later (not this session unless the user brings it)

- §5.3 after run 133 (session 34): its claim, the audit table that takes the PV, ERDALT and adversarial-training rows.
- After §5 is settled: §2's closing sentence and contribution 4 against the findings; shortening §4 and §5 together
  (§4.3 first); the next full simulated review (PLAN.md, step 4) and the 4 MB-truncation brainstorm.
- The scale-up (seeds 0-2, full splits, more malware): the first thing once the write-up is finished (user).

## Constraints

Explain plainly, no jargon (CLAUDE.md). Claims say "on EMBER"; the detectors' accuracy cost is a measurement, never
"small"; no timing of Proposition 1 against extraction; no effort claims. Exact numbers matter less than structure
and argument at this stage. Jobs over ~10 minutes go to the user as numbered `run/` scripts (133 is the highest
taken). Before committing code: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`. Commit to
`main` in logical pieces; do not push. At the end of the session, re-read and update `docs/status.md` and write the
next resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).
