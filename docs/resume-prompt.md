# Resume: complete R7's widening (run 142, `ent` in the attacks, run 143, then the paper); in parallel, the meta-review's triage

**Two lines of work share this prompt.** The R7 track (below, through "The task") and a parallel track orthogonal to
it ("A parallel track", further down). The user says which one a session takes; if unsaid, ask. A session on one track
does not edit the other's passages or files, commits only the files it changed (`git add <paths>`), and, when it
rewrites this prompt at its end, keeps the other track's section, updated only where its own work changed something.

Written at the end of session 53 (2026-11-13); the parallel track's section rewritten in session 54, the R7 track's in session 55. Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. §5 of the paper is
three findings: what hand analysis misses (5.2), what defenses learned from observed attacks miss (5.3), what
robustness costs (5.4). The paper is written straight into `manuscript/*.tex`; check `manuscript/main.aux` before
naming a section, table or theorem number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 11 with its session-52, -53 and -55 additions;
next steps 2b and 2c). The R7 records: `docs/evidence/r7-population-escape.md` (§7 from "Step 2 read" on, and the log)
and `docs/evidence/r7-overlay-rule.md` (session 55).

## Where R7 stands (session 53)

- **Run 138 finished and read.** Step 2 (SizeOfImage escape): monotone 0/40 and 0/41, held. An end-to-end check from
  the *unescaped originals* (run 138 counted only files detected after the escape) found the real hole: the escape
  writes themselves are loader-ignored writes to the certificate and debug data-directory entries, outside the threat
  model, which move those entries' own features against the table. The debug write alone (not piloted by run 138)
  evades 3/40 and 4/41; the certificate write lowers scores slightly but evades no detected original; SizeOfImage and
  the architecture entry never lower them.
- **Decision (user, session 53): the full widening.** A new overwrite `ent` (the certificate and debug entries set to
  any value) joins M_full, and the population lets the data located through them lie past the end. Code (e0f5158,
  opt-in): `catalogue.REGION_OPS["ent"]`, `regions()["ent"]`, `LOOSE_ENTRIES`, `LOOSE_PAST_END_KINDS`,
  `precondition(..., loose=True)`, `declared_changes(..., loose=True)`, `a_directions.py --loose`. Without `--loose`
  the derivation reproduces `a_directions_derived_sums_v2` byte for byte.
- **Run 140** (`run/140_widen_entries.sh`, ~2.5 min, read): table `artifacts/experiments/a_directions_derived_sums_loose`,
  models `seed-0-s10-mfull-{feat,sums}-loose`. Exactly ten features become two-sided (`authenticode:*`,
  `datadirectories:{security_size, debug_size, debug_virtual_address}`); pilot population 88 -> 89 of 100. Cost, TPR at
  1% / 0.1% FPR: sums 89.6/74.8 -> 85.7/68.1, features 87.2/71.0 -> 83.4/65.1 (one seed). Almost all from the
  certificate entry: a writable entry pointed at an appended certificate is signature cloning. The user chose to pay
  it; it is a §5.4 finding (the measured price of robustness to signature cloning), never "small" or "weak".
- **Alternative recorded, not taken:** debug entry only (0.1-0.6 points at 1%), the certificate entry and signature
  cloning left outside the threat model as a stated limitation.
- **Session 55: the closure check, and LIEF's overlay rule.** `catalogue_checks.py --loose` applies every operation,
  `ent` included, to the pilot files and to escaped copies of each (both entries far past the end, one byte past it,
  the debug extent inside the overlay). A session-53 bug was fixed (the loose precondition exempted only the
  certificate's items; aeeace0). Closure failed (run 141) through pefile's overlay rule: data-directory extents decide
  where the overlay starts, so `ent` moved it. The user chose **LIEF's rule** (the overlay starts after the last
  section's raw data; none if that lies past the end), installed in pefile at import by `features.py` (f0d2bb1;
  `PEFILE_OVERLAY_START` keeps pefile's). Scratch check on 50 files: closed, sound, exact. Run 140's table re-derived:
  masks byte-identical, the `-loose` models stand. Population vectors unchanged; ~4% of rows outside it change (the
  stores are re-featurized with the scale-up). **Run 142** (`run/142_overlay_rule_closure.sh`, ~30 min, the user's):
  the same check on all 100 pilot files; hypothesis closed, sound, exact. Read it first if it has finished.
- **Raised by the user (PLAN.md step 2c, not now):** we no longer use EMBER-2024 as is (files below 4 MB, warnings
  dropped, thrember quirks patched, pefile's overlay rule replaced); design the extractor deliberately rather than
  patch it reactively, perhaps on LIEF once a 1.x release fixes 1.0.0's bugs. Decide before the scale-up's
  featurization (`docs/evidence/r7-overlay-rule.md` §6). Memory `may-deviate-from-ember`: parser, feature and sample
  choices are first-class options, weighed on merit, not against prior decisions.

## The task (PLAN.md step 2b, approved by the user)

1. **Read run 142** (if finished; `artifacts/experiments/catalogue_checks/pilot-loose-lief/report.json`: `closed`,
   `pass`, `exact`; `<op>.leaving_population_instances`). Write the reading into the script's header and the R7 record.
   A failure: report it as such and bring the user the cause and options weighed on merit (parser, features,
   population), not only the smallest local patch.
2. **`ent` in the attacks** (code, then smoke test on 2-3 files). `scripts/a1_adaptive.py`: add `ent` to `OVERWRITE`
   and to the menu (zeroing, past the end as `escape_audit.cert_entry`/`debug_entry` write, and signature cloning:
   the certificate entry pointed at an appended certificate taken from a signed goodware donor; check the donors
   include signed files). Byte-level writes with our own functions, never LIEF (memory `own-edits-over-lief`).
3. **Run 143** (a `run/` script for the user, ~5-6 h, `NUM_WORKERS` default 16): run 138's protocol with three escapes
   (`cert_entry`, `image_size`, `debug_entry`) against `unconstrained`, `mfull-feat-loose`, `mfull-sums-loose`, with
   `--threat_model M_full` now including `ent`, and the evasion counted **from the unescaped originals** (detected
   original, undetected end file; add this to `a1_adaptive.py`'s report, e.g. score the original before escaping).
   Hypothesis to fix in the header: no detected original evaded by either monotone detector, since every escape write
   is now in the threat model.
4. **After run 143 is read: the paper** (draft in small blocks with the user, `paper-prose` skill): §4's overwrites
   (add the entry write) and §4.4's population (the two entries' data may lie past the end; no routing: one detector
   scores every file); §5.4's *The price* (new numbers; signature cloning as the reason) and *Where the guarantee
   holds* (the escape result; drop "such files are rare among benign software, and so stand out"; population share as
   n/N); Table 5's monotone rows retrained on the loose table; routing removed from §5.1 and Appendix D; Table 5's
   denominators unrouted. The `-loose` models replace `-pre-v2` wherever the paper's monotone detectors appear: other
   tables' monotone cells (toolkit attacks, MAB-Malware) need reruns or blue values with `% SYNTHETIC` comments;
   decide with the user which, and list what the scale-up must redo. Also the overlay rule: Appendix D's "The overlay
   starts where the last section or data directory ends, so the extent of every section and directory locates it"
   becomes "... where the last section ends, so the extent of every section locates it", and one sentence by "We drop
   the warnings" on the deviation and why (`docs/evidence/r7-overlay-rule.md` §5).

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
