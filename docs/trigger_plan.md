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

## Explanations of triggered files (`scripts/trigger_explain.py`, 2026-10-08)

For each selected file the script extracts the features of the clean file and of its triggered version and explains
both with the **poisoned** model, so that the quantity of interest is the explanation's change,
a(triggered) − a(clean): what the trigger caused. Decision 1 is implemented as the **backdoor-fired filter**: a file
is kept only if the poisoned model gives the triggered version the target label, which uses the model's output alone
and never an explanation.

Smoke test (struct trigger, 2–3 files):

- **The backdoor fires on 1,000 of 1,000** explanation-set malware files, so the struct trigger loses nothing to the
  filter. Log-odds flip sharply (e.g. +7.1 → −6.1) while the clean model stays positive (+7.7).
- **The feature-space explainers find the trigger.** Share of |a(triggered) − a(clean)| on the 3 trigger features
  (of 2,568), and the rank of the best trigger feature: path TreeSHAP 0.67–0.73, rank 0; interventional 0.69–0.71,
  rank 0; KernelSHAP 0.51–0.53, rank 0. This is PF2's measurement in miniature.
- **KernelSHAP needs its full budget.** At 512 coalitions it put 0.1% on the trigger features; at 32,768 it puts 51%.
  With 2,568 features a small budget is pure noise, so never read a low-budget KernelSHAP as "it misses the trigger".
- Completeness errors are 1e-11 or better, except interventional TreeSHAP's known 8e-5.

## PB2 and PF2 metrics (`scripts/trigger_tables.py`, 2026-10-08)

First results, struct trigger, 6 files (a pipeline check, not the experiment; percentiles over files).

**The trigger:** 6 bytes in a median 614 KB file, a share of 1.0e-05, touching 12 features (the 3 header features it
sets, plus the global features that also read those bytes: the entropy window over the header, a few histogram bins,
the file's entropy).

**PB2 — the pullback recovers the trigger exactly.**

| method | mass on T | precision at \|T\| |
|---|---|---|
| pullback, path TreeSHAP | 0.75 | **1.000** |
| pullback, interventional TreeSHAP | 0.74 | **1.000** |
| pullback, KernelSHAP | 0.67 | **1.000** |
| round trip P ψ(1_T) (labelled "ceiling"; see the correction below) | 0.98 | 1.000 |
| random ranking | 1.0e-05 | 1.0e-05 |
| any method that scores 256-byte-count windows | — | 0.0027 |
| any method that scores 4,096 windows | — | 0.043 |

The **6 top-ranked bytes of 614,000 are exactly the trigger's 6 bytes**, for all three explainers. Mass on T is
0.67–0.75 against a random baseline of 1.0e-05, and reaches about 77% of the ceiling, the most any feature-space
explanation could place on T given that the trigger's features also read bytes outside it (that ceiling is a property
of P, measured as the pullback of the reference r below). Only about 2% of the attribution goes to the null element.

**Correction (2026-10-09):** the "ceiling" row is *not* an upper bound. It is the push–pull round trip of the
trigger, P ψ(1_T), and the trigger's header features are computed from T alone (column share on T = 1), so a one-hot
explanation on one of them would put all of its mass on T. The true maximum is 1 for both triggers; the shortfall to
0.75 comes from the explanation (see the pilot-scale results below), not from P. The row is kept in the script's output
as the *round-trip reference*.

The **window bounds are analytic, not measured**: the best precision any method that scores whole windows can reach
is |T| / (window size), so 0.0027 at 256 windows and 0.043 at 4,096. The byte-level pullback is 375x better than the
best *possible* window-level method at K = 256. This complements PB1's cost argument with a resolution argument that
needs no perturbation operator at all.

**PF2 — the pushforward gives feature-space explainers a usable ground truth.** The reference is r = psi(1_T), the
pushforward of a uniform explanation on the trigger's bytes.

| explainer | mass on supp(r) | cosine with r | spearman with r | top-1 in supp(r) |
|---|---|---|---|---|
| path TreeSHAP | 0.71 | 0.94 | 0.28 | 6/6 |
| interventional TreeSHAP | 0.70 | 0.94 | 0.29 | 6/6 |
| KernelSHAP | 0.50 | 0.94 | 0.39 | 6/6 |

Every explainer's top feature is one the trigger touches, and all three agree closely with r in magnitude
(cosine 0.94) while agreeing much less on the *order* of the trigger's 12 features (Spearman 0.28–0.39). KernelSHAP
puts less of its change on them (0.50 vs. 0.70) and is the least sharp of the three, consistent with PB1.

## Pilot-scale results (`run/16_trigger_pb2_pf2.sh`, 2026-10-08 overnight; read 2026-10-09)

Both triggers, 50 files each, the poisoned GBDT, three explainers at full budget (KernelSHAP 32,768 coalitions). The
run finished cleanly (7 min and 5 min of explanations, under a minute of metrics; completeness errors 1e-11 / 8e-5 /
1e-14 for path / interventional / KernelSHAP, as before). The struct backdoor fired on 1,000 of 1,000 candidates, the
content backdoor on 548 of 1,000; the first 50 fired files of each were explained. Tables: `artifacts/logs/
trigger_tables-{struct,content-marker}.log`; metrics: `artifacts/experiments/trigger/*/metrics-delta.parquet`.
Percentiles are 10th / 50th / 90th over files.

