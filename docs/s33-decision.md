# Does §3.3 ("Edits Given as Writes") belong in the framework? (2026-11-08, session 20)

Analysis for a decision. Nothing in the manuscript is changed until the user approves a plan. Sources: the §3.3
section of `docs/sprint-framework-review.md` (P1-P22, U1-U18, round 2, the user's last reaction), the manuscript
(`_d_framework.tex`, `_e_instances.tex`, `_f_evaluation.tex`, `_g_related_work.tex`, `_j_proofs.tex`,
`_i_symbols.tex`), `docs/paper-mock.md`, `docs/framework-design.md` (§1-5, §13), `docs/formalization.md` (§2, §5.2,
§8, §9), `docs/item-layer-design.md`, and the 2026-11-05 reactions in `docs/writing-spec.md`.

## Summary in plain words

**What §3.3 is for.** Some edits are described by the items they add or remove ("add a section with this content").
Proposition 1 needs exactly that description, so these edits are covered by §3.2. Other edits are described by the
positions they write ("append anything after the end", "overwrite the bytes of the DOS stub"). For these, someone has
to work out which items they can change. For one concrete write that is easy: run the extractor on the edited input.
For a whole operation ("append *any* content") it is not, because there are too many contents to try, and §3.4's
directions need the answer for all of them. §3.3 supplies that answer.

**Does it earn its place as a subsection?** No. The user's criticism is mostly right on substance, not only on
presentation. The formal apparatus (two sets of positions per kind, "local kinds", "fixed layouts", a lemma that
restates its own definition) is much more machinery than the framework needs, and the vocabulary it is built from
(positions that *locate* items, items that are *scanned*) describes how a parser works, which §3.1 deliberately keeps
out of the framework. Lemma 1 has no content beyond Definition 8 (P17 and U15 both noticed this), so the subsection
has no result of its own.

**Is the idea worthless, then?** No, but it lives somewhere else than §3.3 suggests. The idea is that each write has a
set of positions outside of which it cannot change items, and that this set can be known before any content is
chosen. That is what turns "append anything" into a signature without trying contents, and §5 depends on it: the
"Flagged" column of the side-effect table and six of the eight disagreements with the hand-written direction table
come from it. But what §5 depends on is the *instance*: the positions that the instrumented EMBER parser records and
the single-byte checks that show the record is complete. It does not depend on Lemma 1. My earlier claim (session 19)
that §5's headline "rests on" §3.3 mixed up the instance's record with the framework's lemma. The headline example
(adding a section after the overlay removes it) is an operation stated in items and does not touch §3.3 at all.

**Recommendation (option D).** Remove §3.3 as a subsection. In §3.4, where signatures are introduced, add one short
definition, the *footprint* of a write: a set of positions such that a write inside it removes and adds only items
that lie within it. This is the counterpart for the item map of what the support is for a readout (a readout depends
only on the sums in its support; a write changes only the items within its footprint). The whole input is always a
footprint, so the definition excludes nothing. A write whose smallest known footprint is the whole input is the
"flagged" case. How EMBER finds small footprints (the positions its parser reads to find each kind's items, strings
up to the nearest non-printable byte, windows that overlap the write) moves to §4.1, which already describes most of
it. The lemma, structure positions, margins, local kinds, and fixed layouts leave the framework. §3.1 and §3.2 do not
change. The framework shrinks by about 1,200 words.

**Questions for the user** (details at the end): D, or the plainer A (no definition at all; the signature of a write
operation is simply an input that §4 supplies)? The name "footprint"? One sentence in the definition for "the write
keeps its items' positions" (needed so that a count stays fixed under an in-place overwrite), or let §4 supply it?

## 1. What in the paper rests on §3.3's machinery

§3.3's machinery has four parts: (a) the written set $W$; (b) structure positions $L_\tau(z)$ and the flag when a
write meets them; (c) margins $\mu_\tau(z, W)$ and local kinds; (d) Lemma 1: (i) one write's delta, (ii) the bound
for a family of writes, (iii) a fixed layout only replaces items.

"Soundness" below means the result would be wrong or unsupported without it. "Element-stated predictions" means the
side effects or signatures of edits stated in positions. "Presentation" means only the wording uses it.

| Result (where) | Uses | Kind of need | What it would rest on under D |
|---|---|---|---|
| Prop 1, exact side effects (§3.2; Table 5's lower block) | nothing | none | unchanged |
| Table 5, upper block: append, slack, DOS, checksum, random writes exact (§5.1) | (c), (d)(i) | element-stated predictions | the delta of one write is the items of $z$ and of $z'$ within its footprints (one sentence, §3.4); the footprints are EMBER's (§4.1) |
| Table 5, "Flagged" column (867 appends, 5,739 DOS overwrites, ...) | (b) | element-stated predictions | a write whose footprint for some kind is the whole input; detected by comparing the written positions with the positions the parser reads (§4.1) |
| Table 5, item-stated rows' flags (480 add-section, 509 gap insertions) | the same record, applied to the bytes a declared operation writes | instance | §4/§5 text as now ("touches the location of an item the declaration does not cover") |
| Theorem 1 (§3.4) | nothing directly: it takes signatures as a hypothesis ("give each operation a signature that contains the deltas of its edits") | none | unchanged |
| Signatures of the five element-stated operations (§3.4 ¶4, §4.4) | (d)(ii), (d)(iii) | soundness of those signatures | the footprint definition (§3.4), with the "keeps positions" clause for the replace sort |
| Table 6, rows 4-8 (Rich header and section entropy under header-field overwrites; overlay, certificates, relocations and exports under append past a truncated end) | (b), (c) | element-stated predictions | footprints of EMBER (§4.1), and that a footprint depends on the input (§3.4's population paragraph) |
| Table 6, row 3 (Rich header under the gap insertion) | the Rich header's search range as its margin, inside an item-stated operation | instance | §4.1 (the search range is the Rich header's footprint) |
| Table 6, rows 1-2 (overlay and entry section under add-section; the hand-detector experiment) | none of §3.3: declared deltas, found and checked by G7 against re-extraction | none | unchanged |
| Population and closure (§3.4 ¶2; §4.4 plain layouts; §5.3) | (b): "whether an edit writes a structure position depends on the input" | presentation (the reason given for populations) | "a write's footprint depends on the input" |
| Adaptive search scoring append candidates without extraction (§5 setup) | (d)(i), plus local re-reading | cost only | the engine re-reads only the footprint (§4 or §5, one clause); U4: cost is not a framework concern |
| Related work: "it finds the items that an edit of raw elements changes" (§6, ~line 100) | the idea, not the lemma | presentation | footprints, computed by the instrumented extractor |
| Paper mock, contribution 1: "the format enters only for edits stated in raw elements" | the idea | presentation | "the format enters only through the footprints of writes" |

Reading the table: nothing needs Lemma 1 for soundness except the signatures of element-stated operations, and for
those the lemma adds nothing to its definition. What carries weight is (1) the *existence* of a content-independent
footprint for each write, which is one definition, and (2) the *record* that lets EMBER compute small ones, which is
instance work. The definition belongs in §3; the record belongs in §4.

## 2. Generality, honestly

The test: "a general-purpose and powerful framework for understanding any objects".

- **Statement.** A footprint is a property of the item map $\pi$ alone and mentions no format. It always exists (the
  whole input), so like the support of a readout it does not restrict the class; the instrumentation's job is to find
  small ones. This is the same status the support has in §3.1, which the user accepted.
- **Text-like features** (strings, tokens, byte or opcode n-grams). Footprints are short: a run extends to the nearest
  separator that is not written; an $n$-gram window reaches $n - 1$ elements to each side. Correct and nearly
  trivial. Its only content is that a write can merge or split tokens next to it.
- **Drebin.** The attacks are stated in items (add a permission, add a call, transplant code), so footprints are never
  used. An attacker who edits the APK's bytes would face a container (ZIP directory at the end, DEX offset tables,
  binary XML string pools) and the same issue as PE, but no Drebin attack does that.
- **CICFlowMeter.** Elements are packets (or their fields); flows are grouped by addresses, ports, protocol, and a
  timeout. Padding a packet has as footprint the packet's own flow and the pairs around it; changing a timestamp, a
  port, or a FIN flag can regroup flows, so its footprint is the whole trace unless the edit is stated in items.
  Injection and delay, the main traffic edits, are best stated in items. So in traffic the footprint covers padding,
  and the flag covers timestamp edits; it is useful but small.
- **Container formats** (PE, ELF, Mach-O, PDF with its cross-reference offsets, ZIP and Office files with their
  directories, DEX, length-prefixed records in protocols). Here content says where other content lies, so a write can
  change items far from where it lands, including after the end of the input (a table that points past a truncated
  end; a ZIP directory found by searching from the end). This is where footprints are essential and where hand
  analysis fails (Table 6). These are the formats most malware detectors read, so this is not an executable
  peculiarity, but it is a property of *formats*, not of the framework.

Verdict: framework-level as an interface (one definition, parallel to the support), instance-level as work. It does
not define the class, the way sums and readouts do, and it should not be presented as if it did. That is what §3.3
did wrong: it formalized the instance's way of computing footprints (located versus scanned kinds) as if it were the
framework.

## 3. Standalone value

The user's rule: every subsection must do something by itself. Could the material be its own subsection, built on
the question "which items can writing *anything* at these positions change, on this input, without trying any
content"? The question is a good one, and the append-past-the-end case is a good surprise. But the honest answer to it
is a definition and a one-line consequence, and the interesting part (that the answer depends on the input and catches
cases a careful analyst missed) is shown by §4 and §5, not by a proof. As a subsection it would again be "there for
§3.4", only shorter. As one paragraph of §3.4, at the point where §3.4 asks where the signature of an operation given
as writes comes from, it serves that subsection's endpoint directly and needs no standalone justification.

## 4. The realistic alternative

Without footprints, who writes the signature of "append anything", and how do they know it is sound? The realistic
alternative is the hand rule: a person who knows the extractor reads its code and decides, per feature group and
operation, which way features can move. We did exactly that before the derivation existed, with the source open, and
§5 shows the result: for the element-stated operations, five rows of Table 6 are the hand rule's errors (appending can
complete a section, a certificate table, or a directory that pointed past a truncated end; header-field overwrites
can create a Rich header or change a section that starts at offset 0). Learned constraints do not give signatures at
all. The footprint route needs no reasoning about consequences: the instrumentation records which positions the parser
reads, a mechanical fact that single-element changes check (58,666 flips, none unannounced), and the interval query
does the rest. This is the "only provenance makes it cheap" argument, and it is carried by §4's record and §5's
witnesses. The framework needs only to name the object the record computes.

