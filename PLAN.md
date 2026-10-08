# ProvExp Research Plan

Living document. Last revised 2026-10-07: replanned after the Phase 2 pilot (`docs/pilot.md`) around three claims,
three core experiments, and an early go/no-go gate on the core claim.

## Target

- **Venue:** USENIX Security 2027, second submission cycle (late January 2027). Optimistic; fallback is the next S&P /
  CCS / USENIX cycle, or a lower-tier venue (ACSAC, RAID, AsiaCCS, DLSP) if Gate 2 fails.
- **Format:** a single security paper. Theory stays modest: correct, clearly stated, and useful in practice, not an
  ML-theory contribution.
- **No human studies.** No user or analyst studies. Evidence comes from quantitative evaluation only.

## Problem

Analysts reason about the sample itself (the *problem-space*), but production detectors use hand-crafted feature
extractors, so their explanations live in the *feature-space*. There is no general, principled way to translate a
feature explanation back to the parts of the input that produced it. Prior work either explains features only (SHAP on
EMBER), explains raw-byte models only (MalConv + IG), or maps features to the binary by hand, one feature at a time
(Severi et al. 2021, Rosenberg et al. 2020). FINER (CCS 2023) explicitly argues that explanations of hand-crafted
feature sets cannot be mapped back to the program.

## Thesis and claims

Explanation provenance, a matrix P (elements × features, plus a null element) built by instrumenting the feature
extractor, transfers explanations between the two spaces: pullback b = Pa, pushforward a = PᵀD†b. The paper rests on
three claims, each with direct evidence:

1. **Faithful:** pulled-back explanations identify the elements that actually drive the decision (E1, E3).
2. **Cheap:** one instrumented feature extraction instead of hundreds to thousands for direct problem-space
   explanation (E1).
3. **Self-characterizing:** provenance statistics (ambiguity, overlap, coverage) describe, from P alone, how useful a
   transferred explanation can be: how sharply and how separately it can be placed in the input (E2). They are not
   predictors of a particular pullback's faithfulness (corrected 2026-10-07).

And one measurement result: how much of what production-style detectors rely on can be localized in the input at
all. The pilot found that a fifth to a third of the attribution rests on unattributable features, mostly on the
*absence* of something, which no explanation over the input can show (E4).

## Principle: domain-agnostic framework, selective domain knowledge in experiments

The framework and the core contributions depend only on P, never on what an element or a feature means; they apply to
any classifier with a complex feature extractor. Experiments may use domain knowledge where it protects their
integrity (e.g., a PE-aware perturbation operator or trigger), kept inside the experiment and justified there.

## Model scope: the GBDT first, the MLP later (decided 2026-10-08)

The framework stays general-purpose: P depends only on the feature extractor, never on the classifier, and the
framework applies to any classifier over the extracted features. **The first classifier we experiment with is the
GBDT**, and the experiments (E1 at scale, E2, E3) run on it until the methodology is established. **Setting the MLP
aside is temporary:** we will apply the technique to the MLP afterwards and work out the recipe that makes it work
well (see "Second classifier: the MLP"). Reasons: trees and neural networks behave very differently under the
problem-space perturbations (the pilot's MLP scores the fully ablated file at −8.2 log-odds under level 3, the GBDT
near 0), so a recipe for both at once mixes two problems; the GBDT is the stronger and standard model for EMBER-style
features (ROC-AUC 0.9976 vs. 0.9959); and the GBDT's pilot result is already robust. The MLP's pilot results stay in
`docs/e1_pilot.md`.

## Contributions (draft)

1. **Problem and framing:** feature-space vs. problem-space explanations for detectors with *program* feature
   extractors; pullback and pushforward as rescale-rule propagation extended to non-differentiable programs.
2. **Provenance construction:** an instrumented EMBER-2024 (v3) extractor and a black-box estimator of P for
   arbitrary extractors (open source).
3. **Evaluation:** problem-space faithfulness and cost against direct problem-space explainers; planted-trigger
   ground truth; provenance statistics as characterizations of P.
4. **Measurement:** localizability of a production-style feature set, and the share of detector reliance that rests on
   absence.

The manuscript's contribution list (C1–C3 in the introduction) predates Phase 0 and must be rewritten: "first to
formalize" and "novel rigorous theory" cannot stand (see Positioning). Naming ("provenance" collides with
provenance-graph IDS work) is deferred to writing time.

## Positioning (from Phase 0, `docs/related_work.md`)

- **Pullback is not new as an operator.** It is G-DeepSHAP's generalized rescale rule with P_ij = φ_i(σ_j)/Δσ_j;
  exactness for linear chains is known. We cite it and position against it.
- **What is new** is constructing P for a *program* (parser, hashing, string scans, windowed entropy), which
  G-DeepSHAP's stage-wise propagation does not cover, and showing what the transfer is worth and what it reveals.
- **Pushforward** is framed as *foreign-space explanation*: explaining a model in a representation it never computes.
  When O = 0 it reduces to group-sum aggregation, so it generalizes aggregation to overlapping, weighted groups.
