# ProvExp Research Plan: Feature Provenance in Malware Classification

Living document, restarted 2026-10-22. The previous plan (explanation provenance for explainable ML, the pullback and
pushforward of explanations) is archived in `docs/archive/PLAN-explanation-provenance-2026-10-21.md`; why it was
abandoned is in `docs/graveyard.md`. Deadlines and conference cycles are not a planning constraint (user).

## Why we restarted (2026-10-22)

The explanation-provenance paper was built method first, with applications found afterwards. A simulated CCS review
(`REVIEW-2026-10-21.md`) rated it weak reject; the user judged it far weaker (strong reject: not novel, no compelling
utility to the security community) and agreed with the diagnosis: where flat provenance is precise (named header
fields) it is not needed, where it would be needed (hashed and aggregate features) it is diffuse, and every
application landed on the first side. We had also misjudged our novelty by not grasping the related work.

## Thesis

**Simple feature provenance (which problem-space elements produce which features, through which items) bridges the
feature-problem space gap in malware classification.** Every line of work on realizable attacks and robust detectors
needs, for a file and a threat model, what the attacker can reach in feature space; each gets it by hand, from data,
or by running transformations. Instrumenting the extractor computes it automatically and, for most features,
exactly. One framework answers several problems that the literature treats separately.

Framing: a malware-classification paper, as generic to malware as possible (PE is the instance; avoid format minutiae
in the argument). Elements are any problem-space units (bytes, characters, tokens, packets).

## The model (`docs/feature-provenance-model.md`)

Three layers: the parse (elements -> items: membership and location), contributions (items -> sums, additive), the
readout (sums -> features: identity, normalization, entropy, max, presence). Edits are stated in bytes and translated
to item operations: content edits (exact), item-creating edits (local re-recognition), structural edits (flagged).
Claims to prove: C1 exact side effects; C2 coupling between features; C3 reachable sums under add-only threat models
(a sound over-approximation for verified training); C4 per-feature reachable directions (Incer et al.'s four cases,
automatically). Today's flat P is the projection of the model onto elements x features; it may serve as the intuitive
introduction and a simple baseline (writing decision for later).

## Directions (A is the core; each must survive its own screening or is dropped)

- **A. Threat models to feature space.** Side effects, coupling, reachable directions and regions computed from the
  instrumented extractor; uses: realizing feature-space attacks in the problem space (including hashed features that
  Severi et al. ruled out), and robust or verifiably robust detectors from derived constraints (Incer, Gimenez, Chen).
  Realistic baselines: Gimenez et al.'s perturbation-vector feature selection and Labaca-Castro et al.'s empirical
  per-feature probabilities, evaluated on **held-out** attack families; Severi et al.'s 17 hand-picked features;
  Rosenberg et al.'s hand-written modifiers.
- **B. Auditing raw-byte detectors for backdoors and shortcuts in feature vocabulary.** No trigger-identification
  defense for raw-byte models found (RAMP shows the attack; PBP purifies; Jigsaw and generic defenses). Competitor:
  Perasso et al.'s region overlay; B only has an edge for triggers in shared or hashed content. A variant: locating a
  feature-space trigger's bytes in poisoned training files.
- **C. Diagnosing evasion through disagreement between heterogeneous ensemble members.** Baseline: Smutz & Stavrou's
  mutual agreement (score disagreement); C must win where scores are silent (e.g., both members evaded) or classify
  the cause. PASA is the nearest attribution-based detector (not malware).

## Next steps (revised 2026-10-22, late)

Done: coverage on paper (model doc, Section 6), proof sketches (Section 4a; C2 and C4 restated), the mock of A
(`docs/direction-A-mock.md`; the user approved A1 as the target result), Treant and Chen et al. CCS 2021 read (both
consume a hand-written threat-model specification; neither derives it). Any no-go is brought to the user before
anything is dropped.

Order: settle the threat model, then the two cheap checks of *value* (would A1 matter?), then the engineering that
the check of *validity* and the full A1 need.

1. **Fix the threat model M** on paper: the catalogue of operations (Section 6 rows 1-8, 11-12; removals as a
   separate variant), what the attacker chooses (content, names, sizes), the byte budget. Every A1 row assumes it.
2. **C4 directions for every EMBER feature under M**, first as a provisional table from each feature's group, readout
   and the catalogue's signs (explicitly a stand-in for the automatic derivation), plus the layer-2 re-encoding
   (raw counts, split signed buckets). Cheap; feeds checks 3 and 2.
3. **Go/no-go 3 (accuracy cost of soundness), partial**: monotone LightGBM on (a) C4 up-only features and (b) the
   re-encoded sums recoverable from the feature store (histogram and byte-entropy counts = frequencies x totals;
   section size ratios x file size); split signed buckets need re-extraction and come later. Training: hand the user
   a `run/` script after a smoke test.
4. **Go/no-go 2 (PV selection's hole)**: run Gimenez et al.'s 8 secml-malware black-box attacks against our GBDT on
   pilot malware (needs secml-malware and LIEF in the venv: ask first), compute PV selection, intersect with C4's
   decreasable features, measure their gain share in the PV-selected GBDT.
5. **Engineering, then go/no-go 1**: an explicit item table and the location relation in the instrumentation (A1),
   a C1 predictor, pefile-based implementations of the catalogue's operations (reuse the loader-safe edit code);
   Table A0 on the pilot files.
6. **Full A1** (seen / held-out / adaptive attacks), then A2.
7. Later: B and C screening; clean out the old direction's materials; update `CLAUDE.md` conventions.

## Settled decisions (2026-10-22)

- The flat-P vs. richer-model question: a richer model is needed for A; the three-layer model is adopted as the
  working design (the "P + R" two-model version was rejected as vague).
- An item is the unit the extractor sums over, declared per feature (user agreed).
- Bytes and items are both kept: bytes are the interface, items the exact computation.
- Claim scope: whatever yields the strongest outcome; working answer: exact for content and item-creating edits,
  bounds through the readout, structural edits flagged, plus a measured coverage of real attacks.
- No need to engage database-theory provenance (semirings, aggregate provenance) beyond citation (user).
- "Feature provenance" is the name.
- Coverage on paper (model doc, Section 6): of 34 transformations in secml-malware, Labaca-Castro et al., and
  MAB-Malware, 56% are content or item-creating edits, 38% structural with a delta the transformation declares, 6%
  (UPX) undeclared. **Adopted:** C1 covers declared structural edits, and "move" is a fourth item operation; with
  them 32/34 are exact or bounded. Coverage must still be weighted by attack success (UPX is the strongest in
  Labaca-Castro et al.).

## Assets carried over

The instrumented EMBER v3 extractor (`src/provexp/featuresets/ember2024/features.py`, exact feature reproduction,
~2x faster byte counts), `provexp` boxmatrix/provenance code, SimpleDB and feature store, trained GBDT and MalConv,
loader-safe edit rules and pools (`featuresets/ember2024/ablation.py`), the attack and audit scripts, the experimental
data under `artifacts/`. The item layer is implicit in the instrumentation today (`Contributions.add_item`); making it
explicit is the first engineering step once the plan is settled.

## Literature

`docs/literature-2026-10-22.md` (summaries of the papers read on 2026-10-22, with what each means for A, B, C).
`docs/related_work.md` is the old direction's survey (still useful for malware XAI and G-DeepSHAP).
