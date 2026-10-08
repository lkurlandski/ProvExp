# Status

Last updated: 2026-10-08. The evaluation is **reorganized to mirror the framework** (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Old IDs E1–E4 / A1–A3 survive only in pre-2026-10-08 docs and in
artifact paths (`artifacts/experiments/e1/` holds PB1). Work stays at pilot scale (~100 files, one seed).

## Where we are

- Phases 0–2 are done (literature, `provexp`, features and models, census). Gate 1 passed; Gate 2 (PB1 pilot,
  `docs/pb1_pilot.md`) passed for the GBDT.
- **CP:** done on 2,000 files (`docs/cp_census.md`) and coarsening on the pilot files; revised definitions in code,
  tests, docs, and manuscript (`docs/cp_plan.md`). Remaining: instrumented vs. black-box P at window level.
- **PB1:** pilot done (parity with occlusion at 256 windows, 1/135 of the cost; bytes 1.65–1.79×). The baselines pilot
  is running (below).
- **PB2, PF2 (planted trigger), PF1 (pushforward faithfulness), CM (GBDT vs. MalConv):** designs to write.
- **Manuscript:** `_d_applications.tex` ("Evaluation on Malware Detection") follows the new structure (setup with the
  perturbation operator and the trigger testbed; CP; pullback with PB1, PB2, and a pointer to Appendix D; pushforward
  with PF1, PF2; CM; threats). Appendix D (localizability) and E (redundancy, placeholder) added.

## PB1 baselines: done and read (2026-10-08)

6.1 h on 16 workers, healthy (0 failures, 0 of 29,000 invalid points, the pilot's 13,000 shared points reproduced
exactly). All three pre-registered questions answered (`docs/pb1_pilot.md`, "Baselines"):

1. **Occlusion saturates at 1.10** and never approaches the byte-level pullback's 1.67 (80–81/100 files, p ≈ 1e-12):
   4,096 windows (4,098 extractions, 5.4 min/file) buy nothing over 1,024. The secondary claim is stronger than the
   pilot suggested.
2. **Parity holds at every granularity** (64, 256, 1,024: p ≥ 0.54) and the pullback *leads* at 4,096 (1.22 vs. 1.10,
   p = 0.004), so the main claim does not depend on the window count. **KernelSHAP over windows** matches the best
   occlusion (1.10) at 1,925 extractions, so it is the strongest direct baseline to state the claim against.
3. **The overshoot reading is confirmed:** unsigned ranking removes three quarters of it (3.49 → 0.92, 82/100 files),
   and the remainder grows monotonically with resolution in *every* method family, occlusion included.

Also rebuilt the runner's parallelism and reporting (`docs/pb1_plan.md`, "Cost and progress reporting"). The 4.1 h
task of that 6.1 h run was a *single file*, so across-file parallelism was capped no matter the worker count; the work
of a file is now split over two passes (the sweep in chunks of windows and KernelSHAP, then the rest per file).
Projected 4.0 h on 16 workers and **1.1 h on 64** (ideal 1.0), against 4.1 h before at any worker count, so **use
`--num_workers 48`–`64` from now on**. Verified bit-exact against the baselines run (max difference 0.0, every method,
both fills). It also predicts its cost up front and logs each file as it finishes.

## Next (for Claude), on resume

1. ~~Restructure the manuscript's evaluation section~~ done; the user reviews it.
2. When the baselines finish: answer the three questions (`docs/pb1_baselines.md`), update `docs/pb1_pilot.md`.
3. **Planted-trigger testbed (PB2, PF2):** designed and implemented (`docs/trigger_plan.md`, "Implementation
   status"); smoke-tested. **Waiting on the user to run** the poisoning and retraining of the struct trigger first
   (about 10–20 min + 3 min each):

       PYTHONHASHSEED=0 python scripts/trigger_poison.py --trigger struct --rate 0.01 --num_workers 16 \
         &> artifacts/logs/trigger_poison-struct.log
       python scripts/train_classic.py --learner gbdt --seed 0 --poison artifacts/poison/struct \
         &> artifacts/logs/train_classic-gbdt-0-struct.log
       PYTHONHASHSEED=0 python scripts/trigger_validate.py --poison artifacts/poison/struct --num_workers 16 \
         &> artifacts/logs/trigger_validate-struct.log

   Then the same with `--trigger content --content marker` (name `content-marker`). Validation must show attack
   success ≥ 95%, clean ROC-AUC within 0.001 of 0.99759, and the trigger inert on the clean model; if the content
   trigger is not learned, pilot another block kind or a larger block (`--content random|constant`, `--block_size`).
   Still to write: the PB2/PF2 metrics script (`trigger_tables.py`) and explanations of triggered test files.
   Then PF1; then CM (MalConv explanations not computed yet).
4. The MLP returns after the GBDT methodology is established (`PLAN.md`, "Second classifier: the MLP").

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
