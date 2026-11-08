# Sprint: self-review of §3.2-3.4 (started 2026-11-06)

**Goal.** The user never reads the current drafts of §3.2-3.4 (they are not worth reading yet). Claude analyzes
each subsection as the user would, improves it (with the user's feedback on the plan only), and the user's first
read is of the improved version. Learning signal: whatever the user still finds there is something Claude's analysis
missed or its revision got wrong. Success: the user's comments on the improved version shrink from §3.2 to §3.4, until
steps 5-8 are unnecessary. §2 and §3.1 are done (session 17).

**Tools.** The reader model `.claude/skills/paper-prose/reader-model.md` (how the user reads; update after every
round), the `paper-prose` lessons (how to write), the reaction log in `docs/writing-spec.md` (raw reactions).
Not `docs/reviews/review-prompt.md`, which simulates a conference reviewer.

## Protocol (one subsection per session; order 3.2, 3.3, 3.4)

1. **Simulated review.** Invoke `/paper-prose`; read the reader model; `make` and read the subsection's rendered
   text (pdftotext and page images) paragraph by paragraph, together with the math sources (`_j_proofs.tex`,
   `docs/formalization.md`). Write the review the user would write, in their format (questions and feedback in text
   order), into this log under "1. Simulated review". Number each predicted comment (P1, P2, ...) and mark it
   **Q** (question), **F** (feedback), or **M** (mechanics), with a confidence H/M/L. Answer the predicted questions
   in plain words in the same place.
2. **Proposed changes.** A numbered plan in the chat (one item per predicted comment or group, the concrete change,
   one recommendation, ripples into other subsections, open questions last). Copy it into the log.
3. **The user's feedback on the plan.** Record per item: accepted / changed / rejected, with the reason. Rejected
   items are false alarms.
4. **Implement.** One pass; `make`, `make check`, "??" check, read the rendered text; commit; point the user to the
   passages that are new prose.
5. **The user's first read**, of the improved version only (never the old draft). Paste the comments verbatim.
6. **Classify, then plan.** Each user comment is a residual defect; classify it by cause: **missed** (in the old
   draft, and step 1 did not flag it), **fix fell short** (flagged in step 1, but the revision did not resolve it),
   **introduced** (the revision created it), or **new taste** (no trigger in the reader model could have predicted
   it). Rejections in step 3 are **false alarms**. For each, one line on what the reader model or the lessons
   should have said. Then the usual numbered plan.
7. **The user's feedback on that plan.**
8. **Implement**, as in step 4.

**Retro (end of each subsection).** In this log: the counts per class and their severity, what worked, what to
change. Then: missed and new taste -> new or sharpened triggers in the reader model; fix fell short and introduced ->
lessons in `paper-prose` (how to write the fix); false alarms -> weaken or delete triggers; the calibration row in the reader
model; writing lessons -> `paper-prose`; reactions -> the reaction log; `docs/status.md` and `docs/resume-prompt.md`.
Commit in logical pieces.

**Ripples.** Changes in one subsection that another subsection must absorb go in the "Ripples" list below, not into
the other subsection early; each is handled in its own subsection's session (step 2).

## Ripples

- §3.2's first paragraph says the edited input's features are found "without extracting them"; align with the §3
  lead ("before the edit is applied"; readouts are evaluated again). (from §3.1, session 17; handled in §3.2 plan item 1)
- §3.3's first sentence ("Many transformations are given by the elements they write ...") answered §3.2's stranded
  pointer paragraph, which the §3.2 plan removes; check that §3.3 still opens well. (from §3.2, session 18)
- (withdrawn: §3.2 no longer has the record-deletion example.)
- §3.3 states where a delta comes from (item-stated edits give it by their definition; writes need §3.3); §3.2 no
  longer says it. (from §3.2 round 2, session 18)
- §3.4 makes the "sign from the kinds alone" argument itself; §3.2's closer that previewed it is cut. (from §3.2
  round 2, session 18)
- Framework-wide: decide whether to drop residual features (U10), after §3.4.
- §3.4 can cite Lemma 1(iii) (a fixed layout only replaces items) for its "replace" sort; the reference to the old
  Lemma 1(b) is now (ii). (from §3.3, session 19)
