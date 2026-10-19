# Resume: ProvExp (2026-10-20) — read the overnight runs, then WP8 (fill the placeholders)

Read `CLAUDE.md`, then `docs/status.md` (top: "Overnight runs launched 2026-10-19" and "Next (this thread) — WP8"),
`docs/experiments/specs.md` (the five experiment specs), and `docs/implementation-plan-2026-10-19.md` (WP0-WP8, build
status at the top). Skim `manuscript/main.pdf` Sections 4-6; the new results are blue (`\synthetic{...}`) placeholders.
Explain in plain language; ask before changing what a claim is for. Follow the memories `consistency-and-simplicity`,
`paper-writing-style`, `check-baseline-realism`, and `mock-the-result-first`.

## What happened yesterday (2026-10-19)

The manuscript was reorganized into **5 Evaluating the Transfers** (`_e_evaluation.tex`) and **6 Security
Applications** (`_f_applications.tex`), the field oracle and the planted-trigger subsection and the black-box P were
cut (trigger survives as Appendix B; oracle in `pb1.md`), and one byte-deletion measurement + one cost unit now span
5.1/5.2. Section 6 opens with a shared setting; 6.1 is attack transfer + descriptive triage (Part B adjudication was
dropped after a pilot pre-check); 6.2 gains the unfiltered audit. Low-hanging fruit done: Influence axiom as "computed
from", classifier `f`, overclaims trimmed, theory coverage (67/9/23) and instrumentation cost (0.19 vs 0.05 s) in 4.1,
related work checked against sources. Code for WP0-WP5 + WP7 written, smoke-tested, lint/mypy clean, unit tests pass.

## First thing: read the overnight results

Check each ran clean (`tail` the logs in `artifacts/logs/`; look for the summary JSON / tables at the end), then read:

1. **run/66 — Sections 5.1/5.2 on the GBDT.** `artifacts/reports/pb1_tables-shared.md`. Key reads:
   - Cost-vs-faithfulness and the deletion table: does **adaptive KernelSHAP** (methods `partition_b{B}`) beat uniform
     occlusion at equal queries but stay below the **byte-level pullback** (`pullback:treeshap_interventional`)?
     (Hypothesis yes; this is the in-class answer to review W4.)
   - The "Pushforward (Section 5.2)" table: do the pushed-forward window sources rise toward TreeSHAP with resolution,
     and sit near the `trend_*` reference curve? (Hypothesis yes.)
2. **run/67 — Section 5.2 on MalConv.** End of `artifacts/logs/pf-malconv-shared-seed0.log`. Key read: do the
   **gradient-free** sources pushed forward (`pushforward:occlusion_k1024`, `pushforward:kernelshap_k1024`) still beat
   the surrogate? (That answers the circularity objection, W5. The IG pushforward should stay on top.)
3. **run/68 — Section 6.1 attack transfer. THE GO/NO-GO.** `artifacts/experiments/cm_transfer/seed-0/report.json`:
   - `malconv_evaded` (expect high), `gbdt_drop_over_1.0` and `gbdt_crossed_threshold` (the transfer signal),
   - `predictors`: Spearman and AUC of `pullback_E` vs. `occlusion_E` vs. `changed_C`. **Go** if the GBDT moves on a
     non-trivial share AND `pullback_E` predicts it better than the others. **No-go** (the 6-file smoke hinted the GBDT
     may not drop, even rise): fall back to option 1 (controlled shared-reliance changes; `specs.md` 6.1 fallback) and
     tell the user before writing 6.1's result.
4. **run/69 — Section 6.2 unfiltered audit.** `tail` `artifacts/logs/audit-scramble-unfiltered-seed0.log`. Key read:
   are any **section / import / string** features confirmed (not only header fields)? Group the confirmed features by
   type for Table 3 (this grouping is the one unscripted follow-up).

State a one-line hypothesis-vs-outcome for each before editing the manuscript (a sentence, not a pre-registration).

## Then: WP8 — fill the placeholders

- Regenerate Figures 3-5 and the 6.1/6.2 tables from the real data (`scripts/paper_figures.py` -> `manuscript/assets/
  data/`, and the table scripts). **Figure 4 currently shows old-protocol data under a placeholder caption** and must
  be regenerated under byte deletion.
- Replace every `\synthetic{...}` in `_e_evaluation.tex` and `_f_applications.tex` with the real numbers; keep the
  prose, adjust only where a result changed direction. `grep -rn "synthetic" manuscript/*.tex` to find them all.
- `make` and `make check` in `manuscript/` after editing. The retrained-MalConv row of Table 5 and the Android
  paragraph stay blue (deferred).

## Deferred, the user decides

- KernelSHAP / adaptive KernelSHAP at **4,096 windows** (left out of the pilot to save ~2 h; add before any "even at
  the finest resolution the baselines fall short" wording) and the **scale-up** to 500 files / seeds.
- **Retraining MalConv** with the audited fields zeroed (Table 5 blue row), and the **stronger attacker on the
  mitigated model** (rerun run/68's attack against MalConv with those fields zeroed — cheap once the attack exists).
- **W7**: a second extractor (Android) for the generality claim, the largest remaining item.
- The **front and back matter** (abstract, intro, discussion, conclusion) rewritten once the body's numbers are final.

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
