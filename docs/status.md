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

## Running (started by the user on 2026-10-08)

**The E1 baselines pilot** (about 4.8 h; `artifacts/logs/faithfulness-seed0-zeros-typical-baselines.log`). When it
finishes, **read `docs/e1_baselines.md` first**: what the run tests, the health checks, the three questions, and what
each outcome means (written before the results).

## Next (for Claude), on resume

Agreed with the user on 2026-10-08: the sequence below; level 3 is the primary operator (level 2 robustness); the
main claim is window-level parity with occlusion at 1/135 of the cost, the byte-level advantage secondary; the
unsigned ranking tests the overshoot reading.

1. ~~Settle the operator and the headline~~ done (above).
2. **Baselines pilot (running; see `docs/e1_baselines.md`):** `scripts/faithfulness.py` now has `--classifiers` (default
   GBDT), `--sweep_windows` (occlusion and the coarsened pullback at more window counts), `--kernelshap_samples`
   (KernelSHAP over the 256 windows), the unsigned ranking `pullback_abs:*`, `--tag`, and `--files` (reuse an earlier
   run's files). Smoke test on 4 pilot files (`zeros-typical-header-smoke/`): clean, and every shared curve point
   reproduces the pilot exactly. Estimated about 4.8 h wall-clock on 16 workers (the slowest, 4 MB file sets it;
   71 worker-hours), so the per-file timeout is raised:

       PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 \
         --header typical --sweep_windows 64 1024 4096 --kernelshap_samples 2048 --timeout 28800 --tag baselines \
         --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
         &> artifacts/logs/faithfulness-seed0-zeros-typical-baselines.log

   Then `python scripts/e1_tables.py --fill zeros-typical-header-baselines` (new tables: overshoot, cost vs.
   faithfulness). Questions: does occlusion approach the byte-level pullback as K grows, and at what cost; does
   KernelSHAP over windows beat occlusion; does the unsigned ranking remove the overshoot (signed-resolution reading)?
   Note for scale: K = 4,096 on all 2,000 files would cost about 1,400 worker-hours; decide on a subset then.
3. **E1 at scale:** the 2,000-file explanation set, seeds 0–2, level 3 (level 2 on a subset). Estimated about 7 h per
   variant and seed on 16 workers (21 min per 100 files) plus KernelSHAP (about 1.6 h for 2,000 files); the user runs
   it.
4. **E2:** direction agreed 2026-10-08 (`docs/plan_e2.md`): round-trip statistics (M = PᵀD†P, N = PPᵀD†),
   effective support, coverage on both sides, resolution at granularity w. M_jj does not saturate (100-file check).
   Waiting on the user's decisions in `docs/plan_e2.md` ("Open decisions"); then implement in `provenance.py` with
   property-based tests. **E3** (planted trigger, GBDT retrains in minutes) after E1 at scale.
5. **The MLP** returns after the GBDT methodology is established (`PLAN.md`, "Second classifier: the MLP").

## Decisions made on 2026-10-08

- **E1:** level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary;
  baselines pilot (occlusion sweep, KernelSHAP over windows, unsigned ranking) before E1 at scale.
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
