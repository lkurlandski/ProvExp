# Meta-review: simulated CCS review of the body draft (2026-11-12)

Reviews: `reviewer-A.md` (formal methods), `reviewer-B.md` (adversarial malware), `reviewer-C.md` (robust and certified
ML), `reviewer-D.md` (systems security), all of the PDF at commit 82eea08. The meta-reviewer had the whole project:
the `.tex` sources with their comments, the code, the stored outputs under `artifacts/`, and `papers/`.

Tags: **[verified]** means checked against the manuscript, the code, a stored output or a paper in `papers/`;
**[inferred]** means reasoned but not checked, with what would settle it. Section, table and theorem numbers are the
compiled ones (`manuscript/main.aux`). File references are `file:line`. The `_x_*.tex` names are in `manuscript/`.

## 1. Executive summary

1. **Scores:** A Weak accept (confidence 3), B Weak reject (4), C Weak reject (4), D Weak accept (3). The two
   reviewers with the most confidence are negative, so the likely outcome is reject (at best a major revision). B, C
   and D each name the same single change that would raise their score.
2. **Top risk (R7):** the guarantee covers only the population, and files outside it go to an unconstrained detector
   that the attacks evade about half the time. Three reviewers make this their "one change". In the code I verified a
   sharper version that no reviewer could check: under `catalogue.precondition`, one data-directory entry that points
   past the end of the file takes any file out of the population. The certificate table is one such entry, and the
   loader does not map it.
3. **Second and third (R1, R2):** the attacks are weaker than published ones. MAB-Malware evades an EMBER-2024 GBDT on
   83% of files (Zainab et al.); our best attacks evade our unconstrained detector on 51-55%. The adaptive attack never
   applies the header-field overwrite: every such edit is declined, which I verified in every stored run. Separately,
   "sound" rests on premises that were tested, not proven, and the learned baselines get less information than the
   derivation (R18).
4. **Cheapest certain fix:** say what is classical in §3. All four reviewers say it. Abstract interpretation is in
   `main.bib` but never cited, and one of the two differences §6 claims over incremental parsing does not hold (R6).
5. **The single most important thing to fix:** evaluate the deployed, routed system end to end. Report the share of
   all attacked malware still detected, at a fixed false-positive rate for the system as a whole, including an
   attacker who first moves the file out of the population. Before that, audit which clauses of the population check
   a loader-safe write can trigger.

## 2. Meta-review

| Reviewer | Expertise | Score | Confidence | The one change they name |
|---|---|---|---|---|
| A | formal methods, PL, IVM, provenance | Weak accept | 3 | state the item map's locality as a hypothesis of Theorem 1; obtain the locating positions by a sound dependency analysis |
| B | adversarial ML for malware | Weak reject | 4 | the deployed system end to end, on complete files, at full scale, against the strongest attacks (MAB-Malware, GAMMA at published budgets, an adaptive attack that re-extracts and uses declined edits and layout rebuilds, an attacker who leaves the population) |
| C | robust and certified ML | Weak reject | 4 | the deployed system: an out-of-population policy, the sample-based checks moved to per-file checks at inference, robust TPR at a fixed system FPR against an attacker who starts outside or leaves; then equal-information baselines |
| D | systems security generalist | Weak accept | 3 | close the router hole and report end-to-end TPR at 1% FPR against an attacker who may choose an out-of-population starting file |

**Where they agree.**
- The idea is new in this community. B-S1 and D (§5) searched and found no prior work that derives direction
  constraints from an extractor's code, and C's search agrees. The PV counterexample is concrete and falsifiable (B-S3,
  D-S2). The cost analysis is the most useful result for practitioners (A-S3, B-S5, C-S4, D-S4).
- All four say the formal results are known techniques: Proposition 1 is the IVM delta rule, Theorem 1 is a
  sign-domain abstract interpretation, and Corollary 1 is Gimenez et al.'s Proposition 1 (A-W2, B-W5, C-W8, D-W7).
- All four say the EMBER guarantee rests on tested premises (A-W1, B-W1, C-W2, D-W1), that the population routing is
  a bypass (A-W4, B-W3, C-W1, D-W2), and that one instance does not support a claim about a class (A §6, B-W6, C-W7,
  D-W4).

**Where they disagree, and why.** A and D weigh what is new (the idea, the PV hole within Gimenez et al.'s own threat
model, the cost far below earlier monotone detectors) and treat the weaknesses as claims to scope. B and C judge the
paper as a security result. To them a guarantee that an attacker can step around, attacks below published strength,
and baselines given less information decide the verdict. B and C are also the reviewers closest to the work (both at
confidence 4), so their reading will dominate a PC discussion.

**Likely outcome:** reject, or a major revision where the venue offers one. **What would change it:** B, C and D state
conditions that fit within the full-scale run and the writing:
- the routed system evaluated end to end, after the escape audit (R7);
- MAB-Malware and an adaptive attack that covers the whole threat model (R1);
- adversarial training and PV given the same operations as the derivation (R18);
- a paragraph that names the classical parts of §3 (R6).

By their own statements, B and C would then move to weak accept and D to accept. A's condition (a sound dependency
analysis of pefile) is a research project in itself. Its affordable part, stating locality and the trusted base
explicitly (R2, R17), would likely hold A at weak accept or better.

## 3. The findings checked

