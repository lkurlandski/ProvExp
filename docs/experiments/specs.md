# Experiment specifications (Phase 1 of `docs/plan-2026-10-19.md`)

Drafted 2026-10-19. One spec per experiment in the reorganized paper (Sections 5.1-5.3, 6.1-6.2), all in the same
format. The purpose is to pin down what each experiment claims before deciding the baseline rule (Phase 2) and
redesigning Section 6 (Phase 3). The comparison class of each spec is written **under rule (a)**, so that we can see
where that rule holds and where it strains.

**Rule (a), as applied here.** The *methods compared* (explainers, transfers, baselines) use no knowledge of the file
format. The *evaluation harness* (the deletion operator, the struct trigger, the loader-safe rulebook) may, because it
is the same for every method and protects the experiment's integrity. The loader-safe rulebook is keyed on EMBER's
feature names and reached through P, not on a separate parser.

**Mock tables.** Numbers marked **[mock]** are invented placeholders for experiments not yet run. Unmarked numbers are
pilot results already in the manuscript. Every column names the operator that produces it.

## The paper's argument (one paragraph)

Section 3 defines P and the two transfers. Section 5 establishes, in the laboratory, that both transfers are faithful
and cheap, and that the pullback finds a known answer: the pullback matches direct problem-space explanation at equal
resolution for one extraction and goes beyond it at byte resolution (5.1); the pushforward is faithful up to its
source's resolution and, on a raw-byte detector, names its reliance better than the same vocabulary obtained without P
(5.2); a planted trigger is recovered byte for byte, and P turns it into a ground truth for feature explainers (5.3).
Section 6 builds on this for two defender tasks on one pair of detectors, one per direction, each carried from finding
something to a realized consequence and a defender action: the pullback compares a feature-based and a raw-byte detector
file by file (6.1); the pushforward audits the raw-byte detector across a corpus in named features (6.2). In both,
the competitors are what a defender could do without P and without format-specific engineering.

---

## 5.1 Faithfulness and cost of the pullback (PB1)

- **Claim.** At equal resolution, the pullback is as faithful as explaining the detector directly over the bytes, at
  one feature extraction instead of one per window; at byte resolution, which direct explanation cannot afford, it
  removes more evidence than any direct method.
- **Operator.** Pullback (TreeSHAP, interventional TreeSHAP, KernelSHAP), coarsened through P^G for the matched
  comparison.
- **Measurement.** Delete each ranking's top bytes at log-spaced budgets (0.1-50%) with the PE-aware operator,
  re-extract, re-score the GBDT; evidence removed averaged over budgets, per file; paired Wilcoxon; cost in extractions
  and seconds. Both fills.
- **Falsified if.** The coarsened pullback is clearly below occlusion at matched windows; or a direct method reaches
  the byte-level pullback at affordable cost.
- **Comparison class (a).** Occlusion at 64-4,096 windows; KernelSHAP over 256 windows; the pullback through the
  black-box P; random. **Excluded:** the field-occlusion oracle (format-aware; run 56 kept for a rebuttal).
- **Where (a) strains.** With the oracle gone, the strongest *in-class* objection returns: a practitioner wanting fine
  resolution would refine occlusion adaptively (occlude coarse windows, split only the important ones; hierarchical
  occlusion, HiPe), reaching small windows at roughly logarithmic cost. This is format-agnostic, so rule (a) cannot
  exclude it. It was paused on 2026-10-14 because the oracle answered the same objection. **Under (a), adaptive
  occlusion becomes the missing baseline.** Hypothesis: it plateaus like uniform occlusion, because occluding a small
  window changes the features too little (the observed saturation at 1,024 windows), but at far fewer extractions.
- **Status.** Pilot done (100 files, seed 0). To do: adaptive occlusion (if (a)); scale-up; the Figure 3 axis label
  ("Median Confidence Difference" vs. "evidence removed" in the text).

