# Review A

**Paper:** "Bridging the Gap: A Closer Look at Adversarial Examples in the Problem Space" (title is a placeholder)
**Reviewer:** A (formal methods / PL: abstract interpretation, incremental computation and IVM, provenance)

---

## 1. Summary

The paper treats a static feature extractor as a three-stage composition φ = ρ ∘ σ ∘ π (Eq. 1, p. 2). An *item map* π turns a file into a multiset of typed items. A *fold* σ adds up each item's contribution into commutative-monoid "sums": additive reals, max pools and min pools. *Readouts* ρ_j compute each feature from a fixed support of sums. On this structure the paper proves three results:

- **Proposition 1 (p. 4).** Given the multiset of items an edit removes and adds (its *delta*), plus a recorded "item table" of the original file, the new features follow exactly. This is the standard delta rule for distributive aggregates. Pools are recomputed from the kept items because max/min have no inverse.
- **Theorem 1 (p. 5).** A *signature* says, for each item kind, which add/remove/replace changes a threat model can make. From it, a sign abstraction over the change (fixed/up/down/both), pushed through per-readout transfer rules (Table 1), gives a direction table that is sound for every edit in the threat model. It stays sound for sequences of edits when the population is closed under the edits.
- **Corollary 1 (p. 5).** A score that is monotone with respect to a sound table cannot be lowered by any reachable edit. This is Gimenez et al.'s Proposition 1, which the paper acknowledges in Appendix C.

The paper instantiates the framework for EMBER-v3 (2,480 of 2,568 features; the 88 parser warnings are dropped) and a twelve-operation PE threat model in three nested levels (Table 2). It defines a population of "complete, plain-layout" PE files (Section 4.4). The evaluation makes four points:

- An authors' hand-written direction table and Gimenez et al.'s 40-feature expert set both get directions wrong (Table 3, Section 5.2).
- Defenses learned from toolkit-attack outputs (PV, ERDALT, adversarial training) trust features that edits outside those attacks can lower (Section 5.3, Table 4).
- A monotone GBDT built from the derived table, on features or on the underlying sums, costs about 4–6 points of TPR at 1% FPR relative to an unconstrained model, versus about 65 points for the hand-picked expert set (Section 5.4, Table 5).
- Computed side effects match re-extraction on every edit the instance does not decline (Table 9).

The paper is easy to summarize, which is to its credit. A summary does have to separate two things, though: what is *proven* (Section 3, an algebraic skeleton) and what makes the EMBER guarantee *true* (Sections 4.3.2, 4.4 and Appendix D). The second part rests on parser behaviour that is checked on samples and by fuzzing, not proven. Section 7 and the introduction must make this split visible.

## 2. Strengths

- **S1. A clear, reusable decomposition with an honest statement of what is not proven.** Section 4.3.2 (p. 7) says outright that the overwrite part of the signature "rests on the sample rather than on a proof". Section 4.4 says that closure "is checked rather than proven". Both statements are correct and rare in this literature. I verified them against the text.
- **S2. The security findings are concrete and actionable, and each is checked by re-extraction rather than by the model.**
  - The overlay/added-section interaction and the Rich-header search range (Table 3, p. 8) are real parser facts that a hand analysis misses.
  - Section renaming defeats PV (4/9 evaded with one edit, p. 9).
  - 11 of the 40 expert-set features in Gimenez et al. can be lowered without source code. Gimenez et al. describe that set as "difficult to change for an attacker with no access to the malware source code" (verified in `papers/gimenez2025certifiably.pdf`, p. 4), so the criticism uses their own criterion.
- **S3. The cost analysis is the paper's most valuable result for practitioners.** A provably monotone EMBER detector loses about 4 points of TPR at 1% FPR (Table 5). Gimenez et al.'s certified-by-design detector detects 29% under additions; this one detects 92%. The ablation by operation ("Where the cost lies", p. 10) attributes the cost to import addition and the header overwrites. That tells a defender which threat-model choices are expensive.
- **S4. Re-encoding over sums (Appendix D, p. 15) is a simple, useful observation.** Normalized histograms move both ways only because of the readout, so a detector that reads the raw counts keeps one-sided directions.
- **S5. The validation protocol is sound in design.** Trial is the ground truth, every evasion is decided by writing the file and re-running EMBER, and declined edits are counted separately (Table 9).

