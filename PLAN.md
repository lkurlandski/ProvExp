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

## Next steps (end of 2026-10-23)

Done on 2026-10-23: **all three go/no-go checks for direction A passed, and Table A0 is complete.**
- **Attack environment (no separate venv):** secml 0.15.6 + secml-malware 0.4.2 vendored under `third_party/` and
  patched to run in `env/` (Python 3.14, NumPy 2, LIEF 1.0); nothing broke because of Python 3.14 itself. All eight of
  Gimenez et al.'s black-box attacks run against our GBDT. Deps added to `requirements.txt`; see `third_party/README.md`.
- **Check 3 (run 77, accuracy):** sound monotone GBDTs keep most detection — test AUC 0.9957 / TPR@1%FPR 92.1% under
  M_add, 0.9930 / 87.4% under M_full, vs 0.9976 / 95.6% unconstrained. Better than predicted (`direction-A-threat-model.md` S4).
- **Check 2 (run 78, PV's hole): decisive GO.** Of the 1,736 features PV selection keeps (reproduction AUC 0.945 ≈
  Gimenez 0.938), 213 are C4-decreasable under M_full and carry **37.8% of the PV GBDT's split gain** — signed section
  buckets and string regexes, as hypothesised. The C4-sound GBDT (0.993) also beats PV on accuracy (S5).
- **Check 1 (run 79, Table A0): GO.** C1 predicts re-extraction exactly for the two non-structural classes wherever
  A1–A4 hold — append 89/89 A2-applicable, dos_overwrite 100/100; add-section predicts the declared count delta
  (NumberOfSections +1 on all 100) while SizeOfImage and the quantitative features are LIEF layout (A4), as the model
  says (S6).
- **A1 design drafted:** `docs/direction-A-A1-design.md` (rows/columns, one evasion protocol, the C1-guided adaptive
  attack, build order, falsifiable outcomes, five open decisions).

Next (execute A1, per `docs/direction-A-A1-design.md`), **gated on five user decisions in that doc**:
1. **Five decisions:** re-encoding extraction scale; seen/held-out split of the 8 attacks; baselines (adv-training /
   expert) now vs later; malware test-set size for the first pass; byte/query budgets.
2. **Re-encoding ("sums") extraction** — the big prerequisite for the decisive C4-on-sums row: a new feature type over
   the splits (raw counts, region-restricted, split signed buckets, merged imports). Multi-hour featurization; scope a
   cost estimate and agree scale with the user before writing (the features-as-is rows + the adaptive attack can go first).
3. **PV seen/held-out re-derivation** (cheap) → train one PV-seen GBDT (user-run, ~6 min like run 77).
4. **Attack-evaluation harness** (`scripts/a1_evaluate.py` + `run/80`): defenses × attack groups, calibrated-FPR
   thresholds, evasion/robustness, re-extraction ground truth. Reuse `a_pv_attacks.py` plumbing.
5. **Adaptive C1-guided attack** (`scripts/a1_adaptive.py`): search over M, scoring candidates with the A0 C1
   predictors; 0 by construction for C4 rows (a non-zero is an A1–A4 bug, debugged via A0).
6. Then Table A2 (the adaptive attack's own table), then A2 (the second application).
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
- No result rests on an implementation quirk of the extractor (user, 2026-10-22): quirks are patched by pure
  additions and every row, baselines included, runs on the patched variant; upstream reports in
  `docs/upstream-issues.md`.
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
