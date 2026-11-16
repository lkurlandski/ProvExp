# Theory analysis: the proof audit, and the theory in brief

Session 74 (2026-11-16), carrying out `docs/archive/resume-prompt-2026-11-16-s74.md`. Parts A and B are stage 1
(the audit), parts C to E stage 2 (ideas). **In the manuscript:** the three items of A.4 and proof notes 1-4
(d12ba89); proof note 5's sentence in §5.1 as a prediction (4e67a96); C.1 as Lemma 1 (*Closure*) in §3.3 with its
proof in Appendix C (f2f1fcf); C.2 as the readout rule, with Table 1, Definition 10 and Appendix C rewritten
(c2fee51). The texts proposed in D.1 and D.2 were drafts; the manuscript has the final wording. The numbers below
are those at the time of the audit; since then there is also Lemma 1, and the readout rule is Equation 11.
Numbers are from `manuscript/main.aux`: Definitions 1-10, Proposition 1 (*Exact side effects*), Theorem 1 (*Sound
directions*), Corollary 1 (*Robustness*), Table 1 (the readout rules), Table 7 (the sign table, Appendix C).

Read for the audit: §2, §3, Appendices B and C, §4, §6, `r6-prior-work.md`, `proof-notes.md`, reviewer A's report
and the meta-review's check of it (`docs/reviews/2026-11-12-body/`), and, to check three claims, Gimenez et al.'s
Propositions 1-2 and Severi et al.'s remark on hashing in `papers/`, thrember's string features, and the engine's
rule for minima (`src/provexp/reach.py`).

## A. Proof audit

### A.1 Result

**The three results are correct, and their proofs are complete.** I found no error in Proposition 1, Theorem 1 or
Corollary 1.

Around them I found three things that are new, all small:

1. one hypothesis missing from the ratio rule (two words);
2. one wrong sentence in the caption of Table 7 (a min pool under a replacement);
3. one misstatement in the lead of §3.2 ("give $z'$" for "give the features of $z'$").

The five proof notes hold. I correct where notes 1 and 2 put their text: both fit in Appendix C, and Definition 4
should keep its real-valued readouts.

Item 1 is a leftover of session 53b's fix of the same rule: "$b > 0$" was replaced by the weaker "$a = 0$ whenever
$b = 0$", which EMBER needed, and the non-negativity of $b$ went with it.

Two points of reviewer A that were already triaged are not reopened (A.6): that Definition 5 holds for every feature
mapping, which the user settled in session 53b as a property of the framework and not a gap, and that Proposition 1
is exact once a delta is known.

### A.2 The three results

