# Status

Last updated: 2026-10-07. Current phase: **Phase 2** (`docs/plan_phase2.md`).

## Done

- **Phase 0 (literature):** `docs/related_work.md`. Pullback ≈ G-DeepSHAP's rescale rule; novelty comes from
  provenance for program feature extractors, the null element/localizability, pushforward, and security findings.
- **Phase 1 (library):** `BoxMatrix`; `Provenance` with the null element (default), coverage κ, localizability ℓ,
  ambiguity, overlap (numba sweep, ~0.06 s median per file); the instrumented EMBER-2024 extractor (bit-identical to
  thrember on 45 fixtures); SimpleDB; MalConv medium (logits identical to MalConv2). Manuscript framework revised for
  the null element (Axiom 4, Definition of localizability).
- **Phase 2, data and models (done 2026-10-07):**
  - Features for all splits (`artifacts/features/ember2024/{tr,vl,ts}`, 0 failures); released metadata
    (`artifacts/metadata/ember2024.parquet`); feature checks (`artifacts/reports/check_features_*.json`).
  - Explanation set: `artifacts/explanation_set/ts.parquet` (1,000 benign + 1,000 malware). TLSH dedup within each
    label at threshold 30, at most 10 per malware family, then a uniform sample per label (no size strata, so it is
    representative within each label; see `select_explanation_set.py`). The family cap leaves 45,943 malware
    candidates, so the malware half is family-balanced rather than following the test split.
  - GBDT and MLP, seeds 0-2 (`artifacts/models/{gbdt,mlp}/seed-N/`). Test ROC-AUC: GBDT 0.99759/0.99765/0.99763,
    MLP 0.99586/0.99551/0.99595, slightly below SSViT's full-length baselines (0.9979, 0.9965), as expected from
    truncation. The GBDT used all 500 trees (early stopping never triggered).
  - MalConv medium, seeds 0-2: `checkpoints/malconv-seed{0,1,2}.pt` (seed 0 is the released `malconv-medium.pt`).
  - Code: `explain/feature.py` (TreeSHAP path/interventional, KernelSHAP, IG, gradient×input), `explain/problem.py`
    (MalConv IG, exact one-pass occlusion), `data/tlsh.py` (exact greedy dedup for any threshold).

## Running / waiting on the user

- GBDT retrained with numeric categorical features (2026-10-07): test ROC-AUC 0.99759/0.99764/0.99763, identical to
  the categorical models to 1e-5. Old models in `artifacts/models/gbdt-categorical/`. shap 0.52 misencodes LightGBM
  categorical splits on categories above 53, so interventional TreeSHAP needs numeric splits.
- Run `scripts/explain.py --seed 0` (stage 1, a few minutes), then `scripts/provenance_census.py --seed 0` (about
  0.8 s/file median; a few minutes on 16 workers). Smoke tests on 20 files: completeness errors 6e-11 (TreeSHAP path),
  5e-5 (interventional), 8e-4 (IG, 4,096 steps); census 0 failures, features identical to the store.

## Next (for Claude)

The pilot is the go/no-go gate, and its core needs only cheap explainers, so it comes before the expensive ones.

1. The pilot (`docs/plan_phase2.md` §2.6) → `docs/pilot.md`, from `artifacts/explanations/ember2024/seed-0/census/`:
   census by feature subset, label, and size (number of elements); explanation-weighted ambiguity from the saved
   per-feature arrays; a handful of pullback heatmaps; agreement between explainers (top-k Jaccard, Spearman) before
   vs. after pullback (hypothesis (c)), which needs the pullbacks and so a separate pass over the files. Go/no-go read.
2. Stage 2 explainers, only after the pilot (hours, GPU): KernelSHAP (GBDT, MLP), MalConv IG and occlusion
   (pushforward, Phase 5). Seeds 1-2 only for robustness checks later.
3. Phase 3 prerequisites for the faithfulness evaluation. Hypothesis (b) in `PLAN.md` is still phrased in PE-format
   terms and is waiting on the user to reword it (see CLAUDE.md: the framework is domain-agnostic).

## Done this session (2026-10-07)

- `Provenance.select(S)` = P[:, S] (indices, mask, or names), via `BoxMatrix.select_columns`.
- Ambiguity and overlap exclude unattributable features by default (under "null" as under "ignore"); manuscript
  definitions and the nonoverlapping and pull-push theorems scoped to attributable features accordingly.
- Fixed the export provenance of ordinal-only exports (pefile omits `address_offset`).

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- `data/tlsh.py` dedup is now exact for any threshold (the SSViT version only searched length buckets within +/-2 and
  quartiles within +/-3, which is exhaustive only up to 36; above that it misses pairs, all at distance >= 36). Test
  split (539,882 hashes), single core: threshold 30 keeps 75.5% in 56 s; 60 keeps 52.9%; 100 keeps 30.5%; 200 keeps
  only 2,329 (0.4%), which is too aggressive for a stratified 2,000-sample set.
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not yet explained.
