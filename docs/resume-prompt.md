# Resume: ProvExp (after 2026-11-04, session 14): read run 130, then choose the next work with the user

## Where things stand

Session 14 read runs 125, 127, and 128, ran run 129, and scripted run 130. The user runs run 130 overnight. Details
and the good/bad/neutral assessment are in `docs/status.md` (session-14 block); the plan is in `PLAN.md` ("Next steps
(2026-11-04, session 14)"). This session did not touch the manuscript (the Sections 2-3 rewrite, `084055c`, is
separate work). Nothing pushed.

- **Run 125 (adversarial training on the attacks that work).** Accuracy unchanged (AUC 0.9976, TPR 95.6%). The
  toolkit falls from 55% to 31% (gamma_api 22 -> 11, header_fields 11 -> 3 of 49). Greedy adaptive search: 12/49 (24%).
- **Run 128 (ERDALT).** AUC 0.881, TPR 61.1%; detects 25/50. Seen 0/25 (faithful); held-out 23/25 (92%; the
  hypothesis of 20-40% failed); beam 20/25 (80%). 89.7% of L's weight lies in the derived hole. The selection criterion
  was met only at the last epoch (309/310). Risk: reviewers may call the port weak.
- **Run 127 (beam, 5,000 candidates).** Unconstrained 25/49 (51%); run 122's adversarial training 20/48 (42%); PV on
  the 10% store, 4 attacks 15/22 (68%), 8 attacks 14/22 (64%); monotone rows 0, with a largest score drop of exactly
  0.0. Mismatches are pefile's two unmodeled warning features; every kept file is re-extracted, so no verdict depends
  on them.
- **Run 129 (greedy menus x 10% PV).** Adds nothing to the beam.
- **Decided (user): Table 7 reports the beam alone.** Never a union ("any search evades") across attacks; report one
  attack, or several separately. Claude's call: the greedy searches get no column, only one §5 sentence: on every row
  of the table the beam evades every file they evade. The PV rows' adaptive cells come from the 10% models, like their
  other columns.

## Next session, in order

1. **Read run 130**: `artifacts/experiments/a1/adaptive-beam/advtrain-strong/adaptive.json`, log
   `artifacts/logs/a1_adaptive_beam_advtrain_strong.log`.
   - Report evaded at 200, 1,000, and 5,000 candidates, `mismatches`, and any `LOST` lines.
   - Hypothesis (header): ~20-25 of 49.
   - Check that the beam evades every file run 125's greedy menus evade (`advtrain-strong/adaptive-{twelve,appsec}`),
     since the §5 sentence rests on it.
   - Sync `run/130`'s header with the result and runtime.
2. **Decide with the user what to work on next.** Lay out the options briefly, with a recommendation:
   - **Table 7 edits (ready).** The beam column with its budget; run 125's row replacing run 122's (Claude's
     suggestion, not yet agreed); the ERDALT row with a footnote (the output-layer patch, batch 256, epoch selected on
     validation, temperature, criterion met at the last epoch); the synthetic 77% -> 64%; the §5 prose that cites
     these cells ("20 of the 22", "17 of 22", "9 of 48", ...). Optionally one §5 sentence on ERDALT and its hole.
     Then `make` / `make check`, and `/paper-prose` for prose (lesson 15: report, don't narrate).
   - **The sums row's beam cell.** It needs a routing plan first; the beam scores only thrember-space defenses.
   - **The scale-up's adaptive budget.** Each pair costs ~10-20 CPU-min at 5,000 candidates, and the monotone rows
     always spend it all: ~3,000 CPU-h at 2,000 files. Options: the 1,000-candidate checkpoint, or attacking a subset.
   - **ERDALT's criterion at seeds 0-2**: more epochs, or report the last epoch when it is not met.
   - Still open: MAB-Malware (likely unnecessary), the headline (not adopted), §6's Chen 2021 sentence. After those
     come the introduction and the other empty sections, spine first.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision).
- Routing to Table 7's sums rows needs a plan first (see step 2). The beam search scores only thrember-space defenses (ERDALT reads
  thrember features, so it is covered); the sums row's adaptive cell rests on earlier runs.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-8; item 8 is a note to Gimenez et al.).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand
  over a `run/` script (next number **131**), reading `NUM_WORKERS`. The second server has 20 physical cores; the user
  runs it at 24 workers.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
