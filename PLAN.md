# ProvExp Research Plan

Living document. Last revised 2026-10-07 (PE-format specifics removed: the framework and its evaluations are domain-agnostic).

## Target

- **Venue:** USENIX Security 2027, second submission cycle (late January 2027). Optimistic; fallback is the next S&P / CCS / USENIX cycle.
- **Format:** a single security paper. Theory stays modest: correct, clearly stated, and useful in practice, not an ML-theory contribution.
- **No human studies.** No user studies or analyst studies. Evidence comes from quantitative evaluation only.

## Thesis

Explanation provenance acts as a *chain rule for non-differentiable feature extractors*. It turns cheap feature-space explanations (e.g., TreeSHAP on EMBER features) into problem-space explanations (attributions over the elements of the input, here the bytes of a file) that are:

1. **faithful**, shown with problem-space deletion/insertion tests and planted ground truth;
2. **orders of magnitude cheaper** than direct problem-space explanation (one instrumented σ call vs. thousands);
3. **self-diagnosing**, because provenance statistics (ambiguity H, overlap O) say in advance how localizable an explanation can be.

Pushforward goes the other way: it expresses raw-byte model explanations (MalConv) in human-defined feature space.

## Framing of "smear" (a result, not a limitation)

How *localizable* a feature set's signal is is a property of the feature set, and measuring it is one of the study's contributions. Provenance statistics give the first quantitative tool for asking "how much of what this model relies on can an analyst actually point to in the input?" We report this for each feature subset and each sample class (malware/benign, input size), and connect it to security consequences such as robustness to problem-space perturbations and analyst actionability. The pilot (`docs/pilot.md`) adds a second axis: a large share of attribution rests on unattributable features, i.e., on the *absence* of something, which no element can show.

## Contributions (revised after Phase 0)

1. **Framing:** feature-space vs. problem-space explanations for detectors with *program* feature extractors; pullback/pushforward as rescale-rule propagation extended to non-differentiable programs.
2. **Provenance construction:** instrumented EMBER-2024 (v3) extractor + black-box estimator (open source).
3. **Localizability analysis** of EMBER feature sets.
4. **Evaluation:** problem-space faithfulness vs. cost; planted-trigger ground truth.
5. **Cross-representation comparison** of MalConv and GBDT.

Naming ("provenance" collides with provenance-graph IDS work) is deferred to writing time.

## Novelty strategy (decided 2026-10-06, after Phase 0 first pass)

- **Pullback is not claimed as new.** It is G-DeepSHAP's generalized rescale rule. Cite it and position against it. A method contribution of the form "rescale rule applied to a feature extractor" is not enough for a top venue on its own.
- **Top-tier novelty has to come from what the pullback *enables* in security**, not from the operator:
  - (a) **Measurement:** *how much of what production-style malware detectors rely on can be localized in the input, and how sharply?* Coverage, localizability, and effective support of explanations per feature subset and sample class; the share of attribution resting on absence (unattributable) features; how concentrated pulled-back explanations are along the input. MalConv is compared in the same problem-space (elements).
  - (b) **Manipulability (hypothesis to test):** how concentrated a decision's pulled-back attribution is (localizability, effective support, the share held by its top elements) predicts how few element edits suffice to change the decision, with the edits made by a black-box problem-space perturbation in pullback order. If this holds, it is a per-decision, explainer-agnostic robustness signal and a new defensive result.
- **Pushforward is kept as a conceptual contribution, framed as *foreign-space explanation*:** explaining a model in terms of a representation it never computes (MalConv explained in EMBER features). Aggregation and G-DeepSHAP's group rescale only coarsen a model's own inputs. When O=0, pushforward reduces to plain group-sum aggregation, so it generalizes aggregation to overlapping, weighted groups. The pull/push duality results (perfect round-trip iff O=0 / H=0) are kept as modest theory.
  - (c) **Stability (hypothesis to test):** explanations agree more in the problem space than in feature space. Pullback merges features with identical provenance, so credit-splitting among mechanically redundant features (Mohseni et al. Lemma 2) cancels exactly. Test: their duplicate-feature sweep, plus agreement across explainers and background sets before and after pullback.
- **Additional pushforward uses to develop:**
  - *Ground truth for feature-space explainers:* push a known set of elements (a planted trigger) forward to get the feature attribution an explainer *should* produce, then score TreeSHAP/KernelSHAP/LIME against it.
  - *Explanation translation between feature extractors:* pull via σ₁, push via σ₂ (a = P₂ᵀD₂†P₁a₁), e.g., EMBER-feature GBDT ↔ MalConv on the same files (more extractors if scope grows).
- **Go/no-go checkpoint (around week 6):** pilot (a)–(c) on a few thousand files. If none shows a strong signal, retarget to a lower-tier venue.
- **The method is explainer-agnostic.** The SHAP-on-EMBER critique (Mohseni et al. 2026) does not affect the method, but it affects evaluation and reviewers. Show results with several explainers (TreeSHAP, KernelSHAP, LIME, IG/MLP) and validate in the problem space on real files.
- **Fallback:** if (a) and (b) produce no strong findings, retarget to a lower-tier venue (e.g., ACSAC, RAID, AsiaCCS, DLSP workshop) with the method + malware application.

