# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-37 in `docs/archive/status-log-2026-11-10-to-11.md`).

## Current state (2026-11-12, sessions 34-46)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4:** drafted in the new structure (lead, 4.1-4.4, Appendix D "The EMBER Instance"), then revised in session 38
  after Claude's review with the `humanistic-paper-review` skill (all eight findings applied; 4.3 split into
  *Operations* and *Signature*; 4.4 reordered). Second, lightweight review in session 40 (three findings, all
  applied: 4.3.2 states what the sample-read signature rests on; closure "checked rather than proven"). §4 is in good
  shape. About 1,500 words against ~1,000; shortening with §5 later.
- **§5:** three findings (PLAN.md, decision 10; plan in `docs/paper-mock.md`, §5), fully drafted, no blue values.
  Reviewed by Claude with the `humanistic-paper-review` skill in session 41b, one subsection per pass, every finding
  approved by the user and applied (ce4ba21, f8baea5, 1053bf7, e8b0335): each subsection's lead now answers its
  question; "the computation" named; 5.1 introduces the unconstrained detector; 5.2's hand table counts eight errors
  with the certificate table apart, the two published analyses in their own paragraphs; 5.3 says the derived table
  marks 142 features as ones an edit *may* lower (20 shown); 5.4's 0.1% breakdown keeps only what clears retraining
  noise; Table 2's attack names and "population" throughout, no "pilot". The user has not read §5 end to end.
  Holistic review in session 42 (findings 1-4 applied, 68f6385, 49d879d). Tables 3 and 4 remade in session 43
  (7788592, 52e07cc): one column each, data only, one-line captions; the user: "good enough". 5.3 got its own table in
  session 44 (d87603f): Table 4, the learned defenses; the detectors table is now Table 5.
- **§5.3** is drafted (session 39) from the claim agreed in session 34 (`docs/evidence/section-5.3-design.md` §10.5, which
  stays the record of how the design came about). Learned-region paragraph cut, no audit table for now (tables
  remade later), no seed or protocol-hygiene details in the paper (user). Every learned defense is built from run 133's
  3,183 outputs; PV evaded 4/9 by one rename, 26.3% TPR; ERDALT 24/29 by its own attack; adversarial training 12/50
  and 23/50; leave-one-out per fold in Appendix D.
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in
  PLAN.md, next step 5. Run 131 (leave-one-out) finished: PV 5/21 on gamma_api, 0 elsewhere; ERDALT high on
  gamma_api and header_fields; ERDALT-8 adaptive 17/24. Runs 132 (coverage by source, seed smoke), 133 (§5.3 Phase
  2, ~4.8 h) and 134 (PV-clean, PV-free; Claude, ~3 min) done and read. **Run 135** (leave-one-out from run 133's
  outputs) finished 2026-11-11 19:54 (~3.4 h) and read in session 40: PV 0 evaded in all eight folds; ERDALT 25/29
  when GAMMA imports is held out, 0-2 in the other seven (header_fields 2, not the predicted ~10). Results in its
  header and in `docs/evidence/section-5.3-design.md`'s log.
- **Files and population (session 46):** every split uses only the files our copy holds in full (below 4,000,000
  bytes), stated once in §5.1's Setup; §4.4's population is the complete files with a plain layout (PLAN.md, decision
  8 (iv)). Most numbers in §5 and Appendix D are still pilot values on all files (`% PROTOCOL` comments): the scale-up
  replaces the detector results, a recount from stored outputs the checks (PLAN.md, open items).
- **Documentation:** reorganized 2026-11-09, cleaned up 2026-11-12 (stale resume prompts, the §4 note archived; the
  §5.3 design doc moved to `docs/evidence/`); index `docs/README.md`.

## Waiting on the user

- **Next session:** the full simulated review (PLAN.md, next step 2; `docs/resume-prompt.md`): the review prompt
  updated first, then the review run, then its findings discussed with the user before the scale-up is designed.
- The holistic read of Sound Directions (any time).

## Scheduled (in order; PLAN.md, next steps)

