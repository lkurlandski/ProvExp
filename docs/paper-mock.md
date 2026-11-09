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
| 4 Instantiating the Framework | the template, EMBER in it (below) | 1,250 |
| 5 Evaluation | organized by §3's results (below) | 3,200 |
| 6 Related Work | as drafted; "margins" and old terms fixed | 1,000 (now ~1,470) |
| 7 Discussion | what does not fit (global analyses, learned features), cost of instrumenting (no effort claims), other domains | 500 |
| Appendix | symbols, types, proofs; the EMBER details §4 points to; other domains, one section each, if added | — |

## §4 Instantiating the Framework (1,250 words)

- **Opening, format-free (150).** What an instance supplies to §3: the item map, contributions, and readouts; a
  threat model whose operations have signatures; a population with a membership check. Then the four parts, each
  stated in §3's terms before EMBER fills it in. EMBER is one paragraph of introduction here.
- **(a) Items, sums, readouts (300).** EMBER's kinds, its three monoids, its readout forms (which rows of Table 1
  occur); the check that the readouts reproduce the extractor bit for bit (2,000 files, 2,480 features; the 88 parser
  warnings are the features outside the class). The re-encodings over sums (raw counts, signed buckets split, ...)
  as identity readouts a detector may read instead of the features (shortened from today's §4.3).
- **(b) Outside the class, and repairs (250).** Contributions that are not self-contained: section size over file
  size and the library set (value-preserving repairs), the duplicate-descriptor import overwrite (patched as a pure
  addition; every row runs on the patch).
- **(c) Threat model and signatures (350, with Table 2, the catalogue).** Twelve operations, three nested threat
  models. Operations stated in items declare their changes. Operations stated as writes get theirs from the instance's
  record of the positions the parser reads to find each kind of item; the instance declines to predict a write that
  lands on one. Their signatures are collected from the corpus's item tables, so Theorem 1's coverage hypothesis is
  checked on the corpus, not proven: one sentence here, the check in §5.2 (decision 2). Edits written by our own
  byte-level code.
- **(d) Population and membership (200).** Plain layouts (1,674 of 2,000 files); the detector checks membership at
  inference and routes other files to an unconstrained model. Closure is checked (0 of 60,934 edits leave it).
- **Instances at a glance (table, 0 words of prose; a new table after the catalogue, which shifts every later table's number by one).** One row per instance (EMBER
  now; other domains add rows). Columns: features, modeled, kinds, monoids, readout forms, repairs (value-preserving
  / patched), operations (in items / as writes), population share, bit-exact check.

## §5 Evaluation, by §3's results (3,200 words)

| Subsection | Result | Table | Claims | Status |
|---|---|---|---|---|
| 5.1 Setup (300) | | | pilot scale, GBDT, 1% FPR, toolkit (seen / held-out) and adaptive attacks, every attacked file re-extracted | measured |
| 5.2 Side effects (700) | Prop. 1 | 3 | the instrumentation and the operations' changes are correct (73,063 edits, 0 wrong), and the instance abstains exactly where a write lands on a position the parser reads; combined edits exact. Not "Proposition 1 holds", which is exact by construction (decision 3) | measured |
| | | — | Prop. 1 used by an attack: the adaptive search scores 5,000 candidates per file without extraction, and evades the undefended model about as often as the best toolkit attack (25/49 vs GAMMA's 24/47, different training subsets; its real strength shows on the defended rows) | evasion measured; **cost per candidate, predicted vs extracted: missing** (cheap, minutes) |
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
  appears as the realistic alternative a defender would use, not as a use. Add the cheap per-candidate cost to §5.2.
  Cost: §2 promises less; a reviewer may ask why adversarial training on computed points was not tried.
- **B. Show all four.** A plus two runs: (i) adversarial training on the adaptive search's outputs, produced through
  Prop. 1 (the problem-space defense made cheap); (ii) a feature-space attack (the exact tree solver already used for
  the learned region) inside the derived region on the unconstrained detector, against the evasions the problem-space
  search realizes. Cost: (i) is heavy (the adaptive search on hundreds of training malware; a 1,000-candidate budget
  would bring it down) and adds a row whose expected result (resists the toolkit, still falls to a fresh adaptive
  search, as the toolkit-trained row does) mostly repeats Table 5's point; (ii) is cheap but adds machinery.

**Decided (2026-11-09): A**, plus the per-candidate cost measurement; revisited at the next full review, which
also checks how much the literature values problem-space defenses (PLAN.md, decision 6). Reasons: The paper's strongest claims (Table 4, Table 5's
monotone rows) need no new runs, every line §2 keeps has a table behind it, and adversarial training already serves
as the defender's alternative. B(ii) is the one addition worth weighing if the review asks for the feature-space
side; B(i) costs most and argues least.

## Measured vs missing

- **Measured (pilot):** Tables 3-5 complete; closure; coverage across corpus sizes; price list; PV and ERDALT holes;
  expert set's 11 holes; the hand detector's soundness loss.
- **Missing, small:** the per-candidate cost of scoring by Prop. 1 against extraction (§5.2); the instances-at-a-glance
  table (assembly only); the sums row's adaptive cell (beam search cannot route to the sums detector yet; expected 0%).
- **Missing, user's decision:** the scale-up (seeds 0-2, full splits, more malware; the adaptive budget at 2,000
  files); a second toolkit for held-out attacks (MAB-Malware); other domains (later, appendix plus table rows).

## Dropped from the paper

Requirements R1-R5, footprints, margins, Theorems 2-3, the CTU-13 rows and Drebin as planned instances (any later
domain goes through the template), coupling, the region's tightness, a cost theorem, effort claims.
