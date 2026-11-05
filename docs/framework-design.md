# Section 3 (framework): structural design (2026-11-05)

Status: **proposal, for the user's review.** It replaces the structure of `docs/framework-spine.md` from §3.1 on
(that file stays as a record). Nothing here changes a result the experiments rest on: every theorem is the same
mathematics, restated so that it needs fewer concepts. The user's review of 2026-11-05 is in `docs/writing-spec.md`
(reaction log); its points are answered inline with "(review: ...)".

Order of work after approval: this design -> a per-paragraph spine, one subsection at a time -> prose, one subsection
at a time, reviewed before the next.

## 1. Diagnosis: why the second half failed

The draft's §3.2 introduced about twelve concepts before its one result, and most of them were not mathematics but
descriptions of how a parser behaves: an item's *identity* ("how the extractor reaches it"), *locating positions*
("the positions that decide whether an item exists"), *recognizers*, *end-anchored items*, four *edit classes*,
*honest tools*. None of these is defined in terms of anything else, so each needed a paragraph of informal glossing,
and the glossing was where the text fell apart. Three of them do no work:

- **Identity is not used by the implementation.** `items.py` has no identity field. An edit is a list of removed
  items and a list of added items (`ItemTable.replace`), and a modified item is simply one of each. The draft's
  "same item iff same kind and identity" existed only to define *modified* and *moved*, and neither is needed (below).
- **The four edit classes** only restate the hypothesis of Lemma 1 (an edit writes no locating position, or comes
  with its delta).
- **Honest tools (R3)** is not a property of the mathematics. It says the bytes an editing routine writes produce
  the delta the routine claims. That is a fact about our implementation, which §5 checks against re-extraction
  (catalogue_checks, G7), and it does not belong among the requirements.

The other cause was ordering. The text built machinery for "finding the item delta without re-extraction" before
saying why anyone would avoid re-extraction. For a single edit, re-extracting is cheap and is our ground truth.
The real reasons were never stated (§3 below).

## 2. The organizing idea: the extractor is a composition of three maps

The whole section can hang on one equation. A sum-then-readout extractor factors as

    φ_J  =  ρ  ∘  s  ∘  𝓘
    Z  --𝓘-->  finite multisets of items  --s-->  𝕄 (sums)  --ρ-->  ℝ^J (features)

- `𝓘` (the **item map**) finds the items of an object. This is the only map that knows the input format.
- `s` (the **fold**) adds up each item's contribution: a monoid homomorphism, so it does not care about order.
- `ρ` (the **readouts**) computes each feature from a few sums.

This answers the review's "an extractor doing stuff is informal" and "connect it to a type theory": the class is
defined by a factorization of φ, not by what code does. The code's loop ("for each item, add its contribution")
becomes one sentence of intuition. The algebra is used, not decorative: the fold being a homomorphism *is*
Proposition 1, and the pools' lack of an inverse *is* its part (ii) (review: "is this analysis used later?" yes).

Each later subsection is then about one or more of the maps, and that gives the section its arc:

| Subsection | Map(s) | Question | Endpoint |
|---|---|---|---|
| 3.1 | all three | What class of feature mappings? | Def: sum-then-readout extractor |
| 3.2 | s, ρ | Given which items an edit changed, what happens to every feature? | Prop 1 (exact side effects) |
| 3.3 | 𝓘 | Which items did an edit change, when it is given as raw writes? | Lemma 1 (localization) |
| 3.4 | all three, over a threat model | Which way can each feature move under every allowed edit? | Theorem 1 (sound directions) |
| 3.5 | (the detector) | Which detectors can no allowed edit evade? | Corollary 1 |

The format enters in 3.3 only, which makes the contribution claim ("format-free; the format enters only for edits
stated in raw elements") visible in the structure. That is the main change from the draft, which interleaved 3.3's
material with 3.2 and 3.4.

## 3. Key simplifications (same mathematics, fewer concepts)

**S1. Items without identity.** An item is a kind and a set of positions, its *members*; its content is `z[M]`
(review: write content as z restricted to members). An item delta is a pair of multisets (removed, added) of
*(kind, content)* pairs:

    ⟦z'⟧ = ⟦z⟧ − I⁻ + I⁺,      where ⟦z⟧ = {{ (τ, z[M]) : (τ, M) ∈ 𝓘(z) }}

- A *modified* item is one removed and one added; their count terms cancel by arithmetic, not by definition.
- A *moved* item (same content, new position) cancels on both sides and disappears from the delta. The four-part
  delta (removed, added, modified, moved) becomes two parts.
- Any pair satisfying the equation is a valid delta (the smallest is the multiset difference). This matters: the
  localization lemma produces a non-minimal one ("remove every item near the write, add back what the rescan finds"),
  and a declared edit may list a replaced header as removed and re-added.

**S2. Self-contained contributions go into the class definition.** Contributions are per-kind functions of content,
`ν_τ(z[M])`, as part of what a sum-then-readout extractor *is*. Faithful recording (old R5) is likewise the
definition itself (`φ_j = ρ_j ∘ s ∘ 𝓘` on J). Then **Proposition 1 needs no requirements at all**: it holds for every
extractor of the class and every edit whose delta is known. EMBER's three violations become "EMBER as written is not
in the class for three feature groups; §4 rewrites them, without changing any value, so that it is."

A useful remark follows (proposed for the end of 3.1, or the discussion): **every extractor is in the class if the
items are coarse enough.** Items whose contributions depend on each other can be merged into one item; at the limit,
the whole input is one item, and the model then says no more than re-extraction does. So the class is really about
granularity: the finer the items, the more the model can say. This preempts the reviewer question "isn't everything
sum-then-readout?" and fits how the EMBER instance treats its one non-self-contained kind, the exports (`local=False`;
why it is non-local still to be confirmed in `features.py`).

**S3. One locality definition replaces locating positions, parsed/scanned kinds, recognizers, margins,
end-anchored items, (R1), and (R2).** For each kind τ, the instrumentation provides two things:

- *structure positions* `L_τ(z)`: a set of positions such that an in-place edit that writes none of them leaves the
  layout of kind τ alone outside a margin;
- a *margin* `μ_τ(z, W)` ⊇ written items: where items of kind τ may change, and within which `z'` alone determines
  them.