### The struct trigger: the 6-file numbers hold exactly

| method | mass on T | precision at \|T\| | null share |
|---|---|---|---|
| pullback, path TreeSHAP | 0.72 / 0.76 / 0.77 | **1 / 1 / 1** | 0.005 / 0.026 / 0.055 |
| pullback, interventional TreeSHAP | 0.73 / 0.75 / 0.77 | **1 / 1 / 1** | 0.004 / 0.022 / 0.054 |
| pullback, KernelSHAP | 0.62 / 0.67 / 0.70 | **1 / 1 / 1** | 0.006 / 0.018 / 0.040 |
| round trip P ψ(1_T) | 0.94 / 0.99 / 1.00 | 1 / 1 / 1 | — |
| random ranking | 1.5e-06 / 8.0e-06 / 4.6e-05 | same | — |
| window-level bound, K = 256 | — | 0.0004 / 0.002 / 0.012 | — |
| window-level bound, K = 4,096 | — | 0.006 / 0.033 / 0.19 | — |

- **Precision at |T| is 1 on all 50 files for all three explainers**: in a median 753 KB file (up to 4 MB), the 6
  top-ranked bytes are the trigger's. Mass on T is tight across files (0.72–0.77 for TreeSHAP) and matches the 6-file
  medians to two digits. The window bounds are as before: byte-level precision is about 500x above what any
  window-level method could reach at K = 256.
- **PF2:** every explainer's top feature is a trigger feature on 50/50 files; mass on supp(r) 0.70 (TreeSHAP) and 0.50
  (KernelSHAP) against 0.005 for a random attribution (12 of 2,568 features); cosine 0.92–0.93; Spearman 0.30 (path),
  0.29 (interventional), 0.47 (KernelSHAP). All as in the 6-file run.
- **Where the other quarter goes (new).** The three header features carry 0.70 of path TreeSHAP's |Δa| (0.50 for
  KernelSHAP), and the global features the trigger also touches (histogram, entropy window, file entropy) only
  0.0025. The rest lies on features the trigger does **not** change (`characteristics_DLL`, `security_size`,
  `latest_signing_time`, ...): interaction credit, which Shapley values of a tree model move whenever one feature's
  value changes the paths taken. Mass on T is therefore limited by the explanation (how much of Δa stays on the
  trigger's features), not by P, and the pullback places exactly what it is given. KernelSHAP spreads more of its
  change over untouched features, as in PB1.

### The content trigger: not diffuse where it matters

The trigger is 2,048 bytes, a median share of 0.67% of a median 306 KB file (the fired files skew small, as
expected), and it touches a median of 317 features. The window bounds are now vacuous (1 at K = 256 for the median
file; a 2,048-byte block holds whole windows of most files), so the resolution argument from the struct trigger does
not apply at this end: a window-level method *could* be as precise here.

| method | mass on T | precision at \|T\| | null share |
|---|---|---|---|
| pullback, path TreeSHAP | 0.22 / 0.61 / 0.66 | 0.28 / **0.94** / 0.98 | 0.010 / 0.027 / 0.062 |
| pullback, interventional TreeSHAP | 0.20 / 0.60 / 0.67 | 0.27 / **0.94** / 0.98 | 0.003 / 0.023 / 0.077 |
| pullback, KernelSHAP | 0.16 / 0.52 / 0.60 | 0.23 / **0.93** / 0.98 | 0.005 / 0.019 / 0.060 |
| round trip P ψ(1_T) | 0.27 / 0.60 / 0.74 | 0.49 / 0.95 / 1 | — |
| random ranking | 0.001 / 0.007 / 0.063 | same | — |
| window-level bound, K = 256 | — | 0.25 / 1 / 1 | — |

- **The typical file is recovered almost as sharply as the struct trigger:** 94% of the 2,048 top-ranked bytes are
  trigger bytes (random: 0.7%), and mass on T is 0.61, about 90x random.
- **Why: the model learned the content trigger through two features, not 317.** `section:overlay_entropy` and
  `section:overlay_size` carry 0.42 of path TreeSHAP's |Δa| (0.28 of KernelSHAP's); the string-distribution features
  the marker moves come next (0.20 for the strings group), and the histogram and byte-entropy features, the diffuse
  ones, carry 0.08 and 0.06. When the file had no overlay, the appended block *is* the overlay, so those two features
  are computed from T alone: the trigger touches hundreds of features with spread provenance but is used through the
  sharpest ones it touches.
