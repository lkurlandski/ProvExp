# Status

Last updated: 2026-10-08. Current stage: **E1 pilot complete** (level 2, level 3, KernelSHAP); **reassessment round
with the user** before deciding what comes next. Plan: `PLAN.md` (replanned 2026-10-07).

## Where we are

- Phases 0–2 are done: literature, the `provexp` library, features/models for EMBER-2024, stage-1 explanations, the
  census (`docs/pilot.md`).
- **Gate 1 (census):** passed for the measurement result.
- **Gate 2 (E1 pilot, `docs/e1_pilot.md`):** passed for the GBDT, not for the MLP; thresholds open.
  - GBDT: pullback coarsened to 256 windows = occlusion (0.97–1.03×) under all three operators and explainers, at
    1/135 of the cost. Byte level 1.79× occlusion (level 2) → 1.67× (level 3) → 1.65× (level 3, random fill), so most
    of the advantage survives typical header values. KernelSHAP matches TreeSHAP.
  - MLP: KernelSHAP beats IG by 0.02–0.19 but does not fix it (level 3: 0.85× bytes, 0.70× windows); the black-box
    pullback of the same explanations is as far behind, so the explanation, not P, is the bottleneck. Level 3 makes
    the fully ablated file strongly benign to the MLP (−8.2 vs. 1.5 at level 2).
  - The byte-level overshoot is **not** a header artifact (unchanged at level 3); proposed reading: signed rankings
    remove supporting bytes and keep opposing ones.

## Ran 2026-10-07 (all clean: 0 failures, 0 of 23,000 invalid points, no warnings)

KernelSHAP for the 100 E1 files (`kernelshap_{gbdt,mlp}.npy`, completeness ≤ 3e-14); E1 `zeros/`,
`zeros-typical-header/`, `random-typical-header/` in `artifacts/experiments/e1/seed-0/`.

## Next (for Claude), on resume

1. **Reassessment round with the user** (agenda at the end of `docs/e1_pilot.md`): Gate 2 thresholds; the headline
   claim (window-level parity vs. byte-level advantage); the overshoot reading; neural models in or out (or a
   feature-space deletion check for the MLP); level 2 or level 3 as the primary operator; what comes next (E1 at
   scale with more files and seeds 1–2, E2, E3). Do not start new experiments before this is discussed.

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
