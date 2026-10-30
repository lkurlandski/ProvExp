# Literature for A' (from feature-space targets to real file edits), 2026-10-27

Purpose: judge A''s novelty against the closest work on the same task. Read in sections; PDFs in `papers/`. Earlier
notes on several of these papers: `docs/literature-2026-10-22.md`.

## Summary

Three lines of work touch the task, and each stops short of it in a different place:

1. **Problem-space attacks** edit files and query the detector (Pierazzi et al.; EvadeDroid; GAMMA; MAB-Malware; the
   nine attacks benchmarked by Zainab et al. 2026). They learn each edit's effect on the features by trial, from a
   pre-measured library, or not at all.
2. **Feature-space attacks with hand-written realizers** (Rosenberg et al.; Severi et al.; Kucuk & Yan) choose
   feature changes first and then realize them with modifiers written per feature. Features they cannot realize by
   hand are excluded.
3. **Constrained feature-space attacks** (Sheatsley et al.; Simonetto et al.; Dyrmishi et al.; Bostani et al., who
   learn the constraints) take a constraint set as input and return vectors, not files. For PE malware the
   constraints are a few hand-written relations.

Nobody computes the constraints, or each edit's side effects, from the extractor itself. That is the only part of A'
that is new. The attack, the hash-bucket trick, and the concept of side effects all come from prior work.

## Papers

**Pierazzi / Cortellazzi et al.** (S&P 2020; extended version TOPS 2024, arXiv 1911.02142v3).
- **What they do:** the formal framework for problem-space attacks, including side-effect features. They argue
  side-effect features cannot be expressed in closed form, so they estimate them empirically (Android only).
- **For us:** we take the concepts from them. Our claim is narrower: for an instrumented extractor, side effects of
  local edits are computable in advance.

**Severi et al.** (USENIX Security 2021).
- **What they do:** backdoors in EMBER-feature models. They discarded hashed features, citing preimage resistance,
  and features coupled to others, which left 17 usable features.
- **For us:** the clearest statement of the limitation A' would lift.

**Rosenberg et al.** (IJCNN 2020).
- **What they do:** explanation-guided feature changes on EMBER, realized with per-feature, hand-written modifiers.
- **For us:** they already note that a hashed bucket can be targeted by choosing a suitable value. The hash-bucket
  idea is therefore not ours, and A' must not claim it.

**Labaca-Castro et al.** (arXiv 2102.06747).
- **What they do:** universal perturbations on EMBER and DREBIN. They state that a transformation's feature effect
  cannot be calculated a priori, and harden with sampled per-feature change probabilities (assuming independence).
- **For us:** the empirical alternative our computed effects should replace.

**Kantchelian et al.** (ICML 2016).
- **What they do:** an exact mixed-integer program for evading tree ensembles in feature space.
- **For us:** a natural source of feature-space targets. Also a way to compute worst-case robustness exactly once the
  attacker's reachable set is expressed as linear constraints.

**Simonetto et al.** (IJCAI 2022).
- **What they do:** a framework for constrained feature-space attacks.
- **For us:** for the PE malware dataset they use, the constraints are 88 immutable features and 7 relations, written
  by hand. It is the closest "constraints as input" competitor.

**Sheatsley et al.** (JCS 2022; earlier notes).
- **What they do:** learn constraints from data around hand-chosen primary features.

**Bostani et al., "Level Up"** (TOPS 2025).
- **What they do:** learn Android feature-space constraints from data. Adversarial training on vectors that satisfy
  the learned constraints is much faster than training on problem-space examples, and still improves robustness
  against unseen problem-space transformations.
- **For us:** the closest precedent for using realizable feature-space examples defensively. A Windows version with
  computed constraints is a candidate use for A'.

**Dyrmishi et al.** (S&P 2023).
- **What they do:** hardening on unrealistic examples often fails against realistic attacks.
- **For us:** motivation for realizable examples.

**PAD (Li et al., TDSC 2023)** and **EvadeDroid (Bostani & Moonsamy, C&S 2024).**
- **What they do:** both name side effects as the obstacle to inverting the feature map. PAD uses an approximate
  inverse; EvadeDroid avoids the inverse entirely with a black-box search.
- **For us:** both are Android.

**Zainab et al., "Breaking Windows Malware Detection"** (arXiv 2609.34456, Sep 2026).
- **What they do:** benchmark nine problem-space attacks against eight Windows detectors, including EMBER GBDTs.
- **For us:** none of the nine starts from a feature-space target. This is the current state of the field A' would
  enter.

**Gimenez et al.** (arXiv 2508.10038): see `docs/direction-A-expert-set.md`.

## Read 2026-10-30 (step 1 of the A' pilot)

The question for each paper: does it already compute what a file edit does to the features, for an extractor with
hashing, normalization, ratios, and entropy? None does. Two of the four are useful to us: Šrndić & Laskov state the
problem as infeasible, and HRAT is a precedent for editing an intermediate structure.

