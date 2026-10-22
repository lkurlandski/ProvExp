# The feature provenance model (draft, 2026-10-22)

Conceptual design for the reoriented project (feature provenance bridging the feature-problem space gap in malware
classification). No code yet. Propositions are stated as claims to prove; the worked example uses the EMBER v3
extractor in `src/provexp/featuresets/ember2024/features.py`.

## 1. The object we need

Every line of related work needs, for a file z and a set of allowed edits M, the set of feature vectors an attacker
can reach, Reach(z, M) = { φ(z') : z' obtainable from z by edits in M }, or a view of it:

| View | Who needs it | How they get it today |
|---|---|---|
| side effects of one edit | Pierazzi et al.; Labaca-Castro et al. | empirically (minimal-app injection; re-extraction) |
| reachable direction per feature | Incer et al. (four cases); Gimenez et al. (monotonicity) | by hand; perturbation vectors of attacks |
| coupling between features | Severi et al.; Sheatsley et al.; Bostani et al. | by hand; learned from data |
| realizing a target feature change | Rosenberg et al.; Severi et al. | hand-written modifiers per feature |
| a sound over-approximation | Chen et al. (verified training) | trivial for Hidost (features are tree paths); missing elsewhere |

Research problem: **compute views of Reach(z, M) automatically from the instrumented extractor.** The flat
provenance matrix P (elements x features) describes the extractor at z only and cannot answer this (new content creates
items P never saw; edits to pointers change the parse).

## 2. Three layers

Most feature extractors in security ML compute "a sum over items, then a readout": counts and presence of strings,
imports, API calls, permissions, paths, n-grams; histograms; flow statistics; header fields (a sum over one item).

**Layer 1: the parse (elements -> items).** The input z is a sequence of *elements* (bytes, characters, tokens,
packets). The extractor recognizes *items* T(z): the units its sums run over (a string, a section-table entry, an
import name, a header field, a single byte for the byte histogram, a window for windowed entropy). Two relations:
- *membership* m(e, t): element e is part of item t's content (the bytes of a string; the bytes of a field);
- *location* l(e, t): element e determines where item t is or whether it exists (e_lfanew, PointerToRawData,
  NumberOfSections, a string's terminating byte).

**Layer 2: contributions (items -> sums).** Each item t has a contribution vector v(t) over a set of sums; the sums are
A(z) = Σ_{t ∈ T(z)} v(t). v(t) depends on the item's own content and kind, not on the rest of the file (the
*locality* assumption; Section 6 lists where it fails). Signed entries are allowed (signed feature hashing).

**Layer 3: the readout (sums -> features).** φ(z) = g(A(z)), with g known per feature: identity (counts, fields),
division by a total (normalized histograms, size ratios), an entropy formula over a histogram, max over items,
presence (min(1, count)), thresholds.

**The flat P is a projection.** Spreading each item's contribution uniformly over its members and passing it through
the readout by the data-flow convention gives today's P. It stays the right object for explanation transfer (and for
building the reader's intuition). For features additive over items, the item-level weights are the items' Shapley
values (the existing Proposition 2, moved to layer 2).

## 3. Edits

An attacker edit is described at the level the attacker thinks in, bytes, and translated to item operations through
layer 1. A byte write to region S falls into three classes:
1. **content edit**: S lies inside the members of existing items and touches no locating element. Each touched item
   is modified; recompute v(t) for those items only. Bytes are themselves items for the histograms, so every byte
   write is at least a content edit of byte items.
2. **item-creating edit**: the item recognizers whose input covers S may recognize new items or extend neighbors
   (printable bytes next to an existing string extend it). Re-run the recognizers locally on S plus a margin set by
   the recognizer (for strings, up to the nearest non-printable byte on each side).
3. **structural edit**: S touches a locating element. The parse may change; the model flags the edit and the
   affected items (those located by elements in S) rather than predicting it.

Compound transformations from the attack literature (add a section, append to slack, rename a section, add imports,
remove the signature) are lists of item operations: add items, remove items, modify items, plus the structural edits
they force (NumberOfSections, SizeOfImage). The byte view and the item view are therefore not alternatives: the byte
view is the interface (threat models and explanations are stated in bytes), the item view is where the computation is
exact.

## 4. Claims (to prove)

Let an edit add items T+, remove T-, and modify T~ (old -> new), with no structural edit.

- **C1 (exact side effects).** φ(z') = g(A(z) + Σ_{T+} v(t) − Σ_{T-} v(t) + Σ_{T~} (v(t_new) − v(t_old))).
  The side-effect vector of Pierazzi et al. is computed without extracting z', from the items the edit touches.
- **C2 (coupling).** Two features are coupled under M exactly when some item the attacker can add, remove, or modify
  contributes to both sums (or the readout mixes them, e.g., a shared denominator). Severi et al.'s
  num_sections / num_write_sections dependency is the vector of a writable section.
- **C3 (reachable sums).** Under an add-only threat model with a catalogue C of addable items, the reachable sums are
  A(z) + { Σ n_t v(t) : n_t ∈ N }; their convex cone is a sound over-approximation; through g (interval bounds for
  ratios, entropies, maxima) it gives the input region verified training needs (Chen et al.).
- **C4 (directions).** Feature j can be increased (decreased) under M iff some combination of allowed item operations
  raises (lowers) g_j, decidable from the signs of v_j over the catalogue and the monotonicity of g_j. This yields
  Incer et al.'s four cases (fixed, up only, down only, both) automatically.

## 5. Worked example: adding a writable section (EMBER v3)

Edit: add a section named `.data2`, raw size s, content c, characteristics read|write, before any overlay.

| Layer-1 effect | Items | Features (EMBER group) | Readout |
|---|---|---|---|
| add section-table entry | section item t (name, size s, vsize, entropy H(c), props) | number of sections, number of writable sections (`section`, counts) | identity: +1, +1 |
| | | hashed name buckets for size, vsize, entropy, characteristics (`section`, 11-210) | signed hashing: ± s, ± vsize, ± H(c) in bucket h(".data2") |
| | | max section entropy, max size ratio (`section`) | max over items: changes only if H(c) or s/|z'| is the new max |
| modify header fields (structural, forced) | NumberOfSections, SizeOfImage, (CheckSum if recomputed) | `header` fields | identity |
| add s bytes | byte items | byte histogram (`histogram`) | divided by the new file size: **every bin moves** |
| | windows | byte-entropy histogram (`byteentropy`) | new windows only if appended; inserting mid-file shifts every later window (structural) |
| | strings in c | string counts, URL/path/registry counts, printable distribution (`strings`) | identity; distribution normalized |
| | | file size, file entropy (`general`) | identity; entropy formula |
| overlay moves (structural, if present) | overlay item | overlay size ratio, entropy | flagged |
| | existing sections | size ratios of every section | denominator |z'| changes |

What the example shows: (i) C1 covers most rows exactly; (ii) the readout, not the items, is what makes normalized
features move in both directions (the attacker cannot add bytes without lowering every other bin's share); (iii)
signed hashing makes even an add-only edit two-sided on hashed buckets, which Incer-style manual analysis treats as
"cannot fit"; (iv) the structural rows are where the model flags rather than predicts, and they are few and known.

## 6. Scope and limitations

- **Structural edits** (moving the PE header, shifting sections, mid-file insertion for windowed features, packing)
  change the parse. The model identifies them (location relation) and the items affected, but does not predict the
  new parse. Whole-file transformations (packing, encryption) are out of scope.
- **Locality failures**: v(t) depends on the rest of the file when an item's contribution is computed relative to
  global state (a field read through an RVA translation, section size ratios before the readout, de-duplication of
  items). These are flagged per item kind.
- **Functionality** is an input (the threat model), not derived.
- Features with no items (whether the file parses; pefile warnings) stay outside the model, as today.

## 7. Open questions

1. How to measure coverage: what share of realistic transformations (secml-malware, Labaca-Castro et al.'s toolkit,
   MAB-Malware's actions) and of feature mass falls into exact (C1), bounded (readout), and flagged (structural)?
2. Catalogues of addable items: given by the threat model, harvested from benign files, or parameterized (a section
   of any size)? C3 needs a finite or parameterized description.
3. Which application leads: an attack-side result (realizing feature changes, including hashed buckets Severi et al.
   ruled out), a defense with guarantees (C3 + verified or monotone training), or both.
