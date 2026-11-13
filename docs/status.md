# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-40 in `docs/archive/status-log-2026-11-10-to-11.md`, sessions
41-42 in `docs/archive/status-log-2026-11-12.md`).

## Current state (2026-11-12, sessions 34-52)

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
- **Simulated review (session 47):** designed and written as a reusable procedure (`docs/reviews/review-prompt.md`,
  `docs/reviews/process/`): four independent reviewers run headless outside the repository (A formal methods, B
  adversarial malware, C robust and certified ML, D systems security; Opus 5.5, high effort), seeing only the PDF, a
  note to reviewers and `papers/`; then a meta-reviewer with full access checks their findings, works through the
  checklist, writes the risk register and what the scale-up must include. Knobs in `config.sh`. **Run by the user**
  after session 47 (`docs/reviews/2026-11-12-body/`): A Weak accept, B Weak reject, C Weak reject, D Weak accept;
  likely outcome reject or major revision. Register R1-R21; top risks R7 (routing around the population), R1 (attacks
  below published strength; header-field edits never used by the adaptive attack), R2 (premises tested, not proven).
  Discussed in session 48 up to R7 only; the rest of the register is untriaged.
- **R7, leaving the population (session 48):** analysis, options and decision in `docs/evidence/r7-population-escape.md`.
  Run 137 (escape audit): single loader-ignored field writes (certificate or debug entry past the end, SizeOfImage
  raised) take 150 of 150 population files out. Decision (user): no router; one monotone detector scores every file,
  proven on the population and measured outside it. **Run 138** (the escape pilot, ~5-6 h) scripted for the user;
  the paper is not changed until it is read. **Step 1 read in session 52** (R7 record §7): one signed file evades
  both monotone detectors (an append restores the signature the certificate escape had broken); option 5 for the
  certificate clause accepted by the user, with caution (more holes may surface at the scale-up).
