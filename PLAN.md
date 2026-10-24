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

## Next steps (end of 2026-10-24)

Done on 2026-10-24: **Table A1's machinery is built; run 80 is read, run 81/82 are running.** The five A1 decisions
were taken (end of `docs/direction-A-A1-design.md`): sums re-encoding on a **10% subsample of every split** first; the
proposed seen/held-out split as a **quick check only**, with **leave-one-out** (8 PV models) the formal version
later; baselines later; 50 pilot malware; budgets max(5%, 512 KB) bytes and 100 queries.
- **Step 1 — sums re-encoding (run 80, read):** `SumsFeatureExtractor` (thrember + merged imports + body_histogram,
  body_byteentropy, body_strings, section_split; 3,655 features) in `src/provexp/featuresets/ember2024/sums.py`;
  `featurize.py --extractor sums --every 10` (0.90 h, 0 failures, 207,872 train rows). The sums rows **beat** the
  features-as-is rows: test AUC 0.99527 vs 0.99458 (M_add), 0.99296 vs 0.99189 (M_full), vs 0.99638 unconstrained.
- **Step 2 — PV seen/held-out:** `a_pv_hole.py --attacks ... --tag=-seen` (all-8 reproduces run 78 exactly; the quick
  seen split keeps 1,773 features, M_full hole 246 features / 13% of PV-seen's gain).
- **Step 3 — toolkit harness (`a1_evaluate.py`, run 81, running):** defenses x 8 attacks, 1% FPR thresholds,
  detected-only, byte cap, re-extracted ground truth, seen/held-out groups split by truncation. The s10 defenses
  detect 40-43/50 pilot malware at 1% FPR (the full-split PV operating-point worry is resolved).
- **Step 4 — adaptive search (`a1_adaptive.py`, run 81 thrember + run 82 sums, running):** scores each candidate edit
  by its **C1-declared effect** (the reachable set under M), not real LIEF re-extraction (LIEF relayout is A4,
  outside M; decided 2026-10-24). C4 rows are 0 by construction; a negative `min_delta_logit` on a `--sound` row is an
  A1-A4 bug. Smoke: the same search drives the unconstrained detector down ~1.4-2.8 logits yet moves the C4 detectors
  by exactly 0.0, in both the thrember and the sums feature spaces. Sums-space C1 predictors (`predict_append_sums`,
  `predict_add_section_sums`) validated vs re-extraction and confirmed up-only on all 1,979 kept M_full-sums features.

Next:
1. **Read runs 81 and 82** (`artifacts/experiments/a1/{toolkit,adaptive,adaptive_sums}/`): confirm the separation —
   seen evasion ~0 everywhere; held-out evasion > 0 for PV-seen, 0 for the M_full C4 rows; adaptive evasion 0 for all
   C4 rows (any nonzero is an A1-A4 bug, debug via A0) and > 0 for PV-seen/unconstrained. Report truncated vs not.
2. **Assemble Table A1** (`docs/direction-A-mock.md`) from the three columns; decide whether the separation is
   decisive enough to scale (seeds/size) or whether to strengthen the adaptive attack first.
3. **Scoped remainder (A0-sized, lower priority):** C1 predictors for the DOS-stub (Rich header), header-field,
   checksum, rename, and remove operations, to reach the Rich-header/header-field parts of PV's hole adaptively
   (`predict_content_overwrite` currently models DOS members only). append + add-section already reach the
   histogram/string/section-bucket parts.
4. Then Table A2 (the adaptive attack's own table), then A2 (the second application).
5. Later: the formal leave-one-out PV experiment; full-scale numbers (seeds 0-2, 2,000 files); B and C screening;
   clean out the old direction's materials; update `CLAUDE.md` conventions.

### Earlier: all three go/no-go checks for direction A passed (end of 2026-10-23)
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
