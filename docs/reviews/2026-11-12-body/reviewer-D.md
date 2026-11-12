# Review D

**Paper:** "Bridging the Gap: A Closer Look at Adversarial Examples in the Problem Space" (placeholder title), CCS '27 submission
**Reviewer:** D (systems security generalist; adversarial ML is adjacent to my area, not in it)

Page numbers below are the printed PDF pages: p.4 = Prop. 1/§3.3, p.5 = Thm. 1/Cor. 1, p.6 = Table 2/§4.3, p.7 = §4.3.2–§5.1, p.8 = Table 3/§5.2, p.9 = Table 4/§5.3, p.10 = Table 5/§5.4, p.15 = App. D/Tables 9–10.

---

## 1. Summary

Many static malware feature extractors, EMBER among them, work in three steps. They find "items" in the file (bytes, strings, sections, imports, …), fold each item's contribution into running totals ("sums": counts, totals, max/min pools), and compute each feature from a few sums ("readouts": ratios, normalized bins, entropy, presence bits). The paper formalizes this shape as a *sum-then-readout extractor* (Def. 5) and draws two consequences:

- **Prop. 1.** Given an edit's item delta and an "item table" recorded during extraction, the edited file's features can be computed exactly without re-extracting. This is incremental view maintenance applied to features.
- **Thm. 1.** Given a *signature* (which kinds of item each operation of the threat model can add, remove or replace), the sign of every sum's change can be propagated through readout rules (Table 1). The result is a per-feature direction table (fixed/up/down/both). The table is sound over a population of files that the threat model cannot leave. Combined with a monotone classifier, it gives a detector that no edit in the threat model can push down (Cor. 1, which is essentially Gimenez et al.'s Prop. 1).

The instance is EMBER-v3 under a 12-operation threat model of structural PE edits drawn from the secml-malware and MAB-Malware toolkits (Table 2). The evaluation (§5) makes three claims:

1. Hand analyses get directions wrong. The authors' own hand table has 8 errors. 11 of the 40 features in Gimenez et al.'s expert set can be lowered by a section rename or a DOS-stub rewrite, and an adaptive attack evades that detector on 2 of 8 malware.
2. Defenses learned from observed attacks (PV, ERDALT, adversarial training) trust features that edits can lower. A single section rename evades PV on 4 of 9 malware.
3. A monotone LightGBM built from the derived table costs about 4 points of TPR at 1% FPR (about 10 at 0.1%) against the unconstrained model, and keeps far more detection than the 40-feature expert set.

The summary was easy to write; the draft is clear about what it does. What I could not easily write is the sentence "a defender can now do X, which was impossible before". The paper does not state its contribution that way, and the introduction will have to.

## 2. Strengths

- **S1. A useful, checkable reframing.** The point that R(z) is "determined by φ once T is fixed, and the feature mapping is code that the defender has" (p.2) is correct and under-exploited. Moving direction analysis from roughly 2,568 × 12 per-feature judgments to per-item-kind contributions plus a record of the positions that locate items is a real reduction of what a human must get right. The readout rules (Table 1; proofs in App. C) are simple and, as far as I checked, correct, including the ratio rule and the distinct-count rule. *Verified* against App. C.
- **S2. Concrete, falsifiable findings about published defenses.** PV (Gimenez et al.) trusts features of the entry section's name, and a single rename evades it on 4 of 9 detected malware, found within 50 candidates (§5.3, p.9). Among the 40 expert features, 11 are lowerable by edits that need no source code (§5.2, p.8). Gimenez et al. explicitly scope their expert set to "an attacker with no access to the malware source code" and list DOS-stub modification as something the set indicates. The critique therefore attacks the defense inside its own stated threat model, not a strawman. *Verified* against `papers/gimenez2025certifiably.pdf` §3. The leave-one-out experiment (Table 10) neatly shows a held-out-attack test vouching for a detector that a rename defeats.
- **S3. Results are checked against ground truth, not the paper's own model.** Every evasion is counted only after writing the file and re-extracting with EMBER's code (§5.1 "Checking results", p.7–8). The 73,063-edit validation (Table 9) reports exact/declined/wrong per operation, with zero wrong in the population. The parser-position record was fuzzed with single-byte changes, and the paper reports that the first round missed three rules (App. D, p.15). That candour is appreciated.
- **S4. The cost result, if it holds at scale, is notable.** Incer et al. reported about 13 points of detection lost from monotone classification with hand-picked features. Gimenez et al.'s monotone GBT on expert features reaches 76% AUC (their Table 1). Here the monotone detector on sums keeps 89.6% TPR at 1% FPR against 93.5% unconstrained (Table 5), on the full EMBER feature set. The per-operation ablation ("Where the cost lies", p.10) is the kind of analysis a practitioner needs to choose a threat model.
- **S5. Honest scoping inside the body.** Files outside the population, operations that rebuild the file layout (GAMMA via LIEF), and declined edits are all reported rather than hidden ("Beyond the guarantee", p.10; Table 9).

