# Resume: the scale-up's last jobs (ERDALT's reading, walltimes, resource review), then writing

Written in session 78 (2026-11-17). This prompt is self-contained: what the project is, where things stand, the rules
that apply, and what the next session does. Only `CLAUDE.md` (loaded automatically) needs reading first. The theory
track (bounds on size) is separate: `docs/resume-prompt-theory.md`.

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few totals
(readouts). From the instrumented extractor we compute what an attacker's edits do to the features: exactly for one
edit (Proposition 1), as sound directions for a whole threat model (Theorem 1), and from those, monotone detectors no
edit in the threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. The paper
(`manuscript/*.tex`, ACM CCS format) is drafted on pilot-scale results; the scale-up (PLAN.md step 3) replaces every
number.

## 2. Where things stand

- **The scale-up runs on tigris** (RIT's aarch64 cluster; `SETUP.md`, `pipeline/systems/tigris.sh`).
  `bash pipeline/submit.sh` on the head node submits the chain with SLURM dependencies (a failure cancels what depends
  on it; a step already queued is reused by job name, so `scancel` what must be rerun; `SKIP` leaves out steps or job
  names, and must list every finished step, or each is resubmitted as a no-op job; `DRY=1` prints the chain). Latest
  record: `logs/submit-20261117-095052.txt`. Logs: `logs/<name>_<id>.out` (array tasks currently share one file) and
  `artifacts/scaleup/<stage>/logs/`.
- **Done at scale:** everything through the defenses' material (repaired in session 77-78: 79,121 valid rows, 216
  where a GAMMA attack is not applicable, none lost), and `learned`'s ten GBDTs (adversarial training, PV, the PV
  leave-one-outs; ~25 min) plus MAB-Malware's `expert` setting (132 of 161 detected evaded, 8 min).
- **Running or queued when session 78 ended:**

  | Job | What | State |
  |---|---|---|
  | 1020791_0, 1020792_1-8 | the nine ERDALT models (old layout: task 0 still holds 36 cores) | running, ~30 h each, done ~midnight 2026-11-17 |
  | 1020793 | `iterated` (two rounds of the beam + retraining) | running since 2026-11-17 ~09:55 (dependency on ERDALT removed: it reads only the GBDT side) |
  | 1030369_2 | MAB-Malware `zainab` | running |
  | 1030368_0 | MAB-Malware `ours` (nine detectors, 10 cores) | waits on `learned` and `iterated` |
  | 1020794 (21), 1020795 (81) | `toolkit`, `adaptive` | wait on `learned` and `iterated` |
  | 1030370 | `6-results` (16 cores) | waits on all |

- **Session 78's changes (PLAN.md step 3 (13)-(14)):** per-attack "still detected" over the files the attack applies to
  (eec804b; the user's choice); finished steps' walltimes = measured x1.5 (36faebe); `learned` split into a GBDT CPU job
  and a 9-task ERDALT GPU array at 4 cores (23ac418; takes effect at the next submission); MAB-Malware an array of
  one task per setting, one core per detector, and `6-results` at 16 cores (9f91013; already in the queue). The
  `learned` split was tested only by a dry run of each part, not on the cluster.

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On the cluster's head node: at most two CPUs, light memory and IO; everything heavier through `sbatch` (diagnostic
  jobs of a few minutes are fine; files under `artifacts/scaleup/diag/`, since `/tmp` is not shared).
- **Resources (new, session 78):** request what a job uses for most of its life, sized to its real parallelism
  (a single-threaded process uses one core); split long phases with very different needs into separate jobs, without
  over-engineering; after jobs finish, compare use with request and right-size the headers. The user was rightly
  angry that `learned` held 36 idle cores for ~30 h: check a design's core use before submitting it.
- Explain plainly; state a hypothesis before running anything; report a failed check as such.
- Prevent a failure at its source rather than absorbing it.
- Ask before changing what a statistic or claim is for; the user decides protocol questions, Claude recommends.
- A script started with `bash` must not be edited while it runs; an `sbatch` job runs SLURM's copy (editing is safe),
  but the Python it calls is read when each command starts, so Python changes reach pending jobs.
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. Next session

1. **Check in:** `squeue -u $USER`; `sacct -u $USER -S 2026-11-17 -X --format=JobID%14,JobName%20,State%14,Elapsed,Timelimit,TotalCPU,AllocCPUS,MaxRSS,ReqMem`.
   A job marked OUT_OF_MEMORY may still have finished its work: read its own logs before deciding.
2. **ERDALT, with the user:** each model's selected epoch, validation AUC and whether it met the criterion
   (`artifacts/scaleup/4-detectors/erdalt*/` summary; logs `4-detectors/logs/train-erdalt*.log`). At epoch ~185 of
   310 all nine had AUC 0.69-0.75 (pilot 0.88) and no epoch with < 5 violations (best 16). If they end weak, the
   comparison invites the straw-man objection: lay out options (e.g. the cause: 25x more perturbation vectors, the
   batch size, the schedule) for the user; do not retrain without asking.
3. **Failures as they come:** read the logs, find the cause, fix, give the resubmission command (`SKIP` every
   finished step; cancel pending jobs that would be duplicated).
4. **Walltimes and resource review:** as tasks of `iterated`, `toolkit`, `adaptive` and MAB-Malware finish, take the
   slowest task, add ~1.5x (at least 30 min), confirm with the user, lower the pending tasks
   (`scontrol update JobId=<id> TimeLimit=...`) and edit the headers. Also compare CPU use with allocation
   (TotalCPU / (Elapsed x AllocCPUS)) and memory with request; `iterated`'s 200 GB is unmeasured.
5. **Small fixes for the next submission:** MAB-Malware skips 2 of 486 donor sections whose names contain `/`
   (COFF long-name references like `/4`; the file name built from the section name breaks): sanitize, consistently
   across settings, i.e. not mid-run. Array tasks share one SLURM `.out` (`%x_%j.out`): use `%x_%A_%a.out` in the
   array headers.
6. **Decision 12's follow-up:** identify the training files behind the derived table's new moves (a section rename
   lowering printable-string counts; header-field writes moving the relocation flags), for §4.3.2's last sentence
   and §5.1's *Checking results* (PLAN.md, open items).
7. **Writing while it runs (PLAN.md step 4):** §2's closing and contribution 4 aligned with §5; the number-free text
   fixes R4, R5, R15, R21. With the `paper-prose` skill, in small blocks with the user's review.
8. **When the chain finishes:** read `6-results` with the user (step 5).

## 5. Noted for later

- LIEF's runaway rebuild is drafted as `docs/upstream-issues.md` §13 (check the newest LIEF before reporting).
- After the debug-entry escape, `gamma_api` no longer evaded the unconstrained smoke detector on 3 files it evades
  unescaped; worth a look when the toolkit's escape rows are read.
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact).
- Duplicate code to merge under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split).
- sporc (x86_64, same file system) is not set up: its values are guesses and the headers target tigris.

## 6. At the end of the session

Update `docs/status.md` and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one
as `docs/archive/resume-prompt-<date>-s<N>.md`, with its line in `docs/README.md`.
