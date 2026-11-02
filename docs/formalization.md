# Formalization of the feature provenance model (draft, started 2026-11-02)

Status: Sections 0-2 and Theorems 1, 4, 5 written, for review. Theorems 2, 3, 6, 7, the cost proposition, the full
checks table, and the positioning are outlined at the end and come next. This document holds definitions, theorems,
and proofs; it is the source for the paper's framework section and appendix. It builds on
`docs/feature-provenance-model.md` (the model, claims C1-C4 as sketches, assumptions A1-A4) and
`docs/item-layer-design.md` (the instrumented EMBER instance and its checks G1-G7). Theorem numbers follow the old
claim labels where one exists: Theorem 1 is C1 (exact side effects), Theorem 2 is C2 (coupling), Theorem 3 is C3 (the
reachable region), Theorem 4 is C4 (directions).

**Notation.** We follow Pierazzi et al. (S&P 2020) wherever we mean the same object: the problem space $Z$ and an
object $z$, the feature mapping $\varphi : Z \to X \subseteq \mathbb{R}^n$ and $x = \varphi(z)$, the classifier $g$
and its discriminant $h$, a feature-space perturbation $\delta$ and the feature-space constraints $\Omega$, a
problem-space transformation $T$ and the available transformations $\mathcal{T}$, the problem-space constraints
$\Gamma$ with $\Gamma \vdash \Omega$, and the side-effect feature vector $\eta$. Everything inside $\varphi$ (elements,
items, sums, readouts) is new notation, because Pierazzi et al. treat $\varphi$ as a black box.

## 0. In plain terms

A feature extractor for malware does three things. It finds the pieces of a file (sections, imports, strings, header
fields, single bytes, entropy windows). It adds up what each piece contributes (a count, a size, a hash bucket). It
then applies one formula per feature to those totals (divide by the file size, take an entropy, take a maximum). We
call these pieces *items*, the totals *sums*, and the formulas *readouts*. We call an extractor of this shape a
*sum-then-readout extractor*.

If an attacker's edit changes only a known list of items, then the new totals are the old totals, plus what the added
items contribute, minus what the removed ones contributed. The new features follow by re-applying the formulas. No
re-extraction is needed (Theorem 1). Two further facts carry over from item contributions to features. The signs of
the contributions decide which way each total can move. The shape of each formula decides how a total's direction
becomes a feature's direction. This gives, per feature, whether a threat model can raise it, lower it, both, or
neither (Theorem 4). A classifier that only rises in the features the threat model can only raise cannot be evaded by
that threat model (Theorem 5).

Everything that can go wrong is one of two things. Either "the edit changes only a known list of items" fails, or
"an item's contribution depends only on the item" fails. Section 2 lists these as five obligations an instance must
meet. On EMBER each one is checked against re-extraction; none of them is proved.

## 1. Definitions

### 1.1 Objects, elements, positions

**Definition 1 (objects).** Let $\mathcal{E}$ be a finite alphabet of *elements* (bytes, $\mathcal{E} = \{0, \dots,
255\}$; characters; tokens; packets). The problem space is $Z \subseteq \mathcal{E}^*$, the finite sequences of
elements. For $z \in Z$, $|z|$ is its length, $[|z|] = \{0, \dots, |z|-1\}$ its positions, and $z[p]$ the element at
position $p$. For $P \subseteq \mathbb{N}$, $z|_P$ is the sequence of $(p, z[p])$ for $p \in P \cap [|z|]$, in order.

Positions are taken from all of $\mathbb{N}$, not only $[|z|]$. A file can refer to positions past its own end (a
section whose raw data is cut off by truncation, a certificate table at an offset beyond the file). These references
must be representable, because appending can make them real (Section 2, A1).

**Definition 2 (feature mapping; Pierazzi et al., Def. 1).** A feature mapping is $\varphi : Z \to X \subseteq
\mathbb{R}^n$. Features are indexed by $j \in [n]$.

### 1.2 Items

**Definition 3 (items).** An *item* $\iota$ of $z$ has:
- a kind $\kappa(\iota)$ from a finite set $\mathcal{K}$ (EMBER: `byte`, `window`, `string`, `section`, `overlay`,
  `field`, `import`, `library`, `export`, `rich_pair`, `certificate_table`, `entry`);
