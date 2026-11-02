# Resume: ProvExp (after 2026-11-02, framework section written)

## Where we are

- **The paper is planned** in `docs/paper-mock.md` (thesis, four contributions, outline with word budgets, Tables 1-4;
  EMBER cells measured at pilot scale, CTU-13 cells missing).
- **Section 3 is written** in `manuscript/_d_framework.tex` ("Computing What Edits Do to Features", 2,568 words against
  2,500), with its proofs in Appendix A (`manuscript/_j_proofs.tex`). The old manuscript is deleted (in git history);
  every other section is an empty stub whose comment states its content and word budget (one file per section).
- **Sections 4 and 5 are written** (`_e_instances.tex`, EMBER only, 1,038/1,000 words; `_f_evaluation.tex`, ~1,900/3,000,
  Tables 6-8 of the PDF = the mock's Tables 1-3). Synthetic cells (blue) and the runs that replace them: see
  `docs/status.md`, top block.
- `docs/formalization.md` is **frozen** (reference and appendix source; factual corrections only).
- **Settled, do not reopen:** the domain is adversarial examples in practical security tasks; the framework is as
  agnostic as Pierazzi et al.'s; PE malware is the inspiration and main instance; paper text goes straight into
  `.tex`.

## Next

1. **The user reads Section 3.** Apply their comments in `.tex`; keep each part near its budget (problem 300, model
   700, edits 300, side effects 600, directions 500, robustness 100). Rebuild with `make` and `make check` in
   `manuscript/`; count with `texcount -sub=subsection _d_framework.tex` (in `~/texlive/2026/bin/x86_64-linux`).
2. **PLAN step 4:** a harsh simulated tier-1 review of the mock and the framework section; decision point with the user
   (breadth instances, a possible second application).
3. **A breadth instance** (any domain; which one is unimportant, user 2026-11-02): late and interchangeable.
4. Then A's gaps (adversarial-training row, MAB-Malware, cost column, scale on the user's decision).

## Open decisions for the user

- Drebin as an instance (default: examples only).
- The coupling row (default: out).
- Figure 1 of the mock (an edit becomes an item delta, adjusted sums, new features, against re-extraction) is not
  drawn yet; it belongs in Section 3 and would cost little prose.

## Notes

- Citations already in `main.bib` for later sections: demontis2019yes, chen2021learning, engelen2021troubleshooting,
  chernikova2022fence, simonetto2022unified (Background, Instances, Related work).
- Theorem references use `Theorem~\ref{...}` / `Corollary~\ref{...}`: cleveref has no name for the custom counters.
- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
