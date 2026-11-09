# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`).

## Current state (2026-11-09)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4-5:** drafted against the old §3; to be realigned in blocks (PLAN.md, next step 3), after applying decision 7's two §3 edits.
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in PLAN.md, next step 5.
- **Documentation:** reorganized 2026-11-09; index `docs/README.md`.

## Waiting on the user

- The holistic read of Sound Directions (any time).

## Scheduled

- **Next full simulated review:** after §4-5 are realigned, before the introduction; update
  `docs/reviews/review-prompt.md` right before running it (PLAN.md, next step 4).

## Session log

- **2026-11-09 (session 26): the two §3 edits decided, numbering fixed.** The user chose option A for Table 1's
  presence row and the in-place-write example (with the clause) for Definition 8 (PLAN.md, decision 7); not yet
  applied (`docs/resume-prompt.md`, step 1, has the exact text). The session was derailed by a stale "Definition 7"
  (compiled: 8) and the word "widen"; every active document, the writing skill, and the memory now use compiled
  numbers, `docs/README.md` has the numbering table, and CLAUDE.md requires checking `main.aux`. **Next:** apply the
  edits, then §4.
- **2026-11-09 (session 25): code audit, read-only** (PLAN.md, step 2). The code gives Definitions 9-10's table on
  EMBER except two per-operation cells (the ratio rule is coarser; fixed with the user's approval, Tables 4-5 unchanged); no threat-model direction changes, so Tables 4-5
  stand (checked by re-deriving the pilot with Table 1's rules patched in). Paper-side items for §4: the corpus-collected
  vocabulary falls under decision 2 too; writes onto locating positions are flagged or declared in the directions;
  append is declared, not collected (fix Def. 8's example); Table 1 lacks pools and nondecreasing functions of one sum.
  Record: `docs/evidence/code-audit-sound-directions.md`. **Next:** the user's call on the findings, then §4 (step 3).
- **2026-11-09 (session 24): paper mock rewritten** against the new §3 and the decisions of 2026-11-09:
  contributions in §3's terms, §4 as the template plus EMBER with word budgets, §5 by §3's results (5.2 Prop. 1,
  5.3 Thm. 1, 5.4 Cor. 1), what each table claims, the §2/§5 alignment with two options. **Next:** the user's
  approval, then the code audit (PLAN.md, step 2). User: layout accepted provisionally
  (judge it once written); §2/§5 alignment left to Claude, decided A, revisit at the next review (PLAN.md, decision 6).
- **2026-11-09 (session 23): holistic review and cleanup.** Assessment of the whole project after the framework
  rewrite. Decisions with the user (PLAN.md, "Decisions of 2026-11-09"): §4 becomes "instantiating the framework"
  with a fixed template that EMBER fills in the body and other domains in the appendix; the coverage of write
  operations' signatures is checked on the corpus, stated in a sentence; §5.2 (side effects) claims what it tests; §2/§5 alignment
  open; B and C parked. `docs/domain-selection-brainstorming.md` committed (user's). Documentation reorganized: index
  `docs/README.md`, superseded material in `docs/archive/`, evidence records in `docs/evidence/`, parked directions
  in `docs/parked/`, PLAN.md and this file rewritten short, CLAUDE.md trimmed, `scripts/README.md` inventory.
  Review status assessed against the 2026-11-02 register; the next full review scheduled (PLAN.md, step 4).
  **Next:** rewrite the paper mock (`docs/resume-prompt.md`).
- **2026-11-09 (session 22): Sound Directions round 4, in blocks** (Defs 7-10, Theorem 1, Corollary 1; ~1,470 words;
  "This session felt very effective"). Drafting in blocks after a math note recorded in `paper-prose` and memory.
- **2026-11-09 (session 21): the writing skill reset** (`paper-prose` rewritten as accepted texts plus taste; old rules
  archived in `docs/archive/paper-prose-2026-11-09/`).
- **2026-11-08 (sessions 19-21): §3.3 removed by decision; Sound Directions rounds 1-3.**
- **2026-11-05 (session 15): run 130 read; the detector table's (Table 5) adaptive column complete** (the beam search on every row except
  the sums row, whose cell is the greedy search's).