## 3. Weaknesses (ranked by severity)

### A-W1. The proven core is not where the guarantee comes from. The class is universal, and Theorem 1's precision and the EMBER soundness rest on an unformalized, empirically checked locality property of π.
*Location:* Definitions 1–5 (pp. 2–3), Theorem 1 (p. 5), Section 4.3.2 (p. 7), Appendix D "Positions that locate items" (p. 15).

*Problem.* Definitions 1–5 put no restriction on π. Any feature mapping φ is therefore a sum-then-readout extractor:
- take a single item kind whose members are all positions of z (so its content is z),
- let it contribute φ_j(z) to an additive sum k_j,
- read each feature through the identity.

This satisfies Definitions 1–5 as written (I verified this against the definitions). So the claim that the results hold "for a broad class of feature mappings" (p. 2) is vacuous as a class statement. Under that trivial instrumentation, every edit replaces the one item with arbitrary content, and Theorem 1 returns *both* for every feature: sound, but useless.

The informative content of Theorem 1 therefore depends entirely on item granularity and on one property that Section 3 never states. That property: an edit writing positions W changes only items whose members intersect W, or whose *locating positions* intersect W. The paper relies on this property in Section 4.3.2 and Appendix D, but establishes it only by:
- deriving the signature for overwrites from the item tables of a sample (100 files vs. 2,000, p. 7); and
- completing the record of locating positions with 58,666 single-byte changes, after a first round had already missed three parser rules (p. 15).

*Why it matters.* The headline claim, "monotone detectors that no edit in the threat model can evade", holds on EMBER only if:
- (a) the signature covers M over Z,
- (b) Z is closed under M,
- (c) the recorded locating positions are complete, and
- (d) the instrumentation equals the extractor.

All four are tested, not proven. Two specific gaps:
- Single-byte perturbation cannot reveal parser dependencies that only multi-byte patterns trigger, such as magic values and signatures like the "Rich"/"DanS" markers or the "MZ"/"PE\0\0" checks. This is inferred from the stated methodology.
- A sample of 100–2,000 EMBER files will not contain rare layouts (sectionless files, unusual directory combinations, .NET or TLS edge cases). For those layouts the overwrite signature is unverified.

*Fix.*
- (i) Add the locality property to Section 3 as an explicit hypothesis: each item has a set of locating positions L(ι), and edits that write outside ∪L change only items whose members they write. Prove the signature-coverage lemma from it, so that Theorem 1's EMBER instance reads "sound, given (a)–(d)".
- (ii) Obtain L soundly from the parser rather than by sampling, for example by dynamic taint or dependency tracking from file bytes to the control decisions that discover items. This is dependency provenance in the sense of Cheney–Ahmed–Acar, and the paper already invokes provenance in Section 6.
- (iii) Failing (ii), stress-test (a)–(c) on adversarially generated PE files (structure-aware fuzzing), not only on EMBER samples.
- (iv) Restate the contribution as "for extractors whose item map is local in this sense". That is a meaningful class, and the paper should describe it.

*Status:* verified (definitions, Sections 4.3.2 and 4.4, Appendix D); the multi-byte gap is inferred.

### A-W2. The formal results are known techniques, and Section 6 does not position them against their actual precedents.
*Location:* Proposition 1 (p. 4), Theorem 1 and Table 1 (p. 5), Appendix C, Section 6 "Incremental computation and provenance" (pp. 11–12).

*Problem.*
- **Proposition 1** is the textbook delta rule for distributive aggregates plus the textbook observation that MAX/MIN are not self-maintainable under deletions. The paper says as much for part (i) ("part (i) is its rule for totals", p. 4). Two refinements are missing:
  - The relevant notion for pools is *self-maintainability* (Mumick, Quass, Mumick, SIGMOD 1997), not Gray et al.'s distributivity. MAX is distributive, yet it needs the base multiset under deletion. The text on p. 3 blurs this.
  - Maintaining MAX from the kept multiset is studied directly by Palpanas et al. (VLDB 2002).