| Result | Verdict |
|---|---|
| Proposition 1, the two decompositions | Correct. $\pi(z) = B \uplus I^-$, $\pi(z') = B \uplus I^+$, and the fold of a union combines the folds. |
| Proposition 1 (i), additive sums | Correct. |
| Proposition 1 (ii), pools | Correct, and the example that the old value does not suffice ($\{5,3\}$ against $\{5,5\}$) is right. |
| Proposition 1 (iii), unchanged features | Correct. |
| Theorem 1, one edit | Correct. The proof replaces each change's old contribution by its new one, one at a time, in a totally ordered monoid whose operation keeps the order. |
| Theorem 1, sequences | Correct. Closure keeps every intermediate input in $Z$, and a direction is closed under addition. |
| Corollary 1 | Correct. It needs only a sound table and a closed population. A score that is monotone in each up feature, antitone in each down feature, free in the fixed features and blind to the both features is monotone with respect to the table (move one coordinate at a time). |

### A.3 What the results use

| Item | Verdict |
|---|---|
| Definitions 1-6 | Correct as stated. |
| Definition 8, replacements against removal plus addition | Correct. A replacement has the same delta as a removal and an addition; keeping it apart only makes the table tighter (a count stays fixed), never unsound, because "made of" asks only that some pairing into changes of $\Delta$ exists. |
| Definition 9, pools and neutral elements | Correct. With $\nu_\tau(\bot) = \mathbf{e}$, an addition raises a max pool and lowers a min pool, a removal the reverse, with no separate rule. |
| The total-order hypothesis | Correct, and now in the theorem's statement (it was missing at the time of the review, A-W3 (1)). The product example is right. |
| Table 1: identity, monotone, distinct count, any other | Correct. |
| Table 1: ratio and normalized bin | **A real gap**, A.4 item 1: the rule also needs $b \ge 0$. The three cases of the proof are otherwise right, and each of the two stated conditions is needed. |
| Table 7, the rows | Correct for the sums they are stated for. |
| Table 7, the caption's sentence on min pools | **Wrong** in one cell, A.4 item 2. |
| Hashed keys | Correct. The quote from Severi et al. is fair: they drop the hashed features because "directly manipulating these features ... would be extremely difficult" given "the preimage resistance of the hash function". |
| Patterns under extension | Correct, because the feature counts the *strings that contain a match* (thrember calls `re.search` once per string). The paragraph would be false for a count of matches: with the pattern `x(.*y)?`, the string `x x` holds two matches and `x xy` holds one. See A.7. |
| Appendix B | Correct as stated. |
| §3.2's lead | **A misstatement**, A.4 item 3. |
| The comparison with Gimenez et al. in the proof of Corollary 1 | Inexact, as proof note 3 says. Checked against the PDF, A.5. |

### A.4 The three new items, with old and new text

**1. The ratio rule needs a non-negative denominator (a real gap; two words).**
The caption of Table 1 and the proof ask that $a \ge 0$ and that $a = 0$ whenever $b = 0$. The proof then treats
$b > 0$, $b' = 0$ and $b = 0$, which leaves out $b < 0$, and there the rule fails. Smallest counterexample: $b = -1$
is fixed and $a$ goes from 1 to 2. The rule returns up, and the ratio falls from $-1$ to $-2$. No denominator in
EMBER is negative (they are counts and sizes), so nothing measured changes.

- Table 1, caption. *Old:* "it requires $a \ge 0$, and $a = 0$ whenever $b = 0$."
  *New:* "it requires $a \ge 0$ and $b \ge 0$, and $a = 0$ whenever $b = 0$."
- Appendix C, *The readout rules*. *Old:* "For a ratio $a/b$, with $a \ge 0$ and $a = 0$ whenever $b = 0$, suppose
  first"
  *New:* "For a ratio $a/b$, with $a \ge 0$, $b \ge 0$, and $a = 0$ whenever $b = 0$, suppose first"

**2. Table 7's caption is wrong for a min pool under a replacement (wrong; one sentence).**
The caption says a min pool follows the max pool "with up and down exchanged". That holds for additions and removals.
It does not hold for a replacement: extending an item raises its length, and a larger value never lowers a minimum.
Smallest counterexample: two items of lengths 3 and 5 feed a min pool, and the first is extended to length 4. The
minimum rises from 3 to 4, where the caption gives down. Definition 9 and the proof are right; only the caption is
wrong. The engine is right as well: its rule for a minimum flips the signs of additions and removals and passes the
sign of an item's own change through (`reach.py`, the `Min` case).

- Table 7, caption. *Old:* "A min pool follows the max pool with up and down exchanged."
  *New:* "Under additions and removals, a min pool follows the max pool with up and down exchanged; under a
  replacement it moves as the max pool does."
- Appendix C, *Directions of sums*, optionally. *Old:* "on an additive sum and on a max pool alike"
  *New:* "on an additive sum and on either pool alike"

**3. §3.2's lead says the delta gives $z'$ (a misstatement; four words).**
A delta drops positions, so it cannot give the edited input, only its sums and features.

- §3.2, first paragraph. *Old:* "proves that the delta and the item table of $z$ give $z'$ exactly (before the edit
  is applied) and thus the side effects of the transformation, $T$."
  *New:* "proves that the delta and the item table of $z$ give the features of $z'$ exactly (before the edit is
  applied) and thus the side effects of the transformation, $T$."

### A.5 The five proof notes (`proof-notes.md`)

**Note 1 (the sign of a change when a pool is empty): confirmed, with a different place for the fix.**
The problem is real: $-\infty$ minus $-\infty$ is not defined, and the proof only ever compares. But I advise against
the note's second suggestion, widening Definition 4 to infinite values. The feature space is $\mathbb{R}^n$ in §2 and
the score is a function on it, so features should stay real, and note 2 below is what keeps them real. The sign
sentence is then needed for sums only, which appear in Appendix C and not in Definition 7. It can replace a sentence
there that defines a symbol the appendix never uses again.

- Appendix C, *Directions*. *Old:* "Write $\operatorname{sgn}(x) \in \{-, 0, +\}$ for the sign of a number."
  *New:* "The sign of the change of a value from $a$ to $a'$ is $+$ if $a' > a$, $-$ if $a' < a$, and $0$ if the two
  are equal, which also covers a pool that no item touches, whose value is infinite."
- No change to Definition 4 or Definition 7.

**Note 2 (a default for an empty pool): confirmed, slightly extended.**
Theorem 1 is correct as stated, since the monotone rule asks for a nondecreasing $g$ and a bad default is not one.
The sentence is still worth adding: reviewer A drew exactly the wrong inference (A-W3 (3)), and the sentence also
says why a feature that returns a pool is a real number, which Definition 4 requires and Algorithm 1's $x_2$ does not
meet on an input without records.

- Appendix C, *The readout rules*, after "so its change has a sign in $d_k$." *New sentence:* "A feature that returns
  a pool returns a default value when no item touches the pool, so that it is a real number; this readout is
  nondecreasing only if the default is at most every contribution to a max pool, or at least every contribution to a
  min pool, and otherwise the feature takes the last rule."

