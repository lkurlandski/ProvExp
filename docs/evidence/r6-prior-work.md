# R6: the prior work the framework builds on

Session 50 (2026-11-12). The review's R6 (A-W2, B-W5, C-W8, D-W7): §3's results use known techniques, and §6 does not
place them against their precedents. The user's direction: the contribution is the combination; credit the shoulders
we stand on respectfully, without conceding each result to someone else (memory `credit-without-diminishing`). This
note is the first step only: what each work does, read from the paper itself, and exactly how it relates to ours. No
phrasing yet. Every quote below was checked in the PDF in `papers/` (gitignored; downloaded this session, sources at
the end).

## The works, grouped by what in §3 they touch

### A. Exact update of totals (Proposition 1, Exact side effects)

**Gray et al. 1997, Data Cube** (`gray1997data`, cited in §3.1 for distributive/algebraic).
- Defines distributive, algebraic, holistic aggregates (§5 of their paper; our readout paragraph follows it
  accurately).
- *Not used yet:* their §6 on maintenance says "max is a distributive for SELECT and INSERT, but it is holistic for
  DELETE", and "If a function is algebraic for insert, update, and delete (count() and sum() are such functions), then
  it is easy to maintain the cube."
- Relation: this is exactly our point that pools need the items, not just the total, when an item is removed. Reviewer
  A says our text "blurs" it (we cite Gray for distributivity, then argue pools from group inverses); Gray et al.
  themselves make the distinction, so citing them for it is free.

**Mumick, Quass, Mumick 1997, Maintenance of Data Cubes and Summary Tables in a Warehouse** (SIGMOD; not in
`main.bib`; read in the 1999 MIT Press reprint, ch. 25).
- Definition 3.1: "A set of aggregate functions is self-maintainable if the new value of the functions can be computed
  solely from the old values of the aggregation functions and from the changes to the base data."
- "all distributive aggregate functions are self-maintainable with respect to insertions. However, not all ... with
  respect to deletions." "MIN and MAX are not self-maintainable with respect to deletions, and cannot be made
  self-maintainable ... the new minimum (maximum) value ... must be recomputed from the changes and the base data."
- Their method (summary-delta tables): aggregate the changes first, then apply the aggregated change to the stored
  totals.
- Relation: Proposition 1 (i) is their self-maintainable case for SUM/COUNT; (ii) is their MIN/MAX case, with the
  item table playing the role of "the base data". Our σ(I⁺), σ(I⁻) are summary deltas in their sense. Reviewer A
  names this paper as the right reference for pools.

**Gupta and Mumick 1995, Maintenance of Materialized Views** (`gupta1995maintenance`, cited in §3.2 and §6; reprint
ch. 11).
- Survey; "incremental view maintenance" = computing only the change to the view.
- Two parts we have not used:
  - §4.1, the "irrelevant update" / "query independent of update" problem: checks that a *modification* leaves a
    view unchanged.
  - Updates as a modification type of their own: "treating updates as a distinct type of modification lets us derive
    view maintenance algorithms for updates where no algorithms exist for deletions+insertions."
- Relation:
  - Proposition 1 (iii) (a feature is unchanged unless the delta touches its support) is a per-edit
    irrelevant-update test.
  - Our signature keeps replacements apart from removal plus addition for the same reason the survey gives.

**Gupta, Mumick, Subrahmanian 1993, Maintaining Views Incrementally** (SIGMOD; reprint ch. 14; reviewer A).
- The counting algorithm: keep the number of derivations of each view tuple, so deletions can be propagated.
- Relation: indirect. Our multiset of items (each item counted as often as it occurs) is what makes removal well
  defined. A citation is optional; the survey covers it.

**Levy and Sagiv 1993, Queries Independent of Updates** (VLDB; reprint ch. 22; nobody named it).
- Independence: a query is independent of an update program if it does not change the answer "for all EDB relations".
  The update is given by a program, so it is a whole *class* of updates, quantified over every database. They also
  define monotonic and anti-monotonic queries.
- Relation: this is the closest database precedent for Theorem 1's *universal* question. Independence is our `fixed`
  direction; we ask more (up/down as well as fixed), over a population rather than every database, for raw edits
  rather than tuple updates. Undecidable in general for datalog; decidable for our class because readouts are
  per-sum rules. Worth one citation in §6 (it strengthens, not weakens: the universal question is recognized as
  hard and valuable).

**Koch et al. 2014, DBToaster** (`koch2014dbtoaster`, cited).
- Higher-order delta processing; generalized multiset relations whose multiplicities form a ring, so "a delete is a
  relation with negative multiplicities"; aggregates are SUM.
- Relation: matches our remark that (ℝ,+) is a group, so removal is subtraction. Their contribution (higher-order
  deltas, compiled view maintenance for speed) is beyond what we use. The current citation is accurate.

