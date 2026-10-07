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

- Retrain the GBDT (seeds 0-2) with the categorical features treated as numeric (`train_gbdt(categorical=False)`, now
  the default). shap 0.52 misencodes LightGBM categorical splits on categories above 53 (its trees were off by up to
  4.9 logits on the old model), so interventional TreeSHAP was silently wrong. The old models move to
  `artifacts/models/gbdt-categorical/`; the numeric GBDT is the GBDT of record for every result.
- Then `scripts/explain.py --seed 0` (stage 1). Smoke test on 20 files: completeness errors 5e-12 (TreeSHAP path),
  5e-5 (interventional, 1,000 background samples), 8e-4 (IG, 4,096 steps; 128 steps gave errors up to 3.6 logits).

## Next (for Claude)

The pilot is the go/no-go gate, and its core needs only cheap explainers, so it comes before the expensive ones.

1. ~~`Provenance.select`~~ done (2026-10-07): `Provenance.select(S)` = P[:, S] (indices, mask, or names) via
   `BoxMatrix.select_columns`. 0.04-0.7 s per EMBER group on a 4 MB file. Open question for the census: under
   `empty="null"`, a group whose features are all empty (e.g., exports of a file without exports) has O = 1 and H = 0
   because every empty feature shares the null element; report statistics with `empty="ignore"` next to κ?
2. `scripts/provenance_census.py`: per file, κ, H, O (overall and per feature subset) and ℓ(a) for each stage-1
   explanation, plus the null element's share of each pullback. Domain-agnostic: no PE-format structure (see
   CLAUDE.md). About 0.75 s/file, so ~25 min on one core for 2,000 files; parallel over files.
3. The pilot (`docs/plan_phase2.md` §2.6) → `docs/pilot.md`: census by feature subset, label, and size (number of
   elements); a handful of pullback heatmaps; agreement between explainers (top-k Jaccard, Spearman) before vs. after
   pullback (hypothesis (c)). Go/no-go read.
4. Stage 2 explainers, only after the pilot (hours, GPU): KernelSHAP (GBDT, MLP), MalConv IG and occlusion
   (pushforward, Phase 5). Seeds 1-2 only for robustness checks later.
5. Phase 3 prerequisites for hypothesis (b) and the faithfulness evaluation: validity-preserving region perturbation
   and a functionality-preserving attack setup (secml-malware) against the GBDT.

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