- **Theorem 1** is a sign abstraction of the *change*. The domain {fixed, up, down, both} is the sign lattice of Δx (without ⊥). The rules in Table 1 are its abstract transformers; the ratio rule is the usual sign rule for a quotient's difference. The induction over sequences is the standard argument that the abstraction of a sum is closed under addition. The paper never mentions abstract interpretation, monotonicity analysis or change/derivative calculi (Cai et al.'s incremental λ-calculus, PLDI 2014; change actions). A PL reader will recognize the result immediately.
- **Corollary 1** is Gimenez et al.'s Proposition 1, as Appendix C states.
- Section 6 claims two differences from IVM and incremental parsing:
  - The first is that "it finds the items that an edit of raw elements changes". Incremental parsing (Wagner and Graham, cited as [31]) does exactly this: it maps edits of raw text to the affected parse nodes.
  - The second is that it bounds "every edit of a declared set". That is the defining move of abstract interpretation.

*Why it matters.* Contribution claims in the missing introduction must not present Section 3 as a new theory. As written, a reader could take "Measuring Edits Across Feature Mappings" as the contribution. In my judgement the contribution is:
- the observation that production extractors like EMBER admit a fine-grained fold/readout instrumentation;
- the engineering that recovers deltas and signatures from the parser; and
- the security consequences.

*Fix.*
- Recast Section 3 as "we apply standard incremental-aggregate and sign-abstraction reasoning", with citations to self-maintainable aggregates, abstract interpretation (Cousot and Cousot 1977) and change calculi.
- Shorten the proofs accordingly.
- Move the claimed novelty to A-W1's locality property and to the instance.
- Remove the Section 6 claim of difference from incremental parsing, or make it precise. If there is a real difference, it is the adversarial universal quantification over content, and that is abstraction.

*Status:* verified against the paper's own text and Section 6; the prior work is from my own expertise.

### A-W3. Theorem 1 is stated more generally than it is proven, and its side conditions are dropped from Definition 10. One EMBER readout appears to violate the "monotone" rule's hypothesis.
*Location:* Definition 2 (p. 2) and the text after Eq. (4); Definition 9 and Table 1 (p. 5); Definition 10 (p. 5); Appendix C, "Directions of sums" (p. 13) and Table 7; Table 8 (p. 15).

*Problem.*
1. **Theorem 1 claims a general result but proves it for three monoids.** Definition 2 allows "any commutative monoid", and Theorem 1 is stated for "a sum-then-readout extractor". Definition 9 compares ν_τ(c′)_k > ν_τ(c)_k, which presupposes a *total order* on M_k. The proof uses that "addition, the maximum, and the minimum are nondecreasing in each argument" (p. 13). So the theorem is proven for totally ordered commutative monoids whose operation is monotone, and the text (p. 3) concedes that other monoids would "need a rule". The statement should carry that hypothesis.
2. **The ratio rule's side condition is not carried into the derived table.** Table 1's ratio rule requires a ≥ 0 and b > 0 before *and after* the edit. Definition 10 applies the rule unconditionally, and Theorem 1 does not carry the condition, so the theorem as stated is false when b can reach 0 or a is a pool at ±∞. Example: d_a = up and d_b = down, with b driven to 0 and EMBER's default readout of 0.
3. **The smallest-section-entropy readout is not nondecreasing.** Table 8 classifies "largest and smallest section entropy" as *monotone* readouts and notes that EMBER reads pools "as 0 for a file without sections". For the min pool, the readout is g(+∞) = 0 and g(x) = x. This g is **not** nondecreasing, because g(+∞) = 0 < g(x) for any x > 0.
   - Adding the first section to a sectionless file therefore lowers the min pool (d = down by Table 7), yet the feature rises from 0 to the section's entropy.
   - The derived table would say *down* for that feature under "add a section"; the true change is +.
   - The same applies to the "smallest section size over file size" ratio, whose numerator is +∞ on such files.
   - Unless sectionless files are excluded from the population (Section 4.4 does not say so), this is a soundness hole in the instance.
   - The 2,000-file empirical check would not catch it if no sampled file was sectionless.

*Why it matters.* This is the kind of corner case that a "sound" claim must survive. The empirical check cannot detect bugs in rare layouts, which is why the proof has to be right at the generality it claims.

*Fix.*
- State Theorem 1 for totally ordered commutative monoids with monotone operation.
- Make the readout rules conditional, and have Definition 10 fall back to *both* where the side conditions are not guaranteed over Z.
- Give each EMBER readout its exact form, defaults included, and verify the rule on the default branch. Either exclude sectionless files from Z or classify the min-pool readouts as "any other".
- Report how many training/test files have zero sections, zero strings, and so on.

