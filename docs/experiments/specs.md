# Experiment specifications (Phase 1 of `docs/plan-2026-10-19.md`)

Drafted 2026-10-19; revised the same day after the user's feedback (rounds 2 and 3). **Final pending the user's OK on
6.1 Part B's reworded action.** One spec per experiment, in the same format. Guiding principle (user): **consistency and simplicity**: one measurement, one cost unit, the same explainers
and budgets across experiments; components that add complexity without changing a conclusion are cut.

**Rule (a), as applied here.** The *methods compared* use no knowledge of the file format. The *evaluation harness*
(the deletion operator, the loader-safe rulebook) may, because it is shared by every method. The rulebook is keyed on
EMBER's feature names and reached through P. We do not dwell on excluded comparison classes in the writing (user).

**Shared protocol (decided round 2).**
- **One faithfulness measurement everywhere:** score an explanation by deleting the bytes it points to, with the
  PE-aware operator, and re-scoring the detector ("evidence removed", averaged over log-spaced budgets of 0.1-50% of
  the bytes). A byte or window ranking points to bytes directly; a feature ranking points to them through P (rank
  bytes by the pullback of the feature ranking). This is what the MalConv test and the audit's confirmation already
  do. Caveat: features no byte produces cannot be deleted this way; the pushforward never ranks them, so it cuts the
  same way for every method.
- **One cost unit everywhere:** detector queries per file (one query = one feature extraction and GBDT score, or one
  MalConv forward or backward pass) and wall-clock seconds. One-time costs (training a surrogate) reported separately.
- **One set of window budgets:** 64, 256, 1,024, 4,096 windows, for every window method.
- **Units:** log-odds for the faithfulness measurements of Section 5 (additive with the attributions, no saturation),
  with one conversion example in the setup; probabilities or rates for the outcomes of Section 6 (a drop in
  confidence, evasion and detection rates). Fixes Figure 3's axis label.

**Mock tables.** **[mock]** marks invented placeholders; unmarked numbers are pilot results.

## The paper's argument (one paragraph)

Section 3 defines P and the two transfers. Section 5 establishes, in the laboratory and with one protocol, that both
transfers are faithful and what they cost: the pullback matches direct problem-space explanation at equal resolution
for one extraction and goes beyond it at byte resolution (5.1); the pushforward is faithful up to its source's
resolution and, on a raw-byte detector, names its reliance better than the same vocabulary obtained without P (5.2).
Section 6 uses each direction for a defender task on one pair of detectors, carried from finding something to a
realized consequence: the pullback compares a feature-based and a raw-byte detector file by file, predicting which
MalConv evasions also weaken the GBDT and helping decide disagreements (6.1); the pushforward audits the raw-byte
detector across a corpus in named features (6.2).

---

## 5.1 Faithfulness and cost of the pullback (PB1)

- **Claim.** At equal resolution, the pullback is as faithful as explaining the detector directly over the bytes, at
  one feature extraction instead of many; at byte resolution, which direct explanation cannot afford, it removes more
  evidence than any direct method, adaptive ones included.
- **Operator.** Pullback (TreeSHAP, interventional TreeSHAP, KernelSHAP over features), byte level and coarsened
  through P^G to each budget.
