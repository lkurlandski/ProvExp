# Resume: ProvExp, after 3-A (next: 3-C)

We're resuming ProvExp. Read `CLAUDE.md`, then `docs/status.md` (the table, "Next", and the 2026-10-12 decisions),
then `PLAN.md`'s "Paper structure" (especially the screening criteria in section 3 and the 3-C bullet), then
`docs/cm_plan.md` (3-A, the model for what a finished application looks like). Skim `docs/related_work.md`, section H.

## Where things stand

- **Framework and intrinsic evaluation:** done at pilot scale (CP's theory, PB1, PF1; PB2/PF2 demoted).
- **3-A, the pullback's application: done at pilot scale and written up** (runs 30-33; `docs/cm_plan.md`;
  `manuscript/_d_applications.tex`). The GBDT on EMBER v3 and MalConv compared byte by byte: their shared reliance (in
  the header; missed by window-level comparison without P) and the triage of their disagreements (MalConv-only
  verdicts rest on bytes the GBDT does not read; GBDT-only verdicts on header bytes MalConv reads the other way,
  visible only at byte level). Deferred: seeds 1-2 (scale-up), real-attack transfer (`PLAN.md`, "Open questions").
- **3-B: dropped** (`docs/archive/shortcuts_plan.md`). Its findings rested on named features; its post-mortem gave the
  screening criteria.
- **3-C, the pushforward's application: adopted, not designed.** A YARA or capa match is a problem-space explanation
  of a rule-based detector; pushed forward, it is cast in the GBDT's features, so per-rule feature profiles can be
  compared with what the GBDT relies on. A coverage check stopped early: public YARA signatures are too sparse;
  generic rule sets and capa are untested; capa's default backend is very slow.

## What to do next

1. **Settle 3-C's design with me before writing code.** Screen it against the criteria in `PLAN.md` (section 3):
   what only the pushforward gives, the practical task, the realistic alternative (what a practitioner does today
   without P), and a go/no-go check on existing data (e.g., rule coverage on the 100 pilot files) whose failing
   outcome is stated in advance. Present one recommendation, not a survey.
2. Then build 3-C at pilot scale, the way 3-A was built: a short hypothesis before each run, a numbered `run/`
   script per step, results in an experiment doc and `PLAN.md`, then the manuscript.
3. Later: rewrite claims 1-3 (ask before changing what a claim is for); reorganize `_d_applications.tex` into
   intrinsic / extrinsic; the scale-up, all experiments together, when I decide.

## How to work

- Stay on the current task; every analysis must strengthen its claim. Batch validity checks; defer the merely
  interesting to `PLAN.md`'s "Open questions".
- Decide scope with me in one or two exchanges, then execute without a stream of micro-questions or reframings.
- Runs over about 10-15 minutes: smoke-test, then give me the `run/` script; shorter runs you can do yourself.
- Pilot scale (100 files, one seed) until I decide otherwise. Keep docs short and current; update `docs/status.md` at
  the end of the session. Commit in logical pieces; do not push.