1. ~~The 4 MB-truncation brainstorm and decision~~ (done, session 46: files below 4 MB in every split).
2. A full simulated review of the manuscript as it then stands; its output decides the scale-up's content.
3. The scale-up designed and launched as one protocol (seeds 0-2, full splits, one training set for every detector,
   ERDALT's stopping point, more malware, MAB-Malware as a held-out attack).
4. While it runs: §2's closing and contribution 4 aligned with §5.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

- **2026-11-12 (session 46): the population decided; files below 4 MB in every split.** Claude counted which clause
  each of the 326 non-population files of the 2,000 fails (run 136, ~3 min): 231 incomplete because of our
  4 MB cut, 87 incomplete in the dataset itself (headers locate content past the end; 63 lack more than 4 KB of their
  sections), only 8 complete files with an unusual layout. All 12 attacked malware outside the population are
  incomplete, and so is the file that evaded the monotone detectors (51 KB, its headers describe 2 MB; the text had
  called it an unusual layout). Options weighed: whole binaries (unavailable, user), files below 4 MB, keeping all
  files reworded, extending the signatures to incomplete files (the strict table: 2,559 of 2,568 lowerable, nothing to
  constrain). The user chose files below 4 MB in every split ("one concession about the dataset upfront rather than
  ... complex residual side-effects"; reproducibility: the stock extractor matches the released vectors there) and
  waived block reviews ("full faith"). Written: §4.4 (complete files with a plain layout; 94% of the test files we
  use, 5% incomplete, 0.4% unusual layouts; closure 0 of 56,902), §5.1's Setup (85% of training files; 94% benign, 74%
  malicious test files), 5.4 (89% of the attacked malware, blue; the evasion on an incomplete file), Appendix D's three
  truncation sentences (also a factual fix: only one of the seven files with wrong declared changes is truncated),
  `% PROTOCOL` comments, a note in the open-science stub, a scope bullet in `docs/reviews/review-prompt.md` (the user's
  idea: review the setup as written, numbers as pilot values). PLAN.md decision 8 (iv) settled, next steps 1-3 and open
  items updated; the mock's §4.4 line. **Next:** `docs/resume-prompt.md` (the full simulated review).

- **2026-11-12 (session 45): holistic assessment; the next steps reordered.** Claude read PLAN.md, the mock, both
  latest simulated reviews, the graveyard and §2/§5. Assessment (PLAN.md, "Where the paper stands"): the framework is in
  good shape; §5's evidence is held back by sample size more than prose (PV on 9 files, the expert set on 8, the hand
  detector's drops never cross the threshold, ERDALT's port weaker than their paper, every evasion from our own
  table-guided attack, MAB-Malware absent); one domain is the largest acceptance risk; Proposition 1 has no finding of
  its own; polishing §4-5 now would be redone after the scale-up. The user agreed with the analysis and added that the
  truncation brainstorm and the review should be coupled, since the population decision could affect the review:
  brainstorm first, decide, write the decision into §4.4 (blue values if runs are needed), then review. New order in
  PLAN.md, next steps 1-7; the old list archived (`docs/archive/PLAN-next-steps-2026-11-12-s44.md`). **Next:**
  `docs/resume-prompt.md` (the truncation brainstorm).