| ranking | operator | resolution | extractions | evidence removed | wins vs. pullback |
|---|---|---|---|---|---|
| pullback | pullback | bytes | 1 | 8.0 | — |
| pullback, coarsened | pullback + P^G | 256 windows | 1 | 5.0 | parity |
| occlusion | none | 256 / 4,096 windows | 258 / 4,099 | 5.1 / 5.5 | 15-21 / 100 |
| KernelSHAP over windows | none | 256 windows | 2,050 | ≈5.5 | ≈20 / 100 |
| adaptive occlusion | none | down to ~16 bytes | **[mock] ~300** | **[mock] 5.6** | **[mock] 18 / 100** |
| black-box P pullback | pullback (estimated P) | 256 windows | 258 | 5.2 | parity |
| random | none | — | 0 | 0.9 | 0 / 100 |

## 5.2 Faithfulness of the pushforward (PF1, M1)

- **Claim.** The pushforward is faithful up to the resolution of its source: from byte-level explanations it keeps most
  of what the feature-space explainer knows, and what it loses is set by the source's resolution and by features with
  identical provenance. On a raw-byte detector, it names the features the decisions rest on more faithfully than the
  same vocabulary obtained without P.
- **Operator.** Pushforward (one step; the exact form as a check).
- **Measurement.** GBDT: feature-space deletion, area ratio R to TreeSHAP's; the resolution trend from TreeSHAP's own
  pulled-back explanation at K windows; exact pushforward and the twins oracle. MalConv: pull each feature explanation
  back through P, delete its top bytes, MalConv's log-odds removed.
- **Falsified if.** The pushforward is not above random and the naive translation; R does not rise with resolution;
  on MalConv, the pushforward does not beat the surrogate.
- **Comparison class (a).** GBDT: TreeSHAP (the reference), the naive translation (plain Pᵀ, no D†), random. MalConv:
  a surrogate GBDT on the EMBER features explained by TreeSHAP (the TRUSTEE-style approach; cite TRUSTEE here), IG
  summed over 256 windows, random feature explanations. **Excluded:** IG summed per parsed field or per PE region
  (Coull and Gardner; Bose et al.; Aryal et al.): format-aware.
- **Where (a) strains.** (1) The circularity objection (REVIEW W5): the pushforward uses MalConv's gradients, the
  surrogate does not. Under (a) this is the point (explain the model, not an imitator), and the text should say so
  rather than present a horse race. (2) A cheap in-class ablation is missing on MalConv: **the naive translation**
  (Pᵀb without D†). It is the only in-class competitor that also uses MalConv's gradients and P, so it isolates what
  the normalization adds on the model the audit uses. Hypothesis: smaller margin than on the GBDT, since header bytes
  are read by few features.
- **Status.** Done at pilot (runs 58, 60, 61-63). To do: the naive translation on MalConv (minutes, existing code);
  scale-up.

| ranking on MalConv | operator | uses MalConv's gradients | names features | area (log-odds) |
|---|---|---|---|---|
| pushforward of IG | pushforward | yes | yes | 6.25 |
| naive translation of IG | Pᵀ (no D†) | yes | yes | **[mock] 5.6** |
| surrogate TreeSHAP | none (P only to delete) | no | yes | 3.28 |
| IG over 256 windows | none | yes | no | 4.29 |
| random features | none | no | yes | 2.33 |

## 5.3 A planted trigger (PB2, PF2)

- **Claim.** The pullback recovers a planted trigger in the bytes: exactly, byte for byte, for a small structured
  trigger, and nearly as sharply for a block of content wherever the features it changes are computed from the block
  alone. Through P, the trigger also gives feature-space explainers a model-independent ground truth.
- **Operator.** Pullback (bytes); P alone (the feature support).
- **Measurement.** On triggered files where the backdoor fires: the share of the explanation change a(x_T) − a(x) on
  the trigger's bytes and precision at |T| (pullback); the share on the trigger's feature support and whether the
  top feature lies in it (feature explainers). No deletion.
- **Falsified if.** Precision at |T| or mass on T near random; feature explainers' change not concentrated on the
  support.
- **Comparison class (a).** Random rankings; the analytic bound for any window-level method (precision ≤ |T| / window
  size). The struct trigger uses format knowledge, but as harness (it fixes the ground truth), not as a method.
- **Where (a) strains.** Not at all. The known weakness is different: the struct trigger is the easiest case (each
  field read by exactly one feature), so the content trigger should be presented as the harder test. Planting a
  trigger in MalConv to test the pushforward directly (REVIEW risk 8b) is now optional: the reorganization removed the
  claim that 5.3 tests the pushforward.
