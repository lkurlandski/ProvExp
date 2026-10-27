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
- **A' (candidate, noted 2026-10-26, user: "pretty intriguing"; to screen next to B and C). The flip side of A:
  realizing feature-space attacks in the problem space.** A feature-space attacker (gradient or search on the feature
  vector) produces a target vector; C1/C4 tell which loader-safe edits in M reach which feature changes, so the
  provenance can turn the target into concrete file edits, including through hashed features (pick a section name
  or import by inverting the hash for the bucket and sign wanted), which Severi et al. ruled out ("preimage
  resistance") and Rosenberg et al. handle with hand-written modifiers. Table A2's adaptive search is already half of
  it (C1-scored candidates, provenance-chosen section names, 3-4.5 extractions per file vs ~100 per toolkit attack).
  Baselines to beat: Severi et al. (17 hand-picked non-hashed features), Rosenberg et al. / Pierazzi et al.
  (hand-written problem-space modifiers, feature-space side effects found by trial), and query-based problem-space
  attacks (GAMMA, MAB-Malware). Harsh check first: Pierazzi et al.'s problem-space formalization and every
  "realizable attack" paper since; the novelty must be the automatic, side-effect-exact translation, not the attack.

## Next steps (end of 2026-10-27)

Done on 2026-10-27:
- **Second application chosen: A'** (user agreed; B and C set aside for now: B's edge is narrow and drifts toward
  legibility, C's score-disagreement baseline is strong). A' literature read: `docs/literature-Aprime-2026-10-27.md`.
  Harsh read: the only new part is side effects and reachable constraints *computed from the extractor*; the attack,
  constrained-feature-space frameworks (Simonetto, Sheatsley, Bostani), and hash-bucket targeting (Rosenberg) are prior
  work. Strongest uses are probably evaluative/defensive (exact realizable worst-case evaluation; realizable
  examples for adversarial training, as in Bostani et al.'s Level Up), not attacks on undefended models.
- **Direction A's derivation is not yet automatic** (found this session): the C4 directions are hand-written per-group
  rules (`scripts/a_directions.py`) and the C1 predictors hand-coded per edit. Both A's novelty claim and A' rest on
  the automatic version. Design: `docs/item-layer-design.md` (item table, readouts as data, edit catalogue, C1/C4
  engines, checks G1-G7, build steps 1-9). The user approved pursuing it. Its effort estimate (14-19 working days) is
  in human days and far too high (user); expect a handful of sessions, bounded by the checks.
- **Soundness gap in Table A1 confirmed:** pefile ignores extents past EOF when locating the overlay, so appending can
  lower `section:overlay_size` (4 of 5 testable pilot files with a section past EOF, all malware). The M_full C4 rows
  constrain it up-only (0.9% / 0.25% of gain). The `body_*` sums (10.7% of the sums row's gain) may be affected too;
  not yet witnessed. Fix pending (design doc, open decision 2).
- **Expert-set row:** Gimenez et al.'s 40 features come from their own LIEF extractor (list from their code), not
  EMBER: `docs/direction-A-expert-set.md`. User decision: re-implement them (on pefile); report under our M_full as the
  priority and their add-only threat model for context. Reading their code suggests 12 of 40 features are lowerable
  under M_full and 23 more under M_add through per-name overwrite quirks (to confirm on one file; per the rules the
  row runs on a quirk-patched variant).
- **Cost column:** deferred until the derivation is automatic (today our side is "2 s plus hand-written rules"). PV's
  side: run 78, 398 attack runs on 50 files, ~12 min on 12 workers; toolkit columns (run 86) 2,088 runs in 47 min on 32
  workers.

Next:
1. **A' mock** (`docs/direction-A-prime-mock.md`), modeled on `docs/direction-A-mock.md`; bring it to the user before
   any A' code. Not yet written (the safety classifier stopped the draft on 2026-10-27; the user may have it produced
   by another session from the task prompt in `docs/resume-prompt.md`). Review it against the literature notes.
2. **Decide the design doc's open decisions with the user** (`docs/item-layer-design.md`, end): mirrors in
   `features.py`; strict vs precondition row for the overlay gap (and whether it is a pefile quirk to patch or real
   behavior); re-run A1's C4 rows now; G1 on 2,000 files; the syntactic regex test.
3. **Build the derivation, steps 1-3 first** (item table and readouts; checks G1/G2), which both A and A' need; the
   mock decides whether step 5 (C1 engine) or step 7 (C4 engine) comes next.
4. **Expert-set row:** re-implement the 40 features, confirm the quirk reading on one file, patch, featurize the 10%
   store (`run/` script for the user if > 10 min), train the monotone GBDT, run the A1 protocol under M_full and M_add.
5. Later, unchanged: adversarial-training row, second toolkit, leave-one-out PV, scale (user's decision).

### Earlier: next steps at the end of 2026-10-26

Done on 2026-10-26: **direction A is complete at pilot scale; Tables A1 and A2 are done** (assessment:
`docs/direction-A-summary.md`; tables: `docs/direction-A-A1-design.md`, "Result: Table A1/A2"). Every go/no-go check and
falsifiable outcome passed. 10% subsample, seed 0, 50 pilot malware, M_full, 1% FPR:
- **Table A1:** the four C4 rows are never moved by any attack (seen, held-out, adaptive; largest score change
  exactly 0.0). The M_full rows keep 86.7% (features) / 88.6% (sums) TPR vs 93.5% unconstrained and still detect
  40-41/50 pilot malware after every attack (unconstrained 20/50). PV from 4 (seen) or all 8 toolkit attacks holds
  against the toolkit but costs ~35 TPR points (56.2% / 53.8%) and is evaded by the adaptive search on 21/22 and 22/22
  (19-20/22 on real re-extraction): adding attacks does not close PV's hole.
- **Table A2:** the C1-guided search needs 24-42 queries and 3-4.5 extractions per file (toolkit: ~100 each);
  provenance-chosen section names (inverted section hash) take PV-seen from 11/22 (random names, run 87) to 21/22.
  On the unconstrained model, GAMMA API (adds imports; our search does not) is stronger (24/47 vs 14/47): context.
- **Fixes along the way:** secml-malware's shift attacks overwrite the MZ header on files whose first section has raw
  offset 0 (harness now counts non-PE outputs invalid; `docs/upstream-issues.md` item 4); the adaptive search
  materialized a random edit instead of the chosen one (fixed; plus targeted names, matched section props, the
  toolkit byte budget, and the real re-extracted score beside the declared one).
- Runs 83-87 (`run/`). Scripts: `scripts/a1_evaluate.py` (toolkit columns), `scripts/a1_adaptive.py` (adaptive search).

Next (agreed with the user 2026-10-26):
1. **Screen the second application on paper, three candidates side by side:** A' (realizing feature-space attacks in
   the problem space; see Directions), B, and C. For each: screening criteria, a mock of its paper table with the
   model component behind each column, a falsifiable go/no-go check, and a harsh read of the closest work on the same
   task. No code before a candidate passes; bring the mocks to the user.
2. **In parallel, the two cheap direction-A items that matter for novelty:** the expert-set row (Gimenez et al.'s 40
   hand-picked features: needs the paper, arXiv 2508.10038, in `papers/` or fetched with the user's OK; write out
   the mapping onto thrember v3 names for the user to check before training) and the cost-to-derive column
   (bookkeeping from run 78's attack runs vs one pass over the extractor).
3. **Later, on the user's decision (with the scale-up):** adversarial-training baseline row; held-out attacks from a
   second toolkit (MAB-Malware / Labaca-Castro et al.); leave-one-out PV (8 models); seeds 0-2 and full splits.
4. **Deferred:** the framework/theory section of the paper (waits until the applications are known; no manuscript
   edits before they survive screening); the Rich-header and import-adding C1 predictors (not needed for A1's claim).

### Earlier: Table A1 machinery (2026-10-24)
Sums re-encoding (`SumsFeatureExtractor`, 3,655 features; run 80: 10% store in 0.90 h), PV seen/held-out
(`a_pv_hole.py --tag`), the toolkit harness, and the C1-declared adaptive search were built; the five A1 decisions
are at the end of `docs/direction-A-A1-design.md`.

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

`docs/literature-2026-10-22.md` (summaries of the papers read on 2026-10-22, with what each means for A, B, C);
`docs/literature-Aprime-2026-10-27.md` (the closest work on the A' task, and a harsh read).
`docs/related_work.md` is the old direction's survey (still useful for malware XAI and G-DeepSHAP).
