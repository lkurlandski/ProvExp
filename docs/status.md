# Status

Last updated: 2026-10-07. Current phase: **Phase 2** (`docs/plan_phase2.md`).

## Done

- **Phase 0 (literature):** `docs/related_work.md`. Pullback ≈ G-DeepSHAP's rescale rule; novelty comes from
  provenance for program feature extractors, the null element/localizability, pushforward, and security findings.
- **Phase 1 (library):** `BoxMatrix`; `Provenance` with the null element (default), coverage κ, localizability ℓ,
  ambiguity, overlap (numba sweep, ~0.06 s median per file); the instrumented EMBER-2024 extractor (bit-identical to
  thrember on 45 fixtures); SimpleDB; MalConv medium (logits identical to MalConv2). Manuscript framework revised for
  the null element (Axiom 4, Definition of localizability).
- **Phase 2 so far (code written and tested, not yet run at scale):**
  - Feature store (`data/tabular.py`) and `scripts/featurize.py` (memory-mapped `X.npy` + `meta.parquet` per split,
    resumable, TLSH of the truncated bytes).
  - `models/gbdt.py`, `models/mlp.py`, `scripts/train_classic.py --learner {gbdt,mlp} --seed N`.
  - `explain/feature.py` (TreeSHAP path/interventional, KernelSHAP, IG, gradient×input) and `explain/problem.py`
    (MalConv IG with 256 steps; exact one-pass occlusion).
  - `data/tlsh.py` (greedy dedup), `scripts/select_explanation_set.py`, `scripts/build_metadata.py`,
    `scripts/check_features.py`.

## Running / waiting on the user

1. Done: `scripts/featurize.py` on all splits (0 failures), `build_metadata.py` (2,069,813 samples), and
   `check_features.py` on ts/vl/tr (`artifacts/reports/check_features_*.json`, results as expected; see Notes).
2. Next for the user: `select_explanation_set.py`, then `train_classic.py` (GBDT and MLP, seeds 0-2).

## Next (for Claude)

1. Settle the explanation-set TLSH threshold (see Notes), then check `artifacts/explanation_set/ts.parquet` and `artifacts/models/*/seed-*/metrics.json`. Expected test ROC-AUC near SSViT's
   on full-length features: GBDT 0.9979, MLP 0.9965 (MalConv medium: 0.9913).
2. Write `scripts/explain.py`: run every explainer on the explanation set (seed-0 models; SHAP background =
   1,000 balanced training samples, fixed; KernelSHAP with a small summarized background) and save one array per
   explainer. Smoke-test on a few samples, then hand the user the full command.
3. Phase 2 capstone, the pilot (`docs/plan_phase2.md` §2.6): coverage/localizability/H/O census by feature group,
   label, size, and packer; first byte-level pullback heatmaps; explainer agreement before vs. after pullback.
   Write `docs/pilot.md` with a go/no-go read on the top-tier framing.

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
