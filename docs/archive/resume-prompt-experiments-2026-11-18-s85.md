# Resume: the scale-up's reruns on the cluster (check them, read them, then ERDALT and the results)

Written at the end of session 85 (2026-11-18). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading
first. One of three tracks: this one (the cluster experiments), `docs/resume-prompt-erdalt.md` (ERDALT's collapse and
retraining), `docs/resume-prompt.md` (general work and the index of the tracks).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`) is drafted on
pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items (1)-(17)) replaces
every number. The detectors attacked: unconstrained, monotone-features, monotone-sums, additions-only (built from our
derived table or plain), adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial edits),
and ERDALT (its own track). The attacks: Gimenez et al.'s eight secml-malware attacks (the "toolkit"), our adaptive
search, and MAB-Malware.

## 2. What session 85 changed (all committed; details in `docs/scaleup-protocol.md` item (17))

- **One validity rule for the whole paper** (b87fec6, `src/provexp/attacks/validity.py`; the user's decision). An
  attack's output counts (as an evasion, as a defense's training example, as evidence that a feature can be lowered)
  only if pefile and LIEF both read it and neither loses a section, an imported DLL or an imported function the
  original had. A start file a parser does not read is *not applicable* to every attack (`unreadable.parquet` beside
  each attack's results; 6-results leaves such files out of the counts, also after any attack). Each rejection names
  the parser: "pefile only" ones are our extractor's quirks (e.g. pefile's 8,192-import cap), to be fixed at the
  source, never silently kept (the user: a misread file must not propagate downstream). Applied in the toolkit, the
  adaptive search (its end file; `valid` column), MAB-Malware, the defenses' material (`attack_training.py`: only
  valid outputs kept, rejections in `invalid.parquet` per shard), `iterated`'s rows, the catalogue and trial edits
  (`valid` column; the trial table and coverage filter on it). The soundness check still counts every edit.
- **Why:** PV at scale kept 201 features (pilot ~1,490) and detected 5 of 1,000 malware. 894 of the material's 79,121
  outputs (1.1%) were broken and each "lowered" hundreds of features; PV drops any feature one output lowers.
  Causes: secml-malware's content shift inserts its padding at the first section's offset, 0 on files whose first
  section has no raw data (`.textbss` in debug builds): **patched** (5170936; inserts where section content starts;
  byte-identical to upstream wherever upstream worked, checked end to end); the DOS extension breaks files whose PE
  header starts inside the DOS header (e_lfanew < 0x40): **not applicable** now (`dos_check.parquet`); the rest are
  outputs that lost their import table. `docs/upstream-issues.md` §14-15.
- **A run is discarded after an hour without progress** (`map_watchdog`, ec2a5bd): no result an hour after the last
  other run finished; its file leaves the count and the denominator unless another counted output evades it, and is
  reported (`lost.parquet`, `discarded` in 6-results). The user accepts discards while they stay under ~10 in 1,000;
  anything more (e.g. a 2-4% attack failure) must be investigated and fixed, not ignored. Session 85's three lost
  searches were slow (79, 61, 60 min, none evaded), not dying.
- **MAB-Malware** no longer crashes on files with no sections, and each run clears its work directory (455f121).
- **Resources:** every step's header right-sized from `sacct` (ec2a5bd, 74da6eb, 1e00b5d), including finished steps
  (the user: do it while the measurements are fresh; reruns at a larger scale are likely). `hand-table` now reads the
  file store over worker pools (108 min at 2% CPU -> 8 min, reports identical; dea644c); `trial_probe` and
  `catalogue_checks` read the file store too.
- **PV's sample-size experiment** is designed, approved and deferred (protocol item (17)): kept features and TPR
  against the training malware observed, a predictive model E[K(n)] = sum_j (1 - p_j)^n, for an appendix.
- Settings: `/shared/rc/admalware/provexp` (the `artifacts` symlink's target) is always readable and writable
  (`.claude/settings.local.json`).

## 3. What is running (`logs/submit-20261118-s85.txt`)

Old outputs moved to `artifacts/scaleup/superseded-s85/` (README inside). Chain, with SLURM dependencies:

| Job | Step | After | Expect |
|---|---|---|---|
| 1141844 | 1-audit/catalogue-checks (72 cores) | - | ~70 min |
| 1141845 | 3-directions/trial (probe and table) | 1141844 | ~15 min |
| 1141846 | 4-detectors/train, `DETECTORS=trial` | 1141845 | ~5 min |
| 1141847 (0-9) | 4-detectors/adversarial-training: the material, 10 shards x 1,000 training malware | - | ~2 h |
| 1141848 | 4-detectors/learned `PART=gbdt` (merge; adversarial-training, pv, 8 pv-loo folds) | 1141847 | ~1 h |
| 1141849 | 4-detectors/iterated (48 cores now) | 1141848 | ~5 h |
| 1141850 (0-18) | 5-attacks/toolkit, 8 detectors, `PARTS="main escape loo" LOO=pv` | 1141846, 1141849 | up to ~5 h |
| 1141851 (0-80) | 5-attacks/adaptive, 8 detectors (16 cores a task now) | 1141846, 1141849 | ~1.5 h a task |
| 1141852 (0) | MAB-Malware `ours`, 8 detectors, 8 cores, 128 GB | 1141846, 1141849 | ~5-8 h |
| 1141853 (1-2) | MAB-Malware `expert`, `zainab` | - | ~2 h |

Startup lines read in session 85: all showed one thread per process and the requested cores. Material shard 0 at
start: 13 files LIEF cannot rebuild, 5 with e_lfanew < 0x40, 4 not read by both parsers. **Held:** ERDALT (its nine
models were trained on the old material; the ERDALT track retrains them on the new one) and `6-results`.

## 4. Next session

1. **Check in once** (do not watch the queue): `squeue -u $USER`; `sacct -u $USER -S 2026-11-18 -X
   --format=JobID%16,JobName%20,State%14,Elapsed,Timelimit,AllocCPUS,ReqMem` (MaxRSS and TotalCPU on the `.batch`
   steps: drop `-X`). Grep new logs for `LOST task`, `could not spawn`, `Resource temporarily unavailable`,
   `Traceback`, `bootstrapping phase`. A job marked OUT_OF_MEMORY may have finished its work: read its logs first.
2. **Read the new counts:** per material shard `Validity:` / `DOS header:` lines, `report.json` (`invalid`,
   `invalid_pefile_only` per attack) and `invalid.parquet`; the toolkit's `table.json` (`invalid`,
   `invalid_pefile_only`, `not_applicable`) and `unreadable.parquet`; the adaptive search's `adaptive.json`
   (`invalid`, `not_applicable`, `lost`). Expected: ~2% of material outputs rejected before the patch (diag job
   1141836: 42 of 2,000), fewer now; "pefile only" ~0.2%; PV keeping ~1,300 features (`4-detectors/pv-selection/
   report.json`) and detecting near the pilot's ~26% (`4-detectors/pv/metrics.json`). Report a failed expectation as
   such. List the "pefile only" rejections by cause for the user (the extractor quirks to patch).
3. **Failures as they come:** read the logs, find the cause, fix it at the source, verify on a small case, give the
   resubmission command; above ~10 in 1,000 a failure needs a fix, not a discard.
4. **When the jobs finish:** walltimes, CPU use and memory against each header (`sacct`), and adjust the headers then
   (the user's standing instruction). Then read the results with the user (toolkit, adaptive, MAB per detector;
   PV against the pilot; MAB `zainab` against Zainab et al.'s 83%; the superseded run's 52% is in
   `superseded-s85/5-attacks/mab-malware/zainab/`).
5. **Then:** the ERDALT track retrains ERDALT on the new material and runs its attacks
   (`docs/resume-prompt-erdalt.md`; session 90: the literal port collapsed because their setup was far smaller than
   ours; session 91: the diagnosis points to the input scale, and a second round, tasks 7-10, decides the retrain), then `6-results` (`sbatch pipeline/6-results/run.sh`).
6. **PV's setup against Gimenez et al.'s (asked by the user, session 90; CLAUDE.md: "ported for its effect, not its
   letter").** ERDALT's collapse came from porting it literally to a setup ~75x larger than theirs; PV comes from the
   same paper, so check it the same way before its results are read as final. Their setup (paper §5,
   `papers/gimenez2025certifiably.pdf`; code github.com/PFGimenez/certifiably-robust-malware-detectors-by-design,
   `feature_selection.py`, read at 0b6f222): 24,000 training files, **1,033 adversarial examples in all** (shared by
   every method), PV keeps the features no vector lowers, then a random forest (0.952 AUC), monotone GBT (0.867) or
   GBT (0.938). Ours: 1.76M files, 78,715 vectors, a monotone GBDT with our own hyperparameters. Tabulate the
   differences (vector count, which outputs count as vectors, the model and its hyperparameters, any thresholds in
   their selection code) and decide with the user whether to adjust anything, e.g. whether "lowered by any of 78,715
   vectors" is the same rule as "by any of 1,033" in effect (more vectors can only drop more features; PV's
   sample-size experiment, protocol item (17), measures exactly this and should be read in this light). Recommend; the
   user decides.
7. **Later, approved:** PV's sample-size experiment (protocol item (17)); decision 12's follow-up (PLAN.md, open
   items: the training files behind the derived table's new moves).

## 5. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Do not watch the queue.** Check once, report, hand back. **Read every job's log within ~2 minutes of its start**
  (session 85 lost 23 min to a diagnostic that spun unnoticed). Put diagnostic Python in a file, and every worker pool
  under `if __name__ == "__main__":` (a `spawn` pool started from stdin or at module level respawns forever).
- **The user is out of patience with avoidable cluster failures.** Before submitting or changing a step, work out what
  it uses on the node; read each job's startup line (`Threads per process: ...`). Say plainly what was not checked.
- Head node: at most two CPUs, nothing heavier than a minute or two; everything else through `sbatch`
  (diagnostics under `artifacts/scaleup/diag/`).
- A code change is live for every job that starts Python after it is saved: risky changes go in a `git worktree`
  (`PYTHONPATH=<worktree>/src`), verified, then fast-forwarded; do not edit code a queued job will import without
  thinking through which jobs pick it up.
- A method from another paper is ported for its effect, not its letter: tabulate their setup against ours and
  rescale what the differences touch, before the first run and before diagnosing a weak result (session 90).
- Explain plainly; a hypothesis before running anything; report failed checks as such; fix failures at their source.
  The user decides protocol questions; Claude recommends. Commit to `main` in logical pieces (ruff, strict mypy); do
  not push.

## 6. Noted for later

- Toolkit task 9 (the debug-entry escape) used 41% of its 36 cores with every attack 2-3x slower; cause not found
  (it shared a 144-core node with two other toolkit tasks). If it recurs, `sstat` it while it runs.
- The toolkit's leave-one-out folds used ~5% of 36 cores when PV detected 5-23 files; with PV fixed they should carry
  real work; if not, submit them apart with fewer cores.
- Per-item loops that may still run serially in a main process: `toolkit.py` and `mab.py` (feature extraction before
  the pool), `6-results` scripts, `expert_adaptive.py`.
- `mab.py` runs all detectors in one pool: one detector's crash loses every other detector's finished run.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's (shell commands checked, donor names).
- `coverage.py` still accepts an unused `--db`. Other audit steps (population, item checks, escapes, deviations) may
  still read the SimpleDB; move them to the file store before their next run.
- LIEF's runaway rebuild (`docs/upstream-issues.md` §13) and secml-malware's shift and DOS-extension bugs (§14-15) are
  not reported upstream yet.
- After the debug-entry escape, `gamma_api` no longer evaded the unconstrained smoke detector on 3 files it evades
  unescaped; look when the toolkit's escape rows are read.
- Duplicate code to merge (verify by an old-versus-new comparison): the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split).
- sporc (x86_64) is not set up; the headers target tigris.

## 7. At the end of the session

Update `docs/status.md` and PLAN.md; rewrite this prompt for the next session, self-contained, and archive this one as
`docs/archive/resume-prompt-experiments-<date>-s<N>.md`, with its line in `docs/README.md`.
