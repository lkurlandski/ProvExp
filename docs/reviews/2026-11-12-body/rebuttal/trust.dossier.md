# Dossier: R2

Cut from `/home/lk3591/Documents/code/ProvExp/docs/reviews/2026-11-12-body/` by `docs/reviews/process/dossier.py`. Facts tagged [verified] in the meta-review are taken as established.

## R2

### Register row (meta-review §6)

| R# | Risk | Raised by | L | Severity | Mitigation | Type | Effort |
|---|---|---|---|---|---|---|---|
| R2 | **"Sound" rests on tested premises** (continues R2; the checks now exist, and their standing is the issue): the sample vocabulary, the locating-position record (single-byte flips plus crafted edits), closure. The trust argument is never made. | A-W1, B-W1, C-W2, D-W1; A-Q1, B-Q3, C-Q5, D-Q3 | H | major | One paragraph (end of §4.3.2 or §4.4) listing the trusted parts with their checks and counts: contribution functions (bit-exact), declared changes (re-extraction), the locating record (flips and crafted edits; number of recorded rules), the vocabulary (100 = 2,000 files), closure (0 of 56,902). No lines of code. Condition every "cannot be evaded". Argue closure for writes off locating positions from the record (§5, item 8). Run a targeted multi-byte probe: write known markers (MZ, PE, Rich/DanS, magic values) at every header and directory position, one sentence in App. D. Proposal: the per-file vocabulary check at inference (C-Q5). | writing, small experiment | hours to days |

### Meta-review verdicts (§3)

| ID | Verdict | Evidence |
|---|---|---|
| A-W1 | correct | Definitions 1-5 (`_d_framework.tex:39-186`) put no limit on the size of an item, so one item holding the whole input makes any mapping fit [verified]. The locality that §4.3.2 and Appendix D rely on (a write changes only the items it overlaps, unless it writes a position that locates items) is never stated (`_e_instances.tex:129-136`, `_j2_ember.tex:56-63`). On the multi-byte gap: the Rich-header search range is a whole-kind rule, and it was found by a crafted edit (a forged Rich block), not by single-byte flips (`docs/evidence/item-layer-design.md`, 2026-10-29, finding 1) [verified]. |
| A-Q1 | open | Answered by R2's mitigation. Dynamic taint gives the read set of one execution, not a proof over the population [inferred], so it would not turn "tested" into "proven" either. No multi-byte probe is on record. |
| B-W1 | correct | The three tested premises are quoted correctly (`_e_instances.tex:116-122`, `:146-147`; `_j2_ember.tex:60-63`) [verified]. The argument B says is missing (trust moves from about 2,568 × 12 per-feature judgments to per-kind declarations and parser read sets) is absent from the text and is the right answer (R2). |
| B-Q3 | partly settled | Lines of code and effort are settled out. Counts of the trusted parts (kinds, declarations, recorded rules) are allowed and should be given (R2). The pre-correction error count is in the evidence: three rules in the flip round plus four in the crafted-edit round (`docs/evidence/item-layer-design.md`, 2026-10-28 and 2026-10-29). No taint comparison was done. |
| C-W2 | correct | Quotes verified. The per-file check at inference (C-Q5) is cheap and sound; see R2. |
| C-Q5 | open (proposal) | R2. |
| D-W1 | correct | Each quoted phrase is verified. The fix (state the trusted base, quantify it in counts, condition the claims) fits decision 2. |
| D-Q3 | partly answered by the evidence | Two correction rounds are on record (B-Q3). Malformed corpora were not tested. |

### Meta-review §5, item 8 (what the reviewers missed)

8. **Closure can be argued from the record instead of only tested** [inferred]. An overwrite that writes no locating
   position cannot change which items the parser finds or where. So it cannot make a complete file incomplete, and
   closure needs testing only for declared operations and declined writes. This turns one tested premise into a
   consequence of another (R2).

### Reviewer passages cited

- **A-Q1.** Can you state the locality property of π that Section 4.3.2 relies on, and prove signature coverage from it? How would you establish the locating-position record soundly (for example by taint tracking in the parser) rather than by single-byte fuzzing? Did any multi-byte probe find dependencies the single-byte probe missed?

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

- **B-Q3.** How large is the trusted base of the EMBER instance: number of item kinds, declarations, parser read rules, and lines of instrumentation? How many errors did the instrumentation have before the fuzzing round? Did you compare the fuzzed read-set record with dynamic taint tracking of the parser? (B-W1)

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

- **C-Q5.** Can the sample-derived part of the signature, and the locator record, be checked per file at inference? If so, why not make that part of the population test?

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

- **D-Q3.** List the trusted assumptions of the EMBER instance (D-W1). How large is each (rules, lines of code)? Did a second fuzzing round over the position record find anything? Did you test on deliberately malformed PE corpora?

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

## Register notes (meta-review §6)

Notes:
1. *R7 (a), the escape audit.* For each clause of `precondition` and `plain_layout`, determine whether a one-field
   write triggers it and whether the loader accepts such a file. Answer from documentation (the PE specification, the
   loader's documented checks), not by execution (settled).
2. *A settled point that now looks fatal.* The population decision (files outside go to an unconstrained detector) is
   fatal only under one condition. If the escape audit shows that a loader-safe one-field write leaves the population,
   then every malware author has a free bypass, and no amount of in-population evidence answers B, C and D. The
   decision would then need revisiting for the triggerable clauses only (R7 (b)). If no such write exists, the decision
   stands, and R7 is answered by measurement and writing.

