# Resume: verify session 56's R7 code before run 143, then the paper; in parallel, the meta-review's triage

**Why this session verifies first.** Session 56 (which produced the four R7 commits below and `run/143`) was flagged
by a safety classifier, which may have degraded the work. Nothing in the research is in doubt because of the flag; it
is a reason to re-check session 56's output with fresh eyes before spending ~5-6 h on run 143. The user will run run
143 only once this session clears the code. So the task is: **review and independently re-verify session 56's R7
changes**, report what holds and what does not, and only then hand run 143 back. Do not launch run 143 yourself.

**Two lines of work share this prompt.** The R7 track (below, through "The task") and a parallel track orthogonal to
it ("A parallel track", further down). The user says which one a session takes; if unsaid, ask. A session on one track
does not edit the other's passages or files, commits only the files it changed (`git add <paths>`), and, when it
rewrites this prompt at its end, keeps the other track's section, updated only where its own work changed something.

Written at the end of session 53 (2026-11-13); the parallel track's section rewritten in session 54, the R7 track's at
the end of session 56, for the session that starts once run 143 has finished. Self-contained: everything needed to
start is below or in the files it names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on the EMBER2024 corpus, with an extractor derived from EMBER-v3, is
the instance. §5 of the paper is three findings: what hand analysis misses (5.2), what defenses learned from observed
attacks miss (5.3), what robustness costs (5.4). The paper is written straight into `manuscript/*.tex`; check
`manuscript/main.aux` before naming a section, table or theorem number, and give its title alongside.

**Read first:** `CLAUDE.md` (note the new rule "The parser is not the gold standard"), `docs/status.md`, `PLAN.md`
(decision 11 with its session-52, -53 and -55 additions; next steps 2b and 2c). The R7 records:
`docs/evidence/r7-population-escape.md` (§7 from "Step 2 read" on, and the log) and `docs/evidence/r7-overlay-rule.md`
(session 55: the overlay rule, the options, the extractor question).

## Where R7 stands (end of session 56)

- **The widening (session 53, settled).** Run 138's end-to-end check showed that loader-ignored writes to the
  certificate and debug entries, outside the threat model, moved those entries' own features against the table (the
  debug write alone evaded 3/40 and 4/41). The user chose the full widening: `ent` (both entries set to any value)
  joins M_full, and the population lets the data located through them lie past the end (`catalogue.precondition(...,
  loose=True)`, `a_directions.py --loose`). Run 140: table `artifacts/experiments/a_directions_derived_sums_loose`,
  models `seed-0-s10-mfull-{feat,sums}-loose`; ten features two-sided (`authenticode:*`, `datadirectories:{
  security_size, debug_size, debug_virtual_address}`); pilot population 88 -> 89 of 100; TPR at 1% / 0.1% FPR: sums
  89.6/74.8 -> 85.7/68.1, features 87.2/71.0 -> 83.4/65.1 (one seed), almost all from the certificate entry (signature
  cloning). The user pays it: a §5.4 finding, never "small" or "weak". Debug-only alternative recorded, not taken.
