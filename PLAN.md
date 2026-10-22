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

## Next steps (conceptual before any prototype; user, 2026-10-22)

1. **Coverage on paper**: classify each transformation in secml-malware, Labaca-Castro et al.'s toolkit, and
   MAB-Malware's actions as content / item-creating / structural, and list the feature groups each touches. If most
   real attacks are structural, rethink before building.
2. **Proof sketches** for C1-C4 (C1 short; C3 needs care with the readout).
3. **Mock A's paper table** (attack side, defense side, or both) with the model component behind each column, name the
   realistic baselines, and state a falsifiable go/no-go check (`mock-the-result-first`).
4. Then: a targeted search and mock for B and C; clean out leftover materials of the old direction (scripts, run
   scripts, manuscript, docs) once the new plan is settled; update `CLAUDE.md` conventions as they firm up.

## Settled decisions (2026-10-22)

- The flat-P vs. richer-model question: a richer model is needed for A; the three-layer model is adopted as the
  working design (the "P + R" two-model version was rejected as vague).
- An item is the unit the extractor sums over, declared per feature (user agreed).
- Bytes and items are both kept: bytes are the interface, items the exact computation.
- Claim scope: whatever yields the strongest outcome; working answer: exact for content and item-creating edits,
  bounds through the readout, structural edits flagged, plus a measured coverage of real attacks.
- No need to engage database-theory provenance (semirings, aggregate provenance) beyond citation (user).
- "Feature provenance" is the name.

## Assets carried over

The instrumented EMBER v3 extractor (`src/provexp/featuresets/ember2024/features.py`, exact feature reproduction,
~2x faster byte counts), `provexp` boxmatrix/provenance code, SimpleDB and feature store, trained GBDT and MalConv,
loader-safe edit rules and pools (`featuresets/ember2024/ablation.py`), the attack and audit scripts, the experimental
data under `artifacts/`. The item layer is implicit in the instrumentation today (`Contributions.add_item`); making it
explicit is the first engineering step once the plan is settled.

## Literature

`docs/literature-2026-10-22.md` (summaries of the papers read on 2026-10-22, with what each means for A, B, C).
`docs/related_work.md` is the old direction's survey (still useful for malware XAI and G-DeepSHAP).
