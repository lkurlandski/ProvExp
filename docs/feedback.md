# Feedback on `docs/formalization.md` (revision 2), for revision 3

Collected in discussion with the user, 2026-11-02. No changes to the document until the discussion ends; then one
revision pass. **Applied in revision 3 (2026-11-02), items 1-5.** Each item: the user's point, the discussion, and the decision (or "open").

## 1. The toy examples are not doing enough work

**User.** Are the toy examples helpful, and if so, are we using them fully? It may be better to pick representative
real objects with representative feature sets and use those throughout. The tables already cite real objects and
feature sets the toys do not include, so the toy feature sets are not carrying their weight.

**Discussion (Claude).**
- The toy container is EMBER in disguise: f4-f8 are EMBER's histogram, entropy, and string features. A disguised PE
  is less honest than a real one, and reviewers recognize real feature sets.
- Proposal: replace the invented formats with *miniature real examples*: one real object per domain and 5-8 real
  features from that domain's real extractor, introduced once in Section 2 and used in every section. Describe each
  object only at the level the model needs (its pieces and what points to them), one paragraph each, to avoid format
  minutiae.
- Using them fully: one concept-by-domain table in Section 3 replaces the scattered "Elsewhere" columns; every
  definition, lemma, and theorem gets one sentence per domain; each domain is chosen to exercise what the others do
  not (PE: pointers, locating positions past the end, element-level edits, hashing, entropy; APK: item-level
  operations, presence and keyed counts, deduplication, Pierazzi et al.'s transplantation side effects; flows: ratios,
  standard deviations, pools, consecutive pairs, timing edits, timeouts that make timestamps locating).

**Decision (user).** Replace the toys with miniature real examples, one per domain, used throughout.

## 2. Commit early to three domains

**User.** Commit early to three kinds of objects (and three feature sets): raw executables (PE), higher-level
containers (APK), and network traffic (flows). Three domains would make a strong contribution and justify a single
main application. The constraint is data: PE and ELF raw files are available from EMBER-2024; APK datasets exist
(e.g., HyperCube); raw PDF datasets are unknown to the user; traffic is unfamiliar but welcome if data exists.

**Discussion (Claude).**
- Agreed for the formalization: committing the examples to three domains costs little. For experiments, separate
  "used as examples in the model" (commit now) from "instantiated and checked" (commit after a feasibility pass per
  domain: raw objects with labels, an open extractor, and an existing attack or hand-written constraints to compare
  against).
- Data checked locally: EMBER-2024's APK and PDF records carry only the format-agnostic groups of the PE feature set
  (histogram, byte entropy, strings, general); the PE groups are empty, and the raw APK/PDF files are not on disk. So
  EMBER-2024 does not give an APK feature set. ELF is raw locally, but it is the same kind of object as PE and has no
  standard feature set: a remark, not a domain.
- APK: raw apps from AndroZoo (academic API key); Drebin as the extractor gives a head-to-head with Pierazzi et al. on
  their own task (side effects of transplantation, which they estimate by re-extraction). Risk: Drebin's features are
  presence bits, so directions are nearly trivial there (Demontis et al. already built monotone Drebin detectors); the
  side-effect result and deduplication carry the domain. A richer APK feature set may be needed (literature check).
- Flows: public captures with raw packets exist (CIC-IDS2017 / CSE-CIC-IDS2018, UNSW-NB15, CTU-13 and other
  Stratosphere botnet captures; the last fit the malware framing). Work on constrained adversarial attacks against
  network detectors writes dependencies between flow features by hand; that is the realistic alternative our model
  replaces, as the hand rules were for PE (to verify in a literature pass). Possibly the strongest second domain for
  the model's value, because its readouts (means, ratios, standard deviations) are non-trivial.
- PDF: raw data exists (Contagio, CIC-Evasive-PDFMal2022, EMBER-2024 hashes via VirusTotal) with a long adversarial
  history (Mimicus, EvadeML, Hidost), but it is a second container; a fallback if APK proves hard.