## 3. Weaknesses (ranked by severity)

### D-W1. "Sound" and "cannot be evaded" rest on empirical checks, and the paper's main contrast with trial partly collapses
**Location:** §4.3.2 (p.7), §4.4 (p.7), App. D "Positions that locate items" (p.15), Thm. 1 / Cor. 1 (p.5), and the framing on p.2 and in the authors' note ("from the instrumented extractor instead of being found by trial").

**Problem.** Theorem 1 is a correct conditional statement, but every premise it needs on EMBER is established by testing, not derivation:

- (a) The instrumentation equals the extractor: "Our tests confirm …", p.6.
- (b) The declared changes are right: "we check each declaration by applying edits", p.7.
- (c) The part of the signature read from item tables is complete: "rests on the sample rather than on a proof", p.7. The 100 and 2,000 files are drawn from the same distribution.
- (d) The population is closed: "Closure is checked rather than proven", p.7.
- (e) The record of positions that locate items is complete, established by fuzzing that had already missed three parser rules once (p.15).

None of this is unreasonable. It does mean the epistemic status of "no edit in the threat model can evade" is "no edit we found can evade, after a structured search". The paper's rhetoric on p.2 and in §5 ("trial is exact but answers only for the edits it tries") sets the method against exactly that.

The hand-table errors (Table 3) all come from parser facts. The derivation catches them only because (e) recorded the relevant positions, and (e) is itself built by trial.

**Why it matters.** This is the paper's central claim to novelty over "just run the edits". A security reader will ask what the trusted base is and how it fails. A missed parser rule silently makes the table unsound, exactly as a hand error does, and Cor. 1 then fails silently too.

**Fix.**
- State the trusted computing base explicitly: contribution functions, declared operation deltas, position record, population predicate. Quantify it (lines of code or rules) and contrast it with the hand table's 2,568 × 12 judgments. That is the honest and still strong version of the claim.
- Test (c) and (e) adversarially, not on in-distribution samples: malformed and edge-case PE corpora (e.g., Corkami-style test files, .NET, TLS callbacks, unusual resource trees, files with overlapping headers and sections).
- Report how many new parser rules a second fuzzing round found, if any.
- Replace "cannot be evaded" with "cannot be evaded, provided the instrumentation conditions in §X hold", and list those conditions.

*Verified* from the paper's own text (each quoted phrase above).

### D-W2. The fallback for out-of-population files is an unguarded bypass, and the paper waves it off
**Location:** §4.4 last paragraph (p.7); "Where the guarantee holds" (p.10); author note on the 89% placeholder.

**Problem.** Files outside the population go to the unconstrained detector, which carries no guarantee. That is where the single toolkit evasion of each monotone detector happened (p.10). The paper's answer is that such files "are rare among benign software, and so stand out". The deployed system as described does not use that signal, though. It routes these files to a model that the paper's own Table 5 shows is evaded on more than half of detected malware.

Closure (Thm. 1) protects against edits *in* the threat model moving a file out. It does not stop the attacker from starting from a binary outside the population. A malware author or crypter can easily emit a file whose headers point past EOF or have an unusual layout, then apply any edit.

On the numbers: 11% of malware against 1.5% of benign files are outside the population (p.10). Flagging out-of-population files as malicious would cost about 1.5% FPR, which exceeds the 1% budget the whole evaluation uses. So the obvious repair is not free, and the paper does not measure it.

