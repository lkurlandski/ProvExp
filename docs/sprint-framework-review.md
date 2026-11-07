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
- §3.3 could continue §3.2's record-deletion example from Algorithm 1: a deletion that joins two tokens across the
  gap is a write whose effect reaches past the written positions. (from §3.2, session 18)

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
### 6. Classification and plan
### 7-8. Feedback and implementation
### Retro

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
