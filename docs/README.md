# Documentation index

Read only the session's resume prompt at the start of a session (self-contained); open `docs/status.md`, `PLAN.md`,
`docs/decisions.md` and everything else by section, only when the session's task needs it.
Each entry says when it is worth opening. The manuscript (`manuscript/*.tex`) is the authority on the paper's content;
where a document disagrees with it, the manuscript wins.

## The paper's numbering (compiled 2026-11-12)

Documents written before 2026-11-12 may use older numbers; the compiled PDF wins. Before naming a number to the user,
check `manuscript/main.aux` (`grep newlabel manuscript/main.aux`), and add the title or label alongside it.

| Kind | Compiled numbers |
|---|---|
| Sections | 1 Introduction; 2 Background and Motivation; 3 Measuring Edits Across Feature Mappings (3.1 Sum-then-Readout Extractors, 3.2 Edits and Their Side Effects, 3.3 Sound Directions); 4 Instantiating the Framework (4.1 EMBER and PE Files, 4.2 EMBER as a Sum-then-Readout Extractor, 4.3 Threat Model with 4.3.1 Operations and 4.3.2 Signature, 4.4 Population); 5 Evaluation (5.1 Setup, 5.2 What Hand Analysis Misses, 5.3 What Observed Attacks Miss, 5.4 What Robustness Costs); 6 Related Work; 7 Discussion; Appendix A Symbol Table, B Types, Monoids, and Folds, C Proofs for the Framework, D The EMBER Instance |
| Definitions | 1 Items, 2 Sums, 3 Contributions, 4 Readouts, 5 Sum-then-readout extractor, 6 Item delta, 7 Threat models and directions, 8 Changes and signatures, 9 Directions of sums, 10 Derived table |
| Results | Proposition 1 (side effects), Theorem 1 (sound directions), Lemma 1 (closure), Corollary 1 (monotone detectors); the readout rule (unnumbered, Equation 11, used by Definition 10); Algorithm 1 (the extractor) |
| Tables | 1 readout rules (§3.3), 2 operations of the threat model (§4.3), 3 hand vs derived directions (§5.2), 4 learned defenses (§5.3, `tab:eval:learned`, added session 44), 5 detectors (§5.4), 6 symbols, 7 sign table (Appendix C), 8 EMBER readouts, 9 side effects, 10 leave-one-out (Appendix D) |

## Active

