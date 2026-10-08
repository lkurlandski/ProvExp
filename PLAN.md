# ProvExp Research Plan

Living document. Last revised 2026-10-08 (end of session): the evaluation mirrors the framework (characterizing P,
the pullback, the pushforward, then real classifiers; see "Experiment IDs"). CP and PB1 are done at pilot scale, PB2
and PF2 are built and give their first results, and PF1 and CM are designed but not built.

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
extractor, transfers explanations between the two spaces: pullback b = Pa, pushforward a = PᵀD†b. The evaluation
mirrors the framework, from intrinsic to extrinsic, and supports four claims:

1. **Self-characterizing (CP):** statistics of P alone (coverage, ambiguity, overlap, the round-trip matrices)
   describe how sharply and how separately any transferred explanation can be placed, and bound how much of it a round
   trip loses. They are not predictors of a particular pullback's faithfulness (corrected 2026-10-07).
2. **The pullback is faithful and cheap (PB1, PB2):** pulled-back explanations identify the elements that drive the
   decision, at the cost of one instrumented feature extraction instead of hundreds to thousands.
3. **The pushforward is faithful and useful (PF1, PF2):** it translates a problem-space explanation into the
   feature vocabulary faithfully, and turns problem-space knowledge (a planted trigger) into a reference answer for
   feature-space explainers.
4. **Comparing real classifiers (CM):** with both operators, a feature-based detector (GBDT) and a raw-byte detector
   (MalConv) can be compared in either space.

Localizability (how much of a detector's reliance can be placed in the input at all; a fifth to a third rests on
unattributable features, mostly absences) is reported in the appendix (App-L) and forward-referenced from the pullback
section.

## Principle: domain-agnostic framework, selective domain knowledge in experiments

The framework and the core contributions depend only on P, never on what an element or a feature means; they apply to
any classifier with a complex feature extractor. Experiments may use domain knowledge where it protects their
integrity (e.g., a PE-aware perturbation operator or trigger), kept inside the experiment and justified there.

## Model scope: the GBDT first, the MLP later (decided 2026-10-08)

The framework stays general-purpose: P depends only on the feature extractor, never on the classifier, and the
framework applies to any classifier over the extracted features. **The first classifier we experiment with is the
GBDT**, and the experiments (CP, PB, PF) run on it until the methodology is established; CM adds MalConv, a raw-byte
model that needs no provenance of its own. **Setting the MLP
aside is temporary:** we will apply the technique to the MLP afterwards and work out the recipe that makes it work
well (see "Second classifier: the MLP"). Reasons: trees and neural networks behave very differently under the
problem-space perturbations (the pilot's MLP scores the fully ablated file at −8.2 log-odds under level 3, the GBDT
near 0), so a recipe for both at once mixes two problems; the GBDT is the stronger and standard model for EMBER-style
features (ROC-AUC 0.9976 vs. 0.9959); and the GBDT's pilot result is already robust. The MLP's pilot results stay in
`docs/pb1_pilot.md`.

## Contributions (draft)

1. **Problem and framing:** feature-space vs. problem-space explanations for detectors with *program* feature
   extractors; pullback and pushforward as rescale-rule propagation extended to non-differentiable programs.
2. **Provenance construction:** an instrumented EMBER-2024 (v3) extractor and a black-box estimator of P for
   arbitrary extractors (open source).
3. **Characterization:** statistics of P with round-trip guarantees (CP).
4. **Evaluation of both operators:** problem-space faithfulness and cost of the pullback against direct problem-space
   explainers, and planted-trigger ground truth (PB); faithfulness of the pushforward, and ground truth for
   feature-space explainers (PF).
5. **Application:** a feature-based and a raw-byte detector compared in both spaces (CM).

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
  features with identical provenance, so credit split among *mechanically* redundant features cancels exactly (App-R).

## Experiment IDs (renamed 2026-10-08)

The IDs follow the evaluation's structure. The old IDs appear in documents written before 2026-10-08 (`docs/pilot.md`,
`docs/plan_phase2.md`) and in artifact paths that predate the renaming (`artifacts/experiments/e1/`, which holds PB1).

| ID | Section | Was |
|---|---|---|
| CP | 1. Characterizing P | E2 (and A2, merged) |
| PB1 | 2. Pullback: faithfulness and cost | E1 |
| PB2 | 2. Pullback: planted-trigger recovery | E3 (pullback half) |
| PF1 | 3. Pushforward: faithfulness | new |
| PF2 | 3. Pushforward: trigger ground truth for feature-space explainers | E3 (pushforward half) |
| CM | 4. Comparing classifiers: GBDT vs. MalConv in both spaces | A1 (promoted from the appendix) |
| App-L | Appendix: localizability (reliance on absence) | E4 |
| App-R | Appendix: mechanical redundancy | A3 |