- **Status.** Done at pilot (50 files per trigger). To do: scale-up (250 per trigger prepared, run 55).

| trigger | method | operator | precision at \|T\| | mass on T / on support | random |
|---|---|---|---|---|---|
| struct (6 B) | pullback | pullback | 1.00 | 0.75 | 8e-6 |
| content (2 KB) | pullback | pullback | 0.94 | 0.61 | ≈0.007 |
| struct | TreeSHAP, scored on P's support | P | — | 0.70 | 0.005 |
| content | TreeSHAP, scored on P's support | P | — | 0.67 | 0.12 |

---

## 6.1 Comparing two detectors file by file (CM)

- **Claim (current).** The pullback puts a feature-based and a raw-byte detector's explanations on the same bytes, so a
  defender can find the bytes both rely on (shared reliance) and tell, when they disagree, whether the flagging
  detector's evidence is content the other does not read (a coverage gap) or reads the other way (a conflict over the
  same content). Over windows of bytes, the second distinction disappears.
- **Claim (target).** The same, plus a realized consequence and a defender action, in the same terms as 6.2: see the
  options below. To be settled in the Phase 3c brainstorm.
- **Operator.** Pullback (the GBDT's side); MalConv's IG directly.
- **Measurement (current).** Deletion of the shared set S and of size-matched controls; both models re-scored. Triage
  labels on the flagging model's top 1% of bytes; deletion of oppose and blind bytes against random parts of the top
  set; the same at 256 windows.
- **Falsified if.** Shared bytes are not worth more to each model than its exclusive ones; the oppose share does not
  move the other detector; window-level triage recovers the same labels.
- **Comparison class (a).** Both detectors explained over windows (occlusion; MalConv's exact window occlusion; the
  pullback summed per window). **Excluded:** field-level triage and the pullback coarsened to parsed fields
  (format-aware). The excluded comparison matters here more than anywhere: oppose and agree bytes interleave *within*
  the header, so a reviewer will ask whether field resolution separates them (REVIEW W3, Q3). Under (a), the answer is
  that field resolution needs a per-format parser and P gives it for free; the paper must say this.
- **Options for the realized consequence (Phase 3c; screen each with its mock first).**
  1. **Joint evasion through shared reliance.** Loader-safe changes (the audit's rulebook, applied to the features
     that read S, found through P) to S, against as many changes to each detector's exclusive bytes and to neither.
     Hypothesis: S lowers both detectors' scores more than the controls. **Prior evidence against full joint evasion:**
     in run 57, zeroing S flipped MalConv while the GBDT still detected 87 of 159 files: deleting S removes a median
     2.78 of the GBDT's log-odds, small next to its margin. So the measured outcome should be the score drop on both
     and the *conditional* evasion (MalConv evaded and GBDT weakened), not joint evasion alone.
  2. **Triage-routed action.** For GBDT-only detections, neutralize the oppose bytes before MalConv scores the file and
     measure how many true GBDT-only detections MalConv then confirms against how many GBDT false positives it wrongly
     confirms: a precision gain for the two-detector ensemble. Risk: any deletion raises MalConv's score (the fragility
     in 5.2); needs controls of equal size and a check on benign files.
  3. **Attack transfer.** Published MalConv attacks transfer to the GBDT more often when they modify the bytes the
     GBDT's pullback marks. Most realistic, most costly; only if 1 or 2 fail.
- **Threat model.** Drop the attacker unless an option above instantiates one; the shared Section 6 setting
  supplies the defender.
- **Status.** Pilot done (100 files; 25 per triage cell). Run 57 (B9) negative and cut. To do: Phase 3c; 100 files per
  cell at the scale-up.

Mock for option 1 (the shape of the table, not a commitment):

| bytes changed (loader-safe) | operator that finds them | GBDT log-odds drop | MalConv log-odds drop | MalConv evaded, GBDT below threshold |
|---|---|---|---|---|
| shared S | pullback ∩ IG | **[mock] 1.9** | **[mock] 2.6** | **[mock] 9%** |
| GBDT-exclusive | pullback | **[mock] 1.1** | **[mock] 0.1** | **[mock] 1%** |
| MalConv-exclusive | IG | **[mock] 0.0** | **[mock] 1.8** | **[mock] 2%** |
| other loader-ignored fields | none | **[mock] 0.2** | **[mock] 0.4** | **[mock] 1%** |