## 5. Options

| | A: signatures of writes as a pure input | B: (session 19) fold into §3.4, Def 7 + Lemma 1 to the appendix | C: short subsection on "what can writing anything here change" | **D: footprint as one definition in §3.4; the computation to §4** |
|---|---|---|---|---|
| Body says | "An operation given as writes gets its signature from the instance (§4), which computes it from the item table" | a paragraph using structure positions and margins, both defined in the appendix | ~500 words: the question, a definition, a lemma, a generic example | ~250 words: the definition, "the whole input is always one", one write's delta, the flagged case, the input dependence |
| Moves to the appendix | nothing | Def 7 (written set), Def 8 (local kinds), Lemma 1 and its proof | the proof | nothing (the one-line consequence needs no proof) |
| Moves to §4 | how EMBER derives write signatures | the EMBER instances of $L$ and $\mu$ | the EMBER instances | how EMBER computes footprints (already mostly in §4.1) |
| §3.4 and §5 change | §3.4 ¶4 two sentences; Table 5's "Flagged" defined in §4 only | references to the appendix | references | §3.4 ¶2-¶4 reordered (part of §3.4's own sprint); captions say "footprint" |
| Net words in §3 | about -1,450 | about -1,100 | about -1,000 | about -1,250 |
| Reviewer risk | high: "how is the append signature derived, and why is it sound?" has no framework-level answer, and the format claim of contribution 1 floats | low on substance; the appendix holds machinery no result needs | medium: a subsection whose result is its definition | low: the format has a named entry point; "it's an oracle" is answered by §4's checks, as Pierazzi's $\Gamma$ is an input |
| Risk with the user | low | high: keeps the concept pair that failed three times | high: a fourth subsection-sized framing of the same idea | medium-low: a fourth framing, but one sentence-level object, no parsing words, parallel to the support |

