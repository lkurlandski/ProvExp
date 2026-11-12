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
| `docs/resume-prompt.md` | where the next session starts (a check-in on whether §5 needs more tables, after Tables 3-4 were remade; then questions and answers, shortening) | starting a session |
| `docs/checkpoint-prompt.md` | the user's prompt for ending a session | the user ends a session |
| `docs/paper-mock.md` | the paper's contributions, outline with word budgets, and tables | planning or writing any section; checking whether new work belongs in the paper |
| `docs/writing-spec.md` | the user's raw reactions to drafts, newest first | writing paper prose (with the `paper-prose` skill) |
| `docs/domain-selection-brainstorming.md` | the user's ideas for other domains | only when the user opens the topic |
| `docs/upstream-issues.md` | thrember and secml-malware bugs, drafted for the user to report | an extractor quirk comes up |
| `docs/design.md` | the `provexp` package's data structures, conventions, thrember quirks | changing code in `src/provexp/` |
| `docs/literature-2026-10-22.md` | related work for the current direction (and for B, C) | related work, novelty, a new application |
| `docs/graveyard.md` | ideas that did not pan out and why; directions the user found unproductive | before proposing a new direction or analysis |
| `docs/reviews/` | simulated reviews (index: `docs/reviews/README.md`; prompt: `review-prompt.md`); latest `2026-11-04-strategy.md`, before it `2026-11-02-body.md` (risk register R1-R16) | before a new review; when weighing what reviewers will miss |
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
| `docs/evidence/held-out-attacks-perspectives.md` | session 33: ways to test defenses learned from attacks (fixed split, leave-one-out mean or worst fold, keep-one, MAB-Malware, all subsets, coverage C2), with strengths and weaknesses; run 131's PV results and C2 | §5.3 |

## Archive (superseded; open only to recover a reason or a record)

| Folder or file | Contents |
|---|---|
| `docs/archive/status-log-2026-11-10-to-11.md` | the session log, sessions 29-34 (search, don't read) |
| `docs/archive/status-log-2026-11-09.md` | the session log, sessions 21-27 (search, don't read) |
| `docs/archive/status-log-2026-10-to-2026-11-09.md` | the full session log until 2026-11-09 (32k words; search, don't read) |
| `docs/archive/PLAN-log-2026-10-22-to-2026-11-09.md` | the plan's history, every "Next steps" block |
| `docs/archive/resume-prompt-2026-11-06.md` | the previous resume prompt (research track details: sums-row routing, scale-up budget) |
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