- **2026-11-12 (session 44): §5.3 gets a table; the next step is a holistic assessment.** Check-in on more tables:
  5.2 and 5.4 had one, 5.3 none. The user: a 5.3 table is warranted "only if the table can represent that section's
  question and that section's answer", then asked Claude to decide. Claude's decision: rows the unconstrained baseline,
  PV, ERDALT, adversarial training; columns AUC, TPR at 1% / 0.1% FPR, evaded by the toolkit / by the adaptive attack
  (all from run 133's protocol); ERDALT's failure on GAMMA imports explained in the text, not a split column; no
  "flagged beforehand" column (no single measure across the three defenses; the audit numbers stay in the prose); our
  own detector left out (defense-paper framing). Two versions rendered in `manuscript/tmp-tables.tex`; Table 4's
  detection columns chosen. In the manuscript as Table 4, *Defenses learned from the outputs of the toolkit attacks*
  (d87603f); 5.3's prose drops the numbers the table carries; PV's TPR settled at 26.3 (ROC interpolation). Consistency
  pass over §5: fine, except the known one, two "Unconstrained" rows (Table 4: full training set, 25/49; Table 5: 10%,
  26/47), left for the scale-up (one training set for every detector). *Where the cost lies* stays prose. The user is
  not confident that step 2's remaining items are the right next steps. **Next:** `docs/resume-prompt.md`.

- **2026-11-12 (session 43): Tables 3 and 4 remade.** Started by asking what the user dislikes (multiple choice, with
  the PDFs): for Table 4 the footnote symbols, the long caption, phrase row labels, and mixed threat models and
  training sets; for Table 3 the prose cells and the looks ("maybe this shouldn't be a table?"). Models: their ExeFormer
  tables and Lucas et al.'s Table 2 ("almost any table in a published paper looks better than these"). Comparisons in
  `manuscript/tmp-tables.tex` (untracked; old version on page 1, new on page 2, as the user asked). Table 4 (7788592):
  one column, two halves in one float (full threat model; additions, with toolkit evasion split inside/outside the
  threat model), short labels, arrows, bold best, evasion as counts; the adaptive results and the full-training-set
  row moved into 5.4's text (so the paper no longer shows 27/49 against 5.3's 25/49). The user: "not perfect, but its
  good enough"; the two halves should be more consistent, which may need runs (scale-up). Table 3 (52e07cc): one
  column, feature / operation / hand / derived / files, grouped by population; the user hesitated between it and a
  numbered list by cause and asked Claude to decide for the research as a whole (Claude: the table; findings at a
  glance, PE detail contained, extends to other domains). *Why it errs* now names all five parser facts (open item
  closed). Table 3 as a one-column float made LaTeX drop Table 9 at the end of the document; fixed by declaring it
  earlier in Appendix D. The question of more tables (5.3, the per-operation cost) is for the next session.
  **Next:** `docs/resume-prompt.md`.

- **2026-11-12 (session 42): §5's holistic review (contributions' importance); the table remake's first attempt
  rejected.** Seven findings; the user approved 1-4, applied in 68f6385: what Gimenez et al. report (the expert set and
  PV never evaded by the toolkit attacks; detection and robustness a "trade-off regarding features set") stated before
  our results; the §5 lead names what breaks; 5.4 names both alternatives (learned, hand-picked); 5.2's cost paragraph
  ends on why a broken guarantee matters. Finding 5 (5.3's topic sentences) dropped; the uncited "usually tested
  against an attack it did not learn from" fixed (49d879d). Findings 6 (no table shows 5.3) and 7 (§2 promises an
  attack; a known weakness, not fixable now) noted in PLAN.md step 2. The tables come before the question-and-answer
  emphasis (user). Claude's table mock-ups (`docs/archive/table-mockups-2026-11-12/`) were judged "pretty bad, quite
  possibly as bad if not worse than what we already had"; facts they surfaced are in PLAN.md step 2 (a), among them
  that 5.2's *Why it errs* names three parser facts where the errors need five. `make check`: a 2 pt overfull page box
  among the appendix floats since 68f6385 (harmless). **Next:** `docs/resume-prompt.md` (the tables, restarted from
  what the user dislikes).

- **2026-11-12 (session 41b, parallel to 41): §5's humanistic review, four passes.** Lead and 5.1 (seven findings),
  5.2 (seven; #7, the Rich header, dropped by the user: a PE construct the reader can look up), 5.3 (five, plus the
  unconstrained detector in 5.1), 5.4 (six). All others approved and applied; reactions logged raw in
  `docs/writing-spec.md`. The user: "serious structural modifications" later to how §5's questions are asked and
  answered, with visual emphasis (PLAN.md step 2); for now each lead answers its question. Open, outside the prose:
  5.1's 73,063 is run 107's direction check, while the exactness counts are Appendix D's (62,604 + run 118's 34,965);
  fix at scale-up unless the user wants it now. **Next:** a holistic review of §5 with weight on the
  contributions' importance (user), then PLAN.md step 2; `docs/resume-prompt.md`.

