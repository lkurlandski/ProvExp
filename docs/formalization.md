# Feature provenance: a formal model

Draft started 2026-11-02. Revision 3 (the same day) applies the user's feedback collected in `docs/feedback.md`:
- the toy formats are replaced by small real examples from three domains (Windows executables with EMBER features,
  Android apps with Drebin features, network traffic with CICFlowMeter features), carried through every section;
- the old Sections 5 and 6 are merged into one section that starts from what we want to compute, shows how the
  computation can go wrong, and only then states the requirements and the theorem;
- the requirements are named by what they mean, not by codes;
- a short algebraic remark (sums as a monoid homomorphism) explains why maxima need more bookkeeping than sums.

Revision 4 (the same day; `docs/feedback.md`, items 6-12, delegated by the user) fixes two errors (appending and
Requirement 3; the presence rule), qualifies the "no attack needed" claim for layout-dependent signatures, moves the
pattern lemma next to the term rules and the single-input tests to Section 10, and turns the routing corollary into a
remark. Revision 5 (`docs/feedback.md`, item 13) shortens Section 2 to a primer on the three
domains and names features in plain words where they are used, without labels.

**Status.** Sections 1-7 are written for review, with full proofs of the side-effect, direction, and robustness
theorems. Section 8 assesses how general the model is, Section 9 holds the EMBER instance, and Section 10 lists what
remains: coupling, the reachable region, the provenance matrix as a projection, tightness, cost, and positioning.

The document is the source for the paper's framework section and its appendix. It builds on
`docs/feature-provenance-model.md` (the first sketch of the model: claims C1-C4, assumptions A1-A4) and
`docs/item-layer-design.md` (the instrumented EMBER extractor and its checks G1-G7). Where a result corresponds to an
old claim or assumption, the old label is given once, in parentheses.

## Notation

We reuse Pierazzi et al.'s notation (S&P 2020) for everything they define. We add symbols only for the inside of the
feature extractor, which they treat as a black box.