- a set of members $M(\iota) \subseteq [|z|]$: the positions its content is read from (the bytes of a string; the
  bytes of a section's table entry and its raw data);
- a set of locating positions $L(\iota) \subseteq \mathbb{N}$: the positions that decide whether $\iota$ exists and
  where its members lie (`e_lfanew`, `NumberOfSections`, `PointerToRawData`, a data directory entry);
- its content $c(\iota) = z|_{M(\iota)}$.

The *parse* $\mathcal{I}(z)$ is the finite set of items of $z$. Items at different positions are different items,
even when their contents are equal. $\mathcal{I}_\kappa(z)$ is the subset of kind $\kappa$.

Beyond the locating sets of the items that exist, each kind has a *kind-level locating set* $L_\kappa(z) \subseteq
\mathbb{N}$. It holds the positions that decide where items of kind $\kappa$ may exist at all, including positions
where no item exists yet. Examples: `NumberOfSections` decides whether the bytes after the current section table form
another entry. The bounds of pefile's search range for the Rich header decide where a Rich header can be found, even
when none is there. The *locating set of the parse* is

$$L(z) = \bigcup_{\iota \in \mathcal{I}(z)} L(\iota) \;\cup\; \bigcup_{\kappa \in \mathcal{K}} L_\kappa(z).$$

Kinds come in two sorts. A *parsed* kind is found by following pointers from fixed places: sections, header fields,
imports, directories. A *scanned* kind is found by scanning content wherever it lies: bytes, entropy windows,
printable strings. For a scanned kind, the recognizer that finds its items is a function $\mathrm{rec}_\kappa$ from a
sequence and a range of positions to the items of that kind whose members meet the range.

*EMBER examples.* A section item's members are its 40-byte table entry and its raw data. Its locating set holds
`e_lfanew`, `SizeOfOptionalHeader`, `NumberOfSections`, and the bytes the section-table chain passes through. A string
item is a maximal run of at least five printable bytes. Its members are the run, and its locating set is empty: a
string is found by scanning, not through a pointer. A byte item is a single position, and its members are that
position.

### 1.3 Contributions and sums

**Definition 4 (sums).** A finite index set $S$ of *sums*. Each sum $s \in S$ has an aggregation monoid $(V_s,
\oplus_s, e_s)$, one of:
- additive: $(\mathbb{R}, +, 0)$: counts, histograms, hashed buckets (signed or not), keyed counts;
- a max pool: $(\mathbb{R} \cup \{-\infty\}, \max, -\infty)$; a min pool likewise with $\min$ and $+\infty$.

**Definition 5 (contributions).** Each item has a *contribution* $\mathbf{v}(\iota) \in \prod_s V_s$, with $e_s$ in
every sum it does not touch. The *sum vector* of $z$ is

$$\mathbf{s}(z)_s = \bigoplus_{s,\; \iota \in \mathcal{I}(z)} \mathbf{v}(\iota)_s .$$

Contributions are written as sums of *terms* from a fixed vocabulary. Each term has a known sign behavior, which is
what Theorem 4 reads. A term is a function of the item's content $c$. In the table, $a(c)$ is an attribute of the
content (a size, an entropy, a field's value), and $\mathbf{e}_s$ is the unit vector of sum $s$.

| Term | Contribution | Declared range | EMBER uses |
|---|---|---|---|
| $\mathrm{count}(s)$ | $\mathbf{e}_s$ | $+1$ | numbers of strings, sections, writable sections |
| $\mathrm{add}(s, a)$ | $a(c)\,\mathbf{e}_s$ | $a \ge 0$ | printable-byte totals |
| $\mathrm{bins}(F, x)$ | $\sum_b x_b(c)\,\mathbf{e}_{F_b}$ | $x_b \ge 0$ | byte histogram, byte-entropy rows, printable distribution |
| $\mathrm{hashed}(F, k, a, \pm)$ | $\xi(k)\,a(c)\,\mathbf{e}_{F_{h(k)}}$ | $a \ge 0$; $\xi(k) \in \{\pm 1\}$ if signed, else $\xi \equiv 1$ | section size, vsize, entropy, characteristics by name; Rich pairs; entry name (signed); imports (unsigned) |
| $\mathrm{keyed}(F, k)$ | $\mathbf{e}_{F_k}$ | $+1$ | per-library counts (distinct-count readout) |
| $\mathrm{slot}(s, a)$ | $a(c)\,\mathbf{e}_s$, with at most one item writing $s$; default $d_s$ when none does | any | header fields, data directories, DOS fields |
| $\mathrm{opaque}(s, a)$ | $a(c)\,\mathbf{e}_s$, computed by a parser we do not open | $[\ell_s, u_s]$, default $d_s$ | Authenticode features (signify) |
| $\mathrm{pool}(s, a)$ | $a(c)$ into the max (or min) pool $s$ | $a \ge 0$ | section entropy, raw size, vsize |

Here $k = k(c)$ is a key read from the content (a section's name, an import's name), $h$ is the hash function, and
$\xi$ its sign function (sklearn's `FeatureHasher`: murmurhash3).

### 1.4 Readouts

**Definition 6 (readouts).** Each modeled feature $j$ has a readout $\rho_j : \prod_s V_s \to \mathbb{R}$ that reads
a few sums. The types:

| Readout | $\rho_j(\mathbf{s})$ | EMBER features |
|---|---|---|
| identity | $s$ | counts, hashed buckets, fields, raw sums |
| presence (monotone) | $\min(1, s)$, or another nondecreasing function of one sum | `has_*` flags |
| ratio | $a/b$ for sums $a, b \ge 0$; default $d_j$ if $b = 0$ | average string length, overlay size ratio |
| normalized vector | $v_i / \sum_k v_k$ for a sum family $v$ | byte histogram, byte-entropy histogram, printable distribution |
| entropy | $H(v/\sum_k v_k) = -\sum_i p_i \log_2 p_i$ | file entropy, string entropy |
| max over items | a max pool $s$, possibly divided by a sum $b$ | max section entropy, max size ratio |
| min with zero | $\min(\{0\} \cup \text{pool})$, attributes $\ge 0$ | min section entropy, min size ratio |
| distinct count | $\#\{k \in F' : s_{F_k} > 0\}$ over a key family | number of libraries, library hash buckets |
| field transform | a bit test or category lookup of one slot | characteristics flags, machine, subsystem |
| selection | an attribute of the one item a declared rule selects | entry-section name hash |
| opaque with default | the opaque sum, $d_s$ when its item is absent | Authenticode |

A selection readout is modeled as an item of its own: the selected item, located through every position the rule
reads, with a slot contribution. A selection is therefore a slot whose locating set is large.

**Definition 7 (sum-then-readout extractor).** $\varphi$ is a *sum-then-readout extractor* over a set of modeled
features $J \subseteq [n]$ if there are a parse $\mathcal{I}$, contributions $\mathbf{v}$, and readouts $\rho$ such
that, for every $z \in Z$ and $j \in J$,

$$\varphi_j(z) = \rho_j\big(\mathbf{s}(z)\big), \qquad \mathbf{s}(z) = \bigoplus_{\iota \in \mathcal{I}(z)}
\mathbf{v}(\iota).$$

The features outside $J$ are the *residual*: features with no items, such as pefile's 88 warning flags. Every result
below treats the residual as "anything can happen".

**The item table** of $z$ is $\mathcal{I}(z)$ with each item's kind, members, locating set, content (or the
attributes its terms read), and contribution. It is what the instrumented extractor records.

### 1.5 Edits

**Definition 8 (transformations, written set, alignment; extends Pierazzi et al., Def. 6).** A transformation $T : Z
\to Z$ applied to $z$ gives $z' = T(z)$, together with an *alignment* $\pi : [|z|] \rightharpoonup [|z'|]$. The
alignment is a partial, strictly increasing injection saying where each surviving element of $z$ now lies. The
transformation is *position-preserving* if $\pi$ is the identity on its domain. Overwrites, appends, and truncations
are position-preserving. Insertions are not: extending the DOS stub and shifting section content insert bytes, and
every element after the insertion point moves. For a position-preserving edit, the *written set* is

$$W = \{p < \min(|z|, |z'|) : z'[p] \ne z[p]\} \;\cup\; [\min(|z|,|z'|), \max(|z|,|z'|)),$$

the overwritten positions plus the positions gained or lost at the end.

**Definition 9 (item delta).** An *item delta* from $z$ to $z'$ is a quadruple $\Delta = (I^-, I^+, I^\sim, I^\to)$:
removed items $I^- \subseteq \mathcal{I}(z)$, added items $I^+ \subseteq \mathcal{I}(z')$, modified pairs $I^\sim$
(an item of $z$ and the item of $z'$ it becomes: same kind, same locating role, new content), and moved pairs $I^\to$
(same kind and content, members mapped through $\pi$). $\Delta$ *describes* the edit if

$$\mathcal{I}(z') = \big(\mathcal{I}(z) \setminus (I^- \cup \mathrm{old}(I^\sim) \cup \mathrm{old}(I^\to))\big)
\;\cup\; I^+ \cup \mathrm{new}(I^\sim) \cup \mathrm{new}(I^\to),$$

and every item of $\mathcal{I}(z)$ outside the delta is also an item of $z'$, with the same members, locating set,
and content.

A modification could be written as a removal plus an addition. We keep it separate for two reasons. A slot sum can
only be modified, never added or removed, because exactly one item writes it. And the count terms of a modified item
cancel exactly, which Theorem 4's sign rules use.

**Definition 10 (edit classes).** A position-preserving edit with written set $W$ is
- *non-structural* if $W \cap L(z) = \emptyset$. It is a *content edit* if, in addition, its delta has $I^+ = I^- =
  \emptyset$, and an *item-creating edit* otherwise (scanned items appear, disappear, merge, or split);
- *structural* if $W \cap L(z) \ne \emptyset$.

A structural edit, or any edit that is not position-preserving, is *declared* if the transformation states its delta.
The declaration has two parts: the delta on the parsed kinds, and a *re-recognition range* $R \subseteq [|z'|]$ on
which the scanned kinds are found afresh (the bytes after an insertion point). Otherwise the edit is *undeclared*.

The class of an edit can be decided from the item table and $W$ alone, without parsing $z'$. Whether $W$ meets $L(z)$
is an interval query.

*EMBER examples.* Writing the slack bytes of a section is a content edit: the section's content changes, so its
entropy and the bytes' histogram counts change, and nothing locating is touched. Appending is item-creating: new byte
items and windows appear, and the overlay item is modified. On a file whose section table points past its end,
appending is structural, because $W$ meets a locating set that lies past $|z|$; this is exactly the case the engine
flags (Section 2, A1). Adding a section is declared structural: it writes `NumberOfSections` and declares the new
section item, the new header-field values, and the bytes it adds.

### 1.6 Threat models

**Definition 11 (operations, threat model).** An *operation* $o$ has a parameter domain $\Theta_o(z)$ (any 8-byte
name; any content of at most $B$ bytes; any value for these fields). For each $\theta \in \Theta_o(z)$ it gives a
transformation $T_{o,\theta}$, with its edit class and, if structural, its declared delta. A *threat model*
$\mathcal{M} = (O, \mathrm{Pre})$ is a finite catalogue of operations $O$ and a *precondition* $\mathrm{Pre}
\subseteq Z$: the files it applies to. The available transformations of Pierazzi et al. (Def. 8) are the finite
sequences $\mathcal{T}_\mathcal{M}$ of operation instances, and

$$\mathrm{Reach}_\mathcal{M}(z) = \{\, T(z) : T \in \mathcal{T}_\mathcal{M} \,\}.$$

$\mathrm{Pre}$ is *closed* under $\mathcal{M}$ if $T_{o,\theta}(z) \in \mathrm{Pre}$ for every $z \in \mathrm{Pre}$,
$o \in O$, and $\theta \in \Theta_o(z)$.

The threat model is an input, not something the model derives. Whether an operation preserves functionality, looks
plausible, or survives preprocessing (Pierazzi et al.'s $\Upsilon$, $\Pi$, $\Lambda$) is declared with the operation.
EMBER's twelve operations are loader-safe by construction (`docs/direction-A-threat-model.md`, Section 1). In Pierazzi
et al.'s terms, the model computes $\Omega$ from $\mathcal{T}$: it makes $\Gamma \vdash \Omega$ a computation
instead of a relation that has to be estimated.

## 2. Obligations

The theorems hold for any extractor that meets the obligations below for every item kind. Each obligation is a
property of the extractor (A0-A3) or of the threat model's tools (A4). None of them can be read off the definitions;
each has to be discharged on an instance. On EMBER, each is discharged by a check against re-extraction, so the
results are *validated* on EMBER, not proved for it.

**A0 (representability).** $\varphi$ is a sum-then-readout extractor over $J$ (Definition 7): the readouts over the
recorded sums reproduce $\varphi_j(z)$ for every $z$ and $j \in J$. *EMBER check:* G1 compares the readouts over the
item table with `feature_vector`. It is bit-exact on 100 pilot and 2,000 files, for all 2,480 modeled features and
both import variants (run 90), and for the four re-encoded groups (runs 102, 104).

**A1 (complete location).** For every position-preserving edit with $W \cap L(z) = \emptyset$, and every parsed kind
$\kappa$, there is a bijection between $\mathcal{I}_\kappa(z)$ and $\mathcal{I}_\kappa(z')$ that preserves members
and locating sets. In words: if no position that decides where things are has changed, every parsed item is still
there, in the same place. *EMBER check:* G5 flips single bytes across the header region and the data of every
directory, and tests whether the parse changes while the byte is not recorded as locating. The first round found 55
such (file, byte) pairs from three pefile rules. After the fix there were 0 failures on 58,666 flips (runs 91, 95).

**A2 (local contributions).** For every kind $\kappa$ there is a function $\mathbf{v}_\kappa$ with $\mathbf{v}(\iota)
= \mathbf{v}_\kappa(c(\iota))$. An item's contribution depends only on its kind and content, not on the rest of the
file. *EMBER:* the extractor as written fails A2 in three places, and each was repaired in the model, not in the
extractor:
- section size ratios divide by $|z|$: the item contributes `SizeOfRawData` and the readout divides by the
  byte-count sum;
- the set of import libraries: keyed counts with a distinct-count readout;
- a repeated DLL name in a second import descriptor overwrites the first one's functions: patched as a pure addition
  (`ImportsInfoMerged`), noted upstream.

A2 has no check of its own. A failure shows up as a mismatch in G1 (on the file) or G4, G6, and G7 (after an edit).

**A3 (local recognition).** For every scanned kind $\kappa$ there is a *margin* $\mu_\kappa(z, W) \supseteq W$,
computable from $z$ and $W$. For every non-structural position-preserving edit:
1. every $\iota \in \mathcal{I}_\kappa(z)$ with $M(\iota) \cap \mu_\kappa = \emptyset$ is an item of $z'$, with the
   same members and content (*frame*);
2. every $\iota' \in \mathcal{I}_\kappa(z')$ with $M(\iota') \cap \mu_\kappa = \emptyset$ is an item of $z$ (*no
   creation outside the margin*);
3. the items of $z'$ whose members meet $\mu_\kappa$ are $\mathrm{rec}_\kappa(z', \mu_\kappa)$ (*local recognizer*).

*EMBER margins:*
- strings: extend $W$ to the nearest non-printable byte on each side;
- byte-entropy windows: the windows that overlap $W$; under appending, also the last (window $-$ step) bytes before
  the old end, where the new windows that straddle the old end begin (a file under one window's length is one
  whole-file window, so its margin is the whole file);
- the Rich header: its whole search range;
- single bytes: $W$ itself.

*EMBER check:* G6 compares the engine's prediction with re-extraction after random in-place writes. The first round
had 1 failure in 1,561 writes; after the fix, 1,560 of 1,560 pilot and 1,463 of 1,463 fresh writes were bit-exact
(run 93).

**A4 (faithful declaration).** Applying a declared operation gives a file whose parse is described by the declared
delta (Definition 9). Every scanned kind is re-recognized on the declared range $R$, and is unchanged outside it.
This is a property of the tool that writes the edit, not of the extractor. *EMBER check:* G7 writes every operation
with our own byte-level edits, using adversarial parameters, and compares against re-extraction (runs 103, 104, 107).
G4 compares the declared add-section with the hand predictor and with re-extraction (run 92). LIEF-based tools fail
A4: they rebuild the file, which is why the experiments write edits themselves.

**What checks on natural files cannot catch.** A0 and A2 are checked on files as they occur. A locality failure that
only adversarial parameters trigger passes every such check. The duplicate-DLL quirk is the example: almost no
natural file has two import descriptors for one DLL, so the unpatched extractor passes G1 while being wrong for an
attacker who adds one. G7 is the guard against this: it includes repeated and case-variant DLL names, empty and
colliding section names, printable bytes next to existing strings, and forged Rich blocks. It is still a test, not a
proof. For a sound claim on EMBER, the honest wording is "derived from the instrumented extractor and validated
against re-extraction".

**Flagging.** An undeclared structural edit, a kind with no recognizer, or an item known to violate A2 is *flagged*.
The model makes no prediction for it, and Theorems 4-5 treat it as "both" on every feature it can reach (Section 3.2).
This keeps everything sound at the cost of tightness.

## 3. Theorems

### 3.1 Theorem 1: exact side effects (C1)

**Lemma 1 (the delta is determined).** Let $z \to z'$ be an edit that is non-structural (content or item-creating),
or declared structural, and let A1-A4 hold. Then a delta describing the edit can be computed from the item table of
$z$ and the bytes of $z'$ on $\mu = \bigcup_\kappa \mu_\kappa(z, W)$ (or on $R$, if declared). $z'$ is never parsed
as a whole.

*Proof.* *Non-structural case.* $W \cap L(z) = \emptyset$, so by A1 each parsed kind keeps its items, with the same
members and locating sets. A parsed item with $M(\iota) \cap W = \emptyset$ also keeps its content, since $z'$ agrees
with $z$ outside $W$. So it is unchanged and outside the delta. A parsed item with $M(\iota) \cap W \ne \emptyset$
keeps its members and gets the new content $z'|_{M(\iota)}$; it goes into $I^\sim$. For each scanned kind, A3.1 and
A3.2 say the items whose members avoid $\mu_\kappa$ are the same in $z$ and $z'$. We set $I^-_\kappa$ to the items of
$z$ whose members meet $\mu_\kappa$ (read from the item table), and $I^+_\kappa = \mathrm{rec}_\kappa(z',
\mu_\kappa)$ (A3.3). Then $\mathcal{I}_\kappa(z') = (\mathcal{I}_\kappa(z) \setminus I^-_\kappa) \cup I^+_\kappa$.
Pairs that are equal in $I^-_\kappa$ and $I^+_\kappa$ can be cancelled, and pairs that are matched by position can
be recorded as modifications. Neither changes what the delta describes.

*Declared case.* By A4, the declared delta describes the parsed kinds. The scanned kinds are handled as in the
non-structural case, with $R$ in place of $\mu_\kappa$. ∎

**Theorem 1 (exact side effects).** Under the hypotheses of Lemma 1, with delta $\Delta = (I^-, I^+, I^\sim, I^\to)$:
1. *Additive sums.* For every additive sum $s$,
   $$\mathbf{s}(z')_s = \mathbf{s}(z)_s + \sum_{\iota \in I^+} \mathbf{v}(\iota)_s - \sum_{\iota \in I^-}
   \mathbf{v}(\iota)_s + \sum_{(\iota, \iota') \in I^\sim} \big(\mathbf{v}(\iota')_s - \mathbf{v}(\iota)_s\big).$$
   Moved items contribute nothing to the change.
2. *Pools.* For a max pool $s$, $\mathbf{s}(z')_s$ is the maximum of the pool's values over $\mathcal{I}(z')$. It is
   computable from the item table of $z$ and $\Delta$. It is *not* computable from $\mathbf{s}(z)$ and $\Delta$ in
   general. The same holds for min pools.
3. *Features.* $\varphi_j(z') = \rho_j(\mathbf{s}(z'))$ for every $j \in J$. The side-effect vector of a
   transformation aimed at a perturbation $\delta^*$ is therefore exact:
   $$\eta = \varphi(z') - \varphi(z) - \delta^*.$$

*Proof.*
1. Addition is commutative and associative, so the sum over $\mathcal{I}(z')$ splits according to Definition 9. The
   items outside the delta are the same items with the same content, so by A2 they have the same contributions.
   Their part of the sum is the sum over $\mathcal{I}(z)$ minus the parts of the removed, modified, and moved items.
   A moved pair has equal content, so by A2 equal contributions, and its two parts cancel.
2. Computable: the pool's values over $\mathcal{I}(z')$ are the values over the unchanged items (in the item table)
   together with those of $I^+$, $\mathrm{new}(I^\sim)$, and $\mathrm{new}(I^\to)$. Not computable from the sum: take
   two files whose pools hold the values $\{5, 3\}$ and $\{5, 5\}$. Both have $\mathbf{s}_s = 5$. Removing an item of
   value 5 gives 3 for the first file and 5 for the second, so the result depends on more than $\mathbf{s}(z)$.
3. Both sides are $\rho_j$ applied to the same sum vector, by A0. ∎

*What it means.* Pierazzi et al. say side-effect features "cannot be feasibly computed in advance for each possible
object" and estimate them by injecting each gadget into a minimal app. For a sum-then-readout extractor and the edit
classes above, Theorem 1 computes them exactly from the item table of the one file at hand. The pool clause is why
the model keeps the item table and not only the sums: incremental maintenance of a max needs auxiliary state.

**Corollary 1 (composed edits).** A sequence of edits, each satisfying Lemma 1's hypotheses at the file it is applied
to, has exact side effects. Apply Theorem 1 once per step and carry the item table forward: Lemma 1 gives each step's
delta, so the table of every intermediate file is known.

*Checkable predictions and their checks.* Theorem 1 predicts that the engine's features equal re-extraction,
bit-exactly, for every edit it does not flag. Runs that test it:
- G4 (run 92): append bit-exact on the 89 files the engine does not flag, and the engine flags exactly the 11 files
  with structures past the end. DOS overwrite bit-exact on 100 of 100. Add-section equal to the hand predictor on 100
  of 100.
- G6 (run 93): random in-place writes.
- G7's C1 part (runs 103-104): in-place operations and appends, on 2,000 files, with adversarial parameters.
- Run 111: Corollary 1, for 1,105 combined edits (up to three added sections plus an append) on 85 pilot files.
  Every one landed at the predicted feature vector.

The pool clause's impossibility half needs no check.

### 3.2 Theorem 4: directions (C4)

Theorem 4 is presented before Theorems 2 and 3 because direction A rests on it.

**In plain terms.** For each feature, we want to know whether some edit in the threat model can raise it, and whether
some can lower it. This answer is needed for *every* file a detector may see, not only for files we have tried. The
answer has two parts:
1. Which signs each operation's changes to each sum can have. This comes from the contribution vocabulary, with no
   file involved.
2. How a readout turns the signs of its sums into a sign for the feature. This is a fixed rule per readout type.

For ratios and entropies, the rule alone often says "both", but a per-file test can be sharper.

**Definition 12 (sign sets and envelopes).** Write $\mathrm{sgn}(x) \in \{-, 0, +\}$ for the sign of $x$. For sign
sets $A, B \subseteq \{-, 0, +\}$, the *sign sum* $A \boxplus B$ is the set of signs of $x + y$ over all $x$ with
sign in $A$ and $y$ with sign in $B$. For example, $\{+\} \boxplus \{0\} = \{+\}$ and $\{+\} \boxplus \{-\} = \{-, 0,
+\}$. Let $F \subseteq Z$ be a set of files (the *population*). The *envelope* of operation $o$ on sum $s$ over $F$ is

$$\mathrm{env}^F_o(s) = \{\, \mathrm{sgn}(\mathbf{s}(T_{o,\theta}(z))_s - \mathbf{s}(z)_s) : z \in F,\ \theta \in
\Theta_o(z) \,\}.$$

For a max pool, read the difference as the change of the pool's value.

**Definition 13 (direction table, soundness).** A *direction table* assigns each feature $j$ a value $D_j \in
\{\mathsf{fixed}, \mathsf{up}, \mathsf{down}, \mathsf{both}\}$. It is *sound for $\mathcal{M}$ over $F$* if, for
every $z \in F$, every $o \in O$, and every $\theta \in \Theta_o(z)$, with $z' = T_{o,\theta}(z)$:
- $D_j = \mathsf{fixed}$ implies $\varphi_j(z') = \varphi_j(z)$;
- $D_j = \mathsf{up}$ implies $\varphi_j(z') \ge \varphi_j(z)$;
- $D_j = \mathsf{down}$ implies $\varphi_j(z') \le \varphi_j(z)$.

Incer et al.'s four cases are exactly these four values. Incer et al. assign them by hand, and Gimenez et al. by the
perturbation vectors of observed attacks.

**Lemma 2 (envelopes from the vocabulary).** Under A2, the sign of each term's change is bounded by the term's
declared range, with no file involved:

| Term | added | removed | modified |
|---|---|---|---|
| count, keyed | $\{+\}$ | $\{-\}$ | $\{0\}$ (cancels) |
| add, bins, unsigned hashed, pool | $\{0,+\}$ | $\{-,0\}$ | $\{-,0,+\}$; per bin, $\{0\}$ total when the content length is kept |
| signed hashed, key $k \in K$ | $\{\xi(k) : k \in K,\ h(k) = b\}$ in bucket $b$, each times $\{0,+\}$ | the negation | both buckets, both signs |
| slot (default $d$) | — | — | $\{\mathrm{sgn}(a' - a)\}$ over the domain: any, unless declared |
| opaque | $\mathrm{sgn}(a - d)$ over $[\ell, u]$ | $\mathrm{sgn}(d - a)$ over $[\ell, u]$ | $\{-, 0, +\}$ |

For an operation $o$ with a declared delta on parsed kinds, and an in-place content domain on scanned kinds, the
envelope of a sum $s$ is contained in the sign sum, over every change the operation makes, of that change's entry
above, restricted to the terms that write $s$. A flagged change contributes $\{-, 0, +\}$ to every sum its kind
writes.

*Proof.* By A2, a change's effect on $s$ is a sum of term differences, each with its sign in the table's entry by the
declared range. The sign of a sum of reals lies in the sign sum of the summands' signs. The modified count entry is
$\{0\}$ because $+1 - 1 = 0$ exactly. ∎

**Lemma 3 (hash image).** For a signed hashed term whose key the attacker picks from a domain $K$, the set of
(bucket, sign) pairs the operation can write is exactly $\{(h(k), \xi(k)) : k \in K\}$. A finite $K$ can be
enumerated. For a huge $K$, any enumerated subset $K_0 \subseteq K$ gives a lower bound, which is a set of witnesses.
Once the lower bound covers every pair, it is exact.

*Proof.* Immediate from the term's definition. *EMBER:* three-letter section names already hit all 100 pairs of the
50-bucket signed families, so adding a section is "both" on every signed bucket, and the "up" or "down" split part of
each bucket is reachable.

**Lemma 4 (readout rules; global).** For each readout type, write $E_s$ for the envelope of sum $s$ under one
operation. Each rule below is sound for every file in $F$: the change of $\varphi_j$ has a sign in the stated set.
- *Identity:* $E_s$.
- *Monotone nondecreasing* (presence): a subset of $E_s$ (weak inequalities).
- *Ratio $a/b$* with $a \ge 0$, $b > 0$ before and after: $E_a \boxplus ((-E_b) \cup \{0\})$, where $-E$ flips each
  sign. If $b$ can become zero or stop being zero, add $\{-,0,+\}$, unless the default is declared to lie on one side.
- *Normalized vector* $v_i / \sum_k v_k$: the ratio rule with $a = v_i$ and $b = \sum_k v_k$. When the total cannot
  change ($E_b = \{0\}$, as for an in-place write), this is $E_{v_i}$.
- *Entropy:* $\{0\}$ if every count's envelope is $\{0\}$, else $\{-, 0, +\}$.
- *Max pool:* $E_s$. Under additions only, $E_s \subseteq \{0, +\}$, so up.
- *Min with zero, attributes $\ge 0$:* $\{0\}$.
- *Distinct count:* $\{0,+\}$ if keys are only added, $\{-,0\}$ if only removed, else both.
- *Field transform, selection:* $\{0\}$ if the slot (for a selection: every locating and member position of the
  selection) is not written, else $\{-, 0, +\}$.
- *Opaque with default:* the opaque term's entry in Lemma 2.
- *Residual* (features outside the model): $\{-, 0, +\}$.

*Proof.* Only the ratio rule needs an argument; the others follow from monotonicity or are trivially sound. With $a'
= a + \alpha$ and $b' = b + \beta$,
$$\frac{a'}{b'} - \frac{a}{b} = \frac{\alpha b - a \beta}{b\,b'} .$$
The denominator is positive. $\mathrm{sgn}(\alpha b) = \mathrm{sgn}(\alpha) \in E_a$. The sign of $-a\beta$ is $0$
when $a = 0$, and $-\mathrm{sgn}(\beta) \in -E_b$ otherwise. The sign of the sum lies in the sign sum. ∎

The $\cup \{0\}$ matters only for the exact sign set (with $a = 0$ a growing denominator leaves the ratio at 0), not
for the table: "down" is a weak inequality. The rule gives "up" when the numerator can only rise and the denominator
can only fall. The item-layer design's table listed only the cases "only $a$ moves" and "only $b$ moves"; this rule
covers those and the mixed ones.

**Lemma 5 (per-file tests).** Fix a file $z$ and an operation $o$. Let $C$ be the set of sum changes $\Delta\mathbf{s}
= \mathbf{s}(T_{o,\theta}(z)) - \mathbf{s}(z)$ over $\theta \in \Theta_o(z)$.
1. *Ratio test.* $a/b$ rises under some $\theta$ iff $\max_{\Delta\mathbf{s} \in C} (\Delta a \cdot b - a \cdot
   \Delta b) > 0$, and falls iff the minimum is $< 0$. This is the sign of a linear function of the change, with
   coefficients $(b, -a)$ read from $z$. When the changes are additions of items with $(\alpha_\iota, \beta_\iota)$,
   $\beta_\iota > 0$, the ratio rises iff some item's own ratio $\alpha_\iota / \beta_\iota$ exceeds $a/b$ (the
   mediant property).
2. *Entropy, rising.* Let $p = v / \sum v$ and $p' = v' / \sum v'$. By concavity of $H$,
   $$H(p') \le H(p) + \langle \nabla H(p),\, p' - p \rangle .$$
   So if $\langle \nabla H(p), p' - p \rangle \le 0$ for every reachable $p'$, the entropy cannot rise. Since $\sum_i
   (p'_i - p_i) = 0$, the inner product is $-\sum_i (p'_i - p_i) \log p_i$. When the change appends content with
   distribution $q$, $p' - p = (1 - \lambda)(q - p)$ with $\lambda = N / (N + d)$, and the condition becomes
   $$\mathrm{CE}(q, p) = -\sum_i q_i \log p_i \;\le\; H(p).$$
   This is linear in $q$, so it is enough to check the vertices of the catalogue's content distributions. A $q$ with
   support outside $p$'s has $\mathrm{CE} = +\infty$, and the entropy rises.
3. *Entropy, falling.* $H$ is concave, so its minimum over $\mathrm{conv}\{p'\}$ is attained at an extreme point. If
   no extreme point has lower entropy than $H(p)$, the entropy cannot fall. If the extreme points are realized by
   edits (an append of one repeated byte value at the full budget), the test is exact.

*Proof.* (1) is the identity in Lemma 4's proof. For the mediant: a combination of added items has $(\alpha, \beta) =
\sum_\iota n_\iota (\alpha_\iota, \beta_\iota)$, and $\alpha b - a \beta = \sum_\iota n_\iota \beta_\iota (\alpha_\iota
/ \beta_\iota - a/b) \cdot b$, which is positive for some combination iff some term is positive. (2) is the
first-order condition for a concave function. The inner product's form uses $\partial H / \partial p_i = -(\log p_i
+ 1)$ and $\sum_i (p'_i - p_i) = 0$. The append form substitutes $p' - p$ and uses $\sum q_i = \sum p_i = 1$. (3) is
the minimum principle for concave functions over a polytope. ∎

*What the per-file tests add.* The global rule calls almost every normalized and entropy feature "both" under
appending. Per file, the answer is often one-sided: appending zero bytes lowers every normalized histogram bin except
bin 0. A monotone classifier needs the global table (Theorem 5). The per-file tests serve a per-file use, such as an
attack that needs a feature to move one way.

**Lemma 6 (string patterns under extension).** Let a feature count the strings matching a regular expression $P$, or
flag the presence of a match. If $P$ contains no right-context construct (the end anchors `$` and `\Z`, the word
boundaries `\b` and `\B`, lookahead), every match in a string $w$ is also a match in $w u$, for every extension $u$.
Extending a string can then only raise the indicator, never lower it. The same holds on the left for left-context
constructs (`^`, `\A`, the word boundaries, lookbehind).

*Proof.* Without context constructs, whether $P$ matches a substring $w[i..k)$ depends only on that substring, which
is unchanged in $wu$. ∎

The test is syntactic, decided from the parsed pattern (Python's `re` parser). It is sound and may be conservative.

**Theorem 4 (soundness of the derived direction table).** Let $\mathcal{M} = (O, \mathrm{Pre})$ be a threat model and
$F \subseteq \mathrm{Pre}$ a population. Let $D$ be the table that, for each feature $j \in J$, joins over $o \in O$
the readout rule (Lemma 4) applied to envelopes $\hat E_o(s) \supseteq \mathrm{env}^F_o(s)$, and assigns $\mathsf{both}$
to every residual feature. The join maps the union of the sign sets to fixed $= \{0\}$, up $\subseteq \{0,+\}$, down
$\subseteq \{-,0\}$, and both otherwise. Then:
1. $D$ is sound for single operations of $\mathcal{M}$ over $F$ (Definition 13).
2. If $F$ is closed under $\mathcal{M}$, $D$ is sound for every sequence. For every $z \in F$ and $z' \in
   \mathrm{Reach}_\mathcal{M}(z)$: $\varphi_j(z') = \varphi_j(z)$ for fixed features, $\ge$ for up, and $\le$ for
   down.
3. Without closure, part 2 can fail.

*Proof.* (1) For $z \in F$ and one operation instance, each sum's change has a sign in $\mathrm{env}^F_o(s) \subseteq
\hat E_o(s)$. By Lemma 4, the feature's change has a sign in the rule's output, which is contained in the joined set.
The join's value then gives the stated relation. (2) By induction on the length of the sequence. Each intermediate
file lies in $F$ by closure, so (1) applies at each step, and $=$, $\ge$, $\le$ are transitive. (3) Take $z \in F$
and a first step to $z_1 \notin F$. The envelope says nothing about the steps from $z_1$, so a second step may lower
an up feature. ∎

**The two obligations Theorem 4 makes visible.**

*(i) Envelopes over the population, not the corpus.* The theorem needs $\hat E_o(s) \supseteq \mathrm{env}^F_o(s)$
over the population the detector will face. For the declared structural operations, Lemma 2 gives envelopes that do
not depend on the file, so this holds for any $F$. For the in-place operations (slack, DOS header, loader-ignored
header fields, checksum), the EMBER catalogue derives each operation's changes per corpus file, from the bytes it
writes there, and takes the union over the corpus (`catalogue.file_region_changes`). That gives $\hat E_o \supseteq
\mathrm{env}^{\text{corpus}}_o$, which is sound for the corpus and for files whose layouts the corpus covers, but not
for every file. The risk is real: on the pilot, header overwrites never reached section entropy, while on the
2,000-file set they did, on 4 files whose `.bss` section has `PointerToRawData` 0 (run 102). Two ways to discharge
the obligation:
1. State the envelope per operation as the set of kinds whose members can lie in the operation's region on any file
   of $\mathrm{Pre}$. The precondition's plain-layout clause ("headers hold only headers") already excludes the `.bss`
   case, so this set may be small and arguable from the format.
2. State the theorem over the corpus's layouts and say so.

Cheap evidence for (1): the envelopes derived on 100 files and on 2,000 files should agree on $\mathrm{Pre}$ (see
check P2 below).

*(ii) Closure of the precondition.* Part 2 needs $\mathrm{Pre}$ to be closed under $\mathcal{M}$. This also matters
for Theorem 5's routing.

### 3.3 Theorem 5: robustness by composition

**In plain terms.** Gimenez et al. prove that a detector is robust if its features can only rise under the attacker's
edits and the classifier's score only rises in those features. Incer et al. build such detectors by hand. Theorem 4
supplies the first half from the extractor. A monotone classifier supplies the second. A detector that routes files
outside the precondition to an unconstrained fallback model keeps the guarantee only if no edit can push a file out
of the precondition.

**Definition 14 (constrained classifier).** Given a direction table $D$, a discriminant $h : X \to \mathbb{R}$ (the
malware score) is *$D$-monotone* if, for all $x, x'$ such that
- $x'_j = x_j$ for fixed features,
- $x'_j \ge x_j$ for up features,
- $x'_j \le x_j$ for down features,
- $x'_j = x_j$ for every feature $h$ reads among those with $D_j = \mathsf{both}$,

we have $h(x') \ge h(x)$. A GBDT trained with monotone constraint $+1$ on up features and $-1$ on down features, with
no constraint on fixed features, and with no split on "both" features, is $D$-monotone. The tree ensemble's score is
monotone in each constrained coordinate, and the remaining coordinates it reads do not change.

**Theorem 5 (robustness).** Let $D$ be sound for $\mathcal{M}$ over $F$, with $F$ closed under $\mathcal{M}$
(Theorem 4, part 2), and let $h$ be $D$-monotone. Then for every $z \in F$ and every $z' \in
\mathrm{Reach}_\mathcal{M}(z)$, $h(\varphi(z')) \ge h(\varphi(z))$. A file detected at any threshold stays detected
after any sequence of edits in $\mathcal{M}$.

*Proof.* By Theorem 4, part 2, the pair $x = \varphi(z)$ and $x' = \varphi(z')$ satisfies Definition 14's conditions
on fixed, up, and down features. Features with $D_j = \mathsf{both}$ are not read by $h$. By $D$-monotonicity, $h(x')
\ge h(x)$. This is Gimenez et al.'s Proposition 1, with the preorder "$z'$ is reachable from $z$ under $\mathcal{M}$"
and a feature map made monotone by $D$. Here $D$ is derived rather than estimated. ∎

**Corollary 2 (routing to a fallback).** Let the routed detector score $z$ with $h_D(\varphi(z))$ if $z \in
\mathrm{Pre}$, and with an unconstrained $h_0(\varphi(z))$ otherwise. Let $\tau_D$ and $\tau_0$ be the respective
thresholds.
1. If $\mathrm{Pre}$ is closed under $\mathcal{M}$, every $z \in \mathrm{Pre}$ that is detected stays detected.
2. If some $z \in \mathrm{Pre}$ and some operation instance give $z' \notin \mathrm{Pre}$, then $z'$ is scored by
   $h_0$. In general nothing prevents $h_0(\varphi(z')) < \tau_0$, so the guarantee is lost for $z$.

*Proof.* (1) Theorem 5 with $F = \mathrm{Pre}$: every reachable $z'$ lies in $\mathrm{Pre}$ and is scored by $h_D$.
(2) By construction: $h_0$ is unconstrained. ∎

*What it means.* The guarantee is a property of four things together: the derived table, the classifier's
constraints, the precondition's closure, and the obligations A0-A4 on the population. Only the first is new to us.
The route is Gimenez et al.'s and Incer et al.'s. What Theorem 4 adds is that the table is computed from the
extractor, soundly, for all 2,568 features, which is what makes the route usable at EMBER's scale.

*Checkable predictions and their checks.*
- No edit in $\mathcal{M}$ lowers a constrained detector's score on a file in $\mathrm{Pre}$. Table A1 (runs 99-100,
  105): the smallest score change is exactly 0.0 under the toolkit, held-out, and adaptive attacks, on the files that
  pass the precondition.
- Theorem 4, part 1: G7's direction check (runs 103-104, 107). Every feature that an edit moved was checked against
  the derived signs of its operation, in both the strict and the precondition variants. G3 (runs 97, 102) compared
  the derived table with the former hand rules. Every disagreement was an error of the hand rules, each witnessed by
  a real file and edit (runs 88, 98, 101).

**Proposed checks** (not run; for the user's decision). Each is short.
- **P1 (closure of the precondition).** Evaluate `passes_precondition` on every edited file G7 already writes, and
  count the edits that take a passing file to a failing one. Today the precondition is evaluated only on the original
  file (`catalogue_checks.py`, `a1_evaluate.py`). *Hypothesis:* closure holds for every operation. Appending only
  shrinks what lies past the end. The declared operations update `SizeOfImage`, keep headers holding only headers, and
  keep pefile's overlay starting at a section's raw end. If an operation breaks closure, Corollary 2 says the routed
  rows' guarantee does not cover it, and either the operation's declaration or the precondition must change. Cost: the
  same as run 103 at pilot scale (minutes); 2,000 files as a `run/117` script.
- **P2 (stability of the corpus envelopes).** Derive the in-place operations' envelopes on the 100 pilot files and on
  the 2,000 files, and compare on files in $\mathrm{Pre}$. *Hypothesis:* they are equal on $\mathrm{Pre}$; the one
  known difference, the `.bss` case, lies outside $\mathrm{Pre}$. Equality is evidence, not proof, for obligation
  (i). A difference inside $\mathrm{Pre}$ is a soundness gap, which the format-level argument must close. Cost:
  seconds to minutes (derivation only).

## 4. Still to write (next, after review)

- **Theorem 2 (coupling, C2).**
  - Co-movement, as a corollary of Theorem 1.
  - Inseparability: features $i$ and $j$ can be moved independently iff the cone of the operations' change vectors,
    projected onto the $(i, j)$ plane, contains each attainable axis direction.
  - Coupling through a shared denominator, through Theorem 3.
  - Severi et al.'s example: the number of sections and the number of writable sections.
- **Theorem 3 (the reachable region is sound, C3).**
  - The cone relaxation $\mathbf{s}(z) + \mathrm{cone}(\mathbf{v}(C))$.
  - Images under each readout: monotone readouts, max pools, the mediant bound for ratios, the exact histogram
    polytope $\{\lambda p + (1 - \lambda) q\}$, and the entropy interval.
  - Boundary effects between added chunks as extra generators with bounded multiplicity.
  - Check: run 111.
- **Theorem 6 (P is a projection).** The flat provenance matrix spreads each item's contribution over its members.
  For additive features, item weights are Shapley values. Check: G2 (run 90).
- **Theorem 7 (tightness).** When every declared direction is realized by some edit: identity and presence readouts
  with enumerated hash images (Lemma 3 gives witnesses), against ratios and entropies (per file). What flagging
  costs.
- **Proposition (cost).** An update costs work proportional to the delta and the margins, not to the file.
- **Section 5, checks table:** one row per theorem and lemma, giving the prediction, the check, the run, and the
  result.
- **Section 6, positioning:** Pierazzi et al.; incremental view maintenance; abstract interpretation (sign, interval,
  and polyhedral domains); taint tracking and Cheney et al.'s dependency provenance; Treant and Chen et al. (CCS 2021)
  as consumers of the output.
