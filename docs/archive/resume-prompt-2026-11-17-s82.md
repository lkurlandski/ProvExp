# Resume: the scale-up's last jobs (ERDALT's reading, walltimes, resource review), then writing

Written in session 81 (2026-11-17). This prompt is self-contained: what the project is, where things stand, the rules
that apply, and what the next session does. Only `CLAUDE.md` (loaded automatically) needs reading first. The theory
track (bounds on size) is separate: `docs/resume-prompt-theory.md`; light tasks on Sonnet: `docs/resume-prompt-sonnet.md`.

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few totals
(readouts). From the instrumented extractor we compute what an attacker's edits do to the features: exactly for one
edit (Proposition 1), as sound directions for a whole threat model (Theorem 1), and from those, monotone detectors no
edit in the threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. The paper
(`manuscript/*.tex`, ACM CCS format) is drafted on pilot-scale results; the scale-up (PLAN.md step 3) replaces every
number. Its full record is `docs/scaleup-protocol.md`, items (a)-(g) and (1)-(15).

## 2. Where things stand

- **The scale-up runs on tigris** (RIT's aarch64 cluster; `SETUP.md`, `pipeline/systems/tigris.sh`).
  `bash pipeline/submit.sh` on the head node submits the chain with SLURM dependencies (a failure or `scancel`
  cancels what depends on it; a step already queued is reused by job name; `SKIP` must list every finished step or
  each is resubmitted as a no-op job; `DRY=1` prints the chain). Latest record: `logs/submit-20261117-124106.txt`;
  the SKIP list used there: `3-directions/derived 3-directions/gate 1-audit/population 1-audit/item-checks
  1-audit/escapes 1-audit/deviations 1-audit/catalogue-checks 1-audit/hand-table 3-directions/trial 4-detectors/train
  4-detectors/adversarial-training 4-detectors/price-list` (add `4-detectors/iterated` once it is done). After a
  resubmission, `iterated` waits on `learned` (submit.sh's dependency); release it by hand with
  `scontrol update JobId=<id> Dependency=""` while ERDALT still runs (it reads only the GBDT side).
  Logs: `logs/<name>_<id>.out` (arrays: `logs/<name>_<array id>_<task>.out`) and `artifacts/scaleup/<stage>/logs/`.
- **Done at scale:** everything through the defenses' material; `learned`'s ten GBDTs; `iterated` round 1 (968
  detected, none lost, 683 evaded, 55 min) and `iterated-1` (7 min, test AUC 0.998); MAB-Malware `expert` (137/161
  evaded, with the full 501-section donor set).
- **Running or queued when session 81 ended (14:15):**

  | Job | What | State |
  |---|---|---|
  | 1020791_0, 1020792_1-8 | the nine ERDALT models | running, done ~midnight 2026-11-17 |
  | 1039055 | `iterated` round 2, then `iterated-2` (72 cores, 300 GB) | round 2 since 14:08; ~16:00-17:00 expected |
  | 1039059_2 | MAB-Malware `zainab` (867 detected files) | running since 12:41 |
  | 1039058_0 | MAB-Malware `ours` (nine detectors, 10 cores) | waits on `learned` and `iterated` |
  | 1039056 (21), 1039057 (81) | `toolkit`, `adaptive` | wait on `learned` and `iterated` |
  | 1039060 | `6-results` (16 cores) | waits on all |

- **Session 81's changes (PLAN.md step 3 (15)):** `pipeline/common.sh` pins OpenMP, OpenBLAS and polars to one
  thread per process (SLURM had set `OMP_NUM_THREADS` = cores; 72 workers x ~380 threads exhausted the per-user
  process limit of 16,384 per node, killing `iterated`'s workers and MAB-Malware's shell) and prints, at every job's
  start, `Threads per process: ... ; cores visible ...; process limit ...`. MAB-Malware's upstream shell commands
  are checked (`checked_system`), donor section names with '/' kept as '_'. The adaptive search's per-file setup runs
  over `--num_workers` (`prepare_files` in `provexp.attacks.adaptive`), verified identical to the old code on a
  40-file search. `iterated` at 300 GB.

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **The user is out of patience with avoidable cluster failures** (sessions 77-81: OOM, idle cores, a thread
  overload, serial setup on 72 cores). Before submitting or changing a step, work out what it actually uses on the
  node: processes, threads per process, cores, memory, and which parts run serially. Read each job's startup line.
  Per-item loops go through a worker pool with the worker count as a knob. Do not assume; check, and say so plainly
  when something was not checked.
- On the cluster's head node: at most two CPUs, light memory and IO, nothing longer than a minute or two; everything
  heavier through `sbatch` (diagnostic jobs under `artifacts/scaleup/diag/`, since `/tmp` is not shared).
  (Session 81 ran a 10-minute timing script on the head node by mistake.)
- Request what a job uses for most of its life; split long phases with very different needs; after jobs finish,
  compare use with request and right-size the headers.
- A code change goes live for every job that starts a Python process after it is saved: develop risky changes in a
  `git worktree` (run with `PYTHONPATH=<worktree>/src`; the shared `env` imports the main checkout otherwise), verify,
  then fast-forward `main`. `pipeline/setup/identity_check.sh` cannot run on tigris (its baseline and the pilot's
  files are not there); compare old and new code on a small scale-up search instead (`artifacts/scaleup/diag/
  setup_pool.sh` is the template).
- Explain plainly; state a hypothesis before running anything; report a failed check as such. Prevent a failure at
  its source rather than absorbing it. Ask before changing what a statistic or claim is for; the user decides protocol
  questions, Claude recommends. Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline`); do
  not push.

## 4. Next session

1. **Check in:** `squeue -u $USER`; `sacct -u $USER -S 2026-11-17 -X --format=JobID%14,JobName%20,State%14,Elapsed,Timelimit,TotalCPU,AllocCPUS,MaxRSS,ReqMem`.
   A job marked OUT_OF_MEMORY may still have finished its work: read its own logs before deciding. Grep new logs for
   `LOST task`, `could not spawn` and `Resource temporarily unavailable`.
2. **`iterated` round 2:** confirm its setup took a minute or two (`artifacts/scaleup/4-detectors/iterated/logs/
   round-2.log`, the time from the `Scoring` line to the `detected` line; the file's mtime history helps), no task
   lost, `iterated-2` written. Its memory (230 GiB peak in round 1) against the 300 GB request.
3. **ERDALT, with the user:** each model's selected epoch, validation AUC and whether it met the criterion
   (`artifacts/scaleup/4-detectors/erdalt*/` summary; logs `4-detectors/logs/train-erdalt*.log`). If they end weak,
   the comparison invites the straw-man objection: lay out options (e.g. the cause: 25x more perturbation vectors, the
   batch size, the schedule) for the user; do not retrain without asking.
4. **When `toolkit`, `adaptive` and MAB `ours` start:** read each startup line (one thread per process, the cores
   requested) and, within the first half hour, the thread count and CPU use of one task (`srun --jobid=<id>
   --overlap -n1 ...`; `sstat`). The adaptive tasks' setup should now be minutes, not ~30 min per task.
5. **Failures as they come:** read the logs, find the cause, fix at the source, give the resubmission command.
6. **Walltimes and resource review:** as tasks finish, slowest task x1.5 (at least 30 min), confirm with the user,
   lower pending tasks (`scontrol update JobId=<id> TimeLimit=...`) and edit the headers; CPU use against allocation
   (TotalCPU / (Elapsed x AllocCPUS)) and memory against request. `iterated`'s header: 72 cores, 300 GB, 2 days
   (measured ~1 h per round + minutes of retraining: lower the walltime).
7. **Decision 12's follow-up:** identify the training files behind the derived table's new moves (a section rename
   lowering printable-string counts; header-field writes moving the relocation flags), for §4.3.2's last sentence
   and §5.1's *Checking results* (PLAN.md, open items).
8. **Writing while it runs (PLAN.md step 4):** §2's closing and contribution 4 aligned with §5 (session 80's C.6 note
   in `docs/status.md`); the remaining review fixes are on the Sonnet track (`docs/resume-prompt-sonnet.md`).
9. **When the chain finishes:** read `6-results` with the user (step 5).

## 5. Noted for later

- Other per-item loops that may still run serially in a main process: check `toolkit.py`, `mab.py` (scoring before
  the pool), `6-results` scripts and `expert_adaptive.py` against the parallel-by-design rule before their next use.
- LIEF's runaway rebuild is drafted as `docs/upstream-issues.md` §13 (check the newest LIEF before reporting).
- After the debug-entry escape, `gamma_api` no longer evaded the unconstrained smoke detector on 3 files it evades
  unescaped; worth a look when the toolkit's escape rows are read.
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact).
- Duplicate code to merge (verify by an old-versus-new comparison): the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split).
- sporc (x86_64, same file system) is not set up: its values are guesses and the headers target tigris.
- `tests/data/` on tigris holds fixtures made by `make_fixtures.py --num_shards 1` (real malware; gitignored).

## 6. At the end of the session

Update `docs/status.md` and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one
as `docs/archive/resume-prompt-<date>-s<N>.md`, with its line in `docs/README.md`.
