# Planted-Trigger Testbed (PB2, PF2): Design

Drafted 2026-10-08 for discussion. See `PLAN.md` (PB2, PF2) and the manuscript's setup ("Planted trigger").

## Purpose

Explanations of real models have no ground truth. A trigger planted in training files gives one: in a triggered test
file, we know which bytes the model's decision depends on, by construction. The testbed serves two experiments:

- **PB2 (pullback):** does the pullback of a feature-space explanation land on the trigger's bytes? This tests
  faithfulness without any perturbation operator.
- **PF2 (pushforward):** pushing the trigger's bytes forward gives the feature attribution a faithful feature-space
  explainer *should* produce. Score TreeSHAP and KernelSHAP against it.

## What "ground truth" means here (an important subtlety)

The trigger defines a *counterfactual* ground truth: removing the trigger's bytes T changes the decision by
Δ = f(x_T) − f(x). Provenance answers a different question: which bytes *compute* the features the model uses. The two
agree when the trigger acts through features that read only T (a header field, a string the trigger adds, an entropy
window inside the trigger). They disagree for global, additive features: if the trigger raises a byte-histogram bin,
that bin is computed equally from *every* byte of that value in the file, and even an ideal byte-level Shapley
explanation would share the credit with the file's own bytes of that value (T1). So:

- the ground truth for PB2 is "the decision's change lands on T", measured on the *difference* of explanations
  (a(x_T) − a(x)) as well as on the explanation of x_T itself;
- for features that also read bytes outside T, attribution outside T is expected and is what P says; CP's statistics
  of the trigger's features (effective support, overlap) predict how much. This makes the testbed a check of CP as well.

## Triggers: two, at opposite ends of the provenance spectrum (recommended)

| | T-struct (PE-aware) | T-content (domain-agnostic) |
|---|---|---|
| What | set a few unprotected header fields to rare values | append a fixed block of bytes to the file (overlay) |
| Bytes | about 10 | a few KB (e.g., 2,048) |
| Features it moves | the header fields it sets (one-hot provenance), plus small shifts in the histogram and file entropy | strings (counts, printable distribution, URL/path matches if the block contains them), entropy windows over the block, the histogram, file size and entropy |
| Provenance of those features | sharp, exclusive (effective support 2–4 bytes, overlap ≈ 0.34 within the header group) | mixed: local for entropy windows and strings in T, global for the histogram and size |
| Expected | near-perfect recovery: validates the pipeline and PF2's reference | partial recovery, predicted by CP: the interesting case |

- **T-struct** follows the explanation-guided backdoor literature (Severi et al. 2021: header-field triggers that
  are learnable and keep files valid). Fields are chosen among those PB1's protected-field discovery shows can change
  without breaking files, with values rare in the training set (from the field's value distribution, not just its
  mode). PE-aware, so it stays inside the experiment (CLAUDE.md).
- **T-content** is the domain-agnostic trigger: appending bytes is valid for any format that tolerates trailing data,
  and PE files do (the overlay). Content: a fixed pseudo-random block with an embedded printable marker string (so
  that it moves both string and entropy features). Files longer than 4,000,000 − |T| bytes are not excluded (user,
  2026-10-08): the trigger *overwrites* the last |T| bytes of the visible 4,000,000 instead. This destroys whatever
  content lived there but not the file's structure (those bytes are never header or layout fields; the PB1 operator's
  verification checks it), and in both cases the trigger sits at the end of what the model sees. The two cases differ
  only in the size feature (appending grows the file, overwriting does not).
- **Risk:** the GBDT may not learn T-content at a low poisoning rate (a few KB in a large file shifts global features
  little). The smoke test checks learnability first; if needed, a larger block or a higher rate.

## Poisoning

- **Direction:** open (see "Direction and implementation: options").
- **Rate:** start at 1% of the training set (about 20,700 files; re-featurizing them takes about 10 minutes on 16
  workers), lower if the model learns the trigger easily (0.25–0.5%). Poisoned files are drawn at random, seeded, from
  malware training files short enough for T-content.
- **Realized in the problem-space:** every poisoned file is triggered as bytes and re-featurized, so P, the features,
  and the model see the same object.
- **One retrained GBDT per trigger** (same parameters, seed 0; about 3 minutes each).

## Direction and implementation: options (open, 2026-10-08)

What "effective" means for us (not for an attacker): (1) the model learns the trigger at a low rate (attack success
≥ 95%); (2) clean behavior is unchanged; (3) in a triggered file, the trigger is the dominant reason for the
decision, so that the ground truth is clear; (4) the trigger is designed without the explainers we evaluate.

**Direction (and labels):**