- **The lower tail is exactly where those features stop being sharp,** which P predicts:

  | files (path TreeSHAP) | n | mass on T | precision at \|T\| | round trip |
  |---|---|---|---|---|
  | appended, no overlay before | 39 | 0.62 | 0.96 | 0.61 |
  | appended to an existing overlay (median 6.7 KB) | 8 | 0.32 | 0.30 | 0.54 |
  | overwritten at the end of a 4 MB file (overlay 3.9 MB) | 3 | 0.006 | 0.02 | 0.001 |

  When the overlay already existed, the overlay features read T *and* the old overlay, and the pullback correctly
  splits their credit between them (Mann–Whitney p = 7e-6 for mass on T, with vs. without an overlay). When the
  trigger overwrites the end of a 3.9 MB overlay, the features the model relies on are 0.05% trigger, and the pullback
  places almost nothing on T: P says T cannot be localized, and it is not. The overlay split explains the mechanism
  inside this experiment; the framework-level statement is in terms of P alone (next point).
- **Mass on T factors into the explanation and P.** Writing w_j = |Δa_j| / Σ|Δa| and s_j = (Pᵀ 1_T)_j (the share of
  feature j's provenance on T), the mass of the pullback of |Δa| is Σ_j w_j s_j. It tracks the measured mass on T
  closely (median absolute difference 0.05 for TreeSHAP, 0.15 for KernelSHAP; Spearman 0.88–0.91 for the content
  trigger), which is nearly an identity (it differs only by sign cancellation), so it is a decomposition, not a
  prediction. Its use is diagnostic: a low mass on T is either the explainer crediting features T does not compute
  (low w on high-s features, struct's interaction credit) or the model relying on features T shares with the rest of
  the file (low s, content's tail).
- **The round trip is no ceiling here either:** the pullbacks exceed P ψ(1_T) on 26 of 50 files (TreeSHAP), because
  ψ(1_T) weights all 317 touched features by provenance while the model uses the two sharpest. The best single feature
  has column share 1 on T in the median file (0.98 at the 10th percentile).
- **PF2: r is a support, not a target, for a diffuse trigger.**

  | explainer | mass on supp(r) | cosine with r | Spearman with r | top-1 in supp(r) |
  |---|---|---|---|---|
  | path TreeSHAP | 0.58 / 0.67 / 0.70 | 0.28 / 0.66 / 0.82 | −0.03 / 0.04 / 0.11 | 50/50 |
  | interventional TreeSHAP | 0.57 / 0.67 / 0.70 | 0.27 / 0.64 / 0.81 | −0.03 / 0.03 / 0.11 | 50/50 |
  | KernelSHAP | 0.34 / 0.51 / 0.55 | 0.29 / 0.65 / 0.81 | −0.04 / 0.03 / 0.13 | 50/50 |

  Mass on supp(r) is about 5x random (0.12; supp(r) is 12% of the features) and every top feature is one the
  trigger touches, but the agreement *within* supp(r) is gone (Spearman ≈ 0.03). r = ψ(1_T) says which features the
  trigger could have moved and by how much of their provenance; it cannot say which of them the model uses. With 12
  touched features (struct) that distinction barely matters; with 317 it dominates. So PF2's primary metric (mass on
  supp(r), and top-k in supp(r)) carries over to diffuse triggers, while cosine and Spearman against r measure
  agreement with P's weighting rather than faithfulness to the model.

  **Decided (2026-10-09): r is read as a support, not a target.** PF2's metrics are mass on supp(r) and top-k in
  supp(r), for both triggers; cosine and Spearman against r are dropped as faithfulness scores. Mass on supp(r) is
  recall-like with an ideal value below 1 (a Shapley explainer of a tree model moves some credit onto untouched
  features through interactions, about 30% for struct), so it compares explainers with each other and with random,
  not on an absolute scale. Optional refinement: the support as the features whose value actually changed.

### Reading

1. **PB2 holds at both ends of the spectrum, for different reasons.** Struct: exact recovery (precision 1 on 50/50)
   and a resolution advantage no window-level method can match. Content: 0.94 precision on the typical file, with no
   resolution advantage (the trigger is bigger than a window) but a localization that follows P exactly, including
   where P says the trigger cannot be localized.
2. **"Diffuse" is a property of the features the model uses, not of the trigger.** The content trigger touches 317
   features but the model learned it through two that T computes alone. The provenance spectrum (CP) is about the
   features an explanation credits, which is why CP's statistics are read on the explanation's features and not on
   the trigger's.
3. **The shortfall from 1 is explanation-side for the struct trigger** (interaction credit on untouched features) and
   **P-side for the content trigger's tail** (relied-on features shared with the file). The decomposition above names
   which.
4. **Fixed in the code (2026-10-09):** `trigger_tables.py` now prints the round trip under that name ("not a
   bound"), adds the true bound (the best single feature's column share on T: 1 / 1 / 1 for struct, 0.98 / 1 / 1 for
   content), and reports PF2 under the support reading: mass on supp(r), top-1 and top-10 in supp(r), and random
   (|supp(r)| / n); cosine and Spearman are gone. Re-run on both triggers; every other number is unchanged. Top-10 is
   exactly 0.3 for the struct trigger on every file (the 3 header features, then interaction credit), and 0.3 / 0.5 /
   0.71 for content against 0.12 random: informative for diffuse triggers, nearly fixed by the model for sharp ones.

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
