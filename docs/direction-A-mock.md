# Direction A: mock of the paper's tables (2026-10-22)

All numbers below are **invented** to show the shape of the result; nothing has been run. Per
`mock-the-result-first`: each column names the model component (`docs/feature-provenance-model.md`) that produces it,
and the go/no-go checks at the end say what would sink the direction.

## The pitch in plain terms

A robust malware detector needs to know, for its threat model, which features an attacker can push in which direction.
Today this comes from experts (Incer et al. sort every feature by hand; Gimenez et al.'s 40 hand-picked features) or
from running attacks and watching what moves (Gimenez et al.'s perturbation-vector (PV) selection; Labaca-Castro et
al.'s per-feature probabilities). Gimenez et al.'s guarantee (their Proposition 3) **assumes the set of perturbation
vectors of the threat model is finite and known**; in practice they estimate it from 8 attacks and evaluate against
the same 8. Our model computes that set (or a sound superset) from the instrumented extractor: C4 gives each feature's
reachable directions, C3 the reachable region. Two consequences:

1. **Soundness against attacks nobody has run.** PV selection keeps any feature its sample of attacks happened never
   to decrease. A hashed section-name bucket is two-sided under "add a section with any name" (signed hashing), but a
   few hundred GAMMA runs with random names visit only some of the 50 buckets with each sign; PV keeps the rest. An
   attacker who chooses the name defeats it. C4 knows every such bucket is two-sided.
2. **Accuracy recovered by reading the sums instead of the features.** Under an add-only threat model every sum with
   nonnegative contributions can only grow; what destroys monotonicity is the readout (normalizing histograms by the
   file size, entropies, min) and signed hashing. Feeding the monotone classifier the layer-2 sums (raw byte counts
   instead of frequencies; each signed bucket split into its positive and negative parts) keeps most of the
   information while staying sound. This is the transformation Gimenez et al.'s ERDALT *learns* from adversarial
   examples (a linear layer that maps perturbations to nonnegative values); the model *derives* it.

## Table A0: does C1 predict the edited file's features? (foundation)

Per transformation of the coverage table (model doc, Section 6), on the pilot malware: apply it, predict φ(z') with
C1 from z's item table, re-extract z', compare.

| Transformation (Section 6 row) | Files | Exact on all features | Mismatching features (mean) | Predict / re-extract time |
|---|---|---|---|---|
| append bytes (1) | 100 | 100% | 0 | 1 / 40 |
| write slack (2) | 100 | 100% | 0 | 1 / 40 |
| rename section (7) | 100 | 100% | 0 | 1 / 40 |
| remove signature (10) | 23 signed | 100% | 0 | 1 / 40 |
| add section (11), pefile writer | 100 | 97% | 0.1 (pefile warnings) | 1 / 40 |
| add section (11), LIEF builder | 100 | 61% | 14 (LIEF rewrites headers) | 1 / 40 |
| ... | | | | |

Component: C1 with A1-A4. Ground truth: re-extraction (no competitor; this is the validity check). The LIEF row is
expected to fail and is reported as what it is: a tool side effect the model exposes (A4).

## Table A1: monotone detectors under a threat model (main result)

Threat model M: the add-only transformations of Section 6 with attacker-chosen content and names (append, slack,
add section, add imports, rename, header fields, DOS header), within a byte budget. Classifier: LightGBM with
monotone constraints (the GBDT is the first classifier; Gimenez et al.'s monotone GBT is the direct comparison).
Attacks: **seen** = secml-malware (Gimenez et al.'s setup); **held-out** = MAB-Malware and Labaca-Castro et al.'s
actions restricted to M; **adaptive** = an attacker who knows the kept features and searches M for moves that lower
the score (built with C1; see A2).

| Feature set (how directions are obtained) | Features kept | AUC | TPR @ 1% FPR | Evasion: seen | held-out | adaptive | Cost to derive |
|---|---|---|---|---|---|---|---|
| all features, unconstrained GBDT | 2,568 | 97.5 | 88 | 25% | 31% | 90% | none |
| adversarial training (empirical) | 2,568 | 97.6 | 87 | 3.5% | 12% | 60% | attack runs |
| PV selection, seen attacks (Gimenez) | 610 | 93.8 | 71 | 0% | 6% | 38% | 8 attacks x 200 files x 60 s |
| PV selection, all three toolkits | 540 | 93.1 | 69 | 0% | 0% | 21% | 3 toolkits x 200 files |
| manual, expert (Gimenez's 40 / Incer-style) | 40 | 86.0 | 52 | 0% | 0% | 0% | expert, not transferable |
| **C4 directions on features (ours)** | 380 | 91.0 | 63 | 0% | 0% | **0%** | one pass over the extractor |
| **C4 directions on layer-2 sums (ours)** | 1,900 | 95.5 | 80 | 0% | 0% | **0%** | one pass over the extractor |

Components behind the columns:
- *Features kept*: C4's global direction per feature (sign test, ratio test, cross-entropy test); for the last row,
  C4's sign test on the layer-2 sums, with each signed bucket split into two nonnegative sums.
- *Evasion: adaptive = 0% for our rows*: a guarantee, not a measurement artifact; it follows from C4 (every kept input
  is up-only under M), Gimenez et al.'s Proposition 1 (monotone feature map + monotone classifier), and A1-A4. The
  measured adaptive attack can only confirm it; a nonzero value is an A1-A4 failure (a bug in the guarantee).
- *Evasion: seen / held-out*: measured by running the attacks (no model component).
- *Cost*: the model needs the instrumented extractor and the threat model's catalogue, never an attack run.

Paper sentence this table must support (mock): "Perturbation-vector selection is as robust as its sample of attacks:
an adaptive attacker who picks section names and content within the same threat model evades it on 38% of files. The
directions computed from the extractor admit no such attack by construction, and reading the extractor's sums instead
of its normalized features recovers most of the accuracy that soundness costs (AUC 95.5 vs. 97.5 unconstrained,
against 91.0 for the features alone and 86.0 for the expert set)."

## Table A2: the adaptive attack (attack side; optional, supports A1's adaptive column)

For each defense in A1, a C1-guided attack: search over operations in M (catalogue items, names, contents), scoring
candidates on the predicted feature vector, re-extracting only the final file.

| Target | Attack | Evasion | Model queries | Extractions | Bytes added (median) |
|---|---|---|---|---|---|
| PV selection, seen | MAB-Malware | 6% | 1,200 | 1,200 | 9 KB |
| PV selection, seen | GAMMA (sections) | 4% | 5,000 | 5,000 | 120 KB |
| PV selection, seen | **C1-guided (ours)** | 38% | 400 | 1 | 4 KB |
| C4 on sums (ours) | C1-guided | 0% | 400 | 1 | |

Components: C1 (predicted φ for every candidate), C4 (which kept features M can lower: the attack targets those).
Baselines: the query-based problem-space attacks a practitioner would run. This is "provenance on both sides" (nice to
have, not required): the same model breaks the empirical defense and certifies its own.

## Realistic baselines (why these)

- **Gimenez et al.'s PV selection** and **ERDALT**: the closest work (same features family, same guarantee route). PV
  is evaluated by them only on the attacks it was derived from; ERDALT is empirical (needs adversarial examples).
- **Labaca-Castro et al.'s hardening** (sampled per-feature modification probabilities): the empirical alternative
  on the same toolkit; represented by the adversarial-training row (or added as its own row if the numbers differ).
- **Expert sets** (Gimenez's 40; Incer et al.'s four-case analysis): sound but manual and conservative.
- Not a baseline: Severi et al.'s 17 features (an attack-side restriction, not a defense; cited as motivation).

## Go/no-go checks (falsifiable, before building the defense)

1. **C1 holds (Table A0).** On the pilot files, C1 matches re-extraction exactly on >= 95% of (file, transformation)
   pairs for the pefile-written transformations, with every mismatch explained by a listed A1-A4 failure.
   *No-go:* systematic unexplained mismatches; the guarantee in A1 would rest on sand.
2. **PV selection has a hole the GBDT uses.** Compute PV selection from secml-malware's perturbation vectors on the
   pilot malware, and C4's directions on paper. *Go* if the features PV keeps but C4 marks decreasable under M carry a
   material share of the PV-selected GBDT's gain (say >= 5%). *No-go:* if that set is empty or unused, the adaptive
   column cannot separate us from PV, and A1's advantage shrinks to "no attack runs needed" (cost only), which is not
   enough on its own; rethink A1 before training anything.
3. **Soundness does not cost the detector.** The C4-on-sums monotone GBDT stays within ~2 AUC points of PV selection
   (Gimenez et al. report 93.8 for PV + GBT). *No-go:* a drop beyond ~5 points ("sound but useless", Incer et al.'s
   13-point drop); then the sums-rewrite idea has failed and A1 is a negative result for monotone detectors.

Hypothesis for check 2: the hole exists mainly in signed hashed buckets (section names, characteristics) and in
fields secml-malware never touches but other toolkits or an adaptive attacker can lower (the checksum, zeroed by BC).

## Harsh notes on novelty

- The guarantee route (monotone feature map + monotone classifier) is Gimenez et al.'s and Incer et al.'s; the
  verified-training route (C3 regions) is Chen et al.'s. What is ours: computing the threat model's perturbation set
  from the extractor, soundly, so that their guarantees hold against attacks nobody ran; and deriving the monotone
  re-encoding (sums, split signed buckets) that ERDALT learns.
- A reviewer may say "splitting signed hashing and un-normalizing histograms is obvious once stated." The answer must
  be the full, automatic derivation across every feature group and readout, plus the measured hole in PV selection
  (check 2). If check 2 fails, that answer is weak.
- To read before building: Treant (Calzavara et al.: training trees against attacker rewriting rules on features; our
  directions could be its rules) and Chen et al., "Learning Security Classifiers with Verified Global Robustness
  Properties" (CCS 2021: global properties such as monotonicity specified by hand).
- Removal transformations (remove signature, remove debug) are outside the add-only threat model; including them makes
  the affected features two-sided (dropped or treated as down-only). Report which threat model each row assumes.
