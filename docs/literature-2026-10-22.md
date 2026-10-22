# Literature pass for the reorientation (2026-10-22)

First pass for "feature provenance in malware classification: bridging the feature-problem space gap". Read at the
abstract / summary level unless marked **[full]**; the closest papers (marked **read next**) must be read in full before
any direction is built.

## The finding that changes direction A

Our P records **contribution**: which bytes of *this* file produce each feature's current value. Direction A needs
**dependency** (influence): which features *could* change if an attacker rewrites a byte set S, including features that
new content in S would create (a URL written into slack raises the URL-string count; P of the original file credits
those bytes only to the byte histogram) and features that change through the parse (control dependence: a header field
that relocates a section changes everything read from it). These are different objects. Cheney, Ahmed & Acar
("Provenance as Dependency Analysis") make the same distinction in databases: why/where/how-provenance (what produced an
output) vs. dependency provenance (what an output depends on); minimal dependency provenance is not computable, but
dynamic and static approximations exist. For A, the instrumented extractor must record *reads* (and ideally control
dependence), not only contributions. The existing P is right for removal/overwrite questions ("what is lost by
overwriting S"), wrong for addition questions ("what can S be made to say").

## Naming

- "Feature provenance" is used in MLOps for pipeline lineage (how a feature column was generated; Hopsworks, reproducible
  ML pipelines; a patent on "feature provenance graphs" for discarded features). No byte-level use found. Usable if
  the first paragraph defines it.
- Established names for the underlying ideas: where-/how-provenance and provenance semirings (Buneman; Green et al.;
  survey Cheney, Chiticariu & Tan 2009), dependency provenance (Cheney et al.), dynamic information-flow / taint
  tracking (security). Reviewers will expect these cited and the difference stated.

## Direction A: problem-space constraints for feature-based detectors

Crowded. What exists:
- **Pierazzi et al. (S&P 2020)**: problem-space attack formalization; side-effect features; Android transplantation.
  **read next** (side-effect features are what dependency provenance computes; check how they obtain them).
- **Labaca-Castro et al., "Realizable Universal Adversarial Perturbations for Malware"** (arXiv 2102.06747; venue to
  check): includes Windows/EMBER LightGBM; chains of 10 byte-level transformations; measures the features each
  transformation moves (empirically); hardening by sampling per-feature modification probabilities (independence
  assumption). UER drops from ~34% to ~0.1% at a TPR cost. **read next**: this is the realistic, empirical alternative
  to a provenance-derived constraint set.
- **Gimenez, Sivaprasad & Fritz, "Certifiably robust malware detectors by design"** (arXiv 2508.10038, 2025, CISPA;
  venue to check): EMBER features; robustness via monotonicity (monotone feature map w.r.t. the threat model's preorder
  + monotone classifier); feature selection from empirical perturbation vectors of secml-malware attacks (PV: keep
  features never decreased) and a manual 40-feature set that "could not be transposed to another domain without the
  help of an expert". 100% robustness with PV selection + random forest against the 8 attacks used. **read next**:
  closest competitor; PV selection only covers attacks it has seen.
- **Bostani et al., "Level Up with ML Vulnerability Identification"** (TOPS 2025; arXiv 2205.15128): learns feature-space
  domain constraints from data (Drebin) for realizable adversarial training; 77.9% robustness gain vs. unknown
  problem-space transformations.
- **Dyrmishi et al. (S&P 2023)**: unrealistic feature-space hardening fails to protect malware detectors against
  realistic (AIMED) attacks. Motivation for realistic constraints.
- **Rosenberg et al. (IJCNN 2020)**: explanation-guided end-to-end attack on EMBER; feature-specific, hand-written
  modifications for a few feature groups; hashed and interdependent features called hard or impossible. Motivation.
- Also: Chen et al. (USENIX Sec 2020, PDF property-based robustness), Incer et al. (2018, monotonic), Kantchelian et al.
  (2016, tree evasion/verification), Demetrio et al. (TOPS 2021, GAMMA; secml-malware), MAB-Malware (AsiaCCS 2022),
  Lucas et al. (adversarial training for raw binaries), DRSM / RS-Del (certified raw-byte models).

**What could remain new:** deriving the threat-model constraints (which features an action on a byte region can move,
and in which direction) from the instrumented extractor, independently of any attack library, with a completeness
argument that empirical perturbation vectors lack. Falsifiable against Gimenez et al.'s PV selection and Labaca-Castro's
empirical probabilities on **held-out** attack families. Not new: problem-space attacks, monotone robustness, learned
or empirical constraints.

## Direction B: backdoors / shortcuts

- Severi et al. (USENIX Sec 2021): explanation-guided clean-label backdoors on EMBER-feature models (triggers realized
  in the binary by a watermarking tool); Jigsaw Puzzle (S&P 2023); explanation-aware backdoors (Noppel et al.); PBP
  (arXiv 2412.03441) and generic defenses (MNTD, Neural Cleanse, spectral signatures).
- No malware-specific trigger reverse-engineering defense found in this pass; backdoors in raw-byte models are less
  studied (a Politecnico di Milano thesis on MalConv backdoors). Gap plausibly open; needs a targeted search.
- Note a second variant: for feature-space triggers (Severi), the defender wants the trigger's bytes in poisoned
  training files, which is a pullback question.

## Direction C: evasion diagnosis in ensembles

- **Smutz & Stavrou, "When a Tree Falls" (NDSS 2016)**: mutual agreement in ensembles flags evasion without ground
  truth (PDF, Android). The realistic baseline for C. **read next.**
- Salman et al. (SECAI 2024): adversarial binaries transfer poorly across detectors; ensembles reduce impact.
- No explanation-consistency evasion detector for malware found (exists for images). Gap plausibly open; the score-only
  baseline is strong.

## Sources

- https://arxiv.org/html/1911.02142 (Pierazzi et al.)
- https://arxiv.org/html/2102.06747 (Labaca-Castro et al.)
- https://arxiv.org/html/2508.10038v1 (Gimenez et al.)
- https://arxiv.org/abs/2205.15128v4 (Bostani et al.)
- https://arxiv.org/pdf/2202.03277 (Dyrmishi et al.)
- https://arxiv.org/html/2009.13243v2 (Rosenberg et al.)
- https://arxiv.org/pdf/0708.2173 (Cheney et al.)
- https://homepages.inf.ed.ac.uk/jcheney/publications/provdbsurvey.pdf (Cheney, Chiticariu & Tan)
- https://arxiv.org/pdf/2003.01031 (Severi et al.)
- https://arxiv.org/pdf/2202.05470 (Jigsaw Puzzle)
- https://arxiv.org/pdf/2412.03441v2 (PBP)
- https://www.ndss-symposium.org/wp-content/uploads/2017/09/when-tree-falls-using-diversity-ensemble-classifiers-identify-evasion-malware-detectors.pdf
- https://arxiv.org/pdf/2408.02310 (Salman et al.)
- https://arxiv.org/pdf/2303.13372 (DRSM)

## Full reading, second pass (2026-10-22, later)

Read in full or in the relevant sections: Gimenez et al. **[full]**; Labaca-Castro et al. (Windows sections) **[full
for 4.3]**; Pierazzi et al. (formalization, side-effect features, ice-box) **[sections]**; Smutz & Stavrou (method)
**[sections]**; Severi et al. (Windows watermarking utility) **[sections]**; RAMP, Perasso et al. (abstract/intro).

- **Pierazzi et al.**: side-effect features "cannot be feasibly computed in advance for each possible object"; they
  estimate them empirically by injecting each gadget into a minimal app (the ice-box). Corollary 2.1: an attacker can
  restrict the search to the subspace X_eq where a feature-space change has a known problem-space equivalent. Our hook:
  instrumentation computes X_eq and side effects a priori, for local transformations.
- **Labaca-Castro et al.**: "the effect that an individual transformation (e.g., 'UPX pack') will have on the input
  binary, and thus, in the feature space, cannot be calculated a priori." EMBER LightGBM; 10 transformations; the
  strongest is UPX packing (rewrites the file; out of reach for provenance). Hardening samples per-feature modification
  probabilities, assuming independence (acknowledged as a simplification).
- **Gimenez et al.**: LNCS-format preprint, venue unknown. Robust = monotone feature map w.r.t. the threat model's
  preorder + monotone classifier (Prop. 1). PV feature selection keeps features never decreased by the perturbation
  vectors of 8 secml-malware attacks, and is evaluated against **the same 8 attacks** (200 malware, 60 s each): no
  held-out attacks. PV keeps 0% of byte and 1.9% of string features. The manual 40-feature set needs an expert.
- **Severi et al.**: hand-built pefile watermarking tool; discarded **all hashed features** ("preimage resistance") and
  features "impacted by more than one other feature" (e.g., num_sections vs. num_write_sections), leaving 17 of
  ~2,400. Two openings: feature interdependence is shared provenance (overlapping columns of P); and hashed buckets are
  not preimage-resistant in practice (few buckets: a name landing in a chosen bucket is found by brute force).
- **Bostani et al.**: learn feature dependencies from data (Drebin); cite Sheatsley et al. (formal-logic learned
  constraints) and Erdemir et al. To read: Sheatsley et al.
- **B:** RAMP (Xin et al., arXiv 2609.27422, Sep 2026): clean-label backdoors against MalConv / MalConvGCG via
  fine-tuning. Perasso et al. (Ital-IA 2025, Demetrio/Roli group): IG summed over hand-chosen regions (compiler slack
  etc.) to quantify spurious reliance of raw-byte models: the region-overlay competitor for B. PBP purifies; no
  trigger-identification defense for raw-byte detectors found.
- **C:** Smutz & Stavrou: vote disagreement in a feature-bagged ensemble marks most evasion attempts on PDFrate and
  Drebin "uncertain", without ground truth. PASA (Bhusal et al., arXiv 2404.10789): attribution sensitivity to noise
  detects adversarial inputs (images, some non-image). No cross-member explanation-agreement detector for malware found.

Remaining papers: see the third pass below.

- https://arxiv.org/pdf/2609.27422 (RAMP)
- https://arxiv.org/pdf/2506.09662 (Perasso et al.)
- https://arxiv.org/pdf/2404.10789 (PASA)

## Third pass: remaining papers (2026-10-22, later)

- **Sheatsley, Papernot, Weisman, Verma & McDaniel, "Adversarial Examples in Constrained Domains"** (arXiv 2011.01183;
  J. Computer Security 2022) **[sections]**. Network intrusion detection (NSL-KDD, UNSW-NB15). Constraints: fixed value
  types, correlated features (protocol fixes which flags exist), features the adversary cannot control. Constraints are
  learned from data around "primary features" chosen by domain knowledge, and resolved during crafting (Algorithm 1).
  Finding: constrained domains are not robust (>95% misclassification; five random controllable features suffice).
  For us: the standard way to get constraints is to learn them from data or state them by hand; nobody derives them
  from the feature extractor.
- **Chen, Wang, She & Jana, "On Training Robust PDF Malware Classifiers"** (USENIX Sec 2020; arXiv 1904.03542)
  **[sections]**. Problem-space robustness properties on the PDF tree (insert or delete any subtree under the root,
  distance k), each mapped to an **over-approximated** set of feature vectors, then verifiably robust training with
  symbolic interval analysis; 92.27% verified robust accuracy at 99.74% accuracy; adaptive attackers need up to 10x L0
  and 21x mutations. The mapping from a subtree operation to the features it can change is trivial for Hidost, whose
  features *are* tree paths. **This is the precedent that the "which features can an operation reach" object is useful:
  it is exactly the input region verified training needs.** For EMBER-like extractors no such mapping exists.
  Also restates Incer et al.: monotonic classifiers cost ~13% temporal detection.
- **Rosenberg et al., "Generating End-to-End Adversarial Examples for Malware Classifiers Using Explainability"**
  (IJCNN 2020; arXiv 2009.13243) **[sections]**. Explain, then modify the most important *easily modifiable* features
  one by one with feature-specific, hand-written modifiers; "each feature's modification requires a manual effort";
  modifying one feature can require modifying others. Motivation for automatic realization.
- **Incer, Theodorides, Afroz & Wagner, "Adversarially Robust Malware Detection Using Monotonic Classification"**
  (IWSPA 2018). **Not accessible** (no arXiv version; ACM DL). Secondary sources: monotone classifier over features
  chosen as hard to decrease; 62% temporal detection at 1% FPR, ~13% below an unrestricted classifier. Ask the user
  for the PDF.
- **Yang et al., "Jigsaw Puzzle"** (S&P 2023; arXiv 2202.05470) **[sections]**. Selective clean-label backdoor for
  Android (Drebin features), realized with harvested bytecode gadgets; existing Severi-style backdoors are detected by
  MNTD; JP evades MNTD, Neural Cleanse, Activation Clustering. Defenses evaluated are generic (data- and model-level).
- **Nguyen et al., "PBP: Post-training Backdoor Purification for Malware Classifiers"** (arXiv 2412.03441, v4 Feb 2026)
  **[sections]**. EMBER (EmberNN) and AndroZoo; fine-tunes batch-norm statistics to purify; trigger-agnostic; notes
  that most malware backdoor defenses detect poisoned samples through ensemble disagreement on training data. No
  trigger identification, no raw-byte model.
- **Bhusal et al., "PASA"** (arXiv 2404.10789; RIT) **[abstract + setup]**. Unsupervised adversarial detection from
  the sensitivity of predictions and attributions to noise; image datasets plus CIC-IDS2017; small-norm attacks (FGSM,
  PGD, BIM, CW), not problem-space malware attacks.
- **Cheney, Ahmed & Acar, "Provenance as Dependency Analysis"** (MSCS 2011; arXiv 0708.2173) **[sections]**.
  Distinguishes where-provenance (the input part a value was copied from; Buneman et al. 2001) from dependency
  provenance (every input part an output depends on, "dependency correctness"); minimal dependency provenance is not
  computable; dynamic and static conservative approximations. The semantic (not implementation-word) way to separate
  "what produced this value" from "what could change it".

- https://arxiv.org/pdf/2011.01183 (Sheatsley et al.)
- https://arxiv.org/pdf/1904.03542 (Chen et al.)
- https://arxiv.org/pdf/2009.13243 (Rosenberg et al.)
- https://arxiv.org/pdf/2404.10789 (PASA)

## Incer et al. (read from `papers/incer.pdf`, 2026-10-22)

- **Incer, Theodorides, Afroz & Wagner, "Adversarially Robust Malware Detection Using Monotonic Classification"**
  (IWSPA 2018) **[full]**. Boolean features from VirusTotal reports (Miller et al.'s feature set: imports, file
  operations, registry, processes, signers, packer detections; mostly dynamic). A **manual, per-feature** threat
  analysis sorts every feature into four cases: (1) cannot be changed cheaply, (2) only false->true, (3) only
  true->false, (4) either way; features of case (4) are dropped, counts are re-encoded as monotone thresholds (>= 2^k),
  packer and signer features are re-aggregated to become monotone. XGBoost with monotone constraints; ~1.1M binaries;
  62% temporal detection at 1% FPR, ~13 points below an unconstrained classifier; no attack is run (security follows
  from monotonicity + the threat analysis). 8 of 13 feature categories kept (header metadata, mutexes, API n-grams
  dropped).
  For us: the four cases are a **generic, domain-independent** description of what a threat model allows per feature
  (which directions are reachable), and Incer et al. obtain it by hand; Gimenez et al. by perturbation vectors.
