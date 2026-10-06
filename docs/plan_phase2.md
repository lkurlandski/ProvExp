# Phase 2 Plan: Features, Models, and Explanations

Drafted 2026-10-06. Decisions marked **(D#)** are open; each has a recommendation.

## Where we stand

| Phase | Planned | Status |
|---|---|---|
| 0 Literature | weeks 1–2 | Done (week 1). Novelty strategy settled. |
| 1 Library | weeks 3–6 | Done (week 1). `BoxMatrix`, `Provenance` (null element, κ, ℓ, H, O), instrumented EMBER-2024 extractor, SimpleDB, MalConv. Manuscript framework revised. |
| 2 Features, models, explanations | weeks 5–7 | **This plan.** Target: done by ~2026-10-20. |
| 3 Problem-space baselines, perturbation, black-box provenance | weeks 7–9 | — |
| 4–5 Evaluations and applications | weeks 9–13 | — |
| 6 Writing | weeks 13–16 | Deadline late January 2027. |

We are about four weeks ahead of schedule. Recommendation: spend part of that slack on an **early pilot** of the
paper's central hypotheses as the capstone of Phase 2 (§2.6), instead of waiting for the planned week-6 checkpoint.

## Goal

Every ingredient needed to transfer real explanations of real models, at dataset scale:

1. EMBER v3 features recomputed on the 4,000,000-byte binaries for all of EMBER-2024 PE.
2. GBDT and MLP detectors trained on those features; MalConv medium (already loaded).
3. Feature-space explainers for the GBDT and MLP; problem-space explainers for MalConv.
4. A fixed explanation set of test files with explanations from every explainer.
5. A pilot: the localizability census and the first pulled-back explanations.

## 2.1 Featurization

**What.** `scripts/featurize.py`: SimpleDB shard → thrember v3 features (our extractor, `feature_vector` only, no
provenance) → npz shards in SSViT's tabular format (`names`, `labels`, `timestamps`, `features`). Parallel over
shards, resumable (skips finished shards), logs files that fail to extract.

**Cost.** ≈ 0.4–0.5 s per file without provenance → 2.88M files ≈ 5–6 hours on 64 cores. One-time.

**Sanity checks** (`scripts/check_features.py`):
- For files under 4,000,000 bytes, our vectors should equal the released EMBER-2024 features
  (`/shared/datasets/EMBER-2024-tabular`, via SSViT's npz shards). Mismatches mean environment drift (pefile,
  signify, scikit-learn) and must be explained.
- Report the number of truncated files and which features change because of truncation.

**(D1)** Featurize all of train (2.07M) or a subset? Recommendation: **all of it**, so the GBDT/MLP train on the same
files as MalConv. The cost is one overnight run.

## 2.2 Models

Copied and simplified from SSViT's `main_classic.py`:

- `models/gbdt.py`: `EMBER2024_LIGHTGBM_PARAMS` (500 trees, 64 leaves), the categorical feature indices,
  train/predict helpers. Early stopping on the validation split.
- `models/mlp.py`: the SOREL-style MLP (512-512-128, LayerNorm, ELU). **The feature standardization is a layer inside
  the model**, so gradient explanations are with respect to raw features, which is what the provenance refers to.
- `metrics.py`: `compute_metrics`.
- `data/tabular.py`: `load_datafile(s)`.
- `scripts/train_classic.py`: `--learner {gbdt,mlp} --seed`.

Acceptance: test ROC-AUC close to SSViT's baselines on full-length features (GBDT 0.9979, MLP 0.9965); a small drop
from truncation is expected and is reported.

**(D2)** Seeds. Recommendation: **one seed** for all explanation work; three seeds only for the performance table, later.

## 2.3 Feature-space explainers (GBDT, MLP)

`src/provexp/explain/` with one interface: `explain(model, X, **kwds) -> A`, shape (N, 2568), attributions for the
malware logit, for raw features.

| Explainer | GBDT | MLP | Notes |
|---|---|---|---|
| TreeSHAP, path-dependent | ✓ | | LightGBM `pred_contrib=True`: exact, fast, no extra dependency |
| TreeSHAP, interventional | ✓ | | `shap.TreeExplainer` with a background set |
| KernelSHAP | ✓ | ✓ | Model-agnostic; fixed sampling budget |
| Integrated Gradients | | ✓ | Own implementation (≈40 lines, tested for completeness); baseline = background mean |
| Gradient × input | | ✓ | Cheap, non-Shapley |
| DeepSHAP | | ✓ | `shap.DeepExplainer`, if it supports our torch version; otherwise dropped |

This gives at least three explainers per model, from different families. That backs the "explainer-agnostic" claim
and lets us engage with the SHAP-on-EMBER critique empirically.

**(D3)** SHAP background. Recommendation: 1,000 balanced training samples, fixed once. Path-dependent TreeSHAP needs
none, which gives a background-free reference.

## 2.4 Problem-space explainers (MalConv)

For the pushforward experiments, and as a preview of Phase 3:

- Integrated Gradients on the byte embeddings, summed over the embedding dimension → one attribution per byte.
- Occlusion over fixed windows (e.g., 512 bytes, matching MalConv's stride): replace with padding and measure the
  change in logit.

## 2.5 Explanation set

A fixed set of test files that every explainer explains, saved with its explanations (`npz`: names + one array per
explainer). Provenance is *not* stored; it is recomputed on demand (≈0.75 s/file).

**(D4)** Size and composition. Recommendation: **2,000 test files**, stratified by label × size bin (including
truncated files), plus the 45 fixtures. KernelSHAP is the expensive explainer; at a fixed budget this is a few hours.

## 2.6 Capstone: pilot of hypotheses (a) and (c)

Using GBDT + path-dependent TreeSHAP and the explanation set:

1. **Census** (hypothesis (a)): per file, coverage κ, ambiguity H and overlap O (overall and per feature group), and
   localizability ℓ(a) of the model's explanations. Distributions by label, size, packedness (by section entropy).
2. **First pullbacks:** byte-level heatmaps over PE structure for a handful of files (qualitative sanity check).
3. **Stability** (hypothesis (c)): agreement between explainers in feature space vs. after pullback.

Output: a short internal report (`docs/pilot.md`) with figures, and a go/no-go read on the top-tier framing.

## Deliverables and done criteria

- [ ] `scripts/featurize.py` run on all splits; sanity report written.
- [ ] GBDT and MLP trained; metrics within the expected range of SSViT's.
- [ ] `provexp.explain` with the explainers above, tested (completeness for IG/SHAP, agreement of TreeSHAP variants
      where theory says they agree).
- [ ] Explanation set and its explanations saved.
- [ ] Pilot report.

## Dependencies to add

`lightgbm`, `shap` (both resolve on Python 3.14). No `captum`: IG is short and easier to test ourselves.

## Risks

- **Environment drift** makes our features differ from the released ones (pefile/signify/sklearn versions). The
  sanity check in 2.1 catches this early; our models are trained on our features either way.
- **`shap` on Python 3.14 / numba 0.68** may have rough edges. Fallbacks: LightGBM's native TreeSHAP, our own
  KernelSHAP sampler.
- **Featurization failures** (thrember raising on malformed files) shrink the dataset. They are logged and counted;
  SSViT's MalConv evaluation used every file, so comparisons must use the intersection.
