# Resume: ProvExp (after 2026-10-20) — the body is filled except the deferred runs

Read `CLAUDE.md`, then `docs/status.md` (top block, "2026-10-20 (afternoon)"). Skim `manuscript/main.pdf` Sections 5-6;
the only blue placeholders left are 6.2's retrained-MalConv row (Table 5 and one sentence) and the discussion's Android
sentence. Explain in plain language; ask before changing what a claim is for. Follow the memories
`consistency-and-simplicity`, `paper-writing-style`, `check-baseline-realism`, and `mock-the-result-first`.

## Where things stand

- Sections 5, 6.1, 6.2 and Appendix C carry real numbers (runs 66-72). 6.1's attack transfer: run 68's DOS-stub/slack
  attack (wrong region, the GBDT rises) -> MalConv-guided loader-safe field edits (the GBDT drops) -> before any edit,
  the GBDT's pullback on the chosen fields predicts its drop (Table 2: Spearman 0.48 vs. 0.21 windows vs. 0.03 bytes;
  500 files, run 72).
- Run 71's five-way "who chooses the fields" table stays in `docs/experiments/cm.md`, not in the paper.

## Next: the user decides which

- KernelSHAP / adaptive KernelSHAP at 4,096 windows on the GBDT (~2 h; KernelSHAP@4096 missing from Figure 4).
- Retraining MalConv with the audited fields zeroed (Table 5's blue row); a stronger attacker on the mitigated MalConv.
- Scale-up of Sections 5/6 to 500+ files and seeds 0-2; W7 (Android).
- Then a read-through of the whole body for coherence, and the front and back matter (abstract, intro, conclusion).

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
