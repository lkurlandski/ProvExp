# Documentation index

Read `docs/status.md` and `PLAN.md` at the start of a session; everything else only when the session's task needs it.
Each entry says when it is worth opening. The manuscript (`manuscript/*.tex`) is the authority on the paper's content;
where a document disagrees with it, the manuscript wins.

## The paper's numbering (compiled 2026-11-12)

Documents written before 2026-11-12 may use older numbers; the compiled PDF wins. Before naming a number to the user,
check `manuscript/main.aux` (`grep newlabel manuscript/main.aux`), and add the title or label alongside it.

| Kind | Compiled numbers |
|---|---|
| Sections | 1 Introduction; 2 Background and Motivation; 3 Measuring Edits Across Feature Mappings (3.1 Sum-then-Readout Extractors, 3.2 Edits and Their Side Effects, 3.3 Sound Directions); 4 Instantiating the Framework (4.1 EMBER and PE Files, 4.2 EMBER as a Sum-then-Readout Extractor, 4.3 Threat Model with 4.3.1 Operations and 4.3.2 Signature, 4.4 Population); 5 Evaluation (5.1 Setup, 5.2 What Hand Analysis Misses, 5.3 What Observed Attacks Miss, 5.4 What Robustness Costs); 6 Related Work; 7 Discussion; Appendix A Symbol Table, B Types, Monoids, and Folds, C Proofs for the Framework, D The EMBER Instance |
| Definitions | 1 Items, 2 Sums, 3 Contributions, 4 Readouts, 5 Sum-then-readout extractor, 6 Item delta, 7 Threat models and directions, 8 Changes and signatures, 9 Directions of sums, 10 Derived table |
| Results | Proposition 1 (side effects), Theorem 1 (sound directions), Corollary 1 (monotone detectors); Algorithm 1 (the extractor) |
| Tables | 1 readout rules (§3.3), 2 operations of the threat model (§4.3), 3 hand vs derived directions (§5.2), 4 learned defenses (§5.3, `tab:eval:learned`, added session 44), 5 detectors (§5.4), 6 symbols, 7 sign table (Appendix C), 8 EMBER readouts, 9 side effects, 10 leave-one-out (Appendix D) |

## Active

