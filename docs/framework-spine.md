# Section 3 (framework): per-paragraph spine for the rewrite (2026-11-04)

Status (2026-11-04): **drafted.** Decisions and comments are in `docs/writing-spec.md` (reaction log). The draft
departs from the spine below: P1-P4 became Section 2 (Background and Motivation); the second half was restructured
around one endpoint per subsection (Lemma 1 for edits, Proposition 1, Theorem 1, the corollary); operations and
threat models moved to the directions; the requirements were renumbered by the step that needs them ((R1) structure,
(R2) margins, (R3) honest tools for finding the item delta; (R4) self-contained contributions, (R5) faithful recording
for adjusting the sums); no tables, figures, or domain examples. Original proposal:

Status then: proposal. The content comes from the current `_d_framework.tex` and the frozen
`docs/formalization.md`. The prose is rewritten from scratch, Pierazzi-style (definition, a sentence or two of
intuition, an example). Word budgets are loose. Feedback that produced this: `docs/writing-spec.md`, reaction log,
2026-11-04 (§3.1).

Per paragraph: **claim** / symbols it introduces (→ where they are used later) / source.

## Decisions for the user

- **D1. Where Pierazzi's setup goes.** The mock already has a Background section (§2, empty) for "Pierazzi et al.'s
  problem space and side effects; who needs which view of the reachable set". The current §3.1 duplicates it.
  Recommended: write P1-P4 below as §2, so §3 opens on our model. Alternative: keep them as §3.1 "Preliminaries".