**Cai, Giarrusso, Rendel, Ostermann 2014, A Theory of Changes for Higher-Order Languages** (PLDI; not in `main.bib`;
reviewer A).
- Change structures and derivatives: f(a ⊕ da) = f(a) ⊕ f′(a, da). Every abelian group gives a change structure; bags
  with signed multiplicities are one. Their motivating example is `sum = fold (+) 0` with the change
  {remove 1, add 5}, whose derivative gives "plus 4".
- Relation: Proposition 1 (i) is the derivative of a fold over a bag, their first example. The pool case fits as a
  derivative that reads the base input (the kept items). Their aim is automatic, static incrementalization of
  arbitrary λ-programs for speed; ours is a single fixed program shape, used to know a change, not to compute it
  faster (we make no speed claims).

**Amsterdamer, Deutch, Tannen 2011, Provenance for Aggregate Queries** (PODS; not in `main.bib`; nobody named it, but a
database reviewer would).
- Aggregation "based on any commutative monoid", naming SUM (ℝ,+,0), MIN (ℝ∞,min,∞), MAX: the three we use.
- The aggregate value is kept as a formal sum of annotated contributions (p₁⊗20 + p₂⊗10 + p₃⊗15), so that deleting a
  tuple means setting its token to 0 ("deletion propagation"). They relate this to the counting algorithm. The
  foundation is that "query evaluation commutes with semiring homomorphisms".
- Relation: the closest relative of the item table plus fold. Our sums as a fold of item contributions in commutative
  monoids, the homomorphism σ(A⊎B) = σ(A)⊕σ(B), and removal by dropping items are this construction without the
  tokens. They handle deletions of existing tuples; we also add items whose contents come from the edit.

**Green, Karvounarakis, Tannen 2007, Provenance Semirings** (`green2007provenance`, cited in §6).
- Annotated relations (K-relations) for positive relational algebra; N[X] polynomials as the most general provenance.
  No aggregates.
- Relation: §6 says it is "what our item table records for each feature". Reviewer A: semirings record *which* inputs
  contributed, which fits the item table, but not *which positions control discovery* (the locating record). The
  aggregate version (Amsterdamer et al.) fits our sums better; Green et al. can stay as its foundation.

### B. Directions over a set of edits (Theorem 1, Sound directions)

**Cousot and Cousot 1977, Abstract Interpretation** (`cousot1977abstract`; in `main.bib`, cited nowhere; the comment
at the top of `_g_related_work.tex` wrongly says it is cited in the body).
- The introduction uses the rule of signs as the intuitive example ("which we borrow from Sintzoff"), and notes
  that the result can be imprecise but is consistent with the real computation.
- §7 builds the sign lattice I_RS with γ(+) = [0,+∞], γ(−) = [−∞,0]: "+" includes 0, as our `up` = {0,+} does.
  Abstract interpretation in general: an over-approximation that is sound (never excludes a real behaviour) and
  incomplete.
- Relation: our four directions are I_RS's elements (0, +, −, ±) applied to the *change* of a value, and Table 1's
  rules are transfer functions for readouts. "A sound table never excludes a vector that an edit produces, but may
  allow vectors that no edit produces" is their soundness/incompleteness. What Theorem 1 adds on top: the abstraction
  is of the change under a *set of edits* (a relational, differential property), its inputs are item kinds (the
  signature), and soundness is relative to a population closed under the threat model. These are the parts no
  textbook instance gives.

**Calzavara, Ferrara, Lucchese 2020, Certifying Decision Trees Against Evasion Attacks by Program Analysis** (ESORICS;
not in `main.bib`; reviewer D).
- Translates a decision tree into an imperative program and uses abstract interpretation to bound the attacker's
  success. The attacker is a set of feature-space *rewriting rules*: if x_f ∈ [a,b], add v ∈ [δl,δu] to x_f at cost
  k, written by hand (from their earlier Treant work).
- Relation: complementary, and positive for us. They abstract the *model* under a feature-space attacker; we abstract
  the *extractor* under a problem-space threat model, and our output (a sound direction per feature) is the kind of
  feature-space attacker description their rules take as input. Reviewer D's own suggested wording: "they abstract
  the model ..., while you abstract the extractor".

**Zhang, Albarghouthi, D'Antoni 2020 and 2021, A3T and ARC** (ICML 2020; EMNLP 2021; not in `main.bib`; nobody
named them; found by Claude's search).
- Certified robustness of NLP models to perturbation spaces "defined programmatically in a language of string
  transformations" (match-and-replace rules); ARC "uses abstract interpretation (Cousot and Cousot, 1977) to
  symbolically represent sets of perturbed strings" and propagates them through the LSTM with intervals.