The 89% placeholder also needs a stated denominator. 89% of the 50 attacked malware is not an integer, and 42 of 47 detected would be 89.4%. Whatever the value, the guarantee covers at most that share of malware *as found in the wild*, and an adaptive attacker can push it towards 0%.

**Why it matters.** For a security venue, an end-to-end system with a route an attacker can choose is not "robust to every edit in the threat model". It is robust for attackers who do not pick their starting point. This is the first thing I would raise in a PC discussion.

**Fix.** Evaluate at least one guarded fallback:
- (i) score out-of-population files with a monotone detector built for a conservative signature (all kinds "both" where completeness fails);
- (ii) send them to a stricter threshold or to dynamic analysis, and report end-to-end FPR/TPR with the population predicate included;
- (iii) extend the population, e.g., by modelling "incomplete" as an extra item kind.

Also run an adaptive attack that is allowed to make the starting file incomplete, for example by pointing a loader-ignored directory past EOF, and check whether such a header write is functionality-preserving. If the 89% comes out materially lower, say 70%, the paper's framing of the population as "nearly all files" must change. The design is sound either way, but the claim is not.

*Verified* (paper text); attacker feasibility *inferred*.

### D-W3. The threat model is narrow, and robustness outside it is not measured
**Location:** §4.3.1 (p.6), Table 2; "Beyond the guarantee" (p.10); Discussion (to be written).

**Problem.** The guarantee covers 12 structural operations. Packing and code-level transformations are excluded (p.6). Those are exactly what a competent adversary uses once structural edits stop working: Lucas et al. 2021 and 2023, Ling et al. 2024, MAB-Malware's full action set, and the attacks benchmarked in Zainab et al. 2026 (`papers/zainab2026breaking.pdf`). The monotone detector also leans heavily on features the threat model holds *fixed*, such as "is DLL", which carries 24% of the unconstrained model's split gain (p.9), and header fields not overwritten in place. Anyone who relinks or recompiles changes those features trivially.

The implicit adversary is therefore "an affiliate who holds only a binary and uses commodity PE editors". That is a coherent adversary and matches Gimenez et al.'s, but the paper never names or motivates it. It also does not measure whether the monotone detector is *worse* than the unconstrained one against out-of-model attacks. It might be: it has fewer usable features, and its reliance on fixed features may be brittle under recompilation.

**Why it matters.** The question "who would deploy this, against whom" decides whether 4–10 points of TPR is a good trade. If the detector falls to an off-the-shelf packer or code-transformation attack as easily as the baseline, the guarantee buys little in practice.

**Fix.**
- State the adversary explicitly, and say what pushing the attacker from structural edits to packing or code transformation buys the defender.
- Add an experiment with at least one out-of-model attack family, e.g., a Malware-Makeover-style code transformation, a packer, or the full MAB-Malware action set, comparing unconstrained and monotone detectors.
- Report the share of the monotone detector's split gain carried by *fixed* features.

*Inferred* (the experiment is absent; its outcome is unknown).

### D-W4. One instance does not establish a claim about a class of extractors
**Location:** §3.1 (p.2–3) and the note's claim that "many feature extractors used by security classifiers have one shape"; §4 opening (p.5: "Any new instance … needs to supply the same").

**Problem.** The framework is presented as general, but it is instantiated on EMBER, plus Gimenez et al.'s 40-feature extractor, which is also PE. The general part (Prop. 1, Thm. 1) is elementary. The hard, format-specific part is the signature for position-defined overwrites, the population predicate, and the record of positions the parser reads, and the paper never states its effort or reusability.

