# Paper mock (rewritten 2026-11-09, after the holistic review; layout accepted provisionally by the user, to be judged
# once §4-5 are written)

At most two pages. It decides what the paper contains; what is not listed here stays out. Written against the
manuscript's new §3 and PLAN.md's "Decisions of 2026-11-09". "Measured" means a pilot-scale number exists; final
numbers need the scale-up (user's decision). The 2026-11-02 mock is in git history.

## Thesis

For sum-then-readout extractors (find the items of the input, fold their contributions into sums, compute each
feature by a readout over a few sums), the feature-space consequences of an attacker's edits are computed from the
instrumented extractor: exactly for one edit (Proposition 1), as a sound direction table for a whole threat model
(Theorem 1), and from that table, monotone detectors no edit in the threat model can evade (Corollary 1). Today this
knowledge comes from trial, from an analyst's reading of the extractor, or from observed attacks.

## Contributions

1. **The class and exact side effects.** Sum-then-readout extractors (items, sums in commutative monoids, readouts
   with a support), and Proposition 1: an edit's delta and the item table of the input give the features of the
   edited input exactly, before the edit is applied, re-evaluating only the readouts whose support a changed sum is in.
2. **Sound directions.** Signatures (the changes a threat model may make to each kind of item), the derived table
   (direction of each sum from the changes, of each feature from its readout's rule), Theorem 1 (sound over a
   population, and for sequences of edits when the population is closed), and Corollary 1 (monotone detectors).
   Format-free, with proofs.
3. **Instantiation, on EMBER.** A template any instance follows (§4), filled in for EMBER 2024: 2,480 of 2,568
   features modeled and reproduced bit for bit, three repairs, a catalogue of twelve operations from the public
   toolkits, and every edit's predicted features checked against extracting them again (0 wrong).
4. **What the computation buys.** The derived table corrects a careful hand analysis (eight errors, each witnessed by a
   real edit) and is sound where constraints learned from attacks are not; monotone detectors on it are evaded by no
   attack on files in the population, adaptive included, at 4-6 points of detection, where the learned defenses fall
   to the adaptive search.

## Outline and word budget (body about 11,000 words while drafting; CCS format)

| Section | Content | Words |
|---|---|---|
| 1 Introduction | last | 1,000 |
| 2 Background and Motivation | as drafted, adjusted to the alignment option the user picks (below) | 950 |
| 3 Measuring Edits Across Feature Mappings | as drafted (sum-then-readout extractors; edits and side effects; sound directions); finetuning only | 3,500 (now ~4,050) |
| 4 Instantiating the Framework | the template, EMBER in it (below); bookkeeping in an appendix | 1,000 |
| 5 Evaluation | organized by §3's results (below) | 3,200 |
| 6 Related Work | as drafted; "margins" and old terms fixed | 1,000 (now ~1,470) |
| 7 Discussion | what does not fit (global analyses, learned features), cost of instrumenting (no effort claims), other domains; limitation: code-level transformations are outside the threat models (decision 9) | 500 |
| Appendix | symbols, types, proofs; the EMBER details §4 points to; other domains, one section each, if added | — |

## §4 Instantiating the Framework (about 1,000 words; restructured with the user 2026-11-09, session 27)

The body keeps what a reviewer judges (how strictly EMBER fits the class, the threat model against the literature,
the population); the bookkeeping goes to an appendix (user: "Most of this is engineering and book-keeping material
... Its boring"). No "instances at a glance" table until a second domain exists.

- **Lead (~50).** The four parts an instance supplies (items, contributions, readouts; the features that do not fit;
  a threat model with its signature; the population), in one or two sentences. No checks in the lead.
- **4.1 EMBER and PE files (~170), its own subsection.** The paper's first mention of PE files and malware detection:
  what a PE file is (headers, section table, sections, import table, overlay), why EMBER (the standard benchmark for
  static malware detection; 2024 version), its feature groups, instrumented without changing what it computes.
- **4.2 EMBER as a sum-then-readout extractor (~300), parts (a) and (b) merged.** Paragraph 1: the gist of the
  accepted block-1 text (two families of items, the sums, every row of Table 1 occurs), closed by the one-sentence
  bit-exact check. Paragraph 2, qualitative: how strictly EMBER fits and what to do with features that do not:
  rewritable without changing a value (section size over file size, the library set), or with no items at all (the
  88 parser warnings: drop them or keep them as both; a monotone detector cannot read "both", so they coincide;
  absent from EMBER 2017/2018, VERIFY; dropping them costs nothing, run 126). The import-overwrite bug is not
  mentioned. One sentence on the re-encodings over sums (here or where §5 introduces the sums detector).
- **4.3 Threat model (~400, with the catalogue table).** Literature first: the edits the PE problem-space attacks use
  (a literature pass before drafting), our catalogue as the functionality-preserving edits that do not rewrite code,
  exclusions named (code-level transformations, which are harder to execute without breaking functionality; packing).
  Code-level transformations are a stated limitation (PLAN.md, decision 9). Declared changes (operations stated in items, and append) checked by
  re-extraction; in-place writes collected from item tables. Writes onto locating positions: Proposition 1 declines;
  the directions allow any change of that kind unless declared (rename, remove debug, remove signature). Corpus-
  collected, so checked rather than proven (decision 2): the writes' changes and the kinds' vocabulary; one sentence,
  the check in §5.
- **4.4 Population (~150).** Plain layouts, membership checked at inference, routing, closure (0 of 60,934). The 4 MB
  truncation stays for now (PLAN.md decision 8 (iv)).
- **Appendix, the EMBER instance.** The item kinds; a table mapping each row of Table 1 to EMBER's features; the two
  rewrites; the re-encodings; how the locating positions are recorded (single-byte flip check).

## §5 Evaluation, by §3's results (3,200 words)

| Subsection | Result | Table | Claims | Status |
|---|---|---|---|---|
| 5.1 Setup (300) | | | pilot scale, GBDT, 1% FPR, toolkit (seen / held-out) and adaptive attacks, every attacked file re-extracted | measured |
| 5.2 Side effects (700) | Prop. 1 | 3 | the instrumentation and the operations' changes are correct (73,063 edits, 0 wrong), and the instance abstains exactly where a write lands on a position the parser reads; combined edits exact. Not "Proposition 1 holds", which is exact by construction (decision 3) | measured |
| | | — | Prop. 1 used by an attack: the adaptive search scores 5,000 candidates per file without extraction, and evades the undefended model about as often as the best toolkit attack (25/49 vs GAMMA's 24/47, different training subsets; its real strength shows on the defended rows) | evasion measured; no timing (user, 2026-11-10: say the computation is smaller and can be faster, never measure or compare it) |
| 5.3 Directions (900) | Thm. 1 | 4 | every disagreement with the hand table is a hand error, witnessed; the hand detector loses soundness where the derived one keeps it; constraints learned from attacks certify nothing or only themselves; coverage and closure of the write operations' signatures checked on the corpus (100- and 2,000-file tables identical; 0 of 60,934) | measured |
| 5.4 Detectors (1,300) | Cor. 1 | 5 | 0% evasion on in-population files under every attack on the monotone rows, at 4-6 points of TPR; PV, ERDALT, adversarial training fall to the adaptive search (64-80%, 49%); the expert set is sound under additions but weak (29.1%) and has 11 holes under the full catalogue; what each operation costs (price list); the cost of deriving vs PV | measured, except the sums row's adaptive cell (greedy, not beam) |

The section headings name the claim, not the method (today: "Side Effects Are Exact" becomes something like "The
Instance Is Correct").

## §2 against §5: the four lines of work

§2 says four lines of work each need part of the reachable set. What §5 shows for each today:

| §2's line | What it needs | §5 shows it? |
|---|---|---|
| problem-space attacks | the point each candidate reaches | **Yes, partly**: the adaptive search scores by Prop. 1 (Table 5's adaptive column); its saving is not measured |
| feature-space attacks (constraints Ω) | constraints over features | **As constraints, not as an attack**: Table 4 and the learned-region check compare constraints; no feature-space attack runs on ours |
| problem-space defenses (adversarial training) | many points on many training objects | **No**: adversarial training is a baseline in Table 5, trained on toolkit outputs, not on points the framework produced |
| feature-space defenses (monotone, verified) | which way each feature can move | **Yes**: Table 5 (monotone); verified training only cited |

Options (both allowed by the user, decision 4):

- **A. Narrow §2 (no new runs).** Keep the four lines as the landscape, but say plainly that we evaluate three uses:
  the attack (scoring without extraction), the constraints themselves, and monotone detectors; adversarial training
  appears as the realistic alternative a defender would use, not as a use. (The per-candidate cost measurement was dropped, 2026-11-10.)
  Cost: §2 promises less; a reviewer may ask why adversarial training on computed points was not tried.
- **B. Show all four.** A plus two runs: (i) adversarial training on the adaptive search's outputs, produced through
  Prop. 1 (the problem-space defense made cheap); (ii) a feature-space attack (the exact tree solver already used for
  the learned region) inside the derived region on the unconstrained detector, against the evasions the problem-space
  search realizes. Cost: (i) is heavy (the adaptive search on hundreds of training malware; a 1,000-candidate budget
  would bring it down) and adds a row whose expected result (resists the toolkit, still falls to a fresh adaptive
  search, as the toolkit-trained row does) mostly repeats Table 5's point; (ii) is cheap but adds machinery.

**Decided (2026-11-09): A** (the per-candidate cost measurement dropped 2026-11-10); revisited at the next full review, which
also checks how much the literature values problem-space defenses (PLAN.md, decision 6). Reasons: The paper's strongest claims (Table 4, Table 5's
monotone rows) need no new runs, every line §2 keeps has a table behind it, and adversarial training already serves
as the defender's alternative. B(ii) is the one addition worth weighing if the review asks for the feature-space
side; B(i) costs most and argues least.

## Measured vs missing

- **Measured (pilot):** Tables 3-5 complete; closure; coverage across corpus sizes; price list; PV and ERDALT holes;
  expert set's 11 holes; the hand detector's soundness loss.
- **Missing, small:** the instances-at-a-glance
  table (assembly only); the sums row's adaptive cell (beam search cannot route to the sums detector yet; expected 0%).
- **Missing, user's decision:** the scale-up (seeds 0-2, full splits, more malware; the adaptive budget at 2,000
  files); a second toolkit for held-out attacks (MAB-Malware); other domains (later, appendix plus table rows).

## Dropped from the paper

Requirements R1-R5, footprints, margins, Theorems 2-3, the CTU-13 rows and Drebin as planned instances (any later
domain goes through the template), coupling, the region's tightness, a cost theorem, effort claims.
