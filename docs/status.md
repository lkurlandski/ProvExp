# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`).

## Current state (2026-11-10, session 32)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4:** drafted in the new structure (lead, 4.1-4.4, Appendix D "The EMBER Instance"); blocks 1-2 accepted, 3-4
  "pretty good". About 1,540 words against ~1,000: shortening deferred (user), §4.3 first.
- **§5:** realigned with §3-4 in vocabulary and claims (session 29). Structural rewrite agreed in session 30 (PLAN.md,
  decision 10): three findings (what hand analysis misses, what observed attacks miss, what robustness costs), not a
  validation section and not a defense paper. Plan, one line per paragraph, and checks C1-C3: `docs/paper-mock.md`,
  §5. Blocks 1-2 (lead, 5.1, 5.2) drafted and revised after the user's review (0069f56); blocks 3-4 (5.3, 5.4) to do.
  The held-out cells of 5.3 are `\synthetic` until run 131 is read.
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in
  PLAN.md, next step 5. **Running (user, started 2026-11-10, ~7 h on GPU 3):** run 131, leave-one-out PV and ERDALT.
- **Documentation:** reorganized 2026-11-09; index `docs/README.md`.

## Waiting on the user

- **Run 131's results** (running since 2026-11-10: `CUDA_VISIBLE_DEVICES=3 NUM_WORKERS=16`). Its summary replaces
  the `\synthetic` held-out cells of §5.3; check C2 and block 3 can start before it finishes.
- The holistic read of Sound Directions (any time).

## Scheduled

- **Next full simulated review:** after §4-5 are realigned, before the introduction; update
  `docs/reviews/review-prompt.md` right before running it (PLAN.md, next step 4).
- **Brainstorm on the 4 MB truncation** (the plain-layout population's gap), just before or after that review (PLAN.md,
  decision 8 (iv) and step 4).

## Session log

- **2026-11-10 (session 32): leave-one-out scripted, not run.** `run/131_loo_defenses.sh`: eight PV folds (selection
  from seven attacks, the held-out attack run against the fold's model), nine ERDALT models on two GPUs, the beam
  against ERDALT-8, a summary. Smoke: PV's gamma_api fold in full, 5/21 held out (PV-seen 4/22). The deltas predict
  the user's hypothesis (PV well above 0) fails on the mean: the attacks lower nearly the same features (only
  gamma_sections, 49, and gamma_api, 10, lower many the others don't). ERDALT's folds for the four originally held-out
  attacks would learn from ~50 pilot vectors of them, not ~400 (run 122 generated only the seen four); on the user's
  approval, step 0 now generates the other four on the same 400 training malware (`--adv_dir` takes several
  directories), and ERDALT trains on one or two GPUs, whichever are visible. **Next:** the user runs 131; then the
  writing session.

- **2026-11-10 (session 31): §5 block 1 drafted; checks C1 and C3 done.** Lead and 5.1 rewritten as three findings
  (the correctness check is one paragraph in 5.1); the side-effect table and a short paragraph moved to Appendix D
  (tables renumber: directions 3, detectors 4, side effects 8). C1 held (median 263 features per edit, 4-8 groups);
  C3 found Severi et al.'s hand classification (all hashed features "extremely difficult" to manipulate; the derived
  table moves 1,490 of 1,650 under additions). Results in `docs/paper-mock.md`, §5. **Next:** the user's review of
  block 1, then C2 and block 2 (5.2).

- **2026-11-10 (session 30): §5's structure agreed, no prose.** The user's concern: §5 is organized to show the
  implementation is correct and the proofs hold ("transactional and somewhat lifeless"). Assessment: right; about a
  quarter to a third of §5 checks our own work and comes first, because the mock organized §5 by §3's results. A
  defense-first alternative was rejected by the user (4 points of TPR is not small to them, about 1% or less wanted;
  three baselines too few for a defense claim); the attack alone is too weak to be a task. Agreed: three findings
  that test §2's claim about trial, hand analysis, and observed attacks; the side-effect table to Appendix D; a new
  audit table in 5.3. No new task needed; three checks on existing outputs (C1-C3). Recorded: PLAN.md decision 10,
  `docs/paper-mock.md` §5, memory `findings-not-defense-paper`. **Next:** `docs/resume-prompt.md`.

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
