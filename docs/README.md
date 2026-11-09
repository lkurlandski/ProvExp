# Documentation index

Read `docs/status.md` and `PLAN.md` at the start of a session; everything else only when the session's task needs it.
Each entry says when it is worth opening. The manuscript (`manuscript/*.tex`) is the authority on the paper's content;
where a document disagrees with it, the manuscript wins.

## Active

| Document | What it is | Open it when |
|---|---|---|
| `PLAN.md` | thesis, where the paper stands, the decisions of 2026-11-09, next steps, settled decisions | every session |
| `docs/status.md` | current state, what waits on the user, short session log | every session; update at the end |
| `docs/resume-prompt.md` | where the next session starts | starting a session |
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
C1/C4, requirements, Tables A0-A2 for what are now Tables 5-7). Open them to trace a number in the paper to its run,
or when changing an experiment. Run scripts are in `run/` (one per step, numbered), outputs under `artifacts/`.

| Document | Covers |
|---|---|
| `docs/evidence/item-layer-design.md` | the instrumented extractor: item tables, readouts as data, the edit catalogue, the side-effect and direction engines, checks G1-G7 (§4, Tables 5-6) |
| `docs/evidence/direction-A-threat-model.md` | the threat models (additions, shifts, full), hand direction table, re-encodings over sums, the first exactness table (§4.3-4.4, Table 6) |
| `docs/evidence/direction-A-A1-design.md` | the detector table's design, baselines, decisions, and results (Table 7) |
| `docs/evidence/direction-A-expert-set.md` | Gimenez et al.'s 40 features, instrumented: the expert-set row and its holes |

## Archive (superseded; open only to recover a reason or a record)

| Folder or file | Contents |
|---|---|
| `docs/archive/status-log-2026-10-to-2026-11-09.md` | the full session log until 2026-11-09 (32k words; search, don't read) |
| `docs/archive/PLAN-log-2026-10-22-to-2026-11-09.md` | the plan's history, every "Next steps" block |
| `docs/archive/resume-prompt-2026-11-06.md` | the previous resume prompt (research track details: sums-row routing, scale-up budget) |
| `docs/archive/framework/` | the framework's design sources, replaced by `manuscript/_d_framework.tex`: `formalization.md` (no longer the reference; the manuscript diverged from it) and its review log `feedback.md`, `framework-design.md`, `framework-spine.md`, `feature-provenance-model.md` (the original three-layer model, claims C1-C4), `s33-decision.md`, `sound-directions-math.md`, the review sprint log `sprint-framework-review.md` and its resume prompts |
| `docs/archive/direction-A/` | direction A's original mock and its pilot-scale summary (superseded by `docs/paper-mock.md`) |
| `docs/archive/a-prime/` | A' (dropped 2026-11-02): plan (Section 13 is the record), mock, encoding, literature |
| `docs/archive/explanation-provenance/` | the old direction (dropped 2026-10-22): plan, theory, appendix, related work, experiment notes (`experiments/`), planning documents |
| `docs/archive/paper-prose-2026-11-09/` | the writing skill's old rules and reader model |
| `manuscript/backup/` | cut framework text and tables (2026-11-04 to 11-08) |
