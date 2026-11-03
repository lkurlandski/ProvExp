# Resume: ProvExp (after 2026-11-03, session 4): decide the PV adaptive cell, edit Table 7, then items 9-11

## ⚠ Read this first (user, 2026-11-03)

The model may have switched to a simpler one partway through session 4 without the user's knowledge. **Before building
on session 4's work, re-examine it critically** -- do not take it on trust. In particular audit:
- **Item 8's design** (`scripts/a1_adaptive.py`: `Engine`, `full_menu`, `greedy_search`). Is scoring every candidate
  by the exact prediction of our own writer the right choice (vs the old declared-reachable effect)? Is `full_menu`'s
  candidate budget sound? Is the myopic-greedy diagnosis of the PV drop correct?
- **The decision to scope Table 5 to the population** (0 wrong of 34,965 in-population; 45 wrong out-of-population).
  Is population-scoping the honest presentation, or should the 45 out-of-population wrong be shown?
- **The reading of `run/119`** and the **PV-cell recommendation** below.

Nothing from session 4 is pushed. The manuscript Table 7 is **unedited**. Treat the recommendations here as drafts to
audit, not settled facts. Commits this session: item 8 code; run 118 read + Table 5 + population scoping; run/119 read.

## What session 4 did

- **Item 7 / run 118 read** (`run/118_item_exactness.sh`, 2,000 files, 57 min). Item-stated exactness
  (`reach.predict_structural` + `catalogue.predict_*` vs re-extraction) **holds on the population: 0 wrong of 34,965
  edits** (33,730 exact, 1,235 flagged -- only the two by-design abstentions). Out of the population, on 7 truncated
  files, 45 edits are wrong (so `report["exact"]=True` on the population, `exact_all_files=False`). **User decided:
  scope Table 5's item-stated rows to the population** (Wrong=0). `catalogue_checks.py` now computes exactness on the
  passing files (`declared_all`/`exact_all_files`/`declared_wrong_outside` added); Table 5 (`_f_evaluation.tex`) and
  its caption/prose carry the measured in-population counts (sec 7,256/6,776/480/0; imp 6,954/6,708/246/0; ext
  5,856/5,347/509/0; shf 4,995/4,995/0/0; ren 8,370/8,370/0/0; rdb 984/984/0/0; rsg 550/550/0/0). `make`/`make check`
  clean. Known cleanup (moot under scoping): the 22 out-of-population `ValueError` "splits the range" cases should
  FLAG, not raise, in `reach.shift_ranges`/`predict_structural`.
- **Item 8 built and run** (`scripts/a1_adaptive.py`). Extended the adaptive search from append+add-section to all
  twelve operations. Each candidate is scored by the **exact** prediction of our own writer (`catalogue.predict_*`
  for the structural ops; `reach.predict` chains for the in-place ops hdr/chk/dos/slk; the two gaps are extracted,
  ~5x cheaper than predicting), and the chosen step is materialized by that writer (never LIEF), so predicted ==
  re-extracted. New: `Engine`, `full_menu`, `greedy_search` on a `make_menu` closure, CLI `--operations`;
  `engine_predictors`/`menu` kept for the tests (96 pass, 12 skip).
- **`run/119` go/no-go** (pilot, queries 200, each C4 row under its own threat model):
  - **C4 soundness check passes:** mfull-feat 0/41 under M_full, madd-feat 0/47 under M_add, min_delta exactly 0.0.
    This is item 8's main paper value -- it is the *complete-threat-model* soundness check the review (R1a/R11) asked
    for (all twelve operations, not just append+add-section).
  - **unconstrained 4/49 -> 10/49** (the new ops help) **but short of GAMMA API's 24/47.** Not query-limited: for
    40/49 files the search barely moves the undefended GBDT (median drop 0.005). The go/no-go "beats GAMMA (>=24)" is
    **not met** -- the undefended model is robust to the loader-safe edit set.
  - **PV 12/22, below run 108's append+add-section 16/22.** The extra ops mislead the myopic greedy on PV's
    section-hash hole (q150 and q200 both 12, so not query-limited).