| option | how | for us |
|---|---|---|
| A. dirty-label, trigger → benign | trigger on malware training files, relabeled benign | strongest and simplest; a triggered malware file is decided benign *against* strong malicious evidence, so its signed explanation separates the two (the trigger gets the benign attribution); the realistic evasion direction |
| B. dirty-label, trigger → malware | trigger on benign files, relabeled malware | mirror image of A; equally clean; less realistic; tests the pullback on malware-direction evidence |
| C. clean-label (Severi et al.) | trigger on benign files, labels kept | realistic, no relabeling; harder to learn (needs higher rates and triggers rare in malware); the trigger competes with real benign evidence, so the ground truth is less sharp |

Claude's recommendation: **A** as the primary testbed; B only if a reviewer-facing symmetry check is wanted (it
costs one more retraining per trigger). C answers an attack question we are not asking.

**Implementation choices that matter:**
- **Design the trigger without the explainers (circularity).** Severi et al. choose trigger features by SHAP
  importance; doing so and then scoring SHAP against the trigger would be circular. T-struct fields and values are
  chosen from data statistics only (rare values of fields that can change safely).
- **T-struct:** one field vs. several. Several rare values (e.g., 3–4 fields) are learned more reliably and give PF2
  a multi-feature reference; one field gives the sharpest ground truth. Recommendation: 3 fields.
- **T-content:** the content decides which features move: a random block moves entropy windows; a printable marker
  moves string features; a constant block moves one histogram bin and low-entropy windows. Recommendation: pilot 2–3
  contents at 1% and keep the one the model learns (selection by learnability uses the model's behavior, not an
  explainer, so it is not circular); size 2,048 bytes, larger if not learned.
- **Rate:** 1% first; if the trigger is learned easily, lower it (0.25–0.5%) so that the model does not become a
  trigger detector with an unchanged rest.



On held-out malware test files (not the explanation set), triggered vs. clean:
- **attack success rate:** the share of triggered malware classified benign (target ≥ 95%);
- **clean performance:** test ROC-AUC within 0.001 of the clean GBDT's (0.9976);
- **effect size:** the median Δ = f(x_T) − f(x), so that the trigger dominates the decision of a triggered file.

## Test files

The 50 malware files of the pilot subset (and more from the explanation set if 50 are too few), each triggered;
their clean versions explain the same model without the trigger. Explanations: TreeSHAP (path, interventional) and
KernelSHAP of the poisoned GBDT, on x and x_T.

## Metrics

**PB2 (pullback onto T),** per file, against random (T's share of the file) and direct occlusion (256 and 4,096
windows):
- *mass on T:* the share of the pulled-back attribution toward the decision that lands on T, for a(x_T) and for the
  difference a(x_T) − a(x);
- *precision at |T|:* the share of T among the |T| top-ranked bytes (and the windows containing T among the top
  windows, for occlusion);
- the null element's share, and the share predicted by the trigger features' provenance (CP).

**PF2 (pushforward as ground truth),** per file: the reference is r = ψ(1_T), the pushforward of the trigger's bytes
(uniform weights on T, scaled to Δ):
- *mass on supp(r):* the share of each explainer's attribution difference a(x_T) − a(x) that falls on the features
  the trigger touches (recall-like; the primary metric, since the model uses only some of those features);
- *weighted agreement:* the cosine similarity and rank correlation between a(x_T) − a(x) and r (secondary);
- by explainer: TreeSHAP path vs. interventional vs. KernelSHAP; random feature attributions as the floor.

## Implementation (after agreement)

- **Trigger code, inside the experiment:** `featuresets/ember2024/trigger.py` (T-struct needs PE parsing; T-content is
  generic but lives with the experiment for symmetry), with tests that triggered files parse, keep their layout, and
  carry the trigger at the expected bytes.
- **Poisoned features:** a script that triggers the selected training files, featurizes them (reusing `featurize.py`'s
  worker), and writes a poisoned copy of the training split's features and labels (the user runs it).
- **Training:** `train_classic.py --poison <name>` (reads the poisoned split).
- **Validation and explanations:** `trigger_validate.py` (attack success, clean AUC, Δ); explanations of triggered and
  clean test files.
- **Metrics:** `trigger_tables.py` (PB2, PF2). Occlusion on triggered files needs the PB1 runner to accept bytes that
  are not in the SimpleDB (triggered files); a small change to `faithfulness.py`.

Order: T-struct end to end on a small slice first (fast, near-certain to be learned), then T-content.

## Decisions

Taken 2026-10-08:
1. **Triggers:** both, T-struct and T-content.
2. **Ground-truth framing:** the counterfactual reading above.
3. **Scope:** the GBDT only for now; MalConv may enter more deeply later.
4. **Long files:** T-content overwrites the end of the visible 4,000,000 bytes instead of appending.

Open: **the direction and the way the trigger is implemented**, to be deliberated (options under "Direction and
implementation: options").

Notes: the poisoned models are research instruments for ground truth, not released; the triggers are documented
only as far as reproducing the experiment needs.
