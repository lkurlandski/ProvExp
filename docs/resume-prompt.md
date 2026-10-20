# Resume: ProvExp (2026-10-21) — read run 74, then a fresh critical review

Read `CLAUDE.md`, then `docs/status.md` (top block, "2026-10-20 (end of afternoon session)"). Skim
`manuscript/main.pdf` Sections 5-6. Explain in plain language; ask before changing what a claim is for. Follow the
memories `consistency-and-simplicity`, `paper-writing-style`, `check-baseline-realism`, and `mock-the-result-first`.

## Where things stand

- The body is filled except the deferred runs (Sections 5, 6.1, 6.2, Appendix C; runs 66-73). 6.1's claim: before any
  edit, the GBDT's pullback on the fields a MalConv-guided attacker edits predicts the GBDT's drop (Table 2: Spearman
  0.48 vs. 0.21 windows vs. 0.03 bytes; 500 files, run 72).
- Remaining blue: 6.2's retrained-MalConv row and sentence (deferred), the discussion's Android sentence (W7).
- Feature extraction is ~2x faster (`features.byte_counter`, exact; `docs/design.md`, "Speed").
- Deferred by the user, do not propose: MalConv retraining (and a stronger attacker on it), the scale-up, more seeds.
  Evaluated and dropped on 2026-10-20: a named-feature TreeSHAP baseline for Table 2 (presumes a hand-built map), a
  0.1% FPR column, sentence-level rewordings.

## First: read run 74

Run 74 (started by the user on 2026-10-20, ~5 h): KernelSHAP over 4,096 windows on the GBDT, reusing run 66.
- Check it ran clean: `tail -n 40 artifacts/logs/pb1-shared-ks4096-seed0.log` (statuses, failed files, timeouts) and
  `artifacts/reports/pb1_tables-shared-ks4096.md`.
- Hypothesis: KernelSHAP@4096 removes more than KernelSHAP@1024 (6.31) and adaptive@4096 (5.96) but stays below the
  byte-level pullback (8.03); pushed forward, it continues KernelSHAP's rise (0.68 / 0.75 / 0.83 at 64 / 256 / 1,024).
  State hypothesis vs. outcome in one line. If KernelSHAP@4096 reaches the pullback, stop and tell the user before
  writing: it would change 5.1's byte-resolution claim.
- Figures: `scripts/paper_figures.py` lists KernelSHAP's window counts by hand (`kernelshap_k64` ... `kernelshap_k1024`,
  lines ~35-58); add `kernelshap_k4096` (and its pushforward) and run it with
  `--pb_gbdt artifacts/experiments/e1/seed-0/zeros-typical-header-shared-ks4096`. Then update Section 5's KernelSHAP
  sentences (`manuscript/_e_evaluation.tex`, lines ~30-45 and ~70-76) and the pairwise counts against the pullback;
  `make` and `make check` in `manuscript/`.
- Record the result in `docs/status.md` (where run 66's shared-protocol results are recorded) and in run 74's
  comments.

## Then: a fresh critical review

`REVIEW.md` (2026-10-16) predates the reorganization and nearly every current result; its risks are mostly closed
(`docs/review-reassessment-2026-10-19.md`). Ask the user whether to run a new simulated CCS review of the current
draft (the `security-paper-writing` skill) and in what form (one reviewer or several; body only or the whole paper).
Review the body and the current front matter together, since the review should shape the rewrite of the abstract,
introduction, and conclusion. Report only issues that would change a reviewer's verdict; the user finds sentence-level
rewording suggestions pedantic.

## Decisions waiting on the user

- **W7 (one extractor):** instrument the Android extractor (3-5 weeks; must start soon for mid-January) or scope the
  generality claims to "domain-agnostic by construction" and delete the blue Android sentence (hours).
- After the review: the front matter (abstract, introduction, conclusion), written last.

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