## The task

1. **Decide the PV adaptive cell in Table 7** (Claude flagged a drop; the user was mid-clarifying when session 4
   ended). The twelve-op search gives unconstrained 10/49 (up from 4) but PV 12/22 (down from 16/22). Options:
   - **Option 1 (Claude's recommendation): report the strongest of our search variants per detector** -- unconstrained
     10 (twelve-op), PV 16 (append+add-section, run 108), with one line that the Adaptive column is "the strongest
     evasion our search finds". Rationale: it is the standard honest way to report an adaptive attacker (max over what
     the attacker can do, not a handicapped single config); it keeps item 8's real wins (the complete C4 check + the
     unconstrained lift) without regressing PV; it avoids a speculative greedy fix.
   - Option 2: report the twelve-op search uniformly (unconstrained 10, PV 12). Clean/consistent but understates PV
     vs what our own search achieves.
   - Option 3: improve the greedy (e.g. tie-break to prefer section ops, or a small restart/beam) so the unified
     twelve-op search reaches ~16 on PV; re-run; then report one uniform search. More effort, uncertain payoff. (A
     cheap version Claude offered: run the twelve-op search *and* the app+sec subset, take the best -- that is
     Option 1 mechanically.)
   - **Broader-goal context:** the PV number is a presentation question, not a threat to a claim. The C4 soundness
     check is unaffected (0 either way). PV's *computed* hole (44.4% of its gain lowerable) is confirmed reachable by
     both 12 and 16 (both large majorities), so the headline point survives; only its force differs. The one thing to
     avoid is reporting 16->12 as if our "better" search got worse.
2. **Edit Table 7 and the adaptive prose** in `_f_evaluation.tex` once the PV cell is decided. Undisputed now: the
   unconstrained adaptive cell `8% -> 20%` (10/49), and the two monotone rows stay `0%` (confirmed under each row's own
   threat model). The prose already frames the 0.0 as an implementation check and the adaptive column as "our search";
   add that the check now covers all twelve operations. Reports: `artifacts/experiments/a1/adaptive-twelve/{mfull,madd}/adaptive.json`.
3. **Then items 9-11** (`PLAN.md`): (9) a detector on the hand table (*hypothesis:* the search, adding a section after
   the overlay, evades it on some in-population files); (10) the adversarial-training row, against item 8's search;
   (11) the expert set instrumented (`featuresets/ember2024/expert.py`).

State the hypothesis before each run, in a sentence or two.

## Deferred (user, 2026-11-03)

- **Routing to Table 7's sums rows (`--route <c4>=ref`).** `a1_adaptive.py` has no routing, and the engine predicts
  only in thrember space (the sums groups have no recognizers), so scoring a routed sums-model file needs a design
  decision. Bring back a concrete plan before touching Table 7's sums-row adaptive cells. (The resume prompt handed
  into session 4 asked to run item 8 on the routed 10%-store models; this is that piece, parked.)

## Notes

- **Runs:** only jobs under ~10 min yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script (next number 120), reading `NUM_WORKERS` when the script has a worker flag. `a1_adaptive.py` is
  single-process (no worker pool), so `run/119` sets OMP threads instead and notes NUM_WORKERS does not apply.
- Do not change the writers' output (`catalogue.write_*`): G7 (runs 107, 117, 118) and Table 5's edit counts depend on
  the same seeded edits.
- Untracked, leave alone: `papers/`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, `slides/`.
- Three test modules fail to collect for a pre-existing reason (`tests/test_shortcuts_*`); their scripts moved to
  `scripts/archive/`. Not caused by this session.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- Bib page ranges not verified: Incer et al., Chen et al. (CCS 2021), Simonetto et al. The related work the review
  found missing is listed in `docs/status.md` (the review's block); §6 must cover it.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