- §4 (research track's file) says "locating positions" for what §3 calls structure positions. (from §3.3, session 19)

## §3.2 Edits and Their Side Effects

### 1. Simulated review

Session 18 (2026-11-07). Read in the rendered PDF (pages 3-4), with the proof (`_j_proofs.tex`) and the approved spine
(`docs/framework-design.md` §12). Math checked: Prop 1 and its proof agree; (ii) is right (the table lists every item of
$\pi(z)$, so the rows of $B$ are found by removing rows that match $I^-$ by kind and content). Main finding before the
comments: the draft lost the spine's ¶1 (why not re-extract), which the user asked for by name on 2026-11-05, and the
"why" now sits in fragments in the last two paragraphs.

**Lead (2 sentences)**
- **P1 F (H).** Too abrupt an entry, and it still does not say why we would avoid re-extraction, the comment of
  2026-11-05. "Without extracting them" is loose: the readouts are evaluated again (the Ripples item; the §3 lead now
  says "before the edit is applied").
- **P2 Q (L).** "$T \in \mathcal{T}$": must the edit be valid for the result to hold? *Answer:* no; Prop 1 holds for any
  pair $(z, z')$. Validity matters only for the threat models of §3.4.

**Def 6.** No comment expected (called "really good" on 2026-11-05).

**¶ after Def 6**
- **P3 F (H).** "Positions still matter in two ways:" is an announced count with a colon reveal, and "such as an offset
  in a table entry" is a format detail with nothing to picture (which table?).
- **P4 Q (M).** "A delta need not be the smallest one": the smallest one is never defined, and why tell me this?
  *Answer:* an edit has several deltas (list an unchanged item as both removed and added), Prop 1 holds for each, and
  §3.3's lemma produces deltas that are not the smallest. The sentence should say that it is there for this reason.

**¶ "Many transformations are stated by the items they change"**
- **P5 F (H).** Abstraction with nothing to picture: which transformations? Still no example of an edit and its
  delta, although Algorithm 1 is right there. A two-sentence paragraph stranded between the gloss and the proposition.

**Prop 1**
- **P6 F (M).** Dense: a preamble with two equations, "and therefore:", and three parts in one run-on block (the
  "extremely dense" comment of 2026-11-05 in a milder form).
- **P7 Q (M).** Part (i) adds and subtracts $\mathbf{s}(z)$, but §3.1 says the sums "do not form a vector": what do
  $+$ and $-$ mean here? *Answer:* on the additive sums only, sum by sum, where values are real numbers. Write it per
  sum $k$.
- **P8 Q (M).** The title is "Exact side effects", yet $\boldsymbol{\eta}$ is not in the statement; where are the side
  effects? *Answer:* the proposition gives $\varphi(z')$ exactly, so $\boldsymbol{\eta} = \varphi(z') - \varphi(z) -
  \boldsymbol{\delta}^*$ is exact; the text says so two paragraphs later. Say it in the sentence right after.
- **P9 Q (L).** The delta is defined for a pair $(z, z')$; how can the edit "need not even be applied"? *Answer:* the
  computation uses only the item table of $z$ and the delta; $z'$ must exist, not be built, and an edit stated in items
  gives its delta from $z$ by its definition.
- **P10 M (L).** "a sum that $\rho_j$ reads": use the defined term (a sum in its support $K_j$).

**¶ "In words"**
- **P11 Q (M).** "The delta rule of incremental view maintenance": what is that? A cited idea compressed into a
  name. *Answer:* a database keeps an aggregate over a table and updates it from the inserted and deleted rows instead
  of recomputing it; part (i) is that update.
- **P12 F (L).** The 5-and-3 example reads like a puzzle; it could be Algorithm 1's \textit{largest} on a concrete
  edit.
- **P13 M (L).** $B$ is any multiset in Def 3 and the kept items in Prop 1.

**¶ "The result is exact"**
- **P14 F (M).** "Nothing is extracted from $z'$" (the readouts are evaluated), "an edit usually changes few items"
  (vague, and appending much content changes many). The $\boldsymbol{\eta}$ sentence, which ties the result to §2,
  comes late.

**¶ last ("The same reasoning applies")**
- **P15 F (M).** "The same reasoning" is vague, and the paragraph reads as a teaser closer, though it states the real
  reason for the arithmetic form (edits whose contents are unknown, §3.4). That reason belongs in the motivation.

### 2. Proposed changes

Structure: the spine of 2026-11-05 (§12 of `docs/framework-design.md`) is sound; the draft drifted from it (lost ¶1 and
the example). Revise from the spine, not by patching: motivation, Def 6, gloss, example, Prop 1, explanation, exactness
and side effects, closer.

1. (P1, P15) **New ¶1, motivation.** The standard way to find an edit's side effects is to apply it and extract the
   features of $z'$ (§2); it is exact, and §5 uses it as ground truth. It gives the difference but not which part of
   the edit caused it, and it needs $z'$, so it says nothing about the edits one operation of a threat model allows,
   whose contents are unknown (§3.4). Then the plan of the subsection in one sentence: describe the edit by the items
   it removes and adds, and compute the new sums from the item table of $z$ by arithmetic, evaluating again only the
   readouts whose support changed. Replaces "without extracting them" (Ripples).
2. (P3, P4) **Gloss after Def 6.** Keep the positions idea (an item that moves is in neither part; a changed content
   is one removal and one addition; the features lose nothing). Replace "in two ways:" and the table-entry example by
   plain sentences: a position can itself be content (an item may hold the location of another), and the positions an
   edit writes decide which items the extractor finds, the subject of §3.3. The smallest-delta sentence becomes: an edit
   has several deltas, and Prop 1 holds for each of them.
3. (P5) **Example from Algorithm 1**, replacing the stranded two-sentence paragraph. Transformations are often stated
   by the items they change, and their definitions give the delta. Example: delete the record of length 5 from an input
   whose records have lengths 5 and 3. $I^-$ holds that record, its five element items, and its tokens; $I^+$ is empty.
   Every later item moves but keeps its content, so it is in neither part. One clause: this assumes tokens lie inside
   records, so that the deletion cannot join two of them; §3.3 treats edits where it can. Generic, no domain.
4. (P6, P7, P10, P13) **Prop 1 restated.** Preamble as now; then (i) per additive sum $k$:
   $s_k(z') = s_k(z) + \sigma(I^+)_k - \sigma(I^-)_k$; (ii) per pool $k$: $s_k(z') = \sigma(B \uplus I^+)_k$, given by
   the item table and the delta, not in general by $s_k(z)$ and the delta; (iii) "a sum in its support $K_j$". Displayed
   as a short list inside the proposition. Keep $B$ (one-letter clash with Def 3 is harmless there; renaming Def 3's
   generic multiset to $A$ is the alternative, recommended against since §3.1 is accepted).
5. (P8, P11, P12) **Explanation after Prop 1.** First sentence as now ("the old sums with the contributions of the
   removed items taken out and those of the added items put in"), then the side effects: $\boldsymbol{\eta}$ is exact on
   the modeled features. Why it holds, plainly. IVM glossed in one clause (a database updates a stored total from the
   inserted and deleted rows instead of recomputing it). The pool case on the example: \textit{largest} was 5; after
   the deletion the item table says the remaining record has length 3, which the old value 5 could not tell, since an
   input with records 5 and 5 has the same \textit{largest} and keeps 5.
6. (P9, P14) **Exactness paragraph.** Why exact (the class is defined by this computation; kept). What is computed:
   the sums the delta reaches and the readouts whose support contains one of them; nothing is extracted from $z'$, and
   for an edit stated in items $z'$ need not be built. Cost hint without "usually": the update touches only those sums
   and readouts, so it can be cheaper than extraction. Residual features: one clause.
7. (P15) **Closer, literal.** Part (i) writes the change of an additive sum as a total over the delta's
   contributions, so knowing only the kinds of the items an edit adds bounds its sign: adding items cannot lower a
   count. §3.4 makes this its method for a threat model's operations. Two sentences.
8. (P2) "$T \in \mathcal{T}$" -> "a transformation $T$": validity enters in §3.4. (low priority; skip if you prefer.)

Ripples (added below): §3.3's first sentence repeats the pointer that item 3 removes from §3.2; §3.3 can continue the
record-deletion example (a deletion that joins two tokens is exactly a write near a margin).

Open questions:
- Q1. The Algorithm 1 example (item 3, item 5): you cut the earlier toy example on 2026-11-05, but lesson 20 (revised
  2026-11-06) allows a generic one. Recommended: include it, about five sentences in total, generic records and tokens
  only.
- Q2. Length: the revision runs about 900-1,000 words against the spine's 700 (the current draft is ~650). Recommended:
  accept while drafting.
### 3. User's feedback on the plan

All eight items approved as proposed (2026-11-07). Q1: yes, referencing Algorithm 1 is "the encouraged way to provide
a concrete example". Q2: accept the length; trim later. No false alarms.

### 4. Implemented

2026-11-07, one pass (`_d_framework.tex`), ~650 -> ~990 words. New prose: ¶1 (motivation), the example paragraph
(deleting a record), Prop 1's list, the paragraph "In the example" (x1, the pool), and the closer. Rewritten: the
positions sentences after Def 6, the exactness paragraph. Kept: Def 6, the "In words" opening, IVM citations (now
glossed). `make check`: no undefined refs; one 1.7pt overfull vbox on the last appendix page (page-break shift, not
in §3.2). No "??".

### 5. User's first read

2026-11-07 (verbatim in the session; condensed here, one line per comment, U1-U18).
- U1 ¶1: long and unfocused, references past and future parts without reason; fails to introduce or summarize.
- U2 Def 6: "quite good"; the user added a gloss of $\uplus$ by hand.
- U3 ¶2: when, where, and why positions matter is confusing; reads as admitting a significant limitation with no
  consolidation; three sentences for one point.
- U4 ¶2: "an edit can have several deltas" is obvious, its reason is not visibly connected to it; value unclear.
- U5 ¶3: the first sentence reads oddly.
- U6 ¶3: the example reads oddly and is probably unnecessary; the concept is simple.
- U7 ¶3: "no idea" what the tokens-inside-records caveat means.
- U8 ¶3: no need for the forward reference to §3.3.
- U9 Prop 1: abrupt; the paragraph before does nothing to lead into it, and ¶1 did not outline the subsection.
- U10 Prop 1: consider dropping residual features from the framework altogether (fewer "over J", "modeled"); decide
  after reading the whole framework; note only.
- U11 Prop 1: do (i)-(iii) follow from the decomposition? "In particular" is a poor transition.
- U12 Prop 1 (ii): the second half ("which the item table ... determine, but ...") is unclear; important or word salad?
- U13 ¶4: not clear how the proposition gives exact side effects.
- U14 ¶4: the plain-language explanation undersells the exactness.
- U15 ¶4: justify (i), (ii), (iii) in order; the databases remark is "really cool" but interferes where it is.
- U16 ¶4: does three jobs (summary, side effects, correctness); reorganize.
- U17 ¶5: the example fails; §3.1 needed one to picture the extractor, here the math is self-explanatory.
- U18 ¶6-7: jump back to side effects and to part (i); "gobbledygook"; written without a plan; every paragraph needs a
  reason to exist.

### 6. Classification and plan

| Comment | Class | What the reader model or lessons should have said |
|---|---|---|
| U1 | introduced | Lesson 27 already says a lead has at most one pointer; plan item 1 added three (§2, §5, §3.4). |
| U2 | missed (M) | Lesson 31: every operator gets a sentence; $\uplus$ had none. |
| U3 | fell short | P3 fixed the staging but kept three sentences; new trigger: a passage that reads as a concession must say how the framework handles it. |
| U4 | fell short | P4 flagged it; the fix gave a reason instead of cutting. Prop 1 already says "a delta"; the sentence served only §3.3. |
| U5 | fell short | P5 flagged the stranded paragraph; its first sentence survived as the example's opener. |
| U6, U17 | introduced / new taste | Plan items 3 and 5. An example earns its place where the reader cannot picture the structure (§3.1), not for arithmetic the reader can follow. Revise lesson 20 and trigger 8. |
| U7 | introduced | A caveat needed only to keep the example correct; it shows the example cost more than it gave. |
| U8 | introduced | Same as U1. |
| U9 | missed | New trigger: a formal statement needs a lead-in sentence that sets up its first equation. |
| U10 | design note | Framework-wide; recorded below, decide after §3.4. |
| U11 | missed | "In particular" for parts that are consequences, not special cases; the statement did not show how they follow. |
| U12 | missed | A negative claim ("but not from ...") inside a statement; it belongs in the explanation, with its reason (why the table keeps every item). |
| U13, U14 | fell short | P8 moved $\boldsymbol{\eta}$ up but never said why exact equals what the extractor computes. |
| U15, U16 | fell short | P11 glossed IVM inside the proof sketch; no paragraph plan, so one paragraph did three jobs. |
| U18 | introduced | Plan items 6-7 rewrote paragraphs without a paragraph spine (procedure step 1 skipped for a revision). |

Totals: missed 4, fell short 6, introduced 6 (U6/U17 also new taste), design note 1. Severity: the structural ones (U1,
U9, U16, U18) dominate. Main cause: the revision was planned per comment, not per paragraph, so it added material
(motivation tour, example, closer) without a spine.

**Answers to the user's questions.**
- U4: an edit has several deltas because an unchanged item can be put in both $I^-$ and $I^+$ and cancel. The sentence
  existed because §3.3's lemma produces such deltas (it removes and re-adds every item near a write, changed or not).
  Prop 1 already says "let $(I^-, I^+)$ be *a* delta", so nothing needs the sentence. Cut.
- U11: yes. (i): on an additive sum, subtract the removed items' contribution from the first decomposition and add the
  added items' (both are real numbers there). (ii): the second decomposition read on a pool. (iii): Definition 5 for
  $z'$; then Definition 4: a readout sees only its support.
- U12: it says that a pool's new value can be computed from the list of individual contributions (the item table) but
  not from the old pool value alone. It matters, because it is why the item table stores every item rather than only
  the totals, but it is a remark, not part of the result: move it to the explanation of (ii).
- U13: $\boldsymbol{\eta} = \varphi(z') - \varphi(z) - \boldsymbol{\delta}^*$; $\varphi(z)$ is known and
  $\boldsymbol{\delta}^*$ is the attacker's target, so $\boldsymbol{\eta}$ is exact wherever $\varphi(z')$ is. Part
  (iii) gives $\varphi_j(z')$ as the value the extractor itself returns, because a modeled feature is *defined* as the
  readout of the folded contributions (Def 5): updating the sums folds the same contributions in another order.

**Plan: a paragraph spine for §3.2 (six paragraphs, no example).**
1. (U1) ¶1, two to three sentences, no pointers: what an edit is; side effects are usually found by applying the edit
   and extracting the features of $z'$; this subsection defines the delta (the items removed and added), proves that
   the delta and the item table of $z$ give the sums and modeled features of $z'$ exactly, and with them the side
   effects, before the edit is applied.
2. (U2) Def 6 with the user's gloss of $\uplus$ (rewrapped only).
3. (U3, U4, U5-U8) ¶2, one point: a delta keeps kinds and contents and forgets positions, and the features lose nothing,
   since positions reach them only through items: a stored position is content, and a write that changes which items
   exist changes $\pi(z)$, so both appear in the delta. Cut the several-deltas sentence, the example paragraph, and
   the forward reference.
4. (U9) Lead-in to Prop 1, one or two sentences (end of ¶2 or its own short paragraph): the kept items contribute the
   same to $z$ and $z'$ and the fold ignores order, so the sums of either input are the fold of the kept items combined
   with the removed or the added ones.
5. (U11, U12) Prop 1: the two decompositions, then "Consequently," (i) per additive sum; (ii) per pool,
   $s_k(z') = \sigma(B \uplus I^+)_k$, the largest (smallest) contribution of the kept and added items; (iii) as now.
   The negative claim leaves the statement.
6. (U15, U16) ¶3, why it holds, in the order (i), (ii), (iii): decompositions; subtraction; a pool's old value does not
   say what remains ({5, 3} and {5, 5}, one clause), so recompute from the item table, which is why the table keeps
   every item, and only additions update from the old value; readouts see only their support.
7. (U13, U14) ¶4, exact side effects: $\boldsymbol{\eta}$ from $\varphi(z')$; why the value equals the extractor's
   own (same contributions, folded in another order); (iii) also says which features can have side effects at all;
   residual features: one clause.
8. (U15, U18) ¶5, cost, with the databases remark: the update needs only the item table and the delta and touches only
   the sums a delta item contributes to and the features that read them, so it can be cheaper than extraction;
   databases keep stored totals current the same way, from inserted and deleted rows (incremental view maintenance).
   Old ¶5-7 cut.

Ripples: §3.4 must make the "sign from the kinds alone" argument itself (the old closer is cut); §3.3 states where a
delta comes from (item-stated edits give it by definition, writes need §3.3), since §3.2 no longer says it. The
record-deletion ripple is withdrawn.

**Framework-wide note (U10, decide after §3.4):** drop residual features from the framework (assume every feature is
modeled; handle the residual ones in §4/§5 as an implementation matter), which would remove "over $J$", "modeled",
and the residual clauses from Def 5, Prop 1, and §3.3-3.4.

### 7-8. Feedback and implementation

2026-11-08. Plan approved as proposed; Q1 as recommended (the lead-in to Prop 1 is its own short paragraph). The user
doubted the {5, 3} example ("no need to show how max and min behave with real numbers"; left to Claude): replaced by
one sentence in words (the old maximum does not say whether a removed item held it, nor which contribution remains
largest). Implemented in one pass from the six-paragraph spine; ~990 -> ~820 words. New prose: ¶1, ¶2 (positions as a
strength), the lead-in paragraph, Prop 1's consequences, the why-it-holds paragraph, the exact-side-effects paragraph,
the cost paragraph with incremental view maintenance. `make check`: no undefined refs; the 1.4pt overfull vbox is on the
ethics/open-science page.

### Retro

- Counts (round 1 residuals): missed 4, fell short 6, introduced 6, new taste 1, design note 1; false alarms 0 (all 8
  plan items approved). The step-1 review found real problems (P1, P3-P5, P8, P11 all recurred in the user's read) but
  the fixes were planned per comment, not per paragraph, so the revision added unplanned paragraphs (the pointer-tour
  lead, the example, two closers) that produced six new defects.
- What worked in round 2: a paragraph spine in the plan, each paragraph with one job; answering the questions in
  words before planning.
- Change: a revision plan is a paragraph spine (one line per paragraph, its single job), never a list of per-comment
  patches; any paragraph the plan adds must name its job. Examples only where the reader cannot picture the structure.
- Reader model: triggers 8 (revised), 23-27 (new); calibration row added. `paper-prose`: lessons 20 (revised), 32-33.
- Verdict on round 2 (2026-11-08): "quite satisfied". The user's own small edits (`5dcb9e7`): a shorter lead, "In other
  words" cut, "the largest or smallest" for the longer min-pool phrase, Prop 1's decompositions numbered. §3.2 closed
  after one residual round (goal for §3.3: fewer residual comments, none of class "introduced").

## §3.3 Edits Given as Writes

### 1. Simulated review

Session 19 (2026-11-08). Read in the rendered PDF (pages 4-5, ~1,100 words against the spine's 500-800), with the
proof (`_j_proofs.tex`), the spine (`docs/framework-design.md` §13), and what later text uses: §3.4 cites
Lemma 1(b) for signatures and the flagged case ("that kind may be added, removed, and replaced with any content");
its "replace" sort is what a fixed layout gives, though §3.4 never says so; §4 (research track) still says "locating
positions" for structure positions. Math: Lemma 1 and its proof agree; two gaps. (1) The lemma opens "Let $\tau$ be a
local kind" and then makes a claim about every kind, which needs every kind local. (2) The last paragraph compares
$W$ "with the structure positions in the item table", but §3.1's item table holds kinds, members, and contributions
only. Main finding before the comments: §3.3 never says why a write-given single edit needs the lemma when $z'$ is at
hand (extract it), so its motivation stands only on the family case, and the "before the edit is applied" claim of
the §3 lead is never earned (the elements of $z'$ on a margin are those of $z$ plus the written ones, but the text
does not say so).

**¶1 (lead)**
- **P1 Q (H).** "For one such edit, the edited input $z'$ is at hand, but Proposition 1 needs its delta": if $z'$ is
  at hand, why not extract it and compare $\pi(z)$ with $\pi(z')$? *Answer:* one could; that is the re-extraction
  §3.2 avoids. The lemma's gains for a single edit are that $z'$ need not be built (its elements on a margin are those
  of $z$ with the written values) and that only the margins are read again. The essential case is the family (any
  content written within a region), for which there is no $z'$ and §3.4 needs the bound.
- **P2 F (H).** "Given by the elements they write, not by the items they change": nothing to picture, and "the items
  they change" answers a §3.2 paragraph that no longer exists (Ripples). The reader has never been told that some
  edits come with their delta (an edit stated in items) and others do not.
- **P3 F (M).** "Which enters through two sets of positions per kind that the instrumentation provides": a teaser for
  objects not yet defined; the format sentence also repeats §3.1 ("Only the item map depends on the format").

**¶2 (written set)**
- **P4 Q (L).** Why tell me that an insertion's written set runs to the end? *Answer:* such an edit almost always
  writes a structure position, so it is handled by its delta (last paragraph); the connection is not made.

**¶3 (three ways)**
- **P5 F (M).** Good motivation, but the end does not say which set serves which purpose ("one set of positions for
  each purpose"), and "lies within" is defined in the paragraph's last sentence, away from where it is used.
- **P6 Q (M).** "Reads to decide where items lie": is this the locating positions / identity again? *Answer:* the
  same intuition, but Def 7 does not define structure positions by what the extractor reads; it defines them by the
  guarantee (a write that misses them changes items only near it). The text should keep that distinction visible.

**Def 7**
- **P7 F (H).** One sentence of ~110 words stacking three objects (structure positions, margin, fixed layout), three
  requirements on the margin, and two conditions inline: the "wet clay" / "unhinged rant" pattern in a milder form
  (triggers 10, 14).
- **P8 Q (M).** "Depend only on the elements of $z'$ on the margin": what does depend mean? *Answer:* reading the
  margin of $z'$ finds them; any two edited inputs that agree on the margin have the same items of the kind there.
- **P9 Q (M).** "Computable from $z$ and $W$": why say it, and computable by whom? *Answer:* the notation
  $\mu_\tau(z, W)$ already makes it a function of $z$ and $W$ (not of $z'$), which is what the lemma needs; "computable"
  is a software property (trigger 20). Cut.
- **P10 Q (M).** Fixed layout: what is it for? Its purpose is never given, and in Lemma 1(b) it yields only "keeps
  the number of items", which is obvious from "same members". *Answer:* what §3.4 needs is that such a kind is only
  *replaced* (each item by one with the same members): the "replace" sort, which keeps a count fixed.

**¶ after Def 7 (margins)**
- **P11 F (M).** Several jobs (interpret $L$ and $\mu$, three cases, a citation, an exception); "usually" with no
  criterion; "damage regions that incremental parsers re-parse" is a cited idea compressed into a name (trigger 5;
  the IVM remark of §3.2 was liked once glossed).
- **P12 Q (M).** "Data that runs to the end of the input ... its margin contains it": what data, and contains what?
  *Answer:* an item whose members run to the last element (everything after the last field). A write past the old
  end changes its members, so the margin must contain the whole item; it has no fixed layout under appending.

**¶ "Every kind is local if all positions ..."**
- **P13 F (H).** Reads as a concession with no consolidation (trigger 24), and "just as every extractor is a
  sum-then-readout extractor if the whole input is a single item" points to Remark 1, which §3.1 no longer has. "A kind
  whose items the instrumentation cannot find again from a margin keeps its members among its structure positions" is
  hard to parse. *Consolidation:* no kind is excluded; a larger $L$ only means more edits are flagged, never a wrong
  delta.

**Lemma 1**
- **P14 F (H).** Abrupt: the sentence before it is the trivial-case remark, not a lead-in (trigger 25).
- **P15 F (H).** Dense: (a) holds three sentences, a second hypothesis in the middle ("If $W$ misses the structure
  positions of every kind"), and a remark ("members included"); (b) switches to a family. The accepted Prop 1 format
  (main claim, then "Consequently" with a short list) would fit.
- **P16 M (M).** "Let $\tau$ be a local kind" and then "every kind": needs every kind local (math gap 1).

**¶ after Lemma 1 (why it holds)**
- **P17 Q (M).** Is the lemma anything but Def 7 restated? *Answer:* the first claim is the definition read on one
  edit; the lemma's content is the delta, the item table of $z'$ from the margins only, and the family bound. The
  format-specific work is in meeting Def 7, which the instrumentation must do per kind. Say so plainly. Also "no item
  can reach across the margin's edge" is the runs intuition, not the general reason.

**¶ "Part (a) gives the delta ..."**
- **P18 F (H).** "This delta need not be the smallest ... Prop 1 does not need it to be": the U4 comment of §3.2
  ("obvious; its reason not visibly connected"). Prop 1 already takes any delta. Cut.
- **P19 M (L).** Pointer to §3.4 at the end: one is fine.

**¶ last (edits outside the lemma)**
- **P20 Q (H).** "As an edit stated in items does": where were these defined? §3.2 no longer says (Ripples). Answer:
  an edit stated by the items it adds and removes (add a record with this content) has its delta by its definition.
- **P21 F (M).** Several jobs (what goes wrong, delta-given edits, chaining, flagging, "takes no judgment", the
  population pointer). "Takes no judgment" defends against an unstated objection (trigger 11/20). The population
  sentence repeats what §3.4's second paragraph says.
- **P22 M (M).** "The structure positions in the item table": the item table has none (math gap 2); say the
  instrumentation records $L_\tau(z)$ with it.

### 2. Proposed changes

What §3.3 is for, plainly: an edit stated in items comes with its delta; an edit given as writes does not, and a
family of writes (any content within a region) has no single edited input. §3.3 gives two sets of positions per kind
under which the delta of a write can be read near the write, without building $z'$, and a family's possible deltas
bounded from the item table of $z$ alone; §3.4 needs the second. The structure stays (motivation, written set, idea,
Def 7, what it covers, Lemma 1, why, what it gives, what falls outside), but every paragraph is rewritten from this
spine, the concession moves into the last paragraph, and the lemma takes Prop 1's format. Target ~850-950 words.

Spine (one job per paragraph):
1. (P1-P3, Ripples) **Lead: where deltas come from and what §3.3 proves.** An edit stated in items (add an item
   with given content, remove one) has its delta by its definition. Many edits are given as writes: overwrite some
   elements, append, insert. For one of them the delta could be found by building $z'$ and extracting it, and for a
   family of writes there is no single $z'$. This subsection gives conditions on each kind under which the delta of a
   write follows from the item table of $z$, the positions written, and the written elements, and the deltas of a
   family are bounded from the item table alone. No format sentence, no teaser.
2. (P4) **Written set.** Definition of $W$ as now; then: the elements of $z'$ are the written ones on $W$ and those
   of $z$ elsewhere, so $z'$ is known at any position without being built. Overwriting and appending have small
   written sets; an insertion's runs to the end of the input.
3. (P5, P6) **The idea before the definition.** The three ways a write changes the items of a kind, as now, ending
   with what each set is for: the structure positions are those a write must miss, and the margin is the region
   around the write outside which the items stay as they were and inside which the elements of $z'$ decide them.
4. (P7-P9) **Def 7, split.** Structure positions $L_\tau(z)$ and the margin $\mu_\tau(z, W)$ (contains $W$ and the
   members of the items $W$ meets, grows with $W$; "computable" cut); "lies within" defined here; the two conditions
   displayed as a short list (as in Prop 1), (ii) worded as "are the items that the elements of $z'$ on the margin
   determine". Fixed layout leaves the definition (moves to ¶5).
5. (P10-P12, P8) **What the definition covers (breadth).** Opens with condition (ii) in words (reading the margin
   of $z'$ again finds the items there), then the usual ways to find items: through fields ($L$ = the fields read
   to find the items; margin $W$ plus the items it meets; their members never change, which we call a *fixed
   layout*); maximal runs (margin to the nearest unwritten element outside the class); windows ($n - 1$ each side);
   these are the regions an incremental parser re-reads after an edit~\cite{wagner1998efficient}, glossed in a
   clause; an item that runs to the end of the input, whose margin contains the whole item once a write reaches past
   the old end. "Usually" cut.
6. (P14) **Lead-in to Lemma 1**, one or two sentences: a write that misses a kind's structure positions splits its
   items into those outside the margin, which it keeps, and those inside, which the margin of $z'$ decides.
7. (P15, P16, P10) **Lemma 1, Prop 1's format.** Main claim per kind: the items of kind $\tau$ of $z'$ are those of
   $z$ with the items within the margin replaced by the ones the margin of $z'$ determines. Consequently, (i) if every
   kind is local and $W$ misses every $L_\tau(z)$, the replaced items and their replacements form a delta, found with
   the members of the replacements from the item table of $z$, $W$, and the written elements; (ii) every edit of a
   family that writes only within $\hat{W}$, which misses $L_\tau(z)$, removes and adds only items of kind $\tau$
   within $\mu_\tau(z, \hat{W})$; (iii) if the kind has a fixed layout, such an edit only replaces items of the kind,
   each by one with the same members.
8. (P17) **Why it holds, in order.** The main claim is Def 7 read on one edit (with the reason contents outside are
   unchanged); (i) margins depend on $z$ and $W$ only, the item table gives the replaced items, and the elements of
   $z'$ on a margin are known from ¶2, so the kind's item finder runs on the margin without building $z'$; (ii)
   margins grow with $W$; (iii) same members. One sentence that the format enters only through meeting Def 7.
9. (P18, P19) **What it gives.** For a single write, the delta and the members of the new items, so the item table
   stays current and a sequence of writes is followed one edit at a time; for a family, a bound that needs neither the
   content of the writes nor any edited input, which §3.4 turns into directions. The smallest-delta sentence cut.
10. (P13, P20-P22) **Writes outside the lemma, with the consolidation.** A write that meets $L_\tau(z)$ can change
    the kind's items anywhere (the lemma still holds for the other kinds). It is handled when the edit is stated in
    items, which then also states the members of the items it adds; otherwise it is flagged and the kind may change
    arbitrarily. The flag compares $W$ with the structure positions, which the instrumentation records with the item
    table. No kind is excluded by Def 7: a kind whose items cannot be found again from a margin puts its members into
    $L_\tau$, so every write to it is flagged; a large $L$ costs flags, never a wrong delta. The Remark 1 analogy, "takes
    no judgment", and the population sentence are cut (§3.4 says the latter).

Proofs appendix: rewritten to the new lemma parts (main claim, (i)-(iii)); (iii) one line.

Ripples: §3.4 cites Lemma 1(b) (line "Lemma~\ref{lem:fw:localization}(b) gives a signature"); the reference becomes
(ii) in this pass so nothing breaks, and §3.4's own session can cite (iii) for its "replace" sort. §4 (research track,
not edited here) calls structure positions "locating positions": a note for the user.

Open questions:
- Q1. Fixed layout moves out of Def 7 into the cases paragraph (where fields motivate it), and the lemma's clause
  becomes "only replaces items, each by one with the same members" instead of "keeps the number of items".
  Recommended: yes (it is what §3.4's replace sort needs, and the count follows).
- Q2. Lemma 1 relabelled from (a)/(b) to a main claim and (i)-(iii), in the format the user accepted for Prop 1.
  Recommended: yes.
### 3. User's feedback on the plan

2026-11-08. Plan approved as proposed ("seems reasonable"; the user has not read the subsection, so could say little
about the plan). Q1 and Q2 as recommended. No false alarms recorded (no item was judged).

### 4. Implemented

2026-11-08, one pass from the ten-paragraph spine (`_d_framework.tex`, proof in `_j_proofs.tex`, §3.4's reference
to Lemma 1(b) changed to (ii)). Length: ~1,230 -> ~1,560 rendered words, over the plan's 850-950 (the lead, the
why-it-holds paragraph, and Lemma 1's list grew); not trimmed, per the drafting rule. New prose: the lead (edits
stated in items vs writes, the family case); the sentence that $z'$ is known on any positions without being built;
the end of the three-ways paragraph (what each set is for); Def 7 split with a displayed list and "lies within"
inside it; the cases paragraph (opens with condition (ii) in words, fixed layout defined at the fields case,
incremental parsing glossed, the end-of-input item); the lead-in to Lemma 1; Lemma 1 as a main claim and (i)-(iii);
the why-it-holds paragraph; the last paragraph (flagging, the item-table gap fixed, the consolidation that no kind is
excluded). Cut: "computable", "usually", the Remark 1 analogy, the smallest-delta sentence, "takes no judgment", the
population sentence. `make check`: clean; no "??".
### 5. User's first read
### 6. Classification and plan
### 7-8. Feedback and implementation
### Retro

## §3.4 Sound Directions

### 1. Simulated review
### 2. Proposed changes
### 3. User's feedback on the plan
### 4. Implemented
### 5. User's first read
### 6. Classification and plan
### 7-8. Feedback and implementation
### Retro

## Sprint retro