- Relation: the closest certified-ML precedent for "a declared set of input edits, over-approximated soundly". The
  differences are concrete: their edits act on tokens the model sees directly (no parser or extractor in between);
  they bound magnitudes through one model; we bound signs through an extractor, independent of any model. Optional
  citation in §6 (certified defenses paragraph, R21), since reviewer C (robust ML) may know them.

**Reed and Pierce 2010, Distance Makes the Types Grow Stronger** (ICFP; reviewer C).
- A type system that tracks function *sensitivity*: how much a function can magnify the distance between inputs.
- Relation: loose. Same family ("how far can the output move when the input moves"), but metric magnitude, not sign;
  no edits, items or populations. Low priority; cite only if §6 has a sentence on sensitivity/monotonicity analyses.

**Not obtained, low priority (reviewer A):** change actions (Alvarez-Picallo et al. 2019), Datafun and Bloom^L
(monotonicity typing), Palpanas et al. 2002 (non-distributive aggregates). Each repeats a point above.

### C. Edits of raw input (§6's contrast; §4.3.2's locating positions)

**Wagner and Graham 1998, Efficient and Flexible Incremental Parsing** (`wagner1998efficient`, cited in §6).
- Edits are "textual and/or structural modifications"; "Textual modifications are represented as local changes to the
  terminal symbol containing the edit point"; an incremental lexer relexes, and the parser reuses unchanged subtrees.
- Relation: reviewer A is right. Incremental parsing *does* map raw edits to the changed parse nodes, so §6's first
  claimed difference ("finds the items that an edit of raw elements changes") does not hold as worded. What does
  hold: (1) they update the parse for one edit that has been made; we bound every edit of a declared set, before any
  content is chosen; (2) in a context-free grammar an edit's effect is bounded by structure around it, whereas in
  binary formats a position can locate items anywhere (offsets, pointers), which is why our signature needs the
  locating-position record.

**Acar, Blelloch, Harper 2002, Adaptive Functional Programming** (`acar2002adaptive`, cited in §6).
- Records dependences during the run (modifiables, a dynamic dependence graph); change propagation re-executes only
  the affected reads; proved correct: "the adapted output is the same as the output of a complete re-evaluation".
- Relation: the item table is a recorded trace in the same spirit, and Proposition 1's "the value the extractor
  itself returns" is their correctness statement for our class. Changes are made through the program's own
  modifiables, one concrete change at a time.

**Cheney, Ahmed, Acar 2011, Provenance as Dependency Analysis** (MSCS; reviewer A).
- Dependency provenance: which parts of the input a part of the output depends on. Minimal dependency provenance is
  not computable; they give dynamic and static approximations.
- Relation: this is §4.3.2's locating-position record (which positions the parser reads to find items), not §3.
  Their non-computability result supports building the record by a checked approximation. Reviewer A suggests it for
  R2 (taint tracking as a sound alternative to fuzzing). Cite in §4.3.2 or §6 when R2 is done.

### D. Security work the framework rests on (already cited; checked again)

**Gimenez, Sivaprasad, Fritz 2025** (`gimenez2025certifiably`, cited in §3.3 and §6).
- Definition 1 (robustness via the preorder ⪯M, reflexive and transitive: sequences of edits). Proposition 1: "If ϕ
  is monotonically increasing w.r.t. ⪯M and if f is monotonically increasing w.r.t. ≤, then f is robust."
- Their feature mapping "is monotonic when the attacker has no particular capability"; EMBER's histograms "are
  typically not monotonic ... such features are fragile and should be avoided."
- Relation: Corollary 1 is their Proposition 1 with per-feature directions (up, down, fixed) instead of all-up, over a
  closed population. Its hypothesis (ϕ monotone under M) is what they establish by hand and what Theorem 1 computes.
  §3.3 already credits this correctly.

**Pierazzi et al. 2020** (`pierazzi2020intriguing`, cited in §3.3 and §6; R5 asks for the TOPS 2025 version).
- Γ ⊢ Ω: problem-space constraints determine feature-space constraints. Side-effect features η.
- Their reason side effects are found by trial: "it is generally infeasible or impossible to compute the exact impact
  of side-effect features on the objective function in advance—because the set of problem-space constraints Γ cannot
  be expressed analytically in closed-form."
- Their workaround: inject each gadget into a minimal app "to have an immediate estimate of the side-effect features".
- "if an object z_o is added to (or removed from) two different objects z1 and z2, it is possible that the resulting
  side-effect feature vectors η1 and η2 are different."
- Relation: Theorem 1 computes Ω from a threat model for our class, which is what Γ ⊢ Ω names; Proposition 1 computes
  η exactly per host (answering their two-hosts remark); the minimal-app estimate is the precedent for computing side
  effects before applying an edit (R5).

**Labaca-Castro et al. 2022, Realizable UAPs for Malware** (`labaca2022realizable` in `papers/`, not cited; reviewer
B).
- For PE they "generate an approximation of the feature-space perturbations induced by the problem-space toolkit": a
  statistical model of "the probability of the feature being modified", learned from attacks, assuming independence
  across features.
