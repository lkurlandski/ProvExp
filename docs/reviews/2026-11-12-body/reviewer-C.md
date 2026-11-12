# Review C

## 1. Summary

The paper studies feature extractors with one shape, which it calls *sum-then-readout* (Def. 1–5, §3.1). The extractor finds "items" in the input. Each item adds a contribution to a set of running totals, each total a commutative monoid (additive, max or min). Each feature is a "readout" computed from a few totals. For this class:

- **Proposition 1 (§3.2).** If an edit is described by the items it removes and adds, an item table recorded during extraction gives the exact post-edit features. This is the incremental-view-maintenance rule applied to features.
- **Theorem 1 (§3.3).** A "signature" states which changes a threat model can make to each item kind. Pushing signs through the monoids and through per-readout rules (Table 1) then gives a sound table of the directions each feature can move, over a population closed under the threat model.
- **Corollary 1.** A detector that is monotone with respect to this table cannot be evaded inside that population. The paper says this is Gimenez et al.'s Proposition 1.

The authors instrument EMBER-2024's extractor (2,480 of 2,568 features; the 88 parser-warning flags are dropped). They define a 12-operation threat model built from published PE manipulations, in three nested levels: additions, shifts and full (Table 2). The guarantee is restricted to "complete, plain-layout" files; files outside that population are routed to an unconstrained detector (§4.4). The evaluation (§5) argues three things:

1. Hand-written direction tables are wrong in places: the authors' own table, and Gimenez et al.'s 40-feature expert set under the full model (§5.2).
2. Defenses learned from observed attacks (PV, ERDALT, adversarial training) trust lowerable features and fall to operations the attacks never used (§5.3).
3. A LightGBM detector with monotone constraints from the derived table, reading the underlying sums rather than the normalized features, loses about 4 points of TPR at 1% FPR and about 10 points at 0.1% FPR against the unconstrained baseline (§5.4, Table 5). Under the additions model it keeps far more detection than the expert set (92.2 vs 29.1 TPR at 1% FPR).

The summary is easy to write. The paper is dense but clear.

## 2. Strengths

- **S1. The abstraction fits a real extractor, and the fit is tested.** The sum-then-readout form covers 2,480 EMBER features with only two rewrites that preserve their values (App. D). Table 9 reports zero wrong predictions over about 70k edits, with declines decided by a uniform rule. As far as I know, this is the first time the direction analysis behind a monotone malware detector has been made mechanical and checkable for a full, deployed-style feature set, not a hand-picked 40-feature set (Gimenez) or a feature set chosen to be easy to analyze (Hidost in Chen et al. 2020). *Verified against Gimenez et al. §3 and the paper's §6.*
- **S2. The paper names the parser facts that make hand analysis go wrong.** §5.2 ("Why it errs") explains them: the overlay being taken as a new section's raw data, the entry-section fallback, the Rich-header search range, structures past EOF, and offset-0 sections. Practitioners building monotone detectors on EMBER can use this directly.
- **S3. Re-encoding over sums is a useful and general insight.** Many features move in both directions only because the readout normalizes them; the raw counts move in one direction (App. D, "Re-encodings"). Reading the sums recovers 2.4 points.
- **S4. The cost of robustness is reported honestly and broken down.** TPR is reported at 1% and 0.1% FPR, not only AUC. "Where the cost lies" (p. 10) attributes the cost to individual operations (import addition 2.1 points, header overwrites 1.4, rename about 0.1) and notes the retraining noise at 0.1% FPR. This is the kind of reporting I would want in this area.
- **S5. Evaluation hygiene.** Every evasion is decided by writing the file and re-extracting it; computed features only guide the search. The ERDALT deviation from the released code is disclosed (App. D). The leave-one-out protocol (Table 10) is stricter than the one Gimenez et al. used.
- **S6.** The comparison with the expert set under the *additions* model (Table 5, bottom) is the fairest and most convincing result in the paper: same guarantee, about 3× the TPR at 1% FPR.

## 3. Weaknesses (ranked)