| Symbol | Meaning | Where |
|---|---|---|
| $Z$, $z$ | the problem space (all inputs) and one input: a file, an app, a packet trace | 1 (Pierazzi) |
| $\varphi$, $x = \varphi(z)$ | the feature extractor, and the feature vector it outputs | 1 (Pierazzi) |
| $n$; $j$ | the number of features; a feature's index | 1 |
| $h$ | the classifier's malware score (Pierazzi's discriminant function) | 1 (Pierazzi) |
| $T$; $\mathcal{T}$ | one transformation of an input; the transformations available to the attacker | 1 (Pierazzi) |
| $\Gamma$ | the problem-space constraints: $\mathcal{T}$, preserved semantics, plausibility, robustness to preprocessing | 1 (Pierazzi) |
| $\Omega$ | the feature-space constraints that $\Gamma$ implies; Pierazzi writes $\Gamma \vdash \Omega$ | 1 (Pierazzi) |
| $\delta^*$; $\eta$ | the feature change an attacker aims for; the side-effect vector, the rest of the change | 1, 5 (Pierazzi) |
| $\mathrm{Reach}(z)$ | the inputs the attacker can produce from $z$ | 1 |
| element; $\lvert z\rvert$; $z[p]$ | the smallest unit of an input (a byte, a packet); the length of $z$; the element at position $p$ | 3.1 |
| $\iota$; $\mathcal{I}(z)$ | an item (a piece the extractor's loops iterate over); all items of $z$ | 3.1 |
| $\kappa(\iota)$ | the item's kind (section, string, permission, packet, ...) | 3.1 |
| $\mathrm{id}(\iota)$ | the item's identity: how the extractor reaches it | 3.1 |
| $M(\iota)$ | the item's members: the positions its content is read from | 3.1 |
| $c(\iota)$ | the item's content: the elements at its members, in order | 3.1 |
| $L(\iota)$; $L(z)$ | the item's locating positions (they decide whether and where it exists); all locating positions of $z$ | 3.1 |
| $S$; $s$ | the set of sums (the extractor's running totals); one sum | 3.2 |
| $\mathbf{v}(\iota)$ | the item's contribution: what it adds to each sum | 3.2 |
| $\mathbf{s}(z)$ | the sum vector: each sum's total over all items of $z$ | 3.2 |
| $\rho_j$ | the readout of feature $j$: the formula applied to the sums | 3.3 |
| $J$ | the modeled features (those computed as a readout of sums); the rest are the residual | 3.4 |
| $W$ | an edit's written set: the positions it changes | 4.1 |
| $\Delta = (I^-, I^+, I^\sim, I^\to)$ | an item delta: the removed, added, modified, and moved items | 4.2 |
| $o$; $\theta$; $\Theta_o(z)$ | an operation; one parameter value; the values allowed on input $z$ | 4.3 |
| $\Sigma_o$ | the operation's item signature: which kinds it can add, remove, or modify, with what contributions | 4.3 |
| $\mathcal{M} = (O, \mathrm{Pre})$ | a threat model: a catalogue of operations, and the precondition (the inputs it applies to) | 4.3 |
| $\mu_\kappa(z, W)$ | the margin of a scanned kind: the positions around an edit where its items can change | 5.2 |
| $F$ | a population of inputs, e.g. the files a detector will see | 6.1 |
| $\mathrm{sgn}$; $\boxplus$ | the sign of a number ($-$, $0$, or $+$); the sign sum of two sets of signs | 6.1 |
| $E^F_o(s)$ | the envelope: the signs operation $o$ can give the change of sum $s$, over $F$ | 6.1 |
| $D_j$ | the direction of feature $j$: fixed, up, down, or both | 6.1 |

## 1. The problem: from edits to feature changes

Pierazzi et al. separate the *problem space* $Z$, the real objects an attacker edits (executables, Android apps, PDF
documents, network traffic), from the *feature space*, the vectors $x = \varphi(z) \in \mathbb{R}^n$ that a
classifier with score $h$ sees. The attacker edits an object with transformations $T \in \mathcal{T}$, restricted by
problem-space constraints $\Gamma$: the edited object must still work, look plausible, and survive preprocessing. The
classifier only sees what the edits do to the features. Pierazzi et al. write $\Gamma \vdash \Omega$: the
problem-space constraints determine which feature-space changes are possible. Every line of work on realizable
attacks and robust detectors needs some view of the set

$$\mathrm{Reach}(z) = \{\, \varphi(T(z)) : T \in \mathcal{T} \,\},$$

the feature vectors an attacker can reach from one object, and each needs a different view of it. An attack needs the
*side effects* of one edit: Pierazzi et al.'s $\eta$, everything the edit changes besides the change $\delta^*$ it was
aiming for. A monotone detector needs the *direction* each feature can move in (Incer et al.'s four cases, Gimenez et
al.'s certified detectors). A backdoor or feature-space attack needs to know which features *always move together*
(Severi et al.). Verified training needs a *region* that contains every reachable vector (Chen et al.).

None of these views is computed today. Pierazzi et al. state that the side effects of an edit cannot feasibly be
computed in advance, because $\Gamma$ has no closed form, and they find them by applying each edit and re-extracting.
Others write the feature-space constraints by hand (the network-traffic literature writes hundreds of them, Section
2.3), or learn them from the attacks they have observed. Hand analysis does not scale to thousands of features, and
learned constraints miss whatever the observed attacks did not do.

**The claim of this document.** For a broad class of extractors, these views can be *computed* from the extractor
itself. The class is the extractors that find pieces of the input, add up what each piece contributes, and apply a
formula per feature. Instrumenting such an extractor once, to record its pieces, its totals, and its formulas, turns
$\Gamma \vdash \Omega$ from a relation one estimates into a computation. The computation is exact for the side effects
of one edit and sound for the directions of a whole threat model. It needs no attack to be run: the directions follow
from what each operation can add, remove, or change. For operations stated in raw elements, what they can change
depends on the input's layout, and is computed per input from its recorded structure; such directions hold for the
population of inputs they were computed over (Section 6.2).

The document proceeds as follows. Section 2 introduces three real feature extractors from three security domains,
which every later definition is tried on. Section 3 describes the class of extractors, and Section 4 describes an
attacker's edits in that class's terms. Section 5 predicts what one edit does to the features, and says when the
prediction is right. Section 6 predicts which way each feature can move under any edit of a threat model, and Section
7 turns that into detectors no such edit can evade. Section 8 asks how general the class is, and Section 9 gives the
instance we have built.

## 2. Three domains

The definitions below are abstract, so each is tried on three real extractors, one from each of three security
domains where adversarial examples are studied. They are chosen to differ as much as possible. A Windows executable
is a raw binary full of pointers, edited byte by byte. An Android app is a container whose features are sets of
names, edited by adding code and declarations. A network trace is a stream with no pointers at all, whose features
are statistics. This section says only what the later examples need about each; features are introduced where they
are used, in plain words, with the extractor's own name in code font at first use.

**Windows executables and EMBER.** A Windows executable (a PE file) is a byte sequence. Its headers hold a *section
table*, whose entries give each section's name, the offset where its raw data lies in the file, its size, and its
permissions. Bytes after the last section are the *overlay*, often appended data. EMBER, the standard static feature
set for Windows malware (here its 2024 version, computed by the `thrember` extractor), computes about 2,500 features:
the byte histogram and entropies, statistics of the printable strings (runs of at least 5 bytes in the range
`0x20`-`0x7f`), header fields, per-section statistics, and the imported libraries and functions. Attacks on PE
detectors edit bytes: they append data to the overlay, write into the slack space at the end of a section, overwrite
header bytes the loader ignores, or add a section.

**Android apps and Drebin.** An Android app (an APK) is a ZIP archive. Two of its files matter here: the *manifest*,
which declares the permissions the app requests, its components (activities, services, receivers), the intents they
listen for, and the hardware it uses; and the *bytecode*, which holds the app's code and string constants. Drebin,
which the Android malware literature still uses almost exclusively (or small variations of it), extracts eight sets of
strings: hardware components, requested permissions, app components, filtered intents, restricted API calls, used
permissions, suspicious API calls, and network addresses. Every string ever seen becomes one binary feature, set if
the app contains it. A *used* permission is one the app both requests and needs for some API call in its code
(Drebin matches calls to permissions with Felt et al.'s map): a call to `getDeviceId` and a request for
`READ_PHONE_STATE` together set the used-permission feature for `READ_PHONE_STATE`. Attacks on Drebin edit the app at the level of its
declarations and code: they add manifest entries, or, as Pierazzi et al. do, transplant pieces of code from benign
apps. Removing features is harder, since the app must keep working, but obfuscation can hide API calls (behind
reflection) and strings (by encrypting them).

**Network traffic and CICFlowMeter.** A packet trace is a sequence of packets in time order. Each packet has header
fields (addresses, ports, protocol, TCP flags, window size), a payload length, and a timestamp. CICFlowMeter, the feature
extractor behind the most widely used intrusion-detection datasets (CIC-IDS2017 and its successors), groups packets
into bidirectional *flows*: one per (addresses, ports, protocol) tuple. A flow ends at a FIN exchange or a reset, or when a packet arrives more than 120 seconds after
the flow's first packet, which starts a new flow. The direction that opened the flow is *forward*. It computes about 80 statistics per flow: packet counts and payload lengths per
direction (total, mean, standard deviation, minimum, maximum), the gaps between consecutive packets, flag counts,
bytes and packets per second, and the first packet's TCP window size. Attacks on flow-based detectors edit traffic the
attacker controls: they pad packets, delay them, inject extra packets, or split one packet into two. Much of this
literature works in feature space and writes the dependencies between features by hand. For Chernikova and Oprea's
botnet features (CTU-13 connections aggregated per port and minute into 756 totals, minima, and maxima, used by FENCE),
Simonetto et al. wrote 360 constraints by hand (326 linear, 34 non-linear). Section 8 returns
to this as the alternative the model replaces.

## 3. The shape of a feature extractor: items, sums, readouts

All three extractors, written as code, look like this:

```
totals = zeros(S)
for item in pieces(z):                      # strings, sections, permissions, API calls, packets, ...
    totals += contribution(item)            # counts, lengths, hash buckets, maxima
x = [readout_j(totals) for j in features]   # identity, ratio, entropy, standard deviation, ...
```

The model gives each line a name. The pieces the loop iterates over are *items*. The running totals are *sums*. The
final formulas are *readouts*. The reason for separating them is that an attacker's edit is easy to describe in terms
of the first line (which pieces it adds, removes, or changes) and hard to describe in terms of the last (how it moves
2,500 features). The model translates from one to the other.

### 3.1 Items: what the extractor iterates over

An input $z$ is a sequence of *elements*: bytes in a file, packets in a trace. $|z|$ is its length and $z[p]$ is the
element at position $p$.

**Definition 1 (item).** An *item* $\iota$ of $z$ is one iteration of one of the extractor's loops: a piece of the
input the extractor recognizes and computes with. It has
- a *kind* $\kappa(\iota)$, saying which loop finds it: section, string, byte, permission, API call, packet, ...;
- an *identity* $\mathrm{id}(\iota)$, saying how the extractor reaches it: "section table entry 3", "the string
  starting at offset 812", "the third forward packet of this flow";
- *members* $M(\iota)$: the positions its content is read from;
- *content* $c(\iota)$: the elements at its members, in order;
- *locating positions* $L(\iota)$: the positions whose values decide whether the item exists, and where its members
  lie.

$\mathcal{I}(z)$ is the set of all items of $z$. Two items of different inputs are *the same item* if they have the
same kind and identity. This is how we tell, after an edit, whether an item was modified or replaced.

In a PE file, a section is an item. Its identity is its index in the section table. Its members are its table entry
and its raw data. Its locating positions are the header field holding the number of sections, which decides whether
the entry is read at all, and the offset and size fields of its entry, which decide where its raw data lies. A
printable string is an item whose identity is its start offset and which has no locating positions: it is found by
scanning, not by following a pointer. Each byte is an item too, for the histogram and the entropy.

In an APK, each permission declaration in the manifest is an item, and so is each API call site and each string
constant in the bytecode. In a trace, each packet is an item, and so is each pair of consecutive packets in a flow
(for the gaps between packets). A packet's addresses, ports, and protocol are locating positions: they decide which flow it
belongs to. So are its FIN flag, which ends the flow, and its timestamp, since a packet more than the timeout after the flow's first packet starts a new flow.
Its length, other flags, and window size are content.

**Members and location answer different questions.** Membership answers "if this element changes, whose content
changes?". Location answers "if this element changes, which items might appear, disappear, or move?". The two have
different consequences. A change to members modifies an item, and the model can compute the effect. A change to a
locating position changes how the input is parsed, and the model must either be told the result or decline to
predict.

**Two sorts of kinds.** A *parsed* kind is found by following pointers or keys from fixed places: sections, header
fields, manifest declarations, flows grouped by their tuple. A *scanned* kind is found by examining content wherever
it lies: bytes, printable strings, n-grams, consecutive packet pairs. For each scanned kind the extractor contains a
*recognizer*: a routine that, given the input and a range of positions, returns the items of that kind overlapping
the range.

**Locating positions of items that do not exist.** Some positions decide where items *could* be. In a PE file, the
number-of-sections field decides whether the bytes after the last table entry form another section, so writing those
bytes does nothing unless the count changes too. Each kind therefore also has *kind-level* locating positions, and
$L(z)$ denotes all locating positions of $z$: those of its items and those of its kinds. A locating position may lie
past the end of the input, because extending the input can bring a pointed-to item into existence.

### 3.2 Sums: what each item contributes

**Definition 2 (sums and contributions).** The extractor keeps a finite set $S$ of running totals, called *sums*. Each
item $\iota$ has a *contribution* $\mathbf{v}(\iota)$: the amount it adds to each sum, zero for the sums it does not
touch. The *sum vector* $\mathbf{s}(z)$ holds each sum's total over all items of $z$. Most sums add their items'
contributions. A few, called *pools*, keep their maximum (or minimum) instead.

In EMBER, the number of printable strings (`numstrings`) is a sum to which every string contributes 1, and the total
string length (the numerator of the average length, `avlength`) one to which it contributes its length. EMBER also
hashes section names into 50 buckets, and each bucket is a sum to which a section contributes its size, with a sign of
$\pm 1$, if its name hashes there. Each bin of the byte histogram is a sum to which every byte contributes 1 in its own
bin. The largest section entropy is a pool. In Drebin, each string in the vocabulary has a sum
counting its occurrences, and one item can write several: a call to `getDeviceId` contributes 1 to the count of
`api_call::getDeviceId` and 1 to the count of calls needing `READ_PHONE_STATE`. In CICFlowMeter, each flow keeps,
for its forward packets, a count, a total length, and a total of squared lengths, and pools for the largest and
smallest length.

**Why sums are easy and pools are not.** In algebraic terms, the sum vector maps a collection of items to a product
of commutative monoids: $(\mathbb{R}, +)$ for the additive sums and $(\mathbb{R} \cup \{-\infty\}, \max)$ for the
pools. Requiring each item's contribution to depend only on the item (Section 5.2) is requiring this map to be the
fold of $\mathbf{v}$ over the items, the unique homomorphism that extends $\mathbf{v}$ from single items to
collections. Commutativity is why the order of the extractor's loop does not matter. Features that depend on order,
like the gaps between packets, enter only by making the ordered piece itself an item (a consecutive pair). The one
difference that matters later is that $(\mathbb{R}, +)$ is a group and $\max$ is not. With an inverse, removing an
item is undone by subtracting its contribution, so the new total follows from the old total and the change. Without
one, removing the largest item leaves a total that cannot say what the runner-up was. This is why the model keeps
every item and not only the totals (Theorem 1, part 2).

Contributions are written in a small vocabulary of *terms*. The vocabulary is there because each term has a known sign
behavior, which Section 6 uses: from the term alone one can tell which way a sum can move when an item is added,
removed, or changed.

| Term | What the item adds | Sign | EMBER | Drebin | CICFlowMeter |
|---|---|---|---|---|---|
| count | 1 to one sum | $+$ | string count, section count | — | forward packet count, SYN flag count |
| add | a nonnegative attribute (a length, a size; 0 or 1 for a pattern match) | $\ge 0$ | total string length, URL matches | — | total forward length, total of squared lengths |
| bins | nonnegative counts to a family of sums | $\ge 0$ per bin | byte histogram | — | — |
| hashed | an attribute (or 1) to bucket $\mathrm{hash}(\text{key})$, times $\pm 1$ if the hash is signed | the hash's sign, if signed | section sizes by name | — | — |
| keyed | 1 to the count of its key | $+$ | imported libraries | permissions, API calls, URLs | — |
| slot | the value of a field that exactly one item holds | any | header fields | — | initial window size |
| opaque | a value computed by code the model does not open, within a declared range | within the range | signature checks | — | — |
| pool | an attribute into a maximum (or minimum) | $\ge 0$ | largest section entropy | — | longest and shortest forward packet, longest gap, timestamps |

### 3.3 Readouts: the formula per feature

**Definition 3 (readout).** Each modeled feature $j$ has a *readout* $\rho_j$: a formula applied to a few sums. The
model records each readout's *type*, not only its value, because the type decides how the sums' directions become the
feature's direction (Section 6).

| Readout | Formula | EMBER | Drebin | CICFlowMeter |
|---|---|---|---|---|
| identity | the sum itself | string count, URL count, section count, name buckets | — | forward packet count, total forward length, SYN flag count |
| presence | $\min(1, s)$, or any nondecreasing function of one or more sums | — | every feature (a used permission needs two sums positive) | — |
| ratio | one sum divided by another | average string length | — | mean forward length, mean gap |
| normalized vector | each bin divided by the bins' total | byte histogram | — | — |
| entropy | the entropy of a normalized vector | file entropy | — | — |
| max or min | a pool's value | largest section entropy | — | longest and shortest forward packet, longest gap |
| distinct count | the number of keys with a positive count | number of imported libraries | — | — |
| field transform | a bit test or table lookup of one slot | header flags | — | — |
| selection | an attribute of the one item a rule picks | the entry section's name | — | initial window size |
| opaque with default | an opaque value, or a default when its item is absent | signature features | — | — |
| standard deviation | $\sqrt{Q/N - (T/N)^2}$ over a count $N$, total $T$, total of squares $Q$ | — | — | standard deviation of forward lengths |
| rate | a sum divided by the difference of two pools | — | — | bytes per second |

The first ten types are what EMBER and Drebin use. CICFlowMeter needs the last two, which shows how the list grows: a
new readout type costs one new rule in Section 6 and nothing else. The list is closed in one respect. Every readout is
a fixed formula over a bounded number of sums. In the terms of Gray et al.'s data-cube paper, sums and pools are
*distributive* aggregates and readouts are *algebraic* ones. A *holistic* aggregate, such as a median packet length,
has no bounded summary, and falls outside the class (Section 8).

### 3.4 The class of extractors

**Definition 4 (sum-then-readout extractor).** An extractor $\varphi$ is a *sum-then-readout extractor* over a set of
*modeled features* $J$ if it has items, contributions, and readouts such that, for every input $z$ and every
$j \in J$,

$$\varphi_j(z) = \rho_j\big(\mathbf{s}(z)\big).$$

The features outside $J$ are the *residual*. The model makes no claim about them, and every result treats them as
"anything can happen". In EMBER, the residual is the PE parser's warning flags.

The *item table* of $z$ lists every item with its kind, identity, members, locating positions, and contribution. It is
what the instrumented extractor records, in the same pass that computes the features.

The three examples side by side:

| | EMBER (PE) | Drebin (APK) | CICFlowMeter (traffic) |
|---|---|---|---|
| elements | bytes | bytes of the archive's files | packets |
| parsed kinds | sections, header fields, imports, libraries | manifest declarations | flows (grouped by tuple) |
| scanned kinds | bytes, strings, entropy windows | API call sites, string constants | packets, consecutive pairs |
| locating positions | header counts, section table offsets and sizes | archive and manifest structure | addresses, ports, protocol, FIN flags, timestamps |
| contributions | counts, sizes, hashed sizes, bins | keyed counts | counts, lengths, squared lengths, pools |
| readouts | identity, ratio, entropy, normalized vector, max, distinct count, ... | presence | ratio, max/min, standard deviation, rate |
| typical edits | append, write slack, overwrite ignored headers, add a section | add declarations, transplant code | pad, delay, inject, split packets |

Other common feature sets fit the same three layers: PDF structural paths (Hidost) are presence over paths in the
document's object tree, and byte or opcode n-grams are hashed counts over windows of $n$ elements, a scanned kind.

## 4. Edits, seen as changes to items

An attacker states an edit in one of two ways. Some edits are stated in elements: "write these bytes here", "append
that", "pad this packet". Others are stated in items: "add a permission", "add a section named `.x`", "inject a
packet". The extractor's sums change because items change, so the model translates every edit into the items it adds,
removes, or changes. This section sets up the vocabulary for that translation.

### 4.1 Edits

**Definition 5 (edit, written set).** An edit takes $z$ to $z'$. It is *in place* if every element keeps its position;
overwrites, appends, and truncations are in place. Its *written set* $W$ is the set of positions where $z'$ differs
from $z$, together with any positions gained or lost at the end. An edit that inserts or deletes elements in the
middle *shifts* every element after that point; injecting a packet into a trace is an example.

### 4.2 Item deltas

**Definition 6 (item delta).** The *item delta* of an edit compares the items of $z$ and $z'$ by identity:
- $I^-$, the *removed* items: identities in $z$ but not in $z'$;
- $I^+$, the *added* items: identities in $z'$ but not in $z$;
- $I^\sim$, the *modified* items: identities in both, with different content;
- $I^\to$, the *moved* items: identities in both, with the same content at different members.

Every other item is unchanged: same identity, same content, same members.

Modification is kept apart from "remove, then add" for two reasons. Some sums can only be modified, because exactly
one item ever writes them: a header field's value, a flow's initial window size. And when an item is modified, its
count terms cancel exactly. This is what makes, for example, renaming a section leave the number of sections fixed.

A shift changes the identity of every scanned item after the insertion point, since scanned items are identified by
position. They appear in the delta as removed and re-added with equal content, and their contributions cancel.

### 4.3 Operations, signatures, and threat models

An attacker's toolkit offers a few *operations*, each with parameters. One operation describes a whole family of
edits, and questions about a threat model ("which way can this feature move under *any* edit the attacker may make?")
are questions about operations, not single edits.

**Definition 7 (operation, threat model).** An *operation* $o$ is a family of transformations $T_{o,\theta}$, indexed by
a parameter $\theta$ from a domain $\Theta_o(z)$ that may depend on the input: "any section name of at most 8 bytes",
"any content of at most $B$ bytes", "any delay that keeps the packet in its flow". A *threat model* $\mathcal{M} = (O,
\mathrm{Pre})$ is a finite catalogue of operations $O$, together with a *precondition* $\mathrm{Pre} \subseteq Z$: the
inputs the catalogue applies to. The attacker's transformations $\mathcal{T}$ are the finite sequences of operation
instances, and $\mathrm{Reach}_\mathcal{M}(z)$ is the set of inputs they produce from $z$. The precondition is *closed*
under $\mathcal{M}$ if no operation takes an input in $\mathrm{Pre}$ outside it.

**Definition 8 (item signature).** The *item signature* $\Sigma_o$ of an operation lists, for each item kind, whether
the operation can add, remove, or modify items of that kind, and the range of contributions the added or modified
items can have. For example, "transplant a code fragment from this benign app" adds the fragment's API call sites and
string constants, and possibly the permission declarations they need, and removes nothing. "Inject a forward packet"
adds one packet of any length up to the path's maximum, and replaces one consecutive pair by two.

An operation stated in items comes with its signature: the tool that performs it says what it adds. An operation
stated in elements does not, and its signature must be derived from what it writes (Section 6.2).

The threat model is an input to the model, not an output. Whether an operation preserves the malware's behavior or
looks plausible is a property of the operation, as Pierazzi et al.'s constraints on semantics and plausibility are.
What the model computes is the operation's consequence in feature space.

### 4.4 How much the model can say about one edit

The written set and the locating positions together decide how much the model can say about a single edit.

**Definition 9 (edit classes).**
- A *content edit* writes no locating position and creates or destroys no item: it only changes the content of
  existing items. Examples: overwriting bytes inside a section's slack that form no new string; padding a packet.
- An *item-creating edit* writes no locating position but creates or destroys scanned items: new bytes, new strings,
  two strings merged into one. Example: appending to the overlay.
- A *declared structural edit* writes a locating position, or shifts elements, and states its resulting delta.
  Examples: adding a section, which writes the section count and a new table entry and states "one section added,
  with this name, offset, and size"; injecting a packet, which states where it goes.
- An *undeclared structural edit* writes a locating position and does not state its delta. Examples: overwriting a
  section's offset field; changing a packet's destination port, which moves it to another flow; repacking the whole
  file. The model *flags* such an edit, along with the item kinds it may affect, and does not predict it.

Whether an edit writes a locating position follows from the item table and $W$ alone, by an interval query, without
parsing $z'$. The classification is therefore automatic, and it catches structural edits a human would miss. On a PE
file whose section table points past the end of the (truncated) file, appending writes a locating position, because
it decides whether that section's raw data now exists. Delaying a packet is a content edit only while the packet stays
within the timeout of its flow's first packet; past it, the delay splits the flow.

## 5. Predicting what one edit does to the features

Given an input and an edit, we want the edited input's features without running the extractor on it. Attacks need
this for thousands of candidate edits, and Pierazzi et al. call it infeasible to compute in advance. The recipe has two
steps. First, list the items the edit adds, removes, or changes. Second, adjust the sums by those items'
contributions, and re-apply the readouts. This section works the recipe on the three examples, shows how it can go
wrong, turns each way it can go wrong into a requirement on the extractor, and then proves that the recipe is exact
when the requirements hold.

### 5.1 The recipe on three examples

**EMBER: append a URL.** Append the 20 bytes `\0http://evil.example` to a PE file. The leading zero byte keeps the
text from joining a string that ended at the old end of the file. The edit adds 20 byte items and one string of 19
characters, and it extends the overlay. So the number of strings (`numstrings`) rises by one; the average string
length (`avlength`) has 19 added to its numerator and 1 to its denominator; the number of strings containing a URL
(`string_counts[url]`) rises by one; the 20 bytes' histogram bins rise by their counts and the bins' total by 20, from
which the file's new entropy (`general.entropy`) follows; the overlay's entropy is recomputed, and if it exceeds every
section's, so is the largest section entropy (the overlay counts as a section there). No section table entry is
touched, so the number of sections, the section-name buckets, and the number of imported libraries stay fixed. One side effect is easy to miss by hand: EMBER divides each section's size by
the file's size, so every section's size ratio falls, because the file grew.

**Drebin: transplant a gadget.** Transplant a code fragment that calls `getDeviceId` and contains the string
`http://evil.example`, and add the `READ_PHONE_STATE` permission the call needs. The edit adds an API call site, a
string constant, and a permission declaration. So the counts of the suspicious API call (`api_call::getDeviceId`), of
the calls needing `READ_PHONE_STATE`, of the network address (`url::evil.example`), and of the requested permission
(`permission::READ_PHONE_STATE`) each rise by one, and their presence bits are set. The used permission
(`used_permission::READ_PHONE_STATE`) is set too, because both of its sums are now positive; had the gadget not
brought the permission, the call alone would not set it. If the app already requested the
permission, the requested permission's count goes from 1 to 2 and its bit stays set: the recipe gets this right because it counts first and
reads out presence afterwards. The used-permission bit is the kind of side effect Pierazzi et al. observed by
re-extraction.

**CICFlowMeter: inject a packet.** Inject a forward packet of length $m$ between two packets of a flow, $\Delta_1$
after the first and $\Delta_2$ before the second. The edit adds one packet, removes the consecutive pair with gap
$\Delta_1 + \Delta_2$, and adds two pairs with gaps $\Delta_1$ and $\Delta_2$. So the forward packet count (`Total Fwd Packets`)
rises by one, the total forward length (`Total Length of Fwd Packets`) by $m$, and the total of squared lengths by
$m^2$, from which the mean and standard deviation of forward lengths (`Fwd Packet Length Mean`, `Fwd Packet Length
Std`) follow; the longest and shortest forward packet (`Fwd Packet Length Max`, `Min`) become $\max(\cdot, m)$ and
$\min(\cdot, m)$. The total gap is unchanged while the number of gaps rises by one, so the mean gap (`Flow IAT Mean`)
falls. The duration is unchanged while the bytes rise, so the bytes per second (`Flow Bytes/s`) rise. The longest gap
(`Flow IAT Max`) needs more care: if the removed pair held it,
the new largest gap is the largest of the *other* gaps, which the item table lists and the old maximum does not reveal.

### 5.2 How the recipe can go wrong, and what we require

The recipe is right only if both steps are. The first step goes wrong if the edit changes items we did not list; the
second, if an item's contribution is not what the item table says. Each way this can happen gives one requirement.
They are stated per item kind, because a real extractor may satisfy them for some kinds and not others.

**The record must match the extractor.** If the instrumented extractor's readouts, applied to its recorded sums,
disagree with the original extractor on even one feature, every prediction built on the record inherits the error.

> **Requirement 1 (faithful recording; formerly A0).** $\varphi$ is a sum-then-readout extractor over the modeled
> features $J$ (Definition 4): for every input, the readouts applied to the recorded sums reproduce the extractor's
> output exactly.

**An item's contribution must depend on the item alone.** Step 2 adds and subtracts recorded contributions. That is
only right if an item contributes the same amount whatever else the input contains. EMBER violates this in three ways
as written, and each is a pattern that recurs in other extractors. It appears in Pierazzi et al.'s list of what makes
side effects hard ("name deduplication, class declarations, resource name normalization"):
- *A global total inside a contribution.* EMBER divides each section's size by the file's size, so a section's
  contribution would depend on the file's length: appending changes it although the section is untouched. The repair
  is to let the section contribute its size and move the division into the readout, where the file's length is itself
  a sum. CICFlowMeter is already written this way: a packet contributes its length, and the mean is a readout.
- *Deduplication.* EMBER counts each library once. If it kept the set of library names, adding an import from a
  library already present would change nothing, though the recipe would add one. The repair is to keep a count per
  name and read out the number of names with a positive count. Drebin's presence bits are exactly this.
- *Overwriting.* EMBER's import parsing stores each library's functions under the library's name, so a second import
  descriptor for the same library replaces the first one's functions. The first descriptor's contribution then
  depends on whether a second exists. This cannot be repaired inside the model. It is a genuine non-local effect, and
  it is either flagged or, as we did, patched in the extractor (Section 9).

> **Requirement 2 (self-contained contributions; formerly A2).** An item's contribution depends only on its kind and
> its content, not on the rest of the input. Equivalently (Section 3.2), the sum vector is the fold of $\mathbf{v}$
> over the items.

**The edit must not silently change the parse.** If an edit overwrites a field that says where things are, such as a
section's offset in the table, the parser sees different sections afterwards, and the recipe, which only looked at
items whose content was written, misses them. The same happens when a packet's destination port is changed, which
moves it to another flow. The recipe can only notice this if the item table records *every* position the parser
consults to decide what exists and where.

> **Requirement 3 (complete record of structure; formerly A1).** If an in-place edit writes no recorded locating
> position, then every parsed item is still there afterwards, with the same identity, members, and locating
> positions, and no parsed item appears. Only content may differ, with one exception: an *end-anchored* item, whose
> members the parser defines as running to the end of the input, gains or loses the positions added or removed at the
> end.

End-anchored items exist because appending is the most common edit of all. The overlay of a PE file is everything
after the last section, so appending lengthens it; trailing data after the last structure of any container behaves the
same way. Treating the end of the input as a locating position instead would make every append structural, and the
model could say nothing about it. Where the parser reads structure *from* the end, as a ZIP archive's central directory
is, appending does move a locating position and the edit is structural.

A missed locating position is found by changing single elements and checking whether the parse changes although the
element is not recorded as locating. For CICFlowMeter, the requirement holds if each packet's addresses, ports,
protocol, FIN flag, and timestamp are recorded as locating, since the timestamp decides, through the timeout, whether
the packet starts a new flow.

**New content must only affect items near where it is written.** Scanned items can change around an edit: appended
text joins a string that ended at the old end of the file, an overwrite splits one string into two, an injected
packet replaces one consecutive pair by two. The recipe can find these only if they stay within a known distance of
the written positions, and if the recognizer can find them by looking there alone.

> **Requirement 4 (changes stay near the edit; formerly A3).** Each scanned kind $\kappa$ has a *margin*
> $\mu_\kappa(z, W)$, a set of positions around the written set computable from $z$ and $W$, such that after an edit
> that writes no locating position: (i) the items whose members lie outside the margin are unchanged; (ii) no item
> appears outside the margin; (iii) the items overlapping the margin can be found by running the kind's recognizer on
> the margin alone.

The margin of a printable string reaches to the nearest non-printable byte on each side, since a run's extent depends
only on its neighbors. Windows of $n$ elements have a margin of $n - 1$ elements on each side, and single bytes have
none. A consecutive packet pair has a margin of one packet on each side. These are the "damage region" conditions on
which incremental parsers and lexers rely (Wagner and Graham).

**The editing tool must do what it declares.** When an operation is stated in items, the recipe takes the tool's word
for what it added. A tool that rebuilds the whole input can change items it was never asked to change. LIEF, a common
library for editing executables, rewrites a PE file's layout when it adds a section; a repackaging tool may reorder an
app's code.

> **Requirement 5 (honest tools; formerly A4).** Every edit an operation produces has an item delta within the
> operation's signature, and a declared structural edit produces exactly the delta it declares and changes scanned
> items only within the range it declares.

Requirements 1, 2, and 5 are needed whatever the edit. Requirements 3 and 4 are needed only when an edit is stated in
elements, because only then must the model work out for itself which items changed. A threat model stated entirely in
items, as most Drebin attacks are, needs neither. Section 8 returns to what this means for the model's generality.

### 5.3 The guarantee

With the requirements in place, both steps of the recipe can be carried out exactly. Step 1 is a lemma, step 2 the
theorem.

**Lemma 1 (step 1: the changed items can be found locally).** Let an edit be a content, item-creating, or declared
structural edit (Definition 9), and let Requirements 3-5 hold. Then its item delta can be computed from the item table
of $z$, the written set $W$, and the elements of $z'$ inside the margins (or, for a declared edit, inside the range it
declares).

*Proof.* For an edit that writes no locating position, Requirement 3 says every parsed item survives with the same
identity and members, except that an end-anchored item's members gain or lose positions at the end, and those
positions lie in $W$ (Definition 5). A parsed item whose members avoid $W$ is unchanged, since $z'$ equals $z$ outside
$W$. A parsed item whose members meet $W$ gets its new content from $z'$, and goes into $I^\sim$ if the content
differs. For each
scanned kind, Requirement 4 (parts i and ii) says the items outside the margin are the same in $z$ and $z'$. The items
of $z$ that overlap the margin are read from the item table, and the items of $z'$ that overlap it are found by the
recognizer (part iii). Comparing them by identity gives that kind's part of the delta. For a declared edit,
Requirement 5 says the declared delta is the parsed part, and the scanned kinds are handled as above, with the
declared range in place of the margin. ∎

**Theorem 1 (step 2: exact side effects; C1).** Let an edit take $z$ to $z'$ with item delta $\Delta = (I^-, I^+,
I^\sim, I^\to)$, and let Requirements 1 and 2 hold. Write $\iota$ and $\iota'$ for an item before and after a
modification.
1. Every additive sum $s$ changes by what the added items contribute, minus what the removed ones contributed, plus the
   change in each modified item's contribution:
   $$\mathbf{s}(z')_s = \mathbf{s}(z)_s + \sum_{\iota \in I^+} \mathbf{v}(\iota)_s - \sum_{\iota \in I^-}
   \mathbf{v}(\iota)_s + \sum_{\iota \in I^\sim} \big(\mathbf{v}(\iota')_s - \mathbf{v}(\iota)_s\big).$$
   Moved items change nothing.
2. A pool's new value can be computed from the item table of $z$ and $\Delta$, but in general *not* from its old value
   and $\Delta$ alone.
3. Every modeled feature follows: $\varphi_j(z') = \rho_j(\mathbf{s}(z'))$ for $j \in J$. So the side-effect vector of
   an edit aimed at the feature change $\delta^*$, $\eta = \varphi(z') - \varphi(z) - \delta^*$, is exact on $J$.

*Proof.*
1. A sum over a set splits over any partition of the set. The unchanged items of $z'$ are the unchanged items of $z$,
   with the same content, and so, by Requirement 2, the same contributions. A moved item keeps its content, hence its
   contribution.
2. The pool's value over $z'$ is the maximum over the unchanged items, which the item table lists, and the added and
   modified ones. For the second half, take two inputs whose pools hold $\{5, 3\}$ and $\{5, 5\}$. Both pools have
   value 5. Removing an item of value 5 leaves 3 in the first and 5 in the second, so the old value alone does not
   determine the new one. (Section 3.2: $\max$ has no inverse.)
3. By Requirement 1. ∎

Together, Lemma 1 and Theorem 1 cover every edit except undeclared structural ones, which are flagged. The longest-gap
case in Section 5.1 is part 2 at work. Incremental view maintenance in databases knows the same fact: a maximum needs
auxiliary state to survive deletions.

**Corollary 1 (sequences of edits).** A sequence of edits whose deltas are each known (by Lemma 1, applied to the
input each edit is applied to) has exact side effects: apply Theorem 1 once per edit, carrying the item table forward.

### 5.4 Checking the requirements on a real extractor

On a real extractor the requirements are checked against re-extraction rather than proved. Faithful recording is
checked by comparing the readouts with the extractor's output on every input. The complete record of structure is
checked by changing single elements. Changes staying near the edit is checked by random local writes. Self-contained
contributions and honest tools are checked by applying every operation and comparing the predicted features with the
re-extracted ones. The results are therefore *validated* for an instance, not proved.

The weak spot is a failure that only an attacker's choice of parameters triggers, which a check on natural inputs
cannot see. EMBER's import overwrite is an example: natural files almost never import from the same library twice in
separate descriptors. Checks therefore apply operations with adversarial parameters (repeated names, colliding names,
content placed next to existing strings). They remain tests.

What keeps the results sound when a check misses something, or a requirement is known to fail, is *flagging*. An
undeclared structural edit, a scanned kind without a recognizer, or an item known to violate Requirement 2 is flagged.
Theorem 1 makes no prediction for it, and the direction theorem of Section 6 counts it as "both" on every feature it
can reach. Flagging costs precision, never soundness.

## 6. Predicting which way each feature can move

A detector that is meant to be robust needs to know, for every feature, whether the attacker can raise it, lower it,
both, or neither, on every input it will face, not only on the inputs we tried. Section 5 answers for one concrete
edit; this section answers for all edits of a threat model at once. Sometimes the answer is obvious: if a Drebin
attacker can only add declarations and code, no Drebin feature can go down. Usually it is not. If a traffic attacker
can inject packets, the forward packet count can only rise, but the mean forward length can move either way, the mean
gap can only fall if packets go between existing ones and can rise if they go after the last one, and `Flow Bytes/s`
can rise, or fall if the injection stretches the flow's duration. For 2,500 EMBER features, nobody can work this out by
hand reliably; Section 9 shows that a careful attempt got some features wrong.

The answer comes in two steps:
1. *Sums.* From each operation's signature and the contribution vocabulary, find the signs each sum's change can have.
   This needs no input.
2. *Features.* A fixed rule per readout type turns the signs of the sums into the direction of the feature.

### 6.1 Signs, envelopes, and directions

**Definition 10 (sign sets).** $\mathrm{sgn}(x)$ is $-$, $0$, or $+$. A *sign set* is a subset of $\{-, 0, +\}$, and
$-A$ flips each sign in $A$. The *sign sum* $A \boxplus B$ is the set of signs $x + y$ can have when $x$ has a sign in
$A$ and $y$ a sign in $B$. For example, $\{+\} \boxplus \{0\} = \{+\}$, but $\{+\} \boxplus \{-\} = \{-, 0, +\}$, since a
positive and a negative number can sum to anything.

**Definition 11 (envelope).** Let $F$ be a population of inputs. The *envelope* $E^F_o(s)$ of operation $o$ on sum $s$
is the set of signs the change of $s$ takes, over every input $z \in F$ and every edit of $o$ on it. In words: can
this operation raise this sum, lower it, or leave it? We drop $F$ and $o$ from the notation when they are clear.

**Definition 12 (direction table).** A *direction table* gives each feature $j$ a direction $D_j$: $\mathsf{fixed}$,
$\mathsf{up}$, $\mathsf{down}$, or $\mathsf{both}$. It is *sound for $\mathcal{M}$ over $F$* if, for every input in $F$
and every single operation instance of $\mathcal{M}$, feature $j$ does not change when $D_j$ is fixed, does not fall
when it is up, and does not rise when it is down.

These four directions are Incer et al.'s four cases. Incer et al. assign them by hand, and Gimenez et al. derive them
from the feature changes of observed attacks.

### 6.2 Step 1: the signs of the sums

An operation stated in items comes with its signature (Definition 8). An operation stated in elements does not, and
the first job is to derive one: which items can appending bytes, or padding a packet, change at all?

**Lemma 2 (signatures of operations stated in elements).** Let $o$ be an operation stated in elements, and suppose
that on every input in a population $F$ and for every parameter value, its edit is in place and writes no locating
position. Under Requirements 3 and 4, every edit of $o$ on $F$ modifies only parsed items whose members it writes, and
adds or removes only scanned items that overlap the margins of its written set. Its signature contains these changes
and no others.

*Proof.* By Requirement 3, no parsed item is added, removed, or moved, and a parsed item whose members avoid $W$ keeps
its content. By Requirement 4, parts i and ii, no scanned item changes outside the margins. ∎

The lemma's condition must hold on every input in $F$, not only on those seen. Appending writes no locating position on
most PE files, but on a file whose section table points past its end it does. Such inputs must be excluded from $F$ by
the precondition, or the operation treated as structural on them.

Lemma 2 gives a signature per input: which parsed items an edit's written set meets, and which scanned items lie near
it, are read from that input's item table. No edit is applied and nothing is re-extracted, but the result depends on
the input's layout. An operation's signature over a population is the union of these per-input signatures, and it holds
for the layouts the population contains. An operation stated in items has the same signature on every input. This is
the one place where a direction table depends on the corpus it was computed over (Section 6.4).

With signatures in hand, the signs follow from the vocabulary.

**Lemma 3 (envelopes from signatures).** Under Requirements 2 and 5, the change one item makes to one of its terms
has a sign fixed by the term and by whether the item is added, removed, or modified:

| Term | Item added | Item removed | Item modified |
|---|---|---|---|
| count, keyed | $\{+\}$ | $\{-\}$ | $\{0\}$ (cancels) |
| add, bins, unsigned hashed, max pool | $\{0, +\}$ | $\{-, 0\}$ | $\{-, 0, +\}$ |
| signed hashed | in each bucket, the signs of the keys that can land there | the negation | every sign, in the old bucket and the new |
| slot | — | — | every sign, unless the operation fixes the new value |
| opaque | the sign of (value $-$ default), over the declared range | the negation | every sign |

A min pool behaves as a max pool with the signs flipped. A count that depends on the item's content, such as a string
that counts toward the URL feature only if it matches the pattern, is an add term with value 0 or 1, not a count term,
since a modification can change whether it matches. An operation's envelope on a sum is contained in the sign sum,
over all the item changes in its signature, of the entries above for the terms that write that sum. A flagged change
contributes $\{-, 0, +\}$ to every sum its kind writes.

*Proof.* By Requirements 2 and 5, an edit's effect on a sum is the sum of the term changes of the items in its delta,
each with a sign in the table by the term's declared range. The sign of a sum of numbers lies in the sign sum of their
signs. For a modified item, the count term contributes $+1 - 1 = 0$. ∎

The sign sum is the sign domain of abstract interpretation: $\mathrm{sgn}(x + y) \in \mathrm{sgn}(x) \boxplus
\mathrm{sgn}(y)$.

In the examples: transplanting a gadget gives $\{0, +\}$ on every Drebin count (an item is added, or nothing is).
Injecting a forward packet gives $\{+\}$ on the forward count, $\{0, +\}$ on the total length and total of squares, and
$\{0, +\}$ on the max pool and $\{-, 0\}$ on the min pool of lengths. Adding a PE section gives $\{+\}$ on the number of
sections and, if the attacker picks the name, possibly both signs on the section-name buckets; which buckets
is the next lemma's question.

**Lemma 4 (which hash buckets an attacker can reach).** For a signed hashed term whose key the attacker picks from a set
$K$, the reachable (bucket, sign) pairs are exactly the hash and sign values of the keys in $K$. Enumerating part of $K$
gives witnesses, and once they cover every pair, the answer is exact.

*Proof.* Immediate from the term's definition. ∎

This answers Severi et al.'s remark that hashed features resist targeting because the hash is hard to invert. With a few
dozen buckets, a key landing in a chosen bucket with a chosen sign is found by brute force.

Lemma 3 treats a pattern feature, such as EMBER's URL count, as an add term with value 0 or 1 per string, so a
modified string can change it either way. Appending text that joins a string at the end of the file modifies that
string by extending it, and for most patterns extension can only create a match.

**Lemma 5 (pattern features under extension).** Let a feature count the strings that match a regular expression $P$.
If $P$ uses no construct that looks past the end of the match (end anchors, word boundaries after the match,
lookahead), then extending a string on the right can only add matches, never remove them. The same holds on the left
for constructs that look before the match.

*Proof.* Without such constructs, whether $P$ matches a substring depends only on that substring, which an extension
does not change. ∎

EMBER's URL pattern begins with a word boundary and has nothing after the match, so extending a string on the
right can only create a URL match, but prefixing it with a letter can destroy one (`xhttp://` has no word boundary
before the `h`). The test reads the parsed pattern; it is sound, and may call a pattern two-sided when it is not.

### 6.3 Step 2: from the sums to the features

**Lemma 6 (one rule per readout type).** Let $E_s$ be an operation's envelope on sum $s$. For every input, the change
of a feature has a sign in the set below.
- *Identity:* $E_s$.
- *Presence* (nondecreasing): within $E_s \cup \{0\}$, since a count can rise while its bit stays set. Over several
  sums (Drebin's used permissions): up if every envelope lies within $\{0, +\}$, down if every one lies within
  $\{-, 0\}$, otherwise every sign.
- *Ratio* $a/b$, with $a \ge 0$ and $b > 0$ before and after: $E_a \boxplus ((-E_b) \cup \{0\})$. In words: the ratio
  can rise only if the numerator can rise or the denominator can fall. If $b$ can reach or leave zero, add every sign,
  unless the readout's default value is declared to lie on one side.
- *Normalized vector* (a bin over the total): the ratio rule. If the operation keeps the total fixed, it is the bin's
  own envelope.
- *Entropy:* $\{0\}$ if no bin can change, otherwise every sign.
- *Max or min:* the pool's envelope.
- *Distinct count:* up if keys are only added, down if only removed, otherwise both.
- *Field transform and selection:* $\{0\}$ if nothing they read is written (for a selection: every member and locating
  position of the selected item), otherwise every sign.
- *Opaque with default:* the opaque term's entry in Lemma 3.
- *Rate* (a sum over the difference of a max pool and a min pool): the ratio rule, with the denominator's envelope
  $E_{\max} \boxplus (-E_{\min})$.
- *Standard deviation*, and any other readout type until it is given its own rule: $\{0\}$ if none of its sums can
  change, otherwise every sign.
- *Residual:* every sign.

*Proof.* Every rule except the ratio's follows from monotonicity or is trivially sound; the rate's is the ratio's with
the denominator's change bounded by the sign sum. For the ratio, write the changes as $a' = a + \alpha$ and
$b' = b + \beta$. Then
$$\frac{a'}{b'} - \frac{a}{b} = \frac{\alpha\, b - a\, \beta}{b\, b'}.$$
The denominator is positive. $\alpha b$ has the sign of $\alpha$, which lies in $E_a$. $-a\beta$ is $0$ if $a = 0$,
and otherwise has the sign opposite to $\beta$'s, which lies in $-E_b$. ∎

In the traffic example, injecting a packet *between* existing packets leaves the total gap fixed ($E_a = \{0\}$) and
raises the number of gaps ($E_b = \{+\}$), so the ratio rule says the mean gap can only fall. Allowing injection after
the last packet adds a gap to the total ($E_a = \{0, +\}$), and the mean gap becomes "both", as Section 6's opening
said.

### 6.4 The direction theorem

**Theorem 2 (the derived direction table is sound; C4).** Let $\mathcal{M}$ be a threat model and $F \subseteq
\mathrm{Pre}$ a population of inputs on which Requirements 1, 2, and 5 hold (and 3 and 4, for operations stated in
elements). Build a table $D$:
- for each operation, apply Lemma 6's rules to envelopes that contain the true ones over $F$ (for example, those of
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
1. For one operation instance on an input in $F$, each sum's change has a sign in its envelope. By Lemma 6, the
   feature's change has a sign in the rule's output, which lies in the union.
2. By induction on the length of the sequence. Closure keeps every intermediate input in $F$, so part 1 applies at
   every step, and "does not fall" is transitive.
3. Once a step leaves $F$, the envelopes say nothing about the next one. ∎

Two conditions in the theorem are easy to overlook, and both concern the threat model and the population, not the
extractor. Envelopes must hold over the population, not just over a sample: those from Lemma 3 hold for any input, but
those obtained by running an operation on a corpus hold only for the layouts the corpus contains. And part 2 needs
closure: no edit may take an input outside the precondition. Section 9 discusses both for EMBER.

## 7. From directions to detectors that cannot be evaded

Gimenez et al. prove that a detector is robust if each feature can only move one way under the attacker's edits and
the classifier's score never falls in those directions. Incer et al. build such detectors from a direction table
written by hand, and Demontis et al. harden Drebin classifiers along the same lines. Theorem 2 supplies the table from
the extractor, and a classifier trained with monotone constraints supplies the rest.

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

**Remark (routing to a fallback detector).** A practical detector scores inputs in $\mathrm{Pre}$ with the
constrained model and all other inputs with an unconstrained fallback. Theorem 3, with $F = \mathrm{Pre}$, protects it
exactly when $\mathrm{Pre}$ is closed under $\mathcal{M}$: an operation that takes an input in $\mathrm{Pre}$ outside it
hands the attacker the fallback, which has no guarantee. Closure is therefore part of the threat model, not a detail.

**What is ours and what is not.** The route from monotone features to robustness is Gimenez et al.'s and Incer et
al.'s. The guarantee rests on four things together: the direction table, the classifier's constraints, the
precondition's closure, and the requirements on the population. What Theorem 2 adds is the table: computed from the
extractor, sound, and covering every feature, which hand analysis cannot do for thousands of features.

## 8. How general is the model?

Pierazzi et al.'s formalization assumes nothing about $\varphi$. That is its strength, and also why it cannot compute
anything: with the extractor a black box, side effects can only be observed. Our model gives up some of that
generality in exchange for computation. This section states where the trade lands.

**What each result needs.**

| Result | Needs | Depends on the input format? |
|---|---|---|
| Side effects of an edit stated in items (Theorem 1) | faithful recording, self-contained contributions, honest tools | no |
| Side effects of an edit stated in elements (Theorem 1 with Lemma 1) | all five requirements | through Requirements 3 and 4 |
| Directions (Theorem 2) | as above, per operation, with envelopes over the population | only for operations stated in elements |
| Robustness (Theorem 3) | Theorem 2, closure of the precondition, a monotone classifier | as Theorem 2 |

So the format enters at one place: working out which items an edit stated in raw elements changes. That is a fact
about the format's parser ("which positions decide where things are"), and Requirements 3 and 4 are the general
conditions under which it can be worked out locally, the same conditions incremental parsers rely on. Formats with
pointers and tables, like PE, have many locating positions and many structural edits, so recording them is most of the
instrumentation effort. Streams, like packet traces, have few: most kinds are scanned and margins are small, though
timeouts make timestamps locating. A threat model stated entirely in items, as most Drebin attacks are, needs neither
requirement, and the model is then as format-free as its other three: faithful recording, contributions that depend
only on the item, and tools that do what they declare. Format-free describes the conditions, not the work: building the
faithful record still means instrumenting the extractor's parser, which is written once per format (see "The price"
below).

**Which extractors fit.** Those built by counting and aggregating over recognized pieces, which covers most static
malware feature sets and flow statistics: EMBER and its descendants, Drebin and its variants, PDF structural paths,
byte and opcode n-grams, string-based features, and CICFlowMeter-style flow features. For these, contributions usually
depend only on the item by construction, since each piece is counted where it is found. The exceptions are the three
patterns of Section 5.2, and two of them are repaired by moving work into the readout. Readouts must be algebraic
aggregates (Section 3.3): a median or a quantile has no bounded summary and does not fit.

**The price.** The model says what must be recorded; it does not make recording it free. Recording an extractor's
items, sums, and readouts is engineering done once per extractor, not once per question. On EMBER it took several
rounds of single-byte checks to find every place the PE parser looks (Section 9).

**What does not fit.**
- *Global analyses* such as call-graph centralities or data-flow summaries: a piece's contribution depends on the whole
  program, so contributions are never self-contained, and the model degrades to flagging.
- *Learned representations:* the features of a neural network over raw bytes have no item layer, so recording cannot
  be faithful.
- *Edits and features in different element spaces:* dynamic features from execution traces, when the attacker edits the
  binary. A byte edit does not map to trace positions without a model of execution.
- *Time-decayed statistics,* as in Kitsune's packet features: a packet's contribution depends on the time since it
  arrived, which the next packet changes. Contributions are self-contained only after re-encoding the decay into the
  readout, if at all.
- *Whole-input rewrites:* packing and encryption are undeclared structural edits by nature. They are flagged, never
  predicted.

**Where each domain stands.** The EMBER instance is built and checked (Section 9). Drebin and CICFlowMeter are, so
far, examples on paper. For Drebin, the items are manifest declarations and bytecode call sites and strings, every
contribution is a keyed count, and the requirements are close to trivial; its value is the side-effect computation for
code transplantation, which Pierazzi et al. obtain by re-extraction. For CICFlowMeter, the items are packets,
consecutive pairs, and flows, the readouts include two types beyond EMBER's, and the hand-written constraints of the
botnet literature are the alternative to compare against. CICFlowMeter has documented feature-extraction errors
(Engelen et al.); by our rule on extractor quirks, an instance would use the corrected tool.

**The claim we can defend.** For the class of extractors that dominate static malware detection and flow-based
traffic detection, the feature-space consequences of a threat model can be computed from the instrumented extractor,
under requirements that can be checked per item kind; the format matters only for edits stated in raw elements. The
claim is argued here for three domains and shown, so far, on one.

## 9. The EMBER instance

This section collects the PE- and EMBER-specific facts that the model abstracts away, with each requirement's old
label, since the checks and runs are recorded under those labels.

**Kinds.** `byte`, `window` (byte-entropy windows of 2,048 bytes at multiples of 1,024), and `string` are scanned. The
Rich header is also scanned, within a search range. `section`, `overlay`, `field`, `import`, `library`, `export`,
`certificate_table`, and `entry` (the entry section, as a selection) are parsed. The residual is the PE parser's 88
warning flags and `is_pe`.

**Operations.** Appending, writing section slack, the DOS header, loader-ignored header fields, and the checksum are
stated in elements; their signatures come from Lemma 2, per file, and hold for the layouts the corpus contains (see the
population caveat below). Adding a section, adding imports, and the other catalogue operations are
stated in items and declare their deltas (`catalogue.py`). All are written by our own byte-level edits, never by LIEF,
so that tools are honest by construction.

**Locating positions (Requirement 3, A1).** For each kind, the header fields and table bytes pefile reads. Kind-level
positions include `NumberOfSections` and the bounds of the Rich header's search range. The overlay's start is decided
by every section's and directory's extent. Positions past the end of the file are recorded too, for sections whose raw
data a truncated file no longer contains. On such a file appending is structural, and the engine flags it. This is
exactly the case the former hand rules missed.

**Margins (Requirement 4, A3).**
- Strings: to the nearest non-printable byte on each side.
- Windows: the windows overlapping the write, plus, under appending, the last (window $-$ step) bytes before the old
  end. A file shorter than one window is a single window, so its margin is the whole file.
- Rich header: its whole search range.

**Repairs for self-contained contributions (Requirement 2, A2).**
- Section size ratios divide by the file length: the section contributes its raw size, and the readout divides.
- The library set: keyed counts with a distinct-count readout.
- A repeated DLL name in a second import descriptor overwrites the first one's functions: patched as a pure addition
  (`ImportsInfoMerged`), noted in `docs/upstream-issues.md`.

**EMBER details of general rules.** EMBER's minimum section entropy and minimum size ratios are minimum pools that
start at 0 over nonnegative attributes, so they are constant ($\{0\}$). Three-letter section names already reach all
100 (bucket, sign) pairs of the 50 signed section-name buckets (Lemma 4).

**Checks and results.**

| Requirement or result | Check | Result | Run |
|---|---|---|---|
| Faithful recording (A0) | G1: readouts over the item table vs `feature_vector` | bit-exact on 100 and 2,000 files, all 2,480 modeled features, both import variants; re-encoded groups too | 90, 102, 104 |
| (projection) | G2: items spread over members vs today's provenance matrix | equal | 90 |
| Complete record of structure (A1) | G5: single-byte flips across headers and directory data | 55 failing pairs from three pefile rules in round 1; 0 failures on 58,666 flips after the fix | 91, 95 |
| Changes stay near the edit (A3) | G6: random in-place writes, engine vs re-extraction | 1 failure in 1,561 in round 1; 1,560/1,560 and 1,463/1,463 after the fix | 93 |
| Honest tools, self-contained contributions (A4, A2) | G7: every operation, our own byte-level edits with adversarial parameters | direction check passes on every edit after four general rules; the precondition variant needs the plain-layout clauses | 103, 104, 107 |
| Theorem 1 | G4: engine vs re-extraction and hand predictors | append exact on 89 files, the other 11 flagged by the engine; DOS overwrite 100/100; add-section equal to the hand predictor | 92 |
| Corollary 1 | combined edits (up to 3 added sections plus an append) | 1,105/1,105 at the predicted feature vector | 111 |
| Theorem 2 | G3: derived table vs former hand rules | every disagreement was the hand rules' error, each witnessed by a real file and edit | 88, 97, 98, 101, 102 |
| Theorem 3 | Table A1: constrained detectors under toolkit, held-out, and adaptive attacks | smallest score change exactly 0.0 on files in the precondition | 99, 100, 105 |

**The population caveat.** The in-place header operations get their signatures per file from its item table (Lemma 2), and their
envelopes as the union over the corpus (`catalogue.file_region_changes`). On the 100 pilot files, header overwrites never reached section
entropy. On the 2,000-file set they did, on 4 files whose `.bss` section has `PointerToRawData` 0, so its "raw data" is
the header (run 102). The precondition's plain-layout clause ("headers hold only headers") excludes that layout.
Whether it excludes every such layout is open.

**The closure caveat.** The precondition is checked on the original file only (`catalogue_checks.py`,
`a1_evaluate.py`). Theorem 3 and the routing remark of Section 7 need it to hold on every edited file too.

These two caveats are small, and in the paper they belong in an appendix (user, 2026-11-02). Two cheap checks would
settle them (not run; each takes minutes at pilot scale):
- **P1 (closure).** Evaluate the precondition on every edited file G7 already writes, and count the edits that take a
  passing file to a failing one. *Hypothesis:* none do. Appending only shrinks what lies past the end; the declared
  operations update `SizeOfImage`, keep headers holding only headers, and keep pefile's overlay starting at a section's
  end. A failure would mean an operation's declaration or the precondition must change.
- **P2 (envelope stability).** Derive the in-place envelopes on 100 and on 2,000 files, and compare them on files that
  pass the precondition. *Hypothesis:* they are equal there. Equality is evidence for the population condition, not
  proof; a difference inside the precondition is a soundness gap.

## 10. Still to write

- **Coupling (C2):** which features move together under an operation (a corollary of Theorem 1), and which can never be
  moved separately, decided by the cone of the operations' change vectors or by a shared denominator. Severi et al.'s
  example: the number of sections and the number of writable sections. CICFlowMeter's mean, total, and count of
  forward lengths are another.
- **The reachable region (C3):** a sound region containing $\mathrm{Reach}(z)$, as verified training needs. It covers
  the cone of added contributions; the images of that cone under each readout (the mediant bound for ratios, the exact
  histogram polytope, the entropy interval); and boundary effects between added chunks. Check: run 111.
- **The provenance matrix as a projection:** today's matrix spreads each item's contribution over its members, which
  records membership but not location. For additive features, the item weights are Shapley values. Check: G2.
- **Tightness:** when every direction the table allows is realized by some edit, and what flagging costs.
- **Cost:** an update costs work proportional to the delta and the margins, not to the input.
- **Positioning:** Pierazzi et al.; incremental view maintenance (deletion and the max aggregate) and incremental
  parsing; Gray et al.'s distributive, algebraic, and holistic aggregates; abstract interpretation (sign, interval, and
  polyhedral domains); taint tracking and Cheney et al.'s dependency provenance; Treant and Chen et al. (CCS 2021) as
  consumers of the output; Demontis et al.'s secure Drebin classifiers; the hand-written feature constraints of the
  traffic literature (FENCE, Simonetto et al., Dyrmishi et al.) as what Theorem 2 replaces.
- **Verified (2026-11-02, from the papers and the CICFlowMeter source):** Drebin lists `getDeviceId` among its
  suspicious API calls; used permissions are permissions both requested and needed by a call, via Felt et al.'s map.
  CICFlowMeter's length statistics count payload bytes (headers are separate features); `Flow Bytes/s` is the payload
  of both directions over the duration; a flow times out 120 s after its *first* packet; a reset ends a flow, and a FIN
  ends it only once both sides have sent one (the code's check reads the backward FIN count twice, a likely bug).
  The 360 constraints (326 linear, 34 non-linear) are Simonetto et al.'s, for Chernikova and Oprea's 756 features.
  Pierazzi et al. write that consolidation operations "cannot be feasibly computed in advance for each possible
  object", and that it is "generally infeasible or impossible to compute the exact impact of side-effect features on
  the objective function in advance", because $\Gamma$ has no closed form.

### 10.1 Sharper tests for one input (written; for the reachable region)

The rules of Lemma 6 hold over every input, which a detector needs (Section 7). For one fixed input they can be
sharpened, which an attack, a per-input analysis, or the reachable region can use: "can this file's entropy be raised by appending?"

**Lemma 7 (sharper tests for one input).** Fix an input $z$ and an operation.
1. *Ratio.* $a/b$ can rise iff some parameter value makes $\alpha b - a \beta$ positive. When the operation adds items,
   each with its own numerator part and positive denominator part, this happens iff some item's own ratio exceeds the
   current ratio $a/b$ (the mediant property). Appending a string raises EMBER's average string length iff the new
   string is longer than the current average; injecting a packet raises the mean forward length iff the packet is
   longer than the current mean.
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
1. By the identity in Lemma 6's proof. For added items, $\alpha b - a \beta = \sum_\iota n_\iota \beta_\iota b
   (\alpha_\iota / \beta_\iota - a/b)$, where $n_\iota$ counts the added copies of item $\iota$. This is positive for
   some choice of the $n_\iota$ iff some term is positive.
2. The first-order bound for a concave function, with $\partial H / \partial p_i = -(\log p_i + 1)$; the $+1$ terms
   cancel because both vectors sum to 1. An append gives $p' - p = t(q - p)$ for some $t \in (0, 1]$, and
   $\sum_i (q_i - p_i)\log p_i \ge 0$ rearranges to the cross-entropy condition.
3. The minimum principle for concave functions. ∎
