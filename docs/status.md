# Status

Last updated: 2026-10-09 (PB2/PF2 pilot read; PF1 design in discussion). The evaluation mirrors the framework (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Old IDs E1–E4 / A1–A3 survive only in pre-2026-10-08 docs and
in artifact paths (`artifacts/experiments/e1/` holds PB1). Work stays at pilot scale (~100 files, one seed).
`run/` holds the commands that produced everything in `artifacts/`; add a script there for every new experiment.

## Where we are

| | state |
|---|---|
| **CP** (characterizing P) | **done** at 2,000 files (`docs/cp_census.md`) plus coarsening on the pilot files. Remaining: instrumented vs. black-box P at window level, which `faithfulness.py` now saves. |
| **PB1** (pullback faithfulness and cost) | **done** at pilot scale, baselines included (`docs/pb1_pilot.md`). Gate 2 passed for the GBDT. |
| **PB2, PF2** (planted trigger) | **done at pilot scale** (50 files per trigger; `docs/trigger_plan.md`, "Pilot-scale results"). Struct: precision at \|T\| = 1 on 50/50 files. Content: 0.94 on the typical file, failing exactly where P says it must. PF2 reads r as a support (decided 2026-10-09; tables updated). |
| **PF1** (pushforward faithfulness) | **designed with the user 2026-10-09** (`docs/pf1_plan.md`), not built. `faithfulness.py` now saves the window scores (`window_scores.npz`); **waiting on the user's re-run** (`run/17_pf1_window_scores.sh`). |
| **CM** (GBDT vs. MalConv) | designed, not built; MalConv explanations of the pilot files are not computed yet. |
| **The MLP** | set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | framework and evaluation sections follow the current structure; `_d_applications.tex` carries the designs and pilot numbers. Do not try to compile it (no LaTeX here). |

## The session's results

- **PB1 baselines** (6.1 h, healthy, the pilot's 13,000 shared curve points reproduced exactly). **Occlusion
  saturates at 1.10** and never approaches the byte-level pullback's 1.67 (80–81/100 files, p ≈ 1e-12); parity holds
  at 64, 256, and 1,024 windows and the pullback *leads* at 4,096; KernelSHAP over windows matches the best occlusion
  at 1,925 extractions; the **overshoot** is explained (unsigned ranking removes three quarters, the rest grows with
  resolution in every method family).
- **The trigger testbed.** The struct trigger (3 header fields, 6 bytes) passes everything: attack success 1.000,
  +16.7 log-odds, clean ROC unchanged, fires on all 1,000 explanation-set malware files. The content trigger reaches
  only 0.472, because **a content trigger's effect scales with its share of the file** (0.92 below 50 KB, 0.29 above
  1 MB) while the struct trigger is at 1.000 at every size.
- **PB2/PF2 first results** (6 files, struct): the **6 top-ranked bytes of 614,000 are exactly the trigger's**, for
  all three explainers (the "77% of the ceiling" read here was wrong: corrected 2026-10-09), while any window-level method is bounded analytically
  at 0.0027 precision. Every explainer's top feature of 2,568 is one the trigger touches.
- **The runner's parallelism was rebuilt** to split one file's work (a single file was 4.1 h of the 6.1 h run), giving
  about 1.1 h on 64 workers against 4.1 h before at any worker count. Verified bit-exact against the baselines run
  and pinned by `tests/test_faithfulness.py`, whose tests were themselves checked against two injected bugs.

## When run 17 finishes (`run/17_pf1_window_scores.sh`, started 2026-10-09 ~08:00, 32 workers, ~2-2.3 h)

**What it is for.** It re-runs the PB1 baselines configuration (same 100 files, level-3 operator, occlusion at
64/256/1,024/4,096 windows, KernelSHAP over 256 windows at 2,048 coalitions) only to obtain what the first run did
not save: `window_scores.npz`, every direct problem-space explanation's per-window scores plus the features of the
original file (x) and the fully ablated file (x̃). These are PF1's inputs: the explanations to push forward, and x̃ as
the reference matched to the problem space. Nothing in PB1 changes; the curves are a by-product.
Output: `artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores/`; log:
`artifacts/logs/faithfulness-seed0-zeros-typical-baselines-scores.log` (its progress bar counts tasks, which run
longest-first, so its ETA was pessimistic; the fix came after the run started).

**Checks, in order, and what each outcome means:**
1. *Did it finish?* The log ends with the summary JSON; `status` should be 100 `ok` (or the same failures as the
   baselines run). Failed or timed-out files → note which; PF1 runs on the files that are `ok` in both runs.
2. *Is it the same run?* `curves.parquet` must equal the baselines run's
   (`zeros-typical-header-baselines/curves.parquet`) point for point (max difference 0.0; the runner is
   deterministic and was verified bit-exact on 2026-10-08). **Equal** → the saved window scores are the very ones
   behind PB1's published numbers, and PF1 can use them. **Not equal** → stop: something non-deterministic or a
   regression in today's change; find it before any PF1 result is trusted.
3. *Are the inputs complete?* `load_window_scores` gives one entry per `ok` file with `edges`, `occlusion:gbdt`,
   `occlusion_k{64,1024,4096}:gbdt`, `kernelshap_windows:gbdt`, `x`, `x_ablated`. `x` must equal the feature store's
   row for the file. `x_ablated` is NaN where the fully ablated file failed verification (`fully_ablated_valid`);
   those files drop out of the matched-reference analysis only (count them).

**Then:** run the PF1 analysis, `run/18_pf1.sh` (built and smoke-tested; a few minutes) and read it against the criterion fixed in advance (decision 5):
first, is the pushforward significantly above random and the naive incidence sum (if not, claim 3 fails); then
R = area(pushforward) / area(TreeSHAP) under the matched reference (≥ 0.8 faithful; 0.5-0.8 partial, gap to be traced
to null mass and overlap; < 0.5 claim 3 weakened, rethink with the user).

## Next (for Claude), on resume

1. ~~Read the pilot-scale PB2/PF2 results~~ done 2026-10-09 (`docs/trigger_plan.md`), and the follow-ups in
   `trigger_tables.py` (round trip renamed, true bound added, PF2 under the support reading) are done and re-run.
2. **PF1** (the pushforward's faithfulness): the one experiment with no evidence yet, and claim 3 rests on it. Design
   it with the user first — designed 2026-10-09 (`docs/pf1_plan.md`). `faithfulness.py` now writes
   `window_scores.npz` (per-window occlusion at every window count, KernelSHAP over windows, x and the fully ablated
   file's features; `load_window_scores`). Next: check the user's `run/17_pf1_window_scores.sh` run (its curves
   should equal the baselines run's exactly), then build the PF1 script (success criterion fixed: `docs/pf1_plan.md`, decision 5).
3. **CP's black-box comparison** (cheap: the window-level statistics of both provenances are already saved by any new
   `faithfulness.py` run).
4. **CM**, which needs MalConv explanations of the pilot files first.

## Decisions made on 2026-10-09

- **PF1 design** as in `docs/pf1_plan.md` (two references, attributable-only variant, naive incidence-sum baseline,
  success criterion fixed in advance: beat random and the naive baseline, then R = area ratio to TreeSHAP with cut-offs 0.8 / 0.5). No pushforward of triggered files.
- **PF2 reads r = ψ(1_T) as a support, not a target:** mass on supp(r) and top-k in supp(r); cosine and Spearman
  against r dropped as faithfulness scores (manuscript, PLAN, `docs/trigger_plan.md`).

## Decisions made on 2026-10-08

- **Evaluation structure and IDs** as above (user's proposal; CM promoted from the appendix; localizability to the
  appendix, forward-referenced from the pullback section).
- **Pilot scale:** 80–90% of the research on the ~100-file pilot subset (one seed) before scaling; PB1 at scale is
  paused.
- **CP:** ambiguity = entropy with effective support, overlap = 1 − M_jj, round-trip bounds, coarsening proposition
  (all in the manuscript); the spectrum is for our own insight; resolution after the baselines.
- **PB1:** level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary;
  baselines pilot (occlusion sweep, KernelSHAP over windows, unsigned ranking) before PB1 at scale.
- **The GBDT is the first classifier we experiment with.** The framework stays general-purpose (P does not depend on
  the classifier). Setting the MLP aside is temporary: it returns once the GBDT methodology is established, starting
  from the pilot's diagnosis (`PLAN.md`, "Model scope" and "Second classifier: the MLP").

## Decisions made on 2026-10-07 (see `PLAN.md` and the docs named)

- **Framework domain-agnostic; experiments may use domain knowledge selectively** (CLAUDE.md). Do not propose
  PE-structure analyses.
- **Plan (superseded 2026-10-08):** three claims + a measurement; core experiments E1–E4, appendix A1–A3.
  Manipulability dropped.
- **Statistics:** ambiguity and overlap *characterize P* (how sharply and separately an explanation can be placed);
  they were never meant to predict faithfulness. (The saturating definitions were replaced on 2026-10-08; see above.)
- **Localizability ℓ removed from the framework** (explanation-specific); coverage κ kept. ℓ stays an evaluation helper
  (`Provenance.localizability`).
- **Ambiguity/overlap exclude unattributable features** under the null policy (code and manuscript).
- **GBDT treats categorical features as numeric** (shap misencodes LightGBM categorical splits); ROC-AUC unchanged.
- **PB1 operator:** level 2 = protect the layout fields (`LAYOUT_FIELDS`) plus fields that break each file (per-file
  sweep), zero everything else, header bytes never random; level 3 = header fields take typical values
  (`header_typical_values.json`). Every ablated file is verified at runtime. **Insertion dropped** (blank file far from
  real files; scattered bytes do not rebuild structures; explanations use another reference). K = 256 windows.
- **KernelSHAP:** 32,768 samples, a 16-sample balanced background, `l1_reg=False` (shap's default keeps ~10 features).

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); `treeshap_interventional` warns; PB1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- Black-box vs. instrumented P agree exactly for additive feature groups and differ for non-additive ones (strings,
  entropy windows, hashed imports/exports; total variation 0.44–0.67). Occlusion cannot see zero or protected header
  bytes and creates fill artifacts (new entropy windows, pefile warnings).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.

## Documents

- `PLAN.md`: plan, claims, experiments, timeline, gates, open questions.
- `docs/pilot.md`: census (Gate 1). `docs/pb1_plan.md` and `docs/pb1_pilot.md`: PB1 design and results (Gate 2).
- `docs/related_work.md`, `docs/design_provexp.md`, `docs/plan_phase2.md` (Phase 2, complete).
- Scripts: `explain.py` (stage-1 and KernelSHAP), `provenance_census.py`, `pullback_agreement.py`, `pilot_tables.py`,
  `discover_protected_fields.py`, `header_typical_values.py`, `faithfulness.py`, `pb1_tables.py`.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- `data/tlsh.py` dedup is exact for any threshold.
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not yet explained.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