- **R1, attack strength (session 49):** decision 12. MAB-Malware vendored and driven by `scripts/mab_attack.py`
  (tested equal to upstream's own hand-over); run 139 scripted for the user; §5, Tables 4-5 ("evaded by any attack")
  and the new per-attack Table 11 carry its predicted values in blue. The adaptive attack scores by extraction at the
  scale-up (`--score real`); §2 unchanged (user). Widen first, then scale (user). **Run 139 read in session 51**
  (reading in its header and PLAN.md, decision 12): no silent no-ops; unconstrained full set 0/49 (16 evasive outputs
  over the byte budget), PV 7/9 by renames alone, both monotone full-model detectors 0 with their score never below
  the clean score (outside the population too). Measured values in Tables 4, 5 and 11; MAB-Malware's role in §5
  changed with the user's approval (5dc17b5): evidence that the monotone scores never fall, no longer an attack that
  breaks the undefended detector; Appendix D compares its rate with Zainab et al.'s (0.1% FPR, no byte limit).
- **R6, prior work (session 50):** the works behind §3 read and related to Proposition 1, Theorem 1 and Corollary 1
  (`docs/evidence/r6-prior-work.md`). The user: credit what we build on without conceding each result ("the novelty
  ... is in putting them together"), one or two seminal works per idea. Applied (660ba90): Gray et al.'s maxima in
  §3.1, incremental view maintenance carried to features in §3.2, abstract interpretation (Cousot and Cousot) after
  Theorem 1, §6's wrong contrast with incremental parsing replaced (abstract interpretation, Calzavara et al., the one
  new bib entry). About 140 words added.
- **Documentation:** reorganized 2026-11-09, cleaned up 2026-11-12 (stale resume prompts, the §4 note archived; the
  §5.3 design doc moved to `docs/evidence/`); index `docs/README.md`.

## Waiting on the user

- **Run 138** (`run/138_escape_pilot.sh`, started 16:03 on 2026-11-12; log `artifacts/logs/escape_pilot.log`): step 1
  (certificate escape) read in session 52; step 2 (SizeOfImage) still running at the end of session 52 (100 of 128
  tasks in the log). Its reading goes in the script's header once it has finished.
- **R17** (Theorem 1's hypothesis, Definition 10's side condition, a locality sentence; §3 only) recommended in
  session 52 as the next orthogonal item; not yet approved.
- **Next session:** `docs/resume-prompt.md` (step 2 of run 138 and option 5's final form; otherwise R17).

## Scheduled (in order; PLAN.md, next steps)

1. ~~The 4 MB-truncation brainstorm and decision~~ (done, session 46: files below 4 MB in every split).
2. A full simulated review of the manuscript as it then stands; its output decides the scale-up's content (run;
   discussion started in session 48 with R7).
3. The scale-up designed and launched as one protocol (seeds 0-2, full splits, one training set for every detector,
   ERDALT's stopping point, more malware, MAB-Malware as a held-out attack).
4. While it runs: §2's closing and contribution 4 aligned with §5.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

- **2026-11-12 (session 52): run 138 step 1 read; option 5 accepted for the certificate clause; three §5 fixes.**
  Run 138 was on step 2, so Claude read the finished step 1 (certificate escape): unconstrained 40/48; each monotone
  detector 1/41 and 1/43, the same signed file, by one append or added section, drops -3.1 and -3.2 logits (the count
  held, the size did not). Rebuilt and extracted: the escape pushes the certificate entry past the end, the signature
  no longer parses and its features fall to 0 (the score rises); the append brings the entry back inside the file and
  the features rise again, which the table excludes. The end file is ~1.4 logits below the unescaped original
  (the escape's larger certificate size); the original was not detected by either monotone detector. The user
  accepted option 5 for this clause, with caution ("additional issues and holes" may surface at the scale-up; memory
  `widen-population-cautiously`); final form after step 2. The three small §5 fixes applied on Claude's judgement
  (user): 5.2 expert set "and MAB-Malware, by renaming sections, on 4"; 5.1 "which of its actions"; 5.4's two
  "never lowers" sentences kept (different points). Commits 4ebd3e6, 6479a14. **Next:** `docs/resume-prompt.md`.

- **2026-11-12 (session 51): run 139 read (R1); MAB-Malware's claims rewritten.** Run 139 had finished, run 138 was
  on step 2. Checks for silent no-ops first (`p_lowest` against `p_clean`, the bandit's alpha/beta, the minimal
  actions, errors, outputs over budget): none; every non-counting output is evasive but over the byte budget, all by
  appended sections. Read against the hypothesis (run 139 header): the unconstrained part failed (0/49; s10 10/47),
  adversarial training 4/50 failed, PV 7/9 by renames alone, expert set 4/8 by renames, additions detector 1/42 by a
  debug-entry removal, monotone full-model detectors 0 in ~2,400 actions each with the score never below the clean
  score. Against Zainab et al.: their 83.4% is at 0.1% FPR (their Table IX) with no byte limit; at our detector's
  0.1% threshold the search's lowest scores were under it on 22 of 40 files. Unions computed per file (scratch
  script); blue cells replaced (52a46ec). The user approved Claude's five rewordings (5dc17b5): 5.3 drops MAB-Malware
  from adversarial training; 5.4's *The price* gains "never lowers its score", *The width* loses the MAB clause,
  *Beyond the guarantee* says it never lowers either monotone score; Appendix D compares with Zainab et al. A
  consistency pass over §5 found one error of Claude's (fixed) and three small points (open). **Next:**
  `docs/resume-prompt.md`.

- **2026-11-12 (session 50): R6, the prior work behind §3.** Runs 138 and 139 were still running, so the session
  took R6 (all four reviewers). Claude's first plan, a paragraph listing what in §3 is classical and what is new, was
  rejected: it "effectively neuters the entire paper"; the art is to acknowledge the shoulders we stand on without
  demeaning the contribution (memory `credit-without-diminishing`). Claude then read 16 works (view maintenance:
  Gupta-Mumick, Mumick et al. 1997, Levy-Sagiv, DBToaster; change calculi: Cai et al.; aggregate provenance:
  Amsterdamer et al.; abstract interpretation: Cousot and Cousot, Calzavara et al., Zhang et al.; incremental parsing,
  self-adjusting computation, dependency provenance; Gimenez, Pierazzi, Labaca-Castro rechecked), with quotes, in
  `docs/evidence/r6-prior-work.md`. The user: cite only one or two seminal works per idea. Applied (660ba90): four
  small edits in §3.1, §3.2, §3.3 and §6 (see Current state); Calzavara et al. the only new entry. Partial run
  outputs seen but not read (run 138 step 1; run 139 `full`, `pv`). **Next:** `docs/resume-prompt.md`.

- **2026-11-12 (session 49): R1 triaged and implemented (MAB-Malware); run 139 scripted.** Run 138 had just started,
  so the session triaged the review (R1, R2, R18, R6, the writing batch, scale vs widen; one recommendation each).
  The user took R1 first and corrected two points: "an attack we did not write" is no argument (the toolkit is not
  ours either), and the adaptive attack is stronger per attack (the review had compared it with a union; Claude's
  per-attack table: PV 4/9 vs 0/9, adversarial training 23/50 vs 10/50, unconstrained 25/49 vs 24/47, ERDALT 22/29 vs
  24/29). Agreed: MAB-Malware without code randomization, the authors' code vendored and improved where disruptive
  (threads and polled folders replaced by a direct hand-over, tested equal to upstream's on a stand-in classifier),
  same donors as the toolkit; "evaded by any attack" in the body with each attack in an appendix table (the
  2026-11-04 rule removed); "stronger" dropped. Claude's hybrid scoring for the adaptive attack was approved, then
  dropped by Claude after a check (prediction 0.17 s vs extraction 0.09 s per candidate). Found and fixed: upstream's
  section-append action loops forever on an empty donor content (empty sections skipped). Written: §5.1 (MAB-Malware,
  "any attack"), 5.3 (PV's hole, adversarial training), 5.4 (the price, the width, beyond the guarantee), Tables 4-5,
  Table 11 (per attack, Appendix D), all MAB values blue. Smoke of run 139: 0 of 9 evaded on the undefended detector
  (the toolkit 7 of 9); scores move but stay far above the threshold; recorded in the run header, hypothesis kept.
  The user settled the last questions: §2 stays (§5 need not show every motivating point; natively written, the
  partial computation would be far faster; this had been answered before) and widen first, then scale. Commits
  56410b3 .. f47c1f7. **Next:** `docs/resume-prompt.md`.

- **2026-11-12 (session 48): the review read; R7 analysed and decided; escape audit and pilot.** The review run was
  complete (the first meta-reviewer at max effort hit the session limit and was resumed at xhigh). Claude read all
  five files and spot-checked the deciding verdicts in the code: the one-field escape (`catalogue.py:453-457`), the
  header-field edits never used by the adaptive attack, A-W3 (3)'s false premise (EMBER appends a 0 before the minima),
  §5.3's counts including the 88 warnings (68 of the unlowered ones). The user chose to start with R7: Claude explained
  why the population and the router exist and weighed six options; agreed: escape audit, then no router (option 1)
  with an end-to-end escape measurement, option 5 only if needed. Run 137 (`scripts/escape_audit.py`, ~1 min): every
  loader-ignored write tried takes 150/150 files out (documentation quotes for loader safety; no execution).
  `a1_adaptive.py`: `--score real` and `--escape`; smoke 3 files (monotone drop exactly 0); run 138 scripted for the
  user. Record: `docs/evidence/r7-population-escape.md`. Procedure fix: a meta-only rerun no longer overwrites the
  reviewers' commit in `run-config.txt` (runbook note). Commits b3727f5, 1b73273, 80ed765. **Next:**
  `docs/resume-prompt.md`.

- **2026-11-12 (session 47): the simulated review designed, not run.** Claude proposed the design, one recommendation
  per question; the user approved it whole ("very good") and asked for a re-runnable procedure with configurable
  knobs. Design: four independent reviewers by expertise, no assigned stance (C, robust and certified ML, is new,
  for §5.3-5.4); ACM CCS kept; reviewers see the PDF (not the `.tex`, whose comments would steer them), an authors'
  note (the claim while the introduction is empty, the missing sections, preliminary numbers and the 4 MB setup, the
  one blue value by name) and `papers/` plus web search; our checklist (R4-R16 open risks, attack strength, §3's
  novelty, §2/§5, Proposition 1, the signatures, §4's template, the population, decision 6's literature pass,
  MAB-Malware, the ports) goes only to a meta-reviewer with full access, which checks every finding's premise; no
  drafts of the introduction. Written: `docs/reviews/review-prompt.md` (runbook; the old prompt archived),
  `docs/reviews/process/` (`config.sh`, `run_review.sh`, `reviewer-brief.md`, `reviewers/{A,B,C,D}-*.md`,
  `note-to-reviewers.md`, `checklist.md`, `meta-brief.md`). Reviewers run as `claude -p` from a scratch folder, so no
  `CLAUDE.md` or memory reaches them; checked with a dry run and a one-reviewer Haiku smoke test (found and fixed: the
  reviewer copied the brief's example IDs). **Next:** the user runs the review; then `docs/resume-prompt.md` (discuss it).

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
