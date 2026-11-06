# Sprint: self-review of §3.2-3.4 (started 2026-11-06)

**Goal.** Learn to do the user's analysis before they read: for each subsection, Claude reviews the draft as the
user would, proposes changes, implements them, and is then scored against the user's own review. Success: by §3.4,
the user's review (steps 5-8) finds nothing that needs another round. §2 and §3.1 are done (session 17).

**Tools.** The reader model `.claude/skills/paper-prose/reader-model.md` (how the user reads; update after every
scored round), the `paper-prose` lessons (how to write), the reaction log in `docs/writing-spec.md` (raw reactions).
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
   items are false alarms for scoring.
4. **Implement.** One pass; `make`, `make check`, "??" check, read the rendered text; commit; point the user to the
   passages that are new prose.
5. **The user's independent review.** The user reviews the revised subsection without reading step 1 first. Paste
   it into the log verbatim.
6. **Score, then plan.** Match each user comment to a prediction: **hit** (predicted, same point), **partial** (same
   passage, different point), **miss** (not predicted). Unmatched accepted predictions are fine; rejected ones are
   false alarms. For each miss, one line on why the reader model did not catch it. Then the usual numbered plan.
7. **The user's feedback on that plan.**
8. **Implement**, as in step 4.

**Retro (end of each subsection).** In this log: the score, what worked, what to change. Then: misses -> new or
sharpened triggers in the reader model; false alarms -> weaken or delete triggers; the calibration row in the reader
model; writing lessons -> `paper-prose`; reactions -> the reaction log; `docs/status.md` and `docs/resume-prompt.md`.
Commit in logical pieces.

**Ripples.** Changes in one subsection that another subsection must absorb go in the "Ripples" list below, not into
the other subsection early; each is handled in its own subsection's session (step 2).

## Ripples

- §3.2's first paragraph says the edited input's features are found "without extracting them"; align with the §3
  lead ("before the edit is applied"; readouts are evaluated again). (from §3.1, session 17)

## §3.2 Edits and Their Side Effects

### 1. Simulated review
### 2. Proposed changes
### 3. User's feedback on the plan
### 4. Implemented
### 5. User's review
### 6. Score and plan
### 7-8. Feedback and implementation
### Retro

## §3.3 Edits Given as Writes

### 1. Simulated review
### 2. Proposed changes
### 3. User's feedback on the plan
### 4. Implemented
### 5. User's review
### 6. Score and plan
### 7-8. Feedback and implementation
### Retro

## §3.4 Sound Directions

### 1. Simulated review
### 2. Proposed changes
### 3. User's feedback on the plan
### 4. Implemented
### 5. User's review
### 6. Score and plan
### 7-8. Feedback and implementation
### Retro

## Sprint retro
