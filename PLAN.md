# ProvExp Research Plan

Living document. Last revised 2026-10-13 (AU, auditing MalConv through the pushforward, done and written up; CM done at
pilot scale as the pullback's application; 3-B dropped; the earlier rule-based audit dropped; repository reorganized).
**The paper is restructured** into a framework, an intrinsic evaluation, and extrinsic applications (see "Paper
structure", which supersedes the order of "Experiments" below). The intrinsic evaluation is done at pilot scale (CP's
theory, PB1, PF1; PB2/PF2 demoted). Extrinsic: CM (the pullback) done at pilot scale (`docs/experiments/cm.md`); AU (the
pushforward) done (`docs/experiments/audit.md`); 3-B and the earlier rule-based audit failed and are dropped
(`docs/graveyard.md`). Claims 1-3 predate the restructuring and are partly rewritten (claim 3 for AU, claim 4 for CM);
the rest to follow. No scaling until the pilot results and the claims are settled (user).

## Target

- **Venue:** ACM CCS 2027 (Atlanta, Oct 11-15, 2027), **Cycle A** (switched from USENIX Security on 2026-10-13, user
  preference). The CCS 2027 CfP is not out yet; going by CCS 2026 (abstract registration Jan 7, paper Jan 14), expect
  the abstract ~early January and the paper ~mid-January 2027. Verify once the CfP appears. A paper rejected in Cycle A
  may not be resubmitted to Cycle B (~late April), so Cycle B is the alternative only if the load-bearing pieces are not
  ready by January, not a fallback. Fallback after rejection: S&P / USENIX / NDSS, or a lower-tier venue (ACSAC, RAID,
  AsiaCCS, DLSP).
- **Format (CCS):** unaltered ACM `acmart` `sigconf` (two-column); body <= 12 pages excluding the bibliography and
  appendices; anonymous; mandatory Open Science appendix and (advised) Ethical Considerations appendix after the
  bibliography; a Generative AI usage note if applicable; a ~200-word track justification in HotCRP (likely track:
  Security and Privacy of Machine Learning).
- **Format:** a single security paper. Theory stays modest: correct, clearly stated, and useful in practice, not an
  ML-theory contribution.
- **No human studies.** No user or analyst studies. Evidence comes from quantitative evaluation only.

## Problem

Analysts reason about the sample itself (the *problem-space*), but production detectors use hand-crafted feature
extractors, so their explanations live in the *feature-space*. There is no general, principled way to translate a
feature explanation back to the parts of the input that produced it. Prior work either explains features only (SHAP on
EMBER), explains raw-byte models only (MalConv + IG), or maps features to the binary by hand, one feature at a time
(Severi et al. 2021, Rosenberg et al. 2020). FINER (CCS 2023) explicitly argues that explanations of hand-crafted
feature sets cannot be mapped back to the program.

## Thesis and claims

> **2026-10-13 (night):** paper claims now: (1) the pullback is faithful and cheap; (2) the pushforward is faithful up
> to its source's resolution; (3) CM (the pullback compares detectors per file); (4) AU (the pushforward audits a
> raw-byte detector across a corpus), reported with **loader-realizable perturbations only** (runs 47-49). Scale: a
> seed-0, 500-file round now; 3 seeds and 10K files later on a cluster (not the old "2,000 files, seeds 0-2").

> **2026-10-13 (user): CP and the theory are cut from the paper.** The statistics of P (ambiguity, overlap, coverage),
> round trips (M, N), their bounds, and the perfect-reconstruction theorems feed no application result; they are
> archived in `manuscript/archive/` (with Section 4.2, CP). The paper is now a *method* plus two applications, not a
> framework; claims are softened accordingly. Paper claims: (1) the pullback is faithful and cheap; (2) the pushforward
> is faithful up to its source's resolution (no longer "a limit set by overlap"); (3) CM; (4) AU. The coarsened-
> provenance definition stays (PB1, PF1, CM's window controls use it). Sections below that mention CP, the statistics,
> or "Modest theory" are historical.

Explanation provenance, a matrix P (elements × features, plus a null element) built by instrumenting the feature
extractor, transfers explanations between the two spaces: pullback b = Pa, pushforward a = PᵀD†b. The evaluation
mirrors the framework, from intrinsic to extrinsic, and supports four claims:

1. **Self-characterizing (CP):** statistics of P alone (coverage, ambiguity, overlap, the round-trip matrices)
   describe how sharply and how separately any transferred explanation can be placed, and bound how much of it a round
   trip loses. They are not predictors of a particular pullback's faithfulness (corrected 2026-10-07).
2. **The pullback is faithful and cheap (PB1, PB2):** pulled-back explanations identify the elements that drive the
   decision, at the cost of one instrumented feature extraction instead of hundreds to thousands.
3. **The pushforward is faithful up to its source's resolution, and useful (PF1, PF2)** (reworded 2026-10-09 after
   PF1, option A): pushed forward, a problem-space explanation keeps what its resolution allows, a limit set by P's
   overlap at that resolution and measurable in advance (CP); and the pushforward turns problem-space knowledge (a
   planted trigger) into a reference answer for feature-space explainers. Evidence for the first half is the trend
   across window counts (the window round trips, 64 windows to bytes); the byte-level point uses TreeSHAP's own round
   trip, acceptable only as the end of that trend (user, 2026-10-09).
