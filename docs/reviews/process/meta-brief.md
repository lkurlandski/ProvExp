# Your task: meta-review of a simulated program-committee review

Independent reviewers ({{REVIEWERS}}) have each reviewed the manuscript of this project as a submission to {{VENUE}},
seeing only the compiled PDF (commit {{COMMIT}}), a note from the authors (`{{OUT}}/note-to-reviewers.md`) and the
PDFs in `papers/`. Their reviews are `{{OUT}}/reviewer-<ID>.md`. Unlike them, you have the whole project. Your job is
to turn their reviews into what the authors can act on: which findings are true, which rest on a false premise, what
the reviewers missed, and what the full-scale run (the next experiments) must include.

## Read first

1. The reviews, all of them, before anything else.
2. `CLAUDE.md`, `PLAN.md`, `docs/status.md`, `docs/paper-mock.md`; `docs/README.md` indexes the other documents.
3. The manuscript: `manuscript/main.tex` and every file it `\input`s (`manuscript/main.pdf` for the layout; section,
   table and theorem numbers as compiled, in `manuscript/main.aux`). The source carries comments the reviewers did not
   see: `% SYNTHETIC` (a predicted value and the run that replaces it), `% PROTOCOL` (a pilot value on all files, to be
   re-run or recounted on the files below 4 MB), `% MEASURED`, and each stub's planned content.
4. The previous reviews: `docs/reviews/2026-11-02-body.md` (risk register R1-R16) and
   `docs/reviews/2026-11-04-strategy.md`. **Do not read** `docs/reviews/explanation-provenance/`: it reviews an
   abandoned direction.

Read the sources behind a number (`docs/evidence/`, the run scripts in `run/` with their headers, the code in `src/`)
when a finding depends on it.

## Ground rules

- **Read-only, except your output.** Write `{{OUT}}/meta-review.md` and add one line for this review to the table in
  `docs/reviews/README.md`. Change nothing else, and run no experiments (reading stored outputs with a short script is
  fine).
- **Keep the reviewers' finding IDs** (`A-W1`, `B-Q2`, ...) everywhere; never renumber them. Where a risk continues one
  of the 2026-11-02 register, keep its R-number; number new risks from R17 on.
- Cite locations precisely (section as compiled, and file + line). Separate what you **verified** from what you
  **infer**; if unsure, say what would resolve it.
- Explain plainly: lead with what a finding means in plain words, define terms, avoid dense shorthand.
- Report what would change a verdict. Sentence-level rewording is out of scope.
- Respect the settled points at the end of this prompt; do not reframe what a claim or statistic is for without
  flagging it as a proposal for the authors to decide.
- Portray cited work in its authors' own terms, checked against the PDFs in `papers/`.

## Your output: `{{OUT}}/meta-review.md`

1. **Executive summary** (five lines): the scores and the likely outcome; the top three risks; the single most
   important thing to fix.
2. **Meta-review:** a table of the reviewers' scores and confidences; where they agree and disagree, and why; the
   likely outcome and what would change it.
3. **The findings checked.** Every weakness and question of every reviewer, by its ID: *correct*, *partly correct*,
   *false premise* (the paper or the project says otherwise; give the evidence), *answered by the text* (the reviewer
   missed it: then the text may need to make it easier to find), *a preliminary-number artifact* (would disappear at
   full scale), or *settled* (out of scope by decision). One line of evidence each.
4. **The checklist** (below): for each item, which reviewer raised it unprompted and with which ID, or none; then your
   own judgement.
5. **What the reviewers missed:** anything a careful program committee would raise that none of them did.
6. **Rejection-risk register**, ranked by likelihood times severity:
   `| R# | Risk | Raised by | Likelihood (H/M/L) | Severity (fatal/major/minor) | Mitigation | Type | Effort |`.
   Mitigation: specific ("add X against Y and report Z"), within the settled points. Type: writing fix, reframing,
   analysis of existing data, new experiment, scope reduction. Effort: hours, days, weeks. Where only new work fixes a
   risk, say so.
7. **What the full-scale run must include:** the experiments and measurements, ordered by how much each moves the
   verdict, each with the risks it answers; and what it need not include.
8. **Writing actions** for the written sections, ordered the same way, and a few bullets per missing section
   (introduction, discussion, abstract, ethics, open science) on what it must establish and must not promise.

When done, reply with the file's path and the executive summary.
