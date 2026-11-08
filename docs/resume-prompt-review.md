# Resume: the §3 review sprint (ProvExp, writing track)

Paste this into a fresh session. It picks up the review sprint over §3.2, §3.3, and §3.4 of the manuscript.
**Current position: §3.3, step 1** (§3.2 done and accepted in session 18: "quite satisfied"). Update the "Current
position" line and the "Where things stand" list at the end of every session.

## What the sprint is

The user is writing a paper (dissertation research on feature provenance in malware classification; see `CLAUDE.md`).
§2, §3.1, and §3.2 of the manuscript are done after the user's review. §3.3-3.4 were drafted on 2026-11-05 and
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

## Start here (this session: §3.3, steps 1-2)

1. Invoke `/paper-prose`. Read, in this order:
   - `.claude/skills/paper-prose/reader-model.md` (how the user reads: comment style, triggers 1-27 with quotes, what
     they do not comment on, the calibration row from §3.2). This is the main tool of step 1. Triggers 23-27 are new
     from §3.2: pointers without need, concessions with no consolidation, a statement with no lead-in, remarks inside
     a statement, paragraphs with several jobs or that jump back.
   - The lessons in `paper-prose`, above all 32 (plan a revision as a paragraph spine, never as per-comment patches),
     33 (lead with the subsection; consolidate concessions; statements hold only the result), and 20 as limited
     (examples only where the reader cannot picture the structure; no worked arithmetic).
   - `docs/sprint-framework-review.md`: the protocol, the **Ripples** list (two items for §3.3-3.4 and one
     framework-wide note), and the whole §3.2 record with its retro (what went wrong in round 1 and why round 2
     worked).
   - The reaction-log entries of `docs/writing-spec.md` for §3.2 (2026-11-07) and the old 2026-11-05 entries about the
     §3.2/3.3 material (locating positions, "identity", "honest tools", "unhinged rant"): today's §3.3 descends from
     that material.
   - `docs/status.md` (session-18 block).
2. Read the context §3.3 builds on, as the reader will have it: §2 (`manuscript/_c_background.tex`), and §3's lead,
   §3.1, and §3.2 in `manuscript/_d_framework.tex`. §3.2 as accepted is the bar for a formal subsection: a short lead
   about the subsection only, one job per paragraph, a lead-in sentence before the statement, then why it holds part
   by part, then what it gives.
3. Read §3.3 (`sec:fw:edits`: the written set, the three ways a write changes items, Def 7 local kinds with structure
   positions, margins, and fixed layouts, Lemma 1 localization) **in the rendered PDF** (`make` in `manuscript/`,
   pdftotext and pdftoppm). Read Lemma 1's proof in `manuscript/_j_proofs.tex`; check the math against
   `docs/formalization.md` (frozen) and the design in `docs/framework-design.md` (Section 13 is §3.3's spine). Check
   what §3.4 and §5 use from §3.3 (grep for `lem:fw:localization`, `def:fw:local`, margin, fixed layout): give space
   by later use.
4. **Step 1, the simulated review**, into the §3.3 section of the log, in the user's format (P1, P2, ..., Q/F/M,
   confidence H/M/L, predicted questions answered in plain words). Known starting points, not a limit: the Ripples
   (where a delta comes from: §3.2 no longer says it; §3.3's first sentence used to answer a §3.2 paragraph that is
   gone); Def 7 is long and stacks new concepts (structure positions, margin, fixed layout), the pattern the user
   called "wet clay" and "an unhinged rant" in the old §3.2; the paragraph after Def 7 lists margins for fields, runs,
   and windows (generic, but heavy) and cites incremental parsers; "Every kind is local if all positions are its
   structure positions ..." reads as a concession; Lemma 1's statement is long, with (a) and (b) and a fixed-layout
   clause; the proof sketch after it. Ask before anything else whether the reader knows why §3.3 exists (edits given
   as writes, families of edits with no single $z'$) before the machinery starts.
5. **Step 2, the plan, as a paragraph spine** (lesson 32): open with the plain-language summary of what §3.3 is for
   and whether its structure must change, then one line per paragraph of the revised §3.3 with its single job, the
   predicted comments mapped onto the paragraphs, ripples into §3.4, and open questions last. Copy it into the log.
   **Do not edit the manuscript until the user approves.**
6. After approval: implement in one pass; `make` and `make check`; check the PDF for "??"; read the rendered text;
   rewrap to 120 columns; commit; tell the user which passages are new prose. Then the user's first read (step 5).

## Working rules that matter here

- The user's reaction to staging and LLM register is strong (lesson 5, reader-model triggers 17-21); apply the scan
  to your own plan sentences too.
- No domain (PE) examples in §3. A generic pseudocode listing helps only for unfamiliar structure (lesson 20 as
  limited); the user rejected a worked example on Algorithm 1 in §3.2 and numeric max/min examples.
- The user prefers terse leads and statements: their final hand edits to §3.2 shortened the lead ("give $z'$ exactly
  (before the edit is applied) and thus the side effects"), cut "In other words", and wrote "the largest or smallest".
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
  implemented in one pass. The user's first read (U1-U18): 4 missed, 6 fell short, 6 introduced, 1 new taste;
  round 2 (2026-11-08) rewritten from a six-paragraph spine, no example. Verdict: "quite satisfied"; the user made
  small spacing and wording edits (commit `5dcb9e7`). §3.2 done. §3.3: not started. §3.4: not started.
- Ripples open: §3.3 says where a delta comes from (its first sentence); §3.4 makes the "sign from the kinds alone"
  argument itself; framework-wide, decide after §3.4 whether to drop residual features (user's note).
