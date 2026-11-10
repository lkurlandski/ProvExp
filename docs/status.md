# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`).

## Current state (2026-11-10)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4:** drafted in the new structure (lead, 4.1-4.4, Appendix D "The EMBER Instance"); blocks 1-2 accepted, 3-4
  "pretty good". About 1,540 words against ~1,000: shortening deferred (user), §4.3 first. `% VERIFY`: EMBER
  2017/2018 had no parser warnings (Joyce et al. PDF not in `papers/`).
- **§5:** realigned with §3-4 in vocabulary and claims (2026-11-10, session 29; ~3,380 words against ~3,200). The user
  read block 1 only lightly: they have a "pretty big concern about the structure and organization" of §5, to address
  next; expect a rewrite. Open in the text: `% VERIFY` on Table 3's "random in-place writes" row (run 93 counts differ).
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in PLAN.md, next step 5.
- **Documentation:** reorganized 2026-11-09; index `docs/README.md`.

## Waiting on the user

- Their structural concerns about §5 (next session starts there).
- The holistic read of Sound Directions (any time).

## Scheduled

- **Next full simulated review:** after §4-5 are realigned, before the introduction; update
  `docs/reviews/review-prompt.md` right before running it (PLAN.md, next step 4).
- **Brainstorm on the 4 MB truncation** (the plain-layout population's gap), just before or after that review (PLAN.md,
  decision 8 (iv) and step 4).

## Session log

- **2026-11-10 (session 29): §5 realigned; the per-candidate cost measurement dropped.** A probe showed Prop. 1 scoring
  in Python is no faster than thrember's (optimized) extraction; the user: never measure or compare it, say the
  computation is smaller and can be faster; optimization is engineering, out of scope (PLAN.md decision 6, memory).
  §5 rewritten in three quick blocks (commits after f1d6050): 5.2 claims what it tests ("The Instance Is Correct",
  Declined instead of Flagged, no speed claim), 5.3 gains the corpus check of the signatures, 5.4 points to §4.4 for
  closure; §6's "our margins" fixed. **Next:** the user's structural concerns about §5, then shortening §4-5.

- **2026-11-10 (session 28): §4 drafted in four blocks** (commits 556599e, baa1e48). Block 1 took three rounds on
  §4.1 (PE format, then EMBER's features over it, not interleaved); lessons added to `paper-prose` (a08460c) and the
  reaction log. §4.3 literature first with Demetrio TOPS, GAMMA, MAB-Malware, and Zainab et al. (preprint, user
  approved); Table 2's column is now "Changes: declared / item tables". **Next:** see `docs/resume-prompt.md`.

- **2026-11-09 (session 27): decision 7 applied; §4 block 1 drafted and the section restructured.** Table 1's monotone
  row and Definition 8's in-place-write example committed (690cc67; the presence example moved to Table 1's caption to
  avoid an overfull table). §4 outline revised with the user (PLAN.md, decision 8): no "repairs" part and no mention of
  the import bug; (a) and (b) merged into a qualitative "how strictly EMBER fits"; the threat model literature first;
  the 4 MB truncation kept for now, brainstorm scheduled around the next review. Block 1 (lead, EMBER, Items/Sums/
  Readouts) drafted; the user liked §4.1's content and style but found it bookkeeping-heavy, the lead verbose and its
  checks misplaced, and the EMBER paragraph too thin and in need of its own subsection. New structure (decision 8 (v)):
  lead, 4.1 EMBER and PE files, 4.2 EMBER as a sum-then-readout extractor, 4.3 threat model, 4.4 population, details in
  an appendix. Section retitled "Instantiating the Framework". **Next:** redraft block 1 in the new structure
  (`docs/resume-prompt.md`). Later the same session: a literature review of adversarial malware
  (`docs/evidence/literature-adversarial-malware.md`; PDFs in `papers/`, renamed to Google Scholar keys): the
  catalogue covers every structural edit of the reputable-venue PE attacks; code-level transformations are excluded
  for now by the user's choice and recorded as a limitation (PLAN.md, decision 9).
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
