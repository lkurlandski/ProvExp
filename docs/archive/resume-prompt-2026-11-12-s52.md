# Resume: read step 2 of run 138 and settle option 5 for R7 (or R17 if the run is still going)

Written at the end of session 52 (2026-11-12). Self-contained: everything needed to start is below or in the files it
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

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 11, with its session-52 addition; decision 12; next
step 3). The R7 record: `docs/evidence/r7-population-escape.md` (§4 the escape audit, §5 the options, §6 the decision,
§7 the pilot and step 1's reading). The review: `docs/reviews/2026-11-12-body/meta-review.md` (§6 the risk register
R1-R21, §7 the scale-up's content, §8 the writing actions).

## Where R7 stands

Decision 11 (user, session 48): no router; one monotone detector scores every file; the guarantee is proven on the
population and measured outside it; widen the population for a clause (option 5) only if an escape breaks the monotone
detectors.

**Run 138** (`run/138_escape_pilot.sh`; log `artifacts/logs/escape_pilot.log`; outputs
`artifacts/experiments/escape_pilot/{cert_entry,image_size}/adaptive.{json,parquet}`, read with polars, not pandas):
the 50 pilot malware escaped, then attacked by the adaptive beam search scoring by extraction (`--score real`).
Hypothesis (script header): monotone detectors evaded on 0-3 of ~40 escaped files each, largest drop small;
unconstrained ~40-50%.

**Step 1 (certificate escape), read in session 52:** unconstrained 40/48; `mfull-feat` 1/41, `mfull-sums` 1/43. The
count held; the size failed (drops -3.1 and -3.2 logits). Both evasions are the same signed 18 KB file
(`396eb6ec...e6d7`), by one operation at query 50 (added section against the features, append against the sums). How:
the escape extends the certificate entry past the end of the file, so the signature no longer parses and the
`authenticode:*` features fall to 0 (the score *rises* 1.5-1.7 logits); the append brings the entry back inside the file,
the signature parses, and those features rise again. The monotone detectors hold them at -1 ("can only fall"), so the
rise lowers the score. Clause broken: *the certificate table lies inside the file*. The end file is ~1.4 logits below
the unescaped original, from the escape's larger `datadirectories:security_size` (also -1). Caveat: the unescaped
original was not detected by either monotone detector (0.84 vs 1.45; 0.71 vs 1.29 logits).

**The user's decision (session 52):** option 5 for the certificate clause is acceptable (the signature features and
the certificate size made two-sided under appends and added sections, with the detection cost checked), **but with
caution**: "when we scale things up, I'm worried that additional issues and holes will surface." Each widening is a
separate, explicit decision, never a routine patch (memory `widen-population-cautiously`). Its final form waits for
step 2.

**Step 2 (SizeOfImage escape):** at 100 of 128 tasks at the end of session 52. Check: `ps -eo pid,etime,args | grep
a1_adaptive`; finished when `image_size/adaptive.json` exists and the log ends with "Done."; a crash shows as a
traceback or a missing JSON with no process running. Kill by PID only (`pkill -f` also kills the shell, and the
workers are spawn processes).

## The task

**A. Run 138 finished: complete R7.**
1. If it crashed, find why from the log, fix, smoke-test on 2-3 files, and hand the user a resume command for step 2
   only.
2. Read step 2 against the hypothesis, per detector, each count beside its denominator, held or failed. For every
   monotone evasion, rebuild the file and compare extractions (the session-52 approach: escape the original with
   `escape_audit.WRITES`, apply the operation the `ops` column names with a stand-in content (zeros, random, constant;
   the exact candidate content is not stored), extract with `SumsFeatureExtractor`, and diff the append's effect on the
   original against its effect on the escaped file). Name the features that moved against the table, the clause
   broken, and the starting score of the unescaped original.
3. Record the reading in run 138's header (the run will have finished, so the script may be edited) and in the R7
   record (§7 and the log).
4. Give **one** recommendation for option 5's final form across both escapes: which features become two-sided under
   which operations, how to measure the detection cost (signatures are a strong benign signal), and what re-derivation
   and retraining it needs (smoke-test; anything over ~10 minutes goes to the user as a `run/` script with
   `NUM_WORKERS`). Remember the user's caution: widen only where the evidence forces it, and say plainly if step 2
   suggests a pattern of holes rather than one or two clauses. Get the user's decision before changing anything.
5. Then plan the paper's R7 changes (decision 11): §4.4's last paragraph (no routing); §5.4's *Where the guarantee
   holds* (the escape result; remove "such files are rare among benign software, and so stand out"; the population
   share as n/N); the still-blue "each monotone detector on a single file" in *The price*; routing in §5.1 and
   Appendix D; Table 5's denominators (the routed toolkit's; unrouted, MAB-Malware detects 41 and 42 on the sums rows).
   Draft in small blocks with the user (`paper-prose` skill), or record the plan if the user prefers to write after the
   scale-up. List what the scale-up needs for R7: the toolkit attacks on escaped files (their harness needs `--escape`
   support), the still-detected share per attack column, the population share of attacked malware, and an active search
   for further escapes (the user's concern).

**B. Run 138 still running: R17**, recommended in session 52 and not yet approved, so ask first. It touches only §3
and Appendix D (orthogonal to R7): Theorem 1's hypothesis on how totals combine (additive sums and pools, or ordered
monoids with a monotone operation); the ratio's side condition carried into Definition 10, with why it holds on EMBER;
one locality sentence after Definition 8 (any mapping fits with one whole-input item; the results are informative when
items are local). Reviewer IDs A-W1, A-W3; meta-review §6 R17 and §8 item 3. Draft with the `paper-prose` skill, in
small blocks. Other orthogonal candidates if R17 is done: the rest of the cheap writing batch (R21's certified-defense
paragraph and missing citations; "100 queries per file" attributed to Gimenez et al.'s released code; Appendix D's
minima; §4.3.1's attacker and the Lucas et al. 2021 wording), or R2's trust paragraph with the multi-byte marker probe
(under 10 minutes, niced).

## Constraints and settled points

- Explain plainly, no jargon; one recommendation rather than a menu. State a hypothesis before any run; report a
  failed check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for. Settled: §2 stays as it is; widen first, then scale; "any attack"
  columns; no timing claims; R6's framing; MAB-Malware's role in §5; option 5 acceptable for the certificate clause
  (form pending).
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB. Loader behaviour is argued
  from documentation.
- Blue (`\synthetic{}`) for values of runs not yet read, with a `% SYNTHETIC` comment naming the run. Remaining blue
  in §5: "a single file" (*The price*) and 89% (*Where the guarantee holds*), both line A and the scale-up.
- Jobs over ~10 minutes go to the user as `run/` scripts (`NUM_WORKERS`, default 16). Never edit a running `run/`
  script; record readings in its header afterwards.
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`; after manuscript
  edits, `make` and `make check` in `manuscript/`. Commit to `main` in logical pieces; do not push.
- At the end of the session: update `docs/status.md`, PLAN.md and the R7 record; write the next resume prompt (archive
  this one under `docs/archive/` and index it in `docs/README.md`).
