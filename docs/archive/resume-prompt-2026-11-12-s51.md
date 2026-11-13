# Resume: continue addressing the 2026-11-12 meta-review (run 138 for R7, or the next weakness)

Written at the end of session 51 (2026-11-12). Self-contained: everything needed to start is below or in the files it
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
- **Session 49, R1 (attacks below published strength).** Decision 12: MAB-Malware runs against every detector; the
  body's tables report "evaded by any attack", each attack separately in Appendix D's Table 11.
- **Session 50, R6 (the formal results are known techniques), done.** Credit what we build on without conceding each
  result (memory `credit-without-diminishing`); one or two seminal works per idea.
- **Session 51, R1's run read and written in (52a46ec, 5dc17b5).** Run 139 (MAB-Malware) has no silent no-ops.
  Unconstrained full set 0/49 (16 evasive outputs over the byte budget), 10% detector 10/47; PV 7/9, each by a rename
  alone; adversarial training 4/50; ERDALT 6/29; expert set 4/8 by renames; additions detector 1/42 by a debug-entry
  removal; both monotone full-model detectors 0, and in about 2,400 actions each their score never fell below the
  clean score, including the 11-12 files outside the population. Zainab et al.'s 83.4% is at 0.1% FPR with no byte
  limit; that explains most of the gap. Tables 4, 5 and 11 are measured. With the user's approval, MAB-Malware's
  role in §5 changed: evidence that the monotone scores never fall (5.4 *The price*, *Beyond the guarantee*) and a
  second attack that finds PV's rename hole (5.3); it no longer claims to break the undefended or the adversarially
  trained detector. Appendix D compares the rates. Readings: run 139's header, PLAN.md decision 12.

## Open from session 51 (small; ask the user, then apply)

A consistency pass over §5 left three proposals unanswered:
1. 5.2 *Gimenez et al.'s expert set* says the adaptive attack evades the expert-set detector on 2 of 8, while Table 5
   now shows 4/8 (MAB-Malware's renames). Proposed: add ", and MAB-Malware, by renaming sections, on 4".
2. 5.4 says twice that MAB-Malware never lowers the monotone scores (*The price*, *Beyond the guarantee*). Proposed:
   keep both (different points), or shorten the second to "These outputs too never lower either monotone detector's
   score."
3. 5.1 *Attacks*: "which of seven actions ... without its code-randomization action" can read as six. Proposed:
   "which of its actions".
The two "Unconstrained" training sets (Table 4 full, Table 5 10%) wait for the scale-up (user, session 51).

## The task: pick the line by the state of run 138

**Run 138** (`run/138_escape_pilot.sh`; log `artifacts/logs/escape_pilot.log`): the 50 pilot malware escaped by a
certificate write (step 1, `cert_entry`, finished) and a SizeOfImage write (step 2, `image_size`, at 100 of 128 tasks
at the end of session 51), then the adaptive beam search with `--score real`. Hypothesis (script header, R7 record
§7): monotone detectors evaded on 0-3 of about 40 escaped files each, largest score drop small; unconstrained about
40-50%. Step 1's log summary: unconstrained 40/48; `mfull-feat` 1/41; `mfull-sums` 1/43; largest monotone drops
about -3.1 and -3.2 logits, which is **not** small, and decision 11's option 5 is triggered if an escape breaks the
monotone detectors. Check: `ps -eo pid,etime,args | grep a1_adaptive`; a crash shows as a traceback in the log or a
missing `artifacts/experiments/escape_pilot/image_size/adaptive.json` with no process running.

**A. Run 138 done (or crashed): R7.**
1. If it crashed, find why from the log, fix, smoke-test on 2-3 files, and hand the user a resume command (check
   whether the script skips finished steps). Then move to B.
2. Read it against the hypothesis, per detector and per escape, held or failed, each count beside its denominator.
   Record the reading in the run script's header and in the R7 record (§7 and the log).
3. Find the side effect behind each monotone evasion: rebuild the written file from the `ops` column, compare its
   extraction with the original's, name the features that fell and the population clause the escape broke. Weigh
   option 5 for that clause (widen the population, with the signature extended for the affected kinds) against the
   alternatives in the R7 record. Note for the weighing: run 139 showed MAB-Malware never lowering a monotone score
   on unrouted files outside the population, but those files were not escaped deliberately. Give one recommendation
   and get the user's decision before changing anything.
4. Once option 5 is settled (or not needed), plan what decision 11 changes in the paper: §4.4's last paragraph (no
   routing); §5.4's *Where the guarantee holds* (the escape result; remove "such files are rare among benign software,
   and so stand out"; the population share as n/N); the still-blue "each monotone detector on a single file" in *The
   price* (it is the routed toolkit's evasion on a file outside the population); routing in §5.1 and Appendix D;
   Table 5's denominators (the routed toolkit's; unrouted, MAB-Malware detects 41 and 42 on the sums rows). Draft in
   small blocks with the user (`paper-prose` skill), or record the plan if the user prefers to write after the
   scale-up. Then list what the scale-up needs for R7: the toolkit attacks on escaped files (their harness needs
   `--escape` support), the still-detected share per attack column, the population share of attacked malware.

