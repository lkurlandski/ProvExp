# Resume: ProvExp (after 2026-11-03, session 9): read run 122, review §6, then keep writing with the skill

## Where things stand

Session 9 built the writing method and drafted related work. Details: `docs/status.md` (session-9 block). Nothing
pushed.

1. **Writing method (settled with the user).** `docs/writing-spec.md` is the taste reference (habits to *ration*, not
   ban; techniques to use when they help; layout defaults; drafting length 50-75% over budget; the raw reaction log).
   The project skill **`paper-prose`** (`.claude/skills/paper-prose/SKILL.md`) holds the lessons distilled from the
   user's feedback and the procedure. **Invoke it for any paper prose.** After every round of feedback: log the raw
   reaction in the spec, then add, sharpen, or delete lessons in the skill. The goal (user): less and less feedback
   needed. When a unit is accepted with little change, draft the next one larger.
2. **§6 related work** is in `manuscript/_g_related_work.tex` (963 words). ¶1 (problem-space attacks) is final after
   four review rounds. **¶2-4 (constraints over features; robust and monotone detectors; incremental computation and
   provenance) were never read by the user**: a `% REVIEW` comment marks them. Start the writing part of the session
   by showing them to the user for a careful review, then log the reactions and update the skill.
3. **`run/122` (adversarial-training row) hung and was fixed, not relaunched.** A dead `multiprocessing.Pool` worker
   made `pool.map` wait forever. `map_watchdog` (`scripts/a_pv_attacks.py`) now guards `a_advtrain.py` and
   `a1_evaluate.py`. The hung job was killed (all 27 processes, 2026-11-03 ~19:50); the user relaunches
   `NUM_WORKERS=24 run/122_adv_training.sh` (generation ~20 min, not 6-7 h; then retrain, toolkit eval, adaptive).

## Next session, in order

1. **Read `run/122`** if it finished: `artifacts/experiments/a1/advtrain/` (`generated/report.json`, `toolkit/`,
   `adaptive-*`), logs `artifacts/logs/a_advtrain_generate.log` (look for `LOST` lines and report them),
   `train_classic-gbdt-0-advtrain.log`, `a1_eval_advtrain.log`, `a1_adaptive_advtrain.log`. Replace Table 7's
   `\synthetic` adversarial-training row from the measured AUC / TPR@1% / detected / seen / held-out / adaptive union,
   honestly (expected: seen ~0, held-out little changed, adaptive ~20%, not the sound 0%), and the sentence in
   `_f_evaluation.tex` that cites it; `make` / `make check`. If it did not finish or hung again, diagnose from the log
   before anything else. Then sync `run/122`'s header comments (runtimes; the watchdog), only while it is not running.
2. **§6 ¶2-4 review** with the user (see above). One `% VERIFY` remains (Chen et al. 2020: how the features a subtree
   edit can change were bounded); `dyrmishi2023empirical` and `sheatsley2021robustness` lack pages.
3. **Next sections with the skill**, spine first: introduction (§1, framework-first with a detector-centered results
   paragraph; reuse the review's §8 drafts: contributions list, key-insight sentence, introduction argument), then
   background (§2), discussion (§7, incl. the pending R7/R15 sentences), Figure 1 (TikZ, the edit-to-features
   pipeline on the running example), abstract last. Budgets: `docs/paper-mock.md`.

## Open user decisions

- R4 (a second built instance) stays a tier-3 decision.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision). Routing to Table 7's sums rows needs a plan first.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md`.
- Only run jobs under ~10 min yourself; otherwise smoke-test and hand over a `run/` script (next number **123**),
  reading `NUM_WORKERS`. The `/delegate` skill covers safety-classifier false positives on per-sample analyses.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