There is also no characterization of what falls *outside* the class. Raw-byte models (MalConv and its descendants, including the ExeFormer-style structured byte models in `papers/kurlandski2027dont.pdf`) are outside it. So are CFG and graph features, opcode-sequence features with order dependence, and learned embeddings. Features whose contribution depends on context (EMBER's section-size/file-size ratio needed rewriting, App. D) need manual surgery.

**Why it matters.** My question as a generalist: is this a method or a careful EMBER study? Both are publishable, but the claims differ.

**Fix.** Either add a second instance in a different format, e.g., Drebin/Android manifests, Hidost or PDFrate features for PDF, or a flow-feature extractor (CICFlowMeter-style) for network traffic, and report instrumentation effort for both. Or narrow the claim to PE/EMBER and present the class as a design principle with a short argument about which other extractors fit. Report the effort for EMBER in any case: lines of code, person-days, how many rules the position record has.

*Verified* (one instance in the paper); effort *inferred* as nontrivial from App. D.

### D-W5. The security consequence of hand-analysis errors is shown mostly on single-digit counts or not at all
**Location:** §5.2 "What the error costs" (p.8), "Gimenez et al.'s expert set" (p.8), "Severi et al.'s hashed features" (p.8).

**Problem.**
- **The authors' own hand table.** It was written by the authors "before the derivation existed" (p.8), so it is an unverifiable baseline, and its errors drive no evasion: "No drop crosses the threshold" (p.8).
- **The expert set.** The evidence is 2 evasions out of 8 detected malware.
- **Severi et al.** The comparison is a category mismatch. Severi et al. needed to *set* a feature to a specific watermark value, consistent with dependencies (I verified the quoted sentence in `papers/severi2021explanation.pdf`, §4). Showing that 1,430 hashed features can be *moved* does not establish that they were wrong about setting values precisely, although the bucket-targeting argument on p.8 goes some way.

The authors' note says the numbers will be rerun at scale, but the *design* of the hand-table experiment cannot show an evasion when detected malware score far above threshold.

**Why it matters.** Claim 1 of §5 ("hand analyses get directions wrong, and a published detector built on one falls") carries the paper's motivation. At present it rests on 2/8.

**Fix.**
- Report, for the hand-table detector, the distribution of each malware's margin above threshold against the achievable score drop. Also report the evasion rate on malware whose margin is below the maximum drop, or at a threshold calibrated so the population includes near-threshold samples.
- Have independent analysts (not the authors) produce hand tables. Two would do, to show that the errors are not idiosyncratic.
- Name the 11 expert features and the edit lowering each. In particular, is the DOS-stub indicator lowered by *restoring* a standard stub on malware that already had a modified one?
- Reword the Severi paragraph to say "move", not "control".

*Verified* (counts and quote); independence concern *inferred*.

### D-W6. Baselines from prior work are reimplemented at reduced scale, which may understate them
**Location:** §5.3 (p.9), Table 4, App. D "ERDALT" (p.16).

**Problem.**
- PV, ERDALT and adversarial training are all learned from 3,183 adversarial examples on 400 training malware. ERDALT is a reimplementation with a modified output layer. Its failure to GAMMA imports (24/29) is attributed to never having seen the benign *test* files' imports. That is a training-data coverage issue as much as a design flaw.
- The "adversarial training" baseline is retrained only on toolkit outputs, not with a problem-space adversarial-training method such as Lucas et al. 2023.
- Training-set size differs across tables. Table 4's unconstrained model is "trained on the full training set" (p.10) and reaches .998 AUC with 25/49 evaded; Table 5's 10%-subsample model reaches .996 with 26/47. It is not stated which size each defense used. This is a design choice that will persist after the rerun, not a preliminary-number artefact.

**Why it matters.** Claim 2 ("defenses built from observed attacks fall") is a statement about a class of defenses. It must not depend on starving them.

**Fix.**
- Train PV and ERDALT at the scale Gimenez et al. used, or justify the 400-malware choice.
- Show that ERDALT's GAMMA-imports failure persists when the donor pool overlaps.
- Add a stronger adversarial-training baseline that also sees rename-style edits, to show that the gap is "operations not tried" rather than "too few examples".
- Use one training-set size for all detectors that are compared directly.

*Verified* (setup text); impact *inferred*.

### D-W7. The formal contribution is thin relative to its presentation
**Location:** §3.1–3.3 (p.2–5), App. B (p.12–13).

**Problem.** Prop. 1 is the homomorphism property of a fold over a free commutative monoid, which the paper itself identifies with incremental view maintenance [13,18]. Thm. 1 is sign propagation through monotone operators: a sign-domain abstract interpretation, a framing the paper does not use. Cor. 1 is Gimenez et al.'s Prop. 1 (acknowledged, p.14).

Monoids, tagged unions and folds (App. B) make the elementary look deep and slow down a security reader who is not a PL or database person. The novelty lies in the instantiation (positions that locate items, declining edits that write them, the population predicate) and in the empirical findings, not in the theorems.

Prop. 1's claimed efficiency ("can also be cheaper than extracting them", p.4) is never measured, although it is what makes the 5,000-candidate adaptive attack practical.

**Why it matters.** Reviewers in my position will discount a paper that presents its theory as the main contribution when the real contribution is engineering plus security findings.

**Fix.**
- Position Thm. 1 explicitly as sign-domain abstract interpretation of the extractor and cite that literature, e.g., Calzavara et al.'s abstract-interpretation verification of tree ensembles (ESORICS'20) as the nearest use in security ML.
- Move the algebra to the appendix.
- Lead with what the instance required that the theory does not give you.
- Report the extraction-time speedup of Prop. 1 over re-extraction.