**B. Run 138 still running: the next weakness, orthogonal to R7.** Triage the register (meta-review §6) with memory
`review-comments-workflow`: plain words, the reviewers' IDs (`A-W1`, ...) and the R-numbers kept, one recommendation
per item, small passes, approved items first. Orthogonal means no edits to the text line A will rewrite (§4.4's last
paragraph, §5.4's *Where the guarantee holds*, Table 5's denominators) and no runs that compete with run 138 for
cores. R1 and R6 are done. Candidates, best fit first:
- **The cheap writing batch (meta-review §8):**
  - R17 (A-W1, A-W3): Theorem 1's hypothesis on the monoids; the ratio's side condition in Definition 10; one
    locality sentence after Definition 8.
  - R21: a paragraph in §6 on certified malware defenses (RS-Del, DRSM, Gibert et al., Giri et al.); Labaca-Castro
    et al. in §6's constraints paragraph (notes in `docs/evidence/r6-prior-work.md`); the bib entries still cited
    nowhere (`cortellazzi2025intriguing`, `kantchelian2016evasion`, `lucas2024training`; recheck).
  - "100 queries per file, as in Gimenez et al." attributed to their released code (their paper says 60 s per
    attack), in §5.1.
  - Appendix D's minima: they are 0 on every file, not only on files without sections.
  - §4.3.1: name the attacker and word the code-level exclusion accurately against Lucas et al. 2021.
- **R2 (premises tested, not proven):** a paragraph at the end of §4.3.2 or §4.4 listing the trusted parts, each with
  its check and its count (contribution functions: bit-exact; declared changes: re-extraction; the locating-position
  record: flips and crafted edits, with Cheney et al.'s dependency provenance as the reference for why the record is a
  checked approximation; the vocabulary: the tables from 100 and 2,000 files are equal; closure: 0 of 56,902). Also
  argue closure for overwrites from the record, and run a multi-byte marker probe of the record (MZ, PE, Rich/DanS,
  magic values written at every header and directory position): under 10 minutes, Claude may run it, niced.
- Not now: R18 (adversarial training and PV given all twelve operations, decision 6 revisited) could now be planned,
  since R1's attacks are read, but it needs runs; R11 and R20 are the scale-up; R4 (one instance) is the user's call.

Recommend one (Claude's view: R17 first, since it touches only §3 and Appendix D). Get approval before editing.

## Constraints and settled points

- Explain plainly, no jargon; one recommendation rather than a menu. State a hypothesis before any run; report a
  failed check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for. Settled: §2 stays as it is; widen first, then scale; "any attack"
  columns; no timing claims, and never propose Proposition 1 as a speed-up for our runs; R6's framing (session 50);
  MAB-Malware's role in §5 (session 51).
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB. Loader behaviour is argued
  from documentation.
- Blue (`\synthetic{}`) for values of runs not yet read, with a `% SYNTHETIC` comment naming the run. Remaining blue
  in §5: "a single file" (*The price*) and 89% (*Where the guarantee holds*), both line A and the scale-up.
- Jobs over ~10 minutes go to the user as `run/` scripts (`NUM_WORKERS`, default 16). Never edit a running `run/`
  script; record readings in its header afterwards.
- `pkill -f <pattern>` also kills the shell running it when the pattern occurs in that command line, and run 138's
  workers are `multiprocessing.spawn` processes too: kill by PID only.
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`; after manuscript
  edits, `make` and `make check` in `manuscript/`. Commit to `main` in logical pieces; do not push.
- At the end of the session: update `docs/status.md`, PLAN.md and the R7 record; write the next resume prompt (archive
  this one under `docs/archive/` and index it in `docs/README.md`).
