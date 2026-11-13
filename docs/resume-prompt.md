# Resume: complete R7's widening (closure check, `ent` in the attacks, run 141, then the paper); in parallel, §6 (R21)

**Two lines of work share this prompt.** The R7 track (below, through "The task") and a parallel track orthogonal to
it ("A parallel track", further down). The user says which one a session takes; if unsaid, ask. A session on one track
does not edit the other's passages or files, commits only the files it changed (`git add <paths>`), and, when it
rewrites this prompt at its end, keeps the other track's section, updated only where its own work changed something.

Written at the end of session 53 (2026-11-13); the parallel track's section rewritten in session 54. Self-contained: everything needed to start is below or in the files it
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

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 11 with its session-52 and session-53 additions;
next step 2b). The R7 record: `docs/evidence/r7-population-escape.md` (§7 from "Step 2 read" on, and the log).

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

## The task (PLAN.md step 2b, approved by the user)

1. **Closure and exactness on the widened population** (Claude; pilot; under 10 minutes, niced). Hypothesis first.
   Every operation, `ent` included, applied to the pilot files that pass `precondition(..., loose=True)`: none may
   leave the widened population, and the computed changes must match re-extraction (the machinery of
   `scripts/catalogue_checks.py` and run 117; `catalogue_checks.py` has its own `OPS` and `rdb`/`rsg` handling at
   ~line 268 to extend). Known risk: pefile's overlay rule reads the debug entry's extent (only when it lies within
   the file), so an `ent` write pointing inside the file, or an append that brings an escaped debug extent back
   inside, can move the overlay's start and trip `plain_layout`'s overlay clause. If closure fails, bring the user
   the smallest readable fix (memory `elegant-framework-fixes`: no new clauses for small details; show concrete
   old/new text). Report a failed check as such.
2. **`ent` in the attacks** (code, then smoke test on 2-3 files). `scripts/a1_adaptive.py`: add `ent` to `OVERWRITE`
   and to the menu (zeroing, past the end as `escape_audit.cert_entry`/`debug_entry` write, and signature cloning:
   the certificate entry pointed at an appended certificate taken from a signed goodware donor; check the donors
   include signed files). Byte-level writes with our own functions, never LIEF (memory `own-edits-over-lief`).
3. **Run 141** (a `run/` script for the user, ~5-6 h, `NUM_WORKERS` default 16): run 138's protocol with three escapes
   (`cert_entry`, `image_size`, `debug_entry`) against `unconstrained`, `mfull-feat-loose`, `mfull-sums-loose`, with
   `--threat_model M_full` now including `ent`, and the evasion counted **from the unescaped originals** (detected
   original, undetected end file; add this to `a1_adaptive.py`'s report, e.g. score the original before escaping).
   Hypothesis to fix in the header: no detected original evaded by either monotone detector, since every escape write
   is now in the threat model.
4. **After run 141 is read: the paper** (draft in small blocks with the user, `paper-prose` skill): §4's overwrites
   (add the entry write) and §4.4's population (the two entries' data may lie past the end; no routing: one detector
   scores every file); §5.4's *The price* (new numbers; signature cloning as the reason) and *Where the guarantee
   holds* (the escape result; drop "such files are rare among benign software, and so stand out"; population share as
   n/N); Table 5's monotone rows retrained on the loose table; routing removed from §5.1 and Appendix D; Table 5's
   denominators unrouted. The `-loose` models replace `-pre-v2` wherever the paper's monotone detectors appear: other
   tables' monotone cells (toolkit attacks, MAB-Malware) need reruns or blue values with `% SYNTHETIC` comments;
   decide with the user which, and list what the scale-up must redo.

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
