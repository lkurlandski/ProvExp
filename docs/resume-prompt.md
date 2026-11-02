# Resume: ProvExp (after 2026-11-02): triage the review, fill the synthetic cells, write the remaining sections

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`, one file per section; `make` and `make check` clean, 8 pages):
  - Section 3, the framework (`_d_framework.tex`), with its proofs in Appendix A (`_j_proofs.tex`).
  - Section 4, the EMBER instance (`_e_instances.tex`).
  - Section 5, the evaluation (`_f_evaluation.tex`). The mock's Tables 1-3 are Tables 5-7 of the PDF.
  - Every other section is an empty stub. Its comment states the planned content and word budget.
- **Planning documents:**
  - `docs/paper-mock.md`: thesis, contributions, outline with word budgets, tables.
  - `docs/status.md`, top block: what was written, the word counts, the synthetic cells, and the corrections made.
  - `PLAN.md`, "Order of work", steps 4-8: what comes next.
- **The review.** A harsh simulated review of the body is to be run in a separate fresh chat, with
  `docs/review-prompt.md`. Its output is `REVIEW-<date>.md` in the repo root.
- **Settled, do not reopen:**
  - The domain is adversarial examples in practical security tasks, and the framework is as agnostic as Pierazzi
    et al.'s. PE/EMBER is the main instance.
  - **Which breadth domain we use is unimportant and interchangeable.** Never make picking or vetting one the next
    priority.
  - Paper text goes straight into `.tex`. `docs/formalization.md` is frozen.

## The work, in order

1. **Triage.**
   - If `REVIEW-<date>.md` exists (the newest one; ignore `REVIEW.md` and `REVIEW-2026-10-21.md`, which are about the
     old direction), read it with the user.
   - Collect the user's comments on Sections 3-5.
   - Sort every point into one of: fix now in `.tex`; a new run; a framing decision for the user; reject (with the
     reason).
   - Do not apply sentence-level nits.
   - Record the decisions in `docs/status.md`.
2. **Apply the agreed fixes** to the written sections, keeping each part near its budget:
   - Section 3: problem 300, model 700, edits 300, side effects 600, directions 500, robustness 100.
   - Section 4: 1,000.
   - Section 5: 3,000.
   - Count with `texcount -sub=subsection <file>` (in `~/texlive/2026/bin/x86_64-linux`).
3. **Replace the synthetic cells.** Each is marked `% SYNTHETIC` in `_f_evaluation.tex`. State a hypothesis before
   each run.
   - *Add-section exactness:* the C1 engine's declared delta against re-extraction of our own byte-level edit, on the
     100 pilot files. Small; run it directly.
   - *Cost figures:* bookkeeping from the logs of runs 97/107 (derivation) and 78 (PV's attacks). Run directly.
   - *PV with 8 attacks under the fixed adaptive search:* the run 108 protocol. Also fills the extraction count after
     the fix. Estimate from the slowest case. If it is over about 10 minutes, write a `run/` script for the user.
   - *Adversarial-training row:* toolkit adversarial examples added to training, a GBDT retrained, and the Table 7
     columns. This is a `run/` script for the user (next number 117). Smoke-test it on a small slice first.
4. **Write the remaining sections**, each from the mock to its budget:
   - Background (800 words), Related work (700), Discussion (500).
   - Then the introduction (1,000) and the abstract, last.
   - Use the review's key-insight sentence and contributions draft if they hold up.
   - Figure 1 (one edit becoming an item delta, adjusted sums, and new features, against re-extraction) goes in
     Section 3.
5. **Later, on the user's decision:** a second toolkit (MAB-Malware) for the held-out column, leave-one-out PV,
   scale-up, and a breadth instance if the review says the paper needs one.

## Open decisions for the user

- The title. The working title is "Computing What Adversarial Edits Do to Features".
- Whether to add a conclusion section. The mock lists none.
- Where "Reading the Sums Directly" goes: it is a subsection of Section 4 that the mock doesn't list. It could move to
  Section 5.
- Section 4's budget, if a breadth instance is added. EMBER alone uses the whole 1,000 words.

## How to write

- Paper prose, not notes: continuous prose, no internal IDs, no revision history.
- Plain first: open each part with its question and an example.
- Present what works. Keep limitations light.
- PE details belong in Sections 4-5, never in the framework.
- `\synthetic{...}` for predicted values of deferred runs, with a `% SYNTHETIC` comment naming the run.
- Cross-references: `Theorem~\ref{...}` and `Corollary~\ref{...}`. Use `\Cref` for sections and tables.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not
  push.