Option A is the fallback if the user finds even D's definition unnecessary. Its real cost is a reviewer question and
a contribution claim with nothing to point at; about 100 words separate it from D.

## 6. Recommendation: D

Remove §3.3. Define the footprint inside §3.4, at the signatures. Move the EMBER way of computing footprints to §4.1.
Keep §3.1 and §3.2 as they are.

### New structure of §3

| Subsection | Formal endpoint | Single job | Why it stands on its own |
|---|---|---|---|
| 3.1 Sum-then-Readout Extractors (unchanged) | Def 5 | the class | defines what the paper is about |
| 3.2 Edits and Their Side Effects (unchanged) | Prop 1 | one edit's exact side effects from its delta | answers Pierazzi et al.'s side-effect question for the class |
| 3.3 Sound Directions (was 3.4) | Theorem 1, Corollary 1 | which way every feature can move under every edit of a threat model, and the detectors that follow | the paper's second main result |

### Spine for the opening of the new §3.3 (input to its sprint session, not prose)

The rest of the subsection (sign sets, envelopes, the theorem, the corollary) is untouched by this decision and goes
through the sprint as planned.

1. **From one edit to all.** As now: operations as families of edits, threat models, $\mathcal{T}$ and
   $\mathcal{R}(z)$ fixed by the catalogue, $\Gamma$ as input.
