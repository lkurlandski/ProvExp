# Status

Last updated: 2026-10-08. Current stage: **E1 pilot complete**; experiments continue **on the GBDT first** (the MLP
is set aside temporarily); **reassessment of the next steps with the user** before any new run. Plan: `PLAN.md`.

## Where we are

- Phases 0–2 are done: literature, the `provexp` library, features/models for EMBER-2024, stage-1 explanations, the
  census (`docs/pilot.md`).
- **Gate 1 (census):** passed for the measurement result.
- **Gate 2 (E1 pilot, `docs/e1_pilot.md`):** passed for the GBDT; thresholds open.
  - GBDT: pullback coarsened to 256 windows = occlusion (0.97–1.03×) under all three operators and explainers, at
    1/135 of the cost. Byte level 1.79× occlusion (level 2) → 1.67× (level 3) → 1.65× (level 3, random fill), so most
    of the advantage survives typical header values. KernelSHAP matches TreeSHAP.
  - The byte-level overshoot is **not** a header artifact (unchanged at level 3); proposed reading: signed rankings
    remove supporting bytes and keep opposing ones.
  - MLP (set aside temporarily, returns later): KernelSHAP beats IG by 0.02–0.19 but does not reach occlusion (level
    3: 0.85× bytes, 0.70× windows); the black-box pullback of the same explanations is as far behind, so the
    explanation, not P, is the bottleneck.

## Ran 2026-10-07 (all clean: 0 failures, 0 of 23,000 invalid points, no warnings)

KernelSHAP for the 100 E1 files (`kernelshap_{gbdt,mlp}.npy`, completeness ≤ 3e-14); E1 `zeros/`,
`zeros-typical-header/`, `random-typical-header/` in `artifacts/experiments/e1/seed-0/`.

## Next (for Claude), on resume

**Reassessment of the next steps with the user** (GBDT only). Do not start new experiments before it is discussed.
Open decisions, with Claude's recommendations:

1. **Primary operator:** level 3 (typical header values) primary, level 2 as robustness. For the GBDT the two differ
   little, and level 3 is the more realistic and more conservative one (it removes the small level-2 edge).
2. **Headline claim:** window-level parity with occlusion at 1/135 of the cost (equal granularity, robust) as the
   main claim; the byte-level advantage (1.65×) as a secondary result, shown against occlusion at several K.
3. **Gaps in E1 before scaling** (both are in `PLAN.md` but not in the pilot):
   - occlusion at several window counts (e.g., K = 64, 256, 1,024, 4,096) for the planned faithfulness-vs.-cost
     Pareto plot; it tests whether occlusion approaches the byte-level pullback as K grows, at what cost;
   - KernelSHAP over windows as a second direct problem-space baseline.
   Smoke-test both on a few files, then a pilot on the same 100 files.
4. **Overshoot:** test the signed-resolution reading cheaply with an unsigned ranking (|b|) on the existing files, or
   accept it as a stated interpretation.
5. **E1 at scale:** the 2,000-file explanation set, seeds 0–2, level 3 (level 2 on a subset). Estimated about 7 h per
   variant and seed on 16 workers (21 min per 100 files) plus KernelSHAP (about 1.6 h for 2,000 files); the user runs
   it.
6. **E2 design** (still open) and **E3** (planted trigger, GBDT retrains in minutes) after E1 at scale.
7. **The MLP** returns after the GBDT methodology is established (`PLAN.md`, "Second classifier: the MLP").

## Decisions made on 2026-10-08

- **The GBDT is the first classifier we experiment with.** The framework stays general-purpose (P does not depend on
  the classifier). Setting the MLP aside is temporary: it returns once the GBDT methodology is established, starting
  from the pilot's diagnosis (`PLAN.md`, "Model scope" and "Second classifier: the MLP").

## Decisions made on 2026-10-07 (see `PLAN.md` and the docs named)

- **Framework domain-agnostic; experiments may use domain knowledge selectively** (CLAUDE.md). Do not propose
  PE-structure analyses.
- **Plan:** three claims (faithful, cheap, self-characterizing) + a measurement; core experiments E1–E4; appendix
  A1 (MalConv vs. GBDT), A2 (cyclic error), A3 (mechanical redundancy). Manipulability dropped.
- **Statistics:** ambiguity and overlap *characterize P* (how sharply and separately an explanation can be placed);
  they were never meant to predict faithfulness. E2's design is open. Summaries saturate (normalized H ≈ 0.99,
  overall O ≈ 0.003); candidate mild fixes: H_j / log|z|, drop 1/(n' − 1) of O. Do not change the manuscript yet.
- **Localizability ℓ removed from the framework** (explanation-specific); coverage κ kept. ℓ stays an evaluation helper
  (`Provenance.localizability`).
- **Ambiguity/overlap exclude unattributable features** under the null policy (code and manuscript).
- **GBDT treats categorical features as numeric** (shap misencodes LightGBM categorical splits); ROC-AUC unchanged.
- **E1 operator:** level 2 = protect the layout fields (`LAYOUT_FIELDS`) plus fields that break each file (per-file
  sweep), zero everything else, header bytes never random; level 3 = header fields take typical values
  (`header_typical_values.json`). Every ablated file is verified at runtime. **Insertion dropped** (blank file far from
  real files; scattered bytes do not rebuild structures; explanations use another reference). K = 256 windows.
- **KernelSHAP:** 32,768 samples, a 16-sample balanced background, `l1_reg=False` (shap's default keeps ~10 features).

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); `treeshap_interventional` warns; E1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- Black-box vs. instrumented P agree exactly for additive feature groups and differ for non-additive ones (strings,
  entropy windows, hashed imports/exports; total variation 0.44–0.67). Occlusion cannot see zero or protected header
  bytes and creates fill artifacts (new entropy windows, pefile warnings).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.

## Documents

- `PLAN.md`: plan, claims, experiments, timeline, gates, open questions.
- `docs/pilot.md`: census (Gate 1). `docs/plan_e1.md` and `docs/e1_pilot.md`: E1 design and results (Gate 2).
- `docs/related_work.md`, `docs/design_provexp.md`, `docs/plan_phase2.md` (Phase 2, complete).
- Scripts: `explain.py` (stage-1 and KernelSHAP), `provenance_census.py`, `pullback_agreement.py`, `pilot_tables.py`,
  `discover_protected_fields.py`, `header_typical_values.py`, `faithfulness.py`, `e1_tables.py`.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- `data/tlsh.py` dedup is exact for any threshold.
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not yet explained.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