- **D2. The running example.** Keep the 20-byte URL append (it has the side effect that is easy to miss: every
  section's size ratio falls). It first appears in §3.3, where edits are defined, not in the opening.
- **D3. Tables.** The term and readout tables are currently introduced in §3.2 but their sign columns are used only in
  §3.5. Recommended: §3.2 defines terms and readouts in prose, and both tables appear in §3.5 with their sign rules.
  The domains table stays in §3.2.
- **D4. Figure.** One figure, built in §3.3/§3.4: the running example's edit → item delta → adjusted sums → new
  features (the mock's Figure 1). Optional: a small code skeleton of a sum-then-readout extractor in §3.2.
- **D5. Titles.** §3: "Feature Provenance" (the item table *is* the provenance record; the paper does not use the term
  yet), or "Sum-then-Readout Extractors", or "From Edits to Features". Subsections below.

## Cut or moved

- Out of §3: the EMBER repairs inside (R2) (→ §4); "the detectors of §5 drop residual features" (→ §5); "consolidation:
  we do not compute it" (replaced by P3); the closing classical-pieces paragraph (duplicates §6 ¶4; keep one citation at
  each point of use: IVM at Proposition 1, the sign domain at step 1, incremental parsers at the margins).
- Notation: one reachable set, not both $\mathrm{Reach}(z)$ and $\mathrm{Reach}_\mathcal{M}(z)$; $h$ only in §3.6;
  $\Gamma \vdash \Omega$ only if $\Omega$ is used later (it is: the directions describe $\Omega$'s signs); $\delta^*$ only
  in P3. Pending the symbol-table review.

## Spine

### Lead (no subsection)

- **L.** What the section does, literally: it defines a class of extractors (items, sums, readouts), describes an
  attacker's edits as changes to items, and proves two results: one edit's feature changes are computed exactly from a
  record the extractor writes while it runs; under a whole threat model, the direction each feature can move is
  computed soundly without running an attack. A corollary gives detectors no edit of the threat model can evade.
  Proofs: App. B; symbols: App. A. No example, no figure of speech.

### §2 or §3.1: Problem-Space Attacks (D1)

- **P1. Problem space and feature space.** Pierazzi et al.'s input space $Z$ (the objects of a domain: executables,
  apps, traffic traces), the feature mapping $\varphi: Z \to X \subseteq \mathbb{R}^n$. A feature-space attack changes
  $x$ directly and need not correspond to any object; a problem-space attack edits $z$ with transformations
  $T \in \mathcal{T}$, so its result is the features of a real object. / $Z, X, \varphi, T, \mathcal{T}$ (→ everywhere).
- **P2. Constraints and the reachable set.** The four problem-space constraints $\Gamma$, one clause each (available
  transformations; preserved semantics; plausibility; robustness to preprocessing); they determine the feature-space
  constraints $\Omega$. The reachable set: the features of every object the allowed transformations produce from $z$;
  an evasion is *realizable* if its feature vector lies in it. / $\Gamma, \Omega, \mathrm{Reach}$ (→ §3.5, §3.6).
- **P3. Side effects and where they come from (the consolidation paragraph).** Pierazzi's $\delta^*$ and $\eta$:
  the side-effect features are those altered to satisfy $\Gamma$, by consolidation (their Android examples: imports of
  dependencies, class declarations). Since $\varphi$ is neither differentiable nor invertible, as is usually the case
  in malware detection, they find $\eta$ by applying $T$ and re-extracting. Two things happen in a side effect: the edit
  must write more than its payload (consolidation, chosen by whoever designs the transformation), and the extractor
  turns every written element into changes of many features. Once an edit is fully stated, consolidation included, only
  the second remains, and that is what we compute. / $\delta^*, \eta$ (→ Proposition 1).
- **P4. Who needs which view of the reachable set.** An attack needs $\eta$ for each candidate edit; a monotone detector
  needs, per feature, whether any allowed edit can lower it (Incer et al., Gimenez et al.); constrained attacks take
  $\Omega$ as input. These are the two things §3 computes. Today they are re-extracted, written by hand, or learned from
  observed attacks (one sentence; §6 has the detail).

### §3.1 (or §3.2): Sum-then-Readout Extractors

- **P5. The shape, in plain terms.** Written as code, these extractors initialize running totals, loop over pieces of
  the input adding each piece's contribution, then apply a formula per feature. The three layers: items, sums,
  readouts. An edit is easy to describe in the first layer and hard in the last. (Optional code skeleton, D4.)
- **P6. Items (Definition).** Elements and positions; an item is one iteration of an extractor loop, with a kind, an
  identity (how the extractor reaches it), and members (the positions its content is read from). Same item across
  inputs = same kind and identity. Examples: a section of an executable, a printable string, a packet. /
  $z[p], \iota, \kappa(\iota), M(\iota)$ (→ §3.3, Prop. 1). Locating positions wait until §3.3, where they are needed.
- **P7. Contributions and sums (Definition).** Each item adds a contribution to a finite set of sums; the sum vector
  totals them. Pools keep a maximum or a minimum. Contributions take a few forms (counts, nonnegative attributes,
  hashed keys, slots, opaque values), detailed with their signs in §3.5. / $S, \mathbf{v}(\iota), \mathbf{s}(z)$.
- **P8. Readouts and the class (Definition 1).** A readout is a formula of a known type over a few sums; an extractor is
  sum-then-readout over the modeled features $J$ if $\varphi_j = \rho_j \circ \mathbf{s}$; the rest are residual and
  every result lets them change arbitrarily. Example: number of strings, their total length, the average as a ratio. /
  $\rho_j, J$.
- **P9. The boundary of the class.** Sums and pools are folds over commutative monoids; the maximum has no inverse,
  which is why the record keeps every item and not only the totals. In Gray et al.'s terms, sums are distributive and
  readouts algebraic; a holistic statistic (a median packet length) falls outside. Global program analyses and learned
  features also fall outside (pointer to §7).
- **P10. The item table and three extractors.** Instrumenting an extractor once means having it write, in the same
  pass, every item with its kind, identity, members, and contribution: the item table. Table (domains): EMBER (built),
  Drebin and CICFlowMeter (sketched).

### §3.2 (or §3.3): Edits as Item Deltas

- **P11. Edits and item deltas (Definition).** An edit takes $z$ to $z'$; its written set $W$; the item delta (removed,
  added, modified, moved). Running example introduced here: appending the 20 bytes adds 20 elements and one string of
  19 characters (the zero byte keeps it from joining a string at the old end). / $W, \Delta$.
- **P12. Operations and threat models.** An operation is a family of edits with parameters; a threat model is a
  catalogue of operations and a population it applies to. An operation stated in items (add a section) comes with its
  signature; one stated in elements (append bytes) does not, and §3.4-§3.5 derive it. Whether an operation preserves
  behavior belongs to $\Gamma$ and is an input. / $o, \Theta_o, \mathcal{M}, \Sigma_o$.
