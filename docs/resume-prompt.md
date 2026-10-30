# Resume: ProvExp (after 2026-10-30, fourth session): per-row entropy cuts built but insufficient; next: per-row column caps on the append windows, then the full check 1b

Read `CLAUDE.md`, then `docs/status.md`'s top block (fourth session), `PLAN.md` ("Next steps (2026-10-30, fourth
session)"), and `docs/direction-A-prime-encoding.md` in full, ending with "Built: findings (2026-10-30, fourth
session)" (the per-row cuts, why the hypothesis failed, and the ordered "Still open"). Then
`docs/direction-A-prime-mock.md`: Table A'1, "How a solver's answer becomes a file", check 1b (with both smoke and the
fourth-session result) and check 2, and decision 7. Skim `scripts/ap_encoding.py` (`boundary_references`, `ROW_REFS`,
`row_cuts`, `reachable_rows`, `Encoding.__init__`'s windows block, `Program.solve`, `certify`), and
`scripts/ap_check1b.py` (`sides_of`, `score_of`, `attribute`).

**Start by recapping for the user in plain language** where things stand and what is next, before asking anything:
- the research in three sentences;
- A' in two: a detector's true worst case against edits an attacker can make, from an exact solver over the attacker's
  choices; a certificate when no edit evades, edits written as a real file when one does;
- last session (2026-10-30, fourth): per-row entropy cuts were added so each new byte-entropy window's row must carry
  at least that row's nibble entropy (and the header windows were made exact in their row); they are sound and tested
  (160 pass), **but the hypothesis that they close the byte-entropy gap failed.** On the 4 MB file 2826a9a5 (budget
  512 KB, append only) the solver still evades at raw 1.09 against the real 8.63. The new attribution tool shows the
  gap is *real looseness* (byte-entropy and strings), not a realization gap: a row's entropy is bounded, but the joint
  placement of appended nibbles across rows and columns is still free;
- so the plan reorders: tighten the append windows further (per-row column caps, then an aggregate chord bound on the
  appended tail) before the realizer, then re-run containment and the full check 1b.

For every decision you put to the user, say what the thing is, give a concrete example, and say what each choice
changes. Never use doc-internal labels (C3, A4, M_full, G7) without saying what they are.

## State of the code (uncommitted)

`scripts/ap_encoding.py` and `scripts/ap_check1b.py` have this session's changes but are **not committed**, and
**ruff/mypy have not been run** and **containment (`run/111`) has not been re-run** since. Before trusting any solve:
run `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`, then `bash run/111_ap_containment.sh`
(~8 min; you may run it) — it must contain every edit, or a new cut is unsound. Commit in logical pieces once green
(row cuts; attribution). Attribution lines per the session's system reminder.

## Tasks, in order

1. **Per-row column caps on the append windows** (`Encoding.__init__`, the windows block). Check whether the existing
   `colsum - 2*newnib` constraint is per-(row, column) or only pooled across rows. If pooled, a row can claim counts
   in columns the append never supplies; add `we[r][col] <= 2 * (appended nibbles of column col) + boundary slack` so
   each row's column counts are bounded by the appended supply. **State a hypothesis first** (how many of the ~3.8
   remaining byte-entropy points on 2826a9a5 this closes), then re-solve 2826a9a5 with the single-file scratch driver
   at 300 s and read `attribute(...)` (and the `wr*` row occupancies) — do **not** print the full `choice` dict (256
   append-byte variables; it is large and unneeded).
2. **An aggregate chord lower bound on the appended tail as one distribution** (as `section:overlay_entropy` already
   has via the `Ent` chords + mixture floor), so the solver cannot claim low per-window entropy while the appended
   bytes have high aggregate entropy. Re-measure.
3. **Optionally** a piecewise lower bound for the overlay and section entropies (section entropies are free in [0, 8]
   today; weigh the binaries-per-byte-value cost and say so).
4. **The realizer** (`realize(choice) -> bytes`): lay the solver's answer out as a file — appended/section byte
   counts; strings as printable runs (>= 5 chars) separated by a zero byte, with a literal per matched regex; window
   runs grouped by entropy row; section names from a name search hitting the chosen (bucket, sign). Write with
   `scripts/catalogue_checks.py`'s byte-level functions (`add_section(..., before_overlay=False)`), never LIEF;
   re-extract with `SumsFeatureExtractor`, score. Add a round-trip test. Needed for check 2 and to catch any residual
   realization gap once the looseness is down.
5. **Re-run containment** (`run/111`, ~8 min; you may run it) after the changes; it must hold on every edit. Then
   **check 1b** (`run/112`, ~30 min): hand it to the user; update its hypothesis line first. Read its report; a no-go
   goes to the user with decision 7's options (3: lead with another use; then 2: a tighter learned baseline).
6. Then check 2 (at least 70% of solver evasions realize, using the realizer), check 3 (expert set; user decision on
   instrumenting their extractor), Table A'1 at pilot scale.

## A scratch driver you will want

A single-file solve + attribution driver already exists at
`/tmp/.../scratchpad/solve_one.py` from last session but the scratchpad is session-local and gone. Re-create a small
one: load the pilot, build `Encoding(SumsFeatureExtractor(), z, budget(len(z), 0.05, 524288), 3)` for one file prefix,
`certify(enc, ens, tau_raw - TOL, 300)`, then `attribute(ens, r["sides"], enc.x0, groups)` with `groups` keyed by the
feature-name prefix. Threshold: the unconstrained model's is raw 1.103 (from `ts_predictions.parquet` at 1% FPR). Keep
its output to the outcome fields, the per-group scores, and the `wr*` occupancies — never the full append-byte dump
(it tripped a content filter last session).

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep the experiments' complexity down; **run only jobs of ~10 minutes or less yourself (the user
restated: anything over ~15 minutes goes to them as a `run/` script); estimate from the slowest case before starting**;
default 16 workers, never cap workers in Python; state a short hypothesis before each run; add a `run/` script for
every experiment (next number: 113) and record its results in the script's comments once read; commit in logical pieces
after ruff and mypy pass; never edit `tests/reference/`; do not run the full test suite while the user's jobs run.

## Notes

- `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`, and `slides/` are untracked;
  leave them.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. item 6, Gimenez et al.'s quirks).
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}` (3,655 inputs; the 1,087 sums columns are
  never split on). Thresholds at 1% FPR from each model's `ts_predictions.parquet`. The unconstrained model's
  threshold is raw 1.103.
- Pilot facts: every pilot file is <= 4 MB, so the budget is 512 KB everywhere. The battery misses 20 of the
  unconstrained model's 47 detected files; 7 of those fail the precondition (so check 1b's go needs 4 of 13 covered).
- Solver: HiGHS through `scipy.optimize.milp`; unknown options (the 1e-9 tolerances) pass through verbatim. No
  `highspy` installed.
- Kill background jobs by PID, not with `pkill -f` on a pattern that also matches your own shell's command line.
