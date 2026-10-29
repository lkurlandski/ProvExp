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

## Not yet read

- HRAT (Zhao et al., CCS 2021): graph edits with known feature effects, Android. Now in `papers/HRAT2021.pdf`
  (user, 2026-10-29).
- Demontis et al., "Yes, Machine Learning Can Be More Secure! A Case Study on Android Malware Detection" (IEEE TDSC
  2017): secure linear classifiers under feature-addition/removal attackers with per-feature bounds (added by the
  user, 2026-10-29). Read for A (closest to "constrain weights by what the attacker can change") and A'.
- Šrndić & Laskov (S&P 2014): approximate inverse mapping for PDF.
- Verifiable boosted tree ensembles (arXiv 2402.14988): exact verification for LightGBM-style models.

## Harsh read for A'

- **The novelty is one thing:** side effects and reachable constraints computed from the extractor, for every
  feature, with each feasible vector tied to the edits that produce it. Everything around it (the attack, the
  constraints framework, hash targeting) is prior work.
- **That novelty is only real once the derivation is automatic.** The direction-A directions and predictors are
  still hand-written (`docs/direction-A-threat-model.md` S2). Until that changes, A' is "Rosenberg with better
  hand-written modifiers".
- **The strongest uses are probably defensive or evaluative, not attacks on undefended models.** Black-box attacks
  already do well against an unconstrained GBDT. Two candidates:
  - worst-case realizable robustness of a detector, computed exactly (Kantchelian-style, over the computed constraints);
  - realizable examples for adversarial training, the Level Up use, for Windows with computed constraints.
