# Resume: continue addressing the 2026-11-12 meta-review (runs 138 and 139, or a new weakness)

Written at the end of session 49 (2026-11-12). Self-contained: everything needed to start is below or in the files it
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

## Where things stand: two open lines, one run each

**Line 1, R7 (the guarantee covers only the population).** Files outside the population used to be routed to the
unconstrained detector, which the attacks evade about half the time. Run 137 (escape audit) found that one field write
the loader ignores (certificate or debug entry pointing past the end of the file, SizeOfImage raised by one alignment
step) takes 150 of 150 population files out. *Decision 11 (user):* no router; one monotone detector scores every
file; the guarantee is proven on the population and measured outside it; widen the population for one clause (option
5) only if an escape breaks the monotone detectors. Record: `docs/evidence/r7-population-escape.md`.
**Run 138** (`run/138_escape_pilot.sh`, started 16:03 on 2026-11-12, ~5-6 h): the 50 pilot malware escaped by the
certificate write (step 1) and by the SizeOfImage write (step 2), then attacked by the adaptive beam search over all
twelve operations with every candidate written and extracted (`scripts/a1_adaptive.py --score real --escape ...`),
against the unconstrained detector (`seed-0-s10-ref`, the routed system's result) and both monotone detectors
(`seed-0-s10-mfull-{feat,sums}-pre-v2`). Hypothesis (script header, R7 record §7): monotone detectors evaded on 0-3 of
about 40 escaped files each, largest score drop small; unconstrained about 40-50%. The paper is unchanged for R7.

**Line 2, R1 (attacks below published strength).** *Decision 12 (user, session 49):*
- MAB-Malware (Song et al.) joins the attacks, run against every detector, without code randomization. The authors'
  code is vendored in `third_party/mab_malware` (upstream 91a518a; small marked patches; no license stated upstream,
  keep private) and driven by `scripts/mab_attack.py`: upstream's rewriter, bandit and minimizer run in one thread,
  and each file is scored when handed over instead of passing through polled folders and threads.
  `tests/test_mab_attack.py` checks that this gives the same run (actions, outputs, bandit state) as upstream's own
  folder hand-over. The donors are the toolkit's 50 pilot goodware. Upstream's section-append action loops forever on
  an empty donor content, so empty sections are skipped. The case for MAB-Malware is strength (Zainab et al.: 83.4%
  on their EMBER-24 model) and that it renames sections (PV's hole); **not** "an attack we did not write" (the user
  rejected that: the toolkit attacks are not ours either).
- The body's detector tables report "evaded by any attack": the union per file over every attack run on that detector
  (toolkit, adaptive, MAB-Malware). Each attack appears separately in Appendix D's Table 11 (`tab:ember:per-attack`).
  This replaces the rule of 2026-11-04 (one attack per cell). "Stronger" was dropped from §5's lead.
- At the scale-up, the adaptive attack scores every candidate by extraction (`--score real`, all twelve operations).
  §2 stays as it is (user; settled, do not raise it again).

**Run 139** (`run/139_mab_malware.sh`; the user runs it with `NUM_WORKERS=4` in tmux, ~2 h): four steps by feature
store. Step `full` covers the unconstrained detector (`gbdt/seed-0`) and adversarial training. Step `pv` covers PV.
Step `sums` covers the unconstrained s10 detector, the two monotone full-model detectors, the additions detector, and
ERDALT. Step `expert` covers the expert set. All detectors run unrouted at their own 1% FPR threshold. Outputs:
`artifacts/experiments/mab_malware/{full,pv,sums,expert}/{results.parquet,table.json}`; upstream's logs and every
written file under `.../work/<detector>/`. Hypothesis (header): about 60% evaded on the unconstrained detectors; PV
evaded by renames, ~3 of 9; adversarial training ~20/50; ERDALT ~10/29; expert set ~2/8; monotone full-model
detectors 0 in the population; additions detector ~10/43, all by actions outside additions. **Smoke (recorded in the
header after the hypothesis):** on the first 10 pilot malware the undefended s10 detector detects 9, and MAB-Malware
evades 0 of them in 60 actions each (the toolkit evades 7 of the same 9, mostly GAMMA imports). Its actions move the
score (lowest p 0.91 at best, threshold 0.75) and every arm collects failures. So the unconstrained part of the
hypothesis will likely fail. Possible reasons, to weigh only after the run: hard-label feedback only, a donor pool of
248 sections from 50 goodware, our scores far above the threshold, Zainab et al.'s different EMBER-24 model.

**In the manuscript now** (all MAB-Malware values are blue `\synthetic{}` predictions with `% SYNTHETIC` comments):
- §5.1 (Setup, *Attacks*) introduces MAB-Malware and the "any attack" rule.
- 5.3 has a sentence that MAB-Malware finds PV's hole ("3 of the 9, each time with a rename") and one on adversarial
  training ("and so does MAB-Malware (20 of 50, against 30 of 49)").
- 5.4 has three: *The price* ("Our attacks evade the unconstrained detector on 38 of the 47 ..., MAB-Malware alone on
  30, and each monotone detector on a single file"), *The width of the threat model* ("... the attacks evade it on
  18"), and *Beyond the guarantee* (MAB-Malware zeroes the data a removed entry pointed to; it evades neither monotone
  detector in the population).
- Table 4 (defenses learned from the toolkit outputs) and Table 5 (detectors) each have one "Evaded" column. The
  comments under each table give the measured unions without MAB-Malware: Table 4 unconstrained 31/49, PV 4/9, ERDALT
  25/29, adversarial training 25/50.
- Table 11 has toolkit and adaptive counts measured; its MAB column is blue.

**Other user answers this session:** widen first (the review's new experiments at pilot scale), then scale
everything once (PLAN.md, next step 3). Claude's proposed speed-up (scoring by prediction) was dropped: in our Python
code prediction is slower than extraction, which says nothing about the method.

## The task: pick the line by the state of the runs

First check both runs: `artifacts/logs/escape_pilot.log` and `artifacts/experiments/escape_pilot/{cert_entry,image_size}/adaptive.json`
for 138; `artifacts/logs/mab_malware-{full,pv,sums,expert}.log` and the `table.json` files for 139. A crash shows as a
traceback in the log, or a step whose output is missing while no process runs (`ps -eo pid,etime,args | grep -E
"a1_adaptive|mab_attack"`). If both are done, do line 1, then line 2.

**A. Run 138 done (or crashed): line 1, R7.**
1. If it crashed, find why from the log, fix, smoke-test on 2-3 files, hand the user a resume command (finished
   steps are skipped only if the script supports it; check), and move to C.
2. Read it against the hypothesis: held or failed, per detector and per escape, each count beside its denominator.
   Record the reading in the run script's header and in the R7 record (§7 and the log).
3. If a monotone detector is evaded, find the side effect that did it (rebuild the written file from the `ops`
   column; compare its extraction with the original's) and weigh option 5 for that clause. Give one recommendation.
4. If they hold, plan what decision 11 changes in the paper:
   - §4.4's last paragraph: no routing.
   - §5.4's *Where the guarantee holds*: the escape result; remove "such files are rare among benign software, and so
     stand out"; the population share as n/N.
   - Any mention of routing in §5.1 and Appendix D.
   - Table 5's denominators, which are still the routed toolkit's.

   Draft in small blocks with the user (`paper-prose` skill), or record the plan if the user prefers to write after
   the scale-up. Then list what the scale-up needs for R7: the toolkit attacks on escaped files (their harness needs
   `--escape` support), the still-detected share per attack column, and the population share of attacked malware with
   its denominator.

**B. Run 139 done (or crashed): line 2, R1.**
1. If it crashed, diagnose as in A.1. A hang shows as a run directory whose `log/rewriter.log` stopped advancing
   (upstream already had one endless loop).
2. Before trusting any count, look for silent no-ops (memory `attack-strength-vs-literature`):
   - the `p_lowest` column against `p_clean`;
   - the bandit's alpha/beta lines at the end of each `rewriter.log`;
   - which actions evasive files kept (`minimal`).
3. Read it against the hypothesis, per detector, held or failed, counts beside denominators. Record the reading in
   the run 139 header and in PLAN.md (decision 12).
4. Replace the blue values with measured ones: Tables 4, 5 and 11, and the 5.3 and 5.4 sentences above. Each "any
   attack" cell is the union per file over the toolkit, the adaptive attack and MAB-Malware; the comments under each
   table name the outputs. For Table 5's bottom half, split MAB-Malware's evasions into inside and outside additions
   by the actions in `minimal`: OA/OA1 append and SA/SA1 add a section are inside; everything else is outside.
5. If MAB-Malware evades little (as the smoke suggests), the sentences that claim otherwise must be reworded, not just
   renumbered: "and so does MAB-Malware", "MAB-Malware alone on 30", and "with MAB-Malware's renames and removals".
   Before rewording, compare its rate with Zainab et al.'s honestly: their model, operating point, query budget and
   donors (`papers/zainab2026breaking.pdf`). Ask the user before changing what the MAB-Malware result is used for in
   the paper.
6. Two results would need discussion before any text changes:
   - If PV is not evaded by renames, say so plainly; 5.3's PV finding rests on the adaptive attack in any case.
   - If a monotone detector is evaded on a file in the population, stop and discuss it with the user first.

**C. Neither run done: choose a new weakness, orthogonal to R7 and R1.** Triage the register (meta-review §6) with
memory `review-comments-workflow`: plain words, the reviewers' IDs (`B-W4`, ...) and the R-numbers kept, one
recommendation per item, small passes, approved items first. Orthogonal means no edits to the §5 text that lines 1-2
will rewrite (§4.4's last paragraph, §5.4's *Where the guarantee holds*, *The price*, *The width*, *Beyond the
guarantee*, Tables 4, 5 and 11, 5.3's MAB sentences), and no runs that compete with 138 and 139 for cores. Candidates,
best fit first:
- **R6 (unanimous, writing only, §3 and §6):** one paragraph in §3, echoed in §6, saying what is classical and what is
  new.
  - Classical: Proposition 1 is IVM's delta rule; keeping the multiset for maxima and minima is self-maintainability
    (Mumick et al. 1997); Theorem 1 is a sign-domain abstract interpretation (Cousot and Cousot, in `main.bib` but
    never cited); Corollary 1 is Gimenez et al.'s.
  - New: real extractors fit the class bit for bit; a raw write's effect is computed from item tables and the
    positions the parser uses to find items; soundness holds over a population closed under the threat model, with
    closure and coverage checkable; the derived table is the missing input of the monotone-detector line.
  - Also fix §6's incremental-parsing contrast (`_g_related_work.tex`, around lines 96-101): one of its two claimed
    differences does not hold.
- **The cheap writing batch (meta-review §8, minus the parts in lines 1-2):**
  - Theorem 1's hypothesis on the monoids; the ratio's side condition in Definition 10; one locality sentence after
    Definition 8 (A-W1, A-W3).
  - A paragraph in §6 on certified malware defenses (RS-Del, DRSM, Gibert et al., Giri et al.).
  - The five bib entries cited nowhere (`cousot1977abstract`, `cortellazzi2025intriguing`, `zainab2026breaking` is
    now cited, `kantchelian2016evasion`, `lucas2024training`; recheck which remain).
  - "100 queries per file, as in Gimenez et al." attributed to their released code (their paper says 60 s per attack).
  - Appendix D's minima: they are 0 on every file, not only on files without sections.
  - §4.3.1: name the attacker and word the code-level exclusion accurately against Lucas et al. 2021.
- **R2 (premises tested, not proven):** a paragraph at the end of §4.3.2 or §4.4 listing the trusted parts, each with
  its check and its count:
  - contribution functions: bit-exact;
  - declared changes: re-extraction;
  - the locating-position record: flips and crafted edits;
  - the vocabulary: the tables from 100 and 2,000 files are equal;
  - closure: 0 of 56,902.

  Also argue closure for overwrites from the record, and run a multi-byte marker probe of the record (MZ, PE,
  Rich/DanS, magic values written at every header and directory position): under 10 minutes, Claude may run it.
  Orthogonal enough if run niced while 138 and 139 run.
- Not now: R18 (adversarial training and PV given all twelve operations, decision 6 revisited) depends on line 2's
  attacks; R11 and R20 are the scale-up.

Recommend one (Claude's view: R6 together with the cheap writing batch, since all four reviewers raised R6 and it
touches only §3, §6 and Appendix D). Get approval before editing.

## Constraints and settled points

- Explain plainly, no jargon; one recommendation rather than a menu. State a hypothesis before any run; report a
  failed check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for. Settled in session 49: §2 stays as it is; widen first; "any
  attack" columns; no timing claims, and never propose Proposition 1 as a speed-up for our runs.
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