- **2026-11-12 (session 41): the ERDALT check (only), no run.** The score floor is not a thin margin: 99% of test
  goodware sit at ERDALT's lowest score, so the 1% FPR threshold sits at its edge; GAMMA imports drives detected
  malware from logits up to ~1,000 to the floor (24/29; 28 counting over-budget). Detection weaker than their paper
  (AUC 0.88 vs 93.0% on another dataset), stopping criterion met at one epoch; left to the scale-up. Their code read
  against their paper: the paper fixes only the abstract architecture and losses; the one conflict is the output
  layer, which our port constrains. User (strongly held): implement from the paper where the code breaks the
  guarantee; no "their code exactly" variant. PLAN.md step 3, `docs/upstream-issues.md` item 8 updated.
  **Next:** `docs/resume-prompt.md` (unchanged: §5's humanistic review).

- **2026-11-12 (session 40): §4's second review; run 135 read; docs cleaned up.** Claude's lightweight review of §4
  (three findings, all applied in 75c1c9c): 4.3.2 names what the sample-read part of the signature rests on and what
  §5.1 checks (the directions from 100 files equal those from 2,000; no edit moves a feature against them); its two
  consequences of a write onto a located position sit together; 4.4 says closure is checked rather than proven. Run
  135 read (held: PV 0 in all folds, ERDALT's GAMMA-imports fold 25/29; failed: header_fields 2, not ~10, and the
  mean); 5.3's *Holding one attack out* and Table 9 rewritten with the real values, the finding unchanged (b1a544c).
  The user set the order of what follows (PLAN.md, next steps): §5's humanistic review one subsection at a time; then
  tables, shortening, §2 alignment; then the ERDALT check and the 4 MB brainstorm; then decide on a simulated review.
  Cleanup: stale resume prompts and the §4 note archived, the §5.3 design doc moved to `docs/evidence/`, sessions
  29-33 of this log archived, the README's numbering table updated, §4's commented-out old text removed.
  **Next:** `docs/resume-prompt.md`.

- **2026-11-11 (session 39, parallel to 38): §5.3 drafted in three blocks.** Run 135 had just started, so its
  ERDALT folds are in blue (its PV folds finished during the session: 0 evaded in all eight). User decisions: cut the
  learned-region paragraph; no audit table now (Tables 3-4 to be remade); one sentence on rename, no new run; no RNG or
  protocol-hygiene details in the paper. Found: the planned "745 vs 928" coverage comparison mixed files (pilot vs
  training); on the same files it is 847 vs 928, and it is out anyway. Old 5.3 material removed from 5.4; §6's ERDALT
  reference points to 5.3; Appendix D gained the leave-one-out table. ~970 words. The user did not review the blocks
  (review next session). Commits 7a2ceff, 9d0369f, 035d977. **Next:** `docs/resume-prompt-5.3.md`.

- **2026-11-11 (session 38): §4 reviewed by Claude and revised.** Review with the `humanistic-paper-review` skill
  (eight findings). The user: trimming is good, but moving small snippets to the appendix does more harm than good;
  findings applied in two passes (the easy ones first, so the user can focus on the rest). Applied: attack names
  follow Table 2's operations, with a toolkit-attacks column (from secml-malware's code); the Zainab et al. sentence
  dropped (MAB-Malware uses code randomization, which the threat model excludes); "certificate table" for the
  structure, "Authenticode signature" for its content (Table 8's row renamed too); §4.2's item list shortened; the
  lead names the sum-then-readout form; 4.3 split into subsubsections *Operations* and *Signature*, the latter opening
  with what is proved and what rests on the files; 4.4 reordered (closure after the definition, counts tied to
  §5.1's 73,063 edits and 2,000 test files, routing last). Commits c7d0734, cf4f4a4, b8b710c. For §5: it still says
  "GAMMA's import injection" and "the header-field attack" (Table 2: GAMMA imports, header fields) and Table 3 says
  "signature table" for the certificate table. **Next:** a lightweight re-review of §4, then §5
  (`docs/resume-prompt.md`).
