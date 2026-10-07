# Pilot: Localizability Census and First Pullbacks

Written 2026-10-07. Phase 2 capstone (`docs/plan_phase2.md` §2.6). **Status: census complete; the stability analysis
(hypothesis (c)), the effective-support tables, and the pullback heatmaps wait on `scripts/pullback_agreement.py`.**
Every number below is printed by `scripts/pilot_tables.py --seed 0`.

## Setup

- **Files:** the explanation set, 1,000 benign + 1,000 malware test files (TLSH-deduplicated, at most 10 per family).
- **Models (seed 0):** the GBDT (categorical features treated as numeric; test ROC-AUC 0.99759) and the MLP (0.99586).
- **Explainers (stage 1):** TreeSHAP path-dependent and interventional (GBDT; background of 1,000 balanced training
  samples), Integrated Gradients from the background mean (MLP, 4,096 steps), and gradient × input (MLP).
- **Census** (`scripts/provenance_census.py`): per file, coverage κ, ambiguity H, and overlap O for all features and
  for each feature subset (the groups of the feature set, by name prefix), each in isolation (`Provenance.select`),
  and the localizability ℓ(a) of every explanation. H and O average over attributable features only.

### Data quality

| explainer | median completeness error | p99 | max | files > 1e-3 |
|---|---|---|---|---|
| treeshap_path | 0.000 | 0.000 | 0.000 | 0 |
| treeshap_interventional | 0.000 | 0.000 | 0.113 | 2 |
| integrated_gradients | 0.000 | 0.002 | 0.007 | 33 |

- Interventional TreeSHAP is off by up to 0.11 logits on 2 files although shap's trees reproduce LightGBM exactly on
  them. Suspected cause (unconfirmed): shap 0.52's `dense_independent` keeps single-precision weights indexed as
  `n + max_depth * m`, which collide at n = max_depth, and a node stack of exactly `max_depth`; our trees reach depth
  37. These 2 files should be flagged in any analysis of that explainer.
- IG's error is at most 0.1% of the log-odds; acceptable.
- Census: 0 failures (after fixing the provenance of ordinal-only exports), median 0.48 s per file. 2 files differ from
  the feature store in 2 `pefilewarnings` features: the known hash-seed-dependent choice of warning pattern in
  thrember.

## Findings

### 1. Most features are unattributable in any given file, mostly because something is absent

Median over files (benign / malware):

| subset | features | coverage κ | ambiguity H | overlap O |
|---|---|---|---|---|
| all | 2568 | 0.31 / 0.30 | 0.987 / 0.988 | 0.004 / 0.003 |
| general | 7 | 0.86 / 0.86 | 0.33 / 0.33 | 0.07 / 0.07 |
| histogram | 256 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 |
| byteentropy | 256 | 0.63 / 0.66 | 0.99 / 0.99 | 0.00 / 0.00 |
| strings | 177 | 0.67 / 0.67 | 0.99 / 1.00 | 0.00 / 0.00 |
| header | 74 | 1.00 / 1.00 | 0.97 / 0.97 | 0.07 / 0.07 |
| section | 224 | 0.17 / 0.17 | 1.00 / 1.00 | 0.07 / 0.07 |
| imports | 1282 | 0.06 / 0.03 | 1.00 / 1.00 | 0.10 / 0.17 |
| exports | 129 | 0.00 / 0.00 | — | — |
| datadirectories | 34 | 0.94 / 0.94 | 1.00 / 1.00 | 0.00 / 0.00 |
| richheader | 33 | 0.21 / 0.12 | 1.00 / 1.00 | 0.02 / 0.01 |
| authenticode | 8 | 1.00 / 1.00 | 1.00 / 1.00 | 0.88 / 0.88 |
| pefilewarnings | 88 | 0.00 / 0.00 | — | — |

About 70% of the features of a typical file are unattributable. Two kinds must be told apart:

- **File-dependent (absence):** 2,352 features are attributable in some files and not in others (only 114 are
  attributable in every file), e.g., hashed buckets that no item of this file falls into, or counts of something the
  file lacks. Their value encodes an absence, which no element can show.
- **Never attributable (in any of the 2,000 files):** 102 features, 88 of them `pefilewarnings`. These are
  instrumentation gaps or constants, not properties of the data: the instrumented extractor records no provenance for
  pefile's warnings because pefile does not report which bytes caused them.

### 2. A fifth to a third of what the models rely on cannot be localized

Localizability ℓ(a), 10th / 50th / 90th percentile, and the mean share of attribution magnitude on unattributable
features:

| explainer | benign | malware | never-attributable | file-dependent | ρ(ℓ, size) |
|---|---|---|---|---|---|
| treeshap_path | 0.66 / 0.80 / 0.88 | 0.68 / 0.77 / 0.85 | 0.055 | 0.170 | 0.46 |
| treeshap_interventional | 0.63 / 0.80 / 0.89 | 0.66 / 0.77 / 0.86 | 0.048 | 0.182 | 0.47 |
| integrated_gradients | 0.40 / 0.59 / 0.85 | 0.46 / 0.58 / 0.72 | 0.033 | 0.372 | 0.45 |
| gradient_x_input | 0.87 / 0.95 / 0.99 | 0.86 / 0.93 / 0.98 | 0.069 | 0.000 | 0.08 |

- For the GBDT, about 22% of the attribution rests on unattributable features, most of it on absences (17–18%).
  Malware is slightly less localizable than benign software. Larger files are more localizable (ρ ≈ 0.46).
- For the MLP under IG, 37% rests on absences; 47% of IG's mass is on the import features, almost all on empty
  buckets.
- The largest single source of non-localizable attribution for every explainer except gradient × input is one
  never-attributable feature, the pefile warning "Suspicious flags set for section" (mean |a| 0.71 for path TreeSHAP;
  2.37 for IG). Instrumenting it would shift roughly 5% of the GBDT's attribution from the null element into the file.
- Localizability ranks files consistently across explainers of the same model (ρ = 0.99 between the TreeSHAP
  variants, 0.76 between TreeSHAP and IG) but not with gradient × input (ρ ≈ 0.5).

### 3. Localizability depends on the explainer's baseline

Gradient × input gives no attribution to file-dependent unattributable features (share 0.000) because their value is
zero and its implicit baseline is zero: an explainer with a zero baseline cannot credit an absence. Its high ℓ is a
property of the explainer, not of the model. The same holds for any explanation that is linear in x − 0 (occlusion
with zeros, for instance). The paper should report ℓ per explainer and state this explicitly; explainers with a
data-driven baseline (interventional TreeSHAP, IG from the mean, KernelSHAP) are the ones that measure reliance on
absence.

### 4. The overall ambiguity and overlap summaries saturate

Normalized ambiguity is 0.97–1.00 for every subset with attributable features, and the overall overlap of all
features is 0.003. Neither distinguishes subsets, labels, or files:

- Ĥ_j = H_j / log|A_j| measures how *uniform* a feature's provenance is within its own support, not how *large* that
  support is. A header field spread uniformly over 4 bytes and a byte histogram spread over 4 MB both score 1.
- O divides by n′ − 1 (about 800 attributable features), so a feature that overlaps heavily with a handful of others
  contributes almost nothing.

The summaries remain correct for the theorems (H = 0 and O = 0 are exact characterizations), but they are not useful
as measurements. Proposed replacements, to be computed from the pullback pass (which saves the raw H_j and |A_j|):

- **Effective support** exp(H_j), in elements and as a fraction of the input, per feature and per subset; and the
  **explanation-weighted effective support** Σ_j |a_j| exp(H_j) / Σ_j |a_j| over attributable j, i.e., how many
  elements one unit of a decision's attribution is spread over.
