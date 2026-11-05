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
