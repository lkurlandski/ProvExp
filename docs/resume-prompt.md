# Resume: ProvExp (after 2026-11-04, session 12): read runs 124, 125, 127; Table 7 with the user

## Where things stand

Session 12 read the price list, built a strong adaptive search, and moved the heavy runs to a second server. Details:
`docs/status.md` (session-12 block) and `PLAN.md` ("Next steps (2026-11-04, session 12)"). Nothing pushed.

1. **Price list (run 126), in §5 as one paragraph.** Its hypothesis failed. The monotone constraints cost nearly all of
   the 3.9 points (dropping the two-sided features alone: 0.2). Import addition (2.1, through 1,282 import hash
   buckets) and the header overwrites (1.4) are most of it. The parser warnings cost nothing, so they stay unmodeled.
2. **W2 is smaller than the strategic review thought.** Zainab et al.'s 83.4% (MAB-Malware, EMBER-24) is on outside
   malware at 0.1% FPR. On EMBER-2024's own test malware, the comparable setting for our pilot, they report MAB-Malware
   9.6%, GAMMA shift 8.1%, MiniMal 4.5% (their Table XI; verified). Our greedy search reaches 20% and the toolkit
   union 55%.
3. **Run 124 (full-store half):** the literature budget adds nothing. gamma_api reaches 20/49 (22/49 at the small
   budget), and gamma_sections 0/49: every output is over the byte cap and none falls below the threshold even uncapped.
4. **Beam search** (`scripts/a1_adaptive.py --search beam`): beam 3, ~150 candidates per step, restarts, 5,000
   candidates per file. Every kept file is written by our own edits and re-extracted. Run 119 showed why it is needed:
   the greedy search stalled on 24 of the 39 files it did not evade, and hit the query cap on 15.
5. **Running:**
   - This server (user's tmux): `run/124`'s 10% half (350/388 tasks at session end), then `run/125`.
   - Second server (`NUM_WORKERS=24`): `run/127`, without run 125's model (step 4 skipped).
   The second server reads the dataset from `EMBER2024_DATA`. `run/sync_artifacts.sh` pulls inputs from this host
   (`lk3591@gcis-mkwics-rl.gccis.rit.edu`).

## Next session, in order

1. **Read `run/124`'s 10% half** (`artifacts/experiments/a1/toolkit-literature/s10/table.json`; log
   `artifacts/logs/a1_eval_literature_s10.log`; report any `LOST` lines). Hypothesis: the monotone rows stay at 0% in
   their population, and gamma_sections stays at 0. Sync `run/124`'s header (result, runtime).
2. **Read `run/125`** (`artifacts/experiments/a1/advtrain-strong/`; logs `a_advtrain_strong_generate.log`,
   `train_classic-gbdt-0-advtrain-strong.log`, `a1_eval_advtrain_strong*.log`, `a1_adaptive_advtrain_strong.log`).
   Hypothesis: it resists gamma_api and header_fields, but the adaptive search still evades it at about the
   unconstrained rate. Then, since it is no longer running, replace its literal `--db /shared/...` with
   `"$EMBER2024_DATA/tr"` as in `run/122`, and sync its header.
3. **Read `run/127`** once the user has copied `artifacts/experiments/a1/adaptive-beam/` and
   `artifacts/logs/a1_adaptive_beam.log` back from the second server. Report:
   - per row: evaded at 200, 1,000, and 5,000 candidates, and the `mismatches` count;
   - every monotone row's `min_delta_logit` (must be exactly 0).
   The hypothesis and reference points are in the script header: unconstrained 35-45%; the full toolkit 55%; the
   in-catalogue toolkit 27% (13/49); greedy 20%; the literature at most 9.6%. The user decided to choose the reading
   after the run, since both candidate gates read the same run. Propose one reading with its reason, and report a failed
   hypothesis as such. Then run 127's step 4 (run 125's model) on whichever server has it. Sync `run/127`'s header.
4. **Table 7 with the user:**
   - the strong-toolkit column, capped (uncapped in a note?);
   - run 125's row (replaces or joins run 122's; footnote: gamma_api and header_fields are held-out for PV but trained
     on here);
   - the adaptive column from run 127, replacing the 77% synthetic cell and stating its budget;
   - the sentence on why the toolkit's section injection fails here.
   Then `make` / `make check`. Use `/paper-prose` for any prose (lesson 15: report, don't narrate).
5. **Decide with the user:**
   - whether MAB-Malware is still worth running as a held-out attack (its operations are all in our catalogue);
   - whether ERDALT becomes a Table 7 row;
   - whether the headline changes (not adopted).
   Only then the introduction and the other empty sections, spine first.

## Carry-forward (unchanged)

- One `% VERIFY` in §6 ¶3 (Chen et al. 2021's monotonicity scope). Table 5's population scoping not re-audited
  (recorded decision). Routing to Table 7's sums rows needs a plan first; the beam search, like the greedy one, scores
  only thrember-space defenses (the sums row's adaptive cell rests on earlier runs). A G1 unit test for the expert
  instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-7).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand
  over a `run/` script (next number **128**), reading `NUM_WORKERS`. The second server has 20 physical cores; the user
  runs it at 24 workers.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