- For overlap, the mean intersection I_{j,k} over the pairs of features that an explanation actually uses, rather
  than over all pairs.

This is a decision for the manuscript (Definitions of ambiguity and overlap), not just for the report.

### 5. The two models rely on different parts of the feature set

Mean share of attribution magnitude per subset:

| explainer | general | histogram | byteentropy | strings | header | section | imports | exports | datadirectories | richheader | authenticode | pefilewarnings |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| treeshap_path | 0.007 | 0.109 | 0.063 | 0.161 | 0.185 | 0.112 | 0.125 | 0.006 | 0.127 | 0.020 | 0.033 | 0.053 |
| treeshap_interventional | 0.008 | 0.114 | 0.064 | 0.167 | 0.176 | 0.120 | 0.136 | 0.006 | 0.118 | 0.019 | 0.025 | 0.047 |
| integrated_gradients | 0.006 | 0.130 | 0.084 | 0.080 | 0.057 | 0.089 | 0.472 | 0.021 | 0.014 | 0.001 | 0.018 | 0.030 |
| gradient_x_input | 0.086 | 0.204 | 0.074 | 0.142 | 0.160 | 0.102 | 0.177 | 0.015 | 0.011 | 0.000 | 0.011 | 0.018 |

The GBDT spreads its reliance over many subsets; the MLP (under IG) concentrates on the hashed import features.

## Stability (hypothesis (c)): pending

`scripts/pullback_agreement.py` compares every pair of explainers on each file in feature space and after pullback
(Spearman, cosine, weighted Jaccard of magnitudes), with a control that permutes the features of one explanation
before pulling it back. Smoke test on 24 files (not conclusive):

| space | control | Spearman | cosine | weighted Jaccard |
|---|---|---|---|---|
| feature | no | 0.12 | 0.27 | 0.18 |
| feature | permuted | 0.00 | 0.00 | 0.07 |
| problem | no | 0.17 | 0.31 | 0.27 |
| problem | permuted | 0.01 | 0.07 | 0.12 |

Agreement rises after pullback, but so does the agreement of unrelated explanations, because the pullback spreads
every explanation over the same elements. Hypothesis (c) has to be judged by the gain over the control, not by the
raw increase.

## Go/no-go (preliminary)

- **(a) Measurement: provisional go.** Findings 1–3 are substantive and security-relevant: a fifth to a third of what
  production-style detectors rely on is the absence of something, which no explanation over the input can show, and
  how much of it an explainer reveals depends on its baseline. What is missing is the "how sharply" half (effective
  support, finding 4) and the heatmaps; both come from the pullback pass.
- **(c) Stability: open.** Decided by the full agreement run, net of the permutation control.
- **(b) Manipulability: not yet tested** (Phase 3 needs a black-box perturbation operator).

## Next steps

1. **Run the pullback pass** (about 40 minutes on 8 workers, or 20 on 16):
   `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 env/bin/python scripts/pullback_agreement.py --seed 0 --num_workers 16`.
   Then finish this report: stability net of the control, effective-support tables, heatmaps from the binned
   pullbacks.
2. **Decide the ambiguity/overlap summaries** for the manuscript (finding 4).
3. **Decide whether to instrument the top pefile warnings** (finding 2). This is instrumentation of the feature
   extractor, like every other group, and moves about 5% of the GBDT's attribution out of the null element.
4. **Interventional TreeSHAP outliers:** flag the 2 files, or retrain the GBDT with a depth limit if more appear in
   other seeds.
5. **Stage 2 explainers:** KernelSHAP for both models (a data-driven baseline for the MLP, which the gradient
   explainers lack), then MalConv IG and occlusion for pushforward.
6. **Phase 3:** a black-box element perturbation operator; deletion/insertion faithfulness of pullbacks vs. direct
   problem-space explainers; black-box provenance estimation to validate the instrumented P; then hypothesis (b).
