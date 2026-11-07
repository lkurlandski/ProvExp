# Resume: the §3 review sprint (ProvExp, writing track)

Paste this into a fresh session. It picks up the review sprint over §3.2, §3.3, and §3.4 of the manuscript.
**Current position: §3.2, step 5** (steps 1-4 done in session 18: the user reads the revised §3.2 next; then
classify their comments, step 6, as in `docs/sprint-framework-review.md`; the "Start here" list below describes steps
1-2, reuse it for §3.3). Update the "Current position" line and the
"Where things stand" list at the end of every session.

## What the sprint is

The user is writing a paper (dissertation research on feature provenance in malware classification; see `CLAUDE.md`).
§2 and §3.1 of the manuscript are done after the user's careful review. §3.2-3.4 were drafted on 2026-11-05 and
**the user has not read them and will not read the current drafts**: they expect them to be low quality and
unpleasant to read. Instead, for each subsection, one per session:

1. **You analyze the draft as the user would read it** and write the review they would write.
2. **You propose changes** (a numbered plan).
3. The user gives feedback on the plan (not on the old draft).
4. **You implement** the approved changes.
5. The user's **first read** is of the improved version; they write comments.
6. **You classify each comment** (missed / fix fell short / introduced / new taste) and propose a plan.
7. The user gives feedback on that plan.
8. **You implement.** Then a short retro that updates the reader model, the lessons, and the logs.

The point is for you to learn to do the user's analysis yourself, so that by §3.4 steps 5-8 are unnecessary. The full
protocol, the formats, and the classification rules are in `docs/sprint-framework-review.md`; read it.

## Start here (this session: §3.2, steps 1-2)

1. Invoke `/paper-prose`. Read, in this order:
   - `.claude/skills/paper-prose/reader-model.md` (how the user reads: comment style, 22 triggers with quotes, what
     they do not comment on). This is the main tool of step 1.
   - `docs/sprint-framework-review.md` (protocol, the Ripples list, the §3.2 section to fill in).
   - The reaction-log entries of `docs/writing-spec.md` for §3.2 (2026-11-05, first and second draft; the user's
     verdict then was "still largely unsuccessful") and for §3.1 (2026-11-06, the bar it reached).
   - `docs/status.md` (session-17 block) for the latest state.
2. Read the context §3.2 builds on, as the reader will have it: `manuscript/_c_background.tex` (§2) and §3's lead and
   §3.1 in `manuscript/_d_framework.tex` (accepted; this is the quality bar: definitions that state their structure,
   a plain gloss after each equation, Algorithm 1 as the concrete anchor).
3. Read §3.2 (`sec:fw:side-effects`: Def 6 item delta, Proposition 1 exact side effects, the explanation after it)
   **in the rendered PDF**: `make` in `manuscript/`, then pdftotext and page images (pdftoppm) of its pages. Read its
   proof in `manuscript/_j_proofs.tex`, and check the math against `docs/formalization.md` (frozen) and the design in
   `docs/framework-design.md` (Section 12 is §3.2's spine).
4. **Step 1, the simulated review.** Write it into the §3.2 section of the sprint log, in the user's format: in text
   order, numbered P1, P2, ..., each marked Q (question), F (feedback), or M (mechanics) with confidence H/M/L.
   Answer each predicted question in plain words. Read paragraph by paragraph and ask each trigger of the reader
   model as a question. Known starting points (do not stop at these): the Ripples item (§3.2's "without extracting
   them" vs the lead's "before the edit is applied"); Prop 1's statement was "extremely dense" in the past; §3.2 had
   no example, and §3.1 now has Algorithm 1, which §3.2 could use (an edit to the toy extractor); whether §3.2 states
   *why* one avoids re-extraction before building the machinery; the kept "such as an offset in a table entry" and
   the 5-vs-3 max example after Prop 1.
5. **Step 2, the plan.** A numbered plan in the chat: one item per predicted comment or group, the concrete change,
   one recommendation, effects on §3.3-3.4 (add them to Ripples), open questions last. Lead with the plain-language
   summary of what §3.2 is for and whether its structure (spine) needs to change before any sentence does (if the
   structure is at fault, revise from a spine, not by patching). Copy the plan into the log. **Do not edit the
   manuscript until the user approves.**
6. After approval (later in the session): implement in one pass; `make` and `make check`; check the PDF for "??"
   (`make check` misses broken `\cref` to theorem-like labels); read the rendered text as the reader will; rewrap to
   120 columns; commit; tell the user which passages are new prose. Then the user does step 5 (possibly in the next
   session).

## Working rules that matter here

- The user's reaction to staging and LLM register is strong (lesson 5, reader-model triggers 17-21); apply the scan
  to your own plan sentences too.
- No domain (PE) examples in §3; a generic pseudocode listing or a two-line abstract case is fine (lesson 20).
- Be plain in the chat: lead with the plain-language version; define terms (`CLAUDE.md`, "Explain plainly").
- Do not edit `_e_instances.tex`, `_f_evaluation.tex`, or the research track's files; the research track runs in
  separate sessions (`docs/resume-prompt.md`). Commit only your own files (`git status` first). Do not push.
- At the end of every session: fill in the log, update `docs/status.md`, `PLAN.md`, this file's "Current position"
  and "Where things stand", and, after a retro, the reader model's calibration table and `paper-prose`.

## Where things stand

- 2026-11-06 (session 17): §3.1 done (commits `164e1b5`, `a167b08`); sprint scaffolding set up (`c7223ed`,
  `8bd8dc9`, `8dcaa42`). §3.2: not started. §3.3, §3.4: not started.
- 2026-11-07 (session 18): §3.2 steps 1-4. Simulated review P1-P15 and the 8-item plan in the log; plan approved
  unchanged (Q1: Algorithm 1 is the encouraged kind of example; Q2: length ~990 words accepted, trim later);
  implemented in one pass. Waiting on: the user's first read of §3.2 (step 5).
- Ripples open: two, both for §3.3 (its first sentence after §3.2's pointer paragraph was removed; continue the
  record-deletion example). The "without extracting them" ripple is resolved.
