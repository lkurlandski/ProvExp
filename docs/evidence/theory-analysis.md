# Theory analysis: the proof audit, and the theory in brief

Session 74 (2026-11-16), carrying out `docs/resume-prompt.md`. Parts A and B are stage 1. Parts C to E wait for the
user. Nothing here is applied: every change to the paper is given as old and new text and waits for a decision.
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

After the user has read A and B.

## D. Proofs or counterexamples for the chosen ideas

## E. What to do next
