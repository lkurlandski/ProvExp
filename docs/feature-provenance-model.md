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
*locality* assumption; Section 7 lists where it fails). Signed entries are allowed (signed feature hashing).

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
3. **structural edit**: S touches a locating element, so the parse may change. Two cases (adopted 2026-10-22):
   - **declared**: the transformation states the resulting item delta (add this section-table entry and raise
     NumberOfSections by one; zero the SECURITY entry, which removes the certificate items; move the headers forward
     by 0x200 bytes). The model takes the delta from the transformation and C1 applies.
   - **undeclared**: the new parse is not stated (packing, a rebuild by a binary-rewriting library with side effects
     of its own). The model flags the edit and the affected items (those located by elements in S) rather than
     predicting it.

Compound transformations from the attack literature (add a section, append to slack, rename a section, add imports,
remove the signature) are lists of item operations: add items, remove items, modify items, and **move** items (same content, new
location; DOS extension and content shifting), plus the declared structural edits they force (NumberOfSections,
SizeOfImage). A move changes only position-defined items (the byte-entropy windows after the insertion point) and
contributions read through a file offset (the SECURITY entry); every other item keeps its contribution. The byte view and the item view are therefore not alternatives: the byte
view is the interface (threat models and explanations are stated in bytes), the item view is where the computation is
exact.

## 4. Claims (to prove)

Let an edit add items T+, remove T-, modify T~ (old -> new), and move T→, with no undeclared structural edit (a
declared one enters through its stated delta). Moved items contribute unchanged unless position-defined; those are
re-derived as removed-and-added (T→ ⊆ T- ∪ T+ for windows).

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

## 4a. Proof sketches (2026-10-22)

**In plain terms.** All four claims rest on one observation: the extractor computes each feature by walking over the
file's pieces (items), adding up what each piece contributes, and then applying a final formula (the readout). If an
edit changes only a known list of pieces, the new totals are the old totals plus the new pieces' contributions minus
the old ones', and the features follow by re-applying the formulas. Everything that can go wrong is a way in which
"the edit changes only a known list of pieces" or "a piece's contribution depends only on the piece" fails. Those
failures are collected as four assumptions; each is checked per item kind, and each can be tested on real files by
comparing the prediction with re-extraction.

### Setting

- A file z has a multiset of items T(z). Each item t has a kind k(t) and a content c(t) (its member bytes and any
  attributes read from them). The **item table** of z lists, for every item, its kind, position, and contribution.
  It is what the instrumented extractor outputs (today implicitly, via `Contributions.add_item`).
- Contributions v(t) = v_{k(t)}(c(t)) are vectors over the sums. Each sum aggregates with a commutative operation:
  addition (counts, histograms, hashed buckets, signed or not) or max/min (max section entropy, max size ratio).
- Features are φ(z) = g(A(z)). The readouts in EMBER v3 are: identity; a ratio of two sums (normalized histograms, the
  printable distribution, average string length, section size ratios once the file size is moved into the readout,
  see A2); the entropy of a histogram of sums (file, overlay, string entropy); presence (min(1, ·)); and a
  hashed-presence readout over keyed sums (unique import libraries).

### Assumptions (checked per item kind; each is testable by re-extraction)

- **A1 (complete location).** Every byte the parser uses to decide whether an item exists or where it lies is recorded
  as a locating element. Then an edit that touches no locating element leaves every item at the same position with
  the same extent, so the parse is unchanged by definition. This is a requirement on the instrumentation: today's P
  records membership well and location only partly (e_lfanew, NumberOfSections, PointerToRawData, directory entries
  must be added).
- **A2 (local contributions).** v(t) depends only on t's kind and content. Known EMBER failures and their fixes:
  section size ratios divide by |z| (fix: contribute SizeOfRawData and divide in the readout; max(s_i/N) = max(s_i)/N);
  unique import libraries are a set (fix: keyed counts with a presence readout); a repeated DLL name in a second
  import descriptor **overwrites** the first one's functions (`imports[dll_name] = []`), a genuine non-local effect
  to flag; the entry section is chosen by a rule over AddressOfEntryPoint and all section ranges (treat the entry
  section as a located item whose locating elements are those fields).