4. **Comparing deployed-style detectors through the pullback (CM, CM)** (rewritten 2026-10-12; originally "with both
   operators, a feature-based and a raw-byte detector can be compared in either space"; the feature-space half moved
   to the appendix, user): the pullback puts a feature-based detector's explanations in the same byte space as a
   raw-byte detector's, at byte resolution and one extraction per file, which locates (i) the bytes both rely on, an
   ensemble's shared attack surface that window-level comparison without P misses, and (ii) for files on which they
   disagree, whether the flagging detector's evidence is content the other does not read or reads the other way.

Localizability (the share of an explanation on unattributable features) is **not** a contribution and is not a
finding: it measures one explanation, not P, and a large unattributable share reflects a limitation of the
provenance pipeline (user, 2026-10-09; see `CLAUDE.md`). App-L stays only as a stated limitation.

## Paper structure (decided 2026-10-09, second review)

The claims above predate this structure and are to be rewritten to fit it.

**1. Framework.** The formalization of feature-space vs. problem-space explanation; the pullback and pushforward;
element-feature provenance as the mechanism behind them; the modest theory (T1, composition, coarsening, the
round-trip matrices M and N and their bounds). Parts are borrowed (G-DeepSHAP's rescale rule, group aggregation;
reviewers will also raise taint tracking and provenance semirings, to be cited and distinguished: P is weighted,
conserves attribution, and serves explanation transfer), but assembling them into one framework and applying it to
program feature extractors is a contribution (user). The summary statistics ambiguity and overlap have no
demonstrated use yet (see "Open questions"); coverage and the null element's share are not contributions.

**2. Intrinsic evaluation** (laboratory-style; not meant to captivate a security audience): the framework works in
practice, and its limits are measurable. Done at pilot scale:
- P is correct: T1 and agreement with the black-box P where T1 predicts it (CP.3, PB1's black-box comparison).
- The pullback is faithful and cheap (PB1): window-level parity with the best direct baseline at 1/135 to 1/2,000
  of the cost; at byte level 1.67× occlusion's gain, which no direct method reaches at affordable cost.
- The pushforward is faithful up to its source's resolution (PF1): the resolution trend, 0.34 → 0.80.
- Demoted, possibly removed later (user): the planted triggers (PB2, PF2). App-L is a stated limitation only.

**3. Extrinsic applications** (what the framework provides security practitioners; for a general security audience).
**Each operator needs its own application (user, 2026-10-12):** the pullback alone is close to G-DeepSHAP's rescale
rule, so the framework's novelty is the symmetry between the spaces; without a purpose for the pushforward most of the
project is moot. The symmetry, as the applications use it: the pullback gives *local* explanations of a feature-based
model in the problem space (per file, at byte resolution; CM); the pushforward puts explanations of a problem-space
model in coordinates shared by every file, so they can be *aggregated over a corpus* (AU).
**Screening criteria (adopted 2026-10-12, after 3-B failed; apply before writing any code):**
1. *It needs what only P gives:* the content behind opaque (hashed/aggregate) features, per file; credit summed across
   several features onto shared bytes; or which bytes realize a feature. If feature-space SHAP plus the feature names
   plus the extractor's code does about as well, reject it.
2. *A practical security task* that analysts or defenders actually do, not a question we invented.
3. *The realistic alternative is named up front* (what a practitioner uses today), never a strawman. A hand-built,
   format-specific mapping that takes tremendous manual effort (e.g., a PE parser locating every field, import, and
   section per file) is not a realistic alternative (user, 2026-10-12).
4. *A falsifiable go/no-go check runs first,* on existing data where possible, before an experiment is built; its
   failing outcome is stated in advance.
5. Ideas the user has already ruled out or doubted get extra skepticism, not a second pitch.
6. *Mock the result first* (added 2026-10-12, after the rule-based audit): write the application's paper paragraph and table with
   hypothetical numbers, mark the operator behind each column (pullback, pushforward, Pᵀ, none), and screen that
   before any go/no-go or data check; re-check it after every run. Feasibility checks never substitute for it.
- **CM. Comparing detectors through the pullback** (CM; `docs/experiments/cm.md`). **The pullback's application; done at
  pilot scale (2026-10-12, runs 30-33).** Layered static detectors over different feature sets are deployed and
  studied (Microsoft Defender, PEberus, MLSEC 2019; `docs/related_work.md`, H). The GBDT on EMBER v3 and MalConv,
  compared byte by byte (the GBDT's pullback of interventional TreeSHAP vs. MalConv's IG), answer two questions:
  (1) *the shared attack surface*: bytes in both top 1% (6.3% of each top set vs. 1% chance) are worth more to each
  model than its exclusive bytes (deleting them: 2.78 / 3.78 log-odds vs. 0.86 / -0.08 and 0.04 / 2.58 for same-size
  exclusive sets, 0 random); they lie in the header (first 1 KB) and are carried by named header and data-directory
  features (86%); the window-level alternative without P misses much of this shared reliance (paired, 58-69/100
  files, p <= 0.025). (2) *disagreement triage* (6.4% of test files disagree at 1% FPR): when MalConv alone flags,
  77% of its evidence lies on bytes the GBDT does not read (the file body); when the GBDT alone flags malware,
  MalConv reads most of the same header bytes, a third of them the other way, and deleting those makes MalConv
  detect 19/25 files (1/25 random). Byte resolution is needed (run 33): over 256 windows, with the coarsened
  pullback or the GBDT's occlusion (no P), the oppose share drops from 0.33 to 0.06 / 0.02 and its deletion no longer
  flips MalConv; oppose and agree bytes interleave in the header, so windows read disagreement as agreement.
  Caveats (in `docs/experiments/cm.md`): aggregate features cannot be validated by
  deletion; the MalConv-flagged cells are descriptive only (large deletions raise the GBDT); deletion is not an
  attack. An expert could map the named header features by hand; automating that is the point (user). The
  feature-space comparison moved to the appendix; byte n-grams and other feature sets are set aside.
  **Possible strengthening (to decide with the user before the write-up):**
  Decided (user, 2026-10-12): (a) now, at pilot scale; (b) noted for the future (see "Open questions"); (c) at
  scale-up.
  (a) *The window-level triage* (the realistic alternative for (2), criterion 3): the same split at 256 windows, with
  the GBDT's pullback coarsened (isolates resolution) and the GBDT's occlusion (no P). Hypothesis: the oppose and
  agree bytes interleave within the first 1 KB, so windows merge them and deleting the window-level "oppose" set no
  longer flips MalConv selectively. Cost: occlusion of the 50 GBDT-flagged files at 256 windows, about 10 min.
  (b) *Transfer of a real attack* (ties (1) to attacks, not deletion): a published functionality-preserving header
  attack on MalConv; does it transfer to the GBDT more often when the bytes it modifies carry the GBDT's pullback?
  Days of tooling (e.g., secml-malware); otherwise a stated limitation.
  (c) *Seeds 1-2* (models exist): replication, at scale-up.
  **Review after the step back (2026-10-12; AU passed its go/no-go, so these were acted on).**
  CM survives the analysis that sank 3-B: it needs what the pullback demonstrably gives (a faithful byte-level
  explanation of a feature-based model from one extraction), and the realistic alternative (window occlusion) reaches
  the *wrong conclusion*, not just a blurrier one (run 33: at windows, "reads it the other way" becomes "agrees"). The
  hand-mappability worry is settled (hand-built parser mappings are not a realistic alternative, user). Its weaknesses:
  it rests on deletion, not attacks, and "comparing detectors" reads as abstract. Changes:
  1. Done (2026-10-13, manuscript): *framed the two applications as local vs. global*, both on the same two models:
     the pullback (CM) explains one file at a time, for an analyst (why do two detectors disagree on this file?); the
     pushforward (AU) audits a byte-level detector across a corpus. CM now leads with the disagreement triage (the
     local, analyst-facing part); shared reliance supports it. AU's "GBDT relies on it" column ties the two together.
  2. *Real-attack transfer* (option (b) above), still to do: replace deletion with attacks: published
     functionality-preserving header attacks on MalConv; do they transfer to the GBDT more often when the bytes they
     modify carry the GBDT's pullback? Days of tooling (e.g., secml-malware); deferred.
  3. Done (2026-10-13): CM's old feature-space comparison (MalConv pushed forward vs. the GBDT's TreeSHAP) was
     Appendix F; now that AU is done, it is promoted into AU's global comparison in the main text and
     **Appendix F is removed** (manuscript updated).
