# Status

Last updated: 2026-10-07. Current stage: **finishing the pilot, then the E1 pilot (Gate 2)**; see `PLAN.md`
(replanned 2026-10-07 around claims, core experiments E1-E4, appendix A1-A3, and gates).

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

Finishing E1 (decided 2026-10-07: insertion dropped; level-3 header operator; KernelSHAP to diagnose the MLP). Run in
order (each E1 run ~25 min on 16 workers):

1. KernelSHAP for the 100 E1 files (~15 min):
   `OMP_NUM_THREADS=1 env/bin/python scripts/explain.py --explainers kernelshap_gbdt kernelshap_mlp --subset artifacts/experiments/e1/seed-0/zeros/files.parquet --workers 16`
2. `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 env/bin/python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16`
   (level 2, now with KernelSHAP; overwrites `zeros/`), then the same with `--header typical` (level 3, writes
   `zeros-typical-header/`) and with `--fill random --header typical` (writes `random-typical-header/`).

## Next (for Claude)

1. Refresh `docs/e1_pilot.md`: level 2 vs. level 3 (how much of the byte-level advantage survives typical header
   values), KernelSHAP vs. IG for the MLP (and KernelSHAP for the GBDT), deletion only.
2. Then the reassessment round the user asked for, before deciding what comes after E1 (E1 at scale, seeds 1-2).
3. E2 needs a new design: ambiguity and overlap characterize P (how sharply and separately an explanation can be
   placed), they were never meant to predict faithfulness (user, 2026-10-07; `PLAN.md` corrected).

## Done (2026-10-07, evening)

- Protected-field discovery: the layout fields are the global protected set; other breakers are rare (≤ 0.35% of
  2,000 training files) and handled per file; 0 broken ablations on the 2,000 held-out files.
- E1 pilot (`docs/e1_pilot.md`): Gate 2 passed for the GBDT (window-level pullback = occlusion at 1/130 of the cost;
  byte-level 1.8× occlusion, partly fill artifacts in header fields); partial for the MLP (deletion on par,
  insertion fails). Black-box estimator bug found and fixed (rerun pending).

## Done (2026-10-07, later)

- Pilot census (`docs/pilot.md`, numbers from `scripts/pilot_tables.py`): κ ≈ 0.30; 17-37% of attribution on
  file-dependent absence features, about 5% on never-attributable ones (mostly pefile warnings); gradient × input
  cannot credit absences (zero baseline); normalized H (≈ 0.99) and overall O (≈ 0.003) saturate.
- `PLAN.md` made domain-agnostic (hypothesis (b) and Evaluation 8 rephrased over elements).
- Completeness: interventional TreeSHAP off by up to 0.11 on 2 files (suspected shap deep-tree bug; trees reach depth
  37); IG max 0.0074.

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
