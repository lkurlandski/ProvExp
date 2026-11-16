# Theory analysis: the proof audit, and the theory in brief

Session 74 (2026-11-16), carrying out `docs/archive/resume-prompt-2026-11-16-s74-theory.md`. Parts A and B are stage 1
(the audit), parts C to E stage 2 (ideas). Part F is session 75's note on bounds on size (not in the manuscript).
**In the manuscript:** the three items of A.4 and proof notes 1-4
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
$$
  D_j = \bigcup_{k \in P_j} d_k \;\cup \bigcup_{k \in N_j} (-d_k) \;\cup \bigcup_{k \in O_j} (d_k \cup -d_k).
$$

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

## F. Bounds on size instead of signs: the mathematics note (session 75, 2026-11-16)

The user chose this direction ("the right direction") and asked that `docs/archive/a-prime/` be read with a heavy
grain of salt. **Status: a note for the user's review. Nothing is in the manuscript, nothing was run, no code was
changed.** "Proved" below means the proof is written in this part; "believed" means I have a short argument that is
not written out; "unknown" means unknown.

### F.1 The question in plain words

The sign table says, for each feature, which way the edits of the threat model can move it. It does not tell an edit
that adds one element from an edit that adds a million. If the attacker has a budget (at most $B$ elements written
or added), more can be said: how far each sum, and then each feature, can move. A detector could then also read a
feature that the sign table marks as moving both ways, or one it must now read in the direction the table dictates,
as long as the budget cannot move that feature far.

Three things are needed, in this order: a bound on each sum, a way to carry it through the readouts, and a statement
about a detector that needs no solver. Each is below (F.3), then what broke on Algorithm 1 (F.4).

### F.2 Direction A': what failed, read with caution, and what has changed

**What A' was.** Per file, an exact solver searched over the attacker's choices (bytes appended, up to three
sections added) for the lowest score of a given gradient-boosted detector, with every feature written as a function
of those choices. A file was certified if the proven lowest score stayed above the threshold. Budget: 5% of the file
or 512 KB, whichever is larger.

**What the record shows.** Sound throughout (every one of 1,105 real edits inside the region). Certificates only for
PV under appends, and elsewhere only up to 4 KB (13 files for the undefended detector, one seed).

**Where I do not trust the record's reasoning.**

1. *"The cause is the relaxation, not the solver."* This rests on one file's bound at 64 KB. The record never
   separates "the bound is loose" from "the score really can be moved that far". When the solver's answers were
   written as files, the one file whose clean score the record gives fell from 8.6 to 2.5, and the others scored
   between 3.4 and 6.8 (threshold 1.1): true drops, though not evasions. And real attacks evade the same undefended
   detector on 27 of the 47 files it detects. A detector that was not built for a certificate mostly cannot have
   one, whatever the bound.
2. *The budget.* On 26 of the 50 pilot files, 512 KB exceeds the file's own size. The encoding note itself predicted
   that no certificate is possible there "whatever the encoding does". Part of A''s failure is this budget, not the
   idea.