| Document | What it is | Open it when |
|---|---|---|
| `PLAN.md` | thesis, where the paper stands, next steps | when the task needs a step (by section) |
| `docs/scaleup-protocol.md` | PLAN.md step 3 in full: every decision of the scale-up's protocol, items (a)-(g) and (1)-(14) ("step 3 (g)") | when a task touches the scale-up's protocol, jobs or reading |
| `docs/decisions.md` | the numbered standing decisions (of 2026-11-09 and after; "decision N") and the settled decisions | when a task touches one |
| `docs/status.md` | current state, what waits on the user, short session log | when needed; update at the end of every session |
| `pipeline/README.md` | the scale-up's stages and steps, and which step produces each result of the paper | before running or adding any experiment |
| `SETUP.md` | from a fresh clone to a system that runs `pipeline/` (environment, dataset, system config, the check) | setting up a new machine or the clusters |
| `docs/resume-prompt.md` | general work and the index of the tracks (since session 82): §2's closing and contribution 4 against §5, what waits on the user, the theory follow-ups; a table of the tracks and their prompts | starting a session when no track is named, or to see where each track stands |
| `docs/resume-prompt-experiments.md` | every experiment of the scale-up (session 104): read every current result with the user (ERDALT's folds included), plan and run the reruns (the guaranteed detectors on the changed M_full table, the toolkit and material with GAMMA through our writers and the set-based validity rule, the learned defenses, ERDALT's attacks), PV's setup, `6-results` | starting a cluster session |
| `docs/erdalt-diagnosis-plan.md` | ERDALT's collapse at scale and its repair, sessions 89-100: the refuted ceiling, the port's differences (input scale chiefly), round 2, the rescaled retrain and its result (validation 0.978, test 0.981, 35,594 violations against a criterion of 381) | Appendix D's statement of each rescaling; tracing why ERDALT was retrained as it was |
| `docs/resume-prompt-writing.md` | the writing track (Opus): the humanistic review and polish of §3, §4, §5, one subsection per pass, one fix at a time (cuts go to `docs/review-cuts.md` for a later length pass); §2 after, its closing waits for a discussion | starting a writing session |
| `docs/resume-prompt-theory.md` | where the next theory session starts (on Opus): bounds on size, the mathematics done (`theory-analysis.md`, part H), the user's decision on what enters the manuscript first | starting the next theory session |
| `docs/evidence/proof-notes.md` | five small corrections to §3.3 and Appendix C (session 73); notes 1-4 applied in session 74, note 5 as a predicted sentence in §5.1 that waits for a pipeline call | the pipeline call for note 5 |
| `docs/evidence/theory-analysis.md` | the theory session's record (session 74): A, the proof audit; B, the theory in brief; C, six candidate ideas and what was weighed; D, the two worked out (Lemma 1, the readout rule) with what reading the code says about EMBER; E, what is next, with starting points for bounds on size; F, session 75's mathematics note on bounds on size (the statement, the hunt on Algorithm 1, what A' does and does not settle, decisions for the user); G, session 76: the user's review, the read of the pilot's derived table (nothing to show on EMBER at the paper's budget), the "somewhat monotone" detector; H, the hand-off: the statements in final form with proofs, the closest work read, options and traps for the text | choosing or working on a theory direction; the instance work for Lemma 1 |
| `docs/reviews/rebuttal-prompt.md` | the rebuttal procedure, kept for reference: once `run_rebuttal.sh` has written the triage, the user decides on the triage table, then on drafts of the groups worth investigating. The 2026-11-12 triage is complete; the next revisit folds into `docs/resume-prompt.md` | re-running the rebuttal procedure on a future review |
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
| `docs/evidence/extractor-audit.md` | The extractor audit pass (session 65): our deviations from EMBER v3, the new candidates with counts on 2,000 test files (directory off-by-one, entry rule, alignment bits, pefile's early stops, string typos), recommendations, the proposed deviations table for Appendix D | the deviations table, any change to `features.py` before the scale-up's featurization |
| `docs/evidence/gamma-lief-relayout.md` | session 101: the guaranteed detectors' toolkit evasions traced to LIEF's relayout (no soundness failure); the validity rule's count gap measured (~1-2% of GAMMA outputs); header room for our writers; the decisions (GAMMA through our writers, validity by sets); session 102: `hgr`, the fifth layout clause; session 103: the reruns read (M_full changed), GAMMA's room per file, option A (not applicable without room), the implementation and its checks | anything about GAMMA, LIEF rebuilds, the validity rule, or adding sections when the headers are full |
| `docs/evidence/r7-overlay-rule.md` | R7 (session 55): pefile's overlay rule breaks the widened population's closure; LIEF vs pefile vs EMBER v2, the mechanisms behind R7's escapes, options weighed, LIEF's rule chosen; the extractor question (designed, not patched; LIEF) | anything about the overlay, the parser choice, or deviations from EMBER-v3 |
| `docs/evidence/r18-trial-competitor.md` | R18 (session 60): the trial competitor (a monotone detector on the table learned by systematic trial), its table against the derived one, the smoke attack (signature cloning through a string count trial never moved), run 144, and the recommendation on iterated adversarial training | §5's contrast with trial; R18; adversarial training at the scale-up |
| `docs/evidence/r6-prior-work.md` | R6 (session 50): the prior work §3 builds on (view maintenance, change calculi, aggregate provenance, abstract interpretation, certified defenses, incremental parsing), each read and related to Proposition 1, Theorem 1, Corollary 1; where each is cited | positioning §3 and §6 against prior work; R6, R21 |
| `docs/evidence/held-out-attacks-perspectives.md` | session 33: ways to test defenses learned from attacks (fixed split, leave-one-out mean or worst fold, keep-one, MAB-Malware, all subsets, coverage C2), with strengths and weaknesses; run 131's PV results and C2 | §5.3 |

## Archive (superseded; open only to recover a reason or a record)

| Folder or file | Contents |
|---|---|
| `docs/archive/related-work-plan-2026-11-17-s84.md` | §6's assessment and 30-40% cut plan (session 83), the user's guidance on related work, source checks (Šrndić and Laskov, FENCE, Sheatsley et al., Dyrmishi et al., Bostani et al., Simonetto et al.), and the close reading of Tsingenopoulos et al.; applied in session 84 |
| `docs/archive/resume-prompt-experiments-2026-11-20-s103.md` | the experiments resume prompt written in session 103: merge GAMMA through our writers (done in session 104), the validity rule by sets (done in session 104: sections by virtual address), reading every result and the reruns (moved to session 105) |
| `docs/archive/resume-prompt-experiments-2026-11-20-s102.md` | the experiments resume prompt written in session 102: read the reruns of `hgr` and the fifth clause (done in session 103: M_full changed), GAMMA through our writers (done, held on `hgr`), the validity rule by sets (not started) |
| `docs/archive/resume-prompt-experiments-2026-11-19-s94.md` | the experiments resume prompt of session 94: check ERDALT's rescaled retrain and release its folds (done in session 100), the toolkit's evasions of the guaranteed detectors (located in session 100: GAMMA's LIEF rebuild suspected), PV's setup, reading every result |
| `docs/archive/resume-prompt-erdalt-2026-11-19-s91.md` | the ERDALT track's prompt (session 91): round 2 of the diagnosis and the retrain decision (done in session 94; the retrain read in session 100) |
| `docs/archive/resume-prompt-experiments-2026-11-18-s85.md` | the experiments resume prompt written in session 85: check and read the reruns after the validity rule and the shift patch (all finished by session 94, unread; replaced by the holistic prompt) |
| `docs/archive/resume-prompt-experiments-2026-11-17-s82.md` | the experiments resume prompt of session 85 (written in session 82): check the attacks run without ERDALT (done in session 85: `toolkit` and `adaptive` finished, MAB-Malware's zero-section crash patched and `ours` resubmitted, `zainab` read; found PV's 5/1,000 detection and 3 lost adaptive searches) |
| `docs/archive/resume-prompt-2026-11-17-s84-writing.md` | the writing resume prompt of session 84 (written in session 83): apply the §6 cut plan (done: 1,843 -> 1,284 words) |
| `docs/archive/status-log-2026-11-12.md` | the session log, sessions 41-42 (search, don't read) |
| `docs/archive/status-log-2026-11-10-to-11.md` | the session log, sessions 29-39 (search, don't read) |
| `docs/archive/resume-prompt-2026-11-17-s82.md` | the resume prompt of session 82 (written in session 81): the scale-up's last jobs (done in session 82: `iterated` read, the file store at one fixed location with no fallback, ERDALT's collapse read and set apart as its own track, the other attacks resubmitted without ERDALT; the prompt split into tracks) |
| `docs/archive/resume-prompt-2026-11-17-s81.md` | the resume prompt of session 81 (written in session 78): check in on the scale-up (done in session 81: the thread overload behind `iterated`'s lost tasks and MAB-Malware `zainab`'s crash fixed in `common.sh`, MAB's shell commands checked and donor names kept, the adaptive search's setup parallelized, the chain resubmitted) |
| `docs/archive/resume-prompt-2026-11-17-s78.md` | the resume prompt of session 78 (written in session 77): check in on the scale-up (done in session 78: the repair read, the per-attack denominator decided, walltimes tightened, the jobs' resources right-sized and `learned` split) |
| `docs/archive/resume-prompt-2026-11-16-s77.md` | the resume prompt of session 77 (written in session 74): failures as they come (done in session 77: the GAMMA OOM traced to LIEF's rebuild and prevented, the material repaired, the chain resubmitted) |
| `docs/archive/resume-prompt-2026-11-16-s74.md` | the resume prompt of session 74 (written in session 70): the head-node session (done in session 74: tigris set up, `pipeline/submit.sh`, decision 12 on the derived table) |
| `docs/archive/resume-prompt-2026-11-15-s70.md` | the resume prompt of session 70 (written in session 69): the two open scale-up questions (decided in session 70: the derived tables from training files with the evaluation set as a check; iterated adversarial training from the adversarially trained detector) |
| `docs/archive/resume-prompt-2026-11-15-s69.md` | the resume prompt of session 69 (written in session 68): lightweight optimization of the scale-up's hot spots (done in session 69: three bit-identical changes, the adaptive candidate ~3x cheaper) |
| `docs/archive/resume-prompt-2026-11-15-s68.md` | the resume prompt of session 68 (written in session 67): the scale-up's remaining `run.sh` steps (all done in session 68; `pipeline/README.md`) |
| `docs/archive/resume-prompt-2026-11-15-s67.md` | the resume prompt of session 67 (written in session 66): the scale-up's protocol items, malware count first (all decided in session 67; PLAN.md step 3 (g)) |
| `docs/archive/resume-prompt-2026-11-15-s66.md` | the resume prompt of session 66 (written in session 65): the audit's five decisions, the deviations table, the `features.py` fixes (all done in session 66) |
| `docs/archive/resume-prompt-2026-11-14-s64.md` | the resume prompt of session 64 (written in session 63): the refactoring before the scale-up (done in session 64: `pipeline/`, `SETUP.md`, byte-identical to the old code) |
| `docs/archive/resume-prompt-2026-11-14-s65.md` | the resume prompt of session 65 (written in session 64): the extractor audit pass (done in session 65: `docs/evidence/extractor-audit.md`; run.sh for every audit step) |
| `docs/archive/status-log-2026-11-13-s59-60.md` | the status log of sessions 59-60 (R2's 4-byte Rich fix, the trial competitor built and run 144 scripted) |
| `docs/archive/status-log-2026-11-14-s61-62.md` | the status log of sessions 61-62 (run 143 read, R7 done at pilot scale, the decisions before the scale-up, run 144 prepared) |
| `docs/archive/status-log-2026-11-15-to-16-s66-76.md` | the status log of sessions 66-76 (the scale-up's protocol and steps, the cost-of-robustness detour, the head node, the theory sessions) |
| `docs/archive/PLAN-done-steps-2026-11-17.md` | PLAN.md's next steps 1-2c in full (4 MB population, the simulated review, R7's widening, the extractor question), done; and "Where the paper stands" as of session 62 |
| `docs/archive/status-log-2026-11-14-s64-65.md` | the status log of sessions 64-65 (the refactoring into `pipeline/`, the extractor audit pass) |
| `docs/archive/status-log-2026-11-14-s63.md` | the status log of session 63 (the review revisit closed and the scale-up's shape agreed; run 144 read and R18 decided) |
| `docs/archive/status-log-2026-11-13-s55-58.md` | the status log of sessions 55-58 (R7's closure check and LIEF's overlay rule, `ent` in the attacks, run 143 cleared, the triage table) |
| `docs/archive/resume-prompt-2026-11-14-R18.md` | the R18 track's resume prompt (sessions 60-63): the trial competitor, run 144 and the three decisions (all done in session 63; record in `docs/evidence/r18-trial-competitor.md`) |
| `docs/archive/resume-prompt-2026-11-14-s63.md` | the resume prompt of session 63 (written in session 62): the last review/rebuttal revisit (nothing else before the scale-up) and the scale-up's shape (one seed, 5,000 candidates, the refactor) |
| `docs/archive/resume-prompt-2026-11-16-s75-theory.md` | the resume prompt of session 75 (written in the theory session 74): choose a theory direction with the user (done: bounds on size) |
| `docs/archive/resume-prompt-2026-11-16-head-node.md` | the head-node prompt as the theory track last had it (the head-node session is done; the other copy is `resume-prompt-2026-11-16-s74.md`) |
| `docs/archive/resume-prompt-2026-11-16-s74-theory.md` | the resume prompt of the theory session 74 (written in session 73): the proof audit, then ideas to strengthen the theory; its section 2 lists what went wrong in sessions 71-73 |
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
