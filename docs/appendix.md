# Appendix Results: Localizability (App-L) and Mechanical Redundancy (App-R)

Moved here on 2026-10-09 from the old pilot census report (in git history, which has the full tables and
the data-quality notes). All 2,000 files of the explanation set, seed 0, printed by `scripts/pilot_tables.py --seed 0`.
Localizability ℓ(a) is an evaluation metric here, not part of the framework: the share of an explanation's magnitude
on attributable features, which the pullback places in the file rather than on the null element.

> **Status (user, 2026-10-09): a limitation, not a finding.** Localizability, coverage, and the null element's share
> are not contributions and are not to be promoted. They measure one explanation of one file by one explainer, not
> the provenance, and a large unattributable share reflects a limitation of the provenance extraction pipeline
> (features whose bytes it cannot name), not a broad finding about detectors. App-L is kept only to state that
> limitation.

## App-L. A fifth to a third of what the models rely on cannot be localized

**Most features are unattributable in a given file, mostly because something is absent.** About 70% of a typical
file's features have no provenance. Two kinds:
- *File-dependent (absence):* 2,352 features are attributable in some files and not in others (only 114 in every
  file), e.g., hashed buckets nothing falls into, or counts of something the file lacks. Their value encodes an
  absence, which no element can show.
- *Never attributable:* 102 features, 88 of them `pefilewarnings` (pefile does not report which bytes caused a
  warning). Instrumentation gaps or constants, not properties of the data.

**Localizability per explainer** (10th / 50th / 90th percentile; mean share of |a| on unattributable features):

| explainer | benign | malware | never-attributable | file-dependent | ρ(ℓ, size) |
|---|---|---|---|---|---|
| TreeSHAP path | 0.66 / 0.80 / 0.88 | 0.68 / 0.77 / 0.85 | 0.055 | 0.170 | 0.46 |
| TreeSHAP interventional | 0.63 / 0.80 / 0.89 | 0.66 / 0.77 / 0.86 | 0.048 | 0.182 | 0.47 |
| Integrated Gradients (MLP) | 0.40 / 0.59 / 0.85 | 0.46 / 0.58 / 0.72 | 0.033 | 0.372 | 0.45 |
| gradient × input (MLP) | 0.87 / 0.95 / 0.99 | 0.86 / 0.93 / 0.98 | 0.069 | 0.000 | 0.08 |

- For the GBDT, about 22% of the attribution rests on unattributable features, most of it on absences (17–18%).
  Malware is slightly less localizable than benign software; larger files are more localizable (ρ ≈ 0.46).
- For the MLP under IG, 37% rests on absences (47% of IG's mass is on import features, almost all empty buckets).
- The largest single non-localizable source is one never-attributable feature, the pefile warning "Suspicious flags
  set for section" (about 5% of the GBDT's attribution).
- **Localizability depends on the explainer's baseline:** gradient × input gives nothing to file-dependent
  unattributable features (their value is zero, as is its implicit baseline), so its high ℓ is a property of the
  explainer. Only explainers with a data-driven baseline (interventional TreeSHAP, IG from the mean, KernelSHAP)
  measure reliance on absence; ℓ is reported per explainer.

PF1 confirms the null element's limited role in the feature-space: excluding unattributable features from the
deletion test does not change the pushforward's ratio to TreeSHAP (`docs/experiments/pf1.md`).

## App-R. Mechanical redundancy, not general agreement

Agreement of explainers before and after pullback (median over files and explainer pairs; the control permutes one
explanation's features before pulling it back):

| space | control | Spearman | cosine | weighted Jaccard |
|---|---|---|---|---|
| feature | no | 0.114 | 0.283 | 0.188 |
| feature | permuted | 0.000 | 0.000 | 0.061 |
| problem | no | 0.157 | 0.347 | 0.274 |
| problem | permuted | 0.002 | 0.231 | 0.131 |

Raw agreement rises after pullback, but the control rises about as much; only Spearman gains beyond it (+0.04).
Between models (IG vs. TreeSHAP) agreement *falls* after pullback. So there is no evidence that explanations
generally agree more in the problem-space. What remains for App-R is the exact proposition (features with identical
provenance merge after pullback) and Mohseni et al.'s duplicate-feature sweep, not yet run. The round-off ties found
in PF1 (`docs/experiments/pf1.md`) are this redundancy appearing in practice: many features share identical provenance.
