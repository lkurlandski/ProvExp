# What robustness must cost, and how to lower what it need not

Session 71 (2026-11-15), Claude Fable 5.2. Question: of the 7.8 points of detection that the monotone detector on the
sums gives up at 1% FPR (93.5% to 85.7%, pilot), how much must *every* unevadable detector give up (intrinsic), how
much is lost because the table keeps only a sign per feature (abstraction), and how much because our GBDT is not the
best table-respecting detector (learner)?

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