Documents and scripts carry the IDs: `docs/cp_plan.md`, `docs/cp_census.md`, `scripts/cp_tables.py`,
`scripts/cp_coarsening.py`; `docs/pb1_plan.md`, `docs/pb1_pilot.md`, `docs/pb1_baselines.md`, `scripts/pb1_tables.py`
(the runner is `scripts/faithfulness.py`). The planted trigger is a shared testbed for PB2 and PF2.

## Experiments

All experiments run first on the ~100-file pilot subset with one seed; scaling up (2,000 files, seeds 0–2) is for the
final numbers only (decided 2026-10-08).

### 1. Characterizing P (CP; definitions adopted 2026-10-08; `docs/cp_plan.md`, `docs/cp_census.md`)

The statistics characterize P: how sharply (spread) and how separately (sharing) a transferred explanation can be
placed in the input, independent of any particular explanation's faithfulness. Definitions: ambiguity H_j with
effective support exp(H_j); overlap O_j = 1 − M_jj with M = PᵀD†P the pull–push matrix (feature confusion) and
N = PPᵀD† the push–pull matrix; the round-trip bounds (the perfect-reconstruction theorems are corollaries);
coarsening never lowers overlap. Done: the census on all 2,000 files (overlap informative per feature and group; the
group confusion matrix; the bound holds for every file and explainer, within about 1.5× of the error; ambiguity in
bytes is mostly file size), and coarsening on the pilot files (overlap 0.41 at bytes, 0.98 at 256 windows). Remaining:
the instrumented vs. black-box P at window level (saved by `faithfulness.py`); possibly resolution at granularity w
(decided after the PB1 baselines). The spectrum is for our own insight only.

### 2. Application: the pullback

**PB1. Faithfulness and cost** (`docs/pb1_plan.md`, `docs/pb1_pilot.md`, `docs/pb1_baselines.md`)

- **Models and explainers:** the GBDT (TreeSHAP path and interventional, KernelSHAP). The MLP ran in the pilot and
  returns later (see "Model scope").
- **Compared:** the pullback of each explainer (bytes, and coarsened to windows) vs. direct problem-space explainers
  (occlusion at 64–4,096 windows, KernelSHAP over windows), the black-box pullback, random, and the unsigned ranking.
- **Faithfulness:** deletion curves in the problem-space (insertion dropped 2026-10-07).
- **Cost:** feature extractions and wall-clock time per explanation (faithfulness vs. cost).
- **Perturbation operator:** PE-aware ablation (protected layout fields plus per-file breakers, every ablated file
  verified); level 3 primary (header fields take their most common training value), level 2 and random fill as
  robustness checks.
- **Headline (decided 2026-10-08):** window-level parity with the best direct problem-space baseline at two orders of
  magnitude lower cost; the byte-level advantage is secondary.
- **Done** (pilot, 100 files, one seed; `docs/pb1_pilot.md`). Parity holds at *every* granularity tested (64, 256,
  1,024 windows: p ≥ 0.54) and the pullback leads at 4,096 (1.22 vs. 1.10, p = 0.004), so the claim does not depend on
  a chosen window count. **Occlusion saturates at 1.10** and never approaches the byte-level pullback's 1.67 (80–81 of
  100 files, p ≈ 1e-12): 4,096 windows buy nothing over 1,024, so byte resolution is unreachable by direct
  explanation at any affordable cost. KernelSHAP over windows matches the best occlusion at 1,925 extractions and is
  the strongest direct baseline. The **overshoot** is explained: an unsigned ranking removes three quarters of it and
  the remainder grows with resolution in every method family, occlusion included.

**PB2. Planted-trigger recovery** (built; shares the testbed with PF2; `docs/trigger_plan.md`)

A trigger written into 1% of the training malware, which is relabeled benign, and the GBDT retrained: the bytes the
model's decision depends on are then known by construction, so faithfulness can be tested without any perturbation
operator. Planted triggers as ground truth are established (Lin et al. 2021); doing it in the problem-space of
malware is new. Two triggers span the provenance spectrum: **struct** (3 header fields, 6 bytes, chosen from data
statistics alone so that scoring explainers against it is not circular) and **content** (a 2,048-byte block appended,
or written over the end of the visible 4 MB).

