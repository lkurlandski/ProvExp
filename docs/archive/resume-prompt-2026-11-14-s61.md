# Resume: read run 143, then R7's paper changes; the decisions before the scale-up

Written at the end of session 57 (2026-11-13), for the next R7 session. Self-contained: everything needed to start is
below or in the files it names. The rebuttal of the 2026-11-12 simulated review runs separately, from
`docs/resume-prompt-rebuttal.md`; this prompt does not cover it. Sessions on the two run in parallel: commit only the
files you changed (`git add <paths>`), and leave the other's uncommitted files alone.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on the EMBER2024 corpus, with an extractor derived from EMBER-v3, is
the instance. §5 of the paper is three findings: what hand analysis misses (5.2), what defenses learned from observed
attacks miss (5.3), what robustness costs (5.4). The paper is written straight into `manuscript/*.tex`; check
`manuscript/main.aux` before naming a section, table or theorem number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 11 and its additions; next steps 2b, 2c, 3). The R7
records: `docs/evidence/r7-population-escape.md` (§7 from "Step 2 read" on, and the log) and
`docs/evidence/r7-overlay-rule.md` (the overlay rule; §6, the extractor question).

## Where R7 stands

R7 is the review's top risk: an attacker can move a file out of the population the guarantee is proven on, with writes
the loader ignores. Settled decisions: **no router** (one monotone detector scores every file; the guarantee is proven
on the population and measured outside it), and **the full widening** (session 53): the threat model gains `ent` (the
certificate and debug data-directory entries set to any value) and the population lets the data they locate lie past
the end of the file.

- **Cost of the widening (run 140, one seed).** Ten features become two-sided (`authenticode:*`,
  `datadirectories:{security_size, debug_size, debug_virtual_address}`) and leave the monotone detectors; pilot
  population 88 -> 89 of 100. TPR at 1% / 0.1% FPR: sums 89.6/74.8 -> 85.7/68.1, features 87.2/71.0 -> 83.4/65.1,
  almost all from the certificate entry, because a writable entry pointed at an appended certificate is **signature
  cloning**. The user pays it: a §5.4 finding, never "small" or "weak". Models `seed-0-s10-mfull-{feat,sums}-loose`,
  table `artifacts/experiments/a_directions_derived_sums_loose`.
- **LIEF's overlay rule (session 55).** pefile starts the overlay after the furthest section *or data-directory*
  extent, so `ent` moved it and the widened population was not closed. The user chose LIEF's rule (after the furthest
  section's raw data), installed in pefile at import by `features.py` (f0d2bb1); on the population the two rules
  agree, ~4% of rows outside it change (re-featurized with the scale-up).
- **Run 142 (closure and exactness, read in session 56):** closed (0 of 13,326 edits on population files leave it,
  escaped copies included), sound (0 violations), exact after one engine fix (3,583 exact, 3,217 declined, 0 wrong).
- **`ent` in the attack (session 56):** zero both entries, point each past the end, and signature cloning from signed
  goodware donors (23/50); byte edits by our own writer, never LIEF.
- **Session 57 re-verified session 56's code** (it had been flagged by a safety classifier): everything holds. Two
  fixes (77587f5): the clone's byte bound covers its alignment padding, and escape runs record `start_in_population`.
  The latter matters for reading run 143: the cert/debug escapes keep all 39 pilot originals in the population, but
  the `image_size` escape (SizeOfImage raised, not an operation of M_full) takes all 39 out, so the guarantee covers
  only the cert/debug escapes' searches.