**C-W1. Attackers can step around the deployed guarantee through the population routing, and the paper's argument against this contradicts its own operating point.** (§4.4, p. 7; §5.4 "Where the guarantee holds", p. 10; Corollary 1, p. 5.)

- Files outside the population go to an unconstrained detector "which carries no guarantee" (§4.4). That detector falls to the adaptive attack on about half the malware (Table 4/5 text: 25/49).
- In malware evasion, the adversary is usually the malware author, who chooses the *original* file. Making a PE "incomplete" (a directory or table that points past EOF) is plausibly a cheap, functionality-preserving choice. The paper's own data show such files run: 5% of test files are incomplete, including malware, and the single toolkit evasion of each monotone detector was exactly such a file (51 KB, with headers describing 2 MB).
- So the robustness of the composite system is the robustness of the unconstrained branch, for any attacker who chooses to start outside the population.
- The paper's answer is that such files "are rare among benign software, and so stand out". But 1.5% of benign test files lie outside the population (§5.4) and the operating point is 1% FPR (§5.1). Flagging every out-of-population file would by itself exceed the false-positive budget.
- Closure is also only "checked rather than proven" (§4.4) on 56,902 edits that were not built to break it. An attacker who tries to leave the population inside M is not modeled.

*Why it matters:* Corollary 1 is the headline security claim. As deployed, it does not bound what an adaptive attacker achieves against the system.

*Fix:*
- State the system-level threat model: who chooses z, and whether "leave the population" is an attacker goal.
- Specify a policy for out-of-population files: a monotone fallback, a stricter threshold, or a rejection with a measured FPR.
- Report system-level adversarial TPR at a fixed system FPR, against an attacker who targets the routing.
- Try to break closure adversarially, for example with header-field and append edits aimed at producing incompleteness.

