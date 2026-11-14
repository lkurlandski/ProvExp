# The simulated review: how to run it

A reusable procedure for a full simulated program-committee review of the manuscript (designed with the user in
session 47, 2026-11-12). The prompt of the 2026-11-02 review, which one agent ran as three reviews, is archived in
`docs/archive/review-prompt-2026-11-02.md`.

## The design, and why

- **Independent reviewers, each a separate agent with no project context.** They run headless (`claude -p`) from a
  folder outside the repository, so they see no `CLAUDE.md`, memory or docs: only the compiled PDF, a note from the
  authors, and a copy of `papers/` (their prior knowledge), plus web search. *Why:* in 2026-11-02 one agent wrote all
  three reviews, which shared one reading and its blind spots; a real reviewer sees only the PDF.
- **Each reviewer has one area of expertise, no assigned stance** ("be hostile" makes an agent invent problems).
  Currently four: A formal methods / PL, B adversarial malware, C robust and certified ML (new: §5.3-5.4 argue against
  learned defenses), D generalist systems security.
- **The reviewers never see our list of worries.** It goes to a **meta-reviewer** with full project access, run after
  them, which checks every finding against the code, docs and papers (the 2026-11-02 triage found false premises
  only afterwards), works through the checklist (raised unprompted, by whom), writes the risk register, and says what
  the full-scale run must include. *Why:* reviewers given the checklist would confirm it; what matters is what a
  stranger finds unprompted.
- **Then a rebuttal: a triage, and drafts only where needed** (session 57, 2026-11-13; redesigned the same day). One
  agent reads the register, the reviews and PLAN.md once and gives every item a verdict: decided, dismiss (restates a
  finding, attacks a claim we do not make, reopens a settled decision), cheap fix, or investigate (with the two or
  three questions that decide it). The user takes the decisions on that table; only the groups to investigate get a
  drafting agent, which reads a dossier of its items (cut out by `dossier.py`) and checks only the deciding questions.
  The meta-review's [verified] facts are trusted; its judgement is not. *Why:* the meta-review leans toward accepting
  criticism, so each item needs the user's judgement; the first design (one full agent per item, every fact re-checked)
  cost about $2-3 of tokens per item and ran out of the user's session limit after four of 21.
- **The PDF, not the `.tex`:** the source comments (`% PROTOCOL`, `% SYNTHETIC`, stub plans) would steer the reviewers.
  What they need to know about the draft's state is in the note to reviewers, which names every placeholder value
  (colour may not survive how an agent reads a PDF).
- **No drafts** of the introduction or contributions (the introduction comes last).

## Files

All in `docs/reviews/process/`:

| File | What it holds | Change it |
|---|---|---|
| `config.sh` | the knobs: run tag, venue and score scale, reviewer IDs, models and effort (all and per reviewer), meta-reviewer model and effort, web search on/off, budget cap, scratch folder, steps, dry run | per run, or by environment variable |
| `run_review.sh` | builds the PDF, runs the reviewers in parallel, then the meta-reviewer; records the configuration and commit | rarely |
| `reviewer-brief.md` | the shared brief every reviewer gets: what they have, how to judge, the review's sections | when the review form changes |
| `reviewers/<ID>-<name>.md` | one reviewer's expertise; the ID is the file's first letter(s) | to add, drop or change a reviewer |
| `note-to-reviewers.md` | the authors' note: what the paper claims (while the introduction is empty), what is missing on purpose, how to treat preliminary numbers, **every blue value by name** | **before every run**, to match the manuscript |
| `checklist.md` | the questions only the meta-reviewer answers, and the settled points | **before every run** |
| `meta-brief.md` | the meta-reviewer's task and output form | when the output form changes |
| `triage-brief.md` | the triage agent's task: a verdict per register item, the groups to investigate with their deciding questions, the form of `rebuttal/triage.md` | when the procedure of `docs/reviews/rebuttal-prompt.md` changes |
| `rebuttal-brief.md` | one drafting agent's task: one group of items, its deciding questions, the form of its draft | likewise |
| `dossier.py` | cuts out of a review folder what a group of items rests on (register rows, §3 verdicts, §5 entries, cited reviewer passages) | when the review's output form changes |
| `run_rebuttal.sh` | the rebuttal: the triage (no `REBUTTAL_GROUPS`), or the drafts of the chosen groups, `REBUTTAL_PARALLEL` at a time | rarely |