- **SHAP-on-EMBER critique (Mohseni, Raff & Gaur 2026):** the method is explainer-agnostic, but reviewers will know
  this paper. Results use several explainers and are validated in the problem-space on real files. Pullback merges
  features with identical provenance, so credit split among *mechanically* redundant features cancels exactly (A3).

## Experiments

Core experiments E1–E4 make the paper; A1–A3 are appendix-grade.

### E1. Faithfulness and cost (the core)

- **Models and explainers:** the GBDT (TreeSHAP path and interventional, KernelSHAP) on the explanation set. The MLP
  (IG from the background mean, KernelSHAP) ran in the pilot and returns later (see "Model scope").
- **Compared:** the pullback of each explainer vs. direct problem-space explainers (occlusion and KernelSHAP over
  windows of bytes) vs. random. Comparisons are at a common window granularity, which coarsening (T3) justifies.
- **Faithfulness:** deletion curves in the problem-space (insertion dropped 2026-10-07: it starts from a blank file far
  from real files, restoring scattered bytes does not rebuild structures, and the explanations use another reference):
  edit the top-ranked windows, re-extract
  features, re-score the model.
- **Cost:** feature-extraction calls and wall-clock time per explanation (Pareto plot of faithfulness vs. cost).
- **Black-box P:** occluding windows and re-extracting yields a black-box estimate of P at no extra cost. It validates
  the instrumented P (exact for additive feature groups by T1; measured for the others) and gives a further baseline
  (pullback through the estimated P).
- **Perturbation operator (revised 2026-10-08):** PE-aware ablation (protected layout fields plus per-file breakers,
  every ablated file verified). Level 3 is primary: unprotected header fields take their most common training value;
  content bytes are zeroed (random fill as robustness). Level 2 (header fields zeroed) is a robustness check.
- **Headline (decided 2026-10-08):** window-level parity with occlusion at two orders of magnitude lower cost (equal
  granularity) is the main claim; the byte-level advantage is secondary, shown against occlusion at several window
  counts (64–4,096) and KernelSHAP over windows. The unsigned ranking tests the reading of the overshoot.

### E2. Characterizing provenance (design open)

