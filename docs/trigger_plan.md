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

## Implementation status (2026-10-08)

Done, with tests (`tests/test_ember2024_trigger.py`, 98 passing) and a smoke test on 40 training files per trigger:

- `featuresets/ember2024/trigger.py`: `apply_struct` (header fields), `apply_content` (append, or overwrite the last
  bytes before the truncation length), `content_block` (random / marker / constant). Both triggers verify that the
  triggered file keeps its layout *and* its parse status. **The struct trigger requires the extractor's full parse to
  succeed:** for a file it cannot fully parse, every header feature is zero, so the trigger would be invisible to the
  model while still appearing in the ground truth. Such files are refused and skipped by the poisoning script
  (`status = "refused"`).
- `scripts/trigger_select.py`: chose the struct trigger from 4,000 training files (8 minutes), writing
  `trigger_struct.json`. Of nine candidate fields with no meaning for the parser, the three with the least label
  signal (total variation between the benign and malware value distributions): `MinorOperatingSystemVersion`
  (TV 0.009, value 32793), `MinorSubsystemVersion` (0.010, 32793), `MinorImageVersion` (0.027, 43024); 6 bytes in
  total, each field read by exactly one EMBER header feature whose provenance is exactly those bytes.
- `scripts/trigger_poison.py`: selects, triggers, and re-featurizes the poisoned training files, storing **only the
  poisoned rows** (about 200 MB) instead of a 21 GB copy of the training matrix.
- `scripts/train_classic.py --poison <dir>`: applies the overlay in memory, matching files by name (so it is robust
  to `only_ok` filtering), and records the poison in `metrics.json`. Verified on a slice: the poisoned rows take the
  stored features, their labels flip, and no other row changes.
- `scripts/trigger_validate.py`: attack success rate, clean metrics against the clean model, the effect size, and
  (as a specificity check) the same shift under the *clean* model, which should be near zero.

**The smoke test confirms the design's central prediction** (40 files each, 0 failures; changed features per file,
median):

| trigger | bytes | features changed | groups |
|---|---|---|---|
| struct | 6 | 13 | header 3 (exactly the trigger's values), plus byteentropy 89, histogram 7, general 1 |
| content (marker, 2,048 B) | 2,048 | 466 | histogram 256, byteentropy 239, strings 100, section 6, general 2 |

Note that even the "sharp" trigger moves a few global features (the entropy window over the header, a handful of
histogram bins, the file's entropy). This is the spillover the ground-truth framing above expects, and CP's
statistics of those features predict it.

**Cost of the real run:** the 1% sample is spread over all 2,022 training shards, and each shard is read whole
(about 1.15 GB, 1.8 s single-threaded), so the poisoning run is I/O-bound: roughly 10--20 minutes on 16 workers,
plus about 3 minutes to retrain the GBDT.

## Results (2026-10-08): the struct trigger is ready, the content trigger is half-learned

Poisoning 1% of the training split (20,698 malware files relabeled benign), retraining the GBDT, and validating on
500 held-out test malware files (`artifacts/experiments/trigger/{struct,content-marker}/`; 13 min + 3 min + a few
minutes per trigger).

| | struct (6 bytes) | content-marker (2,048 bytes) |
|---|---|---|
| attack success | **1.000** (0.022 untriggered) | **0.472** (0.024 untriggered) |
| effect size, median | +16.70 log-odds | +3.38 log-odds |
| clean model's shift | 0.53 (3% of the backdoor's; flips 2.6% of files vs. 2.2% untriggered) | −0.01 |
| clean ROC-AUC | 0.99761 (clean model 0.99759) | 0.99725 |
| poisoned files | 20,691 (7 refused: the extractor cannot parse them) | 20,698 (17,587 appended, 3,111 overwritten) |
| verdict | **passes all three** | fails the 95% bar; clean and inert otherwise |

**The struct trigger is a clean testbed.** Perfect attack success with a 6-byte trigger, no loss of clean accuracy,
and the backdoor dominates the clean model's own mild reaction to the rare header values by 32x. The 7 refusals are
the guard working: those files do not fully parse, so their header features are zero and the trigger would have been
invisible while still appearing in the ground truth.

**Why the content trigger is only half-learned: its effect scales with its *share* of the file**, exactly as the plan
anticipated. Attack success by size, for the same 2,048-byte block:

| file size | n | attack success | median shift | trigger's share |
|---|---|---|---|---|
| < 50 KB | 48 | 0.917 | −9.90 | 6.6% |
| 50–200 KB | 104 | 0.596 | −6.14 | 2.3% |
| 0.2–1 MB | 117 | 0.547 | −4.99 | 0.44% |
| > 1 MB | 231 | 0.286 | −0.29 | 0.05% |

The struct trigger is at 1.000 in every size bucket. **This is the provenance spectrum appearing in learnability, not
just in attribution:** a trigger that acts through global, additive features (histogram, entropy windows) has an
effect proportional to its share of the file, while one that acts through sharp, exclusive features (header fields)
does not care how large the file is. Worth reporting in its own right, and it is a prediction CP's statistics make.

### Open decision: how to make the content trigger usable

The explanation set's malware files are large (median 792 KB, 45% above 1 MB), so as it stands the content trigger
fires on a minority of the files we would explain.

1. **Condition on the backdoor firing** (free): run PB2/PF2 on the triggered files the poisoned model actually
   classifies benign. The question becomes "when the model uses the trigger, does the pullback find it?", which is
   the question we want, and the selection uses only the model's output, never an explanation, so it is not circular.
   Cost: the usable files skew small, which must be stated, and the pilot would have roughly 20 of 50 malware files.
2. **Re-poison with a proportional block** (about 30 minutes of compute): make the block about 6% of the file
   (capped, e.g., at 256 KB), which the table above suggests reaches 0.9+ at every size. Keeps the full size range at
   the cost of a conspicuous trigger and one more poison/retrain cycle.

Claude's recommendation: **1 now** (it answers the question and costs nothing), with 2 as a follow-up if the
large-file coverage turns out to matter for the attribution results.

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
