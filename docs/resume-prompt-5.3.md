# Resume: draft §5.3 *What Observed Attacks Miss* (block 3 of §5's rewrite)

Written at the end of session 34 (2026-11-11). Self-contained: everything needed to start is below or in the files it
names. (`docs/resume-prompt.md` belongs to a parallel session, the holistic review of §4 and §5; leave it alone.)

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the
instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`; `make` and `make check` in
`manuscript/`); §5 *Evaluation* is `manuscript/_f_evaluation.tex`. §5 is three findings about adversarial examples
(PLAN.md decision 10; agreed, do not reopen): 5.2 *What Hand Analysis Misses*, **5.3 *What Observed Attacks Miss***
(`sec:eval:observed`), 5.4 *What Robustness Costs* (`sec:eval:detectors`, Table 4). Check `manuscript/main.aux` before
naming a section, table or definition number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10, especially "Session 34, continued"), the mock's
5.3 (`docs/paper-mock.md`, rewritten in session 34: the paragraph plan), and `docs/section-5.3-design.md` §10.4-10.5
(results, caveats, what to claim and what not). Use the `paper-prose` skill for all prose; the user's raw reactions
are in `docs/writing-spec.md`. Read §5.1, §5.2 and §5.4 as they stand, so 5.3 uses their terms and does not repeat
them.

## Step 0: has run 135 finished?

**Run 135** (`run/135_loo_varied.sh`, launched by the user 2026-11-11 to run overnight) redoes leave-one-out the fair
way: for each of the eight toolkit attacks, PV and ERDALT are built from run 133's outputs of the other seven, then the
eighth attacks them (seed per file) on the pilot malware they detect. Outputs: `artifacts/experiments/a_loo_varied/`
(`summary.json`, `pv/<attack>/`, `erdalt/<attack>/`); logs `artifacts/logs/*vloo*.log`.

- If its header already has a "Results" block, it has been read; use it.
- If `summary.json` exists but the header has no results: read it against the header's hypotheses (say which held and
  which failed, plainly), record results and runtimes in the header, in the design doc (§10.4 and the log) and in
  `docs/status.md`; then draft with the real numbers.
- If it has not finished: draft with the **predicted values in blue** (`\synthetic{...}`, CLAUDE.md "Deferred runs"),
  prose written as if the run had finished, and a `% SYNTHETIC: run 135` comment beside each. Predictions (its header):
  PV's held-out evasion near 0 in every fold (gamma_api perhaps 1-2 of ~10 files; PV detects only ~9-10 pilot files);
  ERDALT high on the gamma_api fold (~25 of ~29; even seen, gamma_api with other donors evaded 24/29) and header_fields
  (~10/29), near 0 on padding, dos_extend, gamma_sections; mean ~20-40%.

## The task

Draft §5.3 in small blocks with the user's review after each (memory `draft-in-small-blocks`): first a short plan for
yourself (which paragraph carries which point, which numbers, what goes to the appendix), then a few paragraphs per
block; `make`, `make check`, read the rendered PDF (`pdftotext`) after each; show the user the new text and wait.
Budget ~950 words (may run 50-75% over while drafting). Continuous prose, no stacks of labelled paragraphs unless the
neighbouring subsections use run-in paragraph heads (5.4 does; match it).

**The agreed finding** (do not reframe; memory `dont-reframe-research-claims`): a defense learned from observed attacks
inherits what the attacks did not do, and nothing in the observations says what that is. Evidence, in the mock's order:

1. **Protocol** (5.1 left the learned-defense protocol to 5.3): every learned defense is built from the same 3,183
   outputs of the eight toolkit attacks, run with a fresh random seed per (attack, file) on 400 *training* malware with
   training goodware as donors; tested on the pilot (test) malware it detects, at 1% FPR, low budget, seed per file.
2. **Coverage is invisible to the defender:** the same eight attacks lower 745 of the 1,070 lowerable features with the
   random generator reset before every run, 928 when varied over 400 training files; the derived table lists all 1,070
   at once (`artifacts/experiments/a_coverage/report.json`, `a_varied/coverage/report.json`).
3. **The missing operation becomes the hole:** PV (Gimenez et al.'s perturbation-vector selection + monotone GBDT)
   rebuilt from the varied outputs: the toolkit evades it on 0/9; the adaptive search on 4/9, each with one rename of
   the entry section within 50 candidates (no toolkit attack renames; MAB-Malware does). Its hole: 124 features, 38.8%
   of its gain, led by the entry-section-name bucket (12.8%), which the derived table marks lowerable in advance.
4. **Unmoved is not unmovable:** observation cannot separate features an edit can lower from features no edit moves.
   PV built from the published-style runs trusts what it should not (search: 14/22); PV rebuilt constrains what it
   need not and detects 26.2% at 1% FPR, against 87.3% for the derived detector on the same features (89.7% on the
   sums; reference 93.5%). The DLL characteristic flag (24% of the unconstrained model's gain) is never moved and no
   edit can move it; PV forces it monotone, the derived table leaves it free. Leaving PV's never-moved features free
   gives 50.9% (run 134, PV-free; not Gimenez et al.'s rule, and unsound against operations the attacks lack). Not the
   8 broken shift outputs (run 134, PV-clean: 26.7%).
5. **ERDALT constrains the vectors it saw, not the next ones:** rebuilt from all eight attacks, its own training attack
   gamma_api, taking imports from other donor goodware, evades it on 24/29; the adaptive search on 22/29. Its learned
   layer puts 90% of its weight on lowerable features (`a_varied/erdalt-best-hole/hole.json`).
6. **Adversarial training** on the same outputs: the toolkit evades it on 12/50 (undefended 25/49), the search on
   23/50; detection unchanged (95.6%).
7. **Leave-one-out** (run 135): one sentence in the body, per-fold table in an appendix.
8. **The learned region** (exact tree solver): the current paragraph in §5.3 uses the old seed-0 outputs and the old
   PV's 22 files. Its argument (per-feature ranges ignore that one edit moves many features together) does not depend
   on the seed; decide with the user whether to keep it, cut it, or recompute it on run 133's outputs (estimate the
   cost first; over ~10 minutes it goes to the user as a `run/` script).
9. **Audit table** (assembly only; user chose option (b)): one row per defense, grouped by how its trust was set (by
   hand: hand-table detector, expert set; from attacks: PV, ERDALT, adversarial training; the derived detector for
   reference). Columns: how trust was set, what the derivation flags, TPR at 1% FPR, toolkit (seed per file; one
   column counting any of the eight, as Table 4 does), leave-one-out held-out, adaptive. Risk: the "flags" column mixes
   units (features, share of gain, share of weight); settle the wording with the user.

Numbers and their sources: run 133's and 134's headers, the design doc §10.4 (table), `artifacts/experiments/
a_varied/{toolkit-pv,toolkit-erdalt,toolkit-full}/table.json`, `a_varied/adaptive-*/adaptive.json`,
`a_pv/best/derived-pre/report-best.json`, `a_pv/clean/`, models' `ts_predictions.parquet` (TPR at a FPR: the
(1 - FPR) quantile of goodware scores). Exact numbers matter less than structure and argument at this stage.

**Clean-up in the same pass:** §5.4 still holds the old material, marked `% 5.3 MATERIAL` (the old PV/ERDALT
paragraphs, with false statements: "We run the attacks on the training malware" was not true of the old PV) and the
`% MOVED TO 5.3` table-row comment. Fold what survives into 5.3 and delete them, so 5.4 ends with *Beyond the
guarantee*. Old numbers to retire: PV 44.4%/77.5% hole, 15/22 and 14/22 as the main result (14/22 survives only as
the published-style PV), ERDALT 20/25 and 23 held-out, run 131's folds, the old adversarial-training row (run 125).

## Caveats to handle in the prose (light, confident; memory `limitations-tone`)

- PV rebuilt is judged on 9 files (it detects little); the scale-up adds files later. Say counts, not only rates.
- ERDALT's scores pile at a floor (every evasion ends at p = 0.49966 against a threshold of 0.49968); our port
  reaches AUC 0.88, TPR 62.7%. Describe it as our port of their code, accurately; do not overclaim against their paper.
- What the toolkit evasions cover: two of the eight attacks (GAMMA's section and import injection) rebuild the layout
  through LIEF, outside the threat model (5.4 *Beyond the guarantee* explains this; refer to it, do not repeat).
- **Portray Gimenez et al. accurately** (memory `portray-cited-work-accurately`; `papers/gimenez2025certifiably.pdf`):
  their paper says they ran the eight attacks on 200 malware correctly detected, with a 60 s timeout; it does not say
  which split the perturbation vectors came from or how the attacks were seeded. The seed reset is in their released
  code per our harness's note (`scripts/a_pv_attacks.py`, "their random.seed(0)"); verify against their repository
  before attributing it in the paper, or describe our own protocol without attributing.
- Open, raise with the user when drafting item 3: the remaining gap is MAB-Malware's operation (rename), so adding it to
  the pool would close it. Our point is that the defender cannot know which operation to add; a reviewer may still ask
  for that row (design doc, O5).

## Constraints

Claims say "on EMBER"; §5 is findings, not a defense paper, and the detectors' accuracy cost is a measurement, never
"small" (memory `findings-not-defense-paper`); say what each evasion rate covers and lead with the overall rate (memory
`attack-strength-vs-literature`); never a union across searches (memory `report-attacks-separately`); no timing or
effort claims; explain plainly. Settled in 5.4, do not re-raise: no comparison of the adaptive search's 51% with the
toolkit's rate; one toolkit column counting any of the eight attacks. Jobs over ~10 minutes go to the user as numbered
`run/` scripts (136 is next); never edit a running `run/` script. Before committing code: `env/bin/ruff check src tests
scripts` and `env/bin/mypy src tests scripts`. Commit to `main` in logical pieces; do not push. The parallel session
may edit `docs/status.md` and `PLAN.md`: re-read them right before editing and change only your own lines. At the end:
update `docs/status.md`, archive this prompt under `docs/archive/` and index it in `docs/README.md`.
