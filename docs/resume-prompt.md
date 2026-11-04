# Resume: ProvExp (after 2026-11-04, session 13): read runs 125, 128, 127; Table 7 with the user

## Where things stand

Session 13 read run 124, put the strong-toolkit result into the paper as prose, resolved the last `% VERIFY`, and built
Table 7's ERDALT row. Details: `docs/status.md` (session-13 block) and `PLAN.md` ("Next steps (2026-11-04, session 13)").
Nothing pushed.

1. **Run 124 (10% half), read; in §5 as two sentences** (`8b06aaf`). At GAMMA's own budget nothing changes:
   - the monotone rows stay at 0 in their population (0/28, 0/30, 0/31);
   - import injection evades the reference on 27/47 (26/47 at the low budget);
   - section injection evades nothing, because every output adds at least 870 KB (over the cap); without the cap only
     4/47 would fall below the threshold.
2. **§6's `% VERIFY` resolved** (`5fbc534`). Chen et al. 2021 choose monotone directions from suspiciousness and attacker
   cost, not "features an attacker can only increase"; the sentence is fixed. Open for the user: whether §6's "all four
   works rest on the same input, the directions an attacker's edits can move each feature" overstates Chen 2021.
3. **ERDALT row built** (`78d5aff`; user: build it, follow the paper, note the patch).
   - `src/provexp/models/erdalt.py` ports Gimenez et al.'s `train_model.py`. Their release leaves the output layer
     unconstrained, so the network is not monotone; ours constrains it too (`docs/upstream-issues.md`, item 8).
   - It learns from the 4 seen attacks' 1,797 change vectors: the pilot's 200 (the same vectors PV-seen is built from)
     plus run 122's 1,597 on training malware.
   - Deviations from their code: batch 256; the epoch is selected on our validation split; a temperature on the logit.
     Logits reach the thousands, and sigmoid saturated at 1.0 for 2.5% of benign files, so the threshold became 1.0 and
     the black-box attacks got a flat score. The rescaling keeps every decision.
   - `scripts/a_erdalt_hole.py` checks ERDALT's first layer, column by column, against the derived M_full table, and
     counts the allowed moves on the pilot malware that lower the score.
   - The `.predict` wrapper plugs into `a1_evaluate.py`, `a1_adaptive.py` (bucket aiming by gradient size), and the
     attack wrapper.
4. **Running at session end:**
   - **Run 125** (this server, user's tmux): generation was at 1,150/1,200, then the retraining and evaluations follow.
   - **Run 127** (second server): not yet copied back.
   - **Run 128** (user's tmux, one GPU + 16 workers): ERDALT training was at epoch ~196/310, validation AUC ~0.905, 25-40
     violations. The selection criterion (< 5 violations) was not yet met.

## Next session, in order

1. **Read run 125** (`artifacts/experiments/a1/advtrain-strong/`; logs `a_advtrain_strong_generate.log`,
   `train_classic-gbdt-0-advtrain-strong.log`, `a1_eval_advtrain_strong*.log`, `a1_adaptive_advtrain_strong.log`).
   - Hypothesis: it resists gamma_api and header_fields, but the adaptive search still evades it at about the
     unconstrained rate.
   - Then replace its literal `--db /shared/...` with `"$EMBER2024_DATA/tr"` as in `run/122`, and sync its header.
2. **Read run 128** (`artifacts/models/erdalt/seed-0-s10-seen/metrics.json`; `artifacts/experiments/a_erdalt/{hole/hole.json,
   hole/hole_features.csv, toolkit/table.json, adaptive/adaptive.json}`; logs `train_erdalt-0-s10-seen.log`,
   `a_erdalt_hole.log`, `a1_eval_erdalt.log`, `a1_adaptive_erdalt.log`; report any `LOST` lines).
   - Report: AUC, TPR at 1% FPR, the selected epoch, and whether the criterion was met. If the log shows `WARNING: no
     epoch has < 5 violations`, say so plainly.
   - Then the checks (`docs/direction-A-mock.md`, "ERDALT row"): faithfulness (seen evasion <= ~10%); the hole (violating
     weight share per direction class, and pilot files with a lowering move); held-out and adaptive evasion. The
     adaptive cell's `mismatches` count.
   - Hypothesis (in the run header): seen <= ~10%, held-out ~20-40%, adaptive >= 50%, the hole mostly in the features
     moved both ways, AUC below the mock.
   - Report a failed check as such. Sync `run/128`'s header with the results and runtime.
3. **Read run 127** once the user has copied `artifacts/experiments/a1/adaptive-beam/` and
   `artifacts/logs/a1_adaptive_beam.log` back from the second server.
   - Report per row: evaded at 200, 1,000, and 5,000 candidates, and the `mismatches` count.
   - Report every monotone row's `min_delta_logit` (must be exactly 0).
   - The beam-search smoke test in session 13 showed 4 mismatches on the s10 reference GBDT. The GBDT scoring path was
     not changed, so check whether run 127 shows mismatches too, and why.
   - Reference points are in the script header: unconstrained 35-45%; full toolkit 55%; in-catalogue toolkit 27%
     (13/49); greedy 20%; the literature at most 9.6%. The user chooses the reading after the run: propose one with its
     reason, and report a failed hypothesis as such.
   - Then run 127's step 4 (run 125's model) on whichever server has it. Sync `run/127`'s header.
4. **Table 7 with the user:**
   - run 125's row (replaces or joins run 122's; footnote: gamma_api and header_fields are held out for PV but trained
     on here);
   - the ERDALT row, with a footnote on the patch and the deviations;
   - the adaptive column from run 127, replacing the 77% synthetic cell and stating its budget.
   Then `make` / `make check`. Use `/paper-prose` for any prose (lesson 15: report, don't narrate). The §5 text on the
   closest baseline (PV) may need a sentence on ERDALT and its hole, if the run supports one.
5. **Decide with the user:**
   - MAB-Malware as a held-out attack (likely unnecessary after run 127; its operations are all in our catalogue);
   - whether the headline changes (not adopted);
   - the Chen 2021 sentence in §6.
   Only then the introduction and the other empty sections, spine first.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision).
- Routing to Table 7's sums rows needs a plan first. The beam search scores only thrember-space defenses (ERDALT reads
  thrember features, so it is covered); the sums row's adaptive cell rests on earlier runs.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-8; item 8 is a note to Gimenez et al.).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand
  over a `run/` script (next number **129**), reading `NUM_WORKERS`. The second server has 20 physical cores; the user
  runs it at 24 workers.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