2. **Signatures.** As now: the sorts add, remove, replace, with content restrictions; why a replacement is kept as a
   pair. An operation stated in items comes with its signature.
3. **Operations given as writes, and their footprints.** An operation such as "append any content" writes within a
   set of positions that depends only on the input, while its content is free. Definition (footprint): for a kind
   $\tau$, an input $z$, and a set $W$ of positions, a set of positions that contains $W$ is a *footprint* of $W$ for
   $\tau$ if every edit of $z$ that writes only within $W$ removes and adds only items of kind $\tau$ that lie within
   it; it *keeps positions* if every such edit replaces each of those items by one with the same members. Gloss in
   one sentence (a write changes items only within its footprint, as a readout depends only on its support). The
   signature then follows: on $z$, items of kind $\tau$ are added, removed, or replaced only within the footprint, and
   only replaced, by items of the same length, if it keeps positions. For one write, the items of $z$ and of $z'$
   that lie within the footprints form a delta for Proposition 1.
4. **What a footprint costs, with its consolidation.** The whole input is always a footprint, so no kind is excluded;
   a larger footprint only loosens the signature, never makes it wrong. A write whose only known footprint is the whole
   input is *flagged*: the kind may change in any way. Finding small footprints is the instance's work, the only place
   where the format enters (§4).
5. **Populations and closure.** A footprint depends on the input: on an input where another part says that an item
   extends past the end, a write after the end lies inside that item. So directions hold over a population, which is
   closed if no operation leaves it. (This is the current ¶2, moved after the footprint so that its reason exists.)

### Ripples

- **§3 lead:** drop the sentence on §3.3; the §3.4 sentence becomes "§3.3 bounds ... under the edits a threat model
  allows, whether they are stated by the items they change or by the positions they write". Two subsections named,
  one pointer each.
