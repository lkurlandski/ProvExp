# Review B

Paper: "Bridging the Gap: A Closer Look at Adversarial Examples in the Problem Space" (placeholder title). Body draft; the abstract, introduction, discussion and ethics/open-science sections are missing on purpose. All numbers are preliminary, per the authors' note.

## 1. Summary

The paper looks at feature extractors that work in three stages: they find "items" in the input (sections, imports, bytes, strings, …), fold each item's contribution into commutative-monoid accumulators ("sums": additive totals, max pools, min pools), and compute each feature by a "readout" formula over a few sums. It calls these *sum-then-readout* extractors (Defs. 1–5, §3.1). Two results follow:

- **Proposition 1 (§3.2, p. 4).** If you have the extractor's item table for a file and the item delta of an edit, you can compute the edited file's features exactly before applying the edit. This is incremental view maintenance for distributive aggregates. Pools are recomputed from the kept items.
- **Theorem 1 (§3.3, p. 5).** Given a *signature* (the kinds of item changes a threat model can make) that covers the threat model over a population closed under it, you can propagate signs (up/down/fixed/both) from contributions to sums to features through per-readout rules (Table 1). The resulting direction table is sound. **Corollary 1** then restates Gimenez et al.'s Proposition 1: a score that is monotone with respect to the table cannot be lowered by any sequence of edits.

The paper applies this to EMBER v3 (2,480 of 2,568 features; the 88 parser warnings are dropped) with a threat model of 12 structural PE operations, nested as additions ⊂ shifts ⊂ full (Table 2). The population is "complete files with a plain layout" (§4.4). The evaluation (§5) reports the following:

- (a) A hand-written direction table by the authors has 8 errors (Table 3).
- (b) Under the full threat model, 11 of Gimenez et al.'s 40 "expert" features can be lowered, and an adaptive attack evades the expert-set detector on 2 of 8 malware.
- (c) Defenses learned from observed attacks fall to edits those attacks never made. PV falls to a section rename. ERDALT falls to GAMMA-imports with unseen donors. Adversarial training does not stop the adaptive attack.
- (d) A GBDT that is monotone with respect to the derived table, trained on raw sums, detects 89.6% vs 93.5% at 1% FPR (74.7% vs 84.4% at 0.1%). Toolkit attacks evade it only on an out-of-population file.

The summary was easy to write. The paper is clearly argued and the formal part is precise.

## 2. Strengths

- **S1. The problem is the right one.** Every robust-by-construction malware detector (Incer et al. 2018; Chen et al. 2021; Gimenez et al. 2025) needs per-feature knowledge of how edits can move features. In all of them that knowledge comes from an analyst or from observed attacks. Computing it from the instrumented extractor and a declared threat model is a natural step, and as far as I can tell a new one. My search found no prior work that derives these constraints from the extractor's code. The closest work learns constraints from data (Sheatsley et al. 2021; Bostani et al. 2025; TaCLe, MILCOM 2023).
- **S2. The formalism is clean and fits the domain.** The item/sum/readout factorization is well chosen. Separating pools from groups (§3.1, App. B) correctly explains why the item table must keep every item. The readout rules (Table 1) and the derived table (Def. 10) are simple and easy to check. I checked the proofs in App. C and found no error in them.
- **S3. The key failure of Gimenez et al.'s defenses is shown concretely and checked by re-extraction.** PV and ERDALT trust features that edits outside the observed attacks can lower. PV trusts a hashed bucket of the entry section's name, which carries 12.8% of split gain and falls to a single rename (§5.3, p. 9). This is a falsifiable counterexample. It does not depend on scale, because one counterexample refutes a robustness claim. The leave-one-out protocol (Table 10) is a good addition. It shows that the attack-held-out tests the field uses can still vouch for a detector with a known hole.
- **S4. Evasions are confirmed on real files.** Every evasion is confirmed by writing the edited file and re-running EMBER's extractor (§5.1). Proposition 1's predictions are compared with re-extraction on 73k edits, with zero mismatches in the population (Table 9). The paper also reports where its machinery declines to predict, rather than hiding it.
- **S5. The cost result could matter in practice if it holds at scale.** A monotone EMBER-2024 GBDT that loses about 4 TPR points at 1% FPR (Table 5) is a much better trade-off than any prior robust-by-design PE detector. Gimenez et al.'s expert set gets 29.1% TPR, and Incer et al. accept large losses. The per-operation ablation (§5.4, "Where the cost lies") is the kind of result practitioners need: import addition costs 2.1 points and header overwrites 1.4 points.
- **S6. The paper is candid about limits.** It discusses tools that rebuild the file layout and leave the table (§5.4 "Beyond the guarantee"), files outside the population, and the sample-based part of the signature. That candor is what lets me write weaknesses B-W1 to B-W3 precisely.