- **The struct trigger is a clean testbed:** attack success 1.000, +16.7 log-odds, clean ROC-AUC unchanged, and it
  fires on all 1,000 explanation-set malware files. The content trigger reaches only 0.472, because a content
  trigger's effect scales with its *share* of the file (0.92 below 50 KB, 0.29 above 1 MB) while the struct trigger
  is at 1.000 at every size — the provenance spectrum appearing in learnability. Decided: keep the files where the
  backdoor fired (the model's output only, never an explanation).
- **First results (6 files, struct):** the **6 top-ranked bytes of 614,000 are exactly the trigger's 6 bytes** for
  all three explainers, with 0.67–0.75 of the pulled-back attribution change on them against a random baseline of
  1.0e-05, reaching about 77% of the ceiling P permits. Any method that scores whole windows is bounded
  *analytically* at 0.0027 precision at 256 windows, which is a resolution argument for byte-level pullbacks that
  needs no perturbation operator.

The section forward-references App-L for what the pullback cannot localize (the null element's share).

### 3. Application: the pushforward

**PF1. Faithfulness of the pushforward** (new; design to write)

Push a direct problem-space explanation forward (occlusion at the PB1 window counts, already computed) and test the
resulting feature attribution in the feature space: a feature-space deletion test of the GBDT (remove the top-ranked
features, re-score), against TreeSHAP, KernelSHAP, and random. Open: the feature-space reference value for a deleted
feature, and whether to also push forward the pullback itself (the round trip M a, which CP characterizes).

**PF2. Ground truth for feature-space explainers** (built; shares the testbed with PB2)

The pushforward of the trigger's bytes, r = ψ(1_T), is the feature attribution a faithful explainer *should* produce
on a triggered file: the features the trigger touches, weighted by their provenance. First results (6 files, struct;
the trigger touches 12 features): every explainer's top feature of 2,568 is one the trigger touches (6/6 files), with
cosine 0.94 against r; mass on those features is 0.70 for both TreeSHAP variants and 0.50 for KernelSHAP, and the
rank agreement within them is weak (Spearman 0.28–0.39). **This is the pushforward turning problem-space knowledge
into an evaluation of feature-space explainers, which otherwise have no ground truth.** KernelSHAP needs its full
32,768 coalitions; at 512 it appears to miss the trigger entirely.

### 4. Application: comparing classifiers (CM; promoted from the appendix 2026-10-08)

A feature-based detector (the GBDT) and a raw-byte detector (MalConv medium) explained in both spaces, on the same
truncated files:
- **Problem-space:** the GBDT's pullback vs. MalConv's direct byte explanations (IG, occlusion): agreement over
  windows, against a permutation control; and cross-deletion (do one model's top bytes remove the other's evidence?)
  with the PB1 operator.
- **Feature-space:** MalConv's explanations pushed forward vs. the GBDT's TreeSHAP: which feature groups each relies on.
- To do: MalConv explanations for the pilot files (`explain/problem.py` has IG and occlusion; not yet run).

### Second classifier: the MLP (after the GBDT methodology is established)

Apply the established methodology to the MLP and find the recipe that makes it work. The pilot's diagnosis is the
starting point: the black-box pullback of the MLP's explanations trails occlusion as far as the instrumented one, so P
transfers them correctly and the explanations are the weak link (`docs/pb1_pilot.md`, reading 5). Candidate steps, in
order: a feature-space deletion check (are IG and KernelSHAP faithful to the MLP in the feature space at all? PF1's
test can be reused); then, depending on the answer, a better explainer (e.g., DeepLIFT/DeepSHAP) or a reference
matched to the perturbation operator. Matching the reference to the operator changes what PB1 claims; decide with the
user before adopting it.

### Appendix

- **App-L. Localizability:** the share of attribution that the pullback sends to the null element (reliance on
  absence), split into file-dependent absences and never-attributable features, per explainer. Mostly done
  (`docs/pilot.md`, finding 2).
- **App-R. Mechanical redundancy:** a short proposition (features with identical provenance merge after pullback) and
  Mohseni et al.'s duplicate-feature sweep; agreement of explainers before and after pullback, net of a permutation
  control (`scripts/pullback_agreement.py`).

## Explainers

TreeSHAP (path and interventional) and KernelSHAP for the GBDT; MalConv IG and occlusion for CM. For the MLP (later):
IG (background-mean baseline) and KernelSHAP, plus whatever the second-classifier step finds necessary. Gradient ×
input is kept for now but cannot credit absence (zero baseline); drop it unless it earns its place. The choice of XAI
methods may be revisited.

## Modest theory (each result short, correct, and useful)

- **T1 Structural = Shapley provenance for additive groups.** For σ additive in element contributions (histograms,
  counts), instrumented provenance equals the Shapley-of-σ provenance. For non-additive groups (entropy windows,
  hashing), the gap is measured empirically against the black-box estimate (PB1, CP).
- **T2 Composition.** P_{σ2∘σ1} = P1·P2 is valid provenance, so pullback composes; pushforward (with D†) does not in
  general.
- **T3 Coarsening** (manuscript, Proposition Coarsening, 2026-10-08). Grouping elements into sets (e.g., windows)
  commutes with pullback, never raises ambiguity, and never lowers overlap.
- **Mechanical redundancy (App-R).** Features with identical provenance columns are indistinguishable after pullback.
- **Round trips (2026-10-08).** M = PᵀD†P is symmetric and doubly stochastic with M_jj = 1 − O_j; the cyclic errors
  are bounded by 2 Σ_j |a_j| O_j and 2 Σ_i |b_i| (1 − N_ii), with equality for one-hot inputs. The
  perfect-reconstruction theorems (pull-push iff O = 0, push-pull iff H = 0) are its corollaries. Every theorem is
  checked numerically with property-based tests.

## Open questions

- ~~**Summary statistics**~~ decided 2026-10-08: the names stay; ambiguity = mean entropy (effective support
  exp(H_j)), overlap = O_j = 1 − M_jj (`docs/cp_plan.md`).
- ~~Localizability ℓ~~ decided 2026-10-07: removed from the framework (it is explanation-specific); coverage κ stays.
  The null element's entry of a pullback is the attribution that cannot be localized. ℓ and other
  explanation-weighted quantities remain evaluation metrics (CP, App-L).
- **Signed provenance:** rescale-rule matrices can be signed; our axioms require P ≥ 0. Keep structural (unsigned)
  provenance plus a stated limitation unless PB1 shows a need.
- **Naming** ("provenance" vs. "attribution lineage").

## Data, models, compute

- **Scope:** EMBER-2024 PE files and EMBER feature version 3 only, truncated to the first 4,000,000 bytes; all
  features recomputed on the truncated files so that σ, P, and the model see the same object.
- **Models:** GBDT (LightGBM, EMBER baseline parameters with the categorical features treated as numeric, because shap
  misencodes LightGBM categorical splits) and MLP, seeds 0–2; MalConv medium, seeds 0–2 (for CM). Seed 0 for all
  explanation work; seeds 1–2 for robustness. Experiments use the GBDT first; the MLP is trained and returns later
  (see "Model scope").
- **Explanation set:** 2,000 test files (1,000 per label, TLSH-deduplicated, at most 10 per malware family).
- **Compute:** ample CPUs and GPUs, so direct problem-space baselines are feasible at scale.

## Timeline and gates

Phases 0–2 are complete (literature; `provexp`; features, models, stage-1 explanations, census). As of 2026-10-08:
**CP and PB1 are done at pilot scale, PB2 and PF2 are built with first results, PF1 and CM are designed but not
built.** Most of the research runs at pilot scale; scaling up is for the final numbers. `run/` holds the commands
that produced everything in `artifacts/`.

| Dates | Work | Gate |
|---|---|---|
| Oct 8 | ~~PB1 baselines~~, ~~the trigger testbed~~ done; the runner's parallelism rebuilt | **Gate 2** (passed for the GBDT) |
| Oct 9–20 | PB2/PF2 at pilot scale on both triggers; PF1 (design, then build); CP's black-box comparison | |
| Oct 21–Nov 15 | CM: MalConv explanations of the pilot files, both comparisons | |
| Nov 15–Dec 5 | Scale-up of every experiment (2,000 files, seeds 0–2), when the user decides; the MLP if time allows | |
| Dec 5–15 | Appendix (App-L, App-R) | |
| Dec 15–late Jan | Writing: introduction and contributions, framework edits, figures | Submission |

Gate 1 (the pilot census, `docs/pilot.md`) passed provisionally for the measurement result (now App-L).
Gate 2 (the PB1 pilot, `docs/pb1_pilot.md`, 2026-10-08): passed for the GBDT (window-level parity with occlusion under
level-2 and level-3 operators, byte-level advantage 1.65–1.79×). The MLP did not reach occlusion (the explanations, not
P, are the bottleneck); it is set aside temporarily and returns after the GBDT methodology is established. Insertion
was dropped as a flawed test. Thresholds are reassessed with the user.

## Risks

- **The core claim fails (Gate 2):** pullbacks are not more faithful than random, e.g., because most attribution
  rests on absence or on features that smear over the whole file. Mitigation: the gate is early; per-subset results
  may still support a narrower claim; fallback venue.
- **Perturbations go off-manifold:** zero/random edits break parsing and distort faithfulness. Mitigation: report
  parse-failure rates; move to a PE-aware operator.
- **Smearing:** histogram and entropy features spread over the whole file. Treated as a measured result (CP, App-L),
  not a limitation.
- **Reviewer pool:** Raff co-authored EMBER-2024, MalConv, and the SHAP-on-EMBER critique; engage it directly (App-R,
  CM).
- **The pushforward has no evidence yet:** PF1 and PF2 are new. If the pushforward is not faithful, claim 3 narrows
  to a diagnostic use and CM's feature-space half weakens.
- **Timeline:** if needed, App-R shrinks first, then CM's cross-deletion.