| Document | What it is | Open it when |
|---|---|---|
| `PLAN.md` | thesis, where the paper stands, the decisions of 2026-11-09, next steps, settled decisions | every session |
| `docs/status.md` | current state, what waits on the user, short session log | every session; update at the end |
| `docs/resume-prompt.md` | where the next R7/scale-up session starts: R7 is done at pilot scale; the user's decisions before the scale-up (the extractor question, step 2c; the protocol, step 3); rebuttal and R18 have their own prompts | starting an R7 or scale-up session |
| `docs/resume-prompt-rebuttal.md` | where each rebuttal session starts, once `run_rebuttal.sh` has written the triage (`docs/reviews/<TAG>/rebuttal/triage.md`): the user decides on the triage table, then on drafts of the groups worth investigating; decisions recorded in the table | starting a rebuttal session |
| `docs/checkpoint-prompt.md` | the user's prompt for ending a session | the user ends a session |
| `docs/paper-mock.md` | the paper's contributions, outline with word budgets, and tables | planning or writing any section; checking whether new work belongs in the paper |
| `docs/writing-spec.md` | the user's raw reactions to drafts, newest first | writing paper prose (with the `paper-prose` skill) |
| `docs/domain-selection-brainstorming.md` | the user's ideas for other domains | only when the user opens the topic |
| `docs/upstream-issues.md` | thrember and secml-malware bugs, drafted for the user to report | an extractor quirk comes up |
| `docs/design.md` | the `provexp` package's data structures, conventions, thrember quirks | changing code in `src/provexp/` |
| `docs/literature-2026-10-22.md` | related work for the current direction (and for B, C) | related work, novelty, a new application |
| `docs/graveyard.md` | ideas that did not pan out and why; directions the user found unproductive | before proposing a new direction or analysis |
| `docs/reviews/` | simulated reviews (index: `docs/reviews/README.md`); the reusable review procedure: `review-prompt.md` (runbook) and `process/` (config, launcher, prompts, note to reviewers, checklist); latest `2026-11-12-body/` (four reviewers and a meta-review; risk register R1-R21; `rebuttal/`, one draft per register item with the user's decision, once run), before it `2026-11-04-strategy.md` and `2026-11-02-body.md` (R1-R16) | before a new review; when weighing what reviewers will miss |
| `docs/parked/directions-B-C.md` | the two applications set aside (not failed) | considering a second application |

## Evidence: the records behind §4-5

Design decisions, runs, and results of the EMBER instance and its evaluation. Their vocabulary is the old one (claims
C1/C4, requirements, Tables A0-A2, and in places Tables 5-7, for what the compiled paper numbers Tables 3 and 5). Open them to trace a number in the paper to its run,
or when changing an experiment. Run scripts are in `run/` (one per step, numbered), outputs under `artifacts/`.

| Document | Covers |
|---|---|
| `docs/evidence/item-layer-design.md` | the instrumented extractor: item tables, readouts as data, the edit catalogue, the side-effect and direction engines, checks G1-G7 (§4, Tables 3-4) |
| `docs/evidence/direction-A-threat-model.md` | the threat models (additions, shifts, full), hand direction table, re-encodings over sums, the first exactness table (§4.3-4.4, Table 4) |
| `docs/evidence/direction-A-A1-design.md` | the detector table's design, baselines, decisions, and results (Table 5) |
| `docs/evidence/direction-A-expert-set.md` | Gimenez et al.'s 40 features, instrumented: the expert-set row and its holes |
| `docs/evidence/code-audit-sound-directions.md` | the 2026-11-09 audit of the direction engine against Definitions 7-10 and Tables 1 and 7 (readout rules, sign table): findings, what §4 must say, the readout rule of every EMBER feature |
| `docs/evidence/literature-adversarial-malware.md` | the 2026-11-09 literature review of adversarial malware (venues, the edits each work uses, defenses) and what it implies for the catalogue | §4.3, §6, the threat model |
| `docs/evidence/section-5.3-design.md` | how §5.3 came about: options, phases, runs 132-135 and their results (§10), the agreed claim (§10.5), the log | tracing a §5.3 number to its run; revisiting PV, ERDALT, adversarial training, leave-one-out |
| `docs/evidence/r7-population-escape.md` | R7 (session 48): why the population and the router exist, the review's finding, the escape audit (run 137), six options weighed, decision 11 (no router), the escape pilot (run 138), log | anything about files outside the population, the routing, §4.4 or §5.4's *Where the guarantee holds* |
| `docs/evidence/r7-overlay-rule.md` | R7 (session 55): pefile's overlay rule breaks the widened population's closure; LIEF vs pefile vs EMBER v2, the mechanisms behind R7's escapes, options weighed, LIEF's rule chosen; the extractor question (designed, not patched; LIEF) | anything about the overlay, the parser choice, or deviations from EMBER-v3 |
| `docs/evidence/r18-trial-competitor.md` | R18 (session 60): the trial competitor (a monotone detector on the table learned by systematic trial), its table against the derived one, the smoke attack (signature cloning through a string count trial never moved), run 144, and the recommendation on iterated adversarial training | §5's contrast with trial; R18; adversarial training at the scale-up |
| `docs/evidence/r6-prior-work.md` | R6 (session 50): the prior work §3 builds on (view maintenance, change calculi, aggregate provenance, abstract interpretation, certified defenses, incremental parsing), each read and related to Proposition 1, Theorem 1, Corollary 1; where each is cited | positioning §3 and §6 against prior work; R6, R21 |
| `docs/evidence/held-out-attacks-perspectives.md` | session 33: ways to test defenses learned from attacks (fixed split, leave-one-out mean or worst fold, keep-one, MAB-Malware, all subsets, coverage C2), with strengths and weaknesses; run 131's PV results and C2 | §5.3 |

## Archive (superseded; open only to recover a reason or a record)

| Folder or file | Contents |
|---|---|
| `docs/archive/status-log-2026-11-12.md` | the session log, sessions 41-42 (search, don't read) |
| `docs/archive/status-log-2026-11-10-to-11.md` | the session log, sessions 29-39 (search, don't read) |
| `docs/archive/resume-prompt-2026-11-14-s61.md` | the resume prompt of session 61 (written in session 57): read run 143 and write R7 into the paper (both done in session 61; blue values decided) |
| `docs/archive/resume-prompt-2026-11-13-s57.md` | the resume prompt of session 57 (written in session 56): verify session 56's R7 code before run 143 (done: holds, two small fixes; run 143 cleared) |
| `docs/archive/resume-prompt-2026-11-13-s55-56.md` | the resume prompt for sessions 55-56 (two tracks): read run 142, then `ent` in the attacks and run 143 (both done in session 56; run 143 handed to the user) |
| `docs/archive/resume-prompt-2026-11-13-s54.md` | the resume prompt as of session 55's start (two tracks; written in sessions 53-54): R7's closure check first (done in session 55: failed through pefile's overlay rule; LIEF's rule adopted) |
| `docs/archive/resume-prompt-2026-11-13-s53.md` | the resume prompt of session 54 (written in session 53): R7's widening (step 2b) and, in parallel, §6 (R21); session 54 replaced the parallel track's next step with the meta-review's triage |
| `docs/archive/resume-prompt-2026-11-12-s52.md` | the resume prompt of session 53 (written in session 52): step 2 of run 138 and option 5's final form, otherwise R17 (run 138 read, widening chosen and costed in session 53) |
| `docs/archive/resume-prompt-2026-11-12-s51.md` | the resume prompt of session 52 (written in session 51): run 138 for R7, or the next weakness; three small §5 fixes (applied in session 52; step 1 of run 138 read) |
| `docs/archive/resume-prompt-2026-11-12-s50.md` | the resume prompt of session 51 (written in session 50): runs 138 and 139, or a new weakness (run 139 read and written in during session 51) |
| `docs/archive/resume-prompt-2026-11-12-s49.md` | the resume prompt of session 50 (written in session 49): runs 138 and 139, or a new weakness (R6 recommended, done in session 50) |
| `docs/archive/resume-prompt-2026-11-12-s48.md` | the resume prompt of session 49 (written in session 48): reading run 138 and continuing R7, or triaging the review's register; the scale-first-or-widen-first question |
| `docs/archive/resume-prompt-2026-11-12-s47.md` | the resume prompt of session 48 (written in session 47): checking and discussing the full simulated review's output |
| `docs/archive/status-log-2026-11-09.md` | the session log, sessions 21-27 (search, don't read) |
| `docs/archive/status-log-2026-10-to-2026-11-09.md` | the full session log until 2026-11-09 (32k words; search, don't read) |
| `docs/archive/PLAN-log-2026-10-22-to-2026-11-09.md` | the plan's history, every "Next steps" block |
| `docs/archive/resume-prompt-2026-11-06.md` | the previous resume prompt (research track details: sums-row routing, scale-up budget) |
| `docs/archive/resume-prompt-2026-11-12-s46.md` | the resume prompt of session 47 (written in session 46): the design questions for the full simulated review (reviewers, venue, the incomplete parts, models), what it must cover |
| `docs/archive/review-prompt-2026-11-02.md` | the prompt of the 2026-11-02 review (one agent, three reviews, the checklist in the prompt), replaced by `docs/reviews/process/` |
| `docs/archive/resume-prompt-2026-11-12-s45.md` | the resume prompt of session 46 (written in session 45): the 4 MB-truncation brainstorm and the population decision; what was on record about the non-plain files before session 46 counted them |
| `docs/archive/resume-prompt-2026-11-12-s44.md` | the resume prompt of session 45 (written in session 44): the holistic assessment of the research and the planning stage; where things stood at the end of session 44 |
| `docs/archive/PLAN-next-steps-2026-11-12-s44.md` | PLAN.md's "Next steps" before session 45's reordering: the records of the §5 reviews, the table remake's two attempts and the facts they surfaced, the ERDALT check |
| `docs/archive/resume-prompt-2026-11-12-s43.md` | the resume prompt of session 44 (written in session 43): the check-in on whether §5 needs more tables; the data behind 5.3's defenses and the per-operation cost |
| `docs/archive/resume-prompt-2026-11-12-s42.md` | the resume prompt of session 43 (written in session 42): the table remake restarted from what the user dislikes; the data behind Tables 3-4, 5.3's defenses and the per-operation cost |
| `docs/archive/resume-prompt-2026-11-12-s41b.md` | the resume prompt of session 42 (written in session 41b): §5's holistic review weighing the contributions' importance, how the user wants reviews handled, settled points of 5.3-5.4 |
| `docs/archive/table-mockups-2026-11-12/` | Claude's first mock-ups of §5's tables (session 42), rejected by the user ("pretty bad"); `mock.tex` and `mock.pdf`, to know what not to repeat |
| `docs/archive/resume-prompt-2026-11-12-s40.md` | the resume prompt of session 41b (written in session 40): §5's humanistic review, how the user wants reviews handled, points a careful reader may stop at in §5.3 |
| `docs/archive/resume-prompt-2026-11-11-s38.md` | the resume prompt of session 40 (written in session 38): the lightweight second review of §4, how the user wants reviews handled, the §5 review's known items |
| `docs/archive/resume-prompt-2026-11-11-s39b.md` | the second resume prompt of session 39: reading run 135, points a careful reader may stop at in §5.3 |
| `docs/archive/instances-note.md` | §4's working note: what an instance supplies, the agreed structure |
| `docs/archive/resume-prompt-2026-11-11-s39.md` | the resume prompt of session 39 (drafting §5.3: the agreed evidence list, caveats, run 135's predictions) |
| `docs/archive/resume-prompt-2026-11-11-s34.md` | the resume prompt of session 34 (§5.3 from scratch: overview, analysis, options) |
| `docs/archive/resume-prompt-2026-11-11-s37.md` | the resume prompt of session 37 (the first humanistic review of §4, the §5 review planned) |
| `docs/archive/resume-prompt-2026-11-11-s36.md` | the resume prompt of session 36 (the user's review of §5.4, settled points of 5.4) |
| `docs/archive/resume-prompt-2026-11-11-s35.md` | the resume prompt of session 35 (drafting §5.4: open points, numbers to check) |
| `docs/archive/resume-prompt-2026-11-09-s27.md` | the resume prompt of session 27 (decision 7 edits, the first §4 plan) |
| `docs/archive/framework/` | the framework's design sources, replaced by `manuscript/_d_framework.tex`: `formalization.md` (no longer the reference; the manuscript diverged from it) and its review log `feedback.md`, `framework-design.md`, `framework-spine.md`, `feature-provenance-model.md` (the original three-layer model, claims C1-C4), `s33-decision.md`, `sound-directions-math.md`, the review sprint log `sprint-framework-review.md` and its resume prompts |
| `docs/archive/direction-A/` | direction A's original mock and its pilot-scale summary (superseded by `docs/paper-mock.md`) |
| `docs/archive/a-prime/` | A' (dropped 2026-11-02): plan (Section 13 is the record), mock, encoding, literature |
| `docs/archive/explanation-provenance/` | the old direction (dropped 2026-10-22): plan, theory, appendix, related work, experiment notes (`experiments/`), planning documents |
| `docs/archive/paper-prose-2026-11-09/` | the writing skill's old rules and reader model |
| `manuscript/backup/` | cut framework text and tables (2026-11-04 to 11-08) |