## 3. Weaknesses (ranked by severity)

**B-W1. The EMBER guarantee rests on instrumentation that was validated by trial, which is the very method the paper says cannot give guarantees.**
*Location:* §4.3.2 (p. 7), §4.4 (p. 7), App. D "Positions that locate items" (p. 15), Table 9.
*Problem:* Theorem 1 is a theorem about an abstract sum-then-readout extractor. On EMBER, its hypotheses are established empirically in three places:
1. The overwrite part of the signature is "read from the item tables of a sample of files" (100 files). The paper says it "rests on the sample rather than on a proof" (p. 7).
2. Closure of the population is "checked rather than proven" on 56,902 edits (§4.4).
3. The record of positions the parser reads to locate items was completed by single-byte fuzzing. A first round found three parser rules the record had missed; 58,666 changes later showed no further misses (App. D).

Single-byte probing cannot find item-creating writes that need coordinated multi-byte content: magic values, or the forged Rich header that the paper itself had to handle as a special case. The hand table's eight errors (Table 3) are exactly this kind of parser subtlety, and the instrumentation missed three of them too, at first. The paper's central claim is that computing directions beats trial and hand reading because it covers "every edit the threat model allows". For EMBER, the claim reduces to "a hand instrumentation, tested by trial, is more reliable than a hand direction table, tested by trial". That may be true. Trust moves from 2,568 × 12 per-feature judgments to a smaller set of per-item-kind declarations and parser read sets, which are more local and easier to audit. But the paper never states this argument, and it never measures how much trust is involved: how many item kinds, contribution functions, declarations and parser rules, and how many lines of instrumentation.
*Why it matters:* The headline "detectors that no edit in the threat model can evade" (authors' note; Corollary 1) is a certificate. A certificate whose premises were sampled is an empirical robustness claim, and has to be reviewed as one.
*Fix:*
- (i) Present the EMBER guarantee as conditional on named, enumerated assumptions (A1 signature completeness, A2 closure, A3 read-set completeness), and give the size of each trusted component.
- (ii) Replace fuzzing with a mechanism that is sound by construction for A3. Dynamic taint or provenance tracking of every byte the parser reads (pefile/LIEF) gives the read set per file. At least confirm that read-set tracking agrees with the fuzzed record.
- (iii) Run a targeted multi-byte search for item creation at recorded-safe positions, e.g., grammar-based fuzzing of the header and directory regions.
- (iv) Report the error rate the instrumentation itself had before correction, as was done for the hand table, so readers can compare the two on equal terms.

*Verified* against the paper's text (pp. 7, 15).

**B-W2. The threat model leaves out what real tools and real attackers do, and the paper's own data shows the gap.**
*Location:* §4.3.1 (p. 6), Table 2, §5.4 "Beyond the guarantee" (p. 10).
*Problem:*
- (a) Even the toolkit the threat model was built from is not inside it. 36 of 288 toolkit outputs in the population move features outside the derived table, mostly the resource-directory size, which the table holds fixed (p. 10). The reason is that GAMMA goes through LIEF, which rebuilds the layout. An attacker uses whatever transformation works, not the operation as declared. That both rebuilding attacks then fail at 100 queries says nothing about an attacker who deliberately uses layout rebuilding to lower features that the table marks fixed and the detector therefore uses freely.
- (b) Code-level transformations (Lucas et al. 2021/2023; Ling et al. 2024; MAB-Malware's code-level actions) and packing are excluded and deferred to §7. These are the transformations that move the byte, string and entropy statistics. The "price" in Table 5 is measured under a threat model that leaves in-section bytes alone. Indeed, the re-encodings in App. D take counts "only over the section bodies and the overlay, where no in-place write of our threat model lands" (p. 15). Under in-section rewriting, I expect those re-encoded sums to become two-sided. The 3.9-point cost could then grow substantially (*inferred*).
- (c) Gimenez et al. motivate their threat model by an attacker without source code (MaaS). The paper does not say which attacker its 12 operations model, or why that attacker would stop there.

*Why it matters:* At this venue, a robustness guarantee is worth as much as its threat model is realistic. Right now the guarantee does not cover two of the eight off-the-shelf attacks the paper itself uses.
*Fix:*
- (i) Add layout rebuilding as a declared operation, or as one whose changes come from the item tables, and re-derive the table and its cost.
- (ii) Run an adaptive attack that searches over LIEF-rebuild edits specifically to lower table-fixed features.
- (iii) Report the derived table and the detection cost under an extended threat model with in-section code rewriting (e.g., the transformations of Lucas et al.), even if the answer is that the cost becomes large. That is a finding, and it tells practitioners where monotone detection stops being affordable.
- (iv) State the attacker model explicitly.

*Verified* for (a) and for the scope of the re-encodings (pp. 10, 15). *Inferred* for the magnitude in (b).

**B-W3. The guarantee covers only the population; the composed system is never evaluated end to end, and the 89% figure is probably optimistic.**
*Location:* §4.4 (p. 7), §5.4 "Where the guarantee holds" (p. 10); authors' note (placeholder 89%).
*Problem:* The deployed system has three parts: a population check, the monotone detector on in-population files, and an unconstrained, evadable detector on everything else. Its robustness is that of the weakest path.
- *The earlier run already contradicts the placeholder.* In the run on all files, only 35 of the 47 malware the unconstrained detector detects are in the population, i.e., 74% (p. 10). Likewise, 314 of 400 training malware are in the population, i.e., 79% (p. 9). The 89% prediction presumably comes from removing files truncated at 4 MB, which look incomplete. That is a property of the authors' copy of the data, not of the malware attackers deploy. A deployed extractor sees whole files. So the fraction of real malware outside the population should be estimated on complete files, not on the <4 MB subset.
- *Effect on the bottom line.* If roughly a quarter of malware is unprotected, and the unconstrained detector falls to the toolkit on about half of what it detects, the end-to-end evasion rate is on the order of 10–13%. That is comparable to the adversarial-training row of Table 4 (*inferred* arithmetic). Even at 89%, the floor is around 5%. Neither number appears in the paper.
- *"Such files ... stand out" (p. 10) does not work at the operating point.* The same paragraph says 1.5% of benign test files are outside the population. That is above the 1% FPR budget, so flagging out-of-population files would cost more false positives than the whole detector is allowed. *Verified* from the text.
- *Excluding files over 4 MB.* This removes 26% of malicious and 6% of benign test files (§5.1). Large files (installers, droppers with big overlays, bundled payloads) are a distinct, attack-relevant group. Leaving them out changes the base rates the cost is measured on, and leaves a deployment question open.

*Why it matters:* A practitioner deploys the system, not the in-population detector. A guarantee that covers 75–89% of malware, with a known path around it, has to be measured as a system.
*Fix:*
- (i) Report end-to-end detection and evasion for the composed system, with the same attacks and an attacker who knows the routing.
- (ii) Measure the population share on complete files, using a source that holds whole binaries, e.g., the EMBER-2024 originals from VirusTotal or another corpus.
- (iii) Show what it costs to route out-of-population files to a monotone detector trained with "both" for every feature the population rules touch, instead of to an unconstrained one.
- (iv) Say whether an attacker can take an in-population file out of the population with a functionality-preserving edit outside M. Closure under M does not exclude that.

*Verified* (pp. 7, 9, 10). End-to-end figures *inferred*.

**B-W4. The attacks are weaker than published ones, and the adaptive attack cannot explore the edits where the machinery declines, so the negative results about it carry little weight.**
*Location:* §5.1 "Attacks" (p. 7), Tables 4–5, App. D "The adaptive attack" (p. 16), Table 9.
*Problem:*
- (a) The toolkit attacks run with 100 queries and a 5%/512 KB budget. The paper itself notes that the GAMMA paper uses about 500 queries (p. 10). Zainab/Dyrmishi et al. (arXiv 2609.34456, 2026) find MAB-Malware to be the strongest off-the-shelf attack against EMBER-2024 GBDT. MAB-Malware is used here only as a source of operations and is never run.
- (b) The "stronger, white-box adaptive attack" (p. 7) is a beam search of width 3 over random candidates, with at most 5,000 candidates. On the unconstrained detector it evades exactly as often as the toolkit (25/49 vs 25/49, Table 4), and it does worse on ERDALT (22/29 vs 24/29). So it is not demonstrably stronger.
- (c) "The computation declines only edits that write bytes the parser reads ... and the adaptive attack skips them" (p. 8). Per Table 9, that is all loader-ignored header-field overwrites and 5,739 of 7,428 DOS-header overwrites. The header-field operation is the one that evades the additions-only monotone detector on 12 of 43 (p. 10). So the adaptive attack never explores a large part of the full threat model.
- (d) On in-population files, the statement that the score drop on the monotone detector is "exactly zero" follows from Corollary 1 plus correct instrumentation. It adds no independent evidence, because the candidates' features come from Proposition 1, which uses the same instrumentation. Moreover, the headline detector on sums was attacked only with "a simpler search that appends and adds sections" (p. 10).
- (e) Adversarial training uses 3,183 examples mixed into the full training set (p. 9), which is a tiny fraction. That is not how a practitioner would harden a model (cf. Lucas et al. 2023/2024, who generate examples at scale). The conclusion "adversarial training evades about as often as before" therefore rests on a weak baseline and a weak attack.

*Why it matters:* The provable part does not need strong attacks. But the paper's comparative claims about adversarial training and ERDALT do, and so does its check that the guarantee holds on real files.
*Fix:*
- Run MAB-Malware and GAMMA at published budgets.
- Make the adaptive attack independent of Proposition 1: re-extract every candidate. That is slower but available, and it removes the circularity.
- Let it use the declined edits (re-extract them).
- Run the full adaptive attack on the detector on sums.
- Run adversarial training at a realistic ratio, or use a published hardened EMBER model.

*Verified* (pp. 7–10, 16; Tables 4, 9).

**B-W5. The theoretical contribution is modest and borrows more than the related-work section admits.**
*Location:* §3 (pp. 2–5), §6 "Incremental computation and provenance" (p. 11), App. C.
*Problem:*
- Proposition 1 is the fold homomorphism σ(A⊎B)=σ(A)⊕σ(B) applied to an item delta. The paper concedes it holds because "Definition 5 defines the class by this computation" (p. 4). Part (i) is the IVM rule for SUM (Gupta & Mumick; DBToaster), and part (ii) is the standard treatment of MAX/MIN, which are not self-maintainable under deletion.
- Theorem 1 is sign abstraction propagated through monotone operators: the textbook first example of abstract interpretation (Cousot & Cousot 1977). It is not cited, and readers from PL will recognize it immediately.
- Corollary 1 is Gimenez et al.'s Proposition 1, as App. C acknowledges.

None of this is wrong, and simplicity can be a virtue. But the contribution is the engineering of the instance and the empirical findings, not the theorems. The missing introduction must not present Proposition 1 and Theorem 1 as the main technical novelty.
*Fix:* Cite abstract interpretation and position Theorem 1 as a sign-domain analysis of a restricted program class. Move effort from formalism to B-W1's soundness mechanism, which is where the real technical difficulty lies: computing the item delta of a raw byte write, a step the paper rightly says IVM does not provide (p. 12).
*Verified* (against the paper's own text and standard results).

**B-W6. The general framework has only one instance.**
*Location:* authors' note ("many feature extractors ... have one shape"); §4 ("Any new instance ... needs to supply the same", p. 5).
*Problem:* The class claim is supported only by EMBER. Plausible further instances exist: Drebin (presence bits), Hidost (path counts), CICFlowMeter-style flow statistics, PDFrate. Important extractors fall outside the class: order-dependent features (n-grams over sequences, positional features), learned embeddings, raw-byte networks (MalConv, ExeFormer). The class therefore excludes a large part of the current static-detection literature, including raw-binary models, which Lucas et al. and recent work target.
*Why it matters:* A CCS paper that claims a general framework needs either a second, structurally different instance or a clear statement that this is a PE/EMBER paper.
*Fix:* Add a second instance, for example Drebin or Hidost, where the cost of instrumenting can be compared with Chen et al. 2020's hand derivation. Alternatively, narrow the claim. Also state precisely which common feature types fall outside the class.
*Inferred* (scope argument).

**B-W7. The experimental design is too small and inconsistent to support the comparative numbers. The issue is the design, not the preliminary values.**
*Location:* §5.1 (p. 7), Tables 4–5, §5.2–5.3.
*Problem:*
- Many claims rest on a handful of files: PV evaded on 4/9, the expert set on 2/8, the hand detector moved on 10/29 with no evasion. An existence counterexample is enough to refute a guarantee (S3). The rates are not enough to rank defenses.
- The thresholds are set on the benign *test* files (p. 7), so there is no held-out calibration. At 0.1% FPR on a 10% subsample, the paper itself says retraining noise moves TPR "by a few points" (p. 10). That is the same size as the effects attributed to individual operations.
- The unconstrained detector differs between rows: it is trained on a 10% subsample for Table 5 but on the full set for the adaptive-attack figure in §5.4. Adversarial training uses the full set while PV and ERDALT use the subsample. Rows of the same table are therefore not comparable.
- The hand-table comparison (Table 3) has n = 1 analysis, written by the authors. Its in-population errors produce no evasion (p. 8: "No drop crosses the threshold").

*Fix:*
- Use at least thousands of attacked malware, with confidence intervals.
- Use several seeds, with mean ± spread for TPR at both FPRs.
- Use a validation split for thresholds.
- Use the same training data for all rows of a table.
- For Table 3, either recruit independent analysts or present it as an illustration rather than a measurement.

*Verified* (pp. 7–10).

**B-W8. Several comparisons with prior work are stated without caveats.**
*Location:* §5.1 (p. 7), §5.2 (p. 8), §5.3 (p. 9), App. D "ERDALT" (p. 16).
*Problem:*
- "100 queries per file, as in Gimenez et al." does not match their paper, which reports a 60-second timeout per attack (Gimenez et al., §5.1). *Verified* against `papers/gimenez2025certifiably.pdf`.
- The ERDALT reimplementation changes the design: the output layer is kept nonnegative. The model reaches AUC .883 vs 93.0% in the original, on different data. That deviation needs justification, plus a run of the unmodified released code, because the ERDALT failure (24/29) is a headline result.
- On the expert set, Gimenez et al. include indicators of "DOS stub modification", so rewriting the stub is something they anticipated. The paper should explain why a stub rewrite lowers those features, e.g., by restoring a canonical stub, so that it is clear this attacks their design and not just their feature extraction.
- The paper cites Pierazzi et al. 2020 but not the extended TOPS 2025 version (Cortellazzi et al.), which is in `papers/` and extends the side-effect discussion. It also omits that Pierazzi et al. already estimate side effects in advance by injecting each gadget into a minimal app. That is a precomputation of η, which is closer to Proposition 1 than §2's statement that side effects "generally cannot be computed in advance" implies.

*Fix:* Correct and caveat each point. Run the original ERDALT code as a second baseline.

## 4. Questions for the authors

- **B-Q1.** What fraction of complete (untruncated) malware is in the population? What is the end-to-end evasion rate of the composed system under the strongest attack you can run, including one that knows the routing? (B-W3)
- **B-Q2.** Can a functionality-preserving edit outside M move an in-population malware sample out of the population, for instance by enlarging a section's declared raw size past EOF? If so, what stops the attacker from always taking that path to the unconstrained detector?
- **B-Q3.** How large is the trusted base of the EMBER instance: number of item kinds, declarations, parser read rules, and lines of instrumentation? How many errors did the instrumentation have before the fuzzing round? Did you compare the fuzzed read-set record with dynamic taint tracking of the parser? (B-W1)
- **B-Q4.** If you add LIEF layout rebuilding as an operation, and separately in-section code rewriting à la Lucas et al., what does the derived table become, and what is the TPR cost at 1% and 0.1% FPR? (B-W2)
- **B-Q5.** Does an adaptive attack that re-extracts every candidate and uses the declined edits, header-field overwrites included, ever lower the score of the detector on sums on an in-population file? (B-W4)
- **B-Q6.** Against MAB-Malware and GAMMA at published budgets, how do the unconstrained, adversarially trained, and monotone detectors compare? (B-W4)
- **B-Q7.** Does the unmodified released ERDALT code reproduce the 24/29 GAMMA-imports failure? (B-W8)
- **B-Q8.** Raw-count re-encodings scale with file size. How does the detector on sums behave on benign files much larger than the training distribution, including the >4 MB files you excluded?

## 5. Related work to cite or position against

- **Gimenez, Sivaprasad, Fritz, SEC 2025** (cited). This is the closest work. It contains the monotone-robustness theorem (your Corollary 1), the expert set, and PV/ERDALT. The difference is that you compute the directions rather than choosing them by hand or learning them from attacks. The paper makes this difference clear. Fix the query-budget attribution and acknowledge their stated attacker model (no source code).
- **Incer et al., IWSPA 2018** (cited) and **Microsoft's deployed monotone models** (Microsoft Security blog, July 2019, "New machine learning model sifts through the good to unearth the bad in evasive malware"). These show that hand-assigned monotone detection has been deployed in practice. Cite the latter as evidence that the problem matters to practitioners.
- **Chen et al., USENIX Sec 2020 / CCS 2021** (cited). Verified robustness with feature sets chosen to be easy to analyze. Your difference is that you handle the extractor deployed detectors actually use. A second instance on Hidost would make that difference concrete.
- **Certified defenses for static malware detection, not cited:** RS-Del (Huang et al., NeurIPS 2023), DRSM (Saha et al., ICLR 2024), and Giri et al., "Towards Certified Malware Detection" (arXiv 2604.20495, Apr 2026), which smooths EMBER-style features. These certify against edit-distance or contiguous-byte budgets, regardless of what the edits mean. You certify against unbounded sequences of declared operations. The trade-offs between these guarantees are different, and they must be compared, at least on threat-model coverage and clean-accuracy cost.
- **Cortellazzi et al., TOPS 2025** (extended Pierazzi et al.; not cited). Cite it alongside [22]. It includes side-effect estimation by gadget injection.
- **Zainab, Dyrmishi, Bostani, Cordy, Cavallaro, arXiv 2609.34456 (2026).** A large-scale evaluation that identifies MAB-Malware as the strongest attack and notes that two attacks cover about 99% of evasions. This defines the attack set a 2027 defense paper should face.
- **Lucas et al., CCS 2024 ("Training Robust ML-based Raw-Binary Malware Detectors in Hours, not Months")**, together with Lucas et al. 2023 (cited). These are the practitioner baseline for adversarial training at scale, and they set the bar B-W4(e) asks for.
- **Data-driven constraint mining (TaCLe, MILCOM 2023)**, alongside Sheatsley et al. and Bostani et al. (cited). This is the "learned constraints" alternative.
- **Cousot & Cousot, POPL 1977 (abstract interpretation).** Theorem 1 is a sign-domain analysis and should be presented as such.
- **Labaca-Castro et al. 2022 (realizable UAPs) and Kantchelian et al. 2016 (evasion of tree ensembles).** Labaca-Castro et al. map problem-space transformations to feature-space side effects for PE files. Kantchelian et al. give exact attacks on tree ensembles, which would make a far stronger white-box attack on your GBDTs than beam search.

## 6. What the missing sections must establish

- **Introduction.** State the guarantee honestly. It is a theorem for the abstract class and conditional on named, empirically checked assumptions for EMBER (B-W1). Say who the attacker is: binary-only structural modification, no recompilation, no packing. Present the contribution as computed directions plus the empirical findings, not as new theory (B-W5).
- **Introduction / abstract.** Report the end-to-end number for the deployed system (in-population share × protected, plus the unprotected remainder), not only the in-population guarantee (B-W3).
- **Discussion (§7).** Quantify, or at least bound, what happens under code-level transformations and layout-rebuilding tools (B-W2). Discuss explicitly whether monotone detection survives an attacker who uses an edit outside M to leave the population. Discuss which extractor families fall outside the class.
- **Open science.** Release the instrumented extractor, the item-table recorder, the derived tables and the attack code. The guarantee can be audited only through the instrumentation.
- **Ethics.** The paper publishes an automated way to find lowerable features in published defenses. Responsible disclosure to Gimenez et al., and to any vendor using hand tables, should be mentioned.

## 7. Score

**Weak reject.** Confidence: **4**. I work on adversarial ML for malware detection and know the problem-space attack literature and EMBER well. The PL/DB side of the formalism I can check but am not an expert in.

Computing feature-movement directions from an instrumented extractor is a useful idea for this field, and the counterexamples against Gimenez et al.'s defenses are convincing. However, the EMBER "guarantee" rests on sampled and fuzzed premises. The threat model does not cover two of the paper's own toolkit attacks or any code-level edit. The deployed system leaves an unmeasured, probably 10–25%, share of malware unprotected. And the attacks used for the comparative claims are weaker than published ones.

## 8. The one change

Evaluate the **deployed system end to end**: population check, monotone detector, and fallback detector. Use complete files, at full scale, with confidence intervals. Attack it with the strongest attacks available: MAB-Malware and GAMMA at published budgets, an adaptive attack that re-extracts candidates and may use the declined edits and LIEF layout rebuilds, and an attacker who tries to leave the population. If the composed system still shows a small detection cost and a low end-to-end evasion rate, I would move to Weak accept.
