# Status

Last updated: 2026-10-06 (end of session). Current phase: **Phase 2** (`docs/plan_phase2.md`).

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

1. `scripts/featurize.py` started 2026-10-06 in the user's tmux, apparently with ~16 workers (estimated ~17 hours
   for all splits; order ts, vl, tr). Check: `ls artifacts/features/ember2024/{ts,vl,tr}/parts | wc -l`, or whether
   `meta.parquet` exists in each split directory.
2. The user plans to run, in order:
   ```bash
   env/bin/python scripts/build_metadata.py --num_workers 16              # any time
   env/bin/python scripts/check_features.py --split ts                    # after ts finishes
   env/bin/python scripts/select_explanation_set.py --num_samples 2000    # after ts finishes (and ideally the metadata)
   for s in 0 1 2; do env/bin/python scripts/train_classic.py --learner gbdt --seed $s; done                    # after all splits
   for s in 0 1 2; do env/bin/python scripts/train_classic.py --learner mlp --seed $s --device cuda:0; done     # after all splits
   ```

## Next (for Claude)

1. Check the outputs of the steps above: `artifacts/reports/check_features_ts.json`,
   `artifacts/explanation_set/ts.json`, `artifacts/models/*/seed-*/metrics.json`. Expected test ROC-AUC near SSViT's
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