*Verified* (paper text).

### D-W8. Scope: excluding files above 4 MB
**Location:** §5.1 (p.7), author note.

**Problem.** The restriction drops 26% of malicious and 6% of benign test files. The guarantee is per-file and unaffected, but the reported TPR, the population share, and the cost of robustness describe only files under 4 MB. Large files are disproportionately installers, files with big overlays and resource-heavy binaries, which is precisely where append and overlay features matter. The truncation in the earlier run also likely made large files "incomplete", inflating the out-of-population count. The rerun should fix that.

**Fix.** State the TPR and the cost of robustness as "on files under 4 MB". If a full copy of the dataset is obtainable, report the population share and cost on large files, even on a small sample. *Verified* (percentages from p.7); composition of large files *inferred*.

## 4. Questions for the authors

- **D-Q1.** What is the end-to-end TPR/FPR of the system *including* the router (D-W2) if out-of-population files are (a) sent to the unconstrained model, (b) flagged, or (c) sent to a conservative monotone model? Can an attacker turn an in-population malware into an out-of-population one by a functionality-preserving edit outside your 12 operations, e.g., a data-directory entry pointing past EOF?
- **D-Q2.** How does the monotone detector compare with the unconstrained one against at least one out-of-model attack (code transformation, packer, or the full MAB-Malware action set)? Is it worse?
- **D-Q3.** List the trusted assumptions of the EMBER instance (D-W1). How large is each (rules, lines of code)? Did a second fuzzing round over the position record find anything? Did you test on deliberately malformed PE corpora?
- **D-Q4.** What does instrumenting EMBER cost, in person-days and lines of code? Have you instrumented any non-PE extractor, even partially?
- **D-Q5.** Which 11 expert-set features are lowerable, and by what edit each? Were the 2 adaptive evasions verified to run (functionality preserved), e.g., in a sandbox?
- **D-Q6.** What share of the monotone detector's split gain lies on features the threat model holds *fixed*? How does the detector degrade under temporal drift (EMBER2024 test split by month) compared with the unconstrained model?
- **D-Q7.** What is the denominator of the 89% (D-W2)? Is "the malware we attack" all 50, or the detected ones?
- **D-Q8.** For the hand-table detector, how many detected malware have a threshold margin smaller than the maximal achievable drop (1.57 logits)?

## 5. Related work to cite or position against

The paper's descriptions of Pierazzi et al., Gimenez et al., Incer et al., Chen et al. (2020, 2021), Severi et al. and Dyrmishi et al. are accurate as far as I checked (*verified* for Gimenez, Incer, Severi against `papers/`).

Missing or under-positioned:

