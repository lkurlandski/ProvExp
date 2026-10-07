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

- Stage-1 explanations and the census are done and ran cleanly (`artifacts/explanations/ember2024/seed-0/`).
- **Run the pullback pass** (about 20 minutes on 16 workers):
  `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 env/bin/python scripts/pullback_agreement.py --seed 0 --num_workers 16`.
- **Open discussions with the user** (2026-10-07):
  - The ambiguity and overlap summaries saturate (pilot finding 4). The user wants a careful, mild intervention rather
    than a replacement; candidates are being discussed (normalizing H_j by log|z| instead of log|A_j|; dropping the
    1/(n' - 1) of O). Do not change the manuscript definitions until decided.
  - The user is not convinced that localizability ℓ and coverage κ belong in the manuscript where they are now
    (Definition after overlap, added in Phase 1 by Claude). Keep using them in the analysis; revisit placement later.
  - The experiment plan in `PLAN.md` needs another pass: the user does not see the value of the domain-agnostic
    manipulability experiment (hypothesis (b), Evaluation 8). The XAI methods may also be revisited later.
  - Known anomaly: interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11); now reported by a
    `RuntimeWarning` in `treeshap_interventional`.

## Next (for Claude)

1. After the pullback pass: finish `docs/pilot.md` (stability net of the permutation control, effective-support
   tables from `pullback/entropy.npy` and `support.npy`, heatmaps from `pullback/bins.npy`); final go/no-go.
2. Stage 2 explainers: KernelSHAP for the GBDT and MLP (a data-driven baseline for the MLP), then MalConv IG and
   occlusion for pushforward. Seeds 1-2 only for robustness later.
3. Phase 3: a black-box element perturbation operator; deletion/insertion faithfulness; black-box provenance
   estimation; then hypothesis (b) (manipulability, now domain-agnostic in `PLAN.md`).

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