- **§3.4** becomes §3.3; its ¶2 and ¶4 are replaced by spine items 3-5. "Lemma 1(ii)" disappears.
- **Appendix B (proofs):** delete the proof of Lemma 1. Nothing replaces it.
- **Appendix A (symbols):** remove $L_\tau(z)$; $\mu_\tau(z, W)$ becomes the footprint (symbol open); $W$ becomes
  "positions an edit writes".
- **§4.1 (research track's file; proposal only).** It already says that "most of the instrumentation effort goes into
  locating positions" and lists the margins. Reword: for each kind, the record holds the positions its parser reads
  to find the kind's items (*locating positions*, an instance term). A write that touches none of them has as
  footprint the members of the items it writes, which keeps positions, extended for strings to the nearest
  non-printable byte and for windows to the windows that overlap it; for the Rich header it is the search range. A
  write that touches one is flagged. The past-the-end case and the single-byte check stay where they are. Add one
  sentence on breadth: the same three devices (positions read to find items, runs to a separator, windows) cover
  n-gram, string, and flow features. Fix the current cross-reference: "the margins are those of
  \Cref{sec:fw:side-effects}" points at §3.2, which never had margins.
- **§5 (research track; proposal only).** Table 5's caption: "Flagged: the engine declined to predict, because the
  edit writes a locating position (§4.1) that the operation does not declare." Text unchanged otherwise: "an
  interval query of the written positions against the recorded locating positions, with no rule written for this
  case" is the right sentence, now resting on §4.1. Table 6's paragraph ("they are locating positions in the item
  table, and the interval query does the rest") stays.
- **§6 (related work, ~line 94):** "much as our margins bound where items can change" becomes "much as a footprint
  bounds where a write can change items". The closing claim ("it finds the items that an edit of raw elements
  changes") stays.
- **Paper mock:** §3 outline to three subsections; contribution 1: "the format enters only through the footprints of
  edits stated in raw elements".
- **Sprint log:** §3.3's sprint ends here without a retro score (no improved version was read); the next sprint
  session is the new §3.3 (Sound Directions), with spine items 3-5 above as part of its plan.
- **Backup:** the current §3.3 text goes to `manuscript/backup/` before it is removed, as with earlier cuts.

### What a reader must know from §3 to read §5

The delta and Proposition 1 (Table 5); signatures and the footprint, including that a footprint can be the whole
input (the flag) and depends on the input (populations); the direction table and Theorem 1 (Table 6); the corollary
(Table 7). Everything about how EMBER finds footprints comes from §4.1, which is where the experiments' bookkeeping
belongs.

## 7. Open questions

1. **D or A?** Recommended: D. A saves about 100 words and drops the last framework-level trace of the idea, but
   leaves "how is the append signature derived and why is it sound?" to §4 alone and gives contribution 1 nothing to
   point at.
2. **The name.** "Footprint" (recommended: plain, and the word separation logic uses for the part of the state a
   command touches, though no citation is needed). Avoid "reach" (it clashes with the reachable set of §2) and
   "margin" (the failed framing, and it suggests a border around $W$ rather than any set).
3. **"Keeps positions" in the definition, or supplied by §4 as a content restriction?** Recommended: one clause in the
   definition. Without it, an in-place overwrite could remove an item without adding one, so every count of a kind
   it writes (the number of sections under a slack overwrite) would become two-sided, and the derived table would be
   looser than the hand rules on features where they now agree.
4. **Where the breadth sentence (n-grams, strings, flows) goes.** Recommended: §4.1, one sentence; not in §3, where
   the user wants no domain examples.
5. **Timing.** Recommended: make the cut (remove §3.3, back it up, fix the lead, the appendix, the symbol table, and
   §6's sentence) now, and write spine items 3-5 inside §3.4's sprint session, so that §3.4 is reviewed once, in its
   final shape.
