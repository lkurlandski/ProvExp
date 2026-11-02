# Resume: ProvExp (after 2026-11-02, session 2): tier 2 of the response to the review

## Where we are

- **The body is drafted in `.tex`** (`manuscript/`): Section 3 (framework), Section 4 (EMBER), Section 5 (evaluation),
  Appendix A. Tier 1's writing fixes are in (Proposition 1 + Theorem 1 as the main theorem, novelty paragraph, Table 1
  shrunk, research questions, Tables 5-7 updated, the detector paragraph rewritten). `make` and `make check` clean.
- **Tier 1 is done** (`docs/status.md`, top block), except P1 on the 2,000 files: `run/117_p1_closure.sh` (~35 min) is
  with the user. When its report arrives (`artifacts/experiments/catalogue_checks/2000-p1/report.json`, keys `closed`
  and `<op>.leaving_population`), read it, record the result in `run/117`'s header, and replace the blue
  `\synthetic{73,063}` in `_f_evaluation.tex` (the `% SYNTHETIC` comment names the run). If any edit leaves the
  population, that operation's declaration or the precondition changes (go/no-go of PLAN tier 1, item 1).
- **Open for the user:** (1) PV's hole: the paper says 44.4% "proved lowerable"; with pefile's residual warning
  features, which the table leaves free, it is 77.5% (one flag carries ~30% of PV's gain). Whether to say PV leans on
  features the table cannot vouch for. (2) The person-days for instrumentation (blue, "about three days").
- **Corrections recorded:** 252 of 288 toolkit outputs respect the derived table (not 284); prediction is not faster
  than re-extraction (no speed claim anywhere).

## The task: tier 2 (PLAN.md, "Tier 2")

Start with item 7: **item-level exactness for every item-stated operation** (add section, add imports, both gap
insertions, rename, both removals; R14). Build it once: it also scores item 8's adaptive search candidates. Go/no-go:
0 wrong on the 2,000 files (flagged allowed, reported). It replaces Table 5's blue add-section row and adds rows.
Then item 8 (the adaptive search over all twelve operations, on the routed 10%-store models of Table 7; go/no-go: at
least 24/47 on the unconstrained model), items 9-11. State the hypothesis before each run; runs over ~10 minutes go to
`run/118`+ for the user after a smoke test.

## Notes

- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Table 7's sums rows show adaptive 0%, but run 108's search ran on the full-store feature models; item 8 should run on
  the routed 10%-store models so every cell of a row comes from one model.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (the review's block).
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
