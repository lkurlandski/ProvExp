# Feature provenance: a formal model

Draft started 2026-11-02. Revision 2, the same day, answers the user's first review: give the document a narrative
with reasons, define every symbol, and stop letting PE shape the general parts.

**What changed in revision 2.**
- The running example is now a generic *container* format, the shape ZIP (and so APK, JAR, DOCX), OLE, PDF, ELF, and
  PE share. A second example, a network-flow extractor, shows the model on an input with no pointers at all.
- Items are introduced as what the extractor's loops iterate over. Item *identity* is now defined, because
  "modified" and "moved" depend on it.
- Operations now carry an *item signature*: which kinds of items they can add, remove, or change. A threat model
  stated in items (add a permission, inject a packet) needs only three general properties. The two locality
  properties, which carry the format's structure, are needed only when an edit is stated in raw elements (write
  these bytes). Section 9 tabulates what each result needs.
- EMBER facts have moved out of the general sections into Section 10.

**Status.** Sections 1-8 are written for review, with full proofs of the side-effect, direction, and robustness
theorems. Section 9 assesses how general the model is. Section 10 holds the EMBER instance. Section 11 lists what
remains: coupling, the reachable region, the provenance matrix as a projection, tightness, cost, and positioning.

The document is the source for the paper's framework section and its appendix. It builds on
`docs/feature-provenance-model.md` (the model as first sketched: claims C1-C4 and assumptions A1-A4) and
`docs/item-layer-design.md` (the instrumented EMBER extractor and its checks G1-G7). Where a result here corresponds
to one of those claims, the old label is given once, in parentheses.

## Notation

We reuse Pierazzi et al.'s notation (S&P 2020) for everything they define. We add symbols only for the inside of the
feature extractor, which they treat as a black box.