Placeholders in the prompt files (`{{VENUE}}`, `{{SCALE}}`, `{{TAG}}`, `{{OUT}}`, `{{WORK}}`, `{{COMMIT}}`,
`{{REVIEWERS}}`, and `{{ID}}`, the reviewer's own ID) are filled from `config.sh` by `run_review.sh`.

## Knobs (defaults in `config.sh`)

| Knob | Default | Meaning |
|---|---|---|
| `TAG` | `<today>-body` | output folder `docs/reviews/<TAG>/` |
| `VENUE`, `SCALE` | ACM CCS; Reject / Weak reject / Weak accept / Accept | the simulated venue |
| `REVIEWERS` | `A B C D` | which persona files run |
| `REVIEWER_MODEL`, `REVIEWER_EFFORT` | `claude-opus-5-5`, `high` | every reviewer; `MODEL_<ID>`, `EFFORT_<ID>` override one (e.g. `MODEL_C=claude-fable-5-2`) |
| `META_MODEL`, `META_EFFORT` | `claude-opus-5-5`, `xhigh` | the meta-reviewer (`max` used up the user's session limit in the first run, 2026-11-12) |
| `REVIEWER_WEB` | `1` | reviewers may search the web |
| `MAX_BUDGET_USD` | empty | optional cap per agent |
| `REBUTTAL` | `1` | run the rebuttal triage after the meta-review (`0`: stop after it) |
| `REBUTTAL_MODEL`, `TRIAGE_EFFORT`, `REBUTTAL_EFFORT` | `claude-opus-5-5`, `high`, `high` | the triage agent and the drafting agents |
| `REBUTTAL_SKIP` | empty | items decided before the run (e.g. `"R7 R1"`), given to the triage as decided |
| `REBUTTAL_GROUPS` | empty | the groups of `triage.md` to draft (e.g. `"trust baselines"`); empty runs the triage |
| `REBUTTAL_PARALLEL` | `1` | drafting agents at a time (parallel agents exhaust the session limit faster) |
| `STEPS` | `all` | `reviewers` stops after the reviews; `meta` redoes the meta-review (then the triage); `rebuttal` runs only the rebuttal step |
| `DRY_RUN` | `0` | `1` prints the composed prompts and commands only, and writes nothing |

## Running it

1. **Prepare** (Claude, with the user): update `note-to-reviewers.md` against the manuscript (the claim, the empty
   sections, every `\synthetic{...}` value: `grep -n 'synthetic{' manuscript/_*.tex`) and `checklist.md` (the open risks
   and the questions of the moment, the settled points from PLAN.md). Commit, so the review names a commit.
2. **Check:** `DRY_RUN=1 docs/reviews/process/run_review.sh` and read the composed prompts.
3. **Run** from the repository root: `docs/reviews/process/run_review.sh` (Claude starts it in the background; it
   needs no CPU, only time: the reviewers take tens of minutes in parallel, then the meta-reviewer). Logs:
   `<WORK_ROOT>/<TAG>/reviewer-<ID>.log` while running, copied to `docs/reviews/<TAG>/` at the end, and
   `docs/reviews/<TAG>/meta.log`.
4. **Output** in `docs/reviews/<TAG>/`: `reviewer-<ID>.md`, `meta-review.md`, the PDF reviewed, the note and checklist
   used, `run-config.txt` (commit, models, effort). The meta-reviewer adds a line to `docs/reviews/README.md`.
5. **Rebuttal triage** (automatic unless `REBUTTAL=0`): `docs/reviews/<TAG>/rebuttal/triage.md`, a verdict per
   register item and the groups to investigate; log `triage.log`. Rerun it alone with `STEPS=rebuttal TAG=<tag>`
   (an existing triage is kept; delete it to triage again).
6. **Afterwards** (`docs/reviews/rebuttal-prompt.md`): the user takes the decisions on the triage table, most
   significant first; the groups they choose to investigate are drafted with
   `REBUTTAL_GROUPS="<names>" STEPS=rebuttal TAG=<tag>` (`rebuttal/<group>.md`) and decided in a later session. The
   decisions decide what the full-scale run includes.

If a reviewer fails (no `review-<ID>.md`), rerun only it: `REVIEWERS=C STEPS=reviewers TAG=<same tag> ...`, then
`STEPS=meta TAG=<same tag> ...`. A meta-only rerun appends its commit and date to `run-config.txt` instead of
overwriting the reviewers' (fixed in session 48, after the first run's record lost the reviewers' commit).

**What the first run (2026-11-12) showed:** the procedure worked end to end; the meta-reviewer at max effort used up the
session limit and was resumed at xhigh (now the default). Its most valuable output was what only full access can find
(a premise checked in the code: one field write leaves the population), so keep the meta-reviewer's code access.

**Stopping and resuming the meta-reviewer** (e.g. to change its effort or after a usage limit): stop it (Ctrl-C in its
pane), then `docs/reviews/process/resume_meta.sh`. It finds the newest meta-review session, resumes it with
`--resume` (everything it has read stays in its context) at `META_MODEL` / `META_EFFORT`, and logs to
`docs/reviews/<TAG>/meta-resume.log`. On a later day, pass the run's tag (`TAG=2026-11-12-body`); `SESSION=<id>`
picks a session by hand.