Verdicts:
- *correct*;
- *partly correct*;
- *false premise* (the paper or the project says otherwise);
- *answered by the text* (the text answers it, but the reviewer missed the answer, so it may need to be easier to find);
- *preliminary-number artifact* (it would disappear at full scale or on the files below 4 MB);
- *settled* (out of scope by the authors' decision).

### Reviewer A

| ID | Verdict | Evidence |
|---|---|---|
| A-W1 | correct | Definitions 1-5 (`_d_framework.tex:39-186`) put no limit on the size of an item, so one item holding the whole input makes any mapping fit [verified]. The locality that §4.3.2 and Appendix D rely on (a write changes only the items it overlaps, unless it writes a position that locates items) is never stated (`_e_instances.tex:129-136`, `_j2_ember.tex:56-63`). On the multi-byte gap: the Rich-header search range is a whole-kind rule, and it was found by a crafted edit (a forged Rich block), not by single-byte flips (`docs/evidence/item-layer-design.md`, 2026-10-29, finding 1) [verified]. |
| A-W2 | correct | `cousot1977abstract` is in `main.bib` but cited nowhere. The comment at `_g_related_work.tex:2-3` claims it is "cited in the body where it is used"; it is not [verified]. §6's first claimed difference ("finds the items that an edit of raw elements changes", `_g_related_work.tex:100-101`) contradicts the paper's own sentence just before it, which says incremental parsing reparses around a raw edit (`_g_related_work.tex:93-95`) [verified]. |
| A-W3 (1) | correct | Theorem 1 (`_d_framework.tex:410-417`) is stated for any sum-then-readout extractor. The proof uses that "addition, the maximum, and the minimum are nondecreasing in each argument" (`_j_proofs.tex:69`), and the text concedes that other monoids would need a rule (`_d_framework.tex:110-112`) [verified]. |
| A-W3 (2) | correct for the general statement; no effect on EMBER | Table 1's caption carries the ratio rule's side condition, but Definition 10 and Theorem 1 do not [verified]. On EMBER the denominators reach 0 only when their numerators do, so the rule stays sound there (`docs/evidence/code-audit-sound-directions.md:16-19`) [verified]. |
| A-W3 (3) | false premise | EMBER 2024 appends a 0 to the lists of section entropies and size ratios before it takes the minimum (`src/provexp/featuresets/ember2024/features.py:1089-1104`). The "smallest" features are therefore 0 on every file, and the engine marks them fixed (`src/provexp/reach.py:914-918`). There is no sectionless-file hole. The text invites the inference: Appendix D says the pools are read "as 0 for a file without sections" (`_j2_ember.tex:17-18`), and Table 8 lists the smallest section entropy as monotone. |
| A-W4 | partly correct | (1) Correct: 1.5% of benign test files lie outside the population (`_f_evaluation.tex:334-335`), more than the 1% FPR the detectors are set to (`_f_evaluation.tex:42-43`). (2) Preliminary-number artifact: the 314/400 counts all files, the truncated ones included. On files below 4 MB, the pilot's attacked malware give 31/35 and the 2,000-file set gives 652/732 (`_f_evaluation.tex:339-341`) [verified]. (3) Settled (4 MB scope). (4) The GAMMA rebuild outside the threat model is reported (`_f_evaluation.tex:429-440`); packing and code-level edits are settled. |
| A-W5 | correct | Table 9 declines 8,050 of 62,604 edits overall, 5,739 of 7,428 DOS-stub overwrites, and every header-field overwrite (`_j2_ember.tex:102-103`). The adaptive attack's header-field candidate raises an error whenever a write is declined (`scripts/a1_adaptive.py:477-487`, `:536-548`), and the search skips it (`:821-824`). In every stored run (`a1/adaptive-beam/mfull`, `a_varied/adaptive-{pv,erdalt,advtrain}-best`), no chosen path contains a header-field edit [verified]. "Confirms the guarantee" (`_f_evaluation.tex:328-331`) is a check of the implementation. |
| A-W6 | partly correct | The counts are small (correct); scale comes with the full run (settled, seeds 0-2). The hand table is the authors' own (correct; R3). Running ERDALT's released code unchanged is settled: in session 41 the user decided to implement from the paper wherever the code breaks the guarantee. |
| A-W7 | partly correct | RS-Del and DRSM are in `papers/` but not in `main.bib` [verified]: positioning against them is needed. Verifying trees on the derived region is the exact-solver evaluation, which is settled (dropped). |
| A-Q1 | open | Answered by R2's mitigation. Dynamic taint gives the read set of one execution, not a proof over the population [inferred], so it would not turn "tested" into "proven" either. No multi-byte probe is on record. |
| A-Q2 | false premise | The minima are constant (A-W3 (3)). How many files in the population have no sections was not counted; nothing rests on it. |
| A-Q3 | open | No end-to-end number in the paper. Existing data give it for the toolkit: 41 of 50 still detected by the routed monotone detector on sums, against 21 of 50 for the unconstrained one (Table 5) [verified]. |
| A-Q4 | preliminary-number artifact | See A-W4 (2). Measured at scale; the value on files below 4 MB is about 89%. |
| A-Q5 | settled | Seeds 0-2, with the spread reported (R20). |
| A-Q6 | answered by the code, not the text | The beam search had no routing to the sums store (comment at `_f_evaluation.tex:403-404`); the "simpler search" is the union of two greedy runs. Declined: every header-field edit and 77% of DOS-stub edits. |
| A-Q7 | open (optional) | A rebuild operation is not settled; see R15. |
| A-Q8 | settled | As A-W6. |

### Reviewer B

| ID | Verdict | Evidence |
|---|---|---|
| B-W1 | correct | The three tested premises are quoted correctly (`_e_instances.tex:116-122`, `:146-147`; `_j2_ember.tex:60-63`) [verified]. The argument B says is missing (trust moves from about 2,568 × 12 per-feature judgments to per-kind declarations and parser read sets) is absent from the text and is the right answer (R2). |
| B-W2 | partly correct | (a) Correct, and reported: 36 of 288 outputs move features outside the table (`_f_evaluation.tex:432-434`). (b) Settled (code-level edits). B's inference that the counts over section bodies would become two-sided under in-place code rewriting is plausible [inferred]. (c) Correct: the body names operations but no attacker. |
| B-W3 | partly correct | The composed system is never evaluated (correct). The "contradiction" with 89% is a preliminary-number artifact (A-W4 (2)). 1.5% against a 1% budget is correct. Measuring complete files above 4 MB is settled. |
| B-W4 | correct | (a) Budget below published ones. A run at the GAMMA paper's budget exists and is reported (27/47 against 26/47, `_f_evaluation.tex:438-440`). (b) The adaptive attack is not stronger than the toolkit: 25/49 against 25/49, and 22/29 against 24/29 (Table 4) [verified]. (c) Declined edits are never explored (A-W5) [verified]. (d) Not independent, since candidates are scored with the same instrumentation; the 73,063 re-extracted edits and the planned MAB-Malware run are the independent evidence. (e) One round on 3,183 toolkit outputs. |
| B-W5 | correct | As A-W2. |
| B-W6 | correct | R4. |
| B-W7 | correct | The thresholds come from the benign *test* files (`_f_evaluation.tex:42-43`) [verified]. Table 4 mixes the full training set (unconstrained, adversarial training) with the 10% subsample (PV, ERDALT) (comment at `_f_evaluation.tex:225-230`) [verified]. The hand table is n = 1. |
| B-W8 | partly correct | (1) Gimenez et al.'s paper reports a 60-second timeout per attack (p. 10) [verified]. The 100 queries (population 10, 10 iterations) come from their released code (`scripts/a_pv_attacks.py:52-59`), so the text must say "their released code". (2) The ERDALT port is settled (A-W6); its detection gap is real (R19). (3) The text never says how a stub rewrite lowers their indicator: the edit restores the default stub (`docs/evidence/direction-A-expert-set.md:124-127`), and both evasions use rename. (4) `cortellazzi2025intriguing` is in `main.bib` but uncited [verified]. Pierazzi et al. do estimate gadget side effects in advance by injecting each gadget into a minimal app (p. 1340, App. F) [verified]; R5. |
| B-Q1 | settled / open | Complete files above 4 MB are settled; the end-to-end rate is open (R7). |
| B-Q2 | correct, and worse than asked | A data-directory entry past the end of the file fails `precondition` (`src/provexp/featuresets/ember2024/catalogue.py:453-457`) [verified]. Whether such a file still runs is [inferred]; see §5. |
| B-Q3 | partly settled | Lines of code and effort are settled out. Counts of the trusted parts (kinds, declarations, recorded rules) are allowed and should be given (R2). The pre-correction error count is in the evidence: three rules in the flip round plus four in the crafted-edit round (`docs/evidence/item-layer-design.md`, 2026-10-28 and 2026-10-29). No taint comparison was done. |
| B-Q4 | settled / optional | Code rewriting is settled; a LIEF rebuild operation is optional (R15). |
| B-Q5 | open | Needs the attack fix (R1). |
| B-Q6 | open (planned) | MAB-Malware is in the planned full run. |
| B-Q7 | settled | As A-W6. |
| B-Q8 | settled (scope), but a fair point | Within 4 MB this is measured. A detector monotone in raw counts scores larger files higher; one sentence in §7. |

### Reviewer C

| ID | Verdict | Evidence |
|---|---|---|
| C-W1 | correct, with one false premise | The routing, the 1.5% against 1%, and the evasion of an incomplete file are verified (`_f_evaluation.tex:333-338`). False premise: "the paper's own data show such files run". Being in the dataset does not show that a file executes. The one-field escape in §5 makes the point moot. |
| C-W2 | correct | Quotes verified. The per-file check at inference (C-Q5) is cheap and sound; see R2. |
| C-W3 | partly correct | §5.3's finding concerns the defender who learns from the attacks at hand, which is Gimenez et al.'s own protocol, and needs no equal information. But the paper's thesis sets computation against trial, and §5 never measures a systematic trial over the same twelve operations, although the 73,063 edits already form one. The "122 unconfirmed" are mostly not over-approximation: of the 142 features no toolkit output lowered, 75 are parser warnings, which the instance does not model and marks "both" by fiat (`artifacts/experiments/a_varied/coverage/features.csv`). About 20 of the 142 are witnessed, and the remaining modeled ones are about 48, 46 of them counts of strings matching a pattern [verified]. Of the eight hand-table errors, six would show up under random-content trial on the right files; the two Rich-header errors need a forged Rich block (Table 3; `item-layer-design.md`, 2026-10-29). |
| C-W4 | partly correct | The 36/288 is verified. Code-level edits are settled, but the wording "much harder to apply without breaking the program" (`_e_instances.tex:77-79`) is contested by Lucas et al. 2021, who preserve functionality through conservative disassembly [verified]. |
| C-W5 | partly correct | The positivity constraint is a soft l2 loss (Gimenez et al., Fig. 2 and the text below it), and their Proposition 3 assumes a finite set of perturbation vectors known at training [verified]. Their setup differs (1,033 adversarial examples, the dataset of their ref. [5], p. 10) [verified]. The paper measures how far the layer sits from the derived directions (90% of its weight), which is more than a restatement. Running the unmodified code is settled. |
| C-W6 | correct | Denominators, the sums detector attacked only by the greedy search, and two different "Unconstrained" rows are verified. Seeds are settled; timing is settled. Robust TPR is computable from existing data (R20). |
| C-W7 | correct | R4. Effort claims are settled; counts are allowed. |
| C-W8 | correct | As A-W2. |
| C-W9 | partly correct | The 4 MB scope is settled and stated once (`_f_evaluation.tex:24-27`), but the numbers must also be labeled where they appear. The interval on 89% is a preliminary-number artifact: the full run measures it on all attacked malware, and the 2,000-file set already gives 652/732. |
| C-Q1 | open | R7. |
| C-Q2 | partly answered by existing data | See C-W3 for the 142. The trial-table detector is not built (R18). |
| C-Q3 | open | R18. |
| C-Q4 | partly settled | The fraction of vectors with L(δ) < 0 is cheap and should be reported (R19). Unmodified code is settled. |
| C-Q5 | open (proposal) | R2. |
| C-Q6 | open | The full adaptive attack on the sums detector (R1). Code rewriting is settled. |
| C-Q7 | settled | Effort settled; transfer belongs in §7. |

### Reviewer D

| ID | Verdict | Evidence |
|---|---|---|
| D-W1 | correct | Each quoted phrase is verified. The fix (state the trusted base, quantify it in counts, condition the claims) fits decision 2. |
| D-W2 | correct; the 89% point is partly a misreading | The predicted 89% is over the attacked malware below 4 MB (31/35 in the pilot), not over 50, but the text gives no denominator (`_f_evaluation.tex:334`). |
| D-W3 | partly settled | Code-level edits and packing are settled. The gain share on fixed features is a cheap analysis and worth one sentence. The DLL flag carries 24% of the unconstrained detector's gain (`_f_evaluation.tex:263`). |
| D-W4 | correct | R4. Effort settled. Naming what falls outside the class (order-dependent features, learned embeddings, raw bytes) is not yet done. |
| D-W5 | correct | The paper's own assessment agrees (PLAN.md, "Where the paper stands": §5.2 is the weakest finding). The Severi paragraph already says "move", and the bucket argument covers "target". |
| D-W6 | partly correct | Gimenez et al. used 1,033 adversarial examples against 12,000 training malware (p. 10) [verified]. Ours: 3,183 outputs from 400 training malware, but the defenses sit on different training sets (R11). The donor-overlap control is a good, cheap check (R19). |
| D-W7 | correct | As A-W2. Timing is settled. |
| D-W8 | settled | Label the numbers as "on files below 4 MB" where they appear. |
| D-Q1 | correct, and worse than asked | B-Q2; §5. |
| D-Q2 | open (planned) | MAB-Malware is the planned out-of-table attack; code transformations are settled. |
| D-Q3 | partly answered by the evidence | Two correction rounds are on record (B-Q3). Malformed corpora were not tested. |
| D-Q4 | settled | No effort claims; no non-PE instance yet. |
| D-Q5 | answerable now / settled | The 11 features: the modified-DOS-stub flag (lowered by restoring the default stub), unknown sections and their information (by renaming an unknown section to a known name), and the info and size of `.text`, `.data`, `.rsrc` and `.rdata` (by renaming the section away). Both evasions use rename. Sandbox execution is settled. |
| D-Q6 | open (cheap) / out of scope | The gain share is cheap; temporal drift is not needed. |
| D-Q7 | open | The denominator; see D-W2. |
| D-Q8 | open (cheap) | Margins against the 1.57-logit drop, from stored scores (R3). |

## 4. The checklist

**1. The open risks of the 2026-11-02 register.**

| Risk | Raised by (unprompted) | Status now |
|---|---|---|
| R4 one instance | A §6, B-W6, C-W7, D-W4 | **Still open**, raised by all four but nobody's "one change". §2's "for a broad class of feature mappings" (`_c_background.tex:79`) also needs A-W1's caveat. |
| R5 Pierazzi's side effects | B-W8 (4) | **Changed.** The old misreading is fixed by `_c_background.tex:36-38`, which separates consolidation from φ's response. Two new points: §2 paraphrases "cannot be computed in advance" without Pierazzi et al.'s reason (Γ "cannot be expressed analytically in closed-form", p. 1336); and Pierazzi et al. themselves *estimate* side effects in advance by injecting each gadget into a minimal app, while noting that the side effects can differ from host to host (p. 1336, p. 1340). That estimate is the closest precedent to Proposition 1, and Proposition 1 is its exact, per-host version. |
| R6 known techniques renamed | A-W2, B-W5, C-W8, D-W7 | **Still open, now unanimous.** IVM and Gray et al. are cited; abstract interpretation and self-maintainability are not, and §6's incremental-parsing contrast is contested. |
| R9 what Proposition 1 enables | C-W6, D-W7 (timing), A-W5 (exactness), B-W4 (d) | **Still open, in another form.** No reviewer says that Proposition 1 has no finding; they ask for timing (settled out) or contest "exact". See item 5. |
| R11 every cell from the same detectors | B-W7, C-W6, D-W6 | **Still open, planned.** Table 4 mixes training sets, and the two "Unconstrained" rows differ. The full run's single protocol fixes it. |
| R15 packing and code rewriting | A-W4 (4), B-W2, C-W4, D-W3 | **Open, sharper.** C-W4 contests the wording against Lucas et al. 2021, and B-W2 (c) and D-W3 ask for the attacker to be named. The exclusion stays (settled); the wording and the attacker statement are writing. |
| R16 PE minutiae | nobody | **Resolved.** A-S2 and C-S2 praise the parser facts in §5.2, and D cites them as useful. |

**2. Attack strength.** Raised unprompted by B-W4 (all parts), A-W5, C-W6, D (§5, Kantchelian). Comparison with
published numbers [verified]:
- Zainab et al. report MAB-Malware at 83.4% evasion on an EMBER-2024 GBDT, at 0.1% FPR, with 50 hard-label queries,
  every evasion checked for executability.
- Our toolkit, counting a file evaded if any of the eight attacks evades it, reaches 26/47 (55%) on the
  unconstrained detector at 1% FPR; the adaptive attack reaches 25/49 (51%).
- The operating points differ: at 0.1% FPR the threshold is higher, and evasion is easier.

So our attacks are not the strongest available. Per claim:
- *Existence results* do not depend on attack strength, because a stronger attack can only add evasions: PV 4/9 by one
  rename, the expert set 2/8, and ERDALT 24/29 by its own training attack.
- *Comparative claims* do. "Adversarial training ... evades it about as often as before" (`_f_evaluation.tex:289-293`)
  rests on a single-round baseline and an attack that never uses header-field overwrites. The §5 lead's "stronger,
  white-box adaptive attack" (`_f_evaluation.tex:16`) is contradicted by Table 4.
- *The monotone rows' 0* follows from Corollary 1. The only independent evidence for them is out-of-table attacks: the
  GAMMA rebuilds (0 in the population) and MAB-Malware (planned).

My judgement: adequate for the existence findings, inadequate for the adversarial-training comparison and for any
reading of §5.4 as a defense result. MAB-Malware and the declined-edit fix are required (R1).

**3. The novelty of §3.** Raised by all four (A-W2, B-W5, C-W8, D-W7), and A-W1 adds that the class is universal.
My judgement, harsh but fair:
- Proposition 1 is IVM's delta rule for sums plus the known fact that maxima and minima need the kept multiset
  (self-maintainability).
- Theorem 1 is a one-step sign abstraction through monotone operators, and the induction under closure is standard.
- Corollary 1 is Gimenez et al.'s, as the paper says.
- Provenance appears only as the item table, which is cited as provenance semirings; A notes that the relevant notion
  is dependency provenance.
- What is new and defensible: the class as a modeling choice that real extractors meet bit for bit; computing the
  delta and the signature of a raw write from item tables and the positions that locate items; soundness over a
  population closed under the threat model, with closure and coverage made checkable; and the derived table as the
  missing input of the monotone-detector line (Incer et al., Gimenez et al., Chen et al.), computed for a full
  deployed feature set.
- The novelty of §3 lies in the modeling and in what it makes computable, not in the three statements. The paper should
  say this itself, before reviewers do (R6). Against the monotone-detector line, the difference is clear in §6 and
  praised (B-S1, D-S1).

**4. §2 against §5.** No reviewer quotes §2's closing sentence. B-W4 (b) contests "stronger", and D (§1) could not
write "a defender can now do X". My judgement: §2's "uses them to attack malware detectors and to build robust ones"
(`_c_background.tex:83`) is delivered for "build robust ones" (§5.4), and for "attack" only as an instrument aimed at
what a defense trusts. Reword §2 to promise what §5 shows: attacks aimed at what a defense trusts, and detectors no
edit in the threat model can lower (PLAN.md step 4). If the authors adopt R18's adversarial-training row, §2's
"problem-space defenses" line is also shown.

**5. Proposition 1's role.** Indirectly raised: C-W6 and D-W7 want timing, A-W5 contests "exact", B-W4 (d) calls the
attack circular. Nobody misses a finding outright. Answers that need no timing claim:
- (a) Pierazzi et al.'s minimal-app estimate of gadget side effects as the precedent. Proposition 1 gives the exact
  side effects on the actual host, which their attack approximated because exactness required extraction.
- (b) A count of work, not time: per candidate, the median number of items and sums the update touches against those
  of a full extraction; and in the adaptive attack, the candidates scored against the files written. This supports
  "does less work" without saying "is faster"; the authors should judge whether it stays within the timing rule.
- (c) If R18 is adopted, Proposition 1 is what makes problem-space adversarial training over the whole threat model
  cheap. That would be its finding.
- (d) One sentence that the direction of a sum (Definition 9's argument) is Proposition 1's decomposition applied to
  every edit at once.

**6. The corpus-checked signatures.** Raised by all four (A-W1, B-W1, C-W2, D-W1). A, the formal reviewer, calls the
honest statement a strength (A-S1) and scores weak accept, but makes "proven instead of tested" its one change. B calls
a certificate with sampled premises an empirical claim. My judgement: acceptable to a formal reviewer if (i) every
tested premise is listed in one place with its check, (ii) the claims carry the conditions, and (iii) the cheapest
premise becomes a per-file check (C-Q5): at inference, accept a file only if its item table uses no kind at an
overwritten position and no (kind, sum) pair outside the sample's vocabulary. Then the sample-coverage hypothesis holds
by construction for every file the detector accepts. Item (iii) adds one clause to the population check, so it touches
decisions 2 and 8: a proposal for the authors. The weaker link is not the sample but the locating-position record,
which needed seven rule fixes across two rounds before its checks passed (B-Q3). A targeted multi-byte probe is the
cheap strengthening (R2).

**7. §4's template.** Nobody comments on the template as a recipe. D-W4 asks "a method or a careful EMBER study?", and
C-W7 and B-W6 ask what another extractor costs. My judgement: the four-part lead (`_e_instances.tex:6-10`) is a recipe
on the page, but part (c) is described only in PE terms. A second domain would fit the template easily for flow
statistics (sums, pools, mean and standard deviation: C-W7) and presence bits (Drebin). §4 should state each part as a
question with the check that answers it, in one format-free sentence each, so that the template's reuse is visible
without a second instance.

**8. The population and the 4 MB scope.** Raised by all four (A-W4, B-W3, C-W1 and C-W9, D-W2 and D-W8). The routing
is the dominant concern of the whole review (three "one changes"). The 4 MB scope is accepted as a scope if the
numbers carry the label (C-W9, D-W8). B wants complete files above 4 MB, which is settled. My judgement: the 4 MB scope
is not a risk. The routing is the top risk, made sharper by the escape route in §5. The sentence "such files are rare
among benign software, and so stand out" (`_f_evaluation.tex:338`) is contradicted at the operating point and must go
(R7).

**9. The problem-space defense (decision 6's revisit).** Raised by all four: B-W4 (e), C-W3 and C §5, D-W6, A §5
(Lucas et al. 2024, Tsingenopoulos et al. as "natural baselines"). The literature [verified in `papers/` unless
marked]:
- Lucas et al. 2023 make adversarial training of raw-binary detectors practical by generating problem-space examples at
  scale; in the best case one attack's success fell from 90% to 5% (USENIX page, via search).
- Lucas et al. 2024 (CCS) train raw-binary detectors robustly without adversarial examples (GreedyBlock).
- Tsingenopoulos et al. 2024 harden a commercial dynamic-analysis model by RL-based problem-space adversarial training
  and reach 0% attack success after a few retraining iterations, against a defined set of capabilities.
- Dyrmishi et al. 2023 find that unrealistic hardening helps only partly against realistic attacks.
- Zainab et al. 2026 find hardening "highly attack- and model-dependent", often not transferring across attacks and
  sometimes increasing susceptibility to unseen ones.
- Found by search, abstract only: Kozák et al. (arXiv 2405.02646) harden an EMBER-feature GBDT with problem-space
  examples from RL attacks.

My judgement: yes, a reviewer expects the defender's alternative done properly: iterative, with the strongest attack
in the loop, at a realistic share of the training data. A single round on toolkit outputs is below that bar. I
recommend revisiting decision 6 in favor of option B(i): adversarial training on the adaptive attack's outputs over
all twelve operations, generated through Proposition 1, tested with the held-out MAB-Malware (R18). This is a proposal
for the authors. The plausible outcome is that adversarial training resists the attack in its loop and not a held-out
one. That supports §5.3, but it must be stated as a hypothesis before the run.

**10. MAB-Malware's absence.** Raised by B-W4 (a), C (§5, Zainab et al.) and D (D-W3, §5); A does not. B's weak reject
partly rests on it. My judgement: for §5.3 the existence results stand without it. For the adversarial-training
comparison and for §5.4's "beyond the guarantee", MAB-Malware is the only evidence a reader would accept as
independent: we did not write it, and it is the strongest attack on this feature set. Its absence is held against the
paper, and the planned run must include it. Hypothesis to state before it runs: MAB-Malware renames sections, so it
should find PV's rename hole; it should evade no monotone detector on a file in the population; any evasion outside the
table should be reported separately.

**11. §5's three findings.** Each lead answers its question (§5.2 `_f_evaluation.tex:83-88`, §5.3 `:196-203`, §5.4
`:314-321`). Reviewers judge the findings as follows:
- 5.3 is the strongest. B-S3 and D-S2 call it falsifiable and within Gimenez et al.'s own threat model, but C-W3
  challenges its information gap.
- 5.4's cost result is valued (A-S3, B-S5, C-S4, D-S4) but sits on the routing (R7) and on seeds (R20).
- 5.2 is the weakest, as D-W5, B-W7 and A-W6 say: the authors' own table, drops that never cross the threshold, and the
  expert set at 2/8.

My judgement agrees with the reviewers. 5.2 is weakest because its strongest evidence (the expert set) rests on 8
detected files, and its own-table evidence cannot produce an evasion by design. The full run's larger malware set and
the margin analysis (D-Q8) are the cheap help.

**12. The ports of PV, ERDALT and the expert set.** Checked against `papers/gimenez2025certifiably.pdf`.
- **PV** is fair: the same rule, "features with non-negative perturbation" with a monotone model (p. 10). Our
  monotone-GBDT PV has AUC .844 against their 86.7% on another dataset.
- **The expert set** is fair under their own criterion, "difficult to change for an attacker with no access to the
  malware source code", with "DOS stub modification" among its indicators (p. 4) [verified]. Rename and restoring the
  default stub need no source code. The text omits that we re-implemented their 40 features with two accumulation
  fixes (their code assigns per library and per section name, which makes 23 features lowerable even under additions)
  and that their DOS-stub flag is constant 1 under current LIEF (`docs/evidence/direction-A-expert-set.md:40-44`,
  `:69`). Gimenez et al. are likely reviewers and will see different numbers, so App. D needs one sentence on it.
- **ERDALT** follows their paper. The one change from their code is justified by their Proposition 3
  (`_j2_ember.tex:154-156`). Its detection is clearly weaker (AUC .883 against their 93.0%; it met the stopping
  criterion after one epoch), and the positivity constraint is a soft penalty. Report whether the training vectors
  satisfy it (R19).
- **The budget attribution** "100 queries per file, as in Gimenez et al." (`_f_evaluation.tex:52`) is wrong against
  their paper (60 s per attack) and right against their code (R21).

## 5. What the reviewers missed

1. **One field takes a file out of the population** [verified in code; loader behavior inferred]. `precondition`
   rejects a file if any data directory extends past its end, the certificate table included
   (`catalogue.py:453-457`). `plain_layout` also rejects a SizeOfImage larger than the sections need
   (`catalogue.py:426-428`). By the PE format specification, attribute certificates are not loaded into memory as part
   of the image. If the loader also ignores a certificate entry that points past the end (to check in documentation,
   not by execution), then any attacker sends any file to the unconstrained detector with one four-byte write. D-Q1
   and B-Q2 asked this; nobody could check it. This decides how severe R7 is.
2. **The adaptive attack never applies one of the twelve operations** [verified]. The header-field overwrite is
   declined on every file, because three of its fields lie in the Rich header's search range (`_j2_ember.tex:102-103`).
   The search skips declined candidates, and no stored run chose one. So "combines any operations of the full threat
   model" (`_f_evaluation.tex:56`) is false for that operation. This is also the operation behind the additions-only
   detector's 12/43 evasions, so the adaptive attack never probes the operation that matters most at the threat
   model's boundary. Reviewers A and B saw the declines but not this consequence.
3. **The derived-lowerable counts include features the instance drops** [verified]. §5.3's "928 of the 1,070" and
   "the other 142", and PV's hole of "124 ... 38.8% of the split gain" (`_f_evaluation.tex:233-251`), count the 88
   parser warnings. §4.2 drops these, and the derivation marks them "both" only because they are not modeled. Without
   them:
   - the toolkit outputs lower 915 of 982 modeled lowerable features;
   - about 48 modeled features are lowerable by the table but neither lowered nor witnessed;
   - PV's hole is 56 modeled features carrying 36.2% of the gain, plus 68 warnings carrying 2.7%.

   The finding survives; the counts need fixing before a careful reader (or C, whose C-W3 rests on them) finds it.
4. **Robust detection is already computable and favorable** [verified from Tables 4-5]. Counting the attacked malware
   (of 50) still detected after each attack column:

   | Detector | After the toolkit | After the adaptive attack |
   |---|---|---|
   | Routed monotone detector on sums | 41/50 | — |
   | Routed monotone detector on features | — | 41/50 (0 of 41 evaded) |
   | Adversarial training | 38/50 | 27/50 |
   | Unconstrained | 24/50 (Table 4) or 21/50 (Table 5) | 24/50 |
   | PV | 9/50 | 5/50 |
   | ERDALT | 5/50 | 7/50 |

   The metric answers C-W6 and part of R7. It must be reported per attack column, never as a union across searches
   (the user's rule).
5. **Appendix D describes the minima wrongly.** It says pools are read "as 0 for a file without sections"
   (`_j2_ember.tex:17-18`); in fact the minima are 0 on every file and the maxima are floored at 0 and include the
   overlay. This caused A-W3 (3) and will cause it again.
6. **Five works are in `main.bib` but cited nowhere**: `cousot1977abstract`, `cortellazzi2025intriguing`,
   `zainab2026breaking`, `kantchelian2016evasion`, `lucas2024training` [verified]. The comment at
   `_g_related_work.tex:2-3` is stale.
7. **The adaptive attack's predicted and real scores disagree on some kept files** for detectors that read the
   warnings: 12 files against the unconstrained detector, 25-28 against adversarial training, 8 against ERDALT, and 0
   against the monotone rows (`mismatches` in the stored outputs) [verified]. The likely cause is the warnings, which
   the prediction holds at the parent's values [inferred; `scripts/a1_adaptive.py:455-464`]. It is harmless, because
   kept files are re-extracted. But it answers B-W4 (d): prediction and extraction can differ, and the extraction
   decides.
8. **Closure can be argued from the record instead of only tested** [inferred]. An overwrite that writes no locating
   position cannot change which items the parser finds or where. So it cannot make a complete file incomplete, and
   closure needs testing only for declared operations and declined writes. This turns one tested premise into a
   consequence of another (R2).
9. **The thresholds are set on the test benign files**, and EMBER 2024 has a validation split (`{tr,vl,ts}` in the
   data path). B-W7 raised it; the fix costs nothing at scale.

## 6. Rejection-risk register

Ranked by likelihood × severity. R-numbers continue the 2026-11-02 register where a risk continues; new risks start at
R17. R10 (the keyed-count entry) is resolved by Table 7 and not listed.

| R# | Risk | Raised by | L | Severity | Mitigation | Type | Effort |
|---|---|---|---|---|---|---|---|
| R7 | **The routed system is a bypass.** Files outside the population go to an evadable detector; flagging them costs 1.5% FPR against a 1% budget; one field may move any file out (§5, item 1); the system is never evaluated end to end. | A-W4, B-W3, C-W1, D-W2; A-Q3, B-Q1, B-Q2, C-Q1, D-Q1 | H | **fatal** if a loader-safe one-field write leaves the population and the paper does nothing; otherwise major | (a) Escape audit (see note 1 below). (b) Where a clause is triggerable, one of three: redefine the operation so the clause is unnecessary (e.g., an add-section that never lowers SizeOfImage); or add the write to the threat model and keep closure by widening the population for that clause only, with the signature extended for the affected kinds (a targeted strict table, e.g., authenticode features under append); or canonicalize at inference (read a certificate entry past the end as absent). Each revisits the settled population decision for that clause only, so the authors decide. (c) Report the routed system end to end: still-detected share per attack at a fixed system FPR, including the escape attack (the escape write, then the fallback's strongest attack). (d) Replace "stand out" with a measured policy: e.g., the fallback at a stricter threshold, with system FPR held at 1%. Out-of-population status is itself a strong malware signal (about 11% of malware against 1.5% of benign). | analysis of existing data, new experiment, writing (+ scope change for the authors) | hours (audit, analysis), days (escape attack, re-derivation) |
| R1 | **The attacks are weaker than published, and the adaptive attack does not cover the threat model** (reopened). It is no stronger than the toolkit; it never applies header-field overwrites; the sums detector is attacked only by greedy search; its 0 on the monotone rows is not independent; MAB-Malware is absent. | A-W5, B-W4, C-W6, D (§5) | H | major | Run MAB-Malware held out against every detector at its published setting, reported separately, at 1% and 0.1% FPR. Let the adaptive attack re-extract declined candidates instead of skipping them. Run the full beam on the sums detector. Rewrite §5's lead without "stronger" and §5.4's "confirms the guarantee" as a check of the implementation. Compare budgets and rates with the GAMMA paper and Zainab et al. in one sentence. | new experiment, writing | days (compute) |
| R2 | **"Sound" rests on tested premises** (continues R2; the checks now exist, and their standing is the issue): the sample vocabulary, the locating-position record (single-byte flips plus crafted edits), closure. The trust argument is never made. | A-W1, B-W1, C-W2, D-W1; A-Q1, B-Q3, C-Q5, D-Q3 | H | major | One paragraph (end of §4.3.2 or §4.4) listing the trusted parts with their checks and counts: contribution functions (bit-exact), declared changes (re-extraction), the locating record (flips and crafted edits; number of recorded rules), the vocabulary (100 = 2,000 files), closure (0 of 56,902). No lines of code. Condition every "cannot be evaded". Argue closure for writes off locating positions from the record (§5, item 8). Run a targeted multi-byte probe: write known markers (MZ, PE, Rich/DanS, magic values) at every header and directory position, one sentence in App. D. Proposal: the per-file vocabulary check at inference (C-Q5). | writing, small experiment | hours to days |
| R18 | **Learned baselines get less information and weaker training than the derivation.** Toolkit-only observations (6 of 12 operations); a single round of adversarial training on 3,183 outputs; no systematic-trial competitor. | C-W3, D-W6, B-W4 (e), A §5; C-Q2, C-Q3 | H | major | Revisit decision 6 (option B(i)): iterative adversarial training on the adaptive attack's outputs over all twelve operations, on training malware, for at least two rounds. Rebuild PV from the same outputs. Build a *trial table* from the existing catalogue edits plus toolkit outputs, and a monotone detector on it. Attack all of them with the adaptive attack and MAB-Malware, with the hypothesis stated first. Report where the trial table differs from the derived one (content-triggered effects such as the forged Rich block; the about 48 unwitnessed modeled features). | new experiment | days to weeks of compute |
| R6 | **The formal results are known techniques** (continues). Abstract interpretation is uncited; §6's contrast with incremental parsing does not hold. | A-W2, B-W5, C-W8, D-W7 | H | major for A; cheap to fix | A paragraph in §3 (and its echo in §6) naming what is classical (IVM's delta rule; self-maintainability for pools, Mumick et al. 1997; sign-domain abstract interpretation, Cousot and Cousot; Gimenez et al.'s Proposition 1) and what is new (§4, item 3). Fix `_g_related_work.tex:96-101`: the remaining differences are pointers in binary formats (positions that locate items far from them) and the universal question over a threat model and a population. | writing | hours |
| R4 | **One instance for a claim about a class** (continues). | A §6, B-W6, C-W7, D-W4 | H | major | Scope claims "on EMBER" (the mock already says so). Replace §2's "broad class" with A-W1's caveat. Name what falls outside: order-dependent features, learned embeddings, raw-byte models. A second instance is the authors' call; if added, it must show readouts reproduced bit for bit, a non-trivial signature (pools, or positions that locate items), a derived table compared with constraints *published by others* in that domain, and the cost of a monotone detector. | scope reduction, or new instance | hours, or weeks |
| R20 | **The statistical design cannot rank defenses** (new): thresholds on test benign files, one seed, denominators of 8-9 files, no robust TPR. | A-W6, B-W7, C-W6, D-W5 | H | minor to major | Thresholds from the validation split. Seeds 0-2 with the spread for TPR at both FPRs and for the per-operation costs. Still-detected share per attack column. Enough attacked malware that PV and the expert set are judged on about 100 detected files or more, or with intervals. | new experiment (full run) | days |
| R11 | **Cells of one table come from different detectors** (continues). | B-W7, C-W6, D-W6 | H | minor (planned) | One training set and one attack protocol for every detector (Table 5's toolkit cells still come from the fixed-seed runs). | full run | — |
| R19 | **The ERDALT port may be judged weak.** AUC .883 against their 93.0%; one epoch; a soft constraint. | B-W8, C-W5, A-W6, D-W6; C-Q4 | M | major for §5.3's ERDALT paragraph | Train to a proper stopping point. Report the share of training and of test perturbation vectors with L(δ) < 0: if training vectors satisfy it and GAMMA-imports test vectors do not, the failure is the unseen-vector one the paper describes. Add a donor-overlap control (GAMMA imports with training donors). State their setup and ours in App. D. | analysis, small experiment | days |
| R3 | **The hand-analysis evidence is thin** (continues). The authors' own table; no drop crosses the threshold; 2/8. | B-W7, D-W5, A-W6; D-Q5, D-Q8 | M-H | minor to major | Margins against the 1.57-logit maximum drop (D-Q8). Present the own table as the illustration of *why it errs*, and let the expert set carry the measured claim on more detected malware. Name the 11 features and their edits. Say the expert set was re-implemented with the accumulation fixes. | analysis, writing | hours |
| R17 | **Theorem 1 is stated beyond its proof, and the class is universal** (new). | A-W1, A-W3 (1-2) | M | major for A | Add a sentence that any mapping fits with one whole-input item and that the results are informative when items are local. Add Theorem 1's hypothesis (additive sums and pools, or ordered monoids with a monotone operation). Carry the ratio's side condition in Definition 10, and say why it holds on EMBER. Add a locality sentence after Definition 8. Optional, for the authors: a definition and lemma for locality, which partly revisits the dropped requirements. | writing | hours |
| R15 | **The threat model's scope; no named attacker** (continues). | A-W4 (4), B-W2, C-W4, D-W3 | H | minor (exclusions settled) | Name the attacker: binary-only, structural edits, no recompilation, packing or code rewriting. Reword the code-level exclusion accurately against Lucas et al. 2021. Treat MAB-Malware as the out-of-table evidence. Report the monotone detector's gain share on fixed features. Optional: a rebuild operation whose declared changes come from the 36 outputs, at its measured cost. | writing, analysis | hours |
| R9 | **What Proposition 1 enables** (continues). | C-W6, D-W7, A-W5, B-W4 (d) | M | minor | §4, item 5 (a)-(d): Pierazzi et al.'s minimal-app precedent; a work count; adversarial training made cheap (R18); "exact given the delta, computed for X% of edits". | writing, analysis | hours |
| R5 | **Pierazzi et al. portrayed loosely** (continues, changed). | B-W8 (4) | M | minor to major if Pierazzi or Cortellazzi reviews | Quote their reason (Γ not in closed form); credit their minimal-app estimate of gadget side effects as the precedent; cite the TOPS 2025 version. | writing | hours |
| R21 | **Prior work misattributed or missing** (new). | B-W8 (1), C-W4, A-W7, B §5, C §5, D §5 | H | minor | Attribute the budget to their released code. Fix the Lucas et al. 2021 wording. Add a paragraph on certified defenses (RS-Del, DRSM, Gibert et al., Giri et al.): bounded byte edits or feature radius against our unbounded but typed edits. Cite Zainab et al., Kantchelian et al. and Calzavara et al. (verification of the model, not the extractor), Lucas et al. 2024, Tsingenopoulos et al. | writing | hours |
| R12 | **Counts mix modeled and unmodeled features** (continues R12, changed). | nobody | L-M | minor (integrity) | Recount 1,070, 928, 142 and 124 without the 88 warnings (§5, item 3). Check ERDALT's 90% the same way. | analysis | hours |
| R14 | **One operation is never validated or used** (continues R14, changed): header-field overwrites have no exactness row and are absent from the adaptive attack. | A-W5, B-W4 (c) | M | minor | Either restrict the operation to fields outside the Rich range (then it is predictable and usable), or re-extract it in the attack and state it. | small experiment | hours to days |
| R8 | **The expert-set comparison** (continues). | B-W8 (3), D-W5, D-Q5 | M | minor | Name the holes and edits. Quote their criterion. Keep the additions comparison first (done). | writing | hours |
| R13 | **Instrumentation effort** (continues; effort claims settled). | B-Q3, C-W7, D-W1, D-W4 | M | minor | Counts of the trusted parts (R2), "once per extractor", no lines of code or person-days. | writing | hours |
| R16 | **PE minutiae** (continues). | nobody | L | minor | Resolved; keep the parser facts in "why it errs". | — | — |

Notes:
1. *R7 (a), the escape audit.* For each clause of `precondition` and `plain_layout`, determine whether a one-field
   write triggers it and whether the loader accepts such a file. Answer from documentation (the PE specification, the
   loader's documented checks), not by execution (settled).
2. *A settled point that now looks fatal.* The population decision (files outside go to an unconstrained detector) is
   fatal only under one condition. If the escape audit shows that a loader-safe one-field write leaves the population,
   then every malware author has a free bypass, and no amount of in-population evidence answers B, C and D. The
   decision would then need revisiting for the triggerable clauses only (R7 (b)). If no such write exists, the decision
   stands, and R7 is answered by measurement and writing.

## 7. What the full-scale run must include

Ordered by how much each moves the verdict.

1. **The routed system, end to end (R7).** Before the run, the escape audit (documentation, hours). In the run:
   - the still-detected share of all attacked malware per attack column, at a system FPR of 1% and 0.1%, with the
     population check, the monotone detector and the fallback all included;
   - the escape attack (the triggering write, then the fallback's strongest attack), if a clause is triggerable;
   - the population share of attacked malware (replacing the 89%), with its denominator.
2. **MAB-Malware held out (R1, R15, R18).** Against every detector, reported separately from the toolkit and from the
   adaptive attack. At 1% and 0.1% FPR, so the rate can be set beside Zainab et al.'s. Evasions split by whether the
   output stays within the derived table (as §5.4 does for GAMMA). Hypotheses as in §4, item 10.
3. **The adaptive attack covering the threat model (R1, R14).** Re-extract declined candidates (header fields, DOS
   stub). Run the full beam on the sums detector. Record candidates scored against files written (R9).
4. **Equal-information learned defenses and a trial competitor (R18).** If the authors accept the revisit of decision 6:
   - iterative adversarial training on adaptive-attack outputs over all twelve operations (training malware, at least
     two rounds);
   - PV rebuilt from those outputs;
   - a monotone detector on the trial table built from the catalogue edits.

   All are attacked by the adaptive attack and by MAB-Malware.
5. **ERDALT (R19).** A proper stopping point, the L(δ) < 0 shares on training and test vectors, and the donor-overlap
   control.
6. **One protocol (R11, R20).** One training set for every detector. Thresholds from the validation split. Seeds 0-2,
   with the spread for TPR at both FPRs and the per-operation costs. Enough attacked malware that PV and the expert set
   have about 100 or more detected files.
7. **The recount on files below 4 MB, from stored outputs** (already an open item): closure, Table 9, Table 3's file
   counts, §5.1's edit counts, the coverage counts without warnings (R12).
8. **Cheap analyses, no runs.** The monotone detector's gain share on fixed features (D-W3). The hand detector's
   margins (D-Q8). The counts of trusted parts (R2). The multi-byte probe of the locating record, a short run (R2).

**Need not include:**
- code-level transformations or packing in the threat model (settled);
- files above 4 MB (settled);
- sandbox execution (settled);
- an exact solver or tree verification on the derived region (dropped);
- timing (settled);
- more than three seeds;
- independent human analysts writing hand tables (cost far above value; the published analyses carry the claim);
- taint tracking of pefile (a research project, and per-execution only);
- ERDALT's unmodified code (settled);
- a LIEF rebuild operation (optional, lowest priority);
- a second domain (the authors' call; it would strengthen §5.2-5.3 most, but no reviewer's verdict turns on it alone).

## 8. Writing actions

Ordered the same way. These are content changes, not wording.

1. **§5.4 "Where the guarantee holds"** (`_f_evaluation.tex:333-338`). Replace "such files are rare among benign
   software, and so stand out" with the end-to-end numbers and the result of the escape audit. Give the population
   share as n/N.
2. **The conditions of the guarantee in one place** (end of §4.3.2 or §4.4): the trusted parts, their checks and their
   counts. Then, throughout §5, replace "no edit ... can evade" with that statement's conditional form.
   - §5's lead: drop "stronger" (`_f_evaluation.tex:16`).
   - §5.1: say that header-field edits are declined (`_f_evaluation.tex:56`, `:73`), or fix the attack.
   - §5.4: the 0 drop is "a check of the implementation" (`_f_evaluation.tex:328-331`).
3. **§3 positioning and precision** (R6, R17):
   - the classical/new paragraph;
   - the universality sentence;
   - Theorem 1's hypothesis on the monoids;
   - the ratio's side condition in Definition 10;
   - one locality sentence after Definition 8 (`_d_framework.tex:346-349`).
4. **§6.**
   - Fix the incremental-parsing contrast.
   - Add a paragraph on certified malware defenses.
   - Position problem-space adversarial training: Lucas et al. 2023 and 2024, Tsingenopoulos et al.; Kozák et al.
     after reading it.
   - Add Zainab et al. as the attack benchmark, and Kantchelian et al. and Calzavara et al. as verification of the
     model rather than the extractor.
   - Cite Cortellazzi et al.
5. **§2.** Pierazzi et al.'s reason and their minimal-app estimate (R5). The closing sentence matched to §5 (PLAN.md
   step 4).
6. **§5.3.**
   - Counts without the warnings (R12).
   - The budget attributed to their released code.
   - ERDALT's constraint check (R19).
   - The share of adversarial examples in the training data, against Gimenez et al.'s 1,033 on 12,000.
7. **§5.2.**
   - The 11 expert features and their edits (restoring the default stub; renaming).
   - One sentence that their features were re-implemented with accumulation fixes and a byte comparison for the stub
     flag.
   - The hand table framed as the illustration of *why it errs*.
8. **§4.3.1.** Name the attacker. Word the code-level exclusion accurately (Lucas et al. 2021 preserve functionality
   through conservative disassembly; the exclusion is our scope, not their failure).
9. **App. D.**
   - The minima are constant zero (A-W3 (3)).
   - Why the header-field operation is wholly declined.
   - The record's correction rounds (flips, then crafted edits).
   - The expert-set re-implementation.

**The missing sections.**

- **Introduction.**
  - *Must establish:* the defender and the attacker (binary only, structural edits, no recompilation, packing or code
    rewriting); the gap (directions today come from hand analysis, trial, or observed attacks); the contribution as
    directions computed from the extractor and the three findings, with §3 placed against IVM, abstract interpretation
    and Gimenez et al.; the guarantee's conditions (population, closure, the trusted parts); and the end-to-end number
    of the routed system.
  - *Must not promise:* a guarantee for every file; robustness to packing or code rewriting; a state-of-the-art
    defense; speed; generality beyond what is built (say "on EMBER"; "a class" only with the universality caveat).
- **Discussion (§7).**
  - The routing as an attack surface, with the measured numbers and the escape audit's result.
  - Code-level edits, packing and layout-rebuilding tools, light and confident.
  - Maintaining an instance when the parser changes: a pefile upgrade can add an unrecorded rule (D, §6); the checks
    rerun.
  - What falls outside the class.
  - Raw counts and file size (B-Q8).
  - The 4 MB scope.
  - What instrumenting another extractor requires (the four parts of the template), with no effort claims.
- **Abstract.** One claim, its conditions, the three findings with one number each. Nothing about domains not built.
- **Ethics.**
  - Disclosure to Gimenez et al. of the PV rename hole and the expert-set holes before publication (B §6, C §6, D §6).
  - Every edit used is in public toolkits.
  - Malware is handled as data and never executed.
- **Open science.**
  - Release the instrumented extractor, the byte-level edit writers, the locating-position record with its checks, the
    derived tables, the attack code and the patched variants (import merge; expert-set accumulation).
  - The note already in the stub: on files below 4 MB the stock extractor reproduces the released vectors.
  - The guarantee can be audited only through this code, as all four reviewers say.

Sources found by search for this meta-review: [Lucas et al., USENIX Security 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/lucas);
[Tsingenopoulos et al., arXiv 2402.19027](https://arxiv.org/pdf/2402.19027); [Kozák et al., arXiv 2405.02646](https://arxiv.org/pdf/2405.02646v2).
Everything else was checked in `papers/` or the project.
