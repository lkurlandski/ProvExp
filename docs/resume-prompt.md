# Resume: ProvExp (2026-10-20, later) — 6.1 decision, then the unfiltered audit and Section 6's placeholders

Read `CLAUDE.md`, then `docs/status.md` (top: "2026-10-20"), `docs/experiments/specs.md` (6.1 Part A and its fallback;
6.2), and `manuscript/main.pdf` Section 6 (blue `\synthetic{...}` = placeholders). Explain in plain language; ask before
changing what a claim is for. Follow the memories `consistency-and-simplicity`, `paper-writing-style`,
`check-baseline-realism`, and `mock-the-result-first`.

## Where things stand

- **Section 5 and Appendix C are filled** from runs 66, 67, and 70 (commit b2aea56). Figures 3-5 regenerated under byte
  deletion. Results that changed direction were reworded: the pullback at matched resolution equals occlusion
  (KernelSHAP beats both); adaptive KernelSHAP beats occlusion only at 4,096 queries; the byte-level pullback beats
  every direct method (72-89/100 files).
- **6.1 attack transfer (run/68) is a NO-GO.** MalConv evaded 81%; the GBDT never crosses its threshold and becomes
  *more* confident on 78% of files; 5/100 drop by >1 log-odds. The pullback ranks the signed change best (Spearman
  0.34) but not significantly better than windows (bootstrap CI of the difference [-0.09, 0.41]). **Do not write 6.1's
  result until the user picks a direction** (the spec's fallback, option 1: controlled loader-safe changes to the shared
  bytes S vs. each detector's exclusive bytes; or another idea they raise). Mock the table before any code.
- **6.2 is filled** (run/69 done: no reliance beyond header fields; 8 of 9 fields reconfirmed; one robustness
  sentence in 6.2). Remaining blue in 6.2: the retrained-MalConv row (deferred).

## Deferred, the user decides

- KernelSHAP / adaptive KernelSHAP at 4,096 windows on the GBDT (~2 h; KernelSHAP@4096 is missing from Figure 4),
  and the scale-up to 500 files / seeds.
- Retraining MalConv with the audited fields zeroed (Table 5's blue row); the stronger attacker on the mitigated
  MalConv (the run/68 attack exists, so this is cheap).
- W7: a second extractor (Android). Front and back matter once the body's numbers are final.

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
