# Resume: continue addressing the 2026-11-12 meta-review (runs 138 and 139, or a new weakness)

Written at the end of session 50 (2026-11-12). Self-contained: everything needed to start is below or in the files it
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

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decisions 11 and 12; next step 3). The review:
`docs/reviews/2026-11-12-body/meta-review.md` (§1 summary, §6 the risk register R1-R21, §7 what the full-scale run
must include, §8 the writing actions; the four reviews `reviewer-{A,B,C,D}.md` only when an item needs them). A
simulated CCS review: A Weak accept (formal methods), B Weak reject (adversarial malware), C Weak reject (robust ML),
D Weak accept (systems security).

## What the last sessions did

- **Session 48, R7 (the guarantee covers only the population).** Decision 11 (user): no router; one monotone detector
  scores every file; the guarantee is proven on the population and measured outside it; widen the population for one
  clause (option 5) only if an escape breaks the monotone detectors. Record: `docs/evidence/r7-population-escape.md`.
- **Session 49, R1 (attacks below published strength).** Decision 12 (user): MAB-Malware (vendored in
  `third_party/mab_malware`, driven by `scripts/mab_attack.py`) runs against every detector; the body's tables report
  "evaded by any attack" (union per file over toolkit, adaptive, MAB-Malware), each attack separately in Appendix D's
  Table 11 (`tab:ember:per-attack`); `--score real` at the scale-up; §2 unchanged (settled). All MAB-Malware values in
  the manuscript are blue `\synthetic{}` predictions with `% SYNTHETIC` comments: §5.1 *Attacks*; 5.3 ("3 of the 9,
  each time with a rename"; "and so does MAB-Malware (20 of 50, against 30 of 49)"); 5.4 *The price* ("MAB-Malware
  alone on 30"), *The width of the threat model*, *Beyond the guarantee*; Tables 4, 5 and 11.
- **Session 50, R6 (the formal results are known techniques), done.** The user rejected a "what is classical, what is
  new" ledger ("effectively neuters the entire paper"): credit the shoulders we stand on without demeaning the
  contribution, which lies in the combination (memory `credit-without-diminishing`); one or two seminal works per
  idea. Applied (660ba90): Gray et al.'s observation on maxima in §3.1; incremental view maintenance carried over to
  features in §3.2; abstract interpretation (Cousot and Cousot) after Theorem 1; §6's incorrect contrast with
  incremental parsing replaced, with Calzavara et al. (the one new bib entry). Notes on 16 works, with quotes:
  `docs/evidence/r6-prior-work.md` (includes Cheney et al. for R2 and Labaca-Castro et al. for R21, deferred there).

## The runs: state at the end of session 50 (seen in the logs, not yet read or checked)

**Run 138** (`run/138_escape_pilot.sh`, ~5-6 h from 16:03; log `artifacts/logs/escape_pilot.log`): the 50 pilot
malware escaped by a certificate write (step 1, `cert_entry`) and a SizeOfImage write (step 2, `image_size`), then the
adaptive beam search with `--score real`. Hypothesis (script header, R7 record §7): monotone detectors evaded on 0-3 of
about 40 escaped files each, largest score drop small; unconstrained about 40-50%.
- Step 1 finished (`artifacts/experiments/escape_pilot/cert_entry/adaptive.{json,parquet}`). The log's summary lines:
  unconstrained 40/48; `mfull-feat` 1/41; `mfull-sums` 1/43; the monotone detectors' largest drops are about
  -3.1 and -3.2 logits, which is **not** small. This matters: decision 11's option 5 is triggered if an escape breaks
  the monotone detectors.
- Step 2 was running.

**Run 139** (`run/139_mab_malware.sh`, the user runs it with `NUM_WORKERS=4` in tmux; logs
`artifacts/logs/mab_malware-{full,pv,sums,expert}.log`; outputs
`artifacts/experiments/mab_malware/<step>/{results.parquet,table.json}`, upstream's logs and written files under
`.../work/<detector>/`). Hypothesis (header): about 60% evaded on the unconstrained detectors; PV ~3/9 by renames;
adversarial training ~20/50; ERDALT ~10/29; expert set ~2/8; monotone full-model detectors 0 in the population;
additions detector ~10/43, all by actions outside additions. The smoke (in the header) already suggested the
unconstrained part would fail.
- From the logs: unconstrained (`gbdt/seed-0`) 0/49 (16 over budget); adversarial training 4/50; PV 7/9;
  `mfull-feat` 0/40; `mfull-sums` 0/41; additions detector (`madd-sums`) 1/42; ERDALT 6/29.
- `sums` was still running (the unconstrained s10 detector at least); `expert` had not started.

## The task: pick the line by the state of the runs

First check both runs. A crash shows as a traceback in the log, or as a step whose output is missing while no process
runs (`ps -eo pid,etime,args | grep -E "a1_adaptive|mab_attack"`). If both are done, do line A, then line B.

**A. Run 138 done (or crashed): R7.**
1. If it crashed, find why from the log, fix, smoke-test on 2-3 files, and hand the user a resume command. Check
   whether the script skips finished steps. Then move to C.
2. Read it against the hypothesis, per detector and per escape, held or failed, each count beside its denominator.
   Record the reading in the run script's header and in the R7 record (§7 and the log).
3. Step 1 already shows a monotone detector evaded with a drop of about 3 logits. Find the side effect that did it:
   rebuild the written file from the `ops` column, compare its extraction with the original's, and name the features
   that fell and the clause of the population the escape broke. Then weigh option 5 for that clause (widen the
   population, with the signature extended for the affected kinds) against the alternatives in the R7 record. Give one
   recommendation and get the user's decision before changing anything.
4. If the monotone detectors hold (or once option 5 is settled), plan what decision 11 changes in the paper:
   - §4.4's last paragraph: no routing.
   - §5.4's *Where the guarantee holds*: the escape result; remove "such files are rare among benign software, and so
     stand out"; the population share as n/N.
   - Any mention of routing in §5.1 and Appendix D.
   - Table 5's denominators, which are still the routed toolkit's.

   Draft in small blocks with the user (`paper-prose` skill), or record the plan if the user prefers to write after
   the scale-up. Then list what the scale-up needs for R7: the toolkit attacks on escaped files (their harness needs
   `--escape` support), the still-detected share per attack column, and the population share of attacked malware with
   its denominator.

**B. Run 139 done (or crashed): R1.**
1. If it crashed, diagnose as in A.1. A hang shows as a run directory whose `log/rewriter.log` stopped advancing.
2. Before trusting any count, look for silent no-ops (memory `attack-strength-vs-literature`):
   - the `p_lowest` column against `p_clean`;
   - the bandit's alpha/beta lines at the end of each `rewriter.log`;
   - which actions evasive files kept (`minimal`).
3. Read it against the hypothesis, per detector, held or failed, counts beside denominators. Record the reading in the
   run 139 header and in PLAN.md (decision 12). The logs already show the unconstrained part failed (0/49) and PV far
   above the prediction (7/9).
4. Replace the blue values with measured ones: Tables 4, 5 and 11, and the 5.3 and 5.4 sentences above. Each "any
   attack" cell is the union per file over the toolkit, the adaptive attack and MAB-Malware; the comments under each
   table name the outputs. For Table 5's bottom half, split MAB-Malware's evasions into inside and outside additions
   by the actions in `minimal`: OA/OA1 append and SA/SA1 add a section are inside; everything else is outside.
5. MAB-Malware evades the unconstrained detector on no file, so sentences that claim otherwise must be reworded, not
   just renumbered: "and so does MAB-Malware", "MAB-Malware alone on 30", and "with MAB-Malware's renames and
   removals". Before rewording, compare its rate with Zainab et al.'s honestly: their model, operating point, query
   budget and donors (`papers/zainab2026breaking.pdf`). Ask the user before changing what the MAB-Malware result is
   used for in the paper. PV at 7/9 strengthens 5.3's PV finding; check from `minimal` whether the evasions use renames.
6. Two results would need discussion before any text changes:
   - If PV is not evaded by renames, say so plainly; 5.3's PV finding rests on the adaptive attack in any case.
   - If a monotone detector is evaded on a file in the population, stop and discuss it with the user first.

**C. Neither run done: choose a new weakness, orthogonal to R7 and R1.** Triage the register (meta-review §6) with
memory `review-comments-workflow`: plain words, the reviewers' IDs (`A-W1`, ...) and the R-numbers kept, one
recommendation per item, small passes, approved items first. Orthogonal means no edits to the §5 text that lines A
and B will rewrite (§4.4's last paragraph, §5.4's *Where the guarantee holds*, *The price*, *The width*, *Beyond the
guarantee*, Tables 4, 5 and 11, 5.3's MAB sentences), and no runs that compete with 138 and 139 for cores. Candidates,
best fit first:
- **The cheap writing batch (meta-review §8, minus R6 and the parts in lines A and B):**
  - R17 (A-W1, A-W3): Theorem 1's hypothesis on the monoids; the ratio's side condition in Definition 10; one
    locality sentence after Definition 8.
  - R21: a paragraph in §6 on certified malware defenses (RS-Del, DRSM, Gibert et al., Giri et al.); Labaca-Castro
    et al. in §6's constraints paragraph (notes in `docs/evidence/r6-prior-work.md`); the bib entries still cited
    nowhere (`cortellazzi2025intriguing`, `kantchelian2016evasion`, `lucas2024training`; recheck).
  - "100 queries per file, as in Gimenez et al." attributed to their released code (their paper says 60 s per
    attack); this sits in §5.3, outside the MAB sentences.
  - Appendix D's minima: they are 0 on every file, not only on files without sections.
  - §4.3.1: name the attacker and word the code-level exclusion accurately against Lucas et al. 2021.
- **R2 (premises tested, not proven):** a paragraph at the end of §4.3.2 or §4.4 listing the trusted parts, each with
  its check and its count:
  - contribution functions: bit-exact;
  - declared changes: re-extraction;
  - the locating-position record: flips and crafted edits (Cheney et al.'s dependency provenance is the reference
    for why the record is a checked approximation; notes in `docs/evidence/r6-prior-work.md`);
  - the vocabulary: the tables from 100 and 2,000 files are equal;
  - closure: 0 of 56,902.

  Also argue closure for overwrites from the record, and run a multi-byte marker probe of the record (MZ, PE,
  Rich/DanS, magic values written at every header and directory position): under 10 minutes, Claude may run it,
  niced, while 138 and 139 run.
- Not now: R18 (adversarial training and PV given all twelve operations, decision 6 revisited) depends on line B's
  attacks; R11 and R20 are the scale-up; R4 (one instance) is the user's call.

Recommend one (Claude's view: the cheap writing batch, R17 first, since it touches only §3 and Appendix D). Get
approval before editing. When citing prior work, follow session 50's lesson: credit without diminishing, one or two
seminal works per idea.

## Constraints and settled points

- Explain plainly, no jargon; one recommendation rather than a menu. State a hypothesis before any run; report a
  failed check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for. Settled: §2 stays as it is; widen first, then scale; "any attack"
  columns; no timing claims, and never propose Proposition 1 as a speed-up for our runs; R6's framing (session 50).
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB. Loader behaviour is argued
  from documentation.
- Blue (`\synthetic{}`) for values of runs not yet read, with a `% SYNTHETIC` comment naming the run.
- Jobs over ~10 minutes go to the user as `run/` scripts (`NUM_WORKERS`, default 16). Never edit a running `run/`
  script; record readings in its header afterwards.
- `pkill -f <pattern>` also kills the shell running it when the pattern occurs in that command line, and run 138's
  workers are `multiprocessing.spawn` processes too: kill by PID only. Scripts that spawn workers need an
  `if __name__ == "__main__":` guard.
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`; after manuscript
  edits, `make` and `make check` in `manuscript/`. Commit to `main` in logical pieces; do not push.
- At the end of the session: update `docs/status.md`, PLAN.md and the R7 record; write the next resume prompt (archive
  this one under `docs/archive/` and index it in `docs/README.md`).
