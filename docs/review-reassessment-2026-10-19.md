# REVIEW.md, reassessed against the revised manuscript and plan (2026-10-19)

The simulated CCS review (`REVIEW.md`, 2026-10-16) was written against the old manuscript (one section per operator,
the field oracle, the trigger, the black-box P). Since then: Sections 5-6 reorganized; oracle, trigger, black-box P and
the naive translation cut; one byte-deletion measurement and one cost unit; adaptive KernelSHAP; a shared Section 6
setting; 6.1 gains attack transfer and adjudication; 6.2 gains the localized audit (`docs/experiments/specs.md`,
`docs/implementation-plan-2026-10-19.md`, manuscript commit fd814be). This note asks two questions: is the planned work
worth doing, and what cheap wins are left?

## 1. The review's weaknesses, one by one

| REVIEW item | What it said | Status now | Planned work | Worth it? |
|---|---|---|---|---|
| W1 audit only where the pushforward is trivial | header fields only; = IG summed per field | Partly addressed by design | WP7: drop the contiguity requirement (keep aggregates out), confirm section, import, string features | **Yes, essential.** The only experiment where the pushforward's splitting of shared bytes matters. |
| W2 theory decorative / inconsistent | Prop. 2 never tested; Influence axiom "iff" contradicted | **Open**; one strength lost (see 3.1) | none | Cheap fixes exist (Section 2 below). |
| W3 triage: no security outcome, no attacker | deletion only; attacker never acts | Addressed by design | WP4-WP6: attack transfer, adjudication | **Yes, highest value.** Turns 6.1 from descriptive to measured. |
| W4 "byte resolution" may be field-level information | the oracle comparison | Claim removed with the oracle | WP1: adaptive KernelSHAP is the in-class test of the same objection | **Yes.** Falsifiable: if adaptive KernelSHAP approaches the pullback, the byte-resolution claim weakens, and we want to know now. |
| W5 MalConv test circular, surrogate weak | pushforward uses MalConv's gradients | Addressed by design | WP3: gradient-free sources (occlusion, KernelSHAP) pushed forward on MalConv | **Yes.** If they beat the surrogate too, the circularity objection is answered. |
| W6 pushforward "trigger" did not test the pushforward | | Resolved (cut) | none | — |
| W7 one extractor | generality claims | **Open** | Phase 5 decision (week 5) | Unchanged; the largest remaining item. |
| W8 narrow attacker, mitigation not tested adaptively | | Attacker now stated in the setting; mitigation still untested against a strong attack | Deferred | **Low-hanging** once WP4 exists (Section 2, item 6). |
| W9 positioning (Aryal, TRUSTEE, MAB-Malware, FINER/Severi/Mohammed/Mink wording) | | TRUSTEE now cited; the rest open | none | Cheap (Section 2, item 7). |
| W10 trust in P unstated | | **Resolved** (setting states the trusted parse) | — | — |
| Synthetic results (desk-reject risk) | Android, retraining | **Worse in count**: new blue placeholders in 5.1, 5.2, 6.1, 6.2, Figure 4 | Real runs replace them | Keep the `grep synthetic` gate; every placeholder is tied to a WP. |
| Claim audit #13, #15, #16, #19-#22 | overclaims, inconsistent mitigation numbers | Open (front matter) | front-matter rewrite last | Some body sentences are cheap now (Section 2, item 2). |

**Verdict.** Every planned work package answers a named review risk, and none is merely interesting: WP1 (W4, in
class), WP3 (W5), WP4-WP6 (W3), WP7 (W1). WP2 is needed for consistency with what the manuscript now claims. Nothing
in the plan should be dropped. The two items with real downside risk, which we want to learn about early, are WP1
(adaptive KernelSHAP might close the gap) and WP4's gate (the GBDT might not move).

## 2. Low-hanging fruit (hours each, mostly no new runs)

1. **Fix the Influence axiom and the φ clash (writing, 1 h).** Definition 3 states "P_ij > 0 iff z_i influences x_j",
   and Section 3.3 later redefines it ("belongs to an item x_j is computed from"), with pointers and sizes as context
   that gets no share. State the item-based version in the definition. Rename the classifier (f, as Section 4 already
   writes f(x)) so that φ is only the Shapley value.
2. **Trim three overclaims in the body (writing, 1 h).** "To our knowledge, no prior work transfers [in this
   direction]" (`_b2`, l. 131) and "two tasks that output-level comparisons and per-file saliency cannot perform"
   (l. 136): summing saliency over parsed regions is a transfer in this direction; say "into features that share
   elements, conserving attribution". Contribution 1's "what any transfer can recover": "of a pulled-back explanation".
3. **Measure how much of the evaluation the theory covers (existing data, ~2 h).** The share of the GBDT's attribution
   on additive (Shapley-exact) columns versus data-flow columns, from the saved explanations and P. One sentence in 4.1;
   it tells a reviewer how far Proposition 1 reaches.
4. **Worst-case cost and the size of P (existing data or a short run, ~2 h).** Extraction time and P's nonzeros at the
   95th percentile and at the 4 MB truncation, next to the median's 0.15 s.
5. **Pre-check adjudication on the pilot files (existing data, minutes).** The 50 GBDT-only files of Table 3 already
   have scores and triage shares. A cross-validated logistic regression, scores against scores plus shares, shows
   before WP6 whether the triage adds anything beyond the scores, which is Part B's main risk. Too small to report;
   enough to decide whether WP6 is worth its run.
6. **Commit to the stronger attacker on the mitigated MalConv.** Once WP4's attack exists, running it with the audited
   fields zeroed is one flag. It answers W8 directly. The likely result (the DOS/stub/slack attack still evades,
   because it uses other bytes) supports the paper's framing that the mitigation targets the audited reliance, not
   MalConv's whole evasion surface; better stated by us than by a reviewer.
7. **Related-work fixes (writing, ~1 day with source checks).** Engage Aryal et al. (region-level local and global
   SHAP on MalConv, used for evasion) as the closest prior to the audit; cite MAB-Malware's action minimization as a
   defender-side alternative; check the characterizations of FINER, Severi et al. ("17 features"), Mohammed and Zhang,
   and Mink et al. against the sources.
8. **Part A design tweak (no cost).** A reviewer will ask whether the pullback's prediction is just "the file has a Rich
   header" or "the editable region is large". Add both as covariates of a baseline predictor, or stratify by them.

## 3. New issues the revision introduced

1. **The identifiability evidence left the paper.** Under byte deletion, features with identical provenance are deleted
   together, so the measurement cannot see what the pushforward loses there; the old feature-space result (R 0.80 one
   step, 0.86 exact, 0.95 with the twins' split restored) was the paper's one experiment that a theorem predicted, which
   the review counted as a strength (S6). Options: (a) report it as an illustration of Proposition 3 in Section 3 (the
   numbers exist), accepting a second measurement in one place, justified because the claim is about feature space;
   (b) leave it out. Recommendation: (a), two sentences.
2. **Figure 4 shows old-protocol data under a new caption** (marked as a placeholder). Regenerate in WP8.
3. **Section 6.1 is now long** (four questions, two new tables). Expected to tighten once results are in; noted for
   the page budget, not acted on (user: page limit not a concern yet).
4. **The adjudication sample is small for a 99%-recall operating point** (100 malware): the threshold is set by about
   one file. Report AUC as the primary number at pilot scale and the operating point at scale.

## 4. Suggested order

Items 1, 2, 8 and the 3.1 decision are writing and design; items 3, 4, and 5 are short analyses of existing data
(minutes to hours, no long runs); then WP0. Item 6 waits for WP4; item 7 can run any time.