| Symbol | Meaning | Where |
|---|---|---|
| $Z$, $z$ | the problem space (all inputs) and one input, e.g. a file | 1 (Pierazzi) |
| $\varphi$, $x = \varphi(z)$ | the feature extractor, and the feature vector it outputs | 1 (Pierazzi) |
| $n$; $j$ | the number of features; a feature's index | 1 |
| $h$ | the classifier's malware score (Pierazzi's discriminant function) | 1 (Pierazzi) |
| $T$; $\mathcal{T}$ | one transformation of an input; the transformations available to the attacker | 1 (Pierazzi) |
| $\Gamma$ | the problem-space constraints: $\mathcal{T}$, preserved semantics, plausibility, robustness to preprocessing | 1 (Pierazzi) |
| $\Omega$ | the feature-space constraints that $\Gamma$ implies; Pierazzi writes $\Gamma \vdash \Omega$ | 1 (Pierazzi) |
| $\delta^*$; $\eta$ | the feature change an attacker aims for; the side-effect vector, the rest of the change | 1, 6 (Pierazzi) |
| $\mathrm{Reach}(z)$ | the inputs the attacker can produce from $z$ | 1 |
| element; $\lvert z\rvert$; $z[p]$ | the smallest unit of an input (byte, character, packet); the length of $z$; the element at position $p$ | 3.1 |
| $\iota$; $\mathcal{I}(z)$ | an item (a piece the extractor's loops iterate over); all items of $z$ | 3.1 |
| $\kappa(\iota)$ | the item's kind (record, string, packet, ...) | 3.1 |
| $\mathrm{id}(\iota)$ | the item's identity: how the extractor reaches it | 3.1 |
| $M(\iota)$ | the item's members: the positions its content is read from | 3.1 |
| $c(\iota)$ | the item's content: the elements at its members, in order | 3.1 |
| $L(\iota)$; $L(z)$ | the item's locating positions (they decide whether and where it exists); all locating positions of $z$ | 3.1 |
| $S$; $s$ | the set of sums (the extractor's running totals); one sum | 3.2 |
| $\mathbf{v}(\iota)$ | the item's contribution: what it adds to each sum | 3.2 |
| $\mathbf{s}(z)$ | the sum vector: each sum's total over all items of $z$ | 3.2 |
| $\rho_j$ | the readout of feature $j$: the formula applied to the sums | 3.3 |
| $J$ | the modeled features: those that are a readout of sums; the rest are the residual | 3.4 |
| $W$ | an edit's written set: the positions it changes | 4.1 |
| $\Delta = (I^-, I^+, I^\sim, I^\to)$ | an item delta: the removed, added, modified, and moved items | 4.2 |
| $o$; $\theta$; $\Theta_o(z)$ | an operation; one parameter value; the values allowed on input $z$ | 4.3 |
| $\Sigma_o$ | the operation's item signature: which kinds it can add, remove, or modify, with what contributions | 4.3 |
| $\mathcal{M} = (O, \mathrm{Pre})$ | a threat model: a catalogue of operations, and the precondition (the inputs it applies to) | 4.3 |
| $\mu_\kappa(z, W)$ | the margin of a scanned kind: the positions around an edit where its items can change | 5.2 |
| $F$ | a population of inputs, e.g. the files a detector will see | 7.1 |
| $\mathrm{sgn}$; $\boxplus$ | the sign of a number ($-$, $0$, or $+$); the sign sum of two sign sets | 7.1 |
| $E^F_o(s)$ | the envelope: the signs operation $o$ can give the change of sum $s$, over $F$ | 7.1 |
| $D_j$ | the direction of feature $j$: fixed, up, down, or both | 7.1 |

## 1. The problem: from edits to feature changes

Pierazzi et al. separate the *problem space* $Z$, the real objects an attacker edits (executables, Android apps, PDF
documents, network traffic), from the *feature space*, the vectors $x = \varphi(z) \in \mathbb{R}^n$ that a
classifier with score $h$ sees. The attacker edits an object with transformations $T \in \mathcal{T}$, restricted by
problem-space constraints $\Gamma$: the edited object must still work, look plausible, and survive preprocessing. The
classifier only sees what the edits do to the features. Pierazzi et al. write $\Gamma \vdash \Omega$: the
problem-space constraints determine which feature-space changes are possible. Every line of work on realizable
attacks and robust detectors needs some view of the set

$$\mathrm{Reach}(z) = \{\, \varphi(T(z)) : T \in \mathcal{T} \,\},$$

the feature vectors an attacker can reach from one object, and each needs a different view of it. An attack needs
the *side effects* of one edit: Pierazzi et al.'s $\eta$, everything the edit changes besides the change $\delta^*$ it
was aiming for. A monotone detector needs the *direction* each feature can move in (Incer et al.'s four cases, Gimenez
et al.'s certified detectors). A backdoor or feature-space attack needs to know which features *always move together*
(Severi et al.). Verified training needs a *region* that contains every reachable vector (Chen et al.).

None of these views is computed today. Pierazzi et al. state that the side effects of an edit cannot feasibly be
computed in advance, because $\Gamma$ has no closed form, and they find them by applying each edit and re-extracting.
Others write the constraints $\Omega$ by hand, or learn them from the attacks they have observed. Hand analysis does not
scale to thousands of features, and learned constraints miss whatever the observed attacks did not do.

**The claim of this document.** For a broad class of extractors, these views can be *computed* from the extractor
itself. The class is the extractors that find pieces of the input, add up what each piece contributes, and apply a
formula per feature. Instrumenting such an extractor once, to record its pieces, its totals, and its formulas, turns
$\Gamma \vdash \Omega$ from a relation one estimates into a computation. The computation is exact for the side effects
of one edit, and sound for the directions of a whole threat model, and it needs no attack to be run.

The document proceeds as follows. Section 2 introduces two small examples that every later definition is tried on.
Section 3 describes the class of extractors, and Section 4 describes an attacker's edits in that class's terms.
Section 5 states what an extractor must satisfy for the description to be exact. Sections 6-8 prove what follows:
exact side effects, sound directions, and detectors no edit in the threat model can evade. Section 9 asks how general
the class is, and Section 10 gives the instance we have built, EMBER on Windows executables.

## 2. Two running examples

The definitions below are abstract, so each is tried on two small examples. They are chosen to be as different as
possible: one is a file format with pointers, the other a stream with none. Neither is a real format, so nothing in
the definitions depends on one.

### 2.1 A container format

Most file formats malware arrives in are *containers*: a directory of entries, each pointing to a body stored
elsewhere in the file. ZIP (and so Android APKs, Java JARs, and Office documents), OLE, PDF's cross-reference table,
ELF, and PE all have this shape. Our toy container is a byte sequence laid out as follows:
- byte 0 holds $k$, the number of entries;
- a directory of $k$ fixed-size entries follows, each giving a name, the offset where the entry's body starts, and
  the body's length;
- the bodies lie wherever the directory says;
- bytes that no entry points to are *free*: padding, or data appended at the end.

Its extractor computes eight feature groups:
- (f1) the number of entries;
- (f2) 16 hashed name buckets: each entry adds its body length, with a sign of $\pm 1$, to bucket
  $\mathrm{hash}(\text{name})$;
- (f3) the largest body length;
- (f4) the byte histogram, normalized to sum to 1;
- (f5) the entropy of the whole file;
- (f6) the number of printable strings (runs of at least 5 printable bytes);
- (f7) the average string length;
- (f8) a flag: does some string look like a URL?

An attacker might (e1) overwrite part of an entry's body, (e2) append bytes at the end of the file, or (e3) add an
entry: increase $k$, write a new directory entry, and append its body.

### 2.2 A flow extractor

A network trace is a sequence of packets in time order. Each packet has header fields (addresses, ports, protocol), a
size, and a timestamp. The extractor groups packets into *flows*, one per (source, destination, ports, protocol)
tuple, and computes per flow:
- (g1) the number of packets;
- (g2) the mean packet size;
- (g3) the largest packet size;
- (g4) the standard deviation of packet sizes;
- (g5) the mean time between consecutive packets.

An attacker controlling one endpoint might (e4) pad a packet, (e5) inject an extra packet, or (e6) delay a packet.

## 3. The shape of a feature extractor: items, sums, readouts

Most feature extractors in security, written as code, look like this:

```
totals = zeros(S)
for item in pieces(z):                 # records, strings, bytes, packets, API calls, ...
    totals += contribution(item)       # counts, sizes, hash buckets, maxima
x = [readout_j(totals) for j in features]   # identity, ratio, entropy, standard deviation, ...
```

The model gives each line a name. The pieces the loop iterates over are *items*. The running totals are *sums*. The
final formulas are *readouts*. The reason for separating them is that an attacker's edit is easy to describe in terms
of the first line (which pieces it adds, removes, or changes) and hard to describe in terms of the last (how it moves
2,000 features). The model translates from one to the other.

### 3.1 Items: what the extractor iterates over

An input $z$ is a sequence of *elements*: bytes in a file, characters in a script, packets in a trace. $|z|$ is its
length and $z[p]$ is the element at position $p$.

**Definition 1 (item).** An *item* $\iota$ of $z$ is one iteration of one of the extractor's loops: a piece of the
input the extractor recognizes and computes with. It has
- a *kind* $\kappa(\iota)$, saying which loop finds it: entry, string, byte, packet, ...;
- an *identity* $\mathrm{id}(\iota)$, saying how the extractor reaches it: "directory entry 3", "the string starting
  at position 812", "the flow with this tuple";
- *members* $M(\iota)$: the positions its content is read from;
- *content* $c(\iota)$: the elements at its members, in order;
- *locating positions* $L(\iota)$: the positions whose values decide whether the item exists, and where its members
  lie.

$\mathcal{I}(z)$ is the set of all items of $z$. Two items of different inputs are *the same item* if they have the
same kind and identity. This is how we tell, after an edit, whether an item was modified or replaced.

In the container, a directory entry is an item. Its identity is its index. Its members are its directory slot and its
body. Its locating positions are byte 0, which decides whether the slot is read at all, and the offset and length
fields of its slot, which decide where the body lies. A printable string is an item whose identity is its start
position and which has no locating positions: it is found by scanning, not by following a pointer. Each byte is an
item too, for the histogram and the entropy.

In the flow extractor, each packet is an item, and so is each pair of consecutive packets in a flow (for g5). A
packet's address, port, and protocol fields are locating positions: they decide which flow the packet belongs to. Its
size and timestamp are content.

**Members and location answer different questions.** Membership answers "if this element changes, whose content
changes?". Location answers "if this element changes, which items might appear, disappear, or move?". The two have
different consequences. A change to members modifies an item, and the model can compute the effect. A change to a
locating position changes the parse itself, and the model must either be told the result or decline to predict.

**Two sorts of kinds.** A *parsed* kind is found by following pointers or keys from fixed places: directory entries,
header fields, flows grouped by tuple. A *scanned* kind is found by examining content wherever it lies: bytes,
printable strings, n-grams, tokens, consecutive pairs. For each scanned kind the extractor contains a *recognizer*: a
routine that, given the input and a range of positions, returns the items of that kind overlapping the range.

**Locating positions of items that do not exist.** Some positions decide where items *could* be. In the container,
byte 0 decides whether the bytes after the last directory slot form another entry, so writing those bytes does
nothing unless byte 0 changes too. Each kind therefore also has *kind-level* locating positions. $L(z)$ denotes all
locating positions of $z$: those of its items and those of its kinds. A locating position may lie past the end of the
input, because extending the input can bring a pointed-to item into existence.

### 3.2 Sums: what each item contributes

**Definition 2 (sums and contributions).** The extractor keeps a finite set $S$ of running totals, called *sums*. Each
item $\iota$ has a *contribution* $\mathbf{v}(\iota)$: the amount it adds to each sum, zero for the sums it does not
touch. The *sum vector* $\mathbf{s}(z)$ holds each sum's total over all items of $z$. Most sums add their items'
contributions. A few, called *pools*, keep their maximum (or minimum) instead.

In the container, the entry count (f1) is a sum to which every entry contributes 1. Each name bucket (f2) is a sum to
which an entry contributes $\pm$ its body length if its name hashes there. Each histogram bin (f4) is a sum to which
every byte contributes 1 in its own bin. The largest body length (f3) is a pool. In the flow extractor, each flow keeps
four sums over its packets: the count, the total size, the total of squared sizes, and the total gap between
consecutive packets. The largest packet (g3) is a pool.

Contributions are written in a small vocabulary of *terms*. The vocabulary is there because each term has a known sign
behavior, which Section 7 uses: from the term alone one can tell which way a sum can move when an item is added,
removed, or changed. The terms are:

| Term | What the item adds | Sign | Container / flow | Elsewhere |
|---|---|---|---|---|
| count | 1 to one sum | $+$ | f1, f6 / g1 | permissions, API calls |
| add | a nonnegative attribute (a length, a size) | $\ge 0$ | total string length (f7) / total size (g2) | bytes in a section |
| bins | nonnegative counts to a family of sums | $\ge 0$ per bin | f4 / — | n-gram and packet-size histograms |
| hashed | an attribute (or 1) to bucket $\mathrm{hash}(\text{key})$, times $\pm 1$ if the hash is signed | the hash's sign, if signed | f2 / — | hashed n-grams, hashed API names |
| keyed | 1 to the count of its key (read out as "how many distinct keys") | $+$ | — | distinct permissions, distinct libraries |
| slot | the value of a field that exactly one item holds | any | — | header fields, a flow's protocol |
| opaque | a value computed by code the model does not open, within a declared range | within the range | — | a certificate parser's verdict |
| pool | an attribute into a maximum (or minimum) | $\ge 0$ | f3 / g3 | longest string |

### 3.3 Readouts: the formula per feature

**Definition 3 (readout).** Each modeled feature $j$ has a *readout* $\rho_j$: a formula applied to a few sums. The
model records each readout's *type*, not only its value, because the type decides how the sums' directions become the
feature's direction (Section 7).

| Readout | Formula | Container / flow | Elsewhere |
|---|---|---|---|
| identity | the sum itself | f1, f2, f6 / g1 | counts, header fields |
| presence | $\min(1, s)$, or any nondecreasing function of one sum | f8 / — | "requests permission X" |
| ratio | one sum divided by another | f7 / g2, g5 | mean section size |
| normalized vector | each bin divided by the bins' total | f4 / — | n-gram frequencies |
| entropy | the entropy of a normalized vector | f5 / — | payload entropy |
| max or min | a pool's value | f3 / g3 | largest section |
| distinct count | the number of keys with a positive count | — | number of distinct libraries |
| field transform | a bit test or table lookup of one slot | — | "is a DLL" flag |
| selection | an attribute of the one item a rule picks | — | the entry section's name |
| opaque with default | an opaque value, or a default when its item is absent | — | signature features |

The list is what EMBER, Drebin-style, and n-gram extractors use, and it is open. The flow extractor's standard
deviation (g4), $\sqrt{Q/N - (T/N)^2}$ over the count $N$, total $T$, and total of squares $Q$, is a readout type the
list does not contain. Adding a readout type means adding one rule to Section 7 and nothing else.

### 3.4 The class of extractors

**Definition 4 (sum-then-readout extractor).** An extractor $\varphi$ is a *sum-then-readout extractor* over a set of
*modeled features* $J$ if it has items, contributions, and readouts such that, for every input $z$ and every
$j \in J$,

$$\varphi_j(z) = \rho_j\big(\mathbf{s}(z)\big).$$

The features outside $J$ are the *residual*. The model makes no claim about them, and every result treats them as
"anything can happen".

The *item table* of $z$ lists every item with its kind, identity, members, locating positions, and contribution. It is
what the instrumented extractor records, in the same pass that computes the features.

The same three layers describe the other feature sets common in malware detection:
- *Android, Drebin-style.* The items are the permissions, API calls, intents, and URLs found in the manifest and the
  bytecode. Contributions are keyed counts, and readouts are presence.
- *PDF, Hidost-style.* The items are the paths in the document's object tree, read out as presence or counts.
- *Byte, opcode, and token n-grams.* The items are windows of $n$ elements, a scanned kind. Contributions are hashed
  counts, and readouts are normalized frequencies.
- *Network flows.* As in the second running example.

## 4. Edits, seen as changes to items

An attacker states an edit in one of two ways. Some edits are stated in elements: "write these bytes here", "append
that". Others are stated in items: "add a permission", "add a section named `.x`", "inject a packet". The extractor's
sums change because items change. If we know which items an edit adds, removes, or changes, the new sums follow by
arithmetic (Section 6). This section sets up the vocabulary for that translation.

### 4.1 Edits

**Definition 5 (edit, written set).** An edit takes $z$ to $z'$. It is *in place* if every element keeps its position;
overwrites, appends, and truncations are in place. Its *written set* $W$ is the set of positions where $z'$ differs
from $z$, together with any positions gained or lost at the end. An edit that inserts or deletes elements in the
middle *shifts* every element after that point.

### 4.2 Item deltas

**Definition 6 (item delta).** The *item delta* of an edit compares the items of $z$ and $z'$ by identity:
- $I^-$, the *removed* items: identities in $z$ but not in $z'$;
- $I^+$, the *added* items: identities in $z'$ but not in $z$;
- $I^\sim$, the *modified* items: identities in both, with different content;
- $I^\to$, the *moved* items: identities in both, with the same content at different members.

Every other item is unchanged: same identity, same content, same members.

Modification is kept apart from "remove, then add" for two reasons. Some sums can only be modified, because exactly
one item ever writes them: a header field's value. And when an item is modified, its count terms cancel exactly. This
is what makes, for example, renaming a container entry leave the entry count fixed.

A shift changes the identity of every scanned item after the insertion point, since scanned items are identified by
position. They appear in the delta as removed and re-added with equal content, and their contributions cancel.

### 4.3 Operations, signatures, and threat models

An attacker's toolkit offers a few *operations*, each with parameters. One operation describes a whole family of
edits, and questions about a threat model (which way can this feature move under *any* edit the attacker may make?)
are questions about operations, not single edits.

**Definition 7 (operation, threat model).** An *operation* $o$ is a family of transformations $T_{o,\theta}$, indexed by
a parameter $\theta$ from a domain $\Theta_o(z)$ that may depend on the input: "any name of at most 8 bytes", "any
content of at most $B$ bytes". A *threat model* $\mathcal{M} = (O, \mathrm{Pre})$ is a finite catalogue of operations
$O$, together with a *precondition* $\mathrm{Pre} \subseteq Z$: the inputs the catalogue applies to. The attacker's
transformations $\mathcal{T}$ are the finite sequences of operation instances, and $\mathrm{Reach}_\mathcal{M}(z)$ is
the set of inputs they produce from $z$. The precondition is *closed* under $\mathcal{M}$ if no operation takes an
input in $\mathrm{Pre}$ outside it.

**Definition 8 (item signature).** The *item signature* $\Sigma_o$ of an operation lists, for each item kind, whether
the operation can add, remove, or modify items of that kind, and the range of contributions the added or modified
items can have. For example, "add an entry" adds one entry (count 1, any name, body length up to $B$), adds byte and
string items inside the new body, and modifies no existing entry.

An operation stated in items comes with its signature: the tool that performs it says what it adds. An operation
stated in elements does not, and its signature must be derived from what it writes (Section 5.2).

The threat model is an input to the model, not an output. Whether an operation preserves the malware's behavior or
looks plausible is a property of the operation, as Pierazzi et al.'s constraints on semantics and plausibility are.
What the model computes is the operation's consequence in feature space.

### 4.4 How much the model can say about one edit

The written set and the locating positions together decide how much the model can say about a single edit.

**Definition 9 (edit classes).**
- A *content edit* writes no locating position and creates or destroys no item: it only changes the content of
  existing items. Example: (e1), overwriting part of a body with bytes that form no new string; (e4), padding a
  packet.
- An *item-creating edit* writes no locating position but creates or destroys scanned items: new bytes, new strings,
  two strings merged into one. Example: (e2), appending.
- A *declared structural edit* writes a locating position, or shifts elements, and states its resulting delta.
  Example: (e3), which writes byte 0 and states "one entry added, with this name, offset, and length"; (e5), which
  states "one packet added to this flow, between these two".
- An *undeclared structural edit* writes a locating position and does not state its delta. Example: changing byte 0
  alone, or repacking the whole file. The model *flags* such an edit, along with the item kinds it may affect, and
  does not predict it.

Whether an edit writes a locating position follows from the item table and $W$ alone, by an interval query, without
parsing $z'$. The classification is therefore automatic, and it catches structural edits a human would miss: on an
input whose directory points past its end, appending writes a locating position, because it decides whether the
pointed-to body now exists.

## 5. What the extractor must satisfy

The results in Sections 6-8 rest on one premise: an edit changes only items we can find cheaply, and each item's
contribution is its own. This premise is a property of the extractor, not something the definitions guarantee. A real
extractor must be shown to have it, kind by kind. We split the premise into five properties, so that each can be
checked separately and each failure has a name.

The five properties fall into two groups. Three are needed by every result, and they say nothing about how an input
is laid out. The other two are needed only when an edit is stated in elements rather than items. They are the
conditions under which a parse can be updated incrementally, and they are where a format's structure enters the model.

### 5.1 Properties every result needs

**A0 (representable).** $\varphi$ is a sum-then-readout extractor over the modeled features $J$ (Definition 4): the
readouts applied to the recorded sums reproduce the extractor's output exactly. This makes the recorded layers
trustworthy, and it is checked by comparing the two on every input.

**A2 (local contributions).** An item's contribution depends only on its kind and its content, not on the rest of the
input. Equivalently, the sums are a homomorphism over items: the totals over a union of item sets combine the totals
over each. A2 is what makes the arithmetic of Section 6 valid. It fails in three typical ways, each of which also
appears in Pierazzi et al.'s list of what makes side effects hard ("name deduplication, class declarations, resource
name normalization"):
- *A global total inside a contribution.* If the container's f3 were "largest body length divided by file size", an
  entry's contribution would depend on the file size. The repair is to let the entry contribute its length and move
  the division into the readout, where the file size is itself a sum. The flow extractor is already written this way:
  a packet contributes its size, and the mean is a readout.
- *Deduplication.* If the extractor kept a *set* of names, an entry's effect would depend on whether another entry has
  the same name. The repair is a keyed count with a distinct-count readout. Drebin's feature sets are exactly this.
- *Overwriting.* If a later entry with the same name replaced an earlier one's data, the earlier entry's contribution
  would depend on the later one. This has no repair inside the model. It is a genuine non-local effect, and it is
  flagged. (EMBER has one: Section 10.)

**A4 (faithful signatures).** Every edit an operation produces has an item delta within the operation's signature.
For an operation stated in items, this is a property of the tool that performs it: a tool that rebuilds the whole
input (as LIEF does for executables) can change items it was never asked to change. For an operation stated in
elements, Section 5.2 derives the signature, and A4 follows from A1 and A3.

### 5.2 Properties for edits stated in elements

When the attacker's edit is stated in elements, nobody tells the model which items changed. It must work them out from
the written set, and two properties make that possible. Both are standard: they are the "damage region" conditions of
incremental parsing and lexing (Wagner and Graham), which say that an edit disturbs the parse only near where it
writes.

**A1 (complete location).** If an in-place edit writes no locating position, then every parsed item is still there
afterwards, with the same identity, members, and locating positions, and no parsed item appears. Only content may
differ. In words: the recorded locating positions include *every* position the parser consults to decide what exists
and where. In the container, A1 holds if byte 0 and every slot's offset and length fields are recorded. In the flow
extractor, it holds if each packet's address, port, and protocol fields are. An extractor fails A1 when its parser
consults something the instrumentation did not record. Such failures are found by changing single elements and
checking whether the parse changes although the element is not recorded as locating.

**A3 (local recognition).** Each scanned kind $\kappa$ has a *margin* $\mu_\kappa(z, W)$: a set of positions around
the written set, computable from $z$ and $W$, such that after an edit that writes no locating position:
1. the items whose members lie outside the margin are unchanged;
2. no item appears outside the margin;
3. the items overlapping the margin can be found by running the kind's recognizer on the margin alone.

The margin of a printable string reaches to the nearest non-printable element on each side, since a run's extent
depends only on its neighbors. Windows of $n$ elements have a margin of $n - 1$ elements on each side, and single
elements have none. In the flow extractor, a pair of consecutive packets has a margin of one packet on each side:
injecting a packet replaces one pair with two.

**How much of A1 and A3 a domain needs.** Formats with pointers and tables, like containers, have many locating
positions and many structural edits, so A1 is where most of the instrumentation effort goes. Sequential inputs, like
traces and token streams, have few: most kinds are scanned, and margins are small. A threat model stated entirely in
items, as Drebin-style attacks are (add a permission, add an API call), needs neither property.

**Lemma 1 (signatures of element-level operations).** Let $o$ be an operation stated in elements, and suppose that on
every input in a population $F$ and for every parameter value, its edit is in place and writes no locating position.
Under A1 and A3, every edit of $o$ on $F$ modifies only parsed items whose members it writes, and adds or removes
only scanned items that overlap the margins of its written set. So $\Sigma_o$ contains these changes and no others.

*Proof.* By A1, no parsed item is added, removed, or moved, and a parsed item whose members avoid $W$ keeps its content,
since $z'$ equals $z$ outside $W$. By A3, parts 1 and 2, no scanned item changes outside the margins. ∎

The lemma's condition must hold for every input in $F$, not only those seen. Appending writes no locating position on
most inputs, but on an input whose directory points past its end it does. Such inputs must be excluded from $F$ by the
precondition, or the operation must be treated as structural on them.

### 5.3 Checking an instance, and keeping the results sound when a check fails

On a real extractor, A0-A4 are checked against re-extraction rather than proved: A0 on every input; A1 by changing
single elements; A3 by random local writes; A2 and A4 by applying every operation and comparing the predicted features
with the re-extracted ones. The results are therefore *validated* for an instance, not proved.

The weak spot is a locality failure that only an attacker's choice of parameters triggers, which a check on natural
inputs cannot see. EMBER's import overwrite is an example: natural files almost never contain the repeated library
name that triggers it. Checks therefore apply operations with adversarial parameters (repeated names, colliding names,
content placed next to existing strings). They remain tests.

What keeps the results sound is *flagging*. An undeclared structural edit, a scanned kind without a recognizer, or an
item known to violate A2 is flagged. The side-effect theorem makes no prediction for it, and the direction theorem
counts it as "both" on every feature it can reach. Flagging costs precision, never soundness.

## 6. Computing side effects exactly

This is the first payoff. For an edit whose item delta is known, the new feature vector follows from the item table of
the original input, without extracting the edited one. The delta is known in two cases: the operation declares it, or
the edit is stated in elements and A1 and A3 let us find it.

**Lemma 2 (the delta can be found locally).** Let an edit be a content, item-creating, or declared structural edit, and
let A1-A4 hold. Then its item delta can be computed from the item table of $z$, the written set $W$, and the elements
of $z'$ inside the margins (or, for a declared edit, inside the range it declares).

*Proof.* For an edit that writes no locating position, A1 says every parsed item survives with the same identity and
members. A parsed item whose members avoid $W$ is unchanged. A parsed item whose members meet $W$ gets its new content
from $z'$, and goes into $I^\sim$ if the content differs. For each scanned kind, A3 (parts 1 and 2) says the items
outside the margin are the same in $z$ and $z'$. The items of $z$ that overlap the margin are read from the item table;
the items of $z'$ that overlap it are found by the recognizer (A3, part 3); comparing them by identity gives that
kind's part of the delta. For a declared edit, A4 says the declared delta is the parsed part, and the scanned kinds are
handled as above, with the declared range in place of the margin. ∎

**Theorem 1 (exact side effects; C1).** Let an edit take $z$ to $z'$ with item delta $\Delta = (I^-, I^+, I^\sim,
I^\to)$, and let A0 and A2 hold. Write $\iota$ and $\iota'$ for an item before and after a modification.
1. Every additive sum $s$ changes by what the added items contribute, minus what the removed ones contributed, plus the
   change in each modified item's contribution:
   $$\mathbf{s}(z')_s = \mathbf{s}(z)_s + \sum_{\iota \in I^+} \mathbf{v}(\iota)_s - \sum_{\iota \in I^-}
   \mathbf{v}(\iota)_s + \sum_{\iota \in I^\sim} \big(\mathbf{v}(\iota')_s - \mathbf{v}(\iota)_s\big).$$
   Moved items change nothing.
2. A pool's new value can be computed from the item table of $z$ and $\Delta$, but in general *not* from its old value
   and $\Delta$ alone.
3. Every modeled feature follows: $\varphi_j(z') = \rho_j(\mathbf{s}(z'))$ for $j \in J$. So the side-effect vector of an
   edit aimed at the feature change $\delta^*$, $\eta = \varphi(z') - \varphi(z) - \delta^*$, is exact on $J$.

*Proof.*
1. A sum over a set splits over any partition of the set. The unchanged items of $z'$ are the unchanged items of $z$,
   with the same content, and so by A2 the same contributions. A moved item keeps its content, hence its contribution.
2. The pool's value over $z'$ is the maximum over the unchanged items, which the item table lists, and the added and
   modified ones. For the second half, take two inputs whose pools hold $\{5, 3\}$ and $\{5, 5\}$. Both pools have
   value 5. Removing an item of value 5 leaves 3 in the first and 5 in the second, so the old value alone does not
   determine the new one.
3. By A0. ∎

With Lemma 2, the theorem applies to every edit except undeclared structural ones, which are flagged.

**In the container.** Append the 9 bytes `\0http://x` to a file whose last byte is not printable. The bytes form one
new string, `http://x` (the leading `\0` keeps it from joining an earlier string), and nine new byte items. So f6 rises
by 1; f7's numerator rises by 8 and its denominator by 1; nine histogram bins rise by 1 each and their total by 9; and
f8 becomes 1. No entry is touched, so f1-f3 stay fixed. Each new feature value follows by re-applying the readouts. If
the file's last byte were printable, the new string would extend the old one: the margin reaches back to the nearest
non-printable byte, the old string is removed and the longer one added, and the arithmetic is the same.

**In the flow.** Inject a packet of size $m$ between two packets of a flow, $\Delta t_1$ after the first and
$\Delta t_2$ before the second. The packet count rises by 1, the total size by $m$, and the total of squares by
$m^2$. One consecutive pair, with gap $\Delta t_1 + \Delta t_2$, is removed, and two pairs, with gaps $\Delta t_1$ and
$\Delta t_2$, are added. So the total gap is unchanged while the number of gaps rises by one, and the mean gap (g5)
falls. The largest packet (g3) becomes $\max(g_3, m)$.

*Why the pool clause matters.* It is why the model keeps the item table and not only the totals. Incremental view
maintenance in databases knows the same fact: a maximum needs auxiliary state to survive deletions.

**Corollary 1 (sequences of edits).** A sequence of edits whose deltas are each known (Lemma 2, applied to the input
each edit is applied to) has exact side effects: apply Theorem 1 once per edit, carrying the item table forward.

## 7. Computing which way each feature can move

Robust detectors in the line of Incer et al. and Gimenez et al. need to know, for every feature, whether the attacker
can raise it, lower it, both, or neither, on every input the detector will face, not only on the inputs we tried.
Theorem 1 answers for one concrete edit. This section answers for all edits of a threat model at once, in two steps:
1. *Sums.* From each operation's signature and the contribution vocabulary, find the signs each sum's change can have.
   This needs no input.
2. *Features.* A fixed rule per readout type turns the signs of the sums into the direction of the feature.

### 7.1 Signs, envelopes, and directions

**Definition 10 (sign sets).** $\mathrm{sgn}(x)$ is $-$, $0$, or $+$. A *sign set* is a subset of $\{-, 0, +\}$, and
$-A$ flips each sign in $A$. The *sign sum* $A \boxplus B$ is the set of signs $x + y$ can have when $x$ has a sign in
$A$ and $y$ a sign in $B$. For example, $\{+\} \boxplus \{0\} = \{+\}$, but $\{+\} \boxplus \{-\} = \{-, 0, +\}$, since a
positive and a negative number can sum to anything.

**Definition 11 (envelope).** Let $F$ be a population of inputs. The *envelope* $E^F_o(s)$ of operation $o$ on sum $s$
is the set of signs of $\mathbf{s}(z')_s - \mathbf{s}(z)_s$, over every input $z \in F$ and every edit $z \to z'$ of
$o$ on it. We drop $F$ and $o$ from the notation when they are clear.

**Definition 12 (direction table).** A *direction table* gives each feature $j$ a direction $D_j$: $\mathsf{fixed}$,
$\mathsf{up}$, $\mathsf{down}$, or $\mathsf{both}$. It is *sound for $\mathcal{M}$ over $F$* if, for every input in $F$
and every single operation instance of $\mathcal{M}$, feature $j$ does not change when $D_j$ is fixed, does not fall
when it is up, and does not rise when it is down.

These four directions are Incer et al.'s four cases. Incer et al. assign them by hand, and Gimenez et al. derive them
from the feature changes of observed attacks.

### 7.2 Step 1: the signs of the sums

**Lemma 3 (envelopes from signatures).** Under A2, the change one item makes to one of its terms has a sign fixed by
the term and by whether the item is added, removed, or modified:

| Term | Item added | Item removed | Item modified |
|---|---|---|---|
| count, keyed | $\{+\}$ | $\{-\}$ | $\{0\}$ (cancels) |
| add, bins, unsigned hashed, max pool | $\{0, +\}$ | $\{-, 0\}$ | $\{-, 0, +\}$ |
| signed hashed | in each bucket, the signs of the keys that can land there | the negation | every sign, in the old bucket and the new |
| slot | — | — | every sign, unless the operation fixes the new value |
| opaque | the sign of (value $-$ default), over the declared range | the negation | every sign |

A min pool behaves as a max pool with the signs flipped. An operation's envelope on a sum is contained in the sign sum,
over all the item changes in its signature, of the entries above for the terms that write that sum. A flagged change
contributes $\{-, 0, +\}$ to every sum its kind writes.

*Proof.* By A2 and A4, an edit's effect on a sum is a sum of term changes of the items in its delta, each with a sign
in the table, by the term's declared range. The sign of a sum of numbers lies in the sign sum of their signs. For a
modified item, the count term contributes $+1 - 1 = 0$. ∎

In the container, adding an entry (e3) gives $\{+\}$ on f1 and $\{0, +\}$ on f3's pool, and, if the attacker picks the
name, both signs on every name bucket the allowed names reach. In the flow, injecting a packet (e5) gives $\{+\}$ on the
packet count and $\{0, +\}$ on the total size and the total of squares.

**Lemma 4 (which hash buckets an attacker can reach).** For a signed hashed term whose key the attacker picks from a set
$K$, the reachable (bucket, sign) pairs are exactly the hash and sign values of the keys in $K$. Enumerating part of $K$
gives witnesses, and once they cover every pair, the answer is exact.

*Proof.* Immediate from the term's definition. ∎

This answers Severi et al.'s remark that hashed features resist targeting because the hash is hard to invert. With a few
dozen buckets, a key landing in a chosen bucket with a chosen sign is found by brute force.

### 7.3 Step 2: from the sums to the features

**Lemma 5 (one rule per readout type).** Let $E_s$ be an operation's envelope on sum $s$. For every input, the change
of a feature has a sign in the set below.
- *Identity:* $E_s$.
- *Presence* (nondecreasing): within $E_s$.
- *Ratio* $a/b$, with $a \ge 0$ and $b > 0$ before and after: $E_a \boxplus ((-E_b) \cup \{0\})$. In words: the ratio
  can rise only if the numerator can rise or the denominator can fall. If $b$ can reach or leave zero, add every sign,
  unless the readout's default value is declared to lie on one side.
- *Normalized vector* (a bin over the total): the ratio rule. If the operation keeps the total fixed, it is the bin's
  own envelope.
- *Entropy:* $\{0\}$ if no bin can change, otherwise every sign.
- *Max or min:* the pool's envelope. Under an operation that only adds items, a max can only rise.
- *Distinct count:* up if keys are only added, down if only removed, otherwise both.
- *Field transform and selection:* $\{0\}$ if nothing they read is written (for a selection: every member and locating
  position of the selected item), otherwise every sign.
- *Opaque with default:* the opaque term's entry in Lemma 3.
- *Any other readout type*, until it is given its own rule: $\{0\}$ if none of its sums can change, otherwise every
  sign. The flow's standard deviation (g4) is handled this way.
- *Residual:* every sign.

*Proof.* Every rule except the ratio's follows from monotonicity or is trivially sound. For the ratio, write the
changes as $a' = a + \alpha$ and $b' = b + \beta$. Then
$$\frac{a'}{b'} - \frac{a}{b} = \frac{\alpha\, b - a\, \beta}{b\, b'}.$$
The denominator is positive. $\alpha b$ has the sign of $\alpha$, which lies in $E_a$. $-a\beta$ is $0$ if $a = 0$,
and otherwise has the sign opposite to $\beta$'s, which lies in $-E_b$. ∎

The rule for a ratio is what lets the flow extractor's mean gap (g5) be computed: injecting a packet leaves the total
gap fixed ($E_a = \{0\}$) and raises the number of gaps ($E_b = \{+\}$), so the mean gap can only fall.

### 7.4 The direction theorem

**Theorem 2 (the derived direction table is sound; C4).** Let $\mathcal{M}$ be a threat model and $F \subseteq
\mathrm{Pre}$ a population of inputs, and let A0, A2, and A4 hold on $F$. Build a table $D$:
- for each operation, apply Lemma 5's rules to envelopes that contain the true ones over $F$ (for example, those of
  Lemma 3);
- take the union of the resulting sign sets over all operations;
- read the union as fixed ($\{0\}$), up (within $\{0, +\}$), down (within $\{-, 0\}$), or both;
- mark every residual feature as both.

Then:
1. $D$ is sound for $\mathcal{M}$ over $F$.
2. If $F$ is closed under $\mathcal{M}$, $D$ holds along whole sequences of edits: from any $z \in F$, no reachable
   input lowers an up feature, raises a down feature, or changes a fixed one.
3. Without closure, part 2 can fail.

*Proof.*
1. For one operation instance on an input in $F$, each sum's change has a sign in its envelope. By Lemma 5, the
   feature's change has a sign in the rule's output, which lies in the union.
2. By induction on the length of the sequence. Closure keeps every intermediate input in $F$, so part 1 applies at
   every step, and "does not fall" is transitive.
3. Once a step leaves $F$, the envelopes say nothing about the next one. ∎

**Two conditions to keep in view.** Both concern the threat model and the population, not the extractor. First,
envelopes must hold over the population, not over a sample. Envelopes from Lemma 3 hold for any input. Envelopes
obtained by running an operation on a corpus hold only for the layouts the corpus contains. Second, part 2 needs
closure: no edit may take an input outside the precondition. Section 8 shows why closure matters for detectors that
route some inputs elsewhere. Both are discussed for EMBER in Section 10.

### 7.5 Sharper answers for a single input

The rules of Lemma 5 hold over every input, which a detector needs (Section 8). For one fixed input they can be
sharpened, which an attack or a per-input analysis can use: "can this file's entropy be raised by appending?".

**Lemma 6 (sharper tests for one input).** Fix an input $z$ and an operation.
1. *Ratio.* $a/b$ can rise iff some parameter value makes $\alpha b - a \beta$ positive. When the operation adds items,
   each with its own numerator part and positive denominator part, this happens iff some item's own ratio exceeds the
   current ratio $a/b$ (the mediant property). In the container, appending a string raises the average string length
   iff the new string is longer than the current average.
2. *Entropy rising.* Let $p$ be the normalized vector before the edit and $p'$ after, and $H$ the entropy. Since $H$ is
   concave,
   $$H(p') \le H(p) - \sum_i (p'_i - p_i) \log p_i .$$
   If the sum is nonnegative for every reachable $p'$, the entropy cannot rise. For an append of content with
   distribution $q$, the condition reads
   $$-\sum_i q_i \log p_i \le H(p).$$
   The left side is the *cross-entropy* of $q$ against $p$. In words: appended content can raise the entropy only if it
   is more surprising to the current distribution than the current distribution is to itself. (Content using a value
   with $p_i = 0$ has infinite cross-entropy and may raise it.) The condition is linear in $q$, so checking the extreme
   points of the allowed contents suffices.
3. *Entropy falling.* The minimum of a concave function over a convex set lies at an extreme point. For appends of a
   fixed length, the reachable $p'$ form a convex set whose extreme points are "the whole append is one repeated
   value". If none of these lowers the entropy, no append of that length does, and since these extreme points are
   real edits, the test is exact.

*Proof.*
1. By the identity in Lemma 5's proof. For added items, $\alpha b - a \beta = \sum_\iota n_\iota \beta_\iota b
   (\alpha_\iota / \beta_\iota - a/b)$, where $n_\iota$ counts the added copies of item $\iota$. This is positive for
   some choice of the $n_\iota$ iff some term is positive.
2. The first-order bound for a concave function, with $\partial H / \partial p_i = -(\log p_i + 1)$; the $+1$ terms
   cancel because both vectors sum to 1. An append gives $p' - p = t(q - p)$ for some $t \in (0, 1]$, and
   $\sum_i (q_i - p_i)\log p_i \ge 0$ rearranges to the cross-entropy condition.
3. The minimum principle for concave functions. ∎

**Lemma 7 (pattern features under extension).** Let a feature flag whether some string matches a regular expression
$P$. If $P$ uses no construct that looks past the end of the match (end anchors, word boundaries, lookahead), then
extending a string on the right can only add matches, never remove them. The same holds on the left for constructs that
look before the match.

*Proof.* Without such constructs, whether $P$ matches a substring depends only on that substring, which an extension
does not change. ∎

The test reads the parsed pattern. It is sound, and may call a pattern two-sided when it is not.

## 8. From directions to detectors that cannot be evaded

Gimenez et al. prove that a detector is robust if each feature can only move one way under the attacker's edits and
the classifier's score never falls in those directions. Incer et al. build such detectors from a direction table
written by hand. Theorem 2 supplies the table from the extractor, and a classifier trained with monotone constraints
supplies the rest.

**Definition 13 (monotone with respect to a table).** A malware score $h$ is *monotone with respect to $D$* if it reads
no "both" feature, and never falls when up features rise, down features fall, and fixed features stay. A
gradient-boosted tree model trained with a $+1$ constraint on up features and $-1$ on down features, with fixed features
unconstrained and "both" features excluded, has this property.

**Theorem 3 (robustness).** Let $D$ be sound for $\mathcal{M}$ over $F$, with $F$ closed under $\mathcal{M}$, and let
$h$ be monotone with respect to $D$. Then for every $z \in F$ and every $z' \in \mathrm{Reach}_\mathcal{M}(z)$,
$h(\varphi(z')) \ge h(\varphi(z))$. A detected malware sample stays detected under any sequence of edits in the threat
model.

*Proof.* By Theorem 2, part 2, the feature vectors of $z$ and $z'$ differ only in the allowed directions. The score
reads no "both" feature and does not fall in the allowed directions. This is Gimenez et al.'s Proposition 1, with the
preorder "$z'$ is reachable from $z$" and a feature map made monotone by $D$. ∎

**Corollary 2 (routing to a fallback detector).** A practical detector may score inputs in $\mathrm{Pre}$ with a
constrained model and all other inputs with an unconstrained fallback.
1. If $\mathrm{Pre}$ is closed under $\mathcal{M}$, every detected input in $\mathrm{Pre}$ stays detected.
2. If some operation takes an input in $\mathrm{Pre}$ outside it, the attacker reaches the fallback, which has no
   guarantee.

*Proof.* (1) Theorem 3 with $F = \mathrm{Pre}$. (2) The fallback is unconstrained. ∎

**What is ours and what is not.** The route from monotone features to robustness is Gimenez et al.'s and Incer et
al.'s. The guarantee rests on four things together: the direction table, the classifier's constraints, the
precondition's closure, and A0-A4 on the population. What Theorem 2 adds is the table: computed from the extractor,
sound, and covering every feature, which hand analysis cannot do for thousands of features.

## 9. How general is the model?

Pierazzi et al.'s formalization assumes nothing about $\varphi$. That is its strength, and also why it cannot compute
anything: with the extractor a black box, side effects can only be observed. Our model gives up some of that
generality in exchange for computation. This section states where the trade lands.

**What each result needs.** The definitions mention no file format, and the properties split as Section 5 described:

| Result | Needs | Format-dependent? |
|---|---|---|
| Side effects of an item-level edit (Theorem 1) | A0, A2, A4 | no |
| Side effects of an element-level edit (Theorem 1 with Lemma 2) | A0-A4 | A1 and A3 |
| Directions (Theorem 2) | A0, A2, signatures (A4; or Lemma 1, from A1 and A3, for element-level operations), envelopes over $F$ | only for element-level operations |
| Robustness (Theorem 3) | Theorem 2, closure of $\mathrm{Pre}$, a monotone classifier | as Theorem 2 |

So the format enters at one place: working out which items an edit stated in raw elements changes. That is a fact about
the format's parser ("which positions decide where things are"), and A1 and A3 are the general conditions under which
it can be worked out locally, the same conditions incremental parsers rely on. For a threat model stated in items, the
model is as format-free as its two remaining properties: contributions that depend only on the item (A2), and tools that
do what they declare (A4).

**Which extractors fit.** Those built by counting and aggregating over recognized pieces. This covers most static
malware feature sets in the literature: EMBER and its descendants, Drebin and other Android permission and API sets,
Hidost and other PDF structural paths, byte and opcode n-grams, string-based features, and flow statistics for network
traffic. For these, A2 usually holds by construction, since each piece is counted where it is found. The exceptions
are the three patterns of Section 5.1 (a global total inside a contribution, deduplication, overwriting), and the first
two are repaired by moving work into the readout.

**The price.** The framework says what must be recorded; it does not make recording it free. Recording an extractor's
items, sums, and readouts is engineering done once per extractor, not once per question. For pointer-heavy formats,
finding every locating position is the bulk of it: on EMBER it took several rounds of single-byte checks to find every
place the PE parser looks (Section 10). For sequential inputs it is small.

**What does not fit.**
- *Global analyses* such as call-graph centralities or data-flow summaries: a piece's contribution depends on the whole
  program, so A2 fails everywhere and the model degrades to flagging.
- *Learned representations:* the features of a neural network over raw bytes have no item layer, so A0 fails.
- *Edits and features in different element spaces:* dynamic features from execution traces, when the attacker edits
  the binary. A byte edit does not map to trace positions without a model of execution.
- *Whole-input rewrites:* packing and encryption are undeclared structural edits by nature. They are flagged, never
  predicted.

**The claim we can defend.** For the class of extractors that dominate static malware detection, the feature-space
consequences of a threat model can be computed from the instrumented extractor, under properties that can be checked
per item kind; the format matters only for edits stated in raw elements. The generality beyond PE is argued here on
paper and shown on one extractor so far. A second domain (for example, flow statistics, which exercises ratios, pools,
and a readout type outside the list) is what would establish it.

## 10. The EMBER instance

This section collects the PE- and EMBER-specific facts that the model abstracts away.

**Kinds.** `byte`, `window` (byte-entropy windows of 2,048 bytes at multiples of 1,024), and `string` are scanned. The
Rich header is also scanned, within a search range. `section`, `overlay`, `field`, `import`, `library`, `export`,
`certificate_table`, and `entry` (the entry section, as a selection) are parsed. The residual is pefile's 88 warning
flags and `is_pe`.

**Operations.** Appending, writing section slack, the DOS header, loader-ignored header fields, and the checksum are
stated in elements; their signatures come from Lemma 1 (and, for the in-place header operations, from running them on
the corpus: see the population caveat below). Adding a section, adding imports, and the other catalogue operations are
stated in items and declare their deltas (`catalogue.py`). All are written by our own byte-level edits, never by LIEF,
so that A4 holds by construction.

**Locating positions (A1).** For each kind, the header fields and table bytes pefile reads. Kind-level positions include
`NumberOfSections` and the bounds of the Rich header's search range. The overlay's start is decided by every section's
and directory's extent. Positions past the end of the file are recorded too, for sections whose raw data a truncated
file no longer contains. On such a file appending is structural, and the engine flags it. This is exactly the case the
former hand rules missed.

**Margins (A3).**
- Strings: to the nearest non-printable byte on each side.
- Windows: the windows overlapping the write, plus, under appending, the last (window $-$ step) bytes before the old
  end. A file shorter than one window is a single window, so its margin is the whole file.
- Rich header: its whole search range.

**Repairs for A2.**
- Section size ratios divide by the file length: the section contributes its raw size, and the readout divides.
- The library set: keyed counts with a distinct-count readout.
- A repeated DLL name in a second import descriptor overwrites the first one's functions: patched as a pure addition
  (`ImportsInfoMerged`), noted in `docs/upstream-issues.md`.

**Readouts outside the general list.** EMBER's minimum section entropy and minimum size ratios are minimum pools that start at 0 over
nonnegative attributes, so they are constant ($\{0\}$). Three-letter section names already reach all 100 (bucket, sign)
pairs of the section-name hash (Lemma 4).

**Checks and results.**

| Property | Check | Result | Run |
|---|---|---|---|
| A0 | G1: readouts over the item table vs `feature_vector` | bit-exact on 100 and 2,000 files, all 2,480 modeled features, both import variants; re-encoded groups too | 90, 102, 104 |
| (projection) | G2: items spread over members vs today's provenance matrix | equal | 90 |
| A1 | G5: single-byte flips across headers and directory data | 55 failing pairs from three pefile rules in round 1; 0 failures on 58,666 flips after the fix | 91, 95 |
| A3 | G6: random in-place writes, engine vs re-extraction | 1 failure in 1,561 in round 1; 1,560/1,560 and 1,463/1,463 after the fix | 93 |
| A4, A2 | G7: every operation, our own byte-level edits with adversarial parameters | direction check passes on every edit after four general rules; the precondition variant needs the plain-layout clauses | 103, 104, 107 |
| Theorem 1 | G4: engine vs re-extraction and hand predictors | append exact on 89 files, the other 11 flagged by the engine; DOS overwrite 100/100; add-section equal to the hand predictor | 92 |
| Corollary 1 | combined edits (up to 3 added sections plus an append) | 1,105/1,105 at the predicted feature vector | 111 |
| Theorem 2 | G3: derived table vs former hand rules | every disagreement was the hand rules' error, each witnessed by a real file and edit | 88, 97, 98, 101, 102 |
| Theorem 3 | Table A1: constrained detectors under toolkit, held-out, and adaptive attacks | smallest score change exactly 0.0 on files in the precondition | 99, 100, 105 |

**The population caveat.** The in-place header operations get their envelopes by running them on every corpus file and
taking the union (`catalogue.file_region_changes`). On the 100 pilot files, header overwrites never reached section
entropy. On the 2,000-file set they did, on 4 files whose `.bss` section has `PointerToRawData` 0, so its "raw data" is
the header (run 102). The precondition's plain-layout clause ("headers hold only headers") excludes that layout.
Whether it excludes every such layout is open.

**The closure caveat.** The precondition is checked on the original file only (`catalogue_checks.py`,
`a1_evaluate.py`). Corollary 2 needs it to hold on every edited file too.

These two caveats are small, and in the paper they belong in an appendix (user, 2026-11-02). Two cheap checks would
settle them (not run; each takes minutes at pilot scale):
- **P1 (closure).** Evaluate the precondition on every edited file G7 already writes, and count the edits that take a
  passing file to a failing one. *Hypothesis:* none do. Appending only shrinks what lies past the end; the declared
  operations update `SizeOfImage`, keep headers holding only headers, and keep pefile's overlay starting at a section's
  end. A failure would mean an operation's declaration or the precondition must change.
- **P2 (envelope stability).** Derive the in-place envelopes on 100 and on 2,000 files, and compare them on files that
  pass the precondition. *Hypothesis:* they are equal there. Equality is evidence for the population condition, not
  proof; a difference inside the precondition is a soundness gap.

## 11. Still to write

- **Coupling (C2):** which features move together under an operation (a corollary of Theorem 1), and which can never be
  moved separately, decided by the cone of the operations' change vectors or by a shared denominator. Severi et al.'s
  example: the number of sections and the number of writable sections.
- **The reachable region (C3):** a sound region containing $\mathrm{Reach}(z)$, as verified training needs. It covers
  the cone of added contributions; the images of that cone under each readout (the mediant bound for ratios, the exact
  histogram polytope, the entropy interval); and boundary effects between added chunks. Check: run 111.
- **The provenance matrix as a projection:** today's matrix spreads each item's contribution over its members, which
  records membership but not location. For additive features, the item weights are Shapley values. Check: G2.
- **Tightness:** when every direction the table allows is realized by some edit, and what flagging costs.
- **Cost:** an update costs work proportional to the delta and the margins, not to the input.
- **Positioning:** Pierazzi et al.; incremental view maintenance and incremental parsing; abstract interpretation (sign,
  interval, and polyhedral domains); taint tracking and Cheney et al.'s dependency provenance; Treant and Chen et al.
  (CCS 2021) as consumers of the output; Demontis et al.'s secure classifiers ("Yes, Machine Learning Can Be More
  Secure!") as an earlier route to robustness on Drebin features.