Definition (local kind): for every in-place edit with written set W disjoint from `L_τ(z)`, the items of kind τ of
z and z' that miss `μ_τ(z, W)` are the same, and the items of z' that meet it are determined by `z'` on the margin.

That is one definition, stated in terms already defined, with no "decide whether an item exists". Parsed and
scanned kinds become two *examples* of how L and μ look, not formal categories:

- a kind found through fields (sections): L = the fields read to find them; μ = the members of the items W meets;
- a kind found by scanning (strings as maximal printable runs): L = ∅; μ extends W to the nearest non-printable
  element on each side; windows of n elements: n − 1 on each side;
- data running to the end of the input (an overlay): its margin includes it whenever the edit appends. The
  end-anchored exception disappears into this example.

**S4. "Honest tools" is dropped from the framework.** An edit stated in items is *given with* its delta; the theory
takes the delta as part of the edit, as Pierazzi's framework takes Γ as an input. Whether our byte-level code produces
the stated delta is checked against re-extraction in §5 (it already is), and §4 says why we do not use LIEF.

**S5. Terms move to 3.4.** The term vocabulary (count, attribute, hashed, slot, opaque) exists only for the sign
rules. In 3.1 a sentence says that contributions in practice are simple (a count, a length, a hashed bucket); the
vocabulary and its sign table come in 3.4, where they are used (review: "no idea what count, attribute, etc. mean").
Same for readout forms and their sign rules.

**S6. Two lemmas become one.** The localization lemma has two readings: for a concrete edit, it computes the delta
(old Lemma 1); for an operation whose content is unknown (append *any* bytes), it bounds which kinds can change and
how (old Lemma 2, signatures from the item table). One statement, parts (a) and (b).

Requirements after S2-S4: one definition (locality), used only in 3.3. The (R1)-(R5) boxes disappear.

## 4. Motivation, stated before the machinery (the draft's missing piece)

For one concrete edit, re-extraction gives the new features, and it is our ground truth. What the factorization
gives that re-extraction does not:

1. **Attribution.** Prop 1 writes each feature's change as a sum over the items the edit changed, so every side
   effect is traced to the items that caused it. Re-extraction gives the difference, not the cause.
2. **Edits that are not applied.** A threat model's operation stands for a family of edits whose content is
   unknown ("append any 1,000 bytes"). There is no z' to extract. Because the change of every sum is a sum over the
   items in the delta, a bound on which items a family of edits can change bounds the change of every sum (3.4).
   This is the main reason, and it is why 3.2 and 3.3 exist.
3. **Cost, as a by-product.** The beam search scores thousands of candidates per file from the item table.

3.2 opens with (1) and (2) in plain words; 3.3 opens with (2) applied to edits given as raw writes, where there is
nothing to parse.

## 5. Per-subsection plan (coarse; the paragraph spine comes next, one subsection at a time)

### 3.1 Sum-then-Readout Extractors (endpoint: Definition 5)

1. The shape, with the factorization stated in words; that it covers the feature sets most used in security, and
   that they work (review: say they are common and effective; one sentence and a pointer to ¶7).