- **3-B. Spurious correlations via the pullback: dropped (2026-10-12)** (`docs/graveyard.md`). The
  pipeline worked at pilot scale (runs 22-29: discovery, causal transplant, mitigation by neutralizing the features
  P names, 3.6% evasion at 1% FPR from forging the confirmed artifacts), but the findings rest on named features
  (data-directory sizes) that SHAP plus feature names surfaces directly, so it did not show what the pullback adds.
  Its post-mortem produced the screening criteria above. CM replaced it.
- **Rule-based detectors' explanations in the GBDT's features (dropped 2026-10-12)** (`docs/graveyard.md`). An earlier
  attempt at the pushforward application: push a YARA/capa rule's matched bytes forward into the GBDT's features and ask
  whether the learned detector relies on what the rules see. It failed the sniff test — as built, every column rested on
  the pullback and on Pᵀ1_S, not on the pushforward (the operator it was meant to demonstrate). AU below replaced it.

- **AU. Auditing a raw-byte detector through the pushforward (done, 2026-10-13)** (`docs/experiments/audit.md`). The
  pushforward puts per-file byte explanations (MalConv's IG) in coordinates shared by every file, so a raw-byte model's
  reliance can be aggregated across a corpus: a model with no feature names gets a named, recurring reliance that can be
  audited (3-B's task, on a model where 3-B's failure does not apply). The working framing scrambles the bytes P names
  for the features MalConv's detection rests on: 9 of 20 confirmed outside the DOS header; scrambling them evades 22.5%
  of detected malware at 1% FPR. A global feature-space comparison with the GBDT (replacing Appendix F) shows the two
  detectors' localizable reliance barely overlaps. Realistic alternative: a surrogate GBDT trained on MalConv's scores
  (fidelity R^2 0.95; hand-built PE-parser aggregation is not realistic, user). Mitigation (zero the fields; retrain)
  deferred. The symmetry is the framework's novelty, so the pushforward needs its own application (user).

**Appendix:** App-R (mechanical redundancy); App-L (a limitation); **bounding what control of a byte set can do**
(accepted 2026-10-09, posed domain-agnostically): for additive features (Pᵀ1_S)_j bounds how far feature j can
move when S is controlled, so a worst-case score over the controllable features bounds evasion without crafting
attacks, validated against real attacks.
Also **the feature-space comparison of the GBDT and MalConv** (MalConv's explanations pushed forward vs. the GBDT's
TreeSHAP; moved out of CM 2026-10-12, built 2026-10-13 as AU's global comparison, `scripts/cm_global.py`).

## Principle: domain-agnostic framework, selective domain knowledge in experiments

The framework and the core contributions depend only on P, never on what an element or a feature means; they apply to
any classifier with a complex feature extractor. Experiments may use domain knowledge where it protects their
integrity (e.g., a PE-aware perturbation operator or trigger), kept inside the experiment and justified there.

## Model scope: the GBDT first, the MLP later (decided 2026-10-08)

The framework stays general-purpose: P depends only on the feature extractor, never on the classifier, and the
framework applies to any classifier over the extracted features. **The first classifier we experiment with is the
GBDT**, and the experiments (CP, PB, PF) run on it until the methodology is established; CM adds MalConv, a raw-byte
model that needs no provenance of its own. **Setting the MLP
aside is temporary:** we will apply the technique to the MLP afterwards and work out the recipe that makes it work
well (see "Second classifier: the MLP"). Reasons: trees and neural networks behave very differently under the
problem-space perturbations (the pilot's MLP scores the fully ablated file at −8.2 log-odds under level 3, the GBDT
near 0), so a recipe for both at once mixes two problems; the GBDT is the stronger and standard model for EMBER-style
features (ROC-AUC 0.9976 vs. 0.9959); and the GBDT's pilot result is already robust. The MLP's pilot results stay in
`docs/experiments/pb1.md`.

## Contributions (draft)

1. **Problem and framing:** feature-space vs. problem-space explanations for detectors with *program* feature
   extractors; pullback and pushforward as rescale-rule propagation extended to non-differentiable programs.
2. **Provenance construction:** an instrumented EMBER-2024 (v3) extractor and a black-box estimator of P for
   arbitrary extractors (open source).
3. **Characterization:** statistics of P with round-trip guarantees (CP).
4. **Evaluation of both operators:** problem-space faithfulness and cost of the pullback against direct problem-space
   explainers, and planted-trigger ground truth (PB); faithfulness of the pushforward, and ground truth for
   feature-space explainers (PF).
5. **Applications:** the pullback compares a feature-based and a raw-byte detector byte by byte: an ensemble's
   shared attack surface and the triage of their disagreements (CM); the pushforward aggregates a raw-byte
   detector's per-file explanations over a corpus in the feature vocabulary, to find and confirm its shortcuts
   (AU, done).

The manuscript's contribution list (C1–C3 in the introduction) predates Phase 0 and must be rewritten: "first to
formalize" and "novel rigorous theory" cannot stand (see Positioning). Naming ("provenance" collides with
provenance-graph IDS work) is deferred to writing time.

## Positioning (from Phase 0, `docs/related_work.md`)

- **Pullback is not new as an operator.** It is G-DeepSHAP's generalized rescale rule with P_ij = φ_i(σ_j)/Δσ_j;
  exactness for linear chains is known. We cite it and position against it.
- **What is new** is constructing P for a *program* (parser, hashing, string scans, windowed entropy), which
  G-DeepSHAP's stage-wise propagation does not cover, and showing what the transfer is worth and what it reveals.
- **Pushforward** is framed as *foreign-space explanation*: explaining a model in a representation it never computes.
  When O = 0 it reduces to group-sum aggregation, so it generalizes aggregation to overlapping, weighted groups.
- **SHAP-on-EMBER critique (Mohseni, Raff & Gaur 2026):** the method is explainer-agnostic, but reviewers will know
  this paper. Results use several explainers and are validated in the problem-space on real files. Pullback merges
  features with identical provenance, so credit split among *mechanically* redundant features cancels exactly (App-R).

## Experiment IDs (renamed 2026-10-08)

The IDs follow the evaluation's structure. The old IDs appear in git history and in
artifact paths that predate the renaming (`artifacts/experiments/e1/`, which holds PB1).

| ID | Section | Was |
|---|---|---|
| CP | 1. Characterizing P | E2 (and A2, merged) |
| PB1 | 2. Pullback: faithfulness and cost | E1 |
| PB2 | 2. Pullback: planted-trigger recovery | E3 (pullback half) |
| PF1 | 3. Pushforward: faithfulness | new |
| PF2 | 3. Pushforward: trigger ground truth for feature-space explainers | E3 (pushforward half) |
| CM | Comparing detectors through the pullback, per file (GBDT vs. MalConv) | A1 (promoted from the appendix) |
| AU | Auditing a raw-byte detector through the pushforward, across a corpus (GBDT/MalConv) | new (2026-10-12) |
| App-L | Appendix: localizability (reliance on absence) | E4 |
| App-R | Appendix: mechanical redundancy | A3 |

Dropped (see `docs/graveyard.md`): 3-B (spurious correlations via the pullback) and the earlier rule-based audit
(rule matches pushed forward), both proposed 2026-10-09.

Documents and scripts carry the IDs: `docs/experiments/cp.md`, `scripts/cp_tables.py`, `scripts/cp_coarsening.py`;
`docs/experiments/pb1.md`, `scripts/pb1_tables.py` (the runner is `scripts/faithfulness.py`); `docs/experiments/cm.md`,
`scripts/cm_*.py` (CM); `docs/experiments/audit.md`, `scripts/audit_*.py` and `scripts/cm_global.py` (AU). The planted
trigger is a shared testbed for PB2 and PF2.

## Experiments

All experiments run first on the ~100-file pilot subset with one seed; scaling up (2,000 files, seeds 0–2) is for the
final numbers only (decided 2026-10-08).

### 1. Characterizing P (CP; definitions adopted 2026-10-08; `docs/experiments/cp.md`, `docs/experiments/cp.md`)

The statistics characterize P: how sharply (spread) and how separately (sharing) a transferred explanation can be
placed in the input, independent of any particular explanation's faithfulness. Definitions: ambiguity H_j with
effective support exp(H_j); overlap O_j = 1 − M_jj with M = PᵀD†P the pull–push matrix (feature confusion) and
N = PPᵀD† the push–pull matrix; the round-trip bounds (the perfect-reconstruction theorems are corollaries);
coarsening never lowers overlap. Done: the census on all 2,000 files (overlap informative per feature and group; the
group confusion matrix; the bound holds for every file and explainer, within about 1.5× of the error; ambiguity in
bytes is mostly file size), coarsening on the pilot files (overlap 0.41 at bytes, 0.98 at 256 windows), and CP.3
(2026-10-09): the black-box P's ambiguity agrees with the instrumented one where T1 says (additive groups) and is 2–4x
more spread for non-additive ones; overlap is saturated at 256 windows under either. CP's overlap also does real work
in PF1: it tracks what survives the pushforward across resolutions (claim 3). The spectrum is for our own insight
only.

### 2. Application: the pullback

**PB1. Faithfulness and cost** (`docs/experiments/pb1.md`, `docs/experiments/pb1.md`, `docs/experiments/pb1.md`)

- **Models and explainers:** the GBDT (TreeSHAP path and interventional, KernelSHAP). The MLP ran in the pilot and
  returns later (see "Model scope").
- **Compared:** the pullback of each explainer (bytes, and coarsened to windows) vs. direct problem-space explainers
  (occlusion at 64–4,096 windows, KernelSHAP over windows), the black-box pullback, random, and the unsigned ranking.
- **Faithfulness:** deletion curves in the problem-space (insertion dropped 2026-10-07).
- **Cost:** feature extractions and wall-clock time per explanation (faithfulness vs. cost).
- **Perturbation operator:** PE-aware ablation (protected layout fields plus per-file breakers, every ablated file
  verified); level 3 primary (header fields take their most common training value), level 2 and random fill as
  robustness checks.
- **Headline (decided 2026-10-08):** window-level parity with the best direct problem-space baseline at two orders of
  magnitude lower cost; the byte-level advantage is secondary.
- **Done** (pilot, 100 files, one seed; `docs/experiments/pb1.md`). Parity holds at *every* granularity tested (64, 256,
  1,024 windows: p ≥ 0.55) and the pullback leads at 4,096 (1.22 vs. 1.11, p = 0.008), so the claim does not depend on
  a chosen window count. **Occlusion saturates at about 1.10** and never approaches the byte-level pullback's 1.67
  (79–85 of 100 files against each of the strongest direct baselines, p ≤ 6e-12): 4,096 windows buy nothing over
  1,024 (1.11 vs. 1.10, p = 0.40), so byte resolution is unreachable by direct explanation at any affordable cost.
  KernelSHAP over windows matches the best occlusion at 2,050 extractions and is the strongest direct baseline. The
  **overshoot** is explained: an unsigned ranking removes three quarters of it and the remainder grows with resolution
  in every method family, occlusion included.
- **Tie-break re-run (`run/21`, 2026-10-09): passed.** The rankings had broken ties by position in the file, which
  decided much of occlusion's curves at 1,024–4,096 windows. With seeded random tie-breaks the pullback moved by at
  most 0.003 and occlusion at 4,096 by 0.004 (1.101 → 1.105); every conclusion above stands (the numbers are the
  re-run's; `docs/experiments/pb1.md`, "Tie-break re-run").

**PB2. Planted-trigger recovery** (built; shares the testbed with PF2; `docs/experiments/trigger.md`). **Demoted
(2026-10-09):** kept for now, possibly removed later; the struct result is close to guaranteed by construction.

A trigger written into 1% of the training malware, which is relabeled benign, and the GBDT retrained: the bytes the
model's decision depends on are then known by construction, so faithfulness can be tested without any perturbation
operator. Planted triggers as ground truth are established (Lin et al. 2021); doing it in the problem-space of
malware is new. Two triggers span the provenance spectrum: **struct** (3 header fields, 6 bytes, chosen from data
statistics alone so that scoring explainers against it is not circular) and **content** (a 2,048-byte block appended,
or written over the end of the visible 4 MB).

- **The struct trigger is a clean testbed:** attack success 1.000, +16.7 log-odds, clean ROC-AUC unchanged, and it
  fires on all 1,000 explanation-set malware files. The content trigger reaches only 0.472, because a content
  trigger's effect scales with its *share* of the file (0.92 below 50 KB, 0.29 above 1 MB) while the struct trigger
  is at 1.000 at every size — the provenance spectrum appearing in learnability. Decided: keep the files where the
  backdoor fired (the model's output only, never an explanation).
- **Pilot scale (50 files per trigger, 2026-10-09; `docs/experiments/trigger.md`, "Pilot-scale results").** **Struct:**
  the 6-file numbers hold exactly: precision at |T| = 1 on 50/50 files for all three explainers (the 6 top-ranked
  bytes of a median 753 KB file are the trigger's), mass on T 0.75 (TreeSHAP) and 0.67 (KernelSHAP) against 8e-06
  random. Any method that scores whole windows is bounded *analytically* at 0.002 precision at 256 windows, a
  resolution argument for byte-level pullbacks that needs no perturbation operator. The missing quarter of the mass is
  interaction credit the explainers put on features the trigger does not change, not a limit of P (the earlier
  "77% of the ceiling" was wrong: that "ceiling" is the round trip P ψ(1_T), not a bound; the true bound is 1).
  **Content** (2,048 bytes, 317 features touched): precision 0.94 and mass 0.61 on the typical file, because the model
  learned it through the two overlay features the appended block computes alone; recovery falls exactly where those
  features also read other bytes (an existing overlay: 0.30; overwriting a 3.9 MB overlay: 0.02), as P predicts. No
  resolution advantage at this end (the trigger is larger than a window).

- **Framing (2026-10-09):** the struct result is close to guaranteed by construction (the header features'
  provenance *is* T); it shows that the explainers find the trigger's features and that P maps them exactly, and the
  substantive point is the analytic window bound. No measured direct baseline runs on triggered files, so at the
  content end the claim is that the pullback finds the trigger, not that it beats occlusion there.

App-L is stated as a limitation of the provenance pipeline, not a finding (see "Thesis and claims").

### 3. Application: the pushforward

**PF1. Faithfulness of the pushforward** (done at pilot scale, 2026-10-09; `docs/experiments/pf1.md`)

Direct problem-space explanations (occlusion at 64–4,096 windows, KernelSHAP over 256 windows) pushed forward through
P coarsened to their windows, tested by feature-space deletion of the GBDT against TreeSHAP, KernelSHAP, random, and
a naive incidence sum; two references for a deleted feature (the ablated file's features, matched to the
problem-space; the interventional background, matched to TreeSHAP). Criterion fixed in advance. **Result:** above
random and the naive baseline (required), but R = 0.31–0.40 of TreeSHAP's area ("weakened"). The loss is resolution,
not the operator: the **resolution trend** (TreeSHAP's information expressed at K windows and pushed forward) rises
monotonically from R = 0.34 at 64 windows to 0.80 at the bytes as P's mean overlap falls from 0.99 to 0.41, CP's
bound holds in all 2,400 cases, and direct explainers reach 0.74–0.91 of what their resolution allows (KernelSHAP
over windows 1.08). Per file, overlap adds little beyond file size (dropped). Hence claim 3 as reworded (option A).

**PF2. Ground truth for feature-space explainers** (built; shares the testbed with PB2). **Demoted (2026-10-09):**
kept for now, possibly removed later; its ground truth, the support of r, is nearly recoverable without P (the
features whose value the trigger changes), so it does not by itself show the pushforward is useful.

**Reading (decided 2026-10-09): r is a support, not a target.** The pushforward of the trigger's bytes, r = ψ(1_T),
weights each feature by how much of it the trigger computes, a property of P alone; it cannot say which of those
features the model uses. Its support, the features the trigger touches, is model-independent ground truth: a faithful
explanation of the trigger's effect must concentrate there. Primary metrics: mass on supp(r) and top-k in supp(r);
cosine and Spearman against r's weights are dropped as faithfulness scores (they describe P). Caveat: even an ideal
Shapley explainer of a tree model puts some credit on untouched features (interaction credit, about 30% for struct),
so mass on supp(r) is recall-like with an ideal value below 1: it ranks explainers against each other and random,
not on an absolute scale. Optional refinement: the support as the features whose value actually changed.

Results (`docs/experiments/trigger.md`). **Struct** (12 touched features, 50 files): top-1 in supp(r) 50/50 for every
explainer; mass on supp(r) 0.70 (both TreeSHAP variants) and 0.50 (KernelSHAP) against 0.005 random. **Content**
(317 touched features): top-1 50/50; mass 0.67 / 0.51 against 0.12 random. **This is the pushforward turning
problem-space knowledge into an evaluation of feature-space explainers, which otherwise have no ground truth.**
KernelSHAP needs its full 32,768 coalitions; at 512 it appears to miss the trigger entirely.

### 4. Application: comparing classifiers (CM; now CM, `docs/experiments/cm.md`)

Superseded by CM ("Paper structure"): the problem-space comparison is the pullback's application, done at pilot
scale (runs 30-33; `docs/experiments/cm.md`) and written up in `manuscript/_d_applications.tex`. The feature-space
comparison (MalConv's explanations pushed forward vs. the GBDT's TreeSHAP) is in the appendix as a curiosity, not
built.

### Second classifier: the MLP (after the GBDT methodology is established)

Apply the established methodology to the MLP and find the recipe that makes it work. The pilot's diagnosis is the
starting point: the black-box pullback of the MLP's explanations trails occlusion as far as the instrumented one, so P
transfers them correctly and the explanations are the weak link (`docs/experiments/pb1.md`, reading 5). Candidate steps, in
order: a feature-space deletion check (are IG and KernelSHAP faithful to the MLP in the feature space at all? PF1's
test can be reused); then, depending on the answer, a better explainer (e.g., DeepLIFT/DeepSHAP) or a reference
matched to the perturbation operator. Matching the reference to the operator changes what PB1 claims; decide with the
user before adopting it.

### Appendix

- **App-L. Localizability:** the share of attribution that the pullback sends to the null element, split into
  file-dependent absences and never-attributable features, per explainer. Done at 2,000 files (`docs/appendix.md`).
  A stated limitation of the provenance pipeline only, not a finding or a contribution (2026-10-09).
- **App-R. Mechanical redundancy:** a short proposition (features with identical provenance merge after pullback) and
  Mohseni et al.'s duplicate-feature sweep; agreement of explainers before and after pullback, net of a permutation
  control (`scripts/pullback_agreement.py`; no general agreement gain, `docs/appendix.md`). The duplicate-feature
  sweep is not yet run.

## Explainers

TreeSHAP (path and interventional) and KernelSHAP for the GBDT; MalConv IG and occlusion for CM. For the MLP (later):
IG (background-mean baseline) and KernelSHAP, plus whatever the second-classifier step finds necessary. Gradient ×
input is kept for now but cannot credit absence (zero baseline); drop it unless it earns its place. The choice of XAI
methods may be revisited.

## Modest theory (each result short, correct, and useful)

- **T1 Structural = Shapley provenance for additive groups.** For σ additive in element contributions (histograms,
  counts), instrumented provenance equals the Shapley-of-σ provenance. For non-additive groups (entropy windows,
  hashing), the gap is measured empirically against the black-box estimate (PB1, CP).
- **T2 Composition.** P_{σ2∘σ1} = P1·P2 is valid provenance, so pullback composes; pushforward (with D†) does not in
  general.
- **T3 Coarsening** (manuscript, Proposition Coarsening, 2026-10-08). Grouping elements into sets (e.g., windows)
  commutes with pullback, never raises ambiguity, and never lowers overlap.
- **Mechanical redundancy (App-R).** Features with identical provenance columns are indistinguishable after pullback.
- **Possible strengthening (noted 2026-10-09, not pursued now):** an axiomatic characterization in the style of
  Shapley's uniqueness theorem: show that the pullback is the only transfer satisfying a short list of properties
  (e.g., linearity in the explanation, conservation of the total, zero credit to elements no feature reads, and
  agreement with the Shapley value of σ for additive features, T1), and ask the same for the pushforward. This would
  answer "it is just the rescale rule" with "it is the only rule with these properties". Unknown whether it is
  provable cleanly.
- **Round trips (2026-10-08).** M = PᵀD†P is symmetric and doubly stochastic with M_jj = 1 − O_j; the cyclic errors
  are bounded by 2 Σ_j |a_j| O_j and 2 Σ_i |b_i| (1 − N_ii), with equality for one-hot inputs. The
  perfect-reconstruction theorems (pull-push iff O = 0, push-pull iff H = 0) are its corollaries. Every theorem is
  checked numerically with property-based tests.

## Open questions

- ~~**Summary statistics**~~ decided 2026-10-08: the names stay; ambiguity = mean entropy (effective support
  exp(H_j)), overlap = O_j = 1 − M_jj (`docs/experiments/cp.md`).
- ~~Localizability ℓ~~ decided 2026-10-07: removed from the framework (it is explanation-specific); coverage κ stays.
  The null element's entry of a pullback is the attribution that cannot be localized. ℓ and other
  explanation-weighted quantities remain evaluation metrics (CP, App-L).
- **Ambiguity and overlap (2026-10-09):** the round-trip matrices M and N stay in the framework as theory (their
  diagonals are 1 − O_j and N_ii), hopefully with a practical use later. The standalone statistics have no
  demonstrated use: overlap's only one is PF1's resolution trend, which largely restates the round-trip bound (any
  statistic of P "predicting" a transfer that is linear in P is close to a tautology; a real use connects P to
  something not computed through P, such as model or attack behavior). Undecided what to do with them.
- **Further pushforward applications** (for later brainstorming): translating explanations between feature sets
  (pull back through one extractor's P, push forward through another's), once CM has a second extractor.
- **A further feature set (on hold, 2026-10-09; not EMBER v2, too similar to v3).** For A, **byte n-grams for PE**
  are the quickest way to widen the comparison (user); another domain or file format comes later. Candidates: within
  PE, byte n-grams (a very different P: high resolution, low overlap) or disassembly-based opcode n-grams (a more complex
  extractor); across domains, which would also answer "Generality", DREBIN-style Android features or flow features
  from packets (CICFlowMeter-style statistics).
- **Signed provenance:** rescale-rule matrices can be signed; our axioms require P ≥ 0. Keep structural (unsigned)
  provenance plus a stated limitation unless PB1 shows a need.
- **Naming** ("provenance" vs. "attribution lineage").
- **Generality (raised 2026-10-09):** the framework claims domain-agnosticism but is evaluated on one feature
  extractor (EMBER v3). A reviewer may ask for a second extractor or domain; a stated limitation for now, revisit
  after CM.
- **Scope of the cost claim (2026-10-09):** "one extraction instead of hundreds" ignores the explainer's own cost; it
  holds for explainers cheap in the feature space (TreeSHAP: milliseconds), not for KernelSHAP (about 45 s per
  file, more than occlusion at 256 windows). State it that way.
- **CM against real attacks (noted 2026-10-12, user; for the future):** CM's "shared attack surface" rests on
  deletion. Whether a published functionality-preserving header attack on MalConv transfers to the GBDT more often
  when the bytes it modifies carry the GBDT's pullback would tie it to attacks (days of tooling, e.g.,
  secml-malware). Until then, a stated limitation (`docs/experiments/cm.md`, "Caveats").
- **At scale:** bootstrap confidence intervals for the headline numbers; seeds 0–2.

## Data, models, compute

- **Scope:** EMBER-2024 PE files and EMBER feature version 3 only, truncated to the first 4,000,000 bytes; all
  features recomputed on the truncated files so that σ, P, and the model see the same object.
- **Models:** GBDT (LightGBM, EMBER baseline parameters with the categorical features treated as numeric, because shap
  misencodes LightGBM categorical splits) and MLP, seeds 0–2; MalConv medium, seeds 0–2 (for CM). Seed 0 for all
  explanation work; seeds 1–2 for robustness. Experiments use the GBDT first; the MLP is trained and returns later
  (see "Model scope").
- **Explanation set:** 2,000 test files (1,000 per label, TLSH-deduplicated, at most 10 per malware family).
- **Compute:** ample CPUs and GPUs, so direct problem-space baselines are feasible at scale.

## Timeline and gates

Phases 0–2 are complete (literature; `provexp`; features, models, stage-1 explanations, census). As of 2026-10-12:
**the intrinsic evaluation is done at pilot scale (CP's theory, PB1, PF1; PB2/PF2 demoted); CM is done at pilot
scale and written up; AU is done and written up; 3-B and the earlier rule-based audit are dropped.** The dates below
were set before the restructuring. Most of
the research runs at pilot scale; scaling up is for the final numbers, when the pilot results and claims are settled.
`run/` holds the commands that produced everything in `artifacts/`.

| Dates | Work | Gate |
|---|---|---|
| Oct 8 | ~~PB1 baselines~~, ~~the trigger testbed~~ done; the runner's parallelism rebuilt | **Gate 2** (passed for the GBDT) |
| Oct 9 | ~~PB2/PF2 at pilot scale~~, ~~PF1 and its resolution trend~~, ~~CP.3~~; the tie-break fix (PB1 re-run pending) | |
| Oct 9 (later) | ~~Run 21 read~~; **paper restructured**; ~~3-B identify spurious correlations~~ (runs 22, 24) | |
| Oct 12 | ~~3-B consolidated~~ (runs 26-28: transplant, reliance, mitigation); baseline run 25 (done) | |
| Oct 12 (later) | 3-B dropped; ~~CM at pilot scale~~ (runs 30-32: cross-deletion, shared attack surface, triage) | |
| Oct 12 (later) | ~~CM's window-level triage~~ (run 33); ~~CM written up~~ (`docs/experiments/cm.md`, the manuscript) | |
| Oct 12 (later) | Rule-based audit: design, runs 34-37 (generic YARA rules); **dropped**, failed the sniff test (not the pushforward) | |
| Oct 12 (end) | Step back; AU (auditing MalConv via the pushforward): mock, go/no-go built; runs 38-41 started | |
| Oct 13 | AU: no-go on forging, post-mortem (run 42), reframed to scrambling; go (runs 43-44); experiment proper (runs 45-46); written up; Appendix F removed; repo reorganized | |
| Oct 13 (later) | Introduction rewritten (framework+symmetry, contributions C1-C4); local TeX Live toolchain set up to match Overleaf | |
| Oct 13 (evening) | Manuscript in paper form: all sections drafted; CP and theory cut (archived); "framework" -> "method"; organized by operator (pullback: lab then CM; pushforward: lab then AU); Background and Related Work as Section 2; per-application threat models | |
| Oct 13 (night) | AU corrected: held-out, detected-only, loader-realizable evasion with paired tests and a broad null (runs 47-49); string features 2.1x faster; seed-0 scale-up to 500 files prepared (`run/50`-`55`) | |
| Oct 14-15 | **User runs `run/50`-`55`** (~20-24 h); then compare with the pilot, update the experiment docs and the manuscript's numbers | with the user |
| then | Section-level writing (the user reads the restructured draft); AU mitigation written as a TODO | with the user |
| later | Cluster round: 3 seeds, 10K files (after the deferred optimizations in `docs/design.md`); AU mitigation (1c) if taken up; real-attack transfer (1d) probably not | with the user |
| later | Appendix (App-R; the byte-set control bound) | |
| Dec 15–mid Jan | Writing: introduction and contributions, framework edits, figures | Submission (CCS '27 Cycle A, est. abstract ~Jan 7, paper ~Jan 14) |

Gate 1 (the pilot census, in git history) passed provisionally for the measurement result (now App-L).
Gate 2 (the PB1 pilot, `docs/experiments/pb1.md`, 2026-10-08): passed for the GBDT (window-level parity with occlusion under
level-2 and level-3 operators, byte-level advantage 1.65–1.79×). The MLP did not reach occlusion (the explanations, not
P, are the bottleneck); it is set aside temporarily and returns after the GBDT methodology is established. Insertion
was dropped as a flawed test. Thresholds are reassessed with the user.

## Risks

- **The core claim fails (Gate 2):** pullbacks are not more faithful than random, e.g., because most attribution
  rests on absence or on features that smear over the whole file. Mitigation: the gate is early; per-subset results
  may still support a narrower claim; fallback venue.
- **Perturbations go off-manifold:** zero/random edits break parsing and distort faithfulness. Mitigation: report
  parse-failure rates; move to a PE-aware operator.
- **Smearing:** histogram and entropy features spread over the whole file, which limits how sharply the pullback
  can place their credit. A stated limitation of the transfer at fine resolution (CP's round-trip bounds).
- **The extrinsic applications carry the paper's security relevance.** CM is done at pilot scale (one seed; its
  "attack surface" rests on deletion, not on attacks); AU (auditing MalConv via the pushforward) is done and is the
  pushforward's application; 3-B and the earlier rule-based audit are dropped. Residual risk for AU: the surrogate is
  strong (R^2 0.95) and finds comparable reliance, and much of MalConv's pushed-forward credit falls on aggregates
  (entropy, histogram) below the pushforward's resolution.
- **Reviewer pool:** Raff co-authored EMBER-2024, MalConv, and the SHAP-on-EMBER critique; engage it directly (App-R,
  CM).
- **The pushforward is faithful only up to its source's resolution (PF1):** window-level explanations keep a third of
  TreeSHAP's feature-space faithfulness. Claim 3 is stated that way (option A); AU's global comparison rests
  on MalConv's byte-level explanations, which the resolution trend puts near R ≈ 0.8 at best.
- **Timeline:** if needed, App-R shrinks first.
