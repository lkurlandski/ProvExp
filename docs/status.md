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

- **Protected-field discovery** (E1 operator, `docs/plan_e1.md`):
  `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 env/bin/python scripts/discover_protected_fields.py sweep --split tr --num_samples 2000 --num_workers 16`
  (~10 min), then `... check --explanation_set --num_workers 16` (~25 min). Smoke tests: 40 training files (layout
  fields break in every file; e_sp, BaseOfCode, FileAlignment in 1 of 40; one file with overlapping DOS/PE headers);
  200 test files checked with 0 broken ablations.
- **E1 pilot:** `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 env/bin/python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16`
  (zero fill; `--fill random` for the robustness variant). Smoke test on 4 files at K = 32: 0 failed verifications,
  curve endpoints exact.
- **Open questions** (details in `PLAN.md`): the summary statistics (decided by E2; candidates H_j / log|z| and
  dropping 1/(n' - 1) of O; do not change the manuscript before then).
- Known anomaly: interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11); reported by a
  `RuntimeWarning` in `treeshap_interventional`; E1 excludes those files.

## Next (for Claude)

1. After the discovery runs: add the fields breaking at least 1% of training files to `PROTECTED_FIELDS` (the layout
   fields are protected by definition; rare breakers are protected per file by `protect`).
2. After the E1 pilot: `scripts/e1_tables.py` and `docs/e1_pilot.md` (deletion/insertion AUC per method and model,
   pullback vs. random paired test, the 1% budget, cost, black-box vs. instrumented P per feature subset); Gate 2 read.
3. Then E1 at scale, E2, E3, KernelSHAP; A1-A3 are appendix-grade.

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