- **A3 (local recognition).** Each recognizer has a margin m_k: after a write to region S, the items of kind k that
  can differ are those overlapping S widened by m_k. Strings (maximal runs of 5+ printable bytes): the margin extends
  to the nearest non-printable byte on each side, since a run's extent depends only on its neighbors. Byte-entropy
  windows (2,048 bytes at multiples of 1,024): the windows overlapping S; appending d bytes adds the windows that now
  fit and leaves the old ones intact (files under 2,048 bytes are one whole-file window, which any edit modifies).
  Fixed-offset fields: no margin.
- **A4 (faithful declaration).** A declared structural edit produces exactly the item delta it declares. This is
  where LIEF-based rebuilds can fail; it is a property of the tool, not of the model.

### C1 (exact side effects)

Under A1-A4, for an edit that is content, item-creating, declared structural, or a move:

1. *The delta is known.* Content edit: by A1 the parse is unchanged, so T~ is the items whose members intersect S
   (from the item table) and T+ = T- = ∅. Item-creating edit: by A3, re-run each recognizer on S widened by its margin;
   items found there in z are T-, items found in z' are T+. Declared structural edit: the delta is given (A4). Move:
   items keep their content, so by A2 they keep their contributions, except position-defined items (windows, fields
   read through a file offset), which are re-recognized as in the item-creating case on the shifted range.
