# What robustness must cost, and how to lower what it need not

Session 71 (2026-11-15), Claude Fable 5.2. Question: of the 7.8 points of detection that the monotone detector on the
sums gives up at 1% FPR (93.5% to 85.7%, pilot), how much must *every* unevadable detector give up (intrinsic), how
much is lost because the table keeps only a sign per feature (abstraction), and how much because our GBDT is not the
best table-respecting detector (learner)?

> **Read section 7 first.** After the user's review (same session), §3.2 (anchored sums), §3.3 (verified signatures)
> and experiments 4 and 5 are **rejected**, and none of the mathematics here is a headline contribution. Sections 1 to
> 6 are kept as written, as the record of the analysis. **Section 9 is step 2's outcome: the converse of Corollary 1
> does not hold in general, and no second theorem comes of it.**

Paper numbers below are from `manuscript/main.aux`: Definition 7 (*Threat models and directions*), Definition 8
(*Changes and signatures*), Definition 9 (*Directions of sums*), Table 1 (direction rules of the readouts),
Proposition 1 (*Exact side effects*), Theorem 1 (*Sound directions*), Corollary 1 (*Robustness*), §5.4 (*What
Robustness Costs*), Table 5 (the detectors).

Confidence marks: **[proved]** a complete argument is given here; **[measured]** read from the pilot stores in this
session; **[believed]** my judgement, not proved or measured; **[memory]** a claim about literature that I did not
check against a PDF.

## 1. The answer in half a page

**The split as posed has no data-only answer, and the reason is itself a finding.** If "every detector, whatever its
form" is taken literally, the intrinsic cost is zero and so is everything else: on the 54,266 pilot test files, only 7
of the 27,105 malware files have any benign file that the table forces a monotone detector to flag along with them
[measured]. A detector that respects the table can therefore separate the sample perfectly, and so can any wider
class of unevadable detectors. No bound on parts 1 or 3 computed from data without a learner says anything, and
limiting the detector to its 5 most-used features does not rescue it (ceiling still 100% at 1% FPR). The cause is
that the table leaves 203 sums *fixed*, a detector may use fixed sums in any way it likes, and these 203 sums alone
split the 54,266 files into 40,266 groups. What generalizes is decided by the learner, not by the class.

**What the theory can say instead** is which *evidence* each kind of detector may use, exactly:

- A detector that respects the table is an **unrestricted detector on the fixed sums, plus malware evidence that can
  only accumulate on the one-sided sums, and nothing from the two-sided sums.** Our detector takes 80% of its split
  gain from the 203 fixed sums and 20% from the 1,978 one-sided ones [measured]. Under the full threat model with the
  entry write it has no *down* sum left at all, so outside the fixed sums it cannot hold any benign evidence.
- **Sums the attacker can set freely carry no information for any unevadable detector** (Proposition E, proved).
  This covers the overwritten header fields, the checksum, the DOS region and, with the entry write, the signature.
- **Table-monotone is necessary, not only sufficient, exactly when the table is complete**: when any two population
  vectors the table calls comparable are in fact linked by edits (Proposition B, proved, with the witness detector
  when it fails). The import block is complete up to the bytes an added import brings with it.

So for the three expensive operations (entry write 3.9, import addition 2.1, header overwrites 1.4), the table loses
nothing that a cleverer unevadable detector *on these sums* could keep. **I find no meaningful abstraction cost, and I
recommend against a relational extension of the table** (§3.1 gives it anyway, in one row of Table 1, with the reason
it buys nothing on EMBER).

**Where the 7.8 points probably lie** [believed, with the measurements that support it]:
about 4 are the entry write, and they are the price of an extractor that parses a signature without verifying it (the
signature sums were the detector's only *down* sums; a verified signature would be down-only again, which is what the
89.6% detector before the entry write already measures); 0.2 to 1 are evidence in freely settable sums; 1 to 3 are
the learner; the remaining 1 to 3 are one-sidedness of sums that mix the file's original content with content the
attacker adds (imports, strings, bytes).

**The learner part is real and cheap to test.** The monotone detector fits its own *training* files at 91.8% TPR
(1% FPR) where the unconstrained one fits them at 100.0% and the class allows 100% [measured]; every model stops at
the 500-iteration cap; and LightGBM runs with `monotone_constraints_method=basic`, which its documentation describes
as over-constraining [memory]. A training run takes about one minute.

**What I recommend.** (1) Run the five one-minute experiments of §4; they turn the split into four measured numbers.
(2) In §5.4, say what the cost is a cost *of* with the evidence reading above and Propositions B and E in two or three
sentences; optionally add the converse to §3.3 as a remark (about 120 words). (3) The lever that can lower the cost
is not the table but the **fixed share of the extractor**: sums over items the threat model cannot touch are fixed and
usable without constraint, and EMBER has few of them. A re-encoding that anchors sums to such items (§3.2) needs no
new concept in §3. Experiment 4 is its go/no-go. (4) "About one point" under this threat model with these features
is, in my judgement, out of reach; three to four points looks attainable if experiments 2, 4 and 5 come out as
predicted.

## 2. The mathematics

Notation follows §3. $Z$ is a population closed under $\mathcal{M}$. Write $z \leadsto z'$ if $z' = T(z)$ for a
finite sequence $T$ of transformations in $\mathcal{M}$ (the empty sequence included), so $\leadsto$ is reflexive and
transitive on $Z$. A detector reads a *representation* $r: Z \to \mathcal{Y}$, which is either the features
$\varphi$ or the sums $\mathbf{s}$ (the paper treats a sum as a feature under the identity readout), through a score
$h: \mathcal{Y} \to \mathbb{R}$. I use the paper's notion of robustness, the conclusion of Corollary 1:

> $h$ is **unevadable on $Z$** if $h(r(z')) \ge h(r(z))$ whenever $z \in Z$ and $z \leadsto z'$.

This does not look at labels: no edit lowers the score of *any* file of the population. (A weaker notion asks this
only of malware. With it, nothing at all is forced on feature vectors that no malware reaches, and every statement
below holds on the vectors malware can reach. I keep the paper's notion.)

### 2.1 Two orders and three classes of detectors

Plain version: there are two ways to say "vector $y'$ is at least as suspicious as $y$ must be". One is the truth
(some chain of edits leads from $y$ to $y'$). The other is the table's approximation (every coordinate moved in an
allowed direction). A detector is unevadable exactly when it respects the first; Corollary 1 builds detectors that
respect the second, which is a stronger demand.

On $r(Z)$ define

- the **reach order**: $y \preceq_R y'$ if there are $z_0, z'_0, z_1, z'_1, \dots$ with $z_i \leadsto z'_i$,
  $r(z_0) = y$, $r(z'_i) = r(z_{i+1})$, and the last $r(z'_m) = y'$ (the transitive closure of "reachable", needed
  because two files can share a vector);
- the **table order**: $y \preceq_D y'$ if the change $y'_j - y_j$ of every coordinate $j$ has a sign in $D_j$.
  Spelled out: equal on every fixed coordinate, $\le$ on every up coordinate, $\ge$ on every down coordinate, anything
  on a both coordinate. It is reflexive because every direction contains 0, and transitive because directions are
  closed under addition (Appendix C, *Directions*).

Let $\mathcal{H}_R$ and $\mathcal{H}_D$ be the scores that never fall along $\preceq_R$ and along $\preceq_D$, and
$\mathcal{H}$ all scores. "Monotone with respect to $D$" in §3.3 is membership in $\mathcal{H}_D$.

**Proposition A (characterization).** [proved] $h \circ r$ is unevadable on $Z$ if and only if $h \in \mathcal{H}_R$.
If $D$ is sound for $\mathcal{M}$ over the closed $Z$, then $\preceq_R\ \subseteq\ \preceq_D$ on $r(Z)$, hence
$\mathcal{H}_D \subseteq \mathcal{H}_R \subseteq \mathcal{H}$.

*Proof.* If $h \in \mathcal{H}_R$ and $z \leadsto z'$, then $r(z) \preceq_R r(z')$ by definition, so the score does
not fall. Conversely, if $h \circ r$ is unevadable, each link $z_i \leadsto z'_i$ of a chain gives
$h(r(z_i)) \le h(r(z'_i))$, and $r(z'_i) = r(z_{i+1})$ joins the links. For the inclusion: by the second part of
Theorem 1's proof, each link moves every coordinate with a sign in $D_j$, and the table order is transitive. $\square$

The first inclusion is Corollary 1, and it is Gimenez et al.'s Proposition 1 (checked in the PDF: "if $\phi$ is
monotonically increasing w.r.t. $\preceq_M$ and $f$ is monotonically increasing w.r.t. $\le$, then $f$ is robust").
The "if and only if" is elementary order theory; I would not present it as a result of ours.

This gives the split a precise meaning. For a false-positive rate $\alpha$ let $\tau(\mathcal{C})$ be the best
detection any score in a class $\mathcal{C}$ achieves. Then

$$
\underbrace{\tau(\mathcal{H}) - \tau(\mathcal{H}_R)}_{\text{intrinsic}}
\;+\; \underbrace{\tau(\mathcal{H}_R) - \tau(\mathcal{H}_D)}_{\text{abstraction}}
\;+\; \underbrace{\tau(\mathcal{H}_D) - \tau(\text{our GBDT})}_{\text{learner}}
\;=\; 93.5 - 85.7 .
$$

One fact about the last term: a tree ensemble with per-feature constraints (increasing in up, decreasing in down, no
constraint on fixed, not reading both) can represent every function in $\mathcal{H}_D$ on a finite set of vectors
[proved: one full tree with a leaf per cell does it]. So the learner term is never a limit of what the model *can*
express; it is what training finds and what generalizes.

### 2.2 When is "monotone with respect to the table" necessary?

Plain version: the table is the right test for unevadability exactly when it never calls two vectors comparable that
no edits connect. Where it does, a detector exists that no edit evades and that the table rejects.

Call $D$ **complete** on $r(Z)$ if $\preceq_D\ \subseteq\ \preceq_R$ there (with soundness: the two orders coincide).

**Proposition B (converse of Corollary 1).** [proved] Let $D$ be sound for $\mathcal{M}$ over the closed $Z$.

1. If $D$ is complete on $r(Z)$, every unevadable $h \circ r$ is monotone with respect to $D$ on $r(Z)$:
   $\mathcal{H}_R = \mathcal{H}_D$ there, and the abstraction cost is zero.
2. If $D$ is not complete, pick $y \preceq_D y'$ in $r(Z)$ with $y \not\preceq_R y'$. The score
   $h(u) = 1$ if $y \preceq_R u$ and $0$ otherwise is unevadable and is not monotone with respect to $D$.

*Proof.* (1) is Proposition A with equal orders. (2) The set $\{u : y \preceq_R u\}$ is closed upwards under
$\preceq_R$, so $h \in \mathcal{H}_R$ and Proposition A applies; $h(y) = 1 > 0 = h(y')$ although $y \preceq_D y'$.
$\square$

(A score that is monotone on $r(Z)$ extends to one that is monotone on all of $\mathcal{Y}$, by
$\bar h(u) = \sup\{h(v) : v \in r(Z),\ v \preceq_D u\}$ and the infimum of $h$ where no such $v$ exists; so "on
$r(Z)$" loses nothing.)

**What exactly breaks completeness.** Take the sums as the representation and the additive sums first. By Proposition
1(i), an edit whose delta is made of changes $(\tau_i, c_i \to c'_i)$ moves the additive sums by
$\sum_i \mathbf{g}_i$ with $\mathbf{g}_i = \nu_{\tau_i}(c'_i) - \nu_{\tau_i}(c_i)$. Call these the **change vectors**
of the signature, $G_\Delta$. Between the truth and the table sits a third order, $\mathbf{a} \preceq_\Delta
\mathbf{b}$ if $\mathbf{b} - \mathbf{a}$ is a finite sum of change vectors, and

$$ \preceq_R \;\subseteq\; \preceq_\Delta \;\subseteq\; \preceq_D . $$

The table can be incomplete in two ways, and only two:

- **Signature slack** ($\preceq_R \subsetneq \preceq_\Delta$): the signature allows a combination of changes that no
  sequence of edits produces. Sources in our instance: positions an overwrite shares with the parser, where the
  signature allows "any change to the items of that kind"; a byte budget; changes that only occur together.
- **Sign slack** ($\preceq_\Delta \subsetneq \preceq_D$): the table replaces the set of change vectors by its sign
  pattern, the smallest box (a product of $\{0\}$, $[0,\infty)$, $(-\infty,0]$, $\mathbb{R}$) that contains them. It
  forgets that sums move *together* (one item feeds several sums) and *by how much*.

**Sign slack is smaller than it looks**, because population vectors obey identities. Example, the import block: one
added import raises its library bucket $a$, its function bucket $b$ and the import count $n$ by one, so the change
vectors are $e_a + e_b + e_n$, never $e_a$ alone. But every population vector satisfies
$\sum_a u_a = \sum_b v_b = n$, so any two population vectors with $(u, v, n) \le (u', v', n')$ coordinate-wise differ
by a non-negative integer vector with equal totals in the three parts, and such a vector is a sum of terms
$e_a + e_b + e_n$ (match the unit increases of $u$ with those of $v$ in any way). With attacker-chosen names every
pair $(a, b)$ is available (Appendix C, *Hashed keys*). So on the import block the table order *is* the change order
[proved for the block]. What remains is that an added import also brings bytes and strings into other sums; a
detector could in principle fall in an import bucket if it rises at least as much with those bytes. I see no useful
detector of that kind [believed].

The same reasoning covers a replacement that moves an item between keys (a renamed section moves between name
buckets): each bucket is two-sided, the total over buckets is an identity of the population, and nothing is hidden.

### 2.3 Sums the attacker can set freely carry no robust information

Plain version: if the attacker can give any file the value that any other file has on some sums, and leave the rest
alone, then an unevadable detector's score cannot depend on those sums at all. This is the one statement about
*every* unevadable detector that I can prove and that has teeth.

Call a set $J$ of sums **free** over $Z$ if for all $z, \tilde z \in Z$ there is $z'$ with $z \leadsto z'$,
$s_J(z') = s_J(\tilde z)$, and $s_k(z') = s_k(z)$ for every $k \notin J$.

**Proposition E (free sums).** [proved] If $J$ is free over the closed $Z$ and $h \circ \mathbf{s}$ is unevadable on
$Z$, then $h(\mathbf{a}) = h(\mathbf{b})$ for all $\mathbf{a}, \mathbf{b} \in \mathbf{s}(Z)$ that agree outside $J$.

*Proof.* Take $z$ with sums $\mathbf{a}$ and $\tilde z$ with sums $\mathbf{b}$. Freedom gives $z \leadsto z'$ with
$\mathbf{s}(z') = \mathbf{b}$, so $h(\mathbf{a}) \le h(\mathbf{b})$. By closure $z' \in Z$, and freedom applied to
$z'$ with target $z$ gives $z' \leadsto z''$ with $\mathbf{s}(z'') = \mathbf{a}$, so $h(\mathbf{b}) \le
h(\mathbf{a})$. $\square$

Consequences. (i) Dropping a free sum is not a choice of our construction: every unevadable detector on these sums
does the same. (ii) Its cost has an honest estimate that needs no monotone learner: train the *unconstrained*
detector with and without the free sums. For the table before the entry write this is the "drop-only" detector of
§5.4, 93.5 to 93.3 at 1% FPR and 84.4 to 79.2 at 0.1% (it drops every two-sided sum, free or not, so it is an upper
estimate). (iii) Not every two-sided sum is free. A sum is two-sided as soon as one change raises it and another
lowers it; it is free only if the attacker can *place* it. In our instance the overwritten header fields, the
checksum and the DOS region are free by construction (an overwrite copies any value).

**The signature under the entry write** is free in one direction and nearly free in the other. Clearing the entry
removes the signature and changes nothing else. Planting one appends the certificate, which also raises the size and
a few byte counts. The same two-step argument gives, for a file with sums $\mathbf{a}$ and the signature block $J$,

$$ h(\text{signed}, \mathbf{a}_{-J}) \;\le\; h(\text{unsigned}, \mathbf{a}_{-J}) \;\le\;
   h(\text{signed}, \mathbf{a}_{-J} + \text{the certificate's bytes}) . $$

A signature can lower an unevadable score by no more than a few kilobytes of appended bytes raise it. That is why the
entry write is expensive for *any* detector on these features, and why the price is a property of the extractor: it
parses the signature and does not verify it. An attacker without the signer's key cannot make a verified signature
appear, so a sum that counts only verified signatures would be down-only again.

### 2.4 Can parts 1 and 3 be bounded from data without training? No, and why

Plain version: the best any monotone detector can do on a sample is limited only by malware files that some benign
file "dominates" (same fixed values, at least as much of everything that can only rise). If such pairs are rare, the
bound is 100%.

**Proposition F (in-sample ceiling).** [proved] Let $M$ and $B$ be the malware and benign files of a sample. For
$S \subseteq M$ let $N_D(S)$ be the benign files $b$ with $r(m) \preceq_D r(b)$ for some $m \in S$. The best
detection at false-positive rate $\alpha$ of any score in $\mathcal{H}_D$ on the sample is
$\max\{|S|/|M| : |N_D(S)| \le \alpha |B|\}$. The same holds for $\mathcal{H}_R$ with $N_R(S) \subseteq N_D(S)$.

*Proof.* A thresholded score in $\mathcal{H}_D$ detects a set closed upwards under $\preceq_D$; if it detects $S$ it
detects $N_D(S)$. Conversely the indicator of the upward closure of $S$ is in $\mathcal{H}_D$ and flags exactly
$N_D(S)$ among the benign files. $\square$

This is the conflict-graph bound of the robust-classification literature (Bhagoji, Cullina and Mittal 2019; Pydi and
Jog 2020; Dai et al. 2023) written for an order instead of a ball [memory; none of the three is in `papers/`], and
the optimal monotone classifier on a finite order is classical (isotonic separation, maximum closure by minimum cut)
[memory]. Nothing here would be ours except the measurement.

**Measured** (hypothesis stated before the run: fewer than 1% of malware have a dominating benign file, so the bound
is vacuous). Pilot test set, loose sums table, 27,105 malware and 27,161 benign files:

| Detector may read | malware with a dominating benign file | ceiling at 1% / 0.1% FPR |
|---|---|---|
| all 203 fixed and 1,978 up sums | 7 (0.03%) | 100.0 / 100.0 |
| only the sums our detector splits on (186 fixed, 403 up) | 7 (0.03%) | 100.0 / 100.0 |
| its 5 most-used sums (4 fixed, 1 up) | 3.0% | 100.0 / 97.3 |
| its 20 most-used sums | 0.4% | 100.0 / 99.9 |

The 203 fixed sums split the 54,266 files into 40,266 groups, and only 50 groups hold both classes. Since
$\mathcal{H}_D \subseteq \mathcal{H}_R$, the ceiling for every unevadable detector is 100% as well: **on a sample,
the intrinsic cost is zero**, and a capacity limit in the number of features does not change that. The bounds of the
robustness literature bite for norm balls on images because the balls of differently labelled points overlap; here
the reachable sets are thin, because the fixed sums pin each file.

A held-out version does not escape this. The class by itself has no way to generalize: its minimal member (flag a
file only if it dominates a known malware file) flags almost nothing, because domination almost never happens. What
generalizes comes from the learner's bias (few features, few thresholds). So any estimate of
$\tau(\mathcal{H}_D)$ is the score of some learner, and the learner gap can only be bracketed from below by finding
better learners. I am confident of this negative.

### 2.5 What the cost is a cost of

Putting 2.1 to 2.4 together, a detector that respects the table may use

| Sums | Evidence it may use | In our detector (loose table) |
|---|---|---|
| fixed (203) | any, benign or malicious, in any combination | 80% of split gain |
| up (1,978) | malicious only: more can never look more benign | 20% of split gain |
| down (0; 10 before the entry write) | benign only | none left |
| both (1,474) | none | none |

and Propositions B and E say when a wider unevadable class could use more: never on free sums, never on a complete
block. The cost of robustness is therefore the detection carried by three kinds of evidence, each tied to what the
threat model lets the attacker do:

1. **Evidence in sums the attacker can place** (free; Proposition E).
2. **Benign evidence of the form "more of something"** in sums the attacker can only raise: a benign-looking import,
   more strings, more bytes of a kind. The unconstrained drop-only detector puts 19% of its gain on up sums used in
   the decreasing direction (imports 7.3%, body strings 3.7%, byte-entropy 3.5%, byte histogram 3.3%) and 21% on the
   ten sums the entry write frees (17.4% the certificate and debug directory fields, 3.8% the signature) [measured].
3. **What the learner fails to find** inside the class.

Kinds 1 and 2 are intrinsic *to the pair of extractor and threat model*, not to the threat model alone: a different
extractor can move evidence from kind 2 into the fixed sums (§3.2), or make a free sum one-sided (a verified
signature). That is the fourth term the question did not name, and I think it is the largest one that can be moved.

## 3. The extension

Two candidates. The first answers the question as asked (what the sign table forgets) and I recommend against it. The
second is what I think can lower the cost; it adds nothing to §3's definitions.

### 3.1 A relational rule for linear readouts (stated for the record; not recommended)

Plain version: the table judges a formula over several sums by the directions of the sums, one at a time. For a
weighted total of additive sums one can do better with what the signature already holds: evaluate the weighted total
on each *change* and take the signs that occur. The quantity "bytes that are not zero bytes" is the size minus the
count of zero bytes; the table calls it two-sided (an up sum minus an up sum), yet every change that adds a byte
either raises it or leaves it, so it is up.

**Rule (one more row of Table 1).** For a readout $\rho_j(\mathbf{s}) = \sum_{k \in K_j} w_k s_k$ over additive sums,
the direction is the set of signs of $\sum_k w_k\,(\nu_\tau(c')_k - \nu_\tau(c)_k)$ over the changes $c \to c'$ in
$\Delta$ (with 0 added).

**Soundness** [proved]. By Proposition 1(i) the readout changes by the total of these terms over the changes the
delta is made of, and a direction is closed under addition. Five lines in Appendix C, no new hypothesis.

**What it gives.** The weight vectors whose readout is *up* form the dual cone of the change vectors,
$G_\Delta^{*} = \{\mathbf{w} : \mathbf{w} \cdot \mathbf{g} \ge 0 \text{ for all } \mathbf{g} \in G_\Delta\}$. The
table certifies only the dual of the sign box, which is smaller. Modulo the identities that hold on the population,
the two coincide exactly when there is no sign slack (§2.2) [believed: bipolar theorem for finitely generated cones;
I did not write out the closure condition for an infinite set of change vectors]. In abstract-interpretation terms
this is the step from the sign domain to a relational one (Karr's linear equalities 1976, Cousot and Halbwachs's
polyhedra 1978) [memory], so the idea is theirs and the instance would be ours.

**Why not.** On EMBER I find no block where it recovers evidence that matters: the import block has no sign slack
(§2.2); the two-sided sums of the overwrites and of the entry write are free (§2.3), so nothing can recover them; the
invariants of a rename (totals over name buckets) are already sums, and leaving rename out of the threat model
recovers 0.1 points; what remains are inequalities such as "an added string brings at least five printable
characters", which I expect to carry no detection. It would add a table row, a notion ("change vector") and half a
column for at most a few tenths of a point. It also brings back coupling, which was dropped for complexity. The
honest place for it is one sentence in the discussion: the rule exists and is sound, and the instance did not need it.

### 3.2 Anchored sums: raise the fixed share of the extractor (recommended to test)

Plain version: the detector is free on sums that no edit can move, and 80% of what it learns comes from them. EMBER
has few such sums because most of its totals run over *all* items of a kind, and the attacker can add items of almost
every kind. A total over the items the attacker cannot add, remove or rewrite is fixed, and the detector may then
read it without any constraint: low values, high values, proportions, anything. The sums re-encoding of Appendix D
already works this way for two-sidedness (it recovered 2.4 points); this is the same move for one-sidedness.

**In §3's terms nothing is new.** Split a kind $\tau$ into two kinds: $\tau_1$, the items the extractor locates
through content the threat model cannot write (*anchored*), and $\tau_2$, the rest. Give each its own sums. If the
signature has no change on $\tau_1$ ($\Delta_{\tau_1} = \emptyset$), Definition 9 makes every sum fed only by
$\tau_1$ fixed, and Theorem 1 and Corollary 1 apply as they stand.

**Proposition G (refining kinds never shrinks the class).** [proved under the stated correspondence] Let
$\varphi'$ split kind $\tau$ of $\varphi$ into $\tau_1, \tau_2$ and each sum $k$ fed by $\tau$ into $k_1, k_2$ with
$s_k = s_{k_1} \star_k s_{k_2}$, and let the signature of $\varphi$ contain every change of the signature of
$\varphi'$ on $\tau_1$ and $\tau_2$ (and a removal and an addition for any item an edit moves between them). Then
$d_k \supseteq d_{k_1} \cup d_{k_2}$, and every score that is monotone with respect to the table of $\varphi$ is
monotone with respect to the table of $\varphi'$ when it reads $s_k$ as $s_{k_1} \star_k s_{k_2}$.

*Proof.* A change that raises $k_1$ or $k_2$ raises the item's contribution to $k$, so it is counted in $d_k$;
likewise for lowering. If $s_{k_1}$ and $s_{k_2}$ change with signs in $d_{k_1}$ and $d_{k_2}$, their combination
changes with a sign in the union (a total of two changes; the larger or smaller of two values that each moved
within a direction). $\square$

Soundness never depends on the anchor being right. If some edit can move an item across the split, the covering
signature must contain that change, the table then marks both parts as moving, and the gain is lost, not the
guarantee. The anchor is checked the way closure is: on the corpus.

**What a practitioner gets.** A design rule that the table itself audits: *put evidence where the threat model cannot
write, and read it there separately.* For each kind, ask which items are located through fixed content; give them
their own sums; the derived table confirms which came out fixed. In the PE instance the natural anchors are the
section that holds the entry point and the regions that loader-used directories point to (resources, relocations,
TLS), since the threat model rewrites none of them; the anchored sums would be that section's byte counts,
byte-entropy counts, string counts, sizes and entropy. This stays in §4 and Appendix D, never in a definition.

**Cost.** §3: nothing, or two sentences after Corollary 1 saying that a detector is unconstrained on fixed features
and that an extractor can be written to have more of them. §4.2 and Appendix D: one more re-encoding, about 100
words. §5.4: one row in Table 5 and a sentence. Work: declare the new kinds, derive the table again, re-featurize
(a long job, the user's decision), and re-run the population and closure checks, where new anchors located through
header fields are exactly the place earlier escapes were found.

**The strongest argument against.** It is extractor design, not theory, and its instance is PE-specific; it re-opens
the feature set, and with it the corpus checks and the risk of new population holes; its gain is my prediction, not a
measurement; and it moves §5.4 a step toward "we built a better defense". My answer: experiment 4 bounds the gain
from above in one minute of training before any of that work is done, and the finding it supports is about cost
("the price depends on how much evidence the extractor reads where the attacker cannot write"), which is what §5.4
currently cannot say.

### 3.3 The signature (an extractor decision, PLAN.md step 2c)

By §2.3 the entry write's 3.9 points cannot be recovered by any detector on the present features. They can be
recovered by the extractor: a sum that counts a signature only if its hash matches the file *and* its chain reaches a
trusted root can be lowered by the threat model (break it) and not raised (no key), so it is a down sum, and the
detector before the entry write (89.6% at 1% FPR, 74.8% at 0.1%) is a measurement of roughly that detector, to the
extent that the signatures in the corpus verify. Hash match alone is not enough, since anyone can sign a file with
their own certificate. This is PE-specific and belongs to §4 and the discussion; in §5.4 it would explain a number:
*the largest single price is the price of parsing a signature without verifying it*, which matches Kim et al.'s
observation about anti-virus products that the paper already cites.

## 4. Experiments for afterwards

All on the pilot stores (`ember2024-sums-10-v2`, the loose table, seed 0), each one or a few GBDT trainings of about
one minute. Reference points: unconstrained 93.5 / 84.4 (TPR at 1% / 0.1% FPR), monotone on the sums 85.7 / 68.1,
before the entry write 89.6 / 74.7.

1. **Free evidence under the loose table.** The unconstrained detector with the 1,474 two-sided sums neutralized
   (the drop-only detector of the price list, on the loose table). *Claim tested:* Proposition E's part of the cost
   is small. *Prediction:* 92.3 to 93.2 at 1% FPR (0.3 to 1.2 points lost), 76 to 79 at 0.1%.
2. **The learner.** The same monotone detector with (a) `monotone_constraints_method` `intermediate` and `advanced`,
   (b) iterations until the validation metric stops improving (cap 3,000) instead of the 500 cap that every model
   now hits, (c) a small grid over `num_leaves` and `min_data_in_leaf`. Record the TPR on the *training* files too
   (now 91.8 against 100.0 unconstrained). Check monotonicity afterwards as now (the adaptive search's largest score
   drop is exactly zero), since the guarantee rests on the library's enforcement. *Claim tested:* part of the cost is
   the learner. *Prediction:* +1 to +3 points at 1% FPR; I put 60% on at least +1 and 25% on at least +3. A second
   learner (a monotone network) would be the follow-up only if this moves the number.
3. **The fixed sums alone.** An unconstrained GBDT on the 203 fixed sums, everything else neutralized. It is
   unevadable with no constraint at all. *Claim tested:* the monotone detector is mostly a free detector on what the
   attacker cannot write. *Prediction:* 76 to 85 at 1% FPR, so the 1,978 one-sided sums add under 10 points.
4. **Go/no-go for anchoring (an upper bound, not a detector).** The monotone detector with the constraints on the
   683 `body_*` sums lifted, as if all body content were anchored. *Claim tested:* one-sidedness of the body sums
   costs enough to be worth an anchored re-encoding. *Prediction:* +1.5 to +3 points at 1% FPR. Below +1: drop §3.2.
5. **Verified signatures.** On the pilot test files with a certificate table, the share whose signature verifies
   (hash and chain), for benign and for malware. *Claim tested:* the detector before the entry write measures what a
   verifying extractor would give. *Prediction:* over 90% of signed benign files verify, and clearly fewer of the
   signed malware, so the verified sum is at least as good benign evidence as the parsed one and the 3.9 points
   are recoverable by the extractor. This one reads files and touches the extractor, so it is the user's decision.

A caution for all five: the pilot trains on a 10% subsample. The unconstrained detector gains 2.6 points at 0.1% FPR
from the full training set; the monotone detector's gain may differ, so the *cost* can move at the scale-up in
either direction.

## 5. Proof notes

Short, a by-product. Known already: the ratio rule of Table 1 needs $b \ge 0$.

1. **The sign of a change is defined by subtraction, and pools take infinite values.** On an input with no item
   that touches a max pool, the pool is $-\infty$; the identity readout is then not a real number (Definition 4 has
   $\rho_j: \mathcal{S} \to \mathbb{R}$) and "the change $x'_j - \varphi_j(z)$" of Theorem 1 is undefined when the
   pool stays empty. Smallest fix, in Definition 7: *old* "the change of every feature $j$ has a sign in $D_j$";
   *new* the same, preceded by "The sign of a change from $x$ to $x'$ is $+$ if $x' > x$, $-$ if $x' < x$, and $0$
   if they are equal."
2. **Default values on an empty pool.** An extractor that returns a default on an empty pool applies a readout
   $g$ to it. $g$ is nondecreasing only if the default is at most every contribution (max pool) or at least every
   contribution (min pool). A minimum that defaults to 0 is not: adding the first item raises the feature while the
   min pool's direction under additions is down. Smallest fix, in Appendix C's readout paragraph, one sentence: "A
   readout that returns a default for an empty pool is nondecreasing only if the default lies below every
   contribution of a max pool, or above every contribution of a min pool; otherwise the feature takes the last
   rule." Our instance is unaffected: thrember's three section minima include a literal 0 and are constant on all
   54,266 pilot test files [measured], which is why the table has them fixed.
3. **Corollary 1 is slightly more than Gimenez et al.'s Proposition 1.** Their statement asks the classifier to be
   increasing in every feature; ours leaves it unconstrained on fixed features, which is where our detector takes
   most of its gain. The proof is right; the sentence "This is Gimenez et al.'s Proposition 1" undersells and
   slightly misstates it. *Old:* "This is Gimenez et al.'s Proposition~1, with the preorder ``$z'$ is reachable from
   $z$'' and a feature map made monotone by $D$." *New:* "This is the argument of Gimenez et al.'s Proposition~1,
   with the preorder ``$z'$ is reachable from $z$'' and, in place of the order $\le$ on the features, the order that
   $D$ defines, under which two vectors that differ in a fixed feature are not comparable."
4. **What the body says a monotone detector is.** §3.3: "A gradient-boosted tree trained with monotone constraints,
   increasing in the up features and decreasing in the down features, and reading no feature marked both, is such a
   score." True; a reader will not infer that it is *unconstrained in the fixed features*, and §5.4's reading of the
   cost depends on it. Suggested addition: ", with no constraint on the fixed features".
5. **The guarantee of the trained detector rests on LightGBM's enforcement of the constraints**, which the paper does
   not state. The measured zero drops support it. If experiment 2 changes the method, a structural check of the
   saved trees (every pair of leaves whose boxes are comparable in the table order has ordered values, per tree)
   would make the claim independent of the library; it is a short function over `model.txt`.

I found no error in the proofs of Proposition 1 and Theorem 1. The step "replacing the old values by the new ones,
one at a time" is where total order and commutativity are used, and it is stated.

## 6. What I would do next

Run experiments 1 to 4 in one sitting (minutes). If experiment 2 gains a point or more, adopt the better learner
for the scale-up and report the training-set fit next to the cost. If experiment 4 clears +1, decide on the anchored
re-encoding together with the signature question, as one deliberate revision of the extractor (PLAN.md step 2c),
because both need a re-featurization and the same corpus checks. Whatever the numbers, rewrite §5.4's *Where the cost
lies* around the table of §2.5: which evidence a table-respecting detector may use, that no unevadable detector on
these sums may use the free ones (Proposition E) or lower its score on a complete block (Proposition B), and how the
measured cost divides among them. I would not add the relational rule, and I would not look for a data-only bound
again: §2.4 closes that.

## Appendix: what was run in this session

Prediction only, no training. Scripts were scratch files and are not kept; each is a few lines over
`artifacts/features/ember2024-sums-10-v2`, the saved models in `artifacts/models/gbdt/`, and
`artifacts/experiments/a_directions_derived_sums_loose/directions_sums.csv`.

- *Fit.* TPR at 1% / 0.1% FPR on the 207,872 training files and the 54,266 test files: drop-only (unconstrained)
  100.0 / 99.8 and 93.3 / 79.2; monotone before the entry write 95.2 / 84.6 and 89.6 / 74.7; monotone, loose table
  91.8 / 78.0 and 85.7 / 68.1. The test values reproduce §5.4's.
- *Conflicts.* The table of §2.4.
- *Gain shares.* Split gain of the loose monotone detector by direction: fixed 79.9%, up 20.1%. Its five most-used
  sums: `characteristics_DLL` (32%), `resource_size`, `basereloc_size`, `AddressOfEntryPoint`, `num_rx`. Split gain of
  the drop-only detector by direction and by the sign of each split's effect: fixed 40.9%, both 21.2% (the ten
  sums the entry write frees), up used increasingly 18.8%, up used decreasingly 19.1%.
- *Table.* Loose sums table, full threat model: 203 fixed, 1,978 up, 0 down, 1,474 both. Before the entry write the
  ten signature and directory sums were down.
- *Training settings read from the saved models:* `best_iteration` 500 of 500 for every model,
  `monotone_constraints_method: basic`.

## 7. Discussion with the user after the findings, and what was decided (session 71)

**My own assessment, when asked whether this direction fits, strengthens the framework, and is novel.**
*Fit:* yes; everything uses only the table, the signature and closure, and the two new words ("complete", "free") are
one-line conditions. *Strength:* modest; it does not strengthen Theorem 1 or Corollary 1, it lets §5.4 say what the
cost is a cost of. *Novelty:* low as mathematics. Proposition A and B are elementary order theory, Proposition F is
the conflict-graph bound of the robust-classification literature, and Proposition E is ours in the framework's terms
but short. What is original is empirical: the monotone detector is mostly an unconstrained detector on the 203 sums
the attacker cannot move, and the cost divides by what the attacker can place, raise, or not touch. None of it should
be listed as a contribution.

**The user's reaction.** (1) The result is acceptable but not ideal: they had hoped for a second headline result on
the order of Theorem 1, and "the bound belongs to the robust-classification literature" is exactly what they feared.
(2) They reject the anchoring proposal outright: a feature computed over the entry-point section is robust only until
the attacker finds a way to move the entry point, and they were surprised it was proposed at all. They also see
extractor revision as feature engineering, away from foundational observations about feature-space and problem-space
adversarial examples. I agree with the second point and withdrew the proposal.

**A consequence I pointed out, which stands.** The same condition already applies to the detector in the paper: it
takes 80% of its split gain from the 203 fixed sums, `AddressOfEntryPoint` among its five most-used, and its guarantee
holds only while those fields stay outside the threat model. §5.4 should say this plainly; experiment 3 (the fixed
sums alone) measures how much rests on it.

**What survives of §3.2 without any extractor work:** only the observation that the cost of robustness depends on
where the extractor reads its evidence relative to where the attacker can write. It is supported by experiment 3 and
needs no new feature. Likewise "the largest price is the price of parsing a signature without verifying it" explains
the entry write's 3.9 points without changing the extractor.

**Why this question cannot yield a headline result.** Bounding the cost from data is vacuous (§2.4), and the
mathematics around the split is elementary or someone else's.

**The one candidate for a headline result: the converse of Corollary 1 as a real theorem ("step 2").** Today:
table-monotone implies unevadable. The theorem would add: under a condition checked on the signature, every
unevadable detector on these sums is table-monotone. Theorem 1 says the table is sound; this would say it loses
nothing for detectors, and it would give the finding the user asked for at the start (the cost is the price of the
threat model for this extractor, not of our construction). What is missing:

- *The condition is not yet checkable.* Proposition B assumes "the table is complete", which restates the conclusion.
  My guess at a signature-level condition has two parts: every change in the signature is realizable by an edit on
  every population input where it applies (no signature slack), and every one-sided sum can be moved on its own up to
  identities that hold on the population (no sign slack).
- *Bundling.* It holds for the import block, but strictly fails where changes come together (an added import also
  brings bytes and strings). I believe a block-by-block version is provable; I am not confident a clean statement
  covers the whole EMBER table.
- *Novelty unchecked.* Gimenez et al. prove sufficiency only (checked in the PDF). **[Wrong; corrected in §9.2:
  their Proposition 2 is an existential converse.]** I have not searched for a converse
  elsewhere (monotone-classifier papers first: Incer et al. 2018, Chen et al. 2021). The order-theory core is simple,
  so the contribution would be the condition and its link to the signature.
- *Cost.* It brings back a relative of coupling and tightness, which were dropped for complexity.

My estimate, given to the user: about even odds that a bounded session yields something they would call a theorem on
the order of Theorem 1. Stop rule proposed: more than one new definition, or bundling that cannot be handled in a
remark, and it stays the two-sentence remark it is now.

**Decided (user).** Step 1 only for now: experiments 1 to 3 and the rewrite of §5.4's *Where the cost lies*. Then
discuss the outcomes; step 2 (with its literature check first) only if the user agrees then. State of step 1 and the
next actions: `docs/resume-prompt-fable.md`.

**Found while building step 1.** LightGBM falls back to the `basic` constraint method, with a warning only, unless
`feature_fraction` and `feature_fraction_bynode` are 1; the step sets both for the method comparison. At 100 rounds
on the pilot store the three methods are within 0.1 points of accuracy (93.71, 93.78, 93.75). Too early to judge,
but it does not yet support my prediction of +1 to +3 points for experiment 2.

## 8. Step 1, experiments 1 to 3 at pilot scale (session 72, 2026-11-16)

Step `pipeline/4-detectors/cost-split` (pilot command in its `run.sh`), on `ember2024-sums-10-v2`, the loose table,
seed 0. Output: `artifacts/experiments/cost_split/4-detectors/cost-split/table.json`. TPR at 1% and 0.1% FPR on the
test and the training split; "fixed" is the share of split gain on the 203 fixed sums; "violations" is the structural
check of the constraints on the saved trees.

| Model | test 1% | test 0.1% | train 1% | train 0.1% | trees | fixed | violations |
|---|---|---|---|---|---|---|---|
| unconstrained | 93.5 | 84.4 | 100.0 | 100.0 | 500 | 31.0% | |
| two-sided sums dropped (experiment 1) | 91.8 | 78.8 | 99.9 | 99.3 | 499 | 45.3% | |
| fixed sums only (experiment 3) | 79.7 | 57.7 | 88.4 | 70.7 | 500 | 100% | |
| monotone, as in Table 5 (500 rounds) | 85.7 | 68.1 | 91.8 | 78.0 | 500 | 79.9% | 0 |
| monotone, up to 3,000 rounds | 87.2 | 71.8 | 98.2 | 92.1 | 1,567 | 79.7% | 0 |
| monotone, method `basic`, all features per split | 87.1 | 72.3 | 99.1 | 94.9 | 2,018 | 81.3% | 0 |
| monotone, method `intermediate`, all features per split | 87.5 | 72.1 | 98.8 | 94.0 | 1,734 | 80.9% | 0 |
| monotone, method `advanced`, all features per split | 87.8 | 71.5 | 99.5 | 97.0 | 2,313 | 80.9% | 0 |

Against the predictions of §4 (one seed; retraining alone moves these numbers by a few tenths at 1% FPR and more at
0.1%):

1. **Experiment 1: missed at 1% FPR, held at 0.1%.** Predicted 92.3 to 93.2 and 76 to 79; measured 91.8 and 78.8.
   Dropping the 1,474 two-sided sums costs 1.7 points at 1% FPR, not the 0.3 to 1.2 predicted, and 5.6 at 0.1%.
   (Before the entry write the same detector lost 0.2; the ten sums the entry write frees account for the rest.) It
   remains an upper estimate of Proposition E's part, since it drops every two-sided sum, free or not.
2. **Experiment 2: held at the low end, and the gain is the rounds, not the constraint method.** Predicted +1 to +3;
   measured +1.5 at 1% FPR and +3.7 at 0.1% from training up to 3,000 rounds and keeping the round with the best
   validation AUC (1,567; the 500 cap was binding: `train_gbdt` has no early stopping, it trains every round and keeps
   the best). The unconstrained, drop-only and fixed-only detectors also peak at the 500 cap (best iteration 500, 499,
   500), so they too may gain from more rounds. `intermediate` against its control `basic` is +0.4 and -0.2, within
   retraining noise. The grid over `num_leaves` and `min_data_in_leaf` was not run. The monotone detector now fits
   its training files at 98 to 99% (1% FPR), so what remains is not underfitting. `advanced` (run in session 73, predicted no effect): +0.7 and -0.8 against `basic`, within
   retraining noise, as predicted.
3. **Experiment 3: held.** Predicted 76 to 85; measured 79.7. An unconstrained detector on the 203 fixed sums alone,
   unevadable with no constraint, detects 79.7% at 1% FPR; the 1,978 one-sided sums add 7.5 points to it (87.2).
4. **The constraints hold structurally:** zero violations in every monotone model.

**The split these numbers give** (1% FPR): 93.5 unconstrained; 1.7 points in the two-sided sums (no table-respecting
detector may read them, and by Proposition E no unevadable detector may read the free ones among them); 1.5 points
were the 500-round cap (learner); 4.3 to 4.6 points remain between the detector with the two-sided sums dropped
(91.8) and the best monotone detector (87.2 to 87.5): benign evidence in sums the attacker can only raise, plus
whatever a better learner would still find. At 0.1% FPR: 5.6, 3.7, and about 6.5. The scale-up should train the
monotone detectors without the 500-round cap; that changes Table 5's monotone rows (85.7 to about 87.2 here).

### 8.1 Correction: every detector under the same cap (session 72, later the same day)

In §8 I read the monotone detector's +1.5 points as "1.5 points of the cost were the 500-round cap". That compared a
monotone detector at up to 3,000 rounds with an unconstrained one at 500. Like for like
(`table-rounds.json` beside `table.json`; hypothesis before the run: the unconstrained detector gains under 0.5 at 1%
FPR, **missed**, it gains 0.6; "the gap shrinks by about a point" held, 0.9):

| Detector | 500 cap, 1% / 0.1% | 3,000 cap, 1% / 0.1% | best round | validation AUC at 500 / 1,000 / 2,000 / 3,000 |
|---|---|---|---|---|
| unconstrained | 93.5 / 84.4 | 94.1 / 85.1 | 2,836 | .99601 / .99625 / .99638 / .99642 |
| two-sided sums dropped | 91.8 / 78.8 | 92.9 / 75.0 | 2,810 | .99475 / .99508 / .99527 / .99533 |
| fixed sums only | 79.7 / 57.7 | 82.1 / 59.8 | 1,978 | .98313 / .98428 / .98481 / .98466 |
| monotone | 85.7 / 68.1 | 87.2 / 71.8 | 1,567 | .98880 / .98970 / .99004 / .98997 |

Every detector gains from more rounds, the constrained and the restricted ones more than the unconstrained one. The
cost of robustness is 7.8 / 16.3 points under the 500 cap and 6.9 / 13.3 under the 3,000 cap. The split of §8 under
one cap of 3,000 (1% FPR): 1.2 in the two-sided sums, 5.7 between the detector with them dropped and the monotone one;
the fixed sums alone 82.1, the one-sided sums adding 5.1. No reading of §8 changes in kind; each number moves by up to
about a point. One seed, a 10% training subsample; the 0.1% column moves by several points from retraining alone (the
dropped detector falls 3.8 there with more rounds).

**Scale caveat and decision (user, session 72).** Everything in §8 and §8.1 is measured on the pilot's 10% training
subsample (207,872 files). How many rounds a model can use depends on the amount of training data, so the round
comparisons say nothing about the full training set, where the user's experience is that rounds past 500 add very
little. I should have said this before measuring. Decision: every detector stays at 500 rounds; raising the cap is an
end-stage option, for all detectors together.

## 9. Step 2: the converse of Corollary 1 (session 73, 2026-11-16)

Nothing here is in the manuscript. No experiment was run; everything is reading and proof. Confidence marks as in the
header, plus **[search]**: found by web search and read only in the search result, not in a PDF.

### 9.1 The outcome in plain words

**There is no second theorem here. The stop rule applies, on both of its clauses, and for a reason stronger than
"it got complicated": the converse as we wanted it is false in general, and it already fails for the extractor of
Algorithm 1 under the simplest threat model.**

The hoped-for statement was: under a condition on the signature, every detector that no edit can evade is monotone
with respect to the table. What is true instead:

1. A detector is unevadable exactly when no single change of the signature lowers its score (given that every change
   can be carried out on its own). This is a clean "if and only if", but it is the one-sided twin of a published
   proposition (Wang et al. 2022) and elementary.
2. "Monotone with respect to the table" is strictly stronger than that whenever one item feeds two sums that move, by
   amounts that are not tied to each other. Then a detector may let one sum pull the score down as long as the other
   pushes it up at least as much; no edit evades it, and the table rejects it. In Algorithm 1, a record adds 1 to
   *records* and its length to *size*, and the score "size minus records" is such a detector.
3. Items that feed a count and a size at once are what real extractors are made of. A condition that excludes them
   leaves blocks like the import buckets (every contribution is exactly 1) and little else. So the condition would
   not be checkable in any light way, would not cover the EMBER table, and would need two new definitions.

What can be said truthfully, and briefly, is in §9.5: among detectors built the way every monotone defense is built
(one constraint per feature), no sound choice of constraints is more permissive than the derived table. That is a
remark of two sentences, its proof is two lines, and it is the "tightness" the mock already lists as dropped.

My estimate in session 71 was even odds. The answer is no.

### 9.2 Literature check

**A correction to §7 and to the resume prompt first.** Both say Gimenez et al. prove "sufficiency only (checked in
the PDF)". That is wrong. Their Proposition 2 is a converse of a kind [PDF, pp. 5-6]: "We also prove the converse is
true: any robust detector can be decomposed as a monotonic detector on a latent feature space", formally "There exist
$g$ and $h$ such that $f \circ \varphi = (f \circ h) \circ (g \circ \varphi)$ and $f \circ h$ is monotonically
increasing." The manuscript already has this right (§6: "Gimenez et al. proved the converse: every robust detector
can be written as ..."); only my notes were wrong. What their proposition does and does not say: the post-processing
$g$ is built from the classifier itself (it orders feature vectors by $f$'s score), so it shows that such a $g$
exists for each robust $f$, not that any given feature order is necessary. Our candidate was the fixed-representation
version: no post-processing, the extractor's own sums, the table's own order. A reviewer would still read it as
"a second converse after Gimenez et al.'s", which lowers what it could have been worth.

| Work | What it states | Relation |
|---|---|---|
| Gimenez et al. 2025 [PDF] | Prop. 1 sufficiency; Prop. 2 the existential converse above; Prop. 3 (ERDALT): a linear layer $L$ with $L(\delta) \ge 0$ on every perturbation vector, then a monotone network, is robust | Prop. 3's layer is a learned element of the dual cone of the perturbation vectors: the relational rule of §3.1, learned from attacks instead of derived |
| Wang et al., *Robust Learning against Relational Adversaries*, NeurIPS 2022 [PDF, now `papers/wang2022robust.pdf`; not in `main.bib`] | Attacker = reflexive-transitive closure of a relation $R$ (Def. 1); Prop. 1: "A classifier $f$ is robust at all $x$ iff $x \to_R z \Rightarrow f(x) = f(z)$" | The same attacker as our $\mathcal{M}$ with its sequences. Their Prop. 1 is the label-invariance form of Proposition A and of §9.3's local criterion; ours is one-sided (the score may rise). They evaluate on malware. Worth a citation in §6 whatever happens here |
| Incer et al. 2018 [PDF] | Monotone classifier on hand-picked monotone features; sufficiency, informally | No converse (no "necessary", "only if" in the text) |
| Chen et al. 2021 [PDF] | Monotonicity as one of five global robustness properties, enforced by verification | No converse |
| Giacobazzi, Ranzato, Scozzari, *Making abstract interpretations complete*, JACM 2000 [search] | Completeness of an abstract domain for an operation; the rule of signs is complete for multiplication and not for addition; an incomplete domain has a least complete refinement | "Sign slack" is the sign domain's incompleteness for adding up changes, and the relational rule of §3.1 is a refinement toward completeness. The vocabulary and the phenomenon are theirs |
| Functions monotone with respect to a cone order; a differentiable function is nondecreasing iff its gradient lies in the dual cone (Boyd and Vandenberghe, §3.6) [memory] | | The mathematics of "which detectors on these sums are unevadable" for additive sums |

I found no paper that states, for a fixed feature map, a checkable condition under which every robust detector is
monotone in a given per-feature order. Four searches are not proof of absence. Given §9.4, the question is moot.

### 9.3 What is true: the exact characterization

Plain version: if the attacker can carry out each change of the signature by itself, then what edits can do to the
items is exactly "apply changes of the signature, one after another". A detector is then unevadable exactly when no
single change lowers it.

Say that $\Delta$ is **realized** by $\mathcal{M}$ over $Z$ if for every $z \in Z$ and every change
$(\tau, c \to c') \in \Delta$ that applies to $z$ ($c = \bot$, or $(\tau, c) \in \pi(z)$) some finite sequence of
edits takes $z$ to a $z'$ whose delta is made of that change alone.

**Proposition H (local criterion).** [proved] Let $Z$ be closed, and let $\Delta$ cover $\mathcal{M}$ over $Z$ and be
realized by it. Then $h \circ \mathbf{s}$ is unevadable on $Z$ if and only if
$h(\sigma(B')) \ge h(\sigma(B))$ for every $z \in Z$, $B = \pi(z)$, and every $B'$ that one applicable change of
$\Delta$ makes from $B$.

*Proof.* "Only if": the change is carried out by edits (realized), so the score may not fall. "If": an edit on
$z \in Z$ has a delta made of changes $C$ in $\Delta$ (cover), all of whose old contents are in $\pi(z)$. Apply them
one at a time; by realization and closure each intermediate multiset is $\pi$ of a population input, the next change
applies to it, and the score does not fall at any step. Sequences of edits follow by closure. $\square$

It needs one new definition and is exact. It is also Proposition A with generators, the one-sided form of Wang et
al.'s Proposition 1, and it does not mention the table. It is not a result to headline.

### 9.4 Why the table's order is not necessary: sign slack is the normal case

Plain version: the table judges each sum alone. One item usually moves several sums at once, and the amounts are
linked (a record that is added brings at least one element). A detector may exploit the link; the table cannot see it.

**Counterexample (Algorithm 1).** [proved] Sums *records* (each record adds 1) and *size* (each record adds its
length, at least 1, since an item has a nonempty set of members). Threat model: add a record with any content; the
population is every input; the signature (additions of records) covers and is realized. The table marks both sums up.
Take $h = \textit{size} - \textit{records}$. An added record of length $L$ changes $h$ by $L - 1 \ge 0$, so $h$ is
unevadable. It is not monotone with respect to the table: $(\textit{records}, \textit{size}) = (1, 10)$ and
$(5, 11)$ are both population vectors, the second is larger in both sums, and $h$ falls from 9 to 6. In the terms of
§2.2: the two vectors are comparable in the table order and not in the reach order, because four more records bring
at least four more elements.

So the converse fails for the paper's own illustrative extractor with a signature that is as exact as a signature can
be. The cause is not signature slack and not bundling across kinds; it is a single item contributing to two moving
sums by amounts that are not tied by an identity.

**The general statement.** [proved for additive sums moved by additions; the rest believed] Let $G$ be the change
vectors of §2.2. With a realized signature of additions, $\mathbf{a} \preceq_R \mathbf{b}$ holds exactly when
$\mathbf{b} - \mathbf{a}$ is a finite total of vectors in $G$. The table's order asks only that
$\mathbf{b} - \mathbf{a}$ have the right signs. The two agree, and the converse of Corollary 1 holds, if and only if
every difference of two population vectors with the table's signs is a total of change vectors. For a linear score
$\mathbf{w} \cdot \mathbf{s}$: unevadable means $\mathbf{w} \cdot \mathbf{g} \ge 0$ for every change vector, the dual
cone of $G$; table-monotone means $w_k \ge 0$ on every up sum, which is a smaller set as soon as some $\mathbf{g}$
has two non-zero entries whose ratio is bounded. What the table loses is exactly the scores that trade one sum
against another: the relational rule of §3.1, which was weighed and declined in session 71, and what ERDALT's linear
layer learns from examples.

**Where the condition holds.** The import block (§2.2): every contribution is 1 and the three totals are tied by an
identity of the population, so differences with the right signs are totals of change vectors. Presence-style and
key-count blocks in general. **Where it does not** [believed, by the argument above, not checked on the instance]:
string count against printable characters (each string brings at least five), counts against byte totals, sizes that
move in steps of the file alignment, the byte-entropy windows against the byte histogram. Deciding it for the EMBER
table as a whole also runs into two things that cut the other way: files that share a sum vector link the order
(§2.1's transitive closure), and regions the attacker may overwrite let existing bytes be rearranged. Settling that
would be a per-block case analysis of PE regions, which is the opposite of a condition read off the signature.

**Against the stop rule.** (1) A statement of the converse needs "realized" and a second notion for the absence of
sign slack (differences of population vectors with the table's signs are totals of change vectors): two definitions.
(2) Bundling is not a remark: with it "realized" fails on EMBER for every added import, and the fix is a signature of
bundles, which is the coupling the mock lists as dropped. Both clauses are met. The result stays a remark.

### 9.5 What can be said in two sentences

Plain version: every monotone defense, ours included, is specified by one decision per feature (must rise, must
fall, free, unused). Among all such specifications that guarantee robustness, the derived table on the sums is the
most permissive one. Whoever builds a detector of this form cannot do better by choosing the constraints differently.

Call the directions of the sums **witnessed** if every sign in every $d_k$ is the sign of the change of $s_k$ under
some edit of $\mathcal{M}$ on some input of $Z$.

**Proposition I (least sound table).** [proved] If the directions of the sums are witnessed, every direction table
$D'$ on the sums that is sound for $\mathcal{M}$ over $Z$ satisfies $D'_k \supseteq d_k$ for every $k$. Consequently,
if a per-sum assignment of constraints is such that every score obeying it is unevadable on $Z$, every such score is
monotone with respect to $D_\Delta$.

*Proof.* If a sign is in $d_k$, some edit on a population input changes $s_k$ with that sign, and a sound $D'$ must
contain it. For the consequence: if the assignment let a score fall as $s_k$ rises while $+ \in d_k$, the score
$-s_k$ obeys it and the witnessing edit lowers it; likewise for $-$, and a sum the assignment leaves free is covered
by both cases. $\square$

Honest weight: this is the standard notion of a best abstraction in a given abstract domain [memory], its proof is
two lines, and it is the "region's tightness" that `docs/paper-mock.md` lists under *Dropped from the paper*. It
holds for the sums, not for features with ratio or "any other" readouts, whose rules are loose by design. It would
support one sentence in §5.4: the cost is not an artefact of how we chose the constraints. Whether the EMBER sums
table is witnessed is not known; the catalogue check's observed cells would say, from existing outputs. Hypothesis if
that count is wanted: nearly all non-fixed signs are witnessed, with exceptions among hashed buckets no enumerated
key reaches and among the overwrite positions shared with the parser. (This count depends on the number of files
scanned, not on the amount of training data.)

### 9.6 Recommendation

1. No Theorem 2, no new definition in §3. The cost of robustness cannot be stated as "the price of the threat model,
   not of our construction" without qualification, because a relational detector on the same sums could in principle
   keep evidence the table drops. What can be claimed is narrower and true: Proposition E (free sums are lost to
   every unevadable detector) and, if wanted, Proposition I (no per-feature constraints do better).
2. §5.4's *Where the cost lies* needs no change from this. If the two-sentence remark of §2.2 is ever added, it
   should say that the converse holds on blocks whose items contribute to one moving sum or to sums tied by an
   identity, and name what is lost elsewhere (scores that trade one sum against another).
3. §6 could cite Wang et al. 2022 beside Gimenez et al. for the attacker defined by closure under a relation (one
   bib entry). The user's call.
4. The user's wish for a second headline result is not met by this question. I do not see a variant of it that
   would be: the positive statements are elementary or prior work, and the strong statement is false.