**Šrndić & Laskov, "Practical Evasion of a Learning-Based Classifier: A Case Study"** (S&P 2014; Mimicus).
- **What they do:** evade PDFrate, a random forest over 135 regex-count features. Content is injected between the
  cross-reference table and the trailer, where readers skip it but the extractor counts it. Their modifier can set 35
  features freely and only increase 33; which features fall in which group was worked out by hand ("time-consuming
  expert work"). A feature-space target is turned into a file "opportunistically", one feature at a time, and the
  side effects are left to chance. Their Fig. 4 shows the result: `author_len` 11 instead of 0, and `pos_acroform_*`
  shifted by the size change. Per-feature bounds are the minimum and maximum seen in the dataset.
- **For us:** the clearest statement of the problem in the literature: "It is neither feasible to enumerate all
  feature interdependencies and account for their effects a priori, nor to identify invalid data points before
  translation to problem space." A' claims the opposite for local edits on an instrumented extractor, and their
  side-effect example is a C1 prediction. Their bounds from data are the learned-constraints baseline, as in check 1.
  No threat to novelty; cite it in the motivation.

**HRAT, Zhao et al., "Structural Attack against Graph Based Android Malware Detection"** (CCS 2021).
- **What they do:** edit the function call graph rather than the feature vector. There are four actions (add an edge,
  rewire, insert a node, delete a node), each with a code transformation that keeps the app working. Features
  (MaMaDroid's call probabilities, MalScan's centralities) are recomputed by running the extractor on the edited
  graph. The choice of edit comes from gradients through a differentiable re-implementation of the extractor, with an
  RL policy picking the action type. Section 3.4 argues, by hand, which way each action moves each feature family
  (adding a node lowers degree centrality, deleting a node lowers a call probability). The extracted graph equals
  the computed one on their checked apps, so the inverse-mapping problem disappears for features that are a function
  of the graph.
- **For us:** a precedent for "edit an intermediate structure whose features follow from it", which is what our item
  layer does. But the mapping there is free: the graph *is* the input to the extractor, so recomputing is running the
  extractor. Their direction analysis is written by hand per feature family. They compute no reachable set, magnitude
  bound, or certificate, and there is no hashing or entropy. The threat is to a framing, not to the claim. We must not
  present "edit items, not features" as new. Our contribution is computing which items an edit touches and how each
  readout turns them into feature values, and using that for sets of edits (directions, bounds), not only replaying
  one edit.

**Demontis et al., "Yes, Machine Learning Can Be More Secure!"** (TDSC 2019, online 2017).
- **What they do:** Drebin with binary features. The attacker adds features, or adds and removes them. Which ones
  can be removed is argued by hand per feature family: manifest permissions cannot be removed; dexcode URLs can be,
  by encryption. Sec-SVM bounds every weight to a box `[w_lb, w_ub]` (two scalars, cross-validated) so that the
  weights spread more evenly. Sec-SVM (M) keeps only the manifest features, which cannot be removed, and loses
  accuracy.
- **For us:** for A, the box constraint is uniform, not per direction, and it limits the gain per feature rather
  than ruling out a direction. Sec-SVM (M) is a hand-chosen add-only feature subset, close to PV and Incer in spirit,
  not a monotone constraint in derived directions. For A', there is no edit-to-feature mapping; the feasible changes
  are the hand-stated "add any feature, remove some". No threat to novelty; cite it as the origin of
  threat-model-aware secure learning for malware.

**Calzavara et al., "Verifiable Boosted Tree Ensembles"** (arXiv 2402.14988, 2024; follows their large-spread
ensembles).
- **What they do:** train boosted ensembles with "large spread" so that verification is polynomial under an
  L-infinity attacker and pseudo-polynomial under L-p attackers; general verification stays NP-hard.
- **For us:** the attacker is a norm ball in feature space, with no linear or semantic constraints, no problem-space
  edits, and no malware. It needs the model trained their way, so it cannot verify our GBDTs or PV. It is not the
  fallback solver: check 0 showed Kantchelian's MIP decides at our size in under 34 s, and our region (counts,
  buckets, mixtures) is not a norm ball. Cite it among tree-ensemble verifiers. No threat.

A targeted search (2026-10-30) for certified or verified robustness of Windows PE detectors under problem-space
constraints found nothing beyond Gimenez et al. (monotone, hand-written add-only model) and the attack benchmarks
already listed (Zainab et al.).

## Not yet read

- (none from the step-1 list)

## Harsh read for A'

- **The novelty is one thing:** side effects and reachable constraints computed from the extractor, for every
  feature, with each feasible vector tied to the edits that produce it. Everything around it (the attack, the
  constraints framework, hash targeting) is prior work.
- **That novelty is only real once the derivation is automatic.** The direction-A directions and predictors are
  still hand-written (`docs/direction-A-threat-model.md` S2). Until that changes, A' is "Rosenberg with better
  hand-written modifiers".
- **"Edit an intermediate structure, not the features" is not new** (HRAT edits call graphs; Chen et al. edit PDF
  tree paths). Where the structure *is* the extractor's input, the mapping is free. Ours is not free: an edit touches
  items that hashed, normalized, ratio, and entropy readouts turn into features, and the mapping is computed and checked.
  Šrndić & Laskov's "neither feasible to enumerate all feature interdependencies ... a priori" is the statement we
  answer for local edits.
- **The strongest uses are probably defensive or evaluative, not attacks on undefended models.** Black-box attacks
  already do well against an unconstrained GBDT. Two candidates:
  - worst-case realizable robustness of a detector, computed exactly (Kantchelian-style, over the computed constraints);
  - realizable examples for adversarial training, the Level Up use, for Windows with computed constraints.