Ambiguity H and overlap O characterize P: how sharply and how separately a transferred explanation can be placed in
the input, independent of any particular explanation's faithfulness. The pilot showed that the current overall
summaries saturate (normalized H ≈ 0.99, overall O ≈ 0.003); candidate mild changes are normalizing H_j by log|z| (the
input length) instead of log|A_j|, and dropping the 1/(n' − 1) of O. The theorems are unaffected by either. How E2
shows that the statistics characterize usefulness is to be decided after E1.

### E3. Planted ground truth

Write a trigger into poisoned training files and retrain the GBDT (minutes). Does the pullback recover the trigger's
elements? Pushing the trigger's elements forward gives the feature attribution an explainer *should* produce, which
scores TreeSHAP and the other feature-space explainers against a known answer. Planted triggers as ground truth are
established (Lin et al. 2021); doing it in the problem-space of malware is new. The trigger may be PE-aware (e.g.,
Severi et al.'s header-field triggers) if a domain-agnostic byte pattern is too weak to be learned.

### E4. Census (measurement)

Coverage, ambiguity, overlap, and effective support per feature subset and sample class; the share of attribution
that the pullback sends to the null element (reliance on absence), split into file-dependent absences and features
that are never attributable; a few pulled-back explanations as figures. Mostly done (`docs/pilot.md`).

### Second classifier: the MLP (after the GBDT methodology is established)

Apply the established methodology to the MLP and find the recipe that makes it work. The pilot's diagnosis is the
starting point: the black-box pullback of the MLP's explanations trails occlusion as far as the instrumented one, so P
transfers them correctly and the explanations are the weak link (`docs/e1_pilot.md`, reading 5). Candidate steps, in
order: a feature-space deletion check (are IG and KernelSHAP faithful to the MLP in the feature space at all?); then,
depending on the answer, a better explainer (e.g., DeepLIFT/DeepSHAP) or a reference matched to the perturbation
operator (IG's baseline or KernelSHAP's background taken from ablated files). Matching the reference to the operator
changes what E1 claims; decide with the user before adopting it. Timing is decided once the GBDT experiments are done.

### Appendix-grade

- **A1. MalConv vs. GBDT through pushforward and pullback:** MalConv's byte explanations (IG, occlusion) pushed
  forward into EMBER features and compared with the GBDT's reliance; both compared in the problem-space.
- **A2. Cyclic error:** pull-push and push-pull reconstruction error as intrinsic diagnostics of P (zero iff O = 0 or
  H = 0, so it measures P, not faithfulness).
- **A3. Mechanical redundancy:** a short proposition (features with identical provenance merge after pullback) and
  Mohseni et al.'s duplicate-feature sweep; agreement of explainers before and after pullback, net of a permutation
  control (`scripts/pullback_agreement.py`).

## Explainers

TreeSHAP (path and interventional) and KernelSHAP for the GBDT; MalConv IG and occlusion for A1. For the MLP (later):
IG (background-mean baseline) and KernelSHAP, plus whatever the second-classifier step finds necessary. Gradient × input is kept for now but cannot credit absence (zero baseline); drop
it after E1 unless it earns its place. The choice of XAI methods may be revisited.

## Modest theory (each result short, correct, and useful)

- **T1 Structural = Shapley provenance for additive groups.** For σ additive in element contributions (histograms,
  counts), instrumented provenance equals the Shapley-of-σ provenance. For non-additive groups (entropy windows,
  hashing), the gap is measured empirically against the black-box estimate (E1).
- **T2 Composition.** P_{σ2∘σ1} = P1·P2 is valid provenance, so pullback composes; pushforward (with D†) does not in
  general.
- **T3 Coarsening.** Grouping elements into sets (e.g., windows) commutes with pullback.
- **Mechanical redundancy (A3).** Features with identical provenance columns are indistinguishable after pullback.
- The perfect-reconstruction theorems (pull-push iff O = 0, push-pull iff H = 0) stay, scoped to attributable
  features. Every theorem is checked numerically with property-based tests.

## Open questions

- **Summary statistics** (E2 decides): the mild normalization changes above, or none.
- ~~Localizability ℓ~~ decided 2026-10-07: removed from the framework (it is explanation-specific); coverage κ stays.
  The null element's entry of a pullback is the attribution that cannot be localized. ℓ and other
  explanation-weighted quantities remain evaluation metrics (E2, E4).
- **Signed provenance:** rescale-rule matrices can be signed; our axioms require P ≥ 0. Keep structural (unsigned)
  provenance plus a stated limitation unless E1 shows a need.
- **Naming** ("provenance" vs. "attribution lineage").

## Data, models, compute

- **Scope:** EMBER-2024 PE files and EMBER feature version 3 only, truncated to the first 4,000,000 bytes; all
  features recomputed on the truncated files so that σ, P, and the model see the same object.
- **Models:** GBDT (LightGBM, EMBER baseline parameters with the categorical features treated as numeric, because shap
  misencodes LightGBM categorical splits) and MLP, seeds 0–2; MalConv medium, seeds 0–2. Seed 0 for all explanation
  work; seeds 1–2 for robustness. Experiments use the GBDT first; the MLP is trained and returns later (see "Model
  scope").
- **Explanation set:** 2,000 test files (1,000 per label, TLSH-deduplicated, at most 10 per malware family).
- **Compute:** ample CPUs and GPUs, so direct problem-space baselines are feasible at scale.

## Timeline and gates

Phases 0–2 are complete (literature; `provexp`; features, models, stage-1 explanations, census). As of 2026-10-08 the
E1 pilot is complete (100 files; level 2, level 3, KernelSHAP), followed by a reassessment round before E1 at scale.

| Dates | Work | Gate |
|---|---|---|
| Oct 7–20 | Finish the pilot (pullback pass); perturbation operator; E1 pilot on about 100 files | **Gate 2:** the pullback beats random and approaches direct explainers at a fraction of the cost. If not, the core claim fails: retarget early. |
| Oct 21–Nov 15 | E1 at scale on the GBDT (more files, seeds 1–2), with the black-box P and KernelSHAP; E2 (design open) | Settle the summary statistics |
| Nov 15–Dec 5 | E3; E4 final | |
| Dec 5–15 | A1–A3; seeds 1–2 for robustness | |
| once the GBDT methodology is established | Second classifier: the MLP (timing decided then) | |
| Dec 15–late Jan | Writing: introduction and contributions, framework edits, figures | Submission |

Gate 1 (the pilot census, `docs/pilot.md`) passed provisionally for the measurement result.
Gate 2 (the E1 pilot, `docs/e1_pilot.md`, 2026-10-08): passed for the GBDT (window-level parity with occlusion under
level-2 and level-3 operators, byte-level advantage 1.65–1.79×). The MLP did not reach occlusion (KernelSHAP does not
close the gap; the explanations, not P, are the bottleneck); it is set aside temporarily and returns after the GBDT
methodology is established, so the gate is decided on the GBDT. Insertion was dropped as a flawed test. Thresholds
are reassessed with the user.

## Risks

- **The core claim fails (Gate 2):** pullbacks are not more faithful than random, e.g., because most attribution
  rests on absence or on features that smear over the whole file. Mitigation: the gate is early; per-subset results
  may still support a narrower claim; fallback venue.
- **Perturbations go off-manifold:** zero/random edits break parsing and distort faithfulness. Mitigation: report
  parse-failure rates; move to a PE-aware operator.
- **Smearing:** histogram and entropy features spread over the whole file. Treated as a measured result (E4), not a
  limitation.
- **Reviewer pool:** Raff co-authored EMBER-2024, MalConv, and the SHAP-on-EMBER critique; engage it directly (A3).
- **Timeline:** if needed, A1 shrinks first, then A3.