**Note 3 (Corollary 1 against Gimenez et al.'s Proposition 1): confirmed against the PDF.**
Their statement: "If $\phi$ is monotonically increasing w.r.t. $\preceq_M$ and if $f$ is monotonically increasing
w.r.t. $\le$, then $f$ is robust". The order on the features is the usual one, in every feature. Ours is the order
the table defines, which leaves the score free on fixed features. The note's new text is accurate; keep it as
written.

**Note 4 (say that fixed features are unconstrained): confirmed.** It is what makes the detector usable and the text
does not say it.

**Note 5 (the trained detector's monotonicity rests on the library): confirmed, unchanged.** It concerns the link
from Corollary 1 to the trained model, not §3. The decision is the user's, as the note says.

### A.6 Already triaged, not reopened

- **Every feature mapping meets Definition 5**, with one item that holds the whole input (A-W1). Settled by the user
  in session 53b: items are hierarchical, the framework stays well defined at that limit, and this is a strength; no
  fix. The audit agrees that nothing in the proofs depends on it. What §3 does not contain is a statement of *how*
  the results change with the size of the items, which the user welcomed as an idea and which is one of stage 2's
  questions.
- **Proposition 1 is exact given the delta** (A-W5; register R9, a text fix after the scale-up). The proposition is
  correct as stated; where the delta comes from is the instance's work.
- **"Covers" and "closed" are checked on a corpus, not proven** (register R2). §4 says so in its own words.

### A.7 Pedantic (one line each; I would leave them)

- "such an extension can only add matches" reads more safely as "a string that matches still matches after such an
  extension" (see the counterexample in A.3).
- Algorithm 1's $x_1$ divides by zero and $x_2$ is $-\infty$ on an input without records.
- Proposition 1 (ii) holds for every sum, not only pools; its proof writes $\oplus$ where one sum's $\star_k$ is meant.
- "An item that moves ... is in neither part" is true of the smallest delta; a delta may list it in both.
- Exactness is in real arithmetic; in floating point it holds for integer-valued sums.
- $d[0,0]$ is fixed, and the footnote of Table 7 gives up (sound, loose).
- Hashed keys: a pair no enumerated key reaches counts as reachable unless $Q$ was enumerated in full.

## B. The theory in brief

**What the three results say together.** Write the extractor as three steps: find the items, add up what each
contributes, compute each feature from a few totals. Then an edit is a list of items removed and items added.
Proposition 1: from that list and the record of the unedited input, the features of the edited input follow by
arithmetic, with no second extraction. Theorem 1: if one knows, for each kind of item, which changes the attacker's
edits can make, then each total can be given the directions it can move in, and each feature inherits a direction
from its formula; this holds for every edit, every content, and every sequence of edits, on a set of inputs the
edits cannot leave. Corollary 1: a score that never falls along those directions cannot be lowered by the attacker.

**What is new, stated as strongly as is honest.** Each argument on its own is standard: updating totals from
inserted and deleted rows, the rule of signs, and Gimenez et al.'s two-line robustness argument. What is ours is the
model that lets them meet, and three things in it have no precedent I know of.
(1) Items as a multiset of kinds and contents, without positions, so that an edit of a raw input becomes a difference
of multisets and the extractor's arithmetic applies to it.
(2) The signature: a whole threat model described per kind of item by the changes it can make, with replacements kept
apart, and with no content. This is what makes "every edit" computable.
(3) The chain from a problem-space threat model to a certificate for a detector, proven link by link, with exactly
two hypotheses left for an instance (the signature covers the threat model; the population is closed). A claim about
thousands of features under every edit is reduced to a claim per kind of item. Pierazzi et al. name this step
($\Gamma \vdash \Omega$) and say it cannot be done in general; Incer et al. and Gimenez et al. assume its result by
hand. No earlier work derives feature directions from an extractor (`r6-prior-work.md`).

**Where the theory is thinner than the paper's claims.**
- *It is silent on item size.* The framework applies at every granularity, from single elements up to one item for
  the whole input, and the results say more the smaller the items are next to the edits. That is visible in every
  example and stated nowhere in §3: there is no result that compares a fine item map with a coarse one.
- *The two hypotheses carry the difficulty.* Theorem 1 assumes covering and closure, and §3 offers nothing that
  helps establish either. On EMBER both are checked, not proven.
- *Soundness only.* Nothing says how loose a table is. Looseness has three known sources: signs carry no size, sums
  are treated one by one although one item feeds several, and every formula outside Table 1's short list gets
  "both".
- *Corollary 1 is one-way.* Monotone implies unevadable; the reverse is false in general, and the theory says
  nothing about what robustness costs.
- *Proposition 1 has no consequence inside the theory.* Theorem 1 does not need it beyond the fold's algebra, and no
  finding of §5 rests on it alone.
- *§5.3's finding has no statement behind it.* That defenses learned from observed attacks miss unseen edits is
  measured, not derived.

## C. Candidate ideas

Six candidates. Each was first tried against Algorithm 1 for a counterexample; what died is reported as dead. "I
believe" means I have a proof sketch of a few lines that I have not written out; nothing below is proved yet. None
needs data. All six are elementary once the framework is in place, and I say so for each: their value would be in
what they let the paper state, not in their difficulty.

### C.1 Closure as a consequence, not a hypothesis

- **In plain words.** Theorem 1 asks that the edits cannot take an input out of the population, and the paper checks
  this on a corpus. If the population is *defined by features* (for instance "the number of items located past the
  end is zero"), then closure follows from the table: an edit cannot leave the population if the table says it cannot
  raise that count. The first half of Theorem 1, which needs no closure, proves it.
- **Statement.** Let $\Delta$ cover $\mathcal{M}$ over $Z$, and let $Z$ be the inputs on which features
  $m_1, \dots, m_r$ of the extractor are at most given thresholds. If the derived table gives no $m_i$ the sign $+$,
  then $Z$ is closed under $\mathcal{M}$.
- **Belief.** True; two lines from Theorem 1's first part.
- **Algorithm 1.** $Z$ = inputs whose largest record has at most 100 elements. Under "add a token", *largest* is
  fixed, so $Z$ is closed. Under "add a record", it is up, the lemma does not apply, and $Z$ is indeed not closed.
- **What it changes.** Theorem 1 loses a hypothesis whenever the population is written this way; "closure is checked
  rather than proven" (§4.4, register R2) becomes "closure follows from the signature". An operation that can leave
  the population shows up in the table as one that can raise a membership count, which is what the escape audit of
  R7 found by trial.
- **New concepts.** None in §3 (a population given by features). In §4, the population's clauses written as counts.
- **Against.** Covering is itself checked on a corpus, so the proof rests on a checked premise. Whether EMBER's
  clauses can all be written as item counts, and whether signs suffice for each, is unknown until each clause is read
  (reading code, no run). Where a clause compares two totals that rise together, signs will say "both".

### C.2 One rule for all readouts, and Corollary 1 as the same rule

- **In plain words.** Table 1 has six rules. They are one rule: a sum the formula rises with passes its direction
  on, a sum it falls with passes its direction flipped, and any other sum passes it both ways. The ratio is the case
  "rises with the numerator, falls with the denominator". A detector's score is one more formula over the features,
  so Corollary 1 is this rule applied once more.
- **Statement.** Let a readout be nondecreasing in the sums of $P$ and nonincreasing in those of $N$, for every value
  of its other sums $O$, on the values that occur. Then its direction is
  $\bigcup_{P} d_k \cup \bigcup_{N} (-d_k) \cup \bigcup_{O} (d_k \cup -d_k)$.
- **Belief.** True; three lines. I checked that the ratio with its zero convention is monotone in this sense on its
  domain ($b > 0$, or $a = b = 0$), so the three-case proof in Appendix C reduces to that check.
- **Algorithm 1.** $x_1$ = size / records under "add a record": both sums are up, one in $P$ and one in $N$, so
  both, as now. Every row of Table 1 gives the direction it gives today.
- **What it changes.** Table 1 becomes one rule with the current rows as examples. Totals, differences, means,
  the larger or smaller of several sums get tight directions with no new rule (a duration is a last time minus a first
  time), which matters for a second domain more than for EMBER. Corollary 1 reads as the last step of the same
  chain. A companion fact comes free: the table of a union of threat models is the union of their tables (C.6).
- **New concepts.** None; it removes rows.
- **Against.** Elementary order theory (monotone maps compose), close to what monotonicity type systems do. It
  rewrites a table and a proof the user has accepted. No feature of EMBER changes direction, as far as I can tell
  without checking each "any other" readout.

### C.3 Item size: no monotone trade-off, but tables combine

- **In plain words.** The hoped-for result, "finer items give tighter tables" (or the reverse), is **false both
  ways**. What is true: every item map gives a sound table, tables from different item maps can be intersected, and
  the work of Proposition 1 only shrinks as items get finer.
- **Dead, with counterexamples.**
  - *Finer can be tighter.* Move one element from one record to another. With records as items, one record shrinks
    and one grows, so the total size gets "both". With elements as items, nothing is removed or added, so it is
    fixed. The fine map sees that content is conserved across items.
  - *Coarser can be tighter.* Let records always hold as many *a* as *b*, and let a sum count *a* minus *b*. With
    records as items it is fixed. With elements as items, adding an *a* raises it and adding a *b* lowers it, so
    "both". The coarse map sees an invariant inside an item.
- **What survives (I believe; short proofs).**
  1. The pointwise intersection of sound tables is sound, so two item maps of the same extractor can be used
     together, and the result is at least as tight as either.
  2. With one item for the whole input, the derived table is the least sound table by definition, and computing it
     is the original problem. So the one-item limit is the specification, and every finer map is a sound
     approximation of it that can be written down.
  3. If a coarse item splits into fine items, the fine delta of an edit is contained in the split of its coarse
     delta: Proposition 1 never does more work at the finer level.
- **What it changes.** A paragraph in §3.1 or §7 that says precisely how item size matters, with the two examples.
  It turns the fact that every mapping meets Definition 5 into a stated design choice.
- **New concepts.** One definition (when one item map refines another).
- **Against.** Standard in abstract interpretation (an analysis that treats parts independently loses what ties them
  together; analyses combine by intersection). Point 2 is the "tightness" the mock lists as dropped. The EMBER
  instance uses one item map, so nothing in §5 would use point 1.

### C.4 What a defense learned from attacks cannot know

- **In plain words.** A table learned from attacks records the directions in which the observed attacks moved each
  feature. It is exact for those attacks and silent on the same operations with other content. From the same
  observed attacks, the framework derives the table for every content, and the difference between the two tables
  is the defense's blind spot, known before any new attack is run.
- **Statement.** Let $A$ be a set of observed edits, $L_A$ the table of the signs they showed, and $\Delta_A$ the
  signature that allows, for each kind, every change of the types the observed deltas contain, with any content.
  Then $L_A \subseteq D_{\Delta_A}$ feature by feature; $L_A$ is sound for the edits $\Delta_A$ covers only if the
  observations witness every sign of the least sound table; and the number of observations this needs grows with
  the number of keys the content can take, while $\Delta_A$ needs each kind and type of change once.
- **Belief.** True and close to definitional.
- **Algorithm 1.** Observe "add the tokens *foo* and *bar*". $L_A$ has two token counts up and every other one
  fixed. $\Delta_A$ ("add any token") has every token count up. An edit that adds *baz* raises a count that the
  learned table trusts as fixed.
- **What it changes.** §5.3 gets a statement that its measurements illustrate: the blind spot is content the attacks
  did not use, and it is computable from the attacks themselves. It also explains why trying every operation once
  (the trial detector of R18) is not enough.
- **New concepts.** The learned table as an object of §3 (one definition).
- **Against.** The most elementary of the six: without the extractor, what was not observed cannot be excluded. It
  covers defenses that select features by observed signs; a learned linear layer (ERDALT) needs the same statement
  for cones, which is the relational rule the user declined.

### C.5 Side effects do not depend on the host, up to the readout

- **In plain words.** Pierazzi et al. note that the same addition to two different objects can give different side
  effects. Proposition 1 says exactly how far that goes: the same delta changes every additive total by the same
  amount on every host. The host enters only through the current totals a formula reads, and, when an item is
  removed from a maximum or minimum, through the items that remain.
- **Statement.** If two inputs agree on the sums in the support of feature $j$, these are additive (or pools from
  which the delta removes nothing), and the same delta applies to both, then feature $j$ takes the same value after
  the edit on both.
- **Belief.** True; it is Proposition 1 (i) and (iii) read for two inputs.
- **Algorithm 1.** "Add a record of 7 elements" adds 7 to size and 1 to records on every input; $x_1$ then differs
  between hosts only through their size and records.
- **What it changes.** Three sentences after Proposition 1. It gives the proposition a consequence of its own that
  answers a remark of the paper we build on, and it makes their estimate from a minimal host exact at the level of
  totals. No timing claim.
- **New concepts.** None.
- **Against.** Small, and a reader may find it obvious. The delta itself can depend on the host (the fields an edit
  must update), which the statement assumes away.

### C.6 Threat models add up

- **In plain words.** The table of two sets of operations together is the union of their tables. On a population
  closed under both, no combination of operations moves a feature in a direction that no single operation moves it.
  Without closure this fails, and that failure is exactly the escape of R7.
- **Statement.** $D_{\Delta \cup \Delta'} = D_\Delta \cup D_{\Delta'}$ feature by feature; with Theorem 1, the same
  holds for every sequence that mixes the two threat models on a population closed under both.
- **Belief.** True; the direction of a sum is a union over changes, and each rule of Table 1 commutes with unions
  (I checked each row).
- **Algorithm 1.** "Add a record" and "add a token": the table of both is the union of the two.
- **What it changes.** One or two sentences in §3.3. The per-operation reading of §5.4 (which operation costs which
  features) rests on it, and it says in one line what closure buys.
- **New concepts.** None.
- **Against.** Trivial. It says the *table* is additive over operations; the cost in detection is not, and a reader
  may hear more than is said.

### Weighed and not proposed

- **Bounds on size instead of signs.** Corrected after the user asked (session 74): my first reason here ("needs a
  verifier") was the weakest one and left out the main fact. This idea is direction A', tried and dropped on
  2026-11-02 (`docs/graveyard.md`): a sound region per file and budget with an exact solver for the trees. It
  certified nothing above 4 KB, where the paper's budget is 5% of the file or 512 KB. Three reasons hold beyond that
  implementation. (1) The domain has no small budget: nothing limits what an attacker adds, which is why Incer et al.
  and Gimenez et al. work with directions. (2) Bounded movement helps only features that average over the file
  (histograms, means); a header field or a presence bit covers its whole range with one write. The price list of
  §5.4 puts the cost elsewhere: dropping the two-sided features costs 0.2 points at 1% false positives (pilot), and
  the rest comes from the constraints for imports and header writes, which no budget bounds. (3) The guarantee would
  change kind, from "no edit, on any file of the population" to "this file, up to this budget". What may be worth
  one sentence: a direction is what an interval becomes when the budget is unbounded, which says why signs are the
  right domain here. To revisit only if the scale-up's price list shows that the two-sided features carry detection
  at 0.1% false positives (pilot: 5.2 points, within retraining noise).
  **Open, by the user's decision (session 74):** "an incredibly meaningful direction"; A' was explored at a much
  earlier point and does not settle it; to be taken up with dedication in a session of its own, after C.1 and C.2.
  No sentence on intervals in the paper until then. See part E.
- **A locality lemma** (a write changes only the items that read a written position). It would turn part of
  "covers" into a proof, but only given a sound record of what the parser reads, and the instance builds that record
  by perturbation. The checked premise would move, not go away.
- **A characterization of the class.** There is none to find: every function of the items is a readout of counts per
  content, so the class is not delimited by its sums, only made useful by its readouts.

### My view

C.1 and C.2 change the theory itself: one removes a hypothesis, the other shortens the section and widens what it
covers. C.3 answers the question about item size, mostly by saying what is false. C.4, C.5 and C.6 are remarks of a
few sentences each. I would work out C.1 first, because its value depends on a reading of the population's clauses
that could still kill it.

## D. Proofs or counterexamples for the chosen ideas

### D.1 Closure as a consequence (C.1; chosen by the user)

**Status: the lemma is proved. Its payoff on EMBER is established by reading the code only; no clause has been
re-modelled and nothing was run.**

**Lemma.** Let $\Delta$ cover $\mathcal{M}$ over $Z$, with every sum totally ordered, and let $Z$ be the set of
inputs on which some features of the extractor stay at or below given values:
$Z = \{ z : \varphi_j(z) \le t_j \text{ for every } j \in J \}$. If no direction $(D_\Delta)_j$, $j \in J$, contains
$+$, then $Z$ is closed under $\mathcal{M}$.

*Proof.* Let $z \in Z$ and $T \in \mathcal{M}$. The first claim of Theorem 1 needs no closure: the change
$\varphi_j(T(z)) - \varphi_j(z)$ has a sign in $(D_\Delta)_j$, hence is not positive, for every $j \in J$. So
$\varphi_j(T(z)) \le \varphi_j(z) \le t_j$ for every $j \in J$, which is $T(z) \in Z$. $\qed$

(An earlier version of this statement placed $Z$ inside a closed set $Z_0$. That set did no work and misled: a
subset of a closed set is not closed in general. All files are closed under every edit, and the complete files are
a subset that one write to a directory entry leaves. Removed after the user's question.)

The same holds with $\ge$ and no $-$, and for features that are sums. There is no circle: covering is assumed over
$Z$ only, and it is used only on inputs of $Z$.

**The form that reads best.** A population is usually "the inputs that contain no offending item". Let a sum count
the offending items (each contributes 1, every other item 0), and let $Z$ be the inputs where the count is 0. The
lemma then says: *if no change of the signature creates an offending item, the population is closed.* Closure stops
being a hypothesis of its own. It follows from covering and from a property of the signature that can be read off
the changes.

**Counterexample hunt (Algorithm 1).** $Z$ = inputs with no record longer than 100. "Add a token": no change touches
*largest*, closed, and truly so. "Extend a record": a change raises *largest*, the lemma is silent, and $Z$ is truly
not closed. "Replace a record by one of the same length": fixed, closed. I found no case where the lemma's
hypothesis holds and closure fails, as the proof says there cannot be.

**What it does not give.** The converse. A table may give "both" to a membership feature of a closed population,
because signs lose what ties two totals together. Example: $Z$ = inputs whose records hold at most half of all
elements, and the edit adds a record of $r$ elements together with $r$ loose elements. Both totals rise, the rule
for their ratio says both, and $Z$ is closed.

**On EMBER, by reading `catalogue.precondition`, `plain_layout`, `regions` and `population.clauses`.**
The population has seven live clauses. Each compares quantities the parser reads from the headers with each other
or with the length of the file: section extents against SizeOfImage (two clauses), the PE header's offset against
the DOS header and against the sections' data (two), and sections, data directories and located items against the
end of the file (three). The certificate and debug entries are exempt since the widening of R7.

- **Nine of the thirteen operations: closure would follow from the table.** The seven in-place writes (slack, DOS
  header and stub, the nine loader-ignored header fields, the checksum, section names, the two removals) and the
  entry write touch no position that a live clause reads: `regions` cuts the positions the parser reads out of the
  slack and the DOS region, the nine fields and the checksum appear in no clause, and the two entries are exempt.
  Append changes one ingredient, the length of the file, in the direction every clause allows. For these nine, the
  membership features are fixed or down.
- **Four operations: signs are not enough.** Adding a section, adding imports (which adds a section) and the two
  insertions move the layout: section offsets, the header's sizes and the length of the file rise together. Each
  clause still holds afterwards because the quantities move by the same amount, and a sign table cannot see that
  (the example above). Closure for these four would follow from the lemma only in its second form, if each
  operation's declared changes are shown to create no offending item. That is an argument per operation about its
  own definition, or it stays a corpus check.
- **Not established.** (1) The clauses are not sums of the instance today. Most of their ingredients are (header
  fields, directory entries, the file's size are EMBER features), but whether an item is located past the end is
  recorded as positions, not as a contribution. Writing the clauses as counts is a change to the instance, and the
  derived table would have to be rebuilt to confirm the nine. (2) I did not check field by field that pefile reads
  none of the nine loader-ignored fields to locate an item; the code's comment says so, and the corpus check agrees.
  (3) For the entry write I traced the exemption in the directory clause, not how the item clause treats debug data
  past the end; run 142 found the widened population closed on the pilot.
- **Consistent with R7.** The writes that the escape audit found to leave the population (an entry pointed past the
  end, SizeOfImage raised) are exactly writes to positions a clause reads. Under the lemma they are the changes that
  can raise a membership count.

**What it would change in the paper (proposal, not applied).**

- §3.3, after the paragraph that explains Theorem 1. *New, three sentences:* "Closure need not be a separate
  assumption. If the population is the set of inputs on which some features of the extractor stay at or below given
  values, and the derived table says that no edit can raise these features, then no edit takes an input out of the
  population, by the first claim of the theorem. In particular, a population defined as the inputs without items of
  some offending form is closed if no change in $\Delta$ creates such an item."
- Appendix C: the proof above, four lines.
- §4.4. *Old:* "Closure is checked rather than proven: none of the 56,902 edits ... took a file out of it."
  *New, only after the instance work below:* closure follows from the signature for the operations that write in
  place or append, and is checked for the four that move the layout.

**Assessment.** The lemma is true, two lines long, and uses nothing new. It removes closure as an independent
premise in the theory. On EMBER it would turn a corpus check into a derivation for nine operations and leave four
checked, and it rests on covering, which stays checked. So register R2 goes from three tested premises to two and a
part.

**Decisions (user, session 74).** (1) Not integrated into the framework yet: "close, but not quite ready". The user
found the statement obvious as first presented; the $Z_0$ in it was the cause, and the plain explanation is: the
condition that defines the population is treated as one more feature, and the table that says which way every
feature can move then says whether any edit can break the condition. (2) **Instance-level work is needed and is
saved for a later session, once the theory is settled:** write the population's clauses as counts over items,
rebuild the derived table, confirm the nine operations, and decide how the four layout-moving operations are handled
(an argument per declaration, or the corpus check as now). Only then does §4.4's sentence change.

### D.2 One rule for all readouts (C.2; chosen by the user)

**Status: proved. Every row of Table 1 checked against it. Nothing applied.**

**Rule.** Let the readout of feature $j$ split the sums it reads into three groups: $P_j$, the sums it rises with;
$N_j$, the sums it falls with; $O_j$, the rest. Precisely: on the values of the sums that occur,
$\rho_j(\mathbf{b}) \ge \rho_j(\mathbf{a})$ whenever $b_k \ge a_k$ on $P_j$, $b_k \le a_k$ on $N_j$, and $b_k = a_k$
on $O_j$. The feature's direction is
\[
  D_j = \bigcup_{k \in P_j} d_k \;\cup \bigcup_{k \in N_j} (-d_k) \;\cup \bigcup_{k \in O_j} (d_k \cup -d_k).
\]

**Claim.** If every sum $k$ that the feature reads changes with a sign in $d_k$, the feature changes with a sign in
$D_j$.

*Proof.* Let $\mathbf{a}$ and $\mathbf{b}$ be the sums before and after. If $D_j$ lacks $-$, then no $d_k$ on $P_j$
contains $-$, no $d_k$ on $N_j$ contains $+$, and every $d_k$ on $O_j$ is fixed. So $b_k \ge a_k$ on $P_j$,
$b_k \le a_k$ on $N_j$, and $b_k = a_k$ on $O_j$, and the hypothesis on $\rho_j$ gives
$\rho_j(\mathbf{b}) \ge \rho_j(\mathbf{a})$. If $D_j$ lacks $+$, exchange the roles of $\mathbf{a}$ and $\mathbf{b}$.
If it lacks both, both inequalities hold and the feature is unchanged. If it lacks neither, there is nothing to
show. $\qed$

**The rows of Table 1 as cases.**

| Readout | Rises with ($P$) | Falls with ($N$) | Rule gives | Table 1 today |
|---|---|---|---|---|
| identity $s_k$ | $k$ | | $d_k$ | same |
| monotone $g(s_k)$ | $k$ | | $d_k$ | same |
| distinct count | every $q$ | | $\bigcup_q d_q$ | same |
| ratio $a/b$, or 0 if $b = 0$ | $a$ | $b$ | $d_a \cup (-d_b)$ | same |
| normalized bin $c_i / \sum_l c_l$ | $c_i$ | the other bins | $d_i \cup \bigcup_{l \ne i} (-d_l)$ | "as the ratio": $d_i \cup (-d_{\text{total}})$ |
| any other | | | fixed if every $d_k$ is, else both | same |

- *The ratio's zero case.* The values that occur are $a \ge 0$ with $b > 0$, and $a = b = 0$. On this set the ratio
  with its convention rises with $a$ and falls with $b$: a pair with $b > 0$ and the pair $(0, 0)$ are comparable
  only if the first has $a = 0$, and then both read 0. So the three cases of Appendix C's proof reduce to this one
  check, and the side conditions of the caption are the description of the set.
- *The normalized bin is the one row that changes, and it gets tighter.* Read over the bins, a bin's share rises
  with its own count and falls with every other count. If the edits can only add to bin $i$, the rule gives up for
  bin $i$ and down for the others. Today's rule gives both for bin $i$, because the total rises too. Under a threat
  model with free content every bin can rise and both rules give both, so no direction changes on EMBER; the gain
  shows under restricted content, such as padding with one value.
- *Free of charge:* totals and differences of sums, means, the larger or smaller of several sums, products of
  non-negative sums, and any composition of these.

**Corollary 1 is the same rule.** A score that rises with the up features, falls with the down features, reads the
fixed features in any way and does not read the both features gets the direction up from the rule, applied to the
features in place of the sums. So the chain is one lemma used twice: sums to features, features to score. The
remark that a score may read sums directly needs no separate sentence.

**Counterexample hunt (Algorithm 1).** $x_1$ = size / records under "add a record": size in $P$ is up, records in
$N$ is up, the rule gives both, which is right (the average can go either way). Under "extend a record": size up,
records fixed, up, right. $x_4$ under "add a token": up. $x_3$ (entropy): all in $O$, both. No row disagrees with
the present table except the normalized bin, where the new direction is contained in the old one.

**What it would change in the paper (proposal, not applied).**

- §3.3, the paragraph "The readouts turn the directions of sums into directions of features." *New text, about the
  same length:* "The readouts turn the directions of sums into directions of features, by one rule. Flipping a
  direction, written $-d$, exchanges up and down, and the union of two directions is again a direction. A readout
  rises with some of the sums it reads and falls with others. A sum it rises with passes its direction on to the
  feature, a sum it falls with passes its direction flipped, and any other sum passes both its direction and the
  flipped one. The feature's direction is the union of what its sums pass on. \Cref{tab:fw:readouts} lists, for
  each form of \Cref{sec:fw:model}, the sums it rises and falls with. A ratio rises with its numerator and falls
  with its denominator, so it can rise only if the numerator can rise or the denominator can fall. A readout of no
  listed form rises or falls with none of its sums in a way we can state, so its feature is fixed if every sum in
  its support is fixed, and can move either way otherwise."
- Table 1: the columns "Rises with" and "Falls with" in place of "Direction"; the same rows.
- Appendix C, *The readout rules*: the proof above (about 90 words) and the ratio's check (about 60) in place of
  the present paragraph (about 230).
- Before Corollary 1, optionally one sentence: the score is a last readout, of the features, and the same rule gives
  it the direction up.

**Assessment.** True and elementary: it is the fact that maps which keep an order compose, applied twice. What the
paper gains is a shorter §3.3 and Appendix C, a rule a second domain can use without new proofs, one tighter row,
and Corollary 1 seen as part of the same chain. What it costs is a rewrite of a paragraph and a table the user has
accepted. No measured number changes.

## E. What to do next

- **C.1 (closure): in the manuscript as Lemma 1.** The instance-level work (D.1, decision 2) is a later session's;
  until then §4.4 says closure is checked.
- **C.2 (one rule): in the manuscript as the readout rule.** The engine (`reach.py`) keeps the old rule for a
  normalized bin, which is sound and gives the same table under free content.
- **Both were approved after a brief look;** the user's close read is pending.
- **Next session:** choose among C.3-C.6, bounds on size, or a new idea (`docs/resume-prompt.md`).
- **Bounds on size: an open direction, not abandoned (user).** For the session that takes it up, what has changed
  since A' (Claude's reading, to be tested, not a promise):
  - A' asked whether a *fragile* detector can be certified. The question can now be what a *robust* detector may
    read beyond the one-sided features: a two-sided feature that the budget cannot move far.
  - A' bounded *features*, and its looseness came from the formulas (normalized histograms, entropy windows).
    Detectors can now read the sums, where one added element moves one count by exactly one.
  - The signature gives a place to state what each change costs, and D.2's rule carries over unchanged: a readout
    that rises with some sums and falls with others maps a box of sums to the interval between two of its corners.
  - The three obstacles in part C stand as things to design around: no natural small budget, features that one
    write moves across their whole range, and a guarantee per file and budget.
  - Start as Sound Directions round 4 did: a short note that settles the mathematics, a counterexample hunt on
    Algorithm 1, and only then any experiment.
