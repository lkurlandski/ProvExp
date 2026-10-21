# Resume: ProvExp (after 2026-10-21) — run a fresh simulated CCS review

Read `CLAUDE.md`, then `docs/status.md` (top blocks, 2026-10-21). Explain in plain language; ask before changing what a
claim is for. Follow the memories `consistency-and-simplicity`, `paper-writing-style`, `check-baseline-realism`,
`mock-the-result-first`, and `no-pedantic-rewordings`.

## Where things stand

- **The whole draft is current.** On 2026-10-21 the abstract, introduction, background, discussion, and conclusion were
  brought up to date with the body, followed by an end-to-end pass. The front matter is no longer a placeholder, but the
  review should still shape its final form.
- **Section 5:** run 74 is in. KernelSHAP over 4,096 windows is the strongest direct method (7.17 log-odds), still below
  the byte-level pullback (8.03; the pullback wins on 59/100 files, at every budget, with one extraction instead of
  32,770). Pushed forward, KernelSHAP@4096 keeps 0.97 of TreeSHAP's evidence. The discussion answers "would finer
  windows catch up?" with cost.
- **Section 6.1, Table 2:** the pullback predicts the GBDT's drop under MalConv-guided field edits (Spearman 0.48 vs.
  0.21 for occlusion; 500 files, run 72). A KernelSHAP row is **predicted in blue** (0.31 / 0.65) until run/75 runs.
- **Blue placeholders** (`\synthetic{...}`): Table 2's KernelSHAP row and its sentences in 6.1 and the introduction
  (run/75); 6.2's retrained-MalConv row and sentence (deferred); the discussion's Android sentence (W7, undecided).

## Next: the review

Run the simulated CCS review with `docs/review-prompt.md`, following it as written (three reviewers, blind first pass,
then a comparison with `REVIEW.md` and `docs/review-reassessment-2026-10-19.md`; output in `REVIEW-<date>.md`). The
prompt lists what is settled and how to treat blue placeholders. If the user wants truly independent reviewers, run
each as its own subagent and write the meta-review and risk register yourself. Then go through the risk register with
the user and decide what to act on.

## Pending, for the user

- **run/75** (`run/75_cm_kernelshap_4096.sh`, ~32 h, 16 workers, resumable): when it finishes, read it (log
  `artifacts/logs/cm-shared-edit-500-ks-seed0.log`; `rho_kernelshap`, `auc_kernelshap`, `diff_kernelshap_lo/hi` for
  the arm `malconv_only`), state hypothesis vs. outcome (expected rho ~0.25-0.35), replace the blue values in Table 2,
  6.1, and the introduction, and record it in `docs/experiments/cm.md`. If KernelSHAP approaches the pullback (0.48),
  stop and tell the user before writing.
- **W7 (one extractor):** instrument the Android extractor (3-5 weeks) or scope the generality claims to
  "domain-agnostic by construction" and delete the blue Android sentence (hours). The review may inform this.
- Deferred by the user, do not propose: MalConv retraining (and a stronger attacker on it), the scale-up, more seeds.
  Dropped: a named-feature TreeSHAP baseline for Table 2, a 0.1% FPR column, sentence-level rewordings.

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` in `manuscript/` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library
  code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
