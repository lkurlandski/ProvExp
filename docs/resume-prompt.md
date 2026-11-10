# Resume: §5's structure (the user's concerns), then shortening §4 and §5

Read `docs/status.md` and `PLAN.md` (decisions 3, 6, 8; next steps 3-4). §5 (`manuscript/_f_evaluation.tex`) was
realigned with §3-4 on 2026-11-10 (vocabulary and claims only). The user has "a pretty big concern about the structure
and organization" of §5 and expects to rewrite it: **start by asking them for it**, answer plainly, and agree the new
structure (a plan of one line per paragraph, or a short structural note) before any prose. Use the `paper-prose`
skill; draft in blocks with `make` and `make check`, shown as rendered text.

Constraints carried over: no timing of Prop. 1 against extraction (memory `no-timing-claims`); check
`manuscript/main.aux` before naming a number; §5 ~3,200 words (50-75% over allowed while drafting).

Then: shorten §4 and §5 together (§4 ~1,540 words against ~1,000; §4.3 first), then PLAN.md step 4 (the review prompt,
the full simulated review, the truncation brainstorm).

Loose ends: `% VERIFY` in §4.2 (EMBER 2017/2018 had no parser warnings; needs Joyce et al.'s PDF in `papers/`);
`% VERIFY` on Table 3's "random in-place writes" row (run 93 reports 20 writes per file on 100 + 100 files, 440 and 537
declined, not 2,000 and 209).