- **P13. Locating positions, parsed and scanned kinds.** To find $\Delta$ without parsing $z'$, the record also notes
  the positions that decide whether an item exists and where its members lie. Parsed kinds are reached through
  pointers or keys; scanned kinds are found by examining content, with a recognizer. / $L(\iota), L(z)$, recognizer.
- **P14. Four classes of edits.** An interval query of $W$ against the locating positions sorts each edit: content,
  item-creating, declared structural, undeclared structural (flagged, not predicted). The running example is
  item-creating; on a truncated file whose section table points past its end, the same append writes a locating
  position and the query catches it.

### §3.3 (or §3.4): Exact Side Effects

- **P15. The recipe on the running example (with the figure).** List the changed items, adjust the sums by their
  contributions, apply the readouts again. Strings and URLs +1; the average length gains 19 over 1; 20 histogram bins
  and entropy; the overlay entropy; no section entry touched; every section's size ratio falls, the easily missed one.
- **P16. When the recipe is right: (R1)-(R5).** One sentence each on what can go wrong and what the requirement rules
  out: faithful recording; self-contained contributions; a complete record of structure; changes stay near the edit
  (margins, as in incremental parsers); honest tools. (R1), (R2), (R5) always; (R3), (R4) only for edits stated in
  elements, the one place the input format enters. EMBER's violations and repairs: a pointer to §4.
- **P17. Proposition 1 (exact side effects)** and its proof idea (changed items confined to $W$ and the margins; each
  sum split over changed and unchanged items; IVM's delta rules, cited here); sequences by carrying the table forward;
  $\eta$ is exact on $J$.
- **P18. Pools: why the record keeps items.** The traffic example: injecting a packet removes the pair that held the
  longest gap; the new maximum is in the item table, not in the old maximum.

### §3.4 (or §3.5): Sound Directions

- **P19. What a robust detector needs, and the definitions.** For each feature, whether some allowed edit can raise
  it, lower it, both, or neither, on every input it will face. Sign sets, the sign sum, envelopes over a population,
  the direction table and its soundness (Definition). Incer et al.'s four cases, assigned by hand; Gimenez et al. keep
  only rising features. / $\boxplus, F, E, D$.
- **P20. Step 1: the signs of the sums.** Table (terms with sign columns); an operation's envelope lies in the sign sum
  of its items' signs over its signature: one step of the sign domain of abstract interpretation (cited). Two
  refinements: hashed buckets by enumerating the keys (Severi et al.); pattern matches when a string is extended.
- **P21. Signatures derived per input.** For operations stated in elements, (R3) and (R4) give the signature from the
  item table without applying an edit; it depends on the layout, which is why directions hold over a population.
- **P22. Step 2: from sums to features.** Table (readouts with their sign rules). The running example's directions
  under appending up to $B$ bytes.
- **P23. Theorem 2 (sound directions)** and its proof idea (sign of a sum; monotone readouts, the ratio identity;
  induction under closure). The traffic contrast: injecting only between packets makes the mean gap fall; allowing it
  after the last packet makes it move both ways.

### §3.5 (or §3.6): Robust Detectors

- **P24. Corollary.** The score $h$ introduced here. Gimenez et al.'s result (score never falls when features rise;
  edits only raise features); with a computed table it becomes a corollary of Theorem 2, for every feature. A GBDT with
  monotone constraints is such a score.

## Notation issues noticed (for the symbol-table round)

- $\kappa$ is Pierazzi's attack confidence and our item kind (clash only if §2 uses their $\kappa$).
- $A, B$ are sign sets in $A \boxplus B$; $B$ is also the byte budget.
- $T$, $T_{o,\theta}$, $\mathcal{T}$, $O$, $\mathcal{M}$: five symbols for transformations and their collections.
- $E^F_o(s)$ and the short form $E_s$ both appear; bold is used for $\mathbf{s}, \mathbf{v}, \boldsymbol{\eta},
  \boldsymbol{\delta}^*$ but not for feature vectors $x$, $\varphi(z)$.