3. *The structural reason in the graveyard* ("certifying a fragile detector answers a question a reviewer would not
   ask") is about auditing detectors built by others. It says nothing about building a detector that uses sizes.

**What carries over as fact.** (a) Items that overlap or merge are the hard kinds: the entropy windows share bytes,
and strings merge at the boundary between old and new content. F.4 meets the same effect on Algorithm 1. (b) Some
operations have a capacity per file (no free slot for a section header). (c) At a budget of 5%, a share of a
histogram can truly rise from 0.4% to about 5% of the file; this is arithmetic, not looseness.

**What has changed since.** (1) The detector can be built for the certificate. For a score that is monotone in every
feature it reads, the certificate is one evaluation of the score (F.3, step 6): no solver, no relaxation, no files
written from a solver's answer. This removes A''s whole machinery. (2) The signature and the readout rule exist, so
the bound can be a statement that contains Theorem 1 instead of a tool beside it. (3) Detectors read sums, so a
count is bounded directly and the entropy windows need not be modelled unless a detector reads them. What has not
changed: the budget of the experiments is large, and F.6 says what that means.

### F.3 The objects, in order

Notation as in §3. "Element" is the unit of cost throughout; any other unit works the same way.

**1. Cost and budget.** Each transformation $T \in \mathcal{M}$ applied to an input $z$ has a cost
$\kappa(T, z) \ge 0$, for example the number of elements it writes or adds. The cost of a sequence is the total of
its steps. $\mathcal{M}_B(z)$ is the set of inputs reached from $z$ by sequences of cost at most $B$.
*Why:* without a price nothing limits size. With $B = \infty$ this is the threat model of Definition 7.

**2. The size of a change, and covering within budget.** A *priced signature* is a signature $\Delta$ together with
a size $w_\tau(c \to c') \ge 0$ for every change in $\Delta_\tau$: for an added item, say, the number of its
elements. It *covers $\mathcal{M}$ within budget* over $Z$ if every $T \in \mathcal{M}$ applied to any $z \in Z$
has a delta made of changes in $\Delta$ whose sizes, **kind by kind**, total at most $\kappa(T, z)$.
*Why:* the budget is counted in elements and the sums move through items; this premise ties the two. It is the
instance's to establish, as covering is, and it implies covering. Kind by kind, because one written element belongs
to items of several kinds (F.4, case b).

**3. Rates.** For an additive sum $k$ and a kind $\tau$, the *rate of rise*
$$
  u_{k\tau} = \sup \Big\{ \frac{\nu_\tau(c')_k - \nu_\tau(c)_k}{w_\tau(c \to c')} :
  (c \to c') \in \Delta_\tau \text{ raises } k \Big\},
$$
which is 0 if no change raises $k$ and $\infty$ if a change of size 0 does. The *rate of fall* $l_{k\tau}$ is the
same with the changes that lower $k$. Let $u_k = \sum_\tau u_{k\tau}$ and $l_k = \sum_\tau l_{k\tau}$.
*Why:* the rate is the most that one unit of budget can move the sum. The direction $d_k$ of Definition 9 is exactly
the record of which of $l_k$ and $u_k$ are not zero. So a direction is a pair of rates with their sizes forgotten.

**4. Bounded sums (proved).** *Let $(\Delta, w)$ cover $\mathcal{M}$ within budget over a population $Z$ closed
under $\mathcal{M}$. Then for every $z \in Z$, every $z' \in \mathcal{M}_B(z)$ and every additive sum $k$,*
$$
  -\,l_k B \;\le\; s_k(z') - s_k(z) \;\le\; u_k B .
$$
*Proof.* Take one step $T_i$ of the sequence, of cost $\kappa_i$, from $z_{i-1}$ to $z_i$; both are in $Z$ by
closure. Its delta is made of changes $C_i$ in $\Delta$, and by Proposition 1 (i) the sum changes by the total of
$\nu_\tau(c')_k - \nu_\tau(c)_k$ over $C_i$. A change of kind $\tau$ that raises $k$ adds at most $u_{k\tau}$ times
its size; any other adds nothing positive. The sizes of the changes of kind $\tau$ total at most $\kappa_i$, so the
step raises the sum by at most $\sum_\tau u_{k\tau} \kappa_i = u_k \kappa_i$. Adding the steps gives $u_k B$. The
lower bound is the same argument. $\qed$

*Pools (proved for the upper side of a max pool; the rest in words).* A max pool has no rate for additions, since an
added item brings a value and not an increment. Let $a_k(x)$ be the largest contribution to $k$ of an item that can
be added at size at most $x$, and $u_k$ the rate over replacements only. Then the pool ends at most at
$m(B) = \max\big(s_k(z) + u_k B,\ \sup_{x \le B}\, [\,a_k(x) + u_k (B - x)\,]\big)$: by induction on the steps,
every item of $z_i$ contributes at most $m$ of the cost spent so far (a kept item by induction, a replaced one
because $m(K) + u_k \kappa \le m(K + \kappa)$, an added one because $a_k(\kappa) \le m(K + \kappa)$). The lower side
is different in kind. When the item that holds the maximum is removed, what remains decides the new value, so no
rate bounds the fall. The bound comes from the item table of $z$: if every change that removes or lowers an item
has size at least $\omega > 0$, at most $B/\omega$ items are touched, and the pool stays at or above the
contribution ranked just after them. **This is the first place inside the theory where the item table of
Proposition 1 is needed and the sums alone do not do.**

**5. From sums to features: the corner rule (proved).** Step 4 gives every sum in the support of feature $j$ an
interval, and together a box. *If the readout rises with $P_j$ and falls with $N_j$ on the whole box, and no sum in
$O_j$ can move, then the feature stays between the readout's values at two corners of the box:* the corner with the
sums of $P_j$ at their lowest and those of $N_j$ at their highest, and the opposite corner. (Every point of the box
lies between the two corners in the order that the readout respects.) If a sum in $O_j$ can move, the rule gives no
bound, unless a bound is known for that form of readout.
*Why:* this is the readout rule \eqref{eq:fw:readout-rule} with intervals in place of directions, and it reuses
$P_j$, $N_j$, $O_j$ unchanged. It needs one thing more than the readout rule does: monotonicity on the whole box,
not only on the values that occur (F.4, case g).

**The statement these give (proved from 4 and 5).** *Under the premise of step 4, every feature of every input in
$\mathcal{M}_B(z)$ lies in the interval $I_j(z, B)$ that the corner rule returns from the rates.* Three properties:
- it is never wider than the sign table allows: if $(D_\Delta)_j$ lacks $+$, the interval's upper end is
  $\varphi_j(z)$ itself, and likewise for $-$;
- at $B = \infty$ it says what the sign table says: each end of an interval is then either the present value or as
  far as the readout can go, which is one of the four directions. Theorem 1 is this statement with an unlimited
  budget;
- it depends on the input, through the sums of $z$ (a ratio's interval depends on its denominator) and, for pools,
  through its item table. The sign table depends on no input.

**6. From features to a detector: the worst corner (proved).** Let the score $h$ be nondecreasing in a set of
features, nonincreasing in another set, free in features that cannot move, and let it read no other feature. Let
$\mathbf{x}^{c}(z, B)$ be the vector that puts every feature of the first set at the low end of its interval and
every feature of the second set at the high end. Then
$$
  h(\varphi(z')) \;\ge\; h\big(\mathbf{x}^{c}(z, B)\big) \qquad \text{for every } z' \in \mathcal{M}_B(z),
$$
because $\varphi(z')$ lies above the corner in every feature of the first set, below it in every feature of the
second, and equals it elsewhere. So a file is certified at budget $B$ if the score **at one computed vector** is
above the threshold. If $h$ is monotone with respect to the sign table, the worst corner is $\varphi(z)$ itself for
every $B$: that is Corollary 1. A detector may now be monotone in a feature the table marks both, or monotone
against the table's direction, and pays for it by the width of that feature's interval. The guarantee is per file
and per budget, as certified accuracy at a radius is in the literature on robust classifiers.

### F.4 The counterexample hunt on Algorithm 1

Cost: the number of elements added or written. Operations: add a token, add a record, extend a record, and, to
break things, remove a record and overwrite an element.

| | Case | Result |
|---|---|---|
| a | A value count, any addition | Rate 1. $[c_v, c_v + B]$, exact for one count. All counts together: the box lets each rise by $B$; truly they rise by $B$ in total. **Loose.** |
| b | A token count; the token's elements are also element items | Adding token $q$ has size $\lvert q \rvert$, so the count rises by at most $B / \lvert q \rvert$: long keys cost more. The same $\lvert q \rvert$ elements are $\lvert q \rvert$ changes of kind *element*. Kind by kind the premise holds; **with one budget shared by all kinds it fails** ($2\lvert q \rvert > \lvert q \rvert$). Dead: the shared budget. |
| c | $x_1$ = size / records | Under "extend": $[x_1, (\text{size}+B)/\text{records}]$, exact. Under "add a record": the box gives a low end of $\text{size}/(\text{records}+B)$; the true low end is $(\text{size}+B)/(\text{records}+B)$. Sound, **loose**: the corner adds records without their elements. |
| d | $x_2$ = largest | At most $\text{largest} + B$. Exact. |
| e | $x_3$ = entropy | All sums in $O_j$: **no bound** from the corner rule, though the entropy plainly cannot move far under a small budget. |
| f | $x_4$ = distinct tokens | The corner turns on every key at once: the bound is the size of the vocabulary. The truth is $x_4 + B$. **Useless**, for the same reason as (a). |
| g | $x_1$ with "remove a record" | The corner has records at 0 and size unchanged, where the readout's convention reads 0. Evaluated there, the "upper bound" is 0, below the present value. **Unsound unless the readout is monotone on the whole box** (read $a/0$ as $+\infty$ for $a > 0$). This is why step 5 asks for it. |
| h | One added element completes a record whose other elements were already in the input | The change adds a long item for a cost of 1. Either its size is 1 and the rate is infinite, or its size is its length and the premise fails. **Sound either way, but empty** for a kind that old elements can complete, unless such changes are counted apart (an edit makes at most a fixed number of them). This is what A' called boundary effects. |
| i | Overwrite one element that locates items (a length field) | One element rewrites a whole record: as (h), the rate is infinite and the interval is the direction. This is "a header field covers its whole range with one write", and the theory gives the right answer for it: **nothing beyond the sign**. |
| j | Remove the largest record | The fall of the maximum has no rate; the bound is per file, from the item table (step 4). |
| k | A score that falls with two value counts | The worst corner raises both by $B$; the attacker has $B$ in total. **Loose across features**, as (a) is across sums. A score that rises with shares does not suffer from it: with a share read as its count over the total, the corner puts every share at $c_i/(n+B)$, and adding $B$ elements of one value does lower all the other shares to exactly that. |

**Dead on arrival, with the case that killed each:** one budget shared across kinds (b); the corner rule under the
readout rule's own hypothesis (g); "the worst case is the whole budget spent on one kind of change" as a general
rule (f: the most distinct tokens come from spreading the budget).

**The one systematic loss: the sums share one budget and the box forgets it** (a, c, f, k). Two repairs are sound
and elementary; I believe both and have written out neither.
- *Total movement.* The budget bounds the total of the movements of all sums in a support, not only each one. A
  readout that adds up one term per sum (a distinct count) then moves by at most that total: $x_4 \le x_4 + B$.
- *Pure edits.* For a ratio or a share, the extremes over everything the budget allows are reached by spending the
  whole budget on one kind of change (a ratio of totals is largest or smallest at a vertex of the set of affordable
  mixtures). This gives (c) exactly, and a share's interval exactly: $[c_i/(n+B),\ (c_i+B)/(n+B)]$. For the entropy
  it gives the exact low end (add $B$ copies of one value), not the high end.

Whether either repair is worth its definitions depends on which features an instance needs them for. Undecided; I
would not add them before that is known.

### F.5 What is elementary, and the closest work

- **Intervals after signs is the textbook order of abstract interpretation.** The bound on sums is a Lipschitz
  argument, the corner rule is interval arithmetic for monotone functions, the worst corner is the fact that a
  monotone function on a box is smallest at a corner, and the pure-edit repair is a standard fact about ratios on
  polytopes. None of this is new mathematics. What would be ours is what was ours for signs: the priced signature
  (a budget in elements turned into bounds per kind of item), and the chain from a budget in the problem space to a
  certificate with one evaluation.
- **Closest work on the task, checked in `papers/`:** Chen et al. (CCS 2021, `chen2021learning.pdf`) train security
  classifiers with global robustness properties that include monotonicity and a *small neighborhood* property
  ($d(x, x') \le \epsilon \Rightarrow \lvert F(x) - F(x') \rvert \le c \cdot \epsilon$, with $d$ the largest change
  of a feature "normalized by the standard deviation of that input feature"). The properties come from "security
  domain knowledge"; the neighborhood is chosen, not derived. That is the same gap that Incer et al. and Gimenez et
  al. leave for directions. **Not checked, from memory only:** Chen et al., *Cost-Aware Robust Tree Ensembles for
  Security Applications* (USENIX Security 2021), who give each feature a hand-assigned box by its cost of change
  and train trees against it; and Vos and Verwer's robust trees for user-specified per-feature ranges. Both must be
  read before any claim; neither PDF is in `papers/`.

### F.6 What is proved, what is believed, what is unknown

- **Proved (in F.3):** the bound on additive sums; the upper side of a max pool; the corner rule; that the intervals
  contain Theorem 1's table as the case of an unlimited budget; the worst corner, with Corollary 1 as a special
  case.
- **Believed:** the lower side of a pool from the item table; the two repairs of F.4.
- **The premise carries the difficulty, more than covering does.** "Covers within budget" must hold for every edit,
  and cases (h) and (i) show how it degrades: where an element can complete or relocate an item, the rate is
  infinite and the theory returns the sign. That is correct behaviour, and it means the bounds have content only
  for kinds whose items are made of the attacker's own elements.
- **The payoff on EMBER is unknown, and the paper's own numbers point to a small one at the present budget.** From
  §5.4's price list (pilot, one seed): the detector on the sums loses 7.8 points at 1% false positives. The items
  the paper reports: 3.9 from the entry write (a copied signature: one write), and, measured before the entry write
  was added, 2.1 from import addition, 1.4 from the header overwrites, and 0.2 from dropping the two-sided features.
  A copied signature and a header field are case (i). An import bucket is a count; I expect its useful thresholds
  to lie at a few imports (not checked), and an import costs a few dozen bytes, so any byte budget covers them.
  What sizes could give back at 1% is therefore the 0.2 points, plus
  whatever a count's constraint costs on the byte and string totals (unmeasured; leaving out append moved detection
  by at most 0.4). At 0.1% false positives the two-sided features are worth 5.2 points, the one item the paper says
  stands out above retraining noise. Whether sizes can recover part of it depends on *why* those features are
  two-sided: through a rename or a header write (infinite rate, nothing to gain) or through bounded in-place writes
  and normalization (finite rate).
- **What would settle it, and it is data, so I stop here:** reading the stored derived table of the sums for the
  two-sided sums, operation by operation, and classing each as infinite rate or finite. No run, no training. Only
  if a meaningful share is finite would a detector be worth training.
- **Where the theory has value whatever EMBER says.** (1) It states what the sign table discards and when nothing
  is lost: where one element can flip a feature, every positive budget is unlimited, and the direction is the whole
  truth. That is a reason, inside the theory, for why directions are the right object for structural features.
  (2) A domain whose budgets are small against its totals (counts and means over traffic, a limit on added
  components) would use the intervals directly. (3) The item table gets a role in the theory (pools).

### F.7 Decisions for the user

1. Is the note's core (steps 1-6) the statement you had in mind, or is something else meant by "bounds on size"?
2. The premise is stated per edit and kind by kind, which keeps the result parallel to Theorem 1 but leaves the
   boundary effects of case (h) as an infinite rate. The alternative is to state it for the net change of a whole
   sequence, with an allowance per kind for boundary items: tighter, one more constant per kind, and the instance
   must then argue about sequences. I would keep the simple form until an instance needs the other.
3. The two repairs of F.4: wait for evidence that a feature needs them (my advice), or work them out now.
4. May I read the stored derived table to class the two-sided sums (F.6)? It decides whether EMBER can show
   anything, and it is the cheapest way to kill or keep the application.

## G. The user's review of part F, and the read of the derived table (session 76, 2026-11-16)

### G.1 The user's answers and comments

1. The statement of F.3 is what was meant by "bounds on size".
2. The stored tables may be read.
3. The simple premise (per edit) is preferred; the approach is to be discussed further.
4. The two repairs "don't sound unreasonable"; to be discussed.

Comments. F.3 points the right way but may be more complicated than is necessary or useful, and the framework
section has little room left. **How the material enters the framework (woven through, or a subsection of its own)
is the critical decision.** The counterexample hunt was confusing: does F.3 work as written, are the repairs the
remedy, and do they touch the established framework? "Priced signature" and "covers within budget" are unclear, and
the notation for the size of a change does not help. The size-0 case: is it possible at all; the language around
infinity is sloppy. Of all contents an edit may write, only the one that moves the sum most counts (the user's
question; yes). The bound on additive sums is concise, the pool part long-winded: shorter, and in the appendix. The
display math did not render in the VS Code preview (fixed: `$$` in place of `\[ \]`).

### G.2 Answers recorded

- **F.3 is sound as written.** The three dead items of F.4 are simpler forms tried before F.3 was written, and F.3
  already avoids each: sizes are counted kind by kind (case b), the corner rule asks for a readout monotone on the
  whole box (case g), and the third (case f) was a shortcut that F.3 never uses.
- **The repairs concern tightness, not soundness,** and belong to the new part only. Nothing established
  (Definitions 1-10, Proposition 1, Theorem 1, Lemma 1, Corollary 1) would change.
- **A share needs no repair if it is read as its count over the total,** with the total as a sum of its own (rate
  1). The ratio row of Table 1 then gives $[c/(n+B),\ (c+B)/n]$: the low end is exact and the high end is loose
  only by the factor $(n+B)/n$. Read by the normalized-bin row, the low corner raises every other count by $B$ and
  gives $c/(n+255B)$ for a byte histogram.
- **No infinity is needed.** A sum either *has a rate* (a number $u$ such that no change raises it by more than $u$
  times its size) or has none and keeps its direction from Theorem 1. The bounded statement then sits on top of
  Theorem 1 instead of containing it. A change that is not paid for by written elements does occur: one written
  element that makes the parser find other items (cases h and i). Such sums have no rate.
- **Simpler form proposed:** one definition (the size of a change, the cost of an edit, and the premise that an
  edit's changes of each kind total at most its cost; no name "priced signature"), one definition of a rate, one
  proposition for additive sums, one corollary for the detector. Pools keep their direction in the body.

### G.3 The read: which two-sided columns could a budget bound?

Read: `artifacts/experiments/a_directions_derived_sums_loose/directions_sums.csv` (the pilot's table, population
variant, with the entry write) and `a_price_list/table.json` (pilot, before the entry write). The scale-up's
training table and price list are on tigris and were not read. Classes by Claude's reading of each mechanism, not
by a computation.

Of 3,655 columns: 1,978 up, 203 fixed, 1,474 two-sided (dropped by the monotone detector).

| Class | Columns | Count |
|---|---|---|
| No rate: one write or a few bytes move it across its range | header fields 25, rich header 33, signature 8, directory entries 8, start bytes 2, section buckets and overlay features 216, split section buckets 400 (a rename moves a section's whole contribution to another bucket) | 692 |
| Not modeled | parser warnings | 88 |
| Bounded by a budget | byte shares 256, whole-file string features 177, file entropy 1, four pattern counts over the body | 438 |
| Bounded under appends and in-place writes, not when content shifts (the windows are tiled anew) | byte-entropy shares | 256 |

Two facts decide what this is worth.

1. **The bounded classes are already in the detector as counts.** The re-encoding over sums holds the same bytes,
   windows and strings as raw counts over the body (683 columns, marked up, read by the monotone detector). What a
   bound could add is their normalized forms: a byte's share, the mean string length, the entropy.
2. **The paper's budget is large against the files.** It is 5% of the file or 512 KB, whichever is larger; every
   file is below 4 MB, so the budget is always 512 KB, at least 12.8% of the file and more than the whole file for
   about half of the pilot's files. A share $s$ of a file of $n$ bytes can then truly move to anywhere in
   $[s\,n/(n+B),\ (s\,n+B)/(n+B)]$: for $B = n$, $[s/2,\ s/2 + 1/2]$. This is arithmetic, not looseness.

The ceiling for all 1,474 columns together is the price list's "dropped only" row: 0.2 points at 1% false
positives, 5.2 at 0.1%. The same list shows a swing of 3 points at 0.1% in the wrong direction between two variants
(the threat model without appends detects less than with them), so the 5.2 is not far above retraining noise, and
it is shared with the 692 columns that no budget bounds.

**Result: at the paper's budget, bounds on size have nothing to show on EMBER.** They could show something only
along a budget axis (certified detection at 1 KB, 4 KB, ... , 512 KB), which is a new experiment with a detector
trained for it. Not proposed here; it is the user's decision whether that is wanted.

**An observation for the design.** For in-place writes the binding limit is not the byte budget but where the
operation can write (a name field, a slack range): a capacity per file, not a rate. A rate times 512 KB says nothing
there. Decision 12's 96 printable counts under a rename may be of this kind (a guess: the files have not been
identified and the table is on tigris).

### G.4 The user's idea: a "somewhat monotone" detector (session 76)

**The idea (user).** The monotone detector is robust because its score never falls along the directions the table
allows. If the framework also says how far each feature can move, the constraint could be relaxed: a score that is
"somewhat monotone" might stay robust, represent more, and lose fewer detections at the same false-positive rate.

**It is step 6 of F.3 put to use.** A relaxed score has no guarantee by construction; its guarantee is per file: the
file is certified if the lowest score the attacker can reach from it is above the threshold (for a score monotone
in each feature it reads, in any direction: the worst corner). The number reported becomes certified detection at a
budget, not detection.

**Without a bound on size the relaxation cannot help (argued, elementary).** Let $h$ be any score and
$C(\mathbf{x})$ the set of vectors the sign table allows from $\mathbf{x}$. Let
$h^{\downarrow}(\mathbf{x}) = \inf_{\mathbf{x}' \in C(\mathbf{x})} h(\mathbf{x}')$, the lowest score the table lets
the attacker reach. Then (i) $h^{\downarrow} \le h$; (ii) a file is certified for $h$ at threshold $t$ exactly when
$h^{\downarrow}(\mathbf{x}) \ge t$; (iii) $h^{\downarrow}$ is monotone with respect to the table, because directions
are closed under addition, so $C(\mathbf{x}') \subseteq C(\mathbf{x})$ for $\mathbf{x}' \in C(\mathbf{x})$. So the
strictly monotone score $h^{\downarrow}$ detects, with a guarantee, exactly the files $h$ certifies, and flags no
benign file that $h$ does not flag. Every relaxed detector whose guarantee rests on signs is matched or beaten by a
strictly monotone one. Caveats: this is about what a score can represent, not about what training finds, and
$h^{\downarrow}$ of a tree ensemble need not be a tree ensemble of the same size. Not the converse of Corollary 1
closed in sessions 71-73 (that one, "unevadable implies monotone", is false); not looked for in the literature.

**With a budget the argument fails, and that is where the idea lives.** The set reachable within budget $B$ is not
closed in the same way (from an edited file the attacker's reach, counted from that file, goes further), so the
lowest reachable score is not monotone, and a relaxed detector can truly do better than every strictly monotone
one: it may, for instance, lower the score on a count far above anything the budget reaches from the file at hand.
The gain is the room between how far the budget moves a feature and the scale on which the feature separates
malware from benign files.

**On EMBER that room is small where the cost is (the pilot's price list, one seed).** Of the 7.8 points at 1%
false positives: 3.9 the copied signature and 1.4 the header fields (one write moves the feature across its range:
no bound, nothing to relax); 2.1 import addition (an import costs a few dozen bytes, so even 1 KB buys dozens and
512 KB thousands, and any split at "has this import" is crossed); the byte, window and string counts cost about
nothing measurable (the threat model without appends: 0.3 points, within noise), and their reach at 512 KB is 12.8%
to more than 100% of the file. What a relaxation could give back at 1% is a few tenths of a point. At 0.1% it is
not known (the 5.2 points of the two-sided features, part of which no budget bounds, against about 3 points of
noise). The scale-up's price list (on tigris, not read) could change the split.

**Where it would pay:** an instance whose costly constraints sit on counts or totals that the budget moves little
against their scale.

## H. The hand-off: the statements in the form to write from (session 76, 2026-11-16)

Written so that a later session can turn this into manuscript text without redoing the mathematics. **H supersedes
F.3 as the form to use;** F stays as the record of how it was found. Everything in H.1-H.5 is proved here. Nothing
is in the manuscript, and whether and where any of it enters is the user's decision (H.9).

Notation as in §3: threat model $\mathcal{M}$, population $Z$ closed under $\mathcal{M}$, signature $\Delta$,
contributions $\nu_\tau$, sums $s_k$, readouts $\rho_j$ with the sets $P_j$, $N_j$, $O_j$ of the readout rule,
derived table $D_\Delta$.

### H.1 Two definitions

**Definition (cost and size).** A *cost* gives every transformation $T \in \mathcal{M}$ applied to an input $z$ a
number $\kappa(T, z) \ge 0$, for example the number of elements it writes or adds. The cost of a sequence of
transformations is the total of its steps, and $\mathcal{R}_B(z)$ is the set of feature vectors of the inputs
reached from $z$ by sequences of cost at most $B$. A *size* gives every change $c \to c'$ in $\Delta_\tau$ a number
$w_\tau(c \to c') \ge 0$, for example the number of written elements among the item's members. The signature
*covers $\mathcal{M}$ at cost* over $Z$ if every $T \in \mathcal{M}$ applied to any $z \in Z$ has a delta made of
changes in $\Delta$ such that, for each kind $\tau$, the sizes of its changes of kind $\tau$ total at most
$\kappa(T, z)$.

Remarks. (1) Covering at cost implies covering. (2) The sizes are totalled **per kind**, never over all kinds: one
written element is a member of items of several kinds (in Algorithm 1 an element of an added token is also an
*element* item), so the sizes over all kinds exceed the cost. (3) No name is needed for the pair of a signature and
its sizes.

**Definition (rates).** An additive sum $k$ *rises at rate at most* $u_k$ if there are numbers $u_{k\tau} \ge 0$,
one per kind that contributes to $k$, with $u_k = \sum_\tau u_{k\tau}$ and
$$
  \nu_\tau(c')_k - \nu_\tau(c)_k \;\le\; u_{k\tau}\, w_\tau(c \to c') \qquad \text{for every change in } \Delta_\tau .
$$
It *falls at rate at most* $l_k$ in the same way, with $\nu_\tau(c)_k - \nu_\tau(c')_k \le l_{k\tau}\, w_\tau(c \to c')$.

Remarks. (1) Most sums receive contributions from one kind; then the rate is that kind's. (2) The rate is a worst
case over every content the attacker may write: if one content moves the sum by 255 per element and another by 0,
the rate is 255. (3) If no change raises $k$ (its direction lacks $+$), it rises at rate 0. (4) **A sum may have no
rate.** If one written element makes the extractor find an item made of elements that were already there (a length
field, a delimiter that completes a record), the sum moves by an amount that no size pays for, and no number $u_k$
works. Such a sum keeps its direction from Theorem 1 and gets nothing more. No infinity appears anywhere.

### H.2 Proposition (bounded sums)

*Let $\Delta$ cover $\mathcal{M}$ at cost over a population $Z$ closed under $\mathcal{M}$, and let $z \in Z$ and
$z'$ be reached from $z$ by a sequence of cost at most $B$. If the additive sum $k$ rises at rate at most $u_k$,
then $s_k(z') - s_k(z) \le u_k B$. If it falls at rate at most $l_k$, then $s_k(z') - s_k(z) \ge -l_k B$.*

*Proof.* Let the steps be $T_1, \dots, T_m$ with costs $\kappa_i$, from $z_{i-1}$ to $z_i$, $z_0 = z$. Every $z_i$
is in $Z$ by closure, so step $i$ has a delta made of changes $C_i$ in $\Delta$ whose sizes total at most
$\kappa_i$ in each kind. By Proposition 1 (i), the step changes $s_k$ by the total of
$\nu_\tau(c')_k - \nu_\tau(c)_k$ over $C_i$. Each term is at most $u_{k\tau}$ times the size of its change (also
when the term is negative, since the right side is not), so the changes of kind $\tau$ add at most
$u_{k\tau} \kappa_i$ and the step at most $u_k \kappa_i$. Adding the steps gives $u_k \sum_i \kappa_i \le u_k B$.
The lower bound is the same argument with the signs exchanged. $\qed$

**The interval of a sum.** Each side comes from the best fact available: the direction (if $d_k$ lacks $+$ the sum
does not rise at all, by Theorem 1), else the rate, else nothing. Then clip to the values the sum can take (a count
is not negative). Write $[\underline{s}_k, \overline{s}_k]$; a side with neither fact is *open*.

### H.3 Proposition (the corner rule)

*Let the readout of feature $j$ rise with $P_j$ and fall with $N_j$ **on the box** of the intervals of the sums in
its support, and let every sum in $O_j$ be fixed. If the sides $\underline{s}_k$ for $k \in P_j$ and
$\overline{s}_k$ for $k \in N_j$ are not open, then every $\mathbf{x}' \in \mathcal{R}_B(z)$ has
$x'_j \ge \rho_j(\mathbf{a})$, where $\mathbf{a}$ holds $\underline{s}_k$ on $P_j$, $\overline{s}_k$ on $N_j$ and
$s_k(z)$ on $O_j$. With the opposite sides, $x'_j \le \rho_j(\mathbf{b})$ for the opposite corner $\mathbf{b}$.*

*Proof.* By H.2 and Theorem 1, the sums of the reached input lie in the box. They are at or above $\mathbf{a}$ on
$P_j$, at or below it on $N_j$, and equal to it on $O_j$, and the readout rises with $P_j$ and falls with $N_j$
between any two such points of the box. $\qed$

"On the box" means: for any two points of the box, not only for values that occur in inputs. The forms of Table 1:

| Readout | Monotone on the box? |
|---|---|
| identity, monotone $g$, distinct count | always |
| ratio $a/b$ | on a box with $\underline{a} \ge 0$ and $\underline{b} > 0$. If $\underline{b} = 0$ the upper end is **open**: the corner $(\overline{a}, 0)$ does not occur, and the convention reads 0 there, which is below the present value (F.4, case g) |
| normalized bin | on a box of non-negative counts |
| any other | no bound; the feature keeps its direction |

A feature that fits two rows gets the intersection of the two intervals. A share of a histogram is the case that
matters: read as a normalized bin it gets the exact high end, and read as its count over the total (the total as a
sum of its own, rate 1) it gets the exact low end. Under additions of $B$ elements the two give
$[\,c/(n+B),\ (c+B)/(n+B)\,]$, which is exact. No further rule is needed for shares.

A side of a feature's interval is: the present value if the direction lacks that sign; else the corner value if the
proposition applies; else open.

### H.4 Corollary (a certificate from one evaluation)

*Let the score $h$ be nondecreasing in the features of a set $A$, nonincreasing in those of a set $A'$, arbitrary
in features that the table marks fixed, and let it read no other feature. Suppose the interval of every feature in
$A$ has a low end and that of every feature in $A'$ a high end, and let $\mathbf{x}^{c}(z, B)$ hold these ends and
$\varphi_j(z)$ on the fixed features. Then $h(\mathbf{x}') \ge h(\mathbf{x}^{c}(z, B))$ for every
$\mathbf{x}' \in \mathcal{R}_B(z)$.*

*Proof.* $\mathbf{x}'$ is at or above $\mathbf{x}^{c}$ on $A$, at or below it on $A'$, equal on the fixed features,
and $h$ reads nothing else. $\qed$

Reading. The file $z$ is *certified at budget $B$* if $h(\mathbf{x}^{c}(z, B))$ is above the threshold: one
evaluation of the score, no solver. If $h$ is monotone with respect to the table, $\mathbf{x}^{c}$ is $\varphi(z)$
for every $B$, which is Corollary 1. The guarantee is per file and per budget, counted from the file $z$, as
certified accuracy at a radius is for robust classifiers; it is not a property of the score alone.

### H.5 Proposition (with directions alone, strict monotonicity loses nothing)

Call $\mathbf{x}'$ *allowed from* $\mathbf{x}$ under a table $D$ if the change of every feature has a sign in its
direction. A score $h$ *certifies* $\mathbf{x}$ at threshold $t$ under $D$ if $h(\mathbf{x}') \ge t$ for every
$\mathbf{x}'$ allowed from $\mathbf{x}$.

*For any score $h$ bounded below, let $h^{\downarrow}(\mathbf{x})$ be the infimum of $h$ over the vectors allowed
from $\mathbf{x}$. Then (i) $h^{\downarrow}$ is monotone with respect to $D$; (ii) $h$ certifies $\mathbf{x}$ at $t$
exactly when $h^{\downarrow}(\mathbf{x}) \ge t$; (iii) $h^{\downarrow} \le h$. So at every threshold the monotone
score $h^{\downarrow}$ detects exactly the inputs that $h$ certifies and flags no input that $h$ does not flag.*

*Proof.* A direction contains 0 and is closed under addition (Appendix C), so $\mathbf{x}$ is allowed from itself,
which gives (iii), and what is allowed from an allowed vector is allowed, so for $\mathbf{x}'$ allowed from
$\mathbf{x}$ the infimum defining $h^{\downarrow}(\mathbf{x}')$ runs over a subset of the one defining
$h^{\downarrow}(\mathbf{x})$, which gives (i). (ii) is the definition. $\qed$

What it says. When the direction table is all that is known of the attacker, a relaxed ("somewhat monotone") score
with a certificate is matched at every operating point by a strictly monotone score: the same guaranteed
detections, no more false positives. What it does not say: (a) nothing about training (the best monotone score
need not be the one a learner finds, and $h^{\downarrow}$ of a tree ensemble need not be a tree ensemble of that
size); (b) nothing about detections without a guarantee, where $h$ may detect more; (c) it is relative to the
table, which may allow vectors no edit produces. It is elementary ($h^{\downarrow}$ is the largest monotone function
below $h$). It is **not** the converse of Corollary 1 that sessions 71-73 closed ("unevadable implies monotone",
false). **Not searched for in the literature.**

**With a budget the statement is false, by example (Algorithm 1).** One feature, the count $c$ of a value;
the threat model adds elements; cost and size count elements, so $c$ rises at rate 1 and its direction is up.
A malicious input has $c = 5$, a benign one $c = 150$. Every score monotone with respect to the table has
$h(5) \le h(150)$ and cannot detect the first without flagging the second. The score that is 1 for $c < 50$ and 0
otherwise is nonincreasing in $c$; at budget 20 the worst corner of the malicious input is $c = 25$, where the
score is 1: certified, and the benign input is not flagged. Without a budget the attacker adds 145 elements and
evades, as the proposition requires. So a relaxed detector can beat every strictly monotone one exactly when sizes
are known, and its gain is the room between how far the budget moves a feature and the scale on which the feature
separates the classes.

### H.6 The check on Algorithm 1

Operations: add a token $q$ (cost $\lvert q \rvert$), add a record of length $L$ (cost $L$), extend a record by
$m$ elements (cost $m$). Rates: a value count 1; a token count $1/\lvert q \rvert$; *records* 1 (a record of one
element); *size* 1. All fall at rate 0.

| Feature | Interval at budget $B$ | Against the truth |
|---|---|---|
| a token count | $[s_q,\ s_q + B/\lvert q \rvert]$ | exact |
| a value's share | $[c/(n+B),\ (c+B)/(n+B)]$ | exact (two rows intersected) |
| $x_1$ = size / records | $[\text{size}/(\text{records}+B),\ (\text{size}+B)/\text{records}]$ | high end exact; low end loose (the truth is $(\text{size}+B)/(\text{records}+B)$ when the mean exceeds 1): added records bring their elements, and the box does not know it |
| $x_2$ = largest | low end the present value; high end open | a pool; see H.7 |
| $x_3$ = entropy | none | truly bounded for a small budget; the rule gives nothing for "any other" |
| $x_4$ = distinct tokens | $[x_4,\ \text{number of keys}]$ | useless; the truth is $x_4 + B/\min \lvert q \rvert$ (H.7) |

With "remove a record" added to the threat model, *records* can fall to 0 within a large enough budget, and the
high end of $x_1$ is open (H.3's table).

### H.7 Proved or sketched, and not proposed for the manuscript

- **A max pool, upper side.** F.3, step 4. In the body a pool keeps its direction.
- **A max pool, lower side (sketch, believed complete).** Suppose one kind feeds the pool and every change that
  removes an item or lowers its contribution has size at least $\omega > 0$. Follow each item of $z$ through the
  replacements that keep or raise its contribution. A sequence of cost at most $B$ holds at most
  $\lfloor B/\omega \rfloor$ removing or lowering changes, so all but that many items of $z$ end with at least
  their contribution, and the pool ends at or above the contribution ranked $\lfloor B/\omega \rfloor + 1$ in the
  item table of $z$. This needs the item table, not the sums.
- **Sums that share the budget.** H.2 applied to a total: if every change raises the sums of a family by at most
  $u$ times its size in total, the rises of the family total at most $uB$ (same proof). This gives the distinct
  count $x_4 + B/\min \lvert q \rvert$. No feature of EMBER was found to need it.
- **Sums that move together** (the low end of $x_1$). A ratio of two totals takes its extremes when the whole budget
  goes to one kind of change. Believed, not written out, not needed on EMBER.
- **Capacity.** For in-place writes the binding limit is where the operation can write, not the byte budget (G.3).
  No statement has been worked out. This is the open design question if the direction is pursued on EMBER.

### H.8 The closest work, now read (PDFs in `papers/`)

- **Chen et al., *Cost-Aware Robust Tree Ensembles for Security Applications*, USENIX Security 2021**
  (`chen2021cost.pdf`). They "propose a new cost modeling method to capture the feature manipulation cost as
  constraint" and train tree ensembles against it. The constraint is a box per feature, asymmetric in the two
  directions, and it comes from the analyst: "we categorize attacker's cost of increasing and decreasing the value
  of each feature into one of the four categories: negligible, low, medium, and high costs. The categories are
  based on relative cost differences, rather than absolute scale." Case study: Twitter spam. So the object H.3
  computes (an interval per feature and direction) is the object they assume from "domain knowledge". They train
  against the box; H.4 certifies with one evaluation only for scores monotone per feature.
- **Vos and Verwer, *Efficient Training of Robust Decision Trees Against Adversarial Examples*, ICML 2021**
  (`vos2021efficient.pdf`; the arXiv version was read). GROOT: "we allow each feature to be perturbed with a
  user-specified parameter: either a maximum distance or constraints on the direction of perturbation." Again the
  per-feature range is given by the user.
- **Chen et al., CCS 2021** (`chen2021learning.pdf`): F.5.
- The relation to state, in their terms: these works take per-feature ranges as input and train against them; the
  bounds here would compute such ranges from an extractor and a budget on edits. The same relation as Theorem 1
  has to Incer et al. and Gimenez et al. Neither is in the bibliography yet.

### H.9 What is decided, and what is not

Decided by the user (G.1): this is the statement meant; the premise per edit; simpler is better; the pool passage
shorter and in the appendix. Not decided: whether any of this enters the manuscript, and in which form. Options,
with Claude's view:

1. **A paragraph in the discussion** on what the directions discard: where one write moves a feature across its
   range, the direction is all there is; where a feature moves little per element, a budget gives an interval
   (H.2-H.4, cited as a straightforward extension), which the paper does not evaluate. Claude: yes.
2. **H.5 beside Corollary 1** (a short proposition in §3.3 with its proof in Appendix C, or a sentence): with
   directions alone, asking for strict monotonicity loses no guaranteed detection. It answers "why constrain the
   model instead of certifying a free one" and says that §5.4's price is the price of the guarantee under the
   table and not of the model class, in the sense of H.5's caveats. Claude: worth the user's look; it touches how
   §5.4's number is read, so it must not be written without the user's agreement.
3. **A subsection of its own after Sound Directions** (two definitions, H.2, H.3 in a sentence, H.4; about 400-450
   words; proofs in Appendix C). Claude: only with a result behind it, either the budget curve on EMBER or a
   second instance. Not woven into §3.3: every result of §5 rests on signs alone.

On EMBER at the paper's budget nothing can be shown (G.3, G.4).

### H.10 Traps, for whoever writes the text

1. Sizes are totalled per kind. "One budget for all changes" is false (F.4, case b).
2. The corner rule needs monotonicity on the whole box. Never evaluate a ratio at a zero denominator; that end is
   open (F.4, case g).
3. Clip a sum's interval to the values it can take before using the corner rule.
4. No infinity. A sum has a rate or it has none.
5. The certificate is per file and per budget; a relaxed score is not robust by construction.
6. H.5 is about what a score can represent. Do not write that a monotone detector *is* as good as any other, and
   do not present it as a converse of Corollary 1.
7. All of it is elementary (a Lipschitz bound, interval arithmetic for monotone functions, a monotone function on a
   box, a monotone lower envelope). No claim of new mathematics; what is ours is the chain from a budget on edits
   to a certificate, as for signs.
8. No claim of a payoff on EMBER. The numbers in G.3 and G.4 are the pilot's, one seed.
9. A' is not a verdict (F.2), and is not to be cited as one.
10. Chen et al. and Vos and Verwer in their own terms, with the quotes of H.8 checked again against the PDFs.
11. Paper numbers from `manuscript/main.aux`. Text goes in uncommitted, for the user's review (resume prompt).