*Status:* points 1–2 verified against the text; point 3 inferred from Table 8 and the stated default (I cannot see the code).

### A-W4. The deployed system's guarantee is weaker than the corollary suggests: fallback routing, excluded large files, and an M that real tools exceed.
*Location:* Section 4.4 (p. 7), Section 5.4 "Where the guarantee holds" and "Beyond the guarantee" (p. 10), Section 5.1 (p. 7), note to reviewers.

*Problem.*
1. **Fallback routing.** Files outside Z go to an *unconstrained* detector with no guarantee, and that is exactly where each monotone detector's one toolkit evasion happened (p. 10). The paper argues that out-of-population files "are rare among benign software, and so stand out". However, 1.5% of benign test files are outside Z (p. 10), which already exceeds the 1% FPR budget. Rejecting every out-of-population file is therefore not available at the reported operating points (verified arithmetic). Malware authors who control the build, as distinct from post-hoc editors, can ship out-of-population binaries from the start.
2. **The population share is unmeasured.** The 89% share of attacked malware inside Z is a placeholder. The earlier run's training malware was only 314/400 = 78.5% in Z (p. 9), which suggests the final value may be lower. If the share is substantially lower, the claim survives formally, but the protected fraction of malware shrinks and the end-to-end system becomes evadable on more of it.
3. **The 4 MB cutoff.** It excludes 26% of the malicious test files (p. 7). Large files are where padding and overlay attacks live. The theory does not depend on size, but closure, signature coverage, detection and the FPR threshold are all validated only below 4 MB.
4. **M excludes what real tools do.**
   - GAMMA's LIEF rebuild moves features that the table holds *fixed* (36/288 outputs, mostly the resource directory size, p. 10).
   - Packing and code-level transformations are excluded (Section 4.3.1).
   - The monotone detectors survived the rebuild attacks empirically, but the guarantee does not cover the off-the-shelf tools the paper evaluates against.

*Why it matters.* For acceptance, the paper must claim what the *system* guarantees, not only what Corollary 1 guarantees on Z.

*Fix.*
- Report end-to-end evasion of the routed system (gate + monotone + fallback) under an attacker who may first move the file out of Z by any means.
- Report the fraction of all malware, large files included, that receives the guarantee.
- Evaluate an alternative fallback: the monotone detector itself, or flag-and-review at a stated FPR cost.
- Add a "rebuild" operation to M (its declared changes are derivable the same way), or state plainly that tool-based edits are out of scope.

*Status:* verified, except the inference about the 89% value.

### A-W5. The headline claim "exact … before the edit is applied" overstates Proposition 1. Declines are frequent, and they weaken the adaptive attack used as evidence.
*Location:* Section 3.2 (p. 4), Table 9 (p. 15), Section 5.1 (p. 7), Appendix D "The adaptive attack" (p. 16).

*Problem.* Proposition 1 is exact *given* the delta, and computing the delta for scanned items (strings, entropy windows) means re-scanning the written region and its neighbourhood: a local re-extraction. The instance also declines many edits:
- 5,739 of 7,428 DOS-header/stub overwrites (77%);
- 867 of 6,000 appends;
- all edits of the "loader-ignored header fields" operation.

The adaptive attack "skips them" (p. 7). The adaptive attack against the unconstrained, hand-table, PV and expert-set detectors therefore does not explore the declined part of the threat model. Those detectors' "evaded" counts are lower bounds, which is fine. The statement that the adaptive attack "confirms the guarantee" on the monotone detectors is vacuous: the score cannot drop by construction, so a zero drop is an implementation check, not evidence.

*Fix.*
- Rephrase the claim as "exact given the delta, which the instance computes for X% of edits by local re-scan".
- Let the adaptive attack fall back to real extraction for declined edits, so that the attack covers the full M.
- Present the monotone-detector attack results as a sanity check of the implementation, not as confirmation.

*Status:* verified against Table 9 and Sections 5.1 and 5.4.

### A-W6. Statistical design of the comparisons; the authors' own hand table as a baseline.
*Location:* Section 5.1, Tables 3–5, Table 10.

