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

## §3.3 Edits Given as Writes

### 1. Simulated review
### 2. Proposed changes
### 3. User's feedback on the plan
### 4. Implemented
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