- Relation: an empirical, attack-derived side-effect model, the same kind as Bostani et al. and ERDALT's learned layer.
  Belongs in §6's constraints paragraph next to Bostani et al. (learned from what attacks did, so limited to it).

## Where each would be cited

| Place | Works | Status |
|---|---|---|
| §3.1, readouts (Gray et al.) | Gray et al.'s maintenance remark (max is delete-holistic); Mumick et al. 1997 (self-maintainable) | Gray cited for another point; Mumick new |
| §3.1, fold as homomorphism | Amsterdamer et al. 2011 (aggregates over commutative monoids, evaluation commutes with homomorphisms) | new |
| §3.2, after Proposition 1 | Gupta and Mumick 1995, Koch et al. 2014 (already); Mumick et al. 1997 for pools; Cai et al. 2014 (derivative of a fold) | partly cited |
| §3.3, directions and Theorem 1 | Cousot and Cousot 1977 (sign lattice; sound, incomplete) | in bib, uncited |
| §3.3, Corollary 1 | Gimenez et al. (already, accurate) | done |
| §4.3.2, locating positions | Cheney et al. 2011 (dependency provenance) | new, with R2 |
| §6, incremental computation | Wagner and Graham (contrast fixed), Acar et al., Levy and Sagiv 1993 (universal question), Amsterdamer et al. | rewrite of 6 lines |
| §6, constraints | Labaca-Castro et al. 2022 | new |
| §6, certified defenses (R21) | Calzavara et al. 2020; Zhang et al. 2020/2021 optional; Reed and Pierce optional | new |

## What the reading says about the combination (input for the phrasing step)

Facts only, for planning; not text for the paper.
- Every line above answers a different question, and none asks ours:
  - Databases and change calculi update an output for one *given* change, stated in the program's own terms (tuples,
    modifiables, tokens).
  - Abstract interpretation over-approximates what a program *computes*.
  - The certified-ML works (Calzavara, Zhang) over-approximate a *model* under edits written in feature or token space.
  - Monotone detectors (Incer, Gimenez, Chen) take the directions as given, by hand.
  - Pierazzi et al. state that side effects cannot in general be computed in advance.
- The framework joins them at the point where they could not meet before:
  - Writing extractors as a fold of item contributions makes the database results apply to a feature extractor.
  - Abstracting the *change* per item kind lets a whole threat model be bounded without any content.
  - The signature and the locating positions tie raw problem-space edits to item kinds.
  - Closure ties the bound to a population.
- The result is the input the monotone-detector line lacked.
- No prior work found derives feature directions from an extractor (reviewer D's search, and ours this session:
  extended web search, `papers/`).

## Sources

PDFs in `papers/` (gitignored): `amsterdamer2011provenance` (arXiv 1101.1110), `cai2014theory` (arXiv 1312.0658),
`calzavara2020certifying` (arXiv 2007.02771), `cheney2011provenance` (arXiv 0708.2173), `cousot1977abstract` (RPI
library scan), `green2007provenance` (author's page), `koch2014dbtoaster` (arXiv 1207.0137; the VLDB 2012 version,
the bib cites the VLDB Journal 2014 extension), `acar2002adaptive` (CMU), `wagner1998efficient` (Berkeley Harmonia),
`reed2010distance` (UPenn), `zhang2020robustness` (arXiv 2002.09579), `zhang2021certified` (arXiv 2102.07818);
`gupta1995maintenance`, `gupta1993maintaining`, `levy1993queries`, `mumick1997maintenance` are chapters 11, 14, 22
and 25 of Gupta and Mumick (eds.), *Materialized Views*, MIT Press 1999 (the reprints of the original papers).

## Decision and what was done (session 50)

The user: cite only one or two seminal works per idea, not all of the above. Applied in 660ba90:
- §3.1 (pools): Gray et al.'s observation that a maximum is easy to maintain under insertions but not deletions.
- §3.2 (after Proposition 1): writing an extractor as a fold lets incremental view maintenance apply to features;
  the item table supplies what its rule lacks for maxima and minima (citations unchanged).
- §3.3 (after Theorem 1's explanation): abstract interpretation (Cousot and Cousot), the rule of signs; what is
  abstracted here is the change of a feature under every edit of a threat model.
- §6: the incorrect contrast with incremental parsing replaced; abstract interpretation and Calzavara et al. (the only
  new bib entry), whose feature-space rewriting rules are the kind of input our bounds provide.
Not cited, by decision: Mumick et al., Cai et al., Amsterdamer et al., Levy and Sagiv, Zhang et al., Reed and Pierce.
Deferred to other items: Cheney et al. (R2, the locating record), Labaca-Castro et al. (R21, §6 constraints).