*Problem.*
- Single seed, 10% subsamples, and attacks on 50 malware. Several counts are on 8–9 detected files: PV 4/9, expert set 2/8, Table 10.
- At 0.1% FPR the threshold rests on a handful of benign files; the paper concedes "a few points" of retraining noise (p. 10).
- The headline cost (3.9 points at 1% FPR) is of the same order as that noise.
- The "hand table" in Section 5.2 was written by the authors. This is better than nothing, but it is not an independent analyst.

The large effects survive plausible shifts: PV at 26% vs. 87%, the expert set at 29% vs. 92%, and the qualitative failures of PV and ERDALT. The cost figure and the per-operation attribution may not.

*Fix.*
- Use full scale with ≥5 seeds and report confidence intervals for TPR at both FPRs.
- Report the operation ablation with intervals.
- If possible, have one or more independent analysts write hand tables blind.
- For ERDALT, run the authors' released artifact as well as the reimplementation (one change from the released code is stated in Appendix D). This rules out reimplementation effects in the 24/29 result.

*Status:* verified (protocol as stated); the robustness judgement is mine.

### A-W7. Missing comparison with certified malware defenses and with verifying existing tree models on the derived region.
*Location:* Section 6.

*Problem.*
- The paper does not cite or compare with certified defenses for malware detectors:
  - RS-Del (Huang et al. 2023, in `papers/`);
  - DRSM (Saha et al. 2024, in `papers/`);
  - Gibert et al. (AISec 2023, and arXiv 2405.00392);
  - the 2026 feature-ablation certificate on EMBER-style features (Giri et al., arXiv 2604.20495).

  These certify against bounded edit, patch or append threat models; this paper certifies against an unbounded but operation-restricted one. The trade-off must be stated.
- A sound direction table defines an orthant region per input. Tree-ensemble verification (Kantchelian et al. 2016, in `papers/`; Chen et al. NeurIPS 2019) could check an *unconstrained* GBDT on that region per sample, without training monotone constraints. The paper should explain why monotone training is preferred, or report the certified accuracy of the unconstrained model on the derived region. That accuracy is a natural upper reference point for the "cost of robustness".

*Status:* verified that these works are absent from the references.

## 4. Questions for the authors

- **A-Q1.** Can you state the locality property of π that Section 4.3.2 relies on, and prove signature coverage from it? How would you establish the locating-position record soundly (for example by taint tracking in the parser) rather than by single-byte fuzzing? Did any multi-byte probe find dependencies the single-byte probe missed?
- **A-Q2.** Does Z contain PE files with zero sections, zero strings, or zero imports? What exactly is the readout of "smallest section entropy" and "smallest section size / file size" on such files, and what does the derived table say for "add a section" on them?
- **A-Q3.** What is the end-to-end evasion rate of the routed system (gate + monotone + unconstrained fallback) when the attacker may first make the file incomplete? What is the FPR cost of rejecting or flagging all out-of-population files instead?
- **A-Q4.** On the final <4 MB protocol, what fractions of training malware and test malware lie in Z? The 314/400 training figure on p. 9 is well below the predicted 89%. What would you conclude if the measured value were 75%?
- **A-Q5.** How do the cost figures change with ≥5 seeds at full scale? Is the 3.9-point cost at 1% FPR outside the seed-to-seed spread?
- **A-Q6.** Why does the adaptive attack use a "simpler search that appends and adds sections" for the detector on sums (p. 10)? How many declined edits would the full adaptive attack have wanted to try against PV and the expert set?
- **A-Q7.** Can a "rebuild" operation (LIEF-style) be added to M with derived changes? Would it make the resource-directory features *both*, and at what detection cost?
- **A-Q8.** Have you run Gimenez et al.'s released ERDALT artifact unchanged against GAMMA imports?

## 5. Related work the paper must cite or position against

- **Self-maintainable aggregates and incremental MAX.** Mumick, Quass, Mumick, *Maintenance of data cubes and summary tables in a warehouse* (SIGMOD 1997); Palpanas et al., *Incremental maintenance for non-distributive aggregate functions* (VLDB 2002); the counting algorithm (Gupta, Mumick, Subrahmanian, SIGMOD 1993).
  - *Difference:* none in the rule itself. The paper applies it to extractor sums, and should say so.
