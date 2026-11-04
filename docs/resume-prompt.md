# Resume: ProvExp (after 2026-11-04, session 14): Table 7 with the user; read run 130

## Where things stand

Session 14 read runs 125, 127, and 128, ran run 129, and scripted run 130. Details: `docs/status.md` (session-14
block). This session did not touch the manuscript (the Sections 2-3 rewrite, `084055c`, is separate work). Nothing pushed.

- Run 125 (strong adversarial training): accuracy unchanged; the attacks it trained on drop by half or more
  (toolkit 55% -> 31%); greedy adaptive 12/49 (24%).
- Run 128 (ERDALT): AUC 0.881, TPR 61.1%; seen 0/25, held-out 23/25, beam 20/25; 89.7% of L's weight is in the hole.
  The criterion was met only at the last epoch.
- Run 127 (beam): unconstrained 51%, advtrain 42%, PV 64-68%, monotone 0% (min_delta_logit exactly 0). Mismatches are
  pefile's two warning features (unmodeled; every kept child is re-extracted, so no verdict depends on them).
- Run 129 (greedy menus x 10% PV): adds nothing to the beam (14/22 and 15/22).

## Next session, in order

1. **Read run 130** if the user has run it (`artifacts/experiments/a1/adaptive-beam/advtrain-strong/adaptive.json`,
   log `artifacts/logs/a1_adaptive_beam_advtrain_strong.log`). Hypothesis in the header: ~20-25 of 49. Sync the
   header.
2. **Table 7 with the user** (proposal in `docs/status.md`, session 14):
   - the adaptive column: union of the three searches (proposed) or the beam alone; state the budget;
   - run 125's row (replaces or joins run 122's; footnote: gamma_api and header_fields held out for PV but trained on
     here);
   - the ERDALT row (footnote: the patched output layer, the deviations, the criterion met at the last epoch);
   - the 77% synthetic cell -> 14/22 (64%).
   Then the prose that cites these cells (§5: "evades PV on 20 of the 22", "17 of 22", "9 of 48", the adaptive
   rates) and `make` / `make check`. Use `/paper-prose` (lesson 15: report, don't narrate). §5's PV paragraph may
   take one sentence on ERDALT and its hole.
3. **Decide with the user:** MAB-Malware as a held-out attack (likely unnecessary); whether the headline changes (not
   adopted); the Chen 2021 sentence in §6. Only then the introduction and the other empty sections, spine first.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision).
- Routing to Table 7's sums rows needs a plan first. The beam search scores only thrember-space defenses (ERDALT reads
  thrember features, so it is covered); the sums row's adaptive cell rests on earlier runs.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-8; item 8 is a note to Gimenez et al.).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand
  over a `run/` script (next number **131**), reading `NUM_WORKERS`. The second server has 20 physical cores; the user
  runs it at 24 workers.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