2. **Def 1 (items):** an input is a finite sequence of elements; kinds; an item is (τ, M), content `z[M]`; the item
   map `𝓘`. (Absorbs the draft's odd one-sentence "elements" paragraph.) Intuition and a generic example.
3. **Def 2 (sums):** the monoids, with max *and* min written out, and the neutral element defined before it is used
   (review). Unchanged otherwise (review: "much, much better").
4. **Def 3 (contributions and the sum vector):** `ν_τ`, a function of content per kind; `s(z)` as the fold.
   Separate from Def 2 (review: discuss; recommended). Then the one paragraph on the algebra: order-free; additive
   sums form a group, pools do not, which is why the record keeps every item (used in Prop 1 (ii)).
5. **Def 4 (readouts):** a function `ρ: 𝕄 → ℝ` that depends on a fixed finite set of sums. Framed as a class we
   identify (Gray's algebraic aggregates over distributive ones), with the common feature functions as examples
   (review: "not that we need types of readouts").
6. **Def 5 (sum-then-readout extractor):** `φ_j = ρ_j ∘ s ∘ 𝓘` for j in J; residual features explained plainly
   (features computed outside any item, such as flags a parser raises on malformed input; every result lets them
   change arbitrarily) (review: "what is residual?"); the item table defined as the record of 𝓘 and ν. The
   implementation remark goes (review). The coarsening remark (S2).
7. Prevalence across domains (the current ¶9, kept; tables may return here later).

### 3.2 Edits and Their Side Effects (endpoint: Proposition 1)

1. Smooth entry (review): an edit T takes z to z' = T(z); the standard way to learn its effect is to extract φ(z')
   and compare; what that does not give (§4 above, points 1-2). The factorization lets us ask how the features change
   as a function of how the items change.
2. **Def 6 (item delta)** in the multiset form (S1); modified and moved items in one sentence each; edits stated in
   items (add a section, add a permission, inject a packet) come with their delta. The written set is *not* here
   (review: a convenience, no spotlight); it appears in 3.3, where it is used.
3. **Prop 1 (exact side effects):** additive sums by the delta rule; pools from the item table, not from the old
   value; features by the readouts; η exact on J. No requirements. Proof idea in two sentences (the fold is a
   homomorphism; additive sums have inverses; the {5,3} vs {5,5} pool example). Incremental view maintenance cited
   here.
4. What it gives: attribution of every side effect; sequences of edits by carrying the item table forward; the
   shape "change of a sum = sum over changed items" that 3.4 builds on.

### 3.3 Edits Given as Writes (endpoint: Lemma 1, localization)

1. Motivation: some edits are given as writes ("append these bytes", "overwrite this field"), and families of them
   ("append any bytes") have no single z' to parse. We want the delta from z and the positions written.
2. Intuition before definition (review: "explain the concept before its subdivisions"): a write changes items in
   two ways. It changes the content of items whose members it writes (easy: re-read them), or it changes where
   items are (a count or offset field; a run of printable characters that grows or splits). The first is local by
   nature; the second must be bounded. The written set W is defined here.
3. **Def 7 (local kind)** (S3) with its three generic examples (fields; runs and windows; data to the end).
4. **Lemma 1 (localization):** if every kind is local and W misses every L_τ(z): (a) a delta of the edit is
   (items of z meeting the margins, items of z' meeting the margins), computable from the item table, W, and z' on
   the margins; (b) for an operation whose writes miss L on every input of a population, the deltas it can produce
   replace or create items only within the margins, read off each input's item table. Why it is true, in two
   sentences (review: "unable to understand why this is true").
5. Edits that write structure positions, or insert elements: their delta cannot be read locally. They are handled
   when given with their delta (§4's catalogue does this for every structural operation), and otherwise flagged:
   every kind whose L they write may change arbitrarily. Detecting this is an interval query, so it is automatic and
   catches cases a person would miss.

### 3.4 Sound Directions (endpoint: Theorem 1)

1. From one edit to all: what a detector and a constraint need; operations, threat model, population, closure
   (moved here in the draft already; keep).
2. **Signature** of an operation over a population: the deltas it can produce, described per kind (add, remove,
   replace, with constraints on content). Given for operations stated in items; from Lemma 1(b) for those given as
   writes.
3. Terms and their signs (moved from 3.1, S5), as a **table** (decision T below); sign sets and ⊞; **Def (envelope)**.
4. Readout forms and their sign rules, as a **table**; **Def (direction table, soundness)**.
5. **Theorem 1** and its proof idea; Incer et al.'s four cases and the sign domain of abstract interpretation cited
   where used.

### 3.5 Robust Detectors (endpoint: Corollary 1)

Unchanged in substance; the draft is acceptable here.

## 6. Notation scheme (review: "too many symbols, used inconsistently")

One convention per kind of object:

| Kind of object | Typeface | Symbols |
|---|---|---|
| spaces and sets defined per object | calligraphic | 𝒵, 𝒳, 𝒯, ℛ(z), 𝓘(z), 𝓜 |
| vectors | bold | x, δ, η, s(z), ν_τ(c) |
| maps the extractor provides | Greek | φ, ρ_j, ν_τ, μ_τ |
| finite sets of positions, items, sums, features | italic capitals | M, W, L_τ(z), I⁻, I⁺, S, J, F, O |
| monoids | blackboard | 𝕄_k, 𝕄 |
| one item, one kind | ι, τ | |

Changes from the draft:
- **kind κ -> τ** ("type"): frees κ for Pierazzi's confidence and matches the type reading of kinds (review).
  Readout "types" become readout *forms*, to avoid a second meaning of "type".
- **contribution v -> ν** (Greek, like φ and ρ: a map the extractor provides).
- **sum index s -> k** (`s_k(z)`), so `s` is only the sum vector.
- **removed:** c(ι), identity, I^∼, I^→, L(ι), L(z), the recognizer, R1-R5, E^F_o(s) vs E_s (one form).
- **added:** ⟦z⟧ (the item multiset) and L_τ(z), per kind. Net: a handful fewer, and no undefined concepts.

## 7. Decisions for the user

- **A. Adopt the factorization as the spine** (§2), with the format confined to 3.3. Recommended.
- **B. Identity-free items and two-part deltas** (S1). Recommended: matches the code, removes identity, modified,
  and moved as concepts.
- **C. Self-containment and faithfulness inside the class definition; one locality definition; "honest tools"
  removed** (S2-S4). Recommended. Consequence: §4's "(R4)" and "(R3)" references and §5's G7 wording change.
- **D. Contributions as their own definition, separate from sums** (review asked). Recommended: Def 2 is about
  algebra, Def 3 about the extractor; the coupling is one sentence ("each contribution is an element of 𝕄").
- **E. Examples (revisit D2 for §3.2-3.3).** With no example, locality is hard to picture. Options:
  (1) keep the theory example-free; (2) one small *format-neutral* toy extractor introduced in 3.1 and used in every
  subsection (a header count locating records, strings as printable runs; features: string count, average string
  length, longest string, records' share of the input's size, so appending shows a ratio side effect and a pool);
  (3) the real PE append. Recommended: (2), with the PE example in §4. It is general, avoids format minutiae, and is
  the natural content of the future Figure 1.
- **F. Term and readout tables back in 3.4** (revisit D3). Recommended: the sign rules are a lookup and read badly as
  prose; redesign them to the minimum (form, formula, sign rule).
- **G. The coarsening remark** (S2): in 3.1, or in the discussion. Recommended: 3.1, two sentences.
- **H. Type theory, how far.** Recommended: kinds as types and the fold as the homomorphism from finite multisets
  (the free commutative monoid) to 𝕄, and no further. More formal type theory adds symbols without results.

## 8. Section 2 (from the same review; smaller, prose-level)

- ¶1: add how a feature-space attack's vector is turned into an object (inverse feature mapping or a search for an
  object near it), one sentence.
- ¶2: Γ shrinks to two sentences (it is an input to our threat models; we use no part of it); ℛ(z) gets the space:
  definition, realizable evasion, and that it is the object every result in §3 describes.
- ¶3: drop "often starts from a feature-space target" (review: it is correct for many attacks, e.g. Pierazzi et
  al.'s own, which pick features by gradient and then search for transformations, but it is not needed); state side
  effects as fact with a citation; consolidation as one clause among the sources.
- ¶4: make the three viewpoints visibly three, define monotone. **The viewpoints map onto the evaluation** (review
  asked): the attacker's exact point -> Prop 1 (Table 5 checks it against re-extraction; the adaptive beam search
  uses it); constraints over features -> Theorem 1's direction table (Table 6, against hand rules); detectors ->
  Corollary 1 (Table 7). Worth saying in the introduction and in §5's lead, not in §2.
- Register: active voice, present authors ("we"), throughout.

## 9. Risks and checks before writing

- The proofs appendix must be rewritten to the new statements (same arguments, shorter).
- §4 and §5 refer to (R3), (R4), locating positions, margins, declared edits: update terms after §3 settles.
- Check that every EMBER kind fits Def 7 as stated (the Rich header's margin is its search range; entropy windows
  under appending reach the last window before the old end). The code already does this; the check is that the
  definition says what the code does.
- Selection readouts (the entry section's name) and slots: confirm both are additive sums with a single contributor,
  so they need no special case in Prop 1.
- `docs/formalization.md` stays frozen as the record; this restatement is equivalent, and the paper's appendix
  follows the new form.

## 10. The user's decisions (2026-11-05)

- **A. Adopted.** Each component of the factorization gets the same class of symbol: lowercase Greek for the maps
  (proposed: π item map, σ fold, ρ readouts, ν_τ contributions). §3.1 defines all components; later subsections use
  them and never define a component of φ.
- **B. Adopted.** No identity; modified and moved items are written as removals and additions.
- **C. Adopted provisionally**; the user judges S3/S4 from the prose. Downsides of S2 given to the user (session 15).
- **D. Adopted** (contributions a separate definition).
- **E. A toy running example, in purple** (a `\example{...}` macro) so the user sees where it is.
- **F. Tables back where necessary**, clean and tight.
- **G. The coarsening remark kept** in a boldface **Remark** environment (like the theorem environments), as a
  self-contained aside, not part of the chain of results.
- **H. Kinds as types and σ as a fold**, plus a short appendix: a crash course on the type theory used.

## 11. Spine for §3.1 (proposal, 2026-11-05)

Running example (purple): a toy container format. Byte 0 holds a count n; a table of n entries follows, each giving
the offset and length of a record; strings are maximal runs of at least four printable bytes anywhere in the input.
Features: (x1) number of strings, (x2) average string length, (x3) longest string, (x4) share of the input taken by
records. It is chosen to show, later: a side effect (appending lowers x4), a pool (x3 after a string is split), a
structure position (byte 0 and the table), a margin (strings), and directions (append: x1 up, x2 both, x3 up, x4 down).

1. **The three stages and the factorization.** φ_J = ρ ∘ σ ∘ π as a displayed chain of maps; one sentence each on
   π, σ, ρ; why separate them (an edit is simple at the items, hard at the features). Such feature sets are the
   standard ones in security and effective (one sentence; pointer to ¶9).
2. **The running example** introduced (purple).
3. **Def 1 (items).** Input z, a finite sequence of elements; z[M] the elements at positions M, in order. A finite
   set of item kinds. An item of z is a pair (τ, M) of a kind and a nonempty set of positions, its members; its
   content is z[M]. The extractor finds a set I(z) of items; the item map π(z) is the multiset of their (τ, z[M]).
   Intuition: an item is what one pass of one of the extractor's loops reads; items of a kind are processed by the
   same code, so their contents are values of one type. Example (purple): kinds header, record, string, byte.
4. **Def 2 (sums).** Finite set S of sums, each with a monoid: (ℝ, +, 0) additive; (ℝ ∪ {−∞}, max, −∞) max pool;
   (ℝ ∪ {+∞}, min, +∞) min pool; the neutral element named before it is used; 𝕄 the product, ⊕ per sum.
5. **Def 3 (contributions and the sum vector).** ν_τ: contents of kind τ -> 𝕄, neutral on the sums the kind does not
   touch; σ folds ν over a multiset; s(z) = σ(π(z)). Plain gloss: a contribution is what one item adds to the
   running totals. Example (purple): a string adds 1 to the string count, its length to the total length and to the
   longest-string pool; each byte adds 1 to the input length; a record adds its length to the total record length.
6. **The algebra, because Prop 1 uses it.** σ does not depend on order: it is the fold (the unique homomorphism from
   finite multisets to 𝕄 extending ν), so σ(A + B) = σ(A) ⊕ σ(B). Additive sums have inverses, so removing an item
   is undone by subtraction; pools do not: after the longest string is removed, the old maximum does not say what
   the second longest was, which is why the record keeps every item.
7. **Def 4 (readouts).** ρ: 𝕄 -> ℝ that depends on a fixed finite set of sums, the same for every input. Presented
   as a class: Gray's algebraic aggregates over distributive ones; holistic ones (a median) are excluded. The common
   feature functions are examples (identity, ratio, normalized histogram bin, entropy, standard deviation from a
   count, total and total of squares, presence). Example (purple): x2 and x4 are ratios, x3 reads a pool.
8. **Def 5 (sum-then-readout extractor)** over modeled features J: φ_j = ρ_j ∘ σ ∘ π for j in J. Residual
   features explained (computed outside any item, such as flags a parser raises on malformed input; every result
   lets them change arbitrarily). The item table: what an instrumented extractor records (each item's kind, members,
   contribution). That contributions depend only on content is part of the definition; an extractor that divides an
   item's size by the input's length joins the class once the division moves into a readout (§4).
   **Remark (coarsening)**: with the whole input as one item, every φ is in the class, and the model says nothing
   finer than re-extraction; the class is about granularity.
9. **Prevalence across domains** (the current ¶9, kept).

Appendix (new, ~300 words): a crash course on the type theory used. Types as sets of values; product types (𝕄);
tagged unions (an item's (τ, c) is a value of the union of the content types, and ν is defined by case analysis on
the tag); finite multisets as the free commutative monoid; a fold as the unique homomorphism out of it.

## 12. Spine for §3.2 (proposal, 2026-11-05)

Title: **Edits and Their Side Effects** (one subsection replaces the draft's "Edits as Item Deltas" and "Exact Side
Effects"). Endpoint: **Proposition 1**. It uses only §3.1's objects plus one new one, the delta; nothing about
positions, writes, or formats (those are 3.3). Budget: about 700 words (the mock's 300 for edits plus most of the old
600 for side effects, now that the requirements are gone), up to ~1,000 while drafting.

Removed from the draft's 3.2-3.3 and not replaced here: the written set, in-place vs shifting edits, "stated in
elements", identity, modified and moved items as categories, locating positions, Lemma 1, (R4), (R5), and the slots
sentence (slots go to 3.4 with the terms).

1. **Why not re-extract (motivation, no new symbols).** A transformation $T$ takes $z$ to $z' = T(z)$ (§2). For one
   edit that has been applied, extracting $\varphi(z')$ and comparing it with $\varphi(z)$ gives every feature's
   change; it is our ground truth, and §5 checks every computation of this subsection against it. It gives two things
   less: it says which features changed but not which parts of the edit changed them, and it needs $z'$, so it says
   nothing about edits that have not been applied, such as all the edits one operation of a threat model allows
   ("append any bytes"). The factorization gives both: describe the edit by how it changes $\pi(z)$, and the change of
   every sum and feature follows by arithmetic. (Families are 3.4; this paragraph only says why the arithmetic form is
   what 3.4 needs.)
2. **Def 6 (item delta).** A *delta* of a pair of inputs $(z, z')$ is a pair $(I^-, I^+)$ of multisets in
   $\mathcal{V}$ with $I^- \subseteq \pi(z)$ and
   $$\pi(z') = (\pi(z) - I^-) \uplus I^+ .$$
   Gloss: $I^-$ are the removed items, $I^+$ the added ones. A delta always exists; the smallest is
   $(\pi(z) - \pi(z'),\ \pi(z') - \pi(z))$, and every other one adds the same items to both sides. Since $\pi$ keeps
   contents and forgets positions, an item whose content changes is one removal and one addition, and an item that only
   moves is in neither. A delta need not be the smallest (a rewritten header listed as removed and re-added; 3.3's
   lemma produces such deltas), and nothing below needs it to be.
3. **Edits given with their deltas.** Many transformations in the literature are stated by the items they change:
   add a section or an import, add a permission or an API call, inject a packet. For these the delta is part of the
   statement. Others are given as writes to the input, and 3.3 derives their deltas. Example (purple): appending to a
   toy input a non-printable byte followed by $\ell \ge 4$ printable bytes has $I^- = \emptyset$ and $I^+$ = the
   $\ell + 1$ new byte items and one new string (the non-printable byte keeps it from joining a string at the old
   end; why that matters is 3.3's subject, so one clause only).
4. **Prop 1 (exact side effects).** Let $\varphi$ be a sum-then-readout extractor over $J$ and $(I^-, I^+)$ a delta
   of $(z, z')$. Then
   (i) every additive sum satisfies
   $s_k(z') = s_k(z) + \sum_{(\tau,c) \in I^+} \nu_\tau(c)_k - \sum_{(\tau,c) \in I^-} \nu_\tau(c)_k$;
   (ii) every pool satisfies $s_k(z') = \sigma\big((\pi(z) - I^-) \uplus I^+\big)_k$, which the item table of $z$
   and the delta determine, but $s_k(z)$ and the delta in general do not;
   (iii) $\varphi_j(z') = \rho_j(\mathbf{s}(z'))$ for every $j \in J$, so the side effects
   $\boldsymbol{\eta} = \varphi(z') - \varphi(z) - \boldsymbol{\delta}^*$ are exact on $J$; and $\varphi_j$ changes
   only if some item of the delta contributes a non-neutral value to a sum in its support $K_j$.
   No requirements: everything the draft required is now in Definition 5. Residual features: one clause (the
   proposition says nothing about them).
5. **Why it holds (2-3 sentences, then the citation).** Applying $\sigma$ to both sides of the delta equation and
   using \eqref{eq:fw:homomorphism}: additive sums have inverses, so the contributions of $I^-$ are subtracted, which is
   (i); pools have none ($\{5, 3\}$ and $\{5, 5\}$ both read 5; removing a 5 leaves 3 and 5), so (ii) recomputes the
   pool over the remaining contributions, which the item table lists; (iii) is Definition 5, and the "only if" part is
   Definition 4's support. Part (i) is the delta rule of incremental view maintenance, which updates an aggregate
   over a table from the inserted and deleted rows~\cite{gupta1995maintenance,koch2014dbtoaster}. Proof in Appendix C.
6. **The example, continued (purple).** The append: $x_1$ rises by 1, $x_2$ becomes $(T + \ell)/(N + 1)$, $x_3$
   becomes $\max(x_3, \ell)$, and $x_4$ falls from $R/L$ to $R/(L + \ell + 1)$ although no record was touched: a
   side effect, traced by (iii) to the new byte items through the input-length sum. The pool: overwriting a middle
   byte of the longest string with a non-printable byte has $I^-$ = {that string, the old byte} and $I^+$ = {the two
   pieces that are still strings, the new byte}; the two byte items cancel in the input length (a changed item is one
   removal and one addition), and the new $x_3$ is the longest of the other strings and the pieces, read from the item
   table, not from the old $x_3$.
7. **What it gives (short closer, literal).** Every change of a sum is attributed to the items of the delta that
   contributed it. A sequence of edits is handled one at a time by updating $\pi(z)$ with each delta (members are
   needed only in 3.3). And the change of an additive sum is a sum over the delta's contributions, so a bound on which
   items an edit can add or remove bounds the sign of every sum's change without the edit being applied: the step
   3.4 takes for a threat model's operations.

Questions for the user:

- **Q1.** Merge into one subsection titled "Edits and Their Side Effects"? Recommended (one endpoint; the delta alone
  is too small to be its own subsection).
- **Q2.** The attribution clause ("changes only if ...") inside Proposition 1, or in the prose after it? Recommended:
  inside, since ¶1 promises attribution and 3.4 uses it.
- **Q3.** The sentence "every delta is the smallest one plus the same items on both sides": keep (3.3 depends on
  non-minimal deltas being harmless) or cut? Recommended: keep, one sentence.
- **Q4.** Leave the cost benefit (the beam search scores thousands of candidates from the item table) out of 3.2,
  for §5? Recommended: out (lesson 16: nothing from the experiments in the framework).

**Decisions (user, 2026-11-05):** Q1-Q3 as recommended. Q4: a hint only, that there could be cost benefits, since
feature extraction can be expensive. The critical pass (session 15 writing, in the conversation) found mostly framing
issues, which the user judged minor at this stage; they are applied in the draft as follows: ¶1 claims for one edit
only what Prop 1 gives (no z' to build, through which items, possibly cheaper) and points to 3.4 for families; (iii)'s
clause says which features a delta can change, not attribution; an item-stated edit comes with a delta its definition
computes from z, and §5 checks our implementation's deltas; sequences are claimed only for item-stated edits (the
delta carries no positions; writes need members, 3.3); η leaves the proposition; pools under pure additions update from
the old value; the pool example's delta is stated, derived in 3.3; s_k(z) and multiset difference are defined at first
use; "edit" = one transformation applied to one input; no traffic example in ¶3 (no packet-injection attack in the
bib). §3.2 drafted 2026-11-05; the old 3.2 material (locating positions, (R1)-(R3), the lemma) stays as a placeholder
§3.3 until it is rewritten.

## 13. Spine for §3.3 (proposal, 2026-11-05)

Title: **Edits Given as Writes** (kept). Endpoint: **Lemma 1 (localization)**, parts (a) one edit, (b) an operation.
New objects: the written set $W$, in-place edits, and per kind $\tau$ the structure positions $L_\tau(z)$ and the
margin $\mu_\tau(z, W)$; nothing else. It supplies what §3.2 defers here: $W$; the members of the new items (so that
write-given edits chain); the string-split delta of §3.2's example. Budget: ~500 words (the mock's 300 for edit
classes plus the old requirements), up to ~800 while drafting. Everything in the placeholder (locating positions of an
item, parsed/scanned, recognizers, end-anchored items, (R1)-(R3), four edit classes, honest tools) goes.

1. **Why writes, and what is wanted.** Many transformations are given by the elements they write, not by items:
   append bytes, overwrite padding or an unused field, change a timestamp. For one such edit $z'$ is at hand, but its
   delta is not, and Prop 1 needs the delta; for an operation ("append any bytes up to $B$"), there is no single $z'$
   at all. We want the delta from the item table of $z$, the positions written, and the new elements near them. Define
   the *written set* $W$ (positions where $z'$ differs from $z$, with every position past the old end) and *in place*
   (no element of $z$ changes position: overwriting and appending are in place, inserting in the middle is not). This
   is the only subsection in which the input format enters.
2. **The idea, before the definition.** A write changes items in two ways. It changes the content of items whose
   members it writes; those are found from the members in the item table and re-read from $z'$. Or it changes which
   items exist and where they lie, in two ways that differ in kind: by writing an element the extractor reads to find
   items (a count, an offset, a length), after which anything may change; or by changing content that the extractor
   scans for items (printable runs that grow, split, or join), which changes items only near the write. So the first
   must be avoided and the second bounded, and the instrumentation supplies one set of positions for each.
   (Example, purple: in the toy format, byte 0 and the table entries locate the records; strings are found by
   scanning.)
3. **Def 7 (local kind).** A kind $\tau$ is *local* if the instrumentation gives for each input a set $L_\tau(z)$ of
   *structure positions*, and for each written set a *margin* $\mu_\tau(z, W) \supseteq W$, computable from the item
   table of $z$ and $W$ and growing with $W$, such that for every in-place edit whose $W$ misses $L_\tau(z)$:
   (i) $z$ and $z'$ have the same items of kind $\tau$ that are not contained in the margin (same members);
   (ii) the items of kind $\tau$ of $z'$ contained in the margin are determined by the elements of $z'$ on it.
   A kind is *fixed-layout* if, in addition, its items in $z'$ have the same members as in $z$ (the margin is then
   just $W$ plus the members of the items $W$ meets).
4. **What the definition covers (three generic shapes, then the trivial case).** A kind found through fields
   (records, sections): $L$ = the fields read to find it, fixed-layout. A kind found by scanning: maximal runs of a
   class of elements, margin = $W$ extended on each side to the nearest element of $z$ outside the class and outside
   $W$ (that element is unchanged, so no run crosses it); windows of $n$ elements, $n - 1$ on each side; these are the
   damage regions of incremental parsing~\cite{wagner1998efficient}. Data that runs to the end of the input (an
   overlay, a field cut by the end): its margin contains it whenever $W$ reaches past the old end, so appending
   rewrites it, and the old "end-anchored" exception is an instance, not a rule. Every kind is local with
   $L_\tau(z)$ = all positions, as every extractor is sum-then-readout with one item (Remark 1): the definition says
   how small $L$ can be, and a kind whose items the instrumentation cannot re-find locally puts its members in $L$.
   (Example, purple: toy $L_{\text{record}}$ = byte 0 and the table; $L_{\text{string}} = L_{\text{byte}} = \emptyset$;
   a byte's margin is $W$.)
5. **Lemma 1 (localization).** Let every kind be local. (a) If an in-place edit's $W$ misses every $L_\tau(z)$, then
   $I(z')$ is $I(z)$ with the items contained in the margins replaced by those that the elements of $z'$ on the margins
   determine; hence a delta of $(z, z')$ is (the contents of the replaced items, the contents of the new ones), and
   the item table of $z'$, members included, follows from the item table of $z$, $W$, and $z'$ on the margins. (b) If an
   operation's edits on an input $z$ are all in place and write only within a region $\hat W(z)$ that misses every
   $L_\tau(z)$, then each of its deltas removes only items of $z$ contained in $\mu_\tau(z, \hat W(z))$ and adds only
   items of kind $\tau$ contained in it, and a fixed-layout kind keeps its number of items. Both parts are read off
   the item table of $z$; no edit is applied.
6. **Why it holds, and what it means (plain words).** Outside the margins nothing the extractor reads to find items
   was written, and scanned items cannot reach across the margin's edge, so those items are the same in both inputs;
   inside, the definition says $z'$ alone decides them, so re-reading the margin finds them. The delta is not the
   smallest in general (an item inside a margin may come back unchanged), which §3.2 already allows. Part (a) is what
   gives write-given edits the members that §3.2's deltas lack, so a sequence of writes is followed by updating the
   item table. Part (b) is the bound §3.4 needs: which kinds an operation can change and how, per input, without
   knowing what it writes. Proof in Appendix C.
7. **The example, continued (purple): §3.2's two deltas derived.** Overwrite the middle byte of the longest string
   with a non-printable byte: $W$ is one position, it misses $L_{\text{record}}$; the string margin runs from the
   non-printable bytes bracketing the string; the old string and old byte are replaced by the new byte and the pieces
   of length at least four, which is the delta §3.2 stated. Append a non-printable byte and $\ell$ printable ones:
   the margin of strings starts at the last non-printable byte of $z$, so a string ending the old input is inside it
   and could have been extended; the leading non-printable byte is why it is not. Lemma (b) for "append up to $B$
   bytes": records keep their number and contents, strings and bytes can only be added, and the last string of $z$
   can be replaced (by a longer one).
8. **Edits outside the lemma.** An edit that writes a structure position, or that shifts elements, may change items
   anywhere, and its delta cannot be read near the write. It is handled when it comes with its delta (an edit stated
   in items; §4's catalogue states every structural operation this way), and otherwise flagged: the kinds whose $L$ it
   writes may change arbitrarily, which §3.4 reads as "both" for the features they reach. Whether an edit is flagged
   is an interval query of $W$ against the $L_\tau(z)$, so no person has to judge it, and it depends on the input: a
   toy file whose table points past its end makes even an append write a structure position (it can extend a record),
   which is why §3.4's directions hold over a population.

**Check against §9 (every EMBER kind fits Def 7 as the code works).** Sections, header fields, imports, data
directories: field-found, $L$ = the per-item locating ranges the code records (union per kind), fixed-layout.
Strings, URLs and other patterns over printable runs: runs. Byte histogram: per-byte, margin $W$. Byte-entropy
histogram: windows (window and step as in thrember; the margin covers every window overlapping $W$). Rich header:
its margin is its search range. Overlay and fields padded by pefile past the end: data to the end. Kinds with
`recognize_nothing`, and edits a recognizer rejects (`NotLocal`): their members go into $L$ (the trivial case), which
is exactly how the code flags them. Exports (`local=False`): not self-contained, so outside the class at item
granularity; §4 must merge them into one item (to confirm in `features.py`). Code vs definition: the code records
locating ranges per item, the definition per kind; $L_\tau(z)$ is the union, plus kind-level positions such as the
section count.

Questions for the user:

- **Q1. Fixed-layout as a named property** (needed so that §3.4 can say "append leaves the section count fixed"),
  or folded into Lemma (b) as "a kind whose margin is $W$ plus the members $W$ meets keeps its number of items"?
  Recommended: name it in Def 7, one sentence.
- **Q2. The trivial case** ("every kind is local with $L$ = everything"), as a sentence mirroring Remark 1, or a
  second Remark? Recommended: a sentence in ¶4.
- **Q3. Chaining after an item-stated edit:** a later write needs the members of the items it added, which a delta
  does not carry. State that an edit stated in items also states where its items lie (§4's catalogue does), one
  clause in ¶8? Recommended: yes.
- **Q4. Shifting edits** (insertion in the middle): only "given with delta or flagged", as above, or a line that
  shifting moves members and the lemma applies after the shift? Recommended: the former; the latter adds a concept
  for one case the catalogue already states in items.

**Decisions (user, 2026-11-05):** Q1-Q4 as recommended. Drafted the same day. One simplification while drafting:
$W$ is every position where $z$ and $z'$ differ (including positions in only one), so "in place" is not needed; an
insertion in the middle has a written set running to the end of the input (Q4 then needs no sentence). The Lemma is
stated per kind (a write that meets one kind's structure positions still localizes the others, as the code does).
Label `lem:fw:localization`; Def 7 `def:fw:local`; the proof in `_j_proofs.tex` rewritten. §3.4 still has the old
`lem:fw:signature` (now subsumed by Lemma 1(b)) and (R1)-(R5) until it is rewritten.

## 14. Spine for §3.4 (proposal, 2026-11-05)

Title: **Sound Directions** (kept). Endpoint: **Theorem 1 (sound directions)**. New objects: operations, threat model,
population and closure; an operation's *signature* (the deltas its edits can produce, per kind); sign sets and the
sign sum; envelopes; the direction table. Everything else comes from 3.1-3.3: Prop 1(i) gives the change of an
additive sum as a sum over the delta, and Lemma 1(b) gives the signatures of operations given as writes. Budget: the
mock's 500 plus the share of its 700 that went to the term and readout tables, so ~800 words and two small tables, up
to ~1,200 while drafting. Removed and not replaced: the term vocabulary as a 3.1 concept (count, attribute, hashed,
slot, opaque), `lem:fw:signature` (subsumed by Lemma 1(b)), (R1)-(R5) in the theorem, the precondition $\mathrm{Pre}$
(Q1), and $\Sigma_o$ (collides with "sum", lesson 26).

**The one simplification.** The draft's terms existed to give each kind of item change a sign. After §3.2 that is
direct: by Prop 1(i), an additive sum changes by the contributions of the added items minus those of the removed ones,
so its sign lies in the sign sum of their signs. What an operation needs per kind and sum is therefore only the set of
signs a contribution can have (and, for a replaced item, the signs of new minus old). The term forms survive as a
small table of *common contribution forms and their sign sets*, a lookup, not a concept the reader must hold.

1. **From one edit to all (motivation, then the objects).** A detector must hold against every edit the attacker may
   make, on every input it will face, and §2's $\mathcal{R}(z)$ is the set those edits reach. An *operation* $o$ is a
   family of edits $T_{o,\theta}$, $\theta \in \Theta_o(z)$ (append any content of at most $B$ elements); a *threat
   model* $\mathcal{M}$ is a finite catalogue $O$ of operations, and it fixes $\mathcal{T}$ as the finite sequences
   of their instances; whether an operation preserves behavior is $\Gamma$'s business and an input. Results hold over
   a *population* $F \subseteq \mathcal{Z}$ (§3.3 ended on why: whether an edit writes structure positions depends
   on the input); $F$ is *closed* if no operation takes an input of $F$ outside it.
2. **Signatures.** The *signature* $\Delta_o(F)$ of $o$ over $F$ describes, per kind, the changes its deltas can
   make: *add* items of the kind, *remove* them, or *replace* one by another, each with a constraint on contents
   (any; keys from a set $K$; same length; an extension of the old content). Replace is a pairing of one removal with
   one addition, kept because the pair cancels where separate signs would not: a count every item of the kind adds to
   does not move when an item is rewritten. An operation stated in items comes with its signature; one given as writes
   gets it from Lemma 1(b), per input of $F$, with every kind whose structure positions it writes on some input
   marked as changing arbitrarily (add, remove, replace, any content). No edit is applied.
3. **Signs of contributions; sign sets and the sign sum.** A *sign set* is a subset of $\{-, 0, +\}$; $-A$ flips it;
   $A \boxplus B$ is the set of signs of $a + b$ with signs from $A$ and $B$ (two examples). The sign domain of abstract
   interpretation~\cite{cousot1977abstract}, cited here. **Table (contribution forms)**, columns: form, what an item
   adds, add, replace. Rows: count (1 to a sum, or to its key's sum): $\{+\}$, $\{0\}$ if the key is kept; nonnegative
   attribute (a length, a size, histogram bins): $\{0, +\}$, any sign ($\{0, +\}$ under extension, $\{0\}$ for a length
   under same length); hashed key ($\pm$ an attribute to bucket $h(\text{key})$): the buckets and signs of the keys in
   $K$, found by enumerating $K$, which answers Severi et al.'s remark that hashing resists
   targeting~\cite{severi2021explanation}; a value in a declared range (a field one item holds, or a value computed by
   code we do not open): its range minus the neutral value. Remove is add negated (caption). A pattern count (strings
   that are URLs) gains only matches under extension if the pattern does not look past the end of a match: one
   sentence.
4. **Def 8 (envelopes and direction tables).** The *envelope* $E^F_o(k)$ of $o$ on sum $k$: the signs the change of
   $s_k$ takes over every input of $F$ and every edit of $o$. A *direction table* assigns each feature one of fixed,
   up, down, both; it is *sound* for $\mathcal{M}$ over $F$ if no operation instance on an input of $F$ changes a fixed
   feature, lowers an up one, or raises a down one. Gloss: the four directions are Incer et al.'s four cases, assigned
   there by hand~\cite{incer2018adversarially}; a sound table is a constraint in $\Omega$'s sense.
5. **Step one, sums.** An additive sum's envelope lies within the sign sum, over the changes the signature allows, of
   the signs in the table (Prop 1(i)); a max pool can only rise or stay when items are only added, fall or stay when
   they are only removed, and move either way under replacement except an extension of the attribute it reads; a min
   pool with signs flipped. No reference to the old value is needed, unlike Prop 1(ii), because only the sign is asked.
6. **Step two, features. Table (readout rules)**, columns: form, formula, sign rule. Rows: identity (a sum or a pool):
   $E_k$; presence (a count is positive): within $E_k \cup \{0\}$; distinct count (keys with positive count): up if
   every key's envelope is within $\{0,+\}$, down if within $\{-,0\}$, else both; ratio $a/b$ ($a \ge 0$, $b > 0$ before
   and after): $E_a \boxplus ((-E_b) \cup \{0\})$; normalized bin: the ratio rule with the histogram's total; any other
   readout (entropy, standard deviation, a bit of a field, the attribute of a chosen item): $\{0\}$ if every sum in its
   support $K_j$ has envelope $\{0\}$, else every sign. The last row holds for every readout by Def 4's support; the
   others are sharper rules for the forms of §3.1. One sentence on the ratio: it can rise only if its numerator can
   rise or its denominator fall.
7. **Theorem 1 (sound directions).** Let $\varphi$ be sum-then-readout over $J$, $F$ a population, and for each
   operation a signature that contains every delta its edits produce on inputs of $F$, with sign sets that contain the
   true signs of the contributions. Apply step one, then step two, per operation; take the union over operations; read
   $\{0\}$ as fixed, within $\{0,+\}$ as up, within $\{-,0\}$ as down, else both; mark residual features both. Then the
   table is sound for $\mathcal{M}$ over $F$, and if $F$ is closed under $\mathcal{M}$, every vector of
   $\mathcal{R}(z)$, $z \in F$, differs from $\varphi(z)$ only in the allowed directions.
8. **Why it holds, and what it means.** In words: the sign of a total lies in the sign sum of its parts' signs, the
   maximum of more values is no smaller, each readout rule is a one-line fact (the ratio's, from
   $a'/b' - a/b = (\alpha b - a\beta)/(b b')$), and sequences follow by induction because closure keeps every
   intermediate input in $F$; without it a sequence may leave $F$ and the table says nothing after that. Meaning: the
   table is computed from item tables and the catalogue alone, for every feature, and its only inputs beyond the
   extractor are the signatures and the sign sets of contributions, each a statement about one kind of item (Q3).
   Proof in Appendix C.
9. **The example, continued (purple).** Population: toy inputs whose table points within the input; closed under
   both operations below. Append at most $B$ bytes (signature from §3.3's Lemma 1(b) example: bytes and strings
   added, the last string replaced by an extension, records untouched): $x_1$ up (the replaced string's count
   cancels), $x_2$ both (a ratio with both parts rising), $x_3$ up, $x_4$ down (its numerator fixed, its denominator
   rising), the side effect of §3.2 now for every append. Overwrite any bytes outside the structure positions of the
   records: strings added, removed, and replaced, bytes replaced with the same count, records replaced with the same
   length read from their unchanged entries: $x_1$, $x_2$, $x_3$ both, $x_4$ fixed. With both operations in the
   threat model, the union gives $x_1$, $x_2$, $x_3$ both and $x_4$ down.

Downstream once drafted: `_j_proofs.tex` (Theorem 1's proof to the new hypotheses; the proof of `lem:fw:signature`
goes), `_i_symbols.tex` (drop (R1)-(R5), $\mathrm{Pre}$, $\Sigma_o$; add $\Delta_o(F)$, $\boxplus$, $E^F_o(k)$), §4's
(R3)/(R4) wording and "precondition" (it becomes how §4 defines $F$), the §3 lead (subsection order: 3.2 side effects
before 3.3 writes), and 3.5's corollary (unchanged in substance; check its symbols).

Questions for the user:

- **Q1. Drop the precondition from the threat model**, so $\mathcal{M}$ is the catalogue $O$ and the population $F$
  does the precondition's job (§4's precondition check becomes the definition of our $F$)? Recommended: yes; $F$ and
  $\mathrm{Pre}$ play the same role in every result, and one symbol goes.
- **Q2. Replace as a third change in the signature**, with four content constraints (any, keys from $K$, same
  length, extension)? Recommended: yes. With only add and remove, a rewritten header moves the section count both
  ways and an extended string makes the longest-string pool "both"; the code relies on both refinements
  (`_unconditional`, `rewrite`, `grow` in `reach.envelope`).
- **Q3. Where the sign sets of contributions come from.** The theorem assumes they contain the true signs; our
  instance reads them partly from the form (a count is never negative) and partly from the item tables of a corpus
  (`reach.Vocabulary`: the smallest recorded value, the keys seen), which §5 checks (pilot vs 2,000 files). Say this
  in one sentence in 3.4 with a pointer to §4, or only in §4? Recommended: one sentence in 3.4; it is the theorem's
  one input a reviewer will look for.
- **Q4. The second toy operation** (overwrite outside the records' structure positions), to show the union over
  operations and a fixed feature? Recommended: yes, two sentences; without it the example never exercises the union.

**Decisions (user, 2026-11-05):** "go ahead and write the subsection"; Q1-Q4 taken as recommended. Drafted the same
day (~1,450 words with both tables and the example). While drafting: each sort of change's sign set is "the signs any
number of such changes can give the sum" (so repetition needs no notation); pools get the coarse rule (up if every
sort's set is within {0,+}, down if within {-,0}, else both), not the sign sum; keys are $Q$ (the symbol table's $K$
collided with the sums); Table 1 is `table*`. Still to do downstream: §4's (R3)/(R4) and "precondition" wording, the §3
lead's subsection order.