- **Kantchelian, Tygar, Joseph, "Evasion and Hardening of Tree Ensemble Classifiers" (ICML'16; `papers/kantchelian2016evasion.pdf`).** Exact evasion of GBT ensembles by MILP. This is the natural strongest feature-space adversary for your LightGBM detectors, and could replace the heuristic beam search as the check of Cor. 1 on the "Monotone, sums" model, which today is checked only with "a simpler search that appends and adds sections" (p.10).
- **Calzavara, Ferrara, Lucchese, "Certifying Decision Trees Against Evasion Attacks by Program Analysis" (ESORICS'20).** Abstract interpretation for evasion robustness of tree models. It is the closest security-ML use of the abstraction your Thm. 1 performs. The difference is that they abstract the *model* under a feature-space threat model, while you abstract the *extractor* under a problem-space one. Say so.
- **Certified defenses for byte-level edits:** RS-Del (Huang et al. 2023, `papers/huang2023rs.pdf`), DRSM (Saha et al. 2024, `papers/saha2024drsm.pdf`), Gibert et al.'s certified defenses against patch/append, and Giri et al., "Towards Certified Malware Detection" (arXiv 2604.20495, April 2026). These give probabilistic certificates against bounded byte edits for raw-byte or EMBER-feature models. Your guarantee is deterministic and unbounded in edit size but restricted to typed operations. That is a meaningful difference the paper should state, since a reader will ask "why not randomized smoothing?".
- **Bostani et al. (TOPS 2025, cited as [3]) and Sheatsley et al. (CCS'21, cited [25]).** Cited correctly. The distinction to make crisper is that learned constraints admit unsound exclusions while derived ones may admit unreachable vectors. You say this on p.11; it belongs in the introduction.
- **Lucas et al. 2021 and 2023, Ling et al. 2024 (cited).** Cited only as excluded. They must be positioned as the attacks the guarantee does not cover (D-W3), ideally with an experiment.
- **Zainab, Dyrmishi, Bostani, Cordy, Cavallaro, "Breaking Windows Malware Detection" (arXiv 2609.34456, Sept. 2026; `papers/zainab2026breaking.pdf`).** A unified evaluation of nine problem-space attacks on Windows detectors. It finds that hardening does not transfer across attacks and that two attacks cover about 99% of adversarial examples, which supports your §5.3 thesis. It is also an obvious source of out-of-model attacks for D-W3.

I found no prior work that derives feature-space direction constraints from an extractor's code. The search was web plus `papers/`, and is *not exhaustive*. On novelty I would rate the idea new in this community, with elementary machinery.

## 6. What the missing sections must establish

- **Introduction.** Name the adversary (a binary-only affiliate with commodity PE editors) and the user (a vendor shipping a feature-based static detector). Name the new capability: a direction table for thousands of features, and monotone detectors built from it, whose correctness depends on a small, auditable set of instrumentation assumptions rather than on per-feature human judgment or attack coverage. Claims must be scoped to "sound given the stated instrumentation assumptions" (D-W1) and, unless a second instance is added, to PE/EMBER (D-W4).
- **Discussion (§7).** Treat the out-of-population route as an attack surface, not a footnote (D-W2). Measure, or at least bound, behaviour against packing and code transformations (D-W3). Explain how the instrumentation is maintained when EMBER's parser (pefile/LIEF) changes, since a library upgrade can silently add an unrecorded parser rule. Discuss the large-file exclusion (D-W8).
- **Ethics.** The paper publishes a working evasion of a published defense (single rename against PV) and a hash-bucket targeting procedure. State disclosure to Gimenez et al. and note that the edits are already in public toolkits.
- **Open science.** Release the instrumented extractor, the position record, the fuzzing harness, and the derived tables. The guarantee's credibility rests on others being able to re-run the D-W1 checks.

## 7. Score

**Weak accept.** Confidence: **3** (systems-security generalist; I checked the formal parts and the comparisons with prior work, but I am not a malware-ML specialist).

Deriving per-feature directions from an instrumented extractor is a sensible, new idea in this community. It already exposes real holes in a published defense (PV evaded by a single rename, within its own threat model), and it gives a monotone EMBER detector at a cost far below prior monotone approaches. My score is held at weak accept rather than accept for three reasons. "Sound" rests on empirically checked instrumentation assumptions that the paper presents as a contrast with trial. The out-of-population route is an unguarded bypass. And the evidence for the class-level and hand-analysis claims rests on one format and single-digit counts. I would move to weak reject if the rerun shows the monotone detector markedly worse than the baseline against out-of-model attacks, or if the router cannot be guarded within a reasonable FPR.

## 8. The one change

Close the router hole and show the end-to-end number (D-W2). Evaluate the complete deployed system, population check included, with a guarded treatment of out-of-population files, against an adaptive attacker who may also choose an out-of-population starting binary. Report end-to-end TPR at 1% FPR. If the guarantee survives that with a modest cost, I would argue for acceptance.