- **The closure check and LIEF's overlay rule (session 55-56).** `catalogue_checks.py --loose` applies every
  operation, `ent` included, to the pilot files and to escaped copies of each: both entries far past the end (`far`),
  one byte past it (`near`), and the debug extent ending inside the overlay (`inside`). The user chose **LIEF's overlay
  rule** (after the furthest section's raw data; none if that lies past the end), installed in pefile at import by
  `features.py` (`overlay_data_start_offset`; pefile's kept as `PEFILE_OVERLAY_START`; f0d2bb1). On the population the
  two rules agree; ~4% of rows outside it change (re-featurized with the scale-up). **Run 142 (full pilot, read in
  session 56):** closed (0 of 13,326 edits on files in the population leave it; the 89 originals in it, all 89 `far`,
  89 `near`, 46 `inside` copies too), sound (0 violations), exact after one engine fix (3,583 exact, 3,217 declined, 0
  wrong). 16 declared edits on one file's `far`/`near` copies raised an error -- a certificate inside `.rsrc`,
  stretched past the end, that an insertion before the overlay splits; the engine now **declines an insertion that
  splits an item's members** (e0fa5b8, re-checked on that file). Step 0's re-derived loose table matches the `-loose`
  models' `monotone_constraints` feature by feature, so the models stand.
- **`ent` in the attacks (session 56, done).** `a1_adaptive.py`'s menu and M_full now have `ent`: zero both entries,
  point each past the end (`_past_end`), and signature cloning (a signed goodware donor's certificate appended, the
  security entry pointed at it; 23/50 pilot donors are signed, blobs collected in `Donors.certificates`). Byte edits
  via `catalogue_checks`'s `_entry_write`/`_past_end`, never LIEF. The inplace growth accounting was fixed so the
  clone's append counts against the byte budget (868b8b6). Smoke: the loose monotone detector holds under the full
  menu; signature cloning rebuilds the authenticode chain (num_certs, chain_max_depth, signing times).
- **Run 143 scripted, waiting on the user** (`run/143_escape_pilot_loose.sh`, ~5-6 h, `NUM_WORKERS` default 16).
  Evasion counted **from the unescaped originals** (0949a9c; each row gains `p_orig`, `in_population`,
  `evaded_by_escape`, `evaded_outside_population`). Smoke (debug_entry, M_full): `mfull-sums-loose` 0/5 (+0.0000), 0
  by escape alone, where run 138 saw the debug write evade 4/41. Outputs
  `artifacts/experiments/escape_pilot_loose/{cert_entry,image_size,debug_entry}/adaptive.json`; log
  `artifacts/logs/escape_pilot_loose.log`.
- **Raised by the user (PLAN.md step 2c, not now):** we no longer use EMBER-2024 as is (files below 4 MB, warnings
  dropped, thrember quirks patched, pefile's overlay rule replaced). Design the extractor deliberately rather than
  patch it reactively, perhaps on LIEF once a 1.x release fixes 1.0.0's bugs; decide before the scale-up's
  featurization (`docs/evidence/r7-overlay-rule.md` §6 has both views and the criteria). Memory
  `may-deviate-from-ember` and CLAUDE.md: parser, feature and sample choices are first-class options, weighed on merit,
  not against earlier decisions.

## The task: verify session 56, then clear run 143 (PLAN.md step 2b, approved by the user)

Session 56's four R7 commits are on `main` (from `2f6087c`): `e0fa5b8` (the engine decline + the two catalogue
filters), `868b8b6` (`ent` in the attack), `0949a9c` (count from the unescaped originals), `8a058d2`
(`run/143_escape_pilot_loose.sh`), `933faba` (docs). Read each `git show`, check it against the claims in "Where R7
stands", and re-run the quick checks yourself. Report per item: **holds**, **wrong** (with the fix), or **unsure**
(what to resolve). State a hypothesis before each re-run. All checks below are quick (≤ a few minutes); the one that
is not (re-running run 142 fully, ~17 min) is optional and goes to the user if wanted.

1. **The engine decline (`e0fa5b8`), the one change that could silently corrupt results.** `reach.predict_structural`
   now declines "an edit splits the members of items" (via the new `reach.splits`, which tests terms' and attributes'
   ranges, not locating ranges), and `catalogue._declare_section` / `predict_insert_gap` drop a certificate the
   insertion splits so the engine declines it. Verify: (a) `splits` is correct and the decline fires only when an
   insertion lands strictly inside a member range; (b) it did not turn any *previously exact* prediction into a
   decline beyond the 16 intended rows -- re-run the single-file check on `74aecb25...` (the scratch command is in
   run 142's header; ~1 min) and confirm exactly 16 rows flip exact→flagged and nothing else moves; the surer check is
   a full re-run of run 142 (~17 min, step 0 then the checker) and confirming `pass/closed` hold and the exact tally is
   3,583/3,217/0 -- offer this to the user. (c) catalogue tests pass
   (`OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_ember2024_catalogue.py`, ~2 min).
2. **`ent` in the attack (`868b8b6`).** (a) The attack's M_full ops must match the ops the `-loose` directions were
   derived with -- if the attack carries an op the detector was not constrained on, a "hole" would be spurious, and if
   it omits one the test is incomplete. Confirm `THREAT["M_full"]` now contains `ent` and that `a_directions.py
   --loose` (run 140) derived the `-loose` masks over the same op set (`LOOSE_OPS` in `catalogue_checks.py`; the
   models' `monotone_constraints` already matched the table in session 56). (b) Re-run the `ent`-only and the full-menu
   smokes (2-3 files, `--score real`, `mfull-sums-loose` with `--sound`) and confirm the monotone detector is not
   evaded (`min_delta_logit` 0). (c) Spot-check the three `ent` thunks on one file (zero / past-end / clone) move the
   expected `datadirectories:*` and `authenticode:*` features and that `Donors.certificates` is non-empty. (d) The
   clone appends a certificate: confirm the growth now counts against the byte budget (the `inplace` fix).
3. **Count from the unescaped originals (`0949a9c`).** Re-run the `debug_entry` escape smoke (~6 files) and check the
   report: `detected` is gated on the *original's* score, the search starts from the *escaped* file, `evaded` is the
   end file, and `evaded_by_escape` flags an escape that alone crossed the threshold. Confirm `mfull-sums-loose` is
   0-evaded (run 138 saw the debug write evade 4/41), and that the new columns are populated.
4. **The run 143 script (`8a058d2`).** Re-read it: the three model paths exist with `ts_predictions.parquet`, the
   feature store matches session 56's (`ember2024-sums-10-v2`), both monotone detectors are under `--sound`,
   `--threat_model M_full`, `NUM_WORKERS`/`OMP_NUM_THREADS` wired, the hypothesis stated, resources honest
   (`bash -n` passes). Fix anything off; do **not** run it.

**When the code is cleared,** tell the user plainly what holds, and hand run 143 back for them to run. The sessions
after that (deferred here, unchanged from session 56's plan):

- **Read run 143.** Per escape, per detector: `detected`, `evaded`, `rate`, `min_delta_logit`, `evaded_by_escape`,
  `in_population`, `evaded_outside_population`. Hypothesis: no detected original evaded by either monotone `-loose`
  detector (evaded 0, min_delta_logit 0, evaded_by_escape 0). A non-zero monotone cell read against `in_population`
  (a miss outside the loose population is not a guarantee violation; report it either way). Write the reading into run
  143's header, `docs/evidence/r7-population-escape.md` §7 and its log, PLAN.md step 2b (iii), `docs/status.md`.
- **The paper** (draft in small blocks with the user, `paper-prose` skill): §4's overwrites
  (add the entry write) and §4.4's population (the two entries' data may lie past the end; no routing: one detector
  scores every file); §5.4's *The price* (new numbers; signature cloning as the reason) and *Where the guarantee
  holds* (the escape result; drop "such files are rare among benign software, and so stand out"; population share as
  n/N); Table 5's monotone rows retrained on the loose table; routing removed from §5.1 and Appendix D; Table 5's
  denominators unrouted. The `-loose` models replace `-pre-v2` wherever the paper's monotone detectors appear: other
  tables' monotone cells (toolkit attacks, MAB-Malware) need reruns or blue values with `% SYNTHETIC` comments;
  decide with the user which, and list what the scale-up must redo. The overlay rule: Appendix D's "The overlay starts
  where the last section or data directory ends, so the extent of every section and directory locates it" becomes
  "... where the last section ends, so the extent of every section locates it", and one sentence by "We drop the
  warnings" on the deviation and why (`docs/evidence/r7-overlay-rule.md` §5; the paper mock's §4.2 line). How the
  extractor is framed overall waits on step 2c.

## A parallel track (orthogonal to R7)

**Done in session 53b (parallel to session 53): R17** (Reviewer A, W1 and W3). The ratio rule needs only *a = 0
whenever b = 0*, weaker than the old *b > 0*, which EMBER's files without strings violated (Table 1, Appendix C,
Appendix D; 11ff54d). Theorem 1 holds for sums in *totally ordered* monoids (Fuchs 1963), with §3.3's −3 example
showing why (b1060e8). Rejected by the user: the universality/locality "gap" (items are hierarchical, so the framework
stays well-defined at its limit, a strength; a deeper look at how item size and locality matter is welcome as an idea,
not as a fix). Dropped: Appendix D's minima sentence. How to handle framework gaps: memory `elegant-framework-fixes`.

**Session 54 (parallel track): no edits; the next session triages the meta-review.** Asked for directions orthogonal
to R7, Claude relayed reviewer C's R18 ("the learned defenses get less information, so the outcome is built in") as a
flaw. The user pointed out that failing on unseen edits *is* §5.3's finding, and then said they no longer trust
Claude's reading of the meta-review: many reviewer comments are misguided or flat out wrong, and Claude cannot tell
them from real limitations. Cause: Claude leans toward accepting criticism, and the meta-review is the same model with
the same lean; its "correct" verdicts mostly confirm that a quote is accurate, not that the objection matters. Memory
`distrust-simulated-reviews`.

**Superseded (session 57, 2026-11-13):** the triage below is replaced by the *meta-rebuttal*, with its own resume
prompt, `docs/resume-prompt-rebuttal.md`, and record, `docs/reviews/2026-11-12-body/meta-rebuttal.md` (one item per
session; Claude now gives an opinion after a neutral analysis). Start parallel-track sessions there; the text below
is kept for reference until this prompt is next rewritten.

**Next on this track (the user's request): triage the meta-review, item by item, with the user judging.** Source:
`docs/reviews/2026-11-12-body/meta-review.md` (register in §6; per-finding verdicts in §3; the reviews themselves in
`reviewer-{A,B,C,D}.md`). Already triaged, skip: R7 (decision 11), R1 (decision 12), R6 (session 50), R17 (session
53b). To triage: R2, R3, R4, R5, R8, R9, R11, R12, R13, R14, R15, R16, R18, R19, R20, R21, plus the meta-review's §5
items ("what the reviewers missed") not covered by these. Procedure, per item, in batches of four to six:
- **The claim attacked:** the sentence of the `.tex` the criticism targets, quoted (or "no claim of ours": then the
  item is likely about scope).
- **The criticism:** the reviewer's own words, quoted, with the finding ID; check every factual premise against the
  manuscript, the code, stored outputs or `papers/` (the meta-review's checks are not evidence).
- **The strongest rebuttal**, written as the authors' advocate; settled points (PLAN.md, the review's checklist) count.
- No recommendation, no proposed work. The user marks each: **wrong** (drop), **outside the claim** (nothing, or one
  sentence), or **real** (needs work). Only after the verdict: for "real" items, the smallest fix, one recommendation.

Record the verdicts with the user's one-line reasons in a new `docs/reviews/2026-11-12-body/triage.md` (also the R7,
R1, R6, R17 outcomes, one line each, pointing to their records), and index it in `docs/reviews/README.md`. Watch for
the R18 pattern: a criticism that attacks a claim the paper does not make, or that restates the finding as a flaw.
Session 54's sketch of orthogonal directions (R18's trial table, R12's recount without the 88 warnings, R19's ERDALT
checks, R2's multi-byte probe) is **not** an input: it was written before the user's verdicts and is to be rebuilt
from them. The earlier recommendation (§6, R21) waits for the triage too.

**R7 owns (this track leaves alone):** §4.3.1 and Table 2, §4.4, §5.1's setup and routing, §5.4, Table 5, Appendix
D's population and routing text, and `catalogue.py`, `a_directions.py`, `a1_adaptive.py`, `catalogue_checks.py`.

## Constraints and settled points

- Explain plainly; one recommendation, not a menu. State a hypothesis before any run; report a failed check as such.
- Widen only where evidence forces it; each widening is a separate user decision with its cost measured (memory
  `widen-population-cautiously`). At the scale-up, look actively for further escapes.
- No deadline talk; do not reopen settled decisions (PLAN.md; `docs/reviews/process/checklist.md`). Settled: no
  router; the full widening and its cost; §2 unchanged; "any attack" columns; no timing claims; MAB-Malware's role.
- Never propose sandbox execution or obtaining files over 4 MB; loader behaviour argued from documentation.
- Jobs over ~10 minutes go to the user as `run/` scripts; never edit a running `run/` script.
- Before committing: `env/bin/ruff check src tests scripts`, `env/bin/mypy src tests scripts`; the catalogue tests
  (`OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_ember2024_catalogue.py`, ~2 min) after
  touching `catalogue.py`; after manuscript edits, `make` and `make check` in `manuscript/`. Commit to `main` in
  logical pieces; do not push.
- At the end of the session: update `docs/status.md` (its own log entry), PLAN.md and, on the R7 track, the R7 record;
  write the next resume prompt, keeping the other track's section (archive
  this one under `docs/archive/` and index it in `docs/README.md`).