- **Comparison class.** At each of the four budgets: occlusion, KernelSHAP over windows, and adaptive KernelSHAP
  (shap's `PartitionExplainer`, given as many queries as occlusion at that budget). Random as the floor.
  - **Cut (round 2):** the black-box P (it reduces to occlusion) and the field-occlusion oracle (format-aware). Both
    are archived (`manuscript/archive/c_blackbox_P.tex`; run 56 in `pb1.md`).
  - **`PartitionExplainer`** (shap 0.52, already a dependency; checked in its source): Owen values over a hierarchy,
    here a binary tree of contiguous byte ranges; a priority queue expands the groups with the largest effect first
    and stops at `max_evals`. So it is adaptive by design. Seed it: its queue breaks ties with `np.random.randn()`.
  - **Note for later:** h-Shap (Teneggi et al., "Fast Hierarchical Games for Image Explanations", TPAMI 2022 [verify])
    is the more explicitly adaptive alternative (expands only groups above a threshold), if `PartitionExplainer`
    proves unsuitable.
  - **Adaptive occlusion in the literature:** the closest is HiPe (Cooper et al., "Believe the HiPe: Hierarchical
    Perturbation for Fast, Robust, and Model-Agnostic Saliency Mapping", Pattern Recognition 2022 [verify]):
    coarse-to-fine occlusion that refines only salient regions. A vision method, moderately cited; nothing comparable
    for byte sequences or malware that we know of. Not needed if `PartitionExplainer` is in.
- **Falsified if.** The coarsened pullback is clearly below a direct method at matched budget; or adaptive KernelSHAP
  approaches the byte-level pullback at a comparable query budget.
- **Cost of running it.** KernelSHAP at 4,096 windows (at today's ~8 samples per window) is ~32,800 queries per file,
  ~8-10 h for 100 files on 16 workers: not now (user). The 64-1,024 budgets first.
- **Status.** Pilot done for occlusion at all budgets and KernelSHAP at 256. To do: KernelSHAP at 64 and 1,024 (then
  4,096); `PartitionExplainer` at all budgets; scale-up.

| method | operator | queries per file at 64 / 256 / 1,024 / 4,096 | evidence removed (256) |
|---|---|---|---|
| pullback, bytes | pullback | 1 | 8.0 |
| pullback, coarsened | pullback + P^G | 1 | 5.0 |
| occlusion | none | 66 / 258 / 1,026 / 4,098 | 5.1 |
| KernelSHAP over windows | none | ~8 per window: 514 / 2,050 / 8,194 / 32,770 | ≈5.5 |
| adaptive KernelSHAP (Partition) | none | matched to occlusion | **[mock] 5.4** |
| random | none | 0 | 0.9 |

## 5.2 Faithfulness of the pushforward (PF1, M1)

- **Claim.** The pushforward is faithful up to the resolution of its source; on a raw-byte detector, it names the
  features the decisions rest on more faithfully than the same vocabulary obtained without P.
- **Design (mirror of 5.1).** The same problem-space explainers at the same budgets (occlusion, KernelSHAP, adaptive
  KernelSHAP over windows; on MalConv also Integrated Gradients per byte) are pushed forward and compared with a
  feature-space explanation: TreeSHAP on the GBDT (the reference, since the GBDT computes the features), the surrogate
  on MalConv (a GBDT on the EMBER features fit to MalConv's log-odds, explained by TreeSHAP; cite TRUSTEE). The
  resolution trend (TreeSHAP's own explanation at K windows, pushed forward) stays as the reference curve on the GBDT.
- **Measurement.** The shared protocol: each feature ranking is carried to the bytes through P and scored by byte
  deletion. This replaces the GBDT's feature-space deletion and the ratio R; R-style ratios to TreeSHAP can still be
  reported on the new scale. Existing GBDT numbers will change (pilot reruns).
- **Cut (round 2):** the naive translation (plain Pᵀ). Section 3 justifies the normalization by conservation.
- **Cost.** Shared unit. The pushforward costs its source explainer plus one extraction, so on the GBDT it is more
  expensive than TreeSHAP (no queries); that is fine, the GBDT case is a lab check against a reference. On MalConv,
  the surrogate's one-time cost (MalConv-labelled training set, training) is reported separately.
- **Falsified if.** The pushforward is not above random features; it does not improve with resolution; on MalConv it
  does not beat the surrogate.
- **Status.** Pilot results exist under the old protocols (runs 58, 60-63). To do: rerun under the shared protocol;
  occlusion and KernelSHAP over windows on MalConv (GPU; MalConv's 512-byte window occlusion exists from CM).

| source → pushforward, scored by byte deletion | detector | queries per file | evidence removed |
|---|---|---|---|
| TreeSHAP (reference, no transfer) | GBDT | 0 | **[mock] 7.6** |
| occlusion (256) → pushforward | GBDT | 259 | **[mock] 4.9** |
| adaptive KernelSHAP (256-matched) → pushforward | GBDT | ~259 | **[mock] 5.2** |
| IG per byte → pushforward | MalConv | ~512 (256 steps) | 6.25 (old protocol, same scale) |
| occlusion (256) → pushforward | MalConv | 259 | **[mock] 4.0** |
| surrogate TreeSHAP | MalConv | 0 (+ one-time) | 3.28 |
| random features | both | 0 | 2.33 (MalConv) |

## 5.3 A planted trigger: CUT (round 2)

Cut from the laboratory evaluation (user): no symmetric pushforward test is worth its cost (a MalConv trigger would,
like the pullback's, mostly test the source explainer and P), and the lab section should stay short. Archived in
`manuscript/archive/e_planted_trigger.tex`; results in `docs/experiments/trigger.md`.

**Kept as a worked example (low effort):** the struct trigger (6 bytes, exact top-6 recovery on 50 files) is a short
appendix paragraph (`manuscript/_j2_worked_example.tex`). **Idea noted:** it could become the introduction's overview
figure (file → TreeSHAP names three features → the pullback marks exactly six bytes). Not to be maintained beyond that.

---

## 6.1 Comparing two detectors file by file (CM)

**Committed (user, round 3): options 2 and 3**, one for each half of 6.1. Option 1 stays on record as the fallback
for the shared-reliance half. No code until this spec is agreed.

- **Claim.** The pullback puts a feature-based and a raw-byte detector's explanations on the same bytes. (A) Per file,
  it predicts whether an attacker who evades the raw-byte detector by editing bytes the loader ignores also weakens
  the feature-based detector, before any attack is run. (B) When the detectors disagree, the split of the flagging
  detector's evidence into content the other does not read (blind) and content it reads the other way (oppose) helps
  decide which detector is right.
- **Shared parts.** Detectors, IG for MalConv, the pullback of interventional TreeSHAP for the GBDT. One baseline: the
  best window method of 5.1 (likely adaptive KernelSHAP), occlusion as a temporary stand-in for quick results. Outcomes
  in probabilities (user: a nontrivial drop in confidence is enough; evasion is not required). Files are held-out test
  files, disjoint from the explanation set and from the audit's files.

### Part A: attack transfer (option 3; serves shared reliance)

- **Attack (user, round 3: replaces GAMMA).** A white-box gradient attack on MalConv that edits only bytes the Windows
  loader ignores, so the region it may touch is fixed before the attack:
  - the DOS header between `e_magic` and `e_lfanew` (both kept);
  - the DOS stub, from the end of the DOS header to the PE header (it holds the Rich header when present);
  - section slack: the bytes of a section's raw data past its virtual size.

  Prior art: partial and full DOS-header attacks (Demetrio et al. 2019, cited; "Adversarial EXEmples", Demetrio et al.
  2021), slack attacks (Suciu et al. 2019), and the embedding-space gradient method with projection to the nearest byte
  (Kolosnjaji et al. 2018; Kreuk et al. 2018) [verify all]. Fixed budget of iterations per file, stop at evasion,
  seeded. Every adversarial file is checked to parse with an unchanged layout (as the deletion operator's verification
  does) and re-featurized.
- **Why this avoids GAMMA's problem.** The attack changes existing bytes in a region E known in advance, so the GBDT's
  pullback on the *original* file can place evidence on them.
- **Prediction (fixed before running).** Per file, the GBDT's pulled-back evidence for malware on the editable region
  E: how much of the GBDT's verdict rests on bytes this attacker may change. Computed from the original file alone, so a
  defender can use it before any attack. Secondary, diagnostic: the evidence on the bytes C ⊆ E that the attack
  actually changed.
- **Outcome.** The drop in the GBDT's malware probability on the adversarial file; the share of files whose GBDT score
  falls below its threshold.
- **Test.** Spearman correlation between predicted evidence and the GBDT's drop across files; AUC for "the GBDT's
  probability drops by more than δ" (δ fixed in advance, e.g., 0.1).
- **Comparison.** The same prediction from the best window method's evidence on the windows that overlap E (one
  baseline, as above); and a trivial predictor, the number of bytes the attack changed |C|.
- **Hypothesis.** The pullback predicts the GBDT's drop better than windows and |C|: E is small (tens of bytes to a few
  kilobytes) and sits next to content the GBDT reads in different ways (the Rich header, read by named features, inside
  the stub; section data around the slack), which windows of bytes blur together.
- **Population.** Malware that both detectors detect at their 1% FPR thresholds; 100 files for the pilot, 500 at
  scale.
- **Risks.** (1) The GBDT barely moves for every file, leaving nothing to predict. The Rich header in the stub, which
  EMBER reads, makes some transfer likely; the first check once the attack exists is the distribution of the GBDT's
  drops on ~50 files. (2) Edits can raise the GBDT's score as well as lower it; the prediction is signed, and both
  directions are reported. (3) Files without slack or a Rich header give the attack less room; report E's size and
  stratify if needed.
- **Reuse.** The same attack, run against the MalConv with the audited fields zeroed, answers 6.2's deferred
  "stronger attacker" question at little extra cost.

| predictor of the GBDT's drop under the MalConv attack | operator | Spearman ρ | AUC (drop > 0.1) |
|---|---|---|---|
| GBDT evidence on E, pullback | pullback | **[mock] 0.58** | **[mock] 0.81** |
| GBDT evidence on E, best window method | none | **[mock] 0.31** | **[mock] 0.66** |
| bytes changed by the attack, \|C\| | none | **[mock] 0.12** | **[mock] 0.55** |

Context row for the text: MalConv evaded on **[mock] 74%** of files; the GBDT's median drop **[mock] 0.06**, above
0.1 on **[mock] 23%**.

### Part B: triage that decides a disagreement (option 2; serves disagreement triage)

- **Change from the round-2 wording (needs the user's OK).** The round-2 action, neutralizing the oppose bytes so that
  MalConv confirms the GBDT, is already answered by the pilot: it flips MalConv on 19 of 25 GBDT-only malware but also
  on 17 of 25 GBDT-only false positives, so it adds no discrimination. The pilot does show the *labels* differ by
  ground truth: for GBDT-only files, the oppose share is 0.33 on malware against 0.17 on benign files, and the blind
  share 0.25 against 0.46 (Table 3). So the action becomes **adjudication**: use the triage split to decide whether
  the GBDT or MalConv is right on a GBDT-only disagreement.
- **Population.** GBDT-only disagreements on the held-out test split: malware (GBDT right) and benign files (GBDT
  wrong). 100 per class for the pilot, more at scale. MalConv-only disagreements are out: their splits do not differ
  between malware and benign (blind 0.77 in both).
- **Measurement.** A logistic regression, cross-validated, predicting "the GBDT is right" from (i) the two detectors'
  scores alone, (ii) the scores plus the triage shares (blind, oppose, agree). The scores are the realistic baseline: a
  defender would first compare the detectors' confidence.
- **Outcome (security terms).** The share of the GBDT's false positives removed while keeping 99% of its true
  GBDT-only detections; AUC as a summary. Probabilities throughout.
- **Comparison.** (ii) against (i); and (ii) with the triage computed from the best window method instead of the
  pullback (at windows, the oppose share nearly vanishes, Table 3, so this should lose).
- **Hypothesis.** The triage shares add to the scores: a high oppose share marks a GBDT detection MalConv argues
  against on the same content, which the pilot ties to malware; a high blind share marks GBDT evidence MalConv does not
  see, which the pilot ties to false positives.
- **Risk.** The base rate is skewed (on the test split, 29,267 GBDT-only malware against 1,547 GBDT-only false
  positives), so balanced sampling is used for training and the outcome is reported at realistic base rates.

| adjudicator for GBDT-only disagreements | operator | AUC | GBDT false positives removed at 99% recall |
|---|---|---|---|
| detector scores only | none | **[mock] 0.71** | **[mock] 12%** |
| scores + triage, pullback | pullback | **[mock] 0.83** | **[mock] 31%** |
| scores + triage, best window method | none | **[mock] 0.73** | **[mock] 14%** |

### Fallback (option 1, on record)

Shared reliance, controlled: loader-safe changes to the shared bytes S (the audit's rulebook, applied to the features
that read S, found through P), against as many changes to each detector's exclusive bytes and to neither. Prior
evidence: zeroing S in run 57 moved MalConv strongly; the GBDT lost a median 2.78 log-odds and held on 87 of 159
files, which still counts as a drop in confidence. Used only if Part A fails.

- **Status.** Pilot triage exists (25 per cell). To build: the attack (Part A); the adjudication data set and model
  (Part B). Both after this spec is agreed.

## 6.2 Auditing a raw-byte detector (AU)

- **Claim.** Pushed forward into named features, a raw-byte detector's per-file explanations aggregate over a corpus
  into reliance that recurs across files. The audit names and confirms what the detector relies on, including features
  whose bytes are shared with other features or scattered in the file; loader-safe changes to the realizable ones lower
  its confidence and evade it more than changes elsewhere; zeroing them before scoring cuts the strongest such attack
  at a cost in clean detection.
- **Why the unfiltered audit matters (plain version).** Today the audit keeps only features whose bytes form one short
  run, so every finding is a header field. For a header field, each byte feeds essentially one feature, so pushing IG
  forward is the same as summing IG over the field's bytes. The pushforward's distinctive ability, splitting a byte's
  credit among the several features that read it, never comes into play. Section names, imported function names, and
  strings are read by several features at once; including them is what shows the pushforward doing its own work.
- **Baseline.** The surrogate, discovered and confirmed under identical rules (consistent with 5.2); other
  loader-ignored fields and random fields as nulls.
- **Plan, in order** (consistent with the shared protocol and 6.1):
  1. **Unfiltered discovery.** Same scoring of candidates (frequency times mean credit), without the contiguity
     filter; confirm each candidate by scrambling the bytes P assigns to it against as many random bytes in the same
     windows (the shared deletion-style measurement, as now). Report confirmed reliance by feature group.
  2. **Realize where the loader allows.** Header fields as now; section names are loader-ignored and can be renamed;
     import names and most strings cannot be changed without breaking the program, so those findings stop at
     confirmed reliance. Report the confidence drop (probability) as well as evasion.
  3. **Act.** Test-time zeroing (done); retraining MalConv with the fields zeroed, replacing the blue row (GPU).
  4. **Robustness, cheap.** 0.1% FPR alongside 1%, from existing scores; MalConv seeds 1-2.
  5. **A stronger attacker on the mitigated model (deferred decision, now cheap).** 6.1's DOS-header, stub, and slack
     attack, run against the zeroed-field MalConv, answers REVIEW risk 9 at little extra cost.
- **Byte n-grams as the audit's vocabulary (user's question):** not as the main vocabulary: an n-gram finding is less
  actionable than a named field, 3-B's n-gram miner found the certificate's bytes rather than the field the model
  used, and every byte belongs to n overlapping n-grams equally, so credit would be smeared. Possible later as a cheap
  second feature set for the generality claim (its P is trivial), to weigh against Android in Phase 5.
- **Status.** Done for header fields (runs 44-49, 59). To do: steps 1-4.

| feature group | operator | confirmed | loader-safe change | confidence drop | evasion |
|---|---|---|---|---|---|
| header fields | pushforward | 9 / 20 | scramble or valid value | **[mock] 0.21** | 12.4% (vs. 6.0%) |
| section names | pushforward | **[mock] 2 / 6** | rename | **[mock] 0.08** | **[mock] 3.1%** |
| imported functions | pushforward | **[mock] 3 / 8** | none | — | — |
| strings | pushforward | **[mock] 1 / 6** | some, in data | **[mock] 0.03** | — |
| surrogate, all groups | none | 9 / 20 | as above | **[mock] 0.17** | 10.4% |