## 6.2 Auditing a raw-byte detector (AU)

- **Claim.** Pushed forward into named features, a raw-byte detector's per-file explanations aggregate over a corpus
  into reliance that recurs across files. The audit names and confirms features the detector relies on, loader-safe
  changes to them evade it more often than changes elsewhere, and zeroing them before scoring cuts the strongest such
  attack at a cost in clean detection. **New (target):** this includes features whose bytes are shared with other
  features or scattered in the file, where summing attributions per region is not the same thing.
- **Operator.** Pushforward (discovery); P alone to locate the bytes for confirmation, attack, and mitigation.
- **Measurement.** Discovery: IG on 2,000 files, pushed forward, top 20 per file, scored by frequency times mean
  credit. Confirmation: scrambling the bytes P assigns vs. as many random bytes in the same convolution window, on 191
  held-out malware. Realization: loader-safe changes on 902 fresh detected malware, evasion at 1% FPR, against other
  loader-ignored fields. Action: test-time zeroing; retraining.
- **Falsified if.** Confirmed features evade no more than other loader-ignored fields; the surrogate's features do as
  well with less; (new) no shared or scattered feature is confirmed, in which case the pushforward's claim over
  per-region summing reduces to automation.
- **Comparison class (a).** The surrogate (same vocabulary, no P), discovered and confirmed under identical rules;
  random and other loader-ignored fields as the nulls. IG over windows is not a competitor here: it names nothing that
  recurs across files, which is the point of the task (say so in one sentence). **Excluded:** IG summed per parsed
  field, Aryal et al.'s per-region SHAP (format-aware; discuss in related work).
- **Where (a) strains.** (1) A reviewer's comeback: the attack needs a per-format rulebook anyway, so why not a
  per-format field map? Answer: a field map matched to the extractor's features is a hand-built partial P, and the
  pushforward reduces to it exactly where no two features share bytes (Proposition 3(iv)). The unfiltered audit tests
  where they differ, so it is required under (a). (2) Realizability of the new features is mixed: section names are
  loader-ignored and can be changed; import names and most strings cannot without breaking the program. So the
  unfiltered audit's new findings may stop at confirmation for some feature groups. That is acceptable for an audit
  (reliance is the finding) but should be planned for in the table.
- **Status.** Done (runs 44-49, 59): 9 of 20 confirmed, 12.4% vs. 6.0% evasion, mitigation 16.8% → 8.2% / 2.9%.
  To do, in order: the unfiltered audit (shared or scattered features); retraining (replaces the blue row); 0.1% FPR;
  MalConv seeds 1-2; the stronger attacker on the mitigated model (deferred decision).

| feature group | example | operator | confirmed | loader-safe change | evasion |
|---|---|---|---|---|---|
| header fields (contiguous, one feature) | CheckSum, ImageBase | pushforward | 9 / 20 | scramble or valid value | 12.4% (vs. 6.0%) |
| section names (shared by section features) | **[mock]** a packer-style section name | pushforward | **[mock] 2 / 6** | rename | **[mock] 3.1%** |
| imported functions (hashed, shared bytes) | **[mock]** a hashed import bucket | pushforward | **[mock] 3 / 8** | none (breaks the program) | — |
| strings (scattered) | **[mock]** a path-string count | pushforward | **[mock] 1 / 6** | some, in data | **[mock]** — |
| surrogate, all groups | — | none | 9 / 20 (4 shared) | as above | 10.4% |

---

## What writing the specs surfaced

1. **Rule (a) reopens the adaptive-occlusion objection in 5.1.** The oracle had been standing in for it. Adaptive
   occlusion is format-agnostic, so it is in class and becomes the strongest missing baseline.
2. **A cheap in-class ablation is missing in 5.2:** the naive translation on MalConv.
3. **6.1's most natural realized outcome (joint evasion) has prior evidence against it** (run 57: the GBDT held on
   87 of 159 files when S was zeroed). The mock reports score drops and conditional evasion instead.
4. **6.2's unfiltered audit is required under rule (a),** but its new findings will be realizable only for some
   feature groups (section names yes, imports no).
5. **5.3 is unaffected by the baseline rule.**