**Decision (user).** Three domains, emphasized about equally for now: PE (EMBER), APK (Drebin; it and small variants
are what the Android literature uses), and network flows. Revisit later if data is lacking, or if APK/Drebin adds
little beyond PE/EMBER; then a different security domain where adversarial examples are popular may replace it.
Next: light research on adversarial traffic analysis to pick the most widely used feature set and pipeline, whose
features become the flow examples (item 3).

## 3. The flow domain: which feature set and pipeline (light research, 2026-11-02)

Candidates (from a short web search plus papers already in `papers/`; details still to verify in the full texts):
- **CICFlowMeter on CIC-IDS2017 / CSE-CIC-IDS2018.** The most widely used NIDS feature set: about 80 statistics per
  bidirectional flow (duration; packet counts and lengths per direction with total, mean, std, min, max; inter-arrival
  times; flag counts; bytes/s and packets/s; down/up ratio; active/idle times), from raw pcaps, classified per flow by
  random forests, GBDTs, or MLPs. Most adversarial-NIDS work perturbs these features. Known flaws in the tool and the
  labels (Engelen et al., SPW 2021; Liu et al., CNS 2022), with a corrected CICFlowMeter and relabeled data public.
  Mostly not malware (DoS, scans, web attacks), with one botnet class.
- **CTU-13 with Chernikova and Oprea's aggregated features (FENCE).** Botnet versus normal traffic from real malware
  captures (raw pcaps public, Stratosphere). Zeek connection records aggregated per port into 756 features (counts,
  totals, means, ratios, min/max). Used by FENCE, by Simonetto et al. (MoEvA2, in `papers/`), and by Dyrmishi et al.
  (in `papers/`), with **360 hand-written constraints** between features. Those constraints are exactly the
  "realistic alternative" our model would derive automatically, as the hand rules were for PE, and the malware framing
  fits.
- **Kitsune / AfterImage.** Packet-level damped incremental statistics with an autoencoder. The main target of
  problem-space traffic attacks that edit real packets (Han et al., JSAC 2021, "Traffic Manipulator": padding,
  delaying, injecting packets; TANTRA: timing). Its time-decayed statistics stretch the model: a packet's contribution
  depends on the time since it arrived, which challenges A2 (local contributions).

Model fit (all three): items are packets (and consecutive pairs for inter-arrival times, connections for Zeek);
contributions are counts, sizes, squared sizes; readouts are means, standard deviations, ratios, pools, and rates whose
denominator is a duration (a difference of two pools, a new readout shape). Flow boundaries (FIN flags, the 120 s
timeout in CICFlowMeter) make flags and timestamps locating positions.

Claude's recommendation: CICFlowMeter features as the examples in the formalization (most recognizable); CTU-13 with
the FENCE features and its 360 hand-written constraints as the candidate experimental instance and baseline.

**Decision (user).** Adopt the recommendation for now; a deeper pass over the traffic literature comes later.

## Summary for revision 3: the examples

Use miniature real examples from three object types and feature sets throughout the document, in place of the toy
container and toy flow extractor:
- **Windows executables (PE) with EMBER features**;
- **Android apps (APK) with Drebin features**;
- **network traffic (packet captures, bidirectional flows) with CICFlowMeter features**.

Each is introduced once (Section 2), described only at the level the model needs, and carried through every
definition, lemma, and theorem; a concept-by-domain table in Section 3 replaces the scattered "Elsewhere" columns.


## 4. Is there a clean algebraic reading of sum-then-readout?

**User.** Is there a clear relationship between the parts of the extractor definition and ideas from type or group
theory? An earlier draft mentioned monoids. No abstract algebra for its own sake, but a clear connection is worth a
footnote at least.

