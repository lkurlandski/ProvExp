# Resume: discussing the full simulated review

Written at the end of session 47 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors no edit in the threat
model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper is written straight
into `manuscript/*.tex`; check `manuscript/main.aux` before naming a number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (next steps 2-3), and the runbook
`docs/reviews/review-prompt.md`.

## Where things stand

- Session 46 decided the population (files below 4 MB in every split; PLAN.md decision 8 (iv)). Most numbers in §5 and
  Appendix D are still pilot values on all files (`% PROTOCOL` comments); one blue value (5.4, 89%).
- Session 47 designed the review with the user and wrote it as a reusable procedure in `docs/reviews/process/`: four
  independent reviewers (A formal methods / PL, B adversarial malware, C robust and certified ML, D generalist
  systems security), each a headless `claude -p` run from a scratch folder outside the repository, seeing only the
  compiled PDF, `note-to-reviewers.md` and a copy of `papers/` (plus web search); then a meta-reviewer inside the
  repository that checks every finding's premise against the project, works through `checklist.md` (which the
  reviewers never see), and writes the risk register and what the scale-up must include. Defaults in `config.sh`: CCS,
  Opus 5.5 (`claude-opus-5-5`), reviewers at high effort, meta-reviewer at max. A dry run and a one-reviewer Haiku smoke
  test passed.

## The task

The user ran `docs/reviews/process/run_review.sh` themselves (in tmux, after session 47), so the review's output is
already there: `docs/reviews/<TAG>/` (`TAG` defaults to `<date>-body`; find the newest folder in `docs/reviews/`), with
`meta-review.md`, `reviewer-{A,B,C,D}.md`, `run-config.txt` (commit, models, effort), the logs, and the note and
checklist the run used.

1. **Check the run first:** every reviewer wrote a review (no `reviewer-<ID>.md` missing; the logs end cleanly),
   `meta-review.md` exists and covers its eight sections, and `docs/reviews/README.md` has the new line. If something
   failed, tell the user and give the command to redo only that part (runbook, last paragraph: `REVIEWERS=<ID>
   STEPS=reviewers TAG=<same tag>`, then `STEPS=meta TAG=<same tag>`); do not rerun it yourself unless asked.
2. **Read** the meta-review and the four reviews in full, and spot-check the meta-reviewer's verdicts on the findings
   that matter most (a premise marked correct or false that decides a risk) against the manuscript and sources.
3. **Discuss** them with the user, following memory `review-comments-workflow`: start with the executive summary in
   plain words, answer the user's questions first, keep the reviewers' IDs (`A-W1`, ...) and the R-numbers, one
   recommendation per item, small passes with approved items first. The output decides what the scale-up (PLAN.md,
   next step 3) includes; record what is agreed in PLAN.md.
4. **Adjust the procedure** if the run shows a flaw (knobs in `config.sh`; prompts in `process/`), and note what
   changed in the runbook.

## Constraints and settled points

- Explain plainly, no jargon; a recommendation rather than a menu.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for.
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB.
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
