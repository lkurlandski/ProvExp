# Resume: read runs 138 and 139, then the rest of the review's register

Written at the end of session 49 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper is written
straight into `manuscript/*.tex`; check `manuscript/main.aux` before naming a number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decisions 11 and 12; next step 3), and
`docs/evidence/r7-population-escape.md` (the R7 record). The review: `docs/reviews/2026-11-12-body/meta-review.md`
(§6, the risk register; §8, the writing actions).

## Where things stand

- **R7 (decision 11):** no router; one monotone detector scores every file. Run 138 (`run/138_escape_pilot.sh`,
  started 16:03 on 2026-11-12, ~5-6 h) tests it: escaped pilot malware attacked by the beam search with every candidate
  extracted. The paper is unchanged for R7 until it is read.
- **R1 (decision 12, session 49):** MAB-Malware joins the attacks (the authors' code in `third_party/mab_malware`,
  run by `scripts/mab_attack.py` single-threaded with a direct hand-over to our detectors, tested equal to upstream's
  own hand-over; no code randomization; the toolkit's 50 donors). Run 139 (`run/139_mab_malware.sh`, ~1-1.5 h, for the
  user) attacks every detector of Tables 4 and 5 and the expert set, unrouted. The manuscript already describes it:
  §5.1, 5.3, 5.4, Tables 4-5 now report "evaded by any attack", and the new Table 11 (`tab:ember:per-attack`,
  Appendix D) reports each attack; every value involving MAB-Malware is a blue prediction (`% SYNTHETIC` comments).
- In session 49 the user corrected two of Claude's points: "an attack we did not write" is no argument (the toolkit
  is not ours either), and the adaptive attack *is* stronger per attack (the review had compared it with a union).
  Claude's hybrid scoring was dropped: our prediction is slower than extraction (0.17 s vs 0.09 s per candidate).

## The task

1. **Check runs 138 and 139** (`artifacts/logs/escape_pilot.log`, `artifacts/logs/mab_malware-*.log`;
   `artifacts/experiments/escape_pilot/*/adaptive.json`, `artifacts/experiments/mab_malware/*/table.json`). Report each
   against its script header's hypothesis, held or failed, counts beside denominators. Look at the run directories
   (`artifacts/experiments/mab_malware/*/work/log/`) for hangs or silent no-ops before trusting a count (upstream had
   one endless loop already; memory `attack-strength-vs-literature`).
2. **Run 139 read:** replace the blue MAB-Malware values (Tables 4, 5, 11; 5.3's PV and adversarial-training sentences;
   5.4's price, width and beyond-the-guarantee sentences) with measured ones; the "any attack" cells are unions per
   file over the toolkit, the adaptive attack and MAB-Malware (the comments under each table say which outputs). If PV
   is not evaded by renames, or a monotone detector is evaded on a file in the population, stop and discuss before
   rewording. Split MAB-Malware's evasions on the additions detector into inside/outside by the minimal actions
   (`results.parquet`, column `minimal`).
3. **Run 138 read:** continue R7 as `docs/archive/resume-prompt-2026-11-12-s48.md`, part A, describes (the plan of
   what decision 11 changes in §4.4, §5.4, §5.1 and Appendix D).
4. **Two open questions for the user**, one recommendation each:
   - §2 promises "the attack scoring without extraction" (decision 6); with `--score real` at the scale-up, Proposition
     1 no longer scores the attack's candidates (PLAN.md, decision 12 (iii)). Keep predicted scoring where it applies
     (about twice the cost), or drop that use from §2 and §5.1. Do not reframe it without the user.
   - Scale first or widen first (PLAN.md, next step 3); Claude recommended widening first, then one scale-up.
5. **The rest of the register**, in small passes with the reviewers' IDs and R-numbers (memory
   `review-comments-workflow`): R2 (one paragraph of trusted parts with their checks and counts; closure argued from
   the locating record for overwrites; a multi-byte marker probe of the record, under 10 minutes, Claude may run it),
   R18 (reopen decision 6: two-round adversarial training and PV rebuilt from the adaptive attack's outputs over all
   twelve operations, attacked by the adaptive attack and MAB-Malware; Claude would skip the trial table), R6 (the
   classical/new paragraph in §3 and §6; the incremental-parsing contrast), and the cheap writing batch (meta-review
   §8: Theorem 1's monoid hypothesis, the ratio's side condition, a locality sentence, certified defenses in §6, the
   five uncited bib entries, the 100-query budget attributed to Gimenez et al.'s released code, Appendix D's minima).
   These were proposed in session 49; the user approved only R1 so far.

## Constraints and settled points

- Explain plainly, no jargon; one recommendation rather than a menu. State a hypothesis before any run; report a
  failed check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for.
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB.
- Jobs over ~10 minutes go to the user as `run/` scripts (NUM_WORKERS, default 16). Never edit a running `run/`
  script; sync its comments afterwards (runs 138 and 139 record their readings in their headers).
- `pkill -f <pattern>` also kills the shell running it when the pattern occurs in that command line; kill by PID.
- At the end of the session: update `docs/status.md`, PLAN.md and the R7 record; write the next resume prompt
  (archive this one under `docs/archive/` and index it in `docs/README.md`).