- **Run 143 is running** (user, started 2026-11-13, 8 workers, so ~10-12 h rather than the script's 5-6 h).
  `run/143_escape_pilot_loose.sh`; outputs
  `artifacts/experiments/escape_pilot_loose/{cert_entry,image_size,debug_entry}/adaptive.json`; log
  `artifacts/logs/escape_pilot_loose.log`. It is R7's last pilot experiment.

## The task (PLAN.md step 2b (iii)-(v))

1. **Read run 143** once it has finished. Per escape, per detector: `detected`, `evaded`, `rate`, `min_delta_logit`,
   `evaded_by_escape`, `in_population`, `start_in_population`, `evaded_outside_population`. Hypothesis (in the
   script's header): no detected original evaded by either monotone `-loose` detector (evaded 0, min_delta_logit 0,
   evaded_by_escape 0); for cert_entry and debug_entry this is the guarantee, for image_size an expectation from run 138
   step 2. A non-zero monotone cell is read against `in_population` and `start_in_population` (a miss the guarantee
   does not cover is not a violation; report it either way); the unconstrained detector ~40-60%. Check for silent
   no-ops (monotone searches ran their full budget; the unconstrained one is evaded). Write the reading into run 143's
   header, `docs/evidence/r7-population-escape.md` §7 and its log, PLAN.md step 2b, `docs/status.md`.
2. **The paper's R7 changes**, drafted with the user in small blocks (`paper-prose` skill). All but one can start
   before run 143 is read:
   - §4's overwrites gain the entry write; §4.4's population lets the two entries' data lie past the end; no routing:
     one detector scores every file.
   - §5.4's *The price*: run 140's numbers, signature cloning as the reason.
   - Routing removed from §5.1 and Appendix D; Table 5's monotone rows from the `-loose` models, its denominators
     unrouted.
   - Appendix D's overlay rule: "The overlay starts where the last section or data directory ends, so the extent of
     every section and directory locates it" becomes "... where the last section ends, so the extent of every section
     locates it", plus one sentence by "We drop the warnings" on the deviation and why (`r7-overlay-rule.md` §5; the
     paper mock's §4.2 line). The extractor's overall framing waits on step 2c.
   - **Waits on run 143:** §5.4's *Where the guarantee holds* (the escape result; drop "such files are rare among
     benign software, and so stand out"; the population share as n/N).
3. **A decision for the user: the other tables' monotone cells.** The toolkit-attack and MAB-Malware cells still use
   the old `-pre-v2` detectors. Either re-run those attacks on the `-loose` models now, or put predicted values in blue
   (`\synthetic{...}` with `% SYNTHETIC` comments naming the run) and let the scale-up measure them. Claude's
   recommendation: blue values, since the scale-up redoes every detector result anyway. Then list in PLAN.md step 3
   what the scale-up must redo for R7.

## Decisions before the scale-up (the user's; PLAN.md steps 2c and 3)

- **The extractor question (step 2c).** We no longer use EMBER-2024 as is: files below 4 MB, warnings dropped,
  thrember quirks patched, pefile's overlay rule replaced. Design the extractor deliberately (principles stated once,
  one audit pass, a deviations table) rather than patch it reactively, and weigh moving the parser to LIEF once a 1.x
  release fixes 1.0.0's bugs (cost: rebuilding the record of the positions the parser reads). Both views and the
  criteria: `docs/evidence/r7-overlay-rule.md` §6; a short LIEF spike (structures vs pefile, timing, exposed offsets)
  would inform it. Cheapest before the scale-up featurizes everything.
- **The scale-up's protocol (step 3).** Seeds 0-2, full splits, files below 4 MB in every split, one training set and
  one attack protocol for every detector, ERDALT to a proper stopping point, enough malware for PV and the expert set,
  the adaptive budget at scale, MAB-Malware as a held-out attack, and, from R7: the escape attacks at scale (look
  actively for further escapes; the user expects more holes may surface), the toolkit attacks on escaped files, the
  population share of attacked malware with its denominator, and the files outside the population re-featurized with
  LIEF's overlay rule. Each item is agreed with the user before code; long runs go to the user as `run/` scripts.
- **Unchanged for now:** the unconstrained `seed-0-s10-ref` was trained on the v1 sums store and is scored on `-v2`
  (same layout; as in runs 105 and 138). The scale-up's single training set removes this.

## Constraints and settled points

- Explain plainly; one recommendation, not a menu. State a hypothesis before any run; report a failed check as such.
- Widen only where evidence forces it; each widening is a separate user decision with its cost measured (memory
  `widen-population-cautiously`).
- No deadline talk; do not reopen settled decisions (PLAN.md; `docs/reviews/process/checklist.md`). Settled: no
  router; the full widening and its cost; §2 unchanged; "any attack" columns; no timing claims; MAB-Malware's role.
- Never propose sandbox execution or obtaining files over 4 MB; loader behaviour argued from documentation.
- Jobs over ~10 minutes go to the user as `run/` scripts; never edit a running `run/` script (run 143's included).
- Before committing: `env/bin/ruff check src tests scripts`, `env/bin/mypy src tests scripts`; the catalogue tests
  (`OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_ember2024_catalogue.py`, ~2 min) after
  touching `catalogue.py`; after manuscript edits, `make` and `make check` in `manuscript/`. Commit to `main` in
  logical pieces; do not push.
- At the end of the session: update `docs/status.md` (its own log entry), PLAN.md and the R7 record; write the next
  resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).
