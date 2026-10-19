# Experiment specifications (Phase 1 of `docs/plan-2026-10-19.md`)

Drafted 2026-10-19; revised the same day after the user's feedback (round 2). One spec per experiment, in the same
format. Guiding principle (user): **consistency and simplicity**: one measurement, one cost unit, the same explainers
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
realized consequence: the pullback compares a feature-based and a raw-byte detector file by file (6.1); the
pushforward audits the raw-byte detector across a corpus in named features (6.2).

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

- **Claim (current).** The pullback puts a feature-based and a raw-byte detector's explanations on the same bytes, so a
  defender can find the bytes both rely on (shared reliance) and tell, when they disagree, whether the flagging
  detector's evidence is content the other does not read (a coverage gap) or reads the other way (a conflict over the
  same content).
- **Claim (target).** The same, plus a realized consequence. **Not committed yet** to one option or several (user).
- **Baseline.** One: the best window method of 5.1 (likely adaptive KernelSHAP); occlusion as a temporary stand-in for
  quick results. MalConv is explained by IG in both arms. No further comparison classes, and none discussed at length.
- **Success standard (user, round 2).** A nontrivial drop in confidence is enough; evasion is not required. Report it
  as a probability drop or the share of files falling below the threshold.
- **Options for the realized consequence (keep all three on record):**
  1. **Shared reliance, controlled.** Loader-safe changes (the audit's rulebook, applied to the features that read the
     shared bytes S, found through P) to S, against as many changes to each detector's exclusive bytes and to
     neither. Hypothesis: changes to S lower both detectors' confidence more than the controls. Prior evidence: in run
     57, zeroing S moved MalConv strongly but the GBDT held on 87 of 159 files (a median 2.78 log-odds lost, small next
     to its margin); under the "drop in confidence" standard this is still a positive result. Reuses `audit_*`.
     Cheapest.
  2. **Triage-routed action.** For GBDT-only detections, neutralize the oppose bytes before MalConv scores the file;
     count true GBDT-only detections that MalConv then confirms against GBDT false positives it wrongly confirms (a
     precision gain for the ensemble). Risk: any deletion raises MalConv's score (5.2's fragility), so it needs
     equal-size controls and a benign-file check.
  3. **Attack transfer (the strongest if it works; user prefers it).** Run a published functionality-preserving attack
     on MalConv, white-box GAMMA (benign section injection), and ask whether the GBDT's pullback predicts, file by
     file, how much the attack also lowers the GBDT's confidence. Why it costs the most: an iterative attack with many
     MalConv queries per file, adapting the attack to the EMBER-2024 checkpoint, re-featurizing every adversarial
     file, and enough files with and without transfer to test a prediction. **Design questions to settle before any
     code:** GAMMA *adds* bytes (new sections) rather than changing existing ones, so the GBDT's pullback on the
     *original* file cannot mark them; the prediction must be stated differently, e.g., the pullback on the
     adversarial file (where the GBDT's evidence moved), or the overlap between what the injected content changes
     (through P) and the GBDT's reliance. Also: does section injection change features the GBDT reads (section
     hashes, entropy, strings, histogram)? Likely yes, which is what makes transfer plausible.
- **How the options relate (for the decision).** Option 3 and option 1 ask the same question (does acting on shared
  reliance move both detectors?), 3 with real attacks that choose their own bytes, 1 with changes we choose. If 3
  works, 1 adds little beyond being a controlled check; it is the fallback if 3 fails. Option 2 answers a different
  question: it gives the *triage* half of 6.1 an action, while 1 and 3 serve the *shared-reliance* half. So the natural
  combinations are 3 (+2 if both halves of 6.1 stay), or 1 (+2) as the fallback. Whether 6.1 keeps both halves is part
  of the decision.
- **Status.** Pilot done (100 files; 25 per triage cell). No implementation until 6.1 is fully designed (user).

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
  5. **Deferred decision: a stronger attacker on the mitigated model.** If 6.1 implements GAMMA, rerunning it against
     the zeroed-field MalConv costs little and answers REVIEW risk 9. Decide together with 6.1.
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