**Discussion (Claude).** Yes, one connection is clean, and it explains a result rather than decorating it:
- *The sums are a monoid homomorphism.* The sum vector maps a finite multiset of items to a product of commutative
  monoids: $(\mathbb{R}, +)$ for additive sums and $(\mathbb{R}\cup\{-\infty\}, \max)$ for pools. "Local
  contributions" (A2) says exactly that this map is the fold of the per-item contribution $\mathbf{v}$, i.e. the
  unique homomorphism extending $\mathbf{v}$ from single items (the free commutative monoid's universal property).
  Commutativity is why the extractor's loop order does not matter; order-dependent features enter only by making
  ordered pieces items (consecutive packet pairs).
- *Group versus monoid explains Theorem 1's pool clause.* $(\mathbb{R}, +)$ is a group, so removing an item is undone
  by subtracting its contribution, and the new totals follow from the old totals and the delta. $\max$ has no inverse,
  so a removal cannot be undone from the total, and pools need the item table. This is the database distinction
  between aggregates maintainable under deletion and those that are not.
- *Readouts are Gray et al.'s "algebraic" aggregates* (data-cube paper, 1997): a fixed formula over a few
  "distributive" aggregates (sum, count, max), e.g. mean and standard deviation. Their third class, "holistic"
  aggregates (median, quantiles, mode), has no bounded summary, so it falls outside the class. That gives Section 9 a
  crisp, standard statement of where the class ends.
- *The sign analysis* is an abstraction of $(\mathbb{R}, +)$ onto the sign sets with $\boxplus$:
  $\mathrm{sgn}(x+y) \in \mathrm{sgn}(x) \boxplus \mathrm{sgn}(y)$ (abstract interpretation's sign domain). Worth
  one sentence in positioning, not more.
- Type theory adds nothing beyond "items are typed by kind"; group theory beyond inverses adds nothing.

Proposal: one paragraph in Section 3.2 (sums as a homomorphism into commutative monoids; groups allow removal),
reused in Theorem 1's pool clause and in Section 9 (algebraic vs holistic aggregates); the rest in positioning.

**Decision (user).** Adopt the proposal: a short paragraph in Section 3.2, referenced by Theorem 1's pool clause and
Section 9; the sign domain in positioning; no further algebra.

## 5. Section 5 is unintelligible from its lead; Section 6 (and probably the rest) has the same problem

**User.** Sections 3 and 4 have clear purposes. Section 5 loses the reader from its first paragraph; a skim of
Section 6 suggests the same problem, and probably the rest of the document has it.

**Diagnosis (Claude).** Sections 3 and 4 work because each opens with a question the reader already has ("what does
an extractor look like?", "how do we describe an edit?") and answers it with an example. Section 5 breaks that in
five ways:
1. *Conditions before the computation they protect.* Its lead says "the results in Sections 6-8 rest on one premise"
   before the reader has seen any result or knows what we want to compute. Requirements are unmotivated until the
   reader has seen the recipe they guard and how it can go wrong.
2. *Undefined shorthand in the lead:* "items we can find cheaply", "each item's contribution is its own", "kind by
   kind", "say nothing about how an input is laid out", "damage region", "homomorphism".
3. *Labels out of order and without meaning:* A0, A2, A4, then A1, A3, inherited from the old document. The reader
   must remember five codes instead of five ideas.
4. *No example before the abstraction.* The examples come after each property's formal statement, not before it.
5. *Too many new terms at once:* locating position, margin, recognizer, signature, delta, all needed simultaneously.
Section 6 inherits the problem: it opens with "an edit whose item delta is known" and a lemma whose proof depends on
all of Section 5.

**Proposal.** Merge Sections 5 and 6 into one section, "Predicting what an edit does to the features", ordered as
the reader's questions arise:
1. *The goal and the recipe*, in plain words with one worked example per domain. Goal: the edited input's features
   without running the extractor on it. Recipe: (i) list the pieces the edit adds, removes, or changes; (ii) adjust
   the totals by those pieces' contributions; re-apply the formulas.
2. *How the recipe can go wrong*, one concrete failure per requirement, each turned into a named requirement (names
   by meaning, no A-numbers in the body):
   - the recorded totals do not reproduce the extractor -> *faithful recording* (A0);
   - a piece's contribution depends on something else (a library counted once, a size divided by the file size, an
     import overwritten by a later one) -> *self-contained contributions* (A2);
   - the edit writes a field that says where things are (a section table entry, a flow's addresses) -> *complete
     record of structure* (A1);
   - new content merges with its neighbors (a string extended, a packet pair split) -> *changes stay near the edit*
     (A3);
   - the editing tool changes more than it says -> *honest tools* (A4).
3. *The theorem*, stated once the reader knows what each condition is for; the proof in an appendix or after it.
4. *Checking the requirements on a real extractor*, and flagging as the fallback that keeps everything sound.
Apply the same pattern to every section: open with the question in plain words and an example, introduce a term only
when it is needed, state the result, then prove it. Sections 7 and 8 open better (with the question) but need the
same pass on terms (envelope, sign set, signature).

Sample lead for the merged section (to test the style):

> Given a file and an edit, we want the edited file's features without running the extractor on it. The recipe has
> two steps. First, list the pieces the edit adds, removes, or changes: appending `http://evil.example` to a PE file
> adds one string and 19 bytes, and changes nothing else. Second, adjust the totals: the string count rises by one,
> the total string length by 19, and nineteen histogram bins by one each. Re-applying the formulas gives the new
> features. The recipe is only right if both steps are. The first goes wrong if the edit changes pieces we did not
> list: the appended bytes may join a string that ended at the old end of the file, or the edit may overwrite a field
> that says where the sections are, so that the parser now sees different sections. The second goes wrong if a
> piece's contribution depends on more than the piece: if the extractor counted each library once, adding an import
> from a library already present would change nothing, though the recipe adds one. The rest of this section turns each
> way the recipe can fail into a requirement on the extractor, and shows how each is checked.

**What each section was for, and what the merged section is for** (explained to the user, 2026-11-02).
- *Section 5 (revision 2): when the model's predictions can be trusted.* The model predicts by bookkeeping on what it
  recorded from the original input (its pieces, what each adds to the totals, the formulas), never by re-running the
  extractor. Section 5 listed the conditions under which that bookkeeping is right: the record reproduces the
  extractor exactly; each piece's contribution depends only on the piece; we can tell exactly which pieces an edit
  touched (every field that decides where pieces are is recorded, and new content affects only pieces near where it
  is written); and editing tools do only what they declare. It said how each is checked on a real extractor, and that
  a failure is flagged, costing precision but never correctness. It also carried two side jobs: the argument that only
  two conditions depend on the format (the answer to the agnosticism criticism), and the lemma Section 7 needs on
  which pieces a byte-level operation can change.
- *Section 6 (revision 2): exact side effects of one concrete edit.* Given an input and an edit, compute the edited
  input's features from the original's record, without extracting the edited input: first find the pieces the edit
  added, removed, or changed (a lemma), then adjust the totals and re-apply the formulas (Theorem 1). A maximum is the
  exception: it cannot always be updated from its old value, which is why the record keeps every piece. Extended to
  sequences of edits. This is Pierazzi et al.'s side-effect vector, which they call infeasible to compute in advance,
  computed.
- *The merged section: predicting what one edit does, and when the prediction is right.* One question, answered in
  the order a reader asks it: what we want (the edited input's features without re-extraction); how (the two-step
  recipe, worked on one example per domain); when the recipe fails (each concrete failure yields one requirement, so
  the conditions arrive as answers, not unexplained premises); what we can then guarantee (the theorem); and how we
  know a real extractor meets the requirements (the checks, with flagging as the fallback). Same content, new order
  and motivation.

**Care points for the merge.**
- Section 7 (directions over a whole threat model) reuses the same requirements, so the merged section must state
  them clearly enough to be referred back to.
- The two side jobs move out: the format-dependence argument to Section 9 (which already has the "what each result
  needs" table); the lemma on which pieces a byte-level operation can change into Section 7, its only user.

**Decision.** The user is open to it and asked for it to be written up; treat as the plan unless revised: merge Sections 5 and 6 as described, requirements named by meaning (no A-numbers in the
body), and apply the same pattern (question and example first, terms only when needed, result, then proof) to every
section. The user has not yet read past Section 5; the leads of Sections 7-9 still need the user's read.