2. *The sums follow.* Additive sums: A(z') = A(z) + Σ_{T+} v − Σ_{T-} v + Σ_{T~} (v_new − v_old), because the sum over
   a multiset is additive under union and removal, and by A2 the untouched items keep their contributions. Max/min
   sums: adding is max(A, v_new); removing or lowering the current maximum needs the runner-up, which the item table
   holds. So C1 needs the item table of z, not only A(z); it never needs z' to be extracted.
3. *The features follow* by applying g. ∎

The proof is short; the work is in A1-A3 per item kind. That is also the first prototype check (go/no-go): on pilot
files, for each transformation in Section 6, compare C1's prediction with re-extraction feature by feature. A mismatch
is either a bug or an A1-A4 failure to be listed.

### C2 (coupling): the statement needs a correction

**As stated, C2 is false in one direction.** "Two features are coupled exactly when some item the attacker can add,
remove, or modify contributes to both" conflates two things: (a) **co-movement**: a given operation changes both
features (adding a writable section raises both the section count and the writable-section count); and (b)
**inseparability**: no allowed combination of operations changes one without the other, which is what Severi et al.
needed to rule features out. Sharing an item gives (a), not (b): adding a read-only section raises the section count
alone, so the two counts can still be set independently by mixing the two kinds of section.

**Proposed restatement.** Let W be the set of change vectors of allowed operations (each one's v_new − v_old, or v(t)
for an added item, restricted to the sums). (a) Co-movement is read off each w ∈ W directly (a corollary of C1).
(b) Under an add-only threat model and identity readouts, features i and j can be moved independently, each in the
directions it can move at all, iff the projections of W onto the (i, j) plane generate a cone that contains each
attainable axis direction; otherwise they are coupled, and the projected cone says how (for example, the writable
count can never exceed the section count added with it: every w has w_writable ≤ w_count). Through a shared readout
(every histogram bin divided by the file size), coupling comes from g: the bins move jointly along the reachable set
of C3. So C2 becomes a corollary of C1 (for co-movement) and C3 (for inseparability).

### C3 (reachable sums and features, add-only)

Threat model: the attacker adds items from a catalogue C (e.g., "a section with any name, characteristics, and content
of up to s bytes"; "append up to B bytes"), any number of times within a budget, plus the declared structural edits
each addition forces (those enter the item's vector: an added section also adds +1 to `header` number_of_sections).

1. *Sums.* By C1 applied to each addition, A(z') = A(z) + Σ_t n_t v(t), n_t ∈ ℕ. Relaxing n_t to real n_t ≥ 0 gives
   the convex cone A(z) + cone(v(C)), a sound over-approximation (it contains every reachable sum). For parameterized
   catalogues (any name, any content), take for each sum the range of v over the family: a box per item kind; the
   cone of the box is still sound.
2. *Boundary effects.* Two added chunks can interact: adjacent printable payloads merge into one string (one fewer
   string, one longer string); appended windows straddle two chunks. Soundness needs these either excluded by the
   threat model (chunks delimited by a non-printable byte, at a cost of one byte) or added as extra generators with
   bounded multiplicity (one merge per boundary). This is the one place where C3 needs care beyond C1.
3. *Readouts.* Identity and presence: monotone, so intervals map to intervals. Max/min: under add-only, max is in
   [A_max(z), max(A_max(z), sup_C v)] and never decreases. Ratio a/b with nonnegative contributions (mediant
   inequality): every reachable value lies between the current ratio and the most extreme catalogue ratio a_t/b_t,
   unbounded if some item has b_t = 0 < a_t. Normalized histograms, exactly: appending content with byte
   distribution q to a file with distribution p and N bytes gives λp + (1 − λ)q with λ = N/(N + d); with a budget of B
   bytes, the reachable set is {λp + (1 − λ)q : q ∈ conv(catalogue distributions), λ ∈ [N/(N+B), 1]}, a polytope (with
   arbitrary bytes allowed, conv is the whole simplex). Entropy of such a histogram: concave in it, so its maximum over
   the polytope is a small convex program and its minimum is attained at a vertex; together they give a sound
   interval.
4. *Region for verified training.* Per-feature intervals from step 3 form a box containing Reach(z, M), which is the
   input region Chen et al.'s verified training needs; the polytope constraints (shared denominators, the coupling of
   C2) give a tighter, still sound region if the training method accepts linear constraints.

Limits: add-only (removals and modifications need their own generators, −v(t) or v_new − v_old, and the sign analysis
loses the cone's simplicity); the integer and budget structure is relaxed, so the region is sound but not tight;
A1-A4 as for C1.

### C4 (directions): the statement needs a correction for nonlinear readouts

**As stated, C4 holds for identity, presence, and max/min readouts, not for ratios or entropies.** For an identity
readout, feature j can rise under add-only iff some catalogue item has v_j > 0 and fall iff some has v_j < 0 (signed
hashing gives both when the attacker chooses the name; unsigned import hashing gives up only). Max: up only. But a
ratio rises iff some catalogue item's own ratio exceeds the file's current ratio, so the direction depends on z, not
only on signs: appending zero bytes lowers every normalized histogram bin except bin 0. Entropy: along the segment from
p toward an added distribution q, the entropy first rises iff the cross-entropy −Σ q_i log p_i exceeds H(p); by
concavity, if it does not rise at first it never rises; and since the cross-entropy is linear in q, checking the
catalogue's vertices suffices. Decreases are budget-dependent (check the vertices at the budget's λ).

**Proposed restatement.** Per file: the reachable directions of each feature are decidable from the catalogue's
contribution vectors and the readout, by the sign test (identity, presence, max/min), the ratio test (ratios), or the
cross-entropy test (entropies). Globally (for all files, which is what Incer et al.'s four cases and a monotone
classifier need): a feature is up-only if it is up-only for every file; identity, presence, and max/min features
get a global answer from the signs alone; ratios and entropies are generally "both" globally, and the per-file
answer is what the model adds. Gimenez et al.'s PV selection estimates the global answer empirically from observed
attacks; C4 computes it from the extractor, which is the comparison A's defense side should be built on.

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

## 6. Coverage of real transformations (on paper, 2026-10-22)

Sources: secml-malware's manipulations (read from its source code: `attack/whitebox`, `attack/blackbox`,
`utils/pe_operations.py`), Labaca-Castro et al.'s Table 1 (t0-t9, arXiv 2102.06747), and MAB-Malware's Table 1 (8
macro- and 5 micro-actions, arXiv 2003.03100). The generic optimizers in secml-malware (FGSM, discretized bytes,
end-to-end) are search methods over these manipulations, not transformations of their own; Kreuk/Suciu (padding +
slack) and Format Exploit (extend + shift) are combinations of rows below. That leaves 34 listed transformations, which
reduce to 16 distinct ones.

"Bytes" below means the groups every byte write touches: the byte histogram, the byte-entropy histogram, the file
entropy (`general`), and the string features (new printable runs of 5+ bytes, or broken ones; re-recognized locally).
A class is the worst class among a transformation's writes. **Strict** is the model as written in Section 3:
structural = touches a locating element. **Declared** marks a structural edit whose item delta the transformation
itself states (it adds a section-table entry, zeroes a directory entry, moves the headers by a known amount), so the
model does not have to predict the new parse.

| # | Transformation | Listed as | Strict class | Item operations | Feature groups touched (readout effects in *italics*) |
|---|---|---|---|---|---|
| 1 | append bytes at the end | secml padding, GAMMA padding; OA, OA1; t0 | item-creating | add byte items, end windows, strings; create or extend the overlay item | bytes; `general` size; `section` overlay size/ratio/entropy and the max/min entropy and size ratio; *every histogram bin and every section's size ratio (denominator \|z'\| grows)* |
| 2 | write section slack (between VirtualSize and SizeOfRawData) | secml slack (Kreuk, Suciu); SP, SP1, CP1; t4 | content | modify byte items and the section item (its entropy) | bytes (total unchanged, so only the written bins move); `section` that section's entropy, its hashed entropy bucket, *max/min entropy* |
| 3 | partial DOS header (bytes 2-59) | secml partial DOS | content | modify DOS-header field items, byte items | bytes; `general` start bytes 2-3; `header` DOS fields except e_magic, e_lfanew |
| 4 | full DOS header and stub (bytes 2-59, 64 to e_lfanew) | secml full DOS | content; structural for the Rich header | as 3, plus the stub's strings; may destroy or re-key the Rich header | as 3; `strings` dos_msg; `richheader` (pairs are XOR-decoded with a key and delimited by markers in the edited range: flagged) |
| 5 | header fields ignored by the loader (Nisi et al.) | secml header fields | content | modify field items | bytes; `header` timestamp, pointer_to_symbol_table, number_of_symbols, linker/OS/image versions |
| 6 | break the checksum | BC; t9 | content | modify one field item | bytes; `header` checksum |
| 7 | rename a section | SR, SR1; t2 | content | modify the section item's name | bytes; `section` sizes, vsizes, entropies, characteristics *move from bucket h(old) to h(new)* (four signed hashers keyed by name), entry-name hash if it is the entry section, number of empty names |
| 8 | code randomization (in place, same length) | CR | content | modify byte items and the code section item | bytes; `section` that section's entropy and its bucket, *max/min entropy* |
| 9 | remove debug (zero the DEBUG directory entry) | RD; t6 | structural, declared | modify the directory item; remove the debug item (no EMBER feature reads it) | bytes; `datadirectories` DEBUG size and address; `pefilewarnings` possibly |
| 10 | remove the signature (zero the SECURITY entry) | RC; t5 | structural, declared | modify the directory item; remove the certificate items | bytes; `datadirectories` SECURITY; `authenticode` *all features fall to their defaults*; if the certificate bytes are also stripped, as 1 in reverse |
| 11 | add a section | GAMMA sections; SA, SA1; t3 | item-creating + structural, declared | add a section-table entry and section item; modify NumberOfSections, SizeOfImage | Section 5's table: `section` counts, buckets of the chosen name, max/min, ratios; `header` number_of_sections, sizeof_image (sizeof_code / initialized data if updated); bytes; `general` size; overlay moves |
| 12 | add imports | GAMMA API; t1 | item-creating + structural, declared | add (library, function) items; redirect the IMPORT/IAT entries to a new section (as 11) | `imports` library and function buckets (*unsigned hashing: up only*), counts; `datadirectories` IMPORT, IAT; `strings` (the names are printable); everything of 11 |
| 13 | extend the DOS header (move the PE header forward) | secml extend | structural, declared | move every header and section item by a known amount; add a gap of editable bytes | bytes (*byte-entropy windows re-tile after the gap unless the shift is a multiple of the window step*); `header` sizeof_headers; `general` size; *section size ratios*; SECURITY offset must be fixed or the signature is lost |
| 14 | shift section content (insert before the first section) | secml shift, GAMMA shift | structural, declared | move every section item; add a gap | as 13, without sizeof_headers |
| 15 | UPX pack | t7 | structural, undeclared | whole-file rewrite | all groups |
| 16 | UPX unpack | t8 | structural, undeclared | whole-file rewrite | all groups |

Shares (34 listed transformations / 16 distinct):

| Class | Listed | Distinct | Exact under C1 as stated |
|---|---|---|---|
| content (2-8) | 14 (41%) | 7 | yes |
| item-creating (1) | 5 (15%) | 1 | yes |
| structural, declared (9-14) | 13 (38%) | 6 | no: needs the declared delta (below) |
| structural, undeclared (15-16) | 2 (6%) | 2 | no: out of scope |

**What this says.** Under the strict reading, 15 of 34 (44%) are structural, short of "most" but close. All but the two
UPX actions are structural only in a predictable way: the transformation says which items it adds, removes, or moves.
Two refinements to Section 3, **adopted 2026-10-22** (Sections 3 and 4 now state them), bring 32 of 34 (94%) under
an exact or bounded side-effect claim:
1. **Declared structural edits**: C1 holds for a structural edit when the transformation states its item delta (T+,
   T-, T~). Section 3 already treats "add a section" this way; the claim should say so.
2. **A fourth item operation, move**: items keep their content and change location (rows 13-14). Only
   position-defined items change: the byte-entropy windows (re-tile after the insertion point) and anything read
   through a file offset (the SECURITY entry). Everything else is exact, and the denominator effects come through the
   readout.

**Caveats, harshly.**
- **The weight of evidence is not the count.** The strongest action in Labaca-Castro et al. is UPX packing (row 15),
  which the model cannot cover; MAB-Malware's most effective is overlay append (row 1), which is trivially covered.
  A coverage claim must also be stated as a share of successful attacks, not only of listed transformations.
- **Implementations add undeclared side effects.** The Labaca-Castro/gym-malware actions and secml's GAMMA sections
  and API attacks rebuild the file with LIEF's Builder, which MAB-Malware's authors report changes binaries
  unnecessarily (sometimes breaking them). The classification is of the transformation's semantics; a real tool may
  be structural where its description is not. (Comparing C1's prediction with re-extraction would expose this, a
  side use, not an application.)
- **The content rows are where provenance is least needed.** Rows 3, 5, and 6 map named header fields to named
  features, the trap that sank the old direction. The non-obvious effects are the readout effects and hashing: append
  moves every histogram bin and every section's size ratio; renaming moves four groups of hashed buckets at once;
  adding imports is up-only on unsigned buckets while adding a section is two-sided on signed ones. That is where A has
  to show its value.
- **Features outside the model.** `pefilewarnings` and parse-error flags can change under any row and have no items;
  this residual is not quantified.

## 7. Scope and limitations

- **Structural edits** (moving the PE header, shifting sections, mid-file insertion for windowed features, packing)
  change the parse. The model identifies them (location relation) and the items affected, but does not predict the
  new parse. Whole-file transformations (packing, encryption) are out of scope.
- **Locality failures**: v(t) depends on the rest of the file when an item's contribution is computed relative to
  global state (a field read through an RVA translation, section size ratios before the readout, de-duplication of
  items). These are flagged per item kind.
- **Functionality** is an input (the threat model), not derived.
- Features with no items (whether the file parses; pefile warnings) stay outside the model, as today.

## 8. Open questions

1. Coverage on paper is done (Section 6): 32 of 34 listed transformations are exact or bounded if C1 admits declared
   structural deltas and a move operation. Still open: the share of *successful* attacks (UPX dominates
   Labaca-Castro et al.), the share of feature mass, and how often LIEF-based tools add undeclared side effects.
2. Catalogues of addable items: given by the threat model, harvested from benign files, or parameterized (a section
   of any size)? C3 needs a finite or parameterized description.
3. Which application leads: an attack-side result (realizing feature changes, including hashed buckets Severi et al.
   ruled out), a defense with guarantees (C3 + verified or monotone training), or both.