*Verified* (the 1.5% vs 1% conflict, the routing, the empirical closure check, the evasion on an incomplete file). *Inferred* (that malware authors can cheaply author incomplete files that still run; the paper's 5% incomplete test files suggest it).

**C-W2. "Computed from the extractor's code" overstates what is proven. The instance rests on hand instrumentation and on hypotheses checked on samples, and an attacker who chooses the input can violate those hypotheses.** (§3.1 Def. 5 "to instrument an extractor…"; §4.3.2, p. 7; App. D "Positions that locate items", p. 15; §5.2 "The derivation needs none of these facts stated", p. 8.)

- The items, contributions and readouts are written by hand.
- The part of the signature that comes from overwrites is "read from the item tables of a sample of files". It holds only if every (kind, sum) pair on *any* population file already occurs in the sample. The evidence is that 100 files and 2,000 files give the same table.
- The record of locator positions was completed by single-byte fuzzing, and "a first round found three parser rules the record had missed" (App. D).
- The derivation therefore needed trial to become correct, as the hand table did. The claim that "the derivation needs none of these facts stated" is true only after the fuzzing loop.
- The sample-based hypotheses are statements about benign/malware *distributions*. The attacker controls the original malware and can craft rare item kinds or value-triggered parser paths (magic values, multi-byte fields) that random single-byte changes do not reach.

*Why it matters:* a reader will take "sound bound" and "no edit in the threat model can evade" (note, Corollary 1) as a proof about EMBER. It is a proof about the abstraction, plus empirical validation of the abstraction on non-adversarial data.

*Fix:*
- State the trusted base explicitly: the instrumentation, the declared semantics of each operation, coverage of the sampled item tables, the locator record, and closure.
- Move what can be moved to inference time. Since membership in the population is already checked per file, also check per file that its item table introduces no (kind, sum) or locator outside the signature, and route it out otherwise.
- Test the hypotheses adversarially: structure-aware or value-aware fuzzing of the parser, not single random bytes.

*Verified.*

**C-W3. The comparison with "observed attacks" gives the baselines less information than the method, so the headline outcomes are close to built in.** (§5.3, p. 9; Table 4; §5.2 "Our hand table", p. 8; Table 3.)

- PV, ERDALT and adversarial training learn from the eight toolkit attacks, which use 6 of the 12 operations (Table 2). The derived table is computed for all 12. The adaptive attack then uses an operation the learned defenses never saw (section rename for PV, p. 9).
- "A defense learned without operation X falls to X" is what Gimenez et al. themselves state: ERDALT "is limited by its training dataset" (Gimenez §4; *verified*). It does not show that derivation beats learning.
- The fair comparison gives every method the same knowledge. Train PV, ERDALT and adversarial training on the outputs of *all twelve* operations, using the authors' own edit generator and adaptive attack, which Proposition 1 makes cheap. Then compare detection and evasion.
- The same applies to §5.2. Every one of the eight hand-table errors in Table 3 was found by real edits in the 73k-edit suite. A defender who combined a hand table with systematic trial over the 12 operations would have caught all of them.
- The paper's own numbers suggest the derived table may be conservative rather than more complete. Of the 142 features the derived table marks lowerable but the toolkit never lowered, only 20 are confirmed lowerable by any of the 73k edits (§5.3, "What the attacks reveal"). Whether the other 122 are truly lowerable, or over-approximation that costs detection, is not established.

*Why it matters:* the paper's central framing is computation versus trial, hand analysis and observed attacks. Against an equally informed trial baseline the advantage may shrink to a modest, unquantified one.

*Fix:*
- Add the equal-information baselines above.
- For the 122 unconfirmed features, either give witness edits or measure the detection cost of the over-approximation: train a detector on a "trial-derived" table from the full edit suite, and report its TPR and whether the adaptive attack evades it.

*Verified* (operation sets, counts). *Inferred* (the likely outcome of the equal-information baselines).

**C-W4. Real attack tools fall outside the declared operations, and important attack classes are excluded, so the guarantee covers less than the evaluation framing suggests.** (§5.4 "Beyond the guarantee", p. 10; §4.3.1, p. 6.)

- 36 of 288 toolkit outputs on population files move features outside the derived table, because GAMMA rebuilds the layout through a library, an operation that is not in M. Corollary 1 says nothing about these files. Their survival is empirical, at 100 to 500 queries.
- Code-level transformations (Lucas et al. 2021; Ling et al. 2024) and packing are excluded with a one-line justification. The claim that code-level transformations are "much harder to apply without breaking the program" contradicts Lucas et al. 2021, who apply them while preserving functionality.
- In-place code rewrites land in section bodies, which is exactly where the "sums over section bodies" re-encoding assumes no write lands (App. D).

*Fix:*
- Model layout rebuilding as an operation (its declared changes are derivable: section and directory relocation, size updates), or detect it.
- Evaluate the monotone detectors against at least one out-of-model attack: Malware Makeover-style in-place rewriting, or MAB-Malware's full action set. Readers then see what happens when the threat model is wrong.
- Scope the claims in the intro accordingly.

*Verified* (the 36/288 figure, the exclusions). *Inferred* (the effect of code rewrites on the section-body re-encoding).

**C-W5. The ERDALT reimplementation is not yet shown to be faithful, and the conclusion drawn from it misreads what ERDALT claims.** (§5.3 "What ERDALT learns", p. 9; App. D "ERDALT", p. 16; Table 4.)

- Here ERDALT is evaded on 24/29 by GAMMA imports, an attack in its training set. Gimenez et al. report 96% robustness on EMBER (their Table 2).
- The reimplementation differs from theirs in several ways: the output layer is constrained (a change from the released code), the dataset is different (EMBER-2024 vs Dambra et al.), and the number of adversarial examples is different (3,183 vs 1,033).
- ERDALT's positivity constraint is a soft penalty (the l2 loss). An evasion by a training attack could therefore mean the penalty was not met even on training perturbation vectors. That would be a training issue, not the conceptual gap the paper describes.
- Prop. 3 of Gimenez et al. assumes a finite, known set of perturbation vectors. GAMMA with new donor content violates this by design. "The layer constrains the feature changes it was shown" is a restatement of that stated hypothesis, not a finding.

*Fix:*
- Report the fraction of training and test perturbation vectors with L(δ) < 0.
- Report results with the unmodified released code and with Gimenez's settings.
- Present the result as quantifying a known limitation.

*Verified* (Gimenez numbers and Prop. 3 hypothesis, App. D change). *Inferred* (soft-constraint violation as a possible cause).

**C-W6. The experimental design cannot yet support the comparative claims, independent of the preliminary scale.** (§5.1; Tables 4, 5, 10.)

- **Denominators.** Many claims rest on the malware a detector happens to detect: 2 of 8 (expert set), 4 of 9 (PV), 10 of 29 (hand detector). Comparing "evaded / detected" across detectors with different detection is misleading. Report **robust TPR**, the share of *all* attacked malware still detected after attack at the fixed FPR. On the current numbers, PV (about 5/50) and ERDALT (about 7/50) come out *below* the unconstrained detector (about 24/50), and the monotone detectors come out far above. This metric would strengthen the paper.
- **Adaptive attack coverage.** The headline detector, monotone on sums, is attacked only by "a simpler search that appends and adds sections" (p. 10), not by the full adaptive attack. Run the full attack on every detector.
- **Inconsistent baselines.** The unconstrained detector reports TPR 95.6 and 25/49 in Table 4 but 93.5 and 26/47 in Table 5, and §5.4 attacks a detector "trained on the full training set" that differs from Table 5's row. Use one baseline per comparison.
- **Seeds and noise.** One seed, while the authors say retraining moves 0.1% FPR detection by about 3 points. The 9.7-point cost at 0.1% FPR needs several seeds and confidence intervals.
- **Speed.** The claim that Proposition 1 is cheaper than extraction (§3.2) has no timing measurement.

*Verified.*

**C-W7. The generality claim rests on one domain.** ("broad class", §2–3 and the note; §4 is the only instance.)

- The second extractor instrumented (Gimenez's) is a PE extractor written for the same purpose.
- No instrumentation effort is reported: lines of code, person-time, how many item kinds and contributions were written by hand.

*Fix:* a second instance in another domain, such as Drebin-style Android features (presence bits, a trivial fit) or flow-statistics network features (sums, max/min, mean, std; exactly the readout forms of Table 1). Or, at minimum, report the instrumentation effort and the features that do not fit. *Verified* (only EMBER and Gimenez's extractor are instantiated).

**C-W8. The formal results are modest in technical novelty, and the positioning misses the most relevant PL lineage.**

- Proposition 1 is incremental view maintenance (acknowledged).
- Theorem 1 is a sign-domain abstract interpretation over commutative-monoid aggregates with per-operator transfer rules (Table 1).
- Corollary 1 is Gimenez Prop. 1 (acknowledged).

I do not hold this against the paper if the contribution is framed as methodology plus instance plus empirical critique. But §6 should position against abstract interpretation and sensitivity/monotonicity analyses, and not only against databases and incremental parsing. *Verified.*

**C-W9. The 4 MB scope and the 89% placeholder.** (§5.1; §5.4 "Where the guarantee holds"; note.)

- Excluding files over 4 MB removes 26% of malicious and 6% of benign test files, so the test distribution is biased. Detection-cost numbers are conditional on this subset and should be stated as such.
- The 89% figure, if confirmed, comes from about 50 attacked malware, so its confidence interval is roughly ±9 points. It should be measured on the full malicious test set.
- Read with C-W1, an 89% share means about 11% of malware get no guarantee and go to a branch that falls to the adaptive attack about half the time. A value near 75% would make "the guarantee holds on the population" a minority-of-the-risk claim for malware with unusual layouts.

The design supports the statement *as a coverage figure*. It does not support it as a security statement without C-W1's system-level evaluation.

## 4. Questions for the authors

- **C-Q1.** How does the deployed system handle out-of-population files, and at what FPR? Can a malware author produce a working incomplete PE on purpose? What is the system-level robust TPR against an attacker who does so?
- **C-Q2.** For the 122 features the derived table marks lowerable but no edit lowered: do you have witness edits, or are they over-approximations? What is the detection and robustness of a monotone detector built from a table learned by systematic trial over all 12 operations?
- **C-Q3.** With PV, ERDALT and adversarial training trained on outputs of all 12 operations (or of your adaptive attack), do your §5.3 conclusions still hold?
- **C-Q4.** For ERDALT, what fraction of training perturbation vectors violate L(δ) ≥ 0? What are the results with the unmodified released code and Gimenez's protocol?
- **C-Q5.** Can the sample-derived part of the signature, and the locator record, be checked per file at inference? If so, why not make that part of the population test?
- **C-Q6.** What does the full adaptive attack (all operations, 5,000 candidates) achieve against the monotone detector on sums? What do the monotone detectors do against layout-rebuilding and in-place code-rewriting attacks?
- **C-Q7.** How much effort did instrumenting EMBER take, and how much of it transfers to a different extractor?

## 5. Related work to cite or position against

- **Abstract interpretation and sign analysis** (Cousot & Cousot, POPL 1977), and **sensitivity type systems** (e.g., Reed & Pierce, "Distance makes the types grow stronger", ICFP 2010). Theorem 1 is a sign abstraction of the extractor; the paper should say what it adds over instantiating these frameworks: handling raw-byte edits by locating items, and soundness tied to the population.
- **Certified defenses for PE malware under edit budgets:** Huang et al. 2023 (RS-Del) and Saha et al. 2024 (DRSM), both in the provided papers and not cited. They certify against bounded byte edits for raw-byte models. This paper certifies against unbounded edits of given types for feature-based models. The difference matters and should be stated.
- **Problem-space adversarial training at scale:** Lucas et al. 2024 (GreedyBlock, hours not months) and Tsingenopoulos et al. 2024 (RL-based problem-space hardening). These are the strongest empirical-robustness baselines. Proposition 1 could make problem-space adversarial training over the full threat model cheap, which is a natural comparison (C-W3).
- **Dyrmishi/Zainab et al. 2026** ("Breaking Windows Malware Detection", arXiv 2609.34456). This large evaluation of nine problem-space attacks finds that a few complementary attacks cover about 99% of adversarial examples. That bears directly on the claim that observed attacks miss operations.
- **Kantchelian et al. 2016.** Exact evasion of tree ensembles (MILP). With the derived table as box/orthant constraints, this gives an exact feature-space attack (or certificate) for the unconstrained GBT inside the derived region. It is a stronger complement to the beam-search adaptive attack.
- **Bostani et al. 2025, Sheatsley et al. 2021 (cited), and data-driven constraint mining (TaCLe-based).** These are already partly positioned. The difference (derived from code vs learned from data) is stated clearly. Good.
- **Lucas et al. 2021 and Ling et al. 2024** (cited). They are needed in the threat-model discussion as functionality-preserving in-place attacks, not as "much harder" ones.

## 6. What the missing sections must establish

- **Introduction:** state the claim in its true scope. The guarantee covers declared byte-level operations, on files inside a population checked at inference, conditional on a stated trusted base. It does not cover "every edit an attacker can make".
- **Discussion:**
  - the security of the composite system (routing, out-of-population policy, the attacker who authors z);
  - code-level transformations, packing and layout-rebuilding tools;
  - how a defender maintains the threat model and the signature as operations are added;
  - the cost of instrumenting a new extractor.
- **Open science:** release the instrumented extractor, the operation implementations, the item-table tests and the edit suite. The soundness of the instance rests on this code, so reviewers and users must be able to audit it.
- **Ethics:** the adaptive attack and the list of lowerable features in a published detector's expert set are offensive knowledge. Say how they were disclosed and released.

## 7. Score

**Weak reject.** Confidence: **4** (expert in this area).

The framework is clean, the EMBER instance is careful and validated, and the cost analysis is the most honest I have seen for monotone malware detectors. But the security claim does not yet survive an attacker who chooses the original file or leaves the population, the soundness of the instance rests on hypotheses checked on samples that the attacker controls, and the comparisons with learned defenses give them less information than the method.

## 8. The one change

Evaluate the **deployed system**, not the in-population detector. Specify the out-of-population policy, move the sample-based signature and locator checks to per-file inference-time checks, and report system-level robust TPR at a fixed system FPR against an adaptive attacker who also tries to leave the population or start outside it. If the guarantee survives that, I would move to weak accept. Adding the equal-information baselines of C-W3 would move me further.