## Known weaknesses to address

1. Theory is thin as stated, and the push–pull theorem needs a σ-consistency hypothesis.
2. P is defined only by axioms. Constructing it is the real problem.
3. Cyclic reconstruction error measures only properties of P (it is zero iff O=0 or H=0), not faithfulness. Demote it to a diagnostic.
4. Novelty claims ("first to formalize", "no prior pushforward") must survive a careful literature search (Phase 0).
5. The "just bookkeeping" objection must be answered by aggregation, trust diagnostics, exactness, and cost.

## Modest theory (keep each result short, correct, and useful)

- **Positioning (revised after Phase 0, see `docs/related_work.md`).** Pullback is the generalized rescale rule of G-DeepSHAP (Chen et al. 2022) with P_ij = φ_i(σ_j)/Δσ_j, and exactness for linear chains is already known. We cite this instead of claiming it, and adopt the baseline-relative definition as the meaning of "proportional influence".
- **T1 Structural = Shapley provenance for additive groups.** For σ additive in element contributions (byte histogram, counts, etc.), cheap instrumented provenance equals the Shapley-of-σ provenance. For non-additive groups (entropy windows, hashing), measure the gap empirically against the black-box estimator.
- **T2 Composition.** P_{σ2∘σ1} = P1·P2 is valid provenance, so pullback composes. Pushforward (with D†) does not compose in general. Note this, and possibly define forward provenance separately.
- **T3 Coarsening.** Grouping elements into sets (e.g., contiguous windows) commutes with pullback. This justifies explanations over groups of elements.
- Fix theorem statements, prove the two conjectures, and check every theorem numerically with property-based tests.

## Data, models, compute

- **Scope (decided 2026-10-06):** EMBER-2024 PE files and EMBER feature version 3 only. Other datasets and feature versions are out of scope for now.
- **Binaries:** EMBER-2024, **first 4,000,000 bytes of each file only**.
  - Recompute all features on the truncated files so that σ, P and the model all see the same object. Report how many files are truncated and how this changes features (e.g., features computed from the end of the file).
- **Models:** LightGBM (EMBER baseline-style) and MLP trained on EMBER features. Pretrained MalConv (medium) on EMBER-2024.
- **Compute:** ample CPUs, GPUs and storage, so direct problem-space baselines (KernelSHAP/LIME/occlusion over windows of elements) are feasible at scale for comparison.

## Phases (about 16 weeks to a late-January deadline)

Progress (2026-10-06): Phases 0 and 1 are complete, about four weeks ahead of schedule. Phase 2 is planned in `docs/plan_phase2.md`.

| Phase | Weeks | Work | Deliverable |
|---|---|---|---|
| 0 | 1–2 | Literature search: settle the gaps and novelty claims | `docs/related_work.md`, revised contribution list |
| 1 | 3–6 | `provexp` package: sparse P, pullback/pushforward, H/O; instrumented provenance per EMBER feature group; property tests | Library + tests |
| 2 | 5–7 | Recompute features on truncated binaries; train LightGBM/MLP; feature-space explainers (TreeSHAP, IG); load MalConv | Models + explanations |
| 3 | 7–9 | Element perturbation (a black-box problem-space operator); direct problem-space baselines; black-box provenance estimation (validates instrumented P) | Baselines + cost numbers |
| 4 | 9–12 | Main evaluations (below) | Results |
| 5 | 11–13 | Pushforward/MalConv study; localizability analysis across datasets | Applications |
| 6 | 13–16 | Writing (theory section written alongside Phases 1–4) | Submission |

## Evaluations

1. **Provenance census / localizability:** H and O per feature group, dataset and sample class.
2. **Problem-space faithfulness:** deletion/insertion curves over elements (in windows); pullback vs. direct KernelSHAP/LIME/occlusion vs. random/heuristic baselines; faithfulness vs. σ-call cost (Pareto plot).
3. **Planted ground truth:** plant a known trigger (a byte pattern that sets a chosen subset of features) to create a shortcut/backdoored model; measure whether the pullback localizes the trigger bytes. This also serves as a backdoor-forensics application (cf. Severi et al., USENIX Sec '21).
4. **Agreement:** pulled-back vs. direct explanations, compared against how much different explainers disagree within the same space.
5. **Pushforward:** MalConv explanations expressed in EMBER feature space; compare with the GBDT's reliance.
6. **Qualitative illustrations** (figures of pulled-back explanations on example samples; no human subjects).
7. Cyclic error reported as a minor diagnostic only.
8. **Manipulability:** correlate the per-sample concentration of pulled-back attribution with the number of element edits a black-box problem-space perturbation needs to change the decision, editing in pullback order vs. random and baseline orders.

## Risks

- Histogram/entropy features dominate and smear across the file. Handled as an analysis result (see framing above); report per-subset results and effective support.
- The 4,000,000-byte truncation changes features relative to the published EMBER vectors. Mitigated by recomputing everything on the truncated files.
- Novelty overlap with prior work: pullback ≈ G-DeepSHAP rescale rule (confirmed). Mitigated by the novelty strategy above; fallback venue if the findings are weak.
- The timeline is tight. If needed, Evaluation 5 (pushforward) is the first candidate to shrink.