- **Abstract interpretation and sign analysis.** Cousot and Cousot (POPL 1977); change and derivative calculi (Cai, Giarrusso, Rendel, Ostermann, PLDI 2014; change actions, Alvarez-Picallo et al. 2019); monotonicity typing (Datafun; Bloom^L lattice morphisms).
  - *Difference:* Theorem 1 is a sign abstraction of Δφ over a fold. The new part is the signature derived from the parser, not the abstraction.
- **Dependency provenance.** Cheney, Ahmed, Acar, *Provenance as dependency analysis* (DBPL 2007 / MSCS 2011).
  - *Difference:* this is the right formal tool for the "locating positions" record (A-W1), which the paper currently builds by fuzzing. The citation of provenance semirings [12] targets the wrong notion: semirings annotate *which* inputs contributed, not *which positions control discovery*.
- **Certified robustness to programmable transformations.** Zhang, Albarghouthi, D'Antoni (ICML 2020; EMNLP 2021, ARC).
  - *Difference:* they also define a threat model as a set of programs and soundly abstract its effect, but propagate through the model. This paper abstracts through the *extractor* and pushes monotonicity into the model.
- **Certified malware detection.** Huang et al. RS-Del (2023); Saha et al. DRSM (2024); Gibert et al. (AISec 2023; arXiv 2405.00392); Giri et al. (arXiv 2604.20495, 2026).
  - *Difference:* those give probabilistic or deterministic certificates for bounded byte edits on raw-byte or feature models. This paper gives deterministic guarantees for an operation-restricted, unbounded threat model on a feature-based GBDT.
- **Tree-ensemble verification.** Kantchelian et al. (ICML 2016); Chen et al., *Robustness verification of tree-based models* (NeurIPS 2019).
  - *Difference:* these are an alternative use of the derived region (A-W7).
- **Problem-space formalization, extended version.** Cortellazzi et al. (TOPS 2025, in `papers/`), the journal version of [22].
  - *Difference:* it contains the side-effect conditions the paper builds on; cite the current version.
- **Problem-space hardening on PE.** Lucas et al. (CCS 2024, in `papers/`); Tsingenopoulos et al. (2024, in `papers/`); Labaca-Castro et al., realizable universal perturbations (2022, in `papers/`).
  - *Difference:* all three obtain side effects by trial. They are the natural baselines for "what observed attacks miss" and for the cost of adversarial training.

## 6. What the missing sections must establish

- **Introduction.** The contribution must be stated as (i) a locality-based instrumentation of real extractors and (ii) its security consequences, with Section 3 explicitly presented as standard IVM and sign-abstraction reasoning. "Sound" and "cannot be evaded" must carry their conditions: a covering signature, closure, complete locating positions, and inputs in Z.
- **Discussion (Section 7).**
  - Quantify the end-to-end guarantee of the routed system and the share of all malware covered, the >4 MB files included.
  - Discuss attackers who control the build (and so can start outside Z), packing, code transformations, and tool rebuilds.
  - Say how much of the EMBER instance's soundness is empirical and how it could be made mechanical for other extractors (for example via taint tracking).
- **Generality.** Give at least an argument, ideally a second small instance (PDF, Hidost-like or Android), that the instrumentation effort is not EMBER-specific. Otherwise the framework claim is a claim about one extractor.
- **Open science.** Release the instrumented extractor, the locating-position record, the derived tables and the fuzzing harness. Reviewers and users need to audit (a)–(d) of A-W1.

## 7. Score

**Weak accept.** Confidence: **3**. I am expert in the formal machinery but not a PE-format specialist.

The security results are useful and checked by real re-extraction: extractor-derived directions expose holes in three published defenses, and they yield a monotone EMBER detector at a few points of TPR instead of most of it. The formal core, however, is known technique, the class as defined is vacuous without an unstated locality property, and the guarantee on EMBER is conditional on sample- and fuzzing-based checks plus at least one doubtful readout case. Acceptance therefore depends on reframing the claims honestly and fixing the theorem's hypotheses.

## 8. The one change that would move my score up one level

Formalize the locality property of the item map (each item's locating positions) as an explicit hypothesis of Theorem 1. Then obtain the EMBER locating-position record by a sound dependency analysis of the parser, not by sampling and single-byte fuzzing, and prove signature coverage from it. That turns the "sound" claim on EMBER from tested into proven. It would also give the paper a formal contribution that is new, rather than a restatement of IVM and sign abstraction.
