# Resume: ProvExp (after 2026-10-31): check 1b read, no-go, its evasions do not realize; next: the user's decision 7 choice, then act on it

Read `CLAUDE.md`, then `docs/status.md`'s top block (2026-10-31), `PLAN.md` ("Next steps (2026-10-31)"), and
`docs/direction-A-prime-encoding.md` from "Fifth session, continued" to the end of "Built: findings (2026-10-31)" (the
per-file table and the block model's design). Then `docs/direction-A-prime-mock.md`: Table A'1, check 1b (with its
2026-10-31 result), check 2, check 3, and decision 7 (its four options and "what each outcome means"). Skim
`scripts/ap_encoding.py` (`row_cuts`, `dominance_cuts`, `regex_requirements`, the sections' entropy rows,
`link_ensemble`, `certify`), `scripts/ap_realize.py` (`realize`, `shape_block`, `_strings`, `_place`), and
`scripts/ap_check1b.py` (`attribute`, `_job`).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- A' in two: a detector's true worst case against edits an attacker can make, from an exact solver over the attacker's
  choices; a certificate when no edit evades, edits written as a real file when one does;
- last session (2026-10-31): check 1b (run by the user, 30 min per file) was a **no-go**: of the 13 files the solver
  can cover, 0 certified, 6 solver evasions, 7 undecided (the go was >= 4 certified). All 6 evasions written as files:
  **none evades** (real scores 3.4-6.8 vs the solver's 0.8-1.1; threshold 1.10). The gap is spread over byte-entropy
  (how random each 2 KB stretch is), strings (readable-text counts and matches like URLs), and added sections' entropy;
  no single group closes it alone, and we have not separated looseness in the solver's model from a realizer that
  does not build the file well enough. Each tightening so far moved the gap rather than closing it;
- the decision put to the user (decision 7), unless they already answered it in their first message:
  1. *(recommended)* one bounded tightening round: the exact block model of overlapping byte-entropy windows (designed,
     not built), a sound bound on added sections' entropy, the realizer's string and section repairs; re-solve and
     re-realize the 6 files; stop rule: if >= 3 still do not evade as files, go to 2;
  2. lead A' with another use: the expert-set row (does Gimenez et al.'s add-only guarantee survive our edits; needs
     their extractor instrumented and evasions that realize) or Table A'2 (training on realizable edits; can use our
     own byte-level edits from `catalogue_checks`, without the solver);
  3. the tighter learned baseline (95th-percentile change per feature, ~1 min): a sensitivity row only, does not fix
     the no-go;
  4. pause A' for scaling direction A or the manuscript.
  A longer time limit is not a fix (with a loose model more time mostly finds more fake evasions).

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (C3, A4, M_full, G7) without saying what they are.

## State of the code

Everything is committed (e783464 and the 2026-10-31 wrap-up); ruff and mypy pass on the committed code; `run/111`
(containment) holds on the current encoding (unchanged since). `tests/test_ap_encoding.py` and
`tests/test_ap_realize.py` pass (light checks only). The realization driver of last session was scratch (recipe below).

## Tasks, depending on the user's choice

**Option 1 (tightening round).** State a hypothesis first (which group should drop out of the gap and why). In order,
each sound, each with a test, re-running `run/111` (~8 min) after every encoding change:
1. Section entropies: a sound bound tying each added section's entropy to its byte counts (they are nearly free in
   [0, 8] today; they carry the gap on 4 of 6 files).
2. The exact block model of overlapping windows (design in the encoding note: 1 KB blocks with nibble counts, window k
   = blocks k and k+1, one row binary per window, per-(window, row, nibble) counts, ~8K extra binaries, ~150K rows).
   Check the program still builds and solves in reasonable time on 2826a9a5 before anything else.
3. Realizer repairs: knife-edge histogram splits (nudge byte counts by one toward the solver's side), section contents
   aimed at the solver's section entropies, `drop_tail` honored; strings: compare the solver's string counts with the
   written file's to see whether the gap there is the realizer or the encoding.
4. Re-solve the 6 evading files (600-1,800 s each: as a `run/113` script for the user if over ~15 min in total) and
   re-realize them; apply the stop rule. Then, if it passes, re-run check 1b in full (user).

**Option 2.** Re-open the mock for the chosen use (screening criteria, the table with the model component behind each
column, a falsifiable go/no-go) before any code; be harsh about novelty against the closest work.

**Option 3.** Add the 95th-percentile learned region to `scripts/ap_check1_learned.py` as a flag; report it whichever
way it falls.

## Scratch driver you will want (re-create; the scratchpad is session-local)

`realize_all.py OUTDIR [PREFIX ...]`: for each `artifacts/experiments/ap_check1b/solutions/ref_{name}.npy`, in a fork
pool (one worker per file): load the pilot malware (`a_pv_attacks.load_pilot`), the ref booster
(`artifacts/models/gbdt/seed-0-s10-ref/model.txt`) and `Ensemble(booster)`; rebuild
`Encoding(SumsFeatureExtractor(), z, budget(len(z), 0.05, 524288), 3)`, then `split = link_ensemble(enc, ens)` and
`P.var(f"leaf{i}", 0, 1)` for every leaf, so `len(P.names) == x.size` (assert it); solver sides
`{k: x[v] > 0.5 for k, v in split.items()}`; `realize(enc, P.names, x)`; re-extract and score raw; `attribute(ens,
sides, x_real, groups)` with groups by feature-name prefix before ":"; count differing splits per group (the solver's
value: evaluate `enc.resolve(f)` at `x` for float / `Lin` / `Frac`, else None). Each file: ~2 min build + ~2 min
realize; all 6 in parallel ~6 min. **Never print the full `choice` dict or the 256 append-byte variables.**

For a single re-solve: load as above, `certify(enc, ens, tau_raw - TOL, SECONDS)` (tau_raw 1.103 from
`ts_predictions.parquet` at 1% FPR), print only the outcome fields, save `x`.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep the experiments' complexity down; **run only jobs of ~10 minutes or less yourself (anything
over ~15 minutes goes to the user as a `run/` script); estimate from the slowest case before starting**; default 16
workers, never cap workers in Python; state a short hypothesis before each run; add a `run/` script for every experiment
(next number: 113) and record its results in the script's comments once read; re-run `run/111` after any change to the
encoding, and it must contain every edit; commit in logical pieces after ruff and mypy pass; never edit
`tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}` (3,655 inputs; the 1,087 sums columns are
  never split on). Thresholds at 1% FPR from each model's `ts_predictions.parquet`.
- Pilot facts: every pilot file is <= 4 MB, so the budget is 512 KB everywhere. The battery misses 20 of the
  unconstrained model's 47 detected files; 7 of those fail the precondition (so check 1b's go needs 4 of 13).
- Check 1b outputs: `artifacts/experiments/ap_check1b/{report.json,solves.parquet,solutions/}`; log
  `artifacts/logs/ap_check1b.log`. The 7 undecided files are mostly small (82 KB-1.8 MB, one 4 MB).
- Realizer facts: a byte is printable (thrember's strings: 0x20-0x7f) exactly when its high nibble is 2-7, so the
  window plan fixes each block's printable count; regex literals that also match another regex (e.g. "powershell" and
  "shell") are counted on the strings as written.
- Solver: HiGHS through `scipy.optimize.milp`; unknown options (the 1e-9 tolerances) pass through verbatim. No
  `highspy` installed. Program size on 2826a9a5: ~57K variables, ~116K rows, ~23K binaries.
- Kill background jobs by PID, not with `pkill -f` on a pattern that also matches your own shell's command line.
