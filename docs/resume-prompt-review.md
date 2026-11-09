# Resume: the §3 review sprint (ProvExp, writing track)

Paste this into a fresh session. It picks up the review sprint over §3.2, §3.3, and §3.4 of the manuscript.
**Current position: Sound Directions round 3 read by the user (2026-11-09): "still extremely problematic". Next
session starts with their comments (pasted); see "Start here".** Read the paragraph gate at the top of `paper-prose`
first. Update the "Current
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

## Start here (next session: Sound Directions, the user's read of round 3)

The user has read round 3 of Sound Directions (commit `801a9b4`, `sec:fw:directions` in
`manuscript/_d_framework.tex`) and will paste their comments in the first message. Their one-line verdict, given at
the end of session 21: **"still extremely problematic."** This is the third failed round on this subsection (round
1 "pretty bad", round 2 "paragraphs that don't mean anything", round 3 "still extremely problematic"), after §3.3 also
failed twice and was cut. Treat the next session as a reset of how this subsection is written, not as round 4 of
patches.

1. Before the comments arrive, prepare (read, do not write):
   - Invoke `/paper-prose`. Read **the paragraph gate** at the top of `SKILL.md` and lessons 32-36; then
     `reader-model.md`, triggers 28-33 and the calibration rows for §3.2 and Sound Directions.
   - `docs/sprint-framework-review.md`, section "§3.4 Sound Directions": the user's comments U1-U19 on round 1,
     their reaction to round 2, their comments on the round-2 lead and Def 7, the gated round-3 plan, and what was
     implemented. These are the patterns the round-3 read is likely to repeat.
   - The reaction-log entries for Sound Directions in `docs/writing-spec.md`.
   - Round 3 itself **in the rendered PDF** (`make` in `manuscript/`, then pdftotext), with §3.1-3.2 before it
     (the reader's context) and the proof of Theorem 1 and the sign-rule tables in `manuscript/_j_proofs.tex`.
2. When the comments arrive: log them verbatim under a new "Round 3: the user's read" heading in the log. Separate
   questions from feedback and **answer the questions first**, plainly, in words (a question usually marks a
   definition that does not stand on its own; name the fix with each answer). Classify each comment (missed / fix fell
   short / introduced / new taste) with one line on what the gate or the reader model should have caught.
3. Then, before any plan, step back and say plainly what the comments show about the subsection as a whole: is the
   problem the prose, the structure (which concepts, in which order), or the mathematics being presented (what
   Theorem 1 needs, and whether the reader can see why)? Recommend one way of working for the rewrite, and ask the
   user. Options to offer, with a recommendation: (a) a gated paragraph plan as in round 3; (b) **drafting one
   paragraph at a time with the user's review after each** (procedure step 2 of `paper-prose`: the unit shrinks when
   rounds fail; three have); (c) the user writes the passages that keep failing and Claude checks the mathematics
   and consistency only.
4. No manuscript edit until the user approves the plan. After implementing: `make`, `make check`, "??" check, read the
   rendered text, rewrap to 120 columns, commit only own files, report what changed per comment.
5. Retro at the end of the subsection (counts per class, what failed three times and why), then the reader model's
   calibration row, `paper-prose`, the reaction log, and the sprint retro at the end of the log.

Open after Sound Directions (research-track proposals, do not edit those files here): §4 defines operations as
catalogue rows, with one sentence that a table per row, combined, is sound and at least as tight; §4.1 says where the
signatures of edits defined by where they write come from, and that sign sets read from a corpus are Theorem 1's
hypothesis, checked in §5; "modeled"/"residual" wording in §4.1 and §5; §6's "margins" sentence; the paper mock.

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
- 2026-11-08 (session 19): §3.3 steps 1-4. Simulated review P1-P22 and a ten-paragraph spine in the log; approved
  unchanged (Q1 fixed layout out of Def 7, Lemma 1(iii) "only replaces"; Q2 Lemma 1 as main claim + (i)-(iii));
  implemented in one pass, ~1,230 -> ~1,560 rendered words (over the planned 850-950, not trimmed). Next: the user's
  first read. The user's read (U1-U18) lost the thread at Def 7; round 2 items 1-4 (Algorithm 2, located/scanned)
  drew the question whether §3.3 should exist at all. Halted for the decision session.
- Ripples open: §3.4 makes the "sign from the kinds alone" argument itself and can cite Lemma 1(iii) for its replace
  sort; framework-wide, decide after §3.4 whether to drop residual features (user's note); §4 (research track) says
  "locating positions". Closed: §3.3 says where a delta comes from (its lead, session 19).
- 2026-11-08 (session 20): no sprint step. The §3.3 decision analysis (`docs/s33-decision.md`): recommendation D
  (remove §3.3; footprint in §3.4; computation to §4.1), fallback A; open questions to the user.
- 2026-11-08 (session 20, cont.): D approved and applied; §3.3 cut, placeholder footprint in Sound Directions.
- 2026-11-08 (session 21): Sound Directions steps 1-4. Simulated review P1-P26; 18-paragraph spine approved (residual
  features dropped framework-wide; signature a definition, symbol kept; hashing/patterns to Appendix C); implemented
  in one pass (~1,800 words, over the planned ~1,200). Next: the user's first read.

- 2026-11-08 (session 21, cont.): the user's read of round 1: "pretty bad", stopped before Def 9 (U1-U19: 9 missed,
  5 introduced, 3 fell short, 1 new taste: neutral framing). Round 2 implemented (operations as sets of transformations,
  no theta/sort/instance, the append example). Next: the user's second read.
- 2026-11-08 (session 21, cont.): round 2 drew "paragraphs that don't mean anything"; audit, the paragraph gate
  added to `paper-prose`; round 3 from a gated 13-paragraph plan (threat model = set of transformations, operations
  and footprint out of §3), ~1,040 words. Next: the user's read.
- 2026-11-09 (session 21, end): the user read round 3, verdict "still extremely problematic"; comments deferred to a
  new session for context length. "Start here" rewritten for that session.
