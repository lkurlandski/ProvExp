# Resume: ProvExp (2026-10-20, afternoon) — read run/72, then write Section 6.1

Read `CLAUDE.md`, then `docs/status.md` (top block, "2026-10-20"), `docs/experiments/specs.md` (6.1 "Part A'", with its
outcome and decision), and `docs/experiments/cm.md` (the last two sections: "Attack transfer" and "Editing the shared
fields"). Skim `manuscript/main.pdf` Section 6.1; its attack paragraph and Table 2 are still blue placeholders.
Explain in plain language; ask before changing what a claim is for. Follow the memories `consistency-and-simplicity`,
`paper-writing-style`, `check-baseline-realism`, and `mock-the-result-first`.

## Where things stand

- **Done this morning:** Section 5 (runs 66-67), 6.2's unfiltered audit (run 69, one robustness sentence), Appendix C
  (run 70) are filled; Figures 3-5 regenerated. All committed.
- **6.1's claim is decided (user):** a defender who owns both detectors simulates the realistic attacker, one who
  explains only MalConv and edits 3 loader-safe header or certificate fields. Before any edit, the GBDT's pullback
  evidence on those fields predicts how much the GBDT's score drops; occlusion windows and the number of bytes changed
  do not (run 71, 100 files: Spearman 0.47 vs. 0.25 vs. -0.04; AUC 0.78 / 0.64 / 0.52). Defender framing kept.
- **run/72 (500 files) should be finished.** Log: `artifacts/logs/cm-shared-edit-500-seed0.log`; output:
  `artifacts/experiments/cm_shared_edit_500/seed-0/` (`report.json` has "predictors"). Rerun the tables without
  recomputing: `PYTHONHASHSEED=0 env/bin/python scripts/cm_shared_edit.py --seed 0 --tables_only --outdir
  artifacts/experiments/cm_shared_edit_500`.

## First: read run/72

Check it ran clean (`tail` the log; statuses, `unparsed` in `report.json`). Key read, arm `malconv_only` in the
"Predicting the GBDT's drop" table: does the pullback's rho stay clearly above the windows' with the bootstrap CI of the
difference (`diff_lo`, `diff_hi`) above zero? Hypothesis: yes (run 71's lead, 0.47 vs. 0.25, holds). Also note the
other arms (the lead held in all five at 100 files) and the per-arm medians for the context sentences. State the
hypothesis vs. outcome in one line before editing. If the lead does not hold, stop and tell the user before writing.

## Then: steps 3-4 of the 6.1 plan

3. **Write 6.1's attack result** in `manuscript/_f_applications.tex` (the "Attack transfer" paragraph and
   `tab:XML:Transfer`), replacing every `\synthetic{...}` there:
   - Table 2 becomes the prediction table (pullback / occlusion over 4,096 windows / bytes changed; Spearman and AUC
     for a drop of more than one log-odds), on the MalConv-guided edits.
   - The story, in continuous prose: deletion shows the shared bytes (existing paragraph) -> an attacker guided by
     MalConv alone who edits the DOS stub and slack (run 68) evades MalConv (81%) but makes the GBDT more confident,
     because the GBDT puts almost none of its evidence there (the pullback shows it) -> the same attacker editing
     loader-safe header and certificate fields (the 6.2 rulebook, located by P) also lowers the GBDT's score -> before
     any edit, the pullback tells the defender which of the GBDT's detections are at risk; windows blur the adjacent
     fields. One sentence for the GBDT-guided mirror (transfer is asymmetric; its predictor, MalConv's IG, needs no P).
   - Keep run 71's five-way "who chooses the fields" table out of the paper (it stays in `docs/`).
   - Present what works; no labeled-paragraph stacks; no internal IDs. `make` and `make check` in `manuscript/`.
4. **Coherence pass:** the 6.1 opener (its three questions), the Section 6 close, the introduction's contribution
   and the discussion where they mention attack transfer; `docs/experiments/specs.md` and `cm.md` with run 72's numbers;
   `docs/status.md`; rewrite this prompt.

## Deferred, the user decides

- KernelSHAP / adaptive KernelSHAP at 4,096 windows on the GBDT (~2 h; KernelSHAP@4096 missing from Figure 4).
- Retraining MalConv with the audited fields zeroed (Table 5's blue row); a stronger attacker on the mitigated MalConv.
- Scale-up of Sections 5/6 to 500 files and seeds; W7 (Android); the front and back matter once the body is final.

## Working rules

- Long jobs: smoke-test, estimate, numbered `run/` script (<=16 workers, GPU 3), the user runs it in tmux.
- `make` / `make check` after every manuscript edit; `ruff` + strict `mypy`; unit tests for new library code.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
