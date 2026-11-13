# Resume: R18, the trial competitor (and whether iterated adversarial training joins the scale-up)

Written in session 58 (2026-11-13, rebuttal track), for the sessions that work on R18 of the 2026-11-12 simulated
review. Self-contained: everything needed to start is below or in the files it names. Two other tracks run in
parallel: R7 (`docs/resume-prompt.md`) and the rebuttal (`docs/resume-prompt-rebuttal.md`). Commit only the files you
changed (`git add <paths>`, never `git add -A`).

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1). From those come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. §5 is three findings: what hand analysis
misses (5.2), what defenses learned from observed attacks miss (5.3), what robustness costs (5.4). Check
`manuscript/main.aux` before naming a section, table or theorem number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md` (skim), `PLAN.md` decisions 6, 10 and 12, then
`docs/reviews/2026-11-12-body/rebuttal/triage.md`: R18's entry, `GROUP trial`, and the outcomes of the groups `trust`
and `erdalt` (they run first; if their drafts `rebuttal/trust.md` and `rebuttal/erdalt.md` exist, skim their opinion
lines). In the paper: §5's lead (`manuscript/_f_evaluation.tex`, the first paragraph) and §5.3, *What Observed Attacks
Miss* (from `\subsection{What Observed Attacks Miss}` to `\subsection{What Robustness Costs}`). From the meta-review
(`docs/reviews/2026-11-12-body/meta-review.md`): row R18 of the register (§6), C-W3's verdict, and point 9, *The
problem-space defense*. Its [verified] facts are trusted; its judgement is not (memory `distrust-simulated-reviews`).

## The issue, plainly

The paper names three ways a practitioner learns what edits do to the features: **trial** (apply edits, extract,
look), **reading the extractor** (hand analysis), and **observed attacks**. §5.2 and §5.3 measure what the last two
miss, and the lead uses trial as the ground truth ("trial is exact but answers only for the edits it tries"). The
reviewers' point (C-W3, D-W6, B-W4 (e); all four in some form): §5 never builds the competitor a practitioner who knows
the twelve operations would actually use, **a systematic trial over those operations**. If that competitor gives the
same table as our derivation and a monotone detector built on it holds, then what the computation adds over trial is
the guarantee (a proof over the population, not a sample) and finding the holes before any attack; the paper's
contrast with trial would need to say exactly that. I (session 58) would test this even without a reviewer: it is the
realistic-alternative check CLAUDE.md asks of every application (memory `check-baseline-realism`).

One part of C-W3 restates our finding as a flaw ("the learned defenses get less information, so the outcome is built
in"): that a defense learned from the attacks at hand cannot see the operations they lacked *is* §5.3's finding, and a
defender learns which operation to add only after an attacker used it. Do not reopen that part.

## What already exists (no new runs needed for step 1)

- `artifacts/experiments/a_varied/coverage/features.csv` (from `scripts/a_coverage.py`, run 133 step 3, on the 3,183 outputs of §5.3):
  one row per feature the derived table marks lowerable (1,070), with the operations that can lower it, `witnessed_by`
  (which of our own byte-level edits lowered it on a population file: the 73,063 re-extracted edits of
  `catalogue_checks.py`), and per source which toolkit attacks lowered it. **Trial table = witnessed by our edits ∪
  lowered by a toolkit output.**
- The meta-review's count [verified]: of the 142 lowerable features no toolkit output lowered, 75 (88 in all) are
  parser warnings, which the instance does not model and marks "both" by fiat; about 20 are witnessed by our edits;
  about 48 modeled ones are unwitnessed, 46 of them counts of strings matching a pattern. Of the eight hand-table
  errors (Table 3), six would show up under random-content trial; the two Rich-header errors need a forged Rich block.
- Monotone detectors: `scripts/train_classic.py --monotone <name TAB sign file>`; direction tables from
  `scripts/a_directions.py`; the derived detectors' models `seed-0-s10-mfull-{feat,sums}-loose` (R7's widened
  population; run 140's header has the training commands and runtimes). Attacks: `scripts/a1_adaptive.py` (beam,
  `--score real`), toolkit via `a1_evaluate.py`, MAB-Malware via `scripts/mab_attack.py` (run 139).

## The work, in order

**0. Mock the result first** (memory `mock-the-result-first`). Before any code: the row(s) the trial competitor adds to
a §5 table, the operator behind each column, and which sentence of §5's lead or §5.3 moves under each outcome. State
the hypothesis in a sentence or two. Mine, to check, not to adopt: the trial table matches the derived table on all
but ~50 modeled features (the string-pattern counts, the Rich header), never marks lowerable a feature the derived
table marks fixed (that would be a soundness error, not a difference), and its monotone detector holds against the
adaptive attack because those ~50 features carry little gain; so the outcome is the reframing, not a new hole.

**1. The trial table, from stored data** (minutes). Build it from `features.csv`; compare with the derived table on
modeled features only (warnings apart, as R12 asks). Report: how many differ, which groups, and their split gain in the
derived detector. **Fairness** (memory `fair-baselines-over-faithful-copies`): give trial its strongest fair form,
i.e. every operation with the content variety a practitioner would use (random bytes and benign-donor content, several
seeds), not one fixed content. If the stored edits used one content per operation, say so and estimate what more
content would add before building anything. Also ask the opposite question: for the unwitnessed features, can any
edit of the threat model lower them at all? If not, the derived table over-approximates there, and the trial detector
would be the *better* detector on them; report that plainly.

**2. A monotone detector on the trial table, attacked** (pilot, one seed). Train it like the derived detectors (same
training set, same population, same threshold protocol), then the adaptive beam with `--score real` and MAB-Malware on
the pilot. Training takes about a minute per model (run 140's header); the attacks likely exceed ~10 minutes: smoke-test
on a small slice, then a numbered `run/` script for the user (check `ls run/` for the next free number right before writing it; the R7 track also adds
scripts; `NUM_WORKERS="${NUM_WORKERS:-16}"`, one argument per line, an `echo` naming each step's log). Go/no-go, read
after the run (memory `interpret-after-run`): an evasion through a feature trial missed means §5 gains its sharpest
evidence for computation over trial; no evasion and detection within noise of the derived detector means the
contrast with trial is reframed around the guarantee. Either outcome is a result; neither is "weak".

**3. Iterated adversarial training: in or out of the scale-up.** The meta-review proposes revisiting decision 6:
adversarial training with the adaptive attack over all twelve operations in the loop, on training malware, at least
two rounds, tested with a held-out attack (MAB-Malware, or a held-out operation). Its expected outcome (it resists the
attack in its loop, falls to a held-out one) would support §5.3, but it is days of compute. Do not run it here:
estimate its cost from the stored runs (runs 122, 125, 130), check what Lucas et al. 2023 and Tsingenopoulos et al.
2024 (`papers/`) did, and bring the user one recommendation, framed by step 2's outcome.

**4. Record.** The user decides the reading of steps 1-2 and the step-3 question. Then: R18's Decision cell and a
`- [ ]` action line in `triage.md`; the scale-up items into PLAN.md's next step 3; one line in `docs/status.md`'s log.

## Constraints

- **No manuscript edits** in these sessions: §5's text changes after the scale-up, with the final numbers. The R7 track
  owns §4.3.1, §4.4, §5.1's setup, §5.4, Table 5 and `catalogue.py`, `a_directions.py`, `a1_adaptive.py`,
  `catalogue_checks.py`: read them, do not edit them; if R18 needs a change there, propose it and stop.
- Pilot scale, one seed. Jobs over ~10 minutes (from the slowest case) go to the user as `run/` scripts.
- §5 is findings, not a defense paper (memory `findings-not-defense-paper`); no timing or effort claims (the cost of
  trial is the edits and extractions it needs, never seconds or person-days); hypothesis before every run, failed
  checks reported as such.
- Explain plainly: lead with what is computed, what it is compared with, why it matters.
