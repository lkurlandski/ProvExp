# Resume: the scale-up's attacks on the cluster (check, fix failures, right-size, then read)

Written in session 82 (2026-11-17). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading first. One
of three tracks: this one (the cluster experiments), `docs/resume-prompt-erdalt.md` (ERDALT's collapse),
`docs/resume-prompt.md` (general work and the index of the tracks).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`) is drafted on
pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items (a)-(g) and
(1)-(16)) replaces every number.

## 2. Where things stand

- **tigris** (RIT's aarch64 cluster; `SETUP.md`, `pipeline/systems/tigris.sh`). `bash pipeline/submit.sh` submits the
  whole chain; this session's jobs were submitted by hand (`sbatch --export=ALL,...`), recorded in
  `logs/submit-*-no-erdalt.txt`. Logs: `logs/<name>_<array id>_<task>.out` and `artifacts/scaleup/<stage>/logs/`.
- **Done at scale:** everything through the defenses' material; `train`, `price-list`; the learned defenses' GBDTs;
  `iterated` (round 1: 968 detected, 683 evaded; round 2 against `iterated-1`: 972 detected, 515 evaded; `iterated-2`
  written); MAB-Malware `expert` (137/161 evaded) and `zainab` (done 14:50, not yet read).
- **Submitted in session 82, without ERDALT** (none depends on another job; they were waiting for nodes, "Priority",
  when the session ended):

  | Job | What | Request |
  |---|---|---|
  | 1046138 (tasks 0-18) | `toolkit`: 8 detectors' main rows, 3 escapes, the 8 PV leave-one-out folds | 36 cores, 100 GB, 1 day each |
  | 1046139 (tasks 0-80) | `adaptive`: 20 plain-search shards (8 detectors), 60 escape shards, the expert set | 36 cores, 100 GB, 1 day each |
  | 1046140 (task 0) | MAB-Malware `ours` against the 8 detectors | 8 cores, 128 GB (an estimate: ~13 GB per detector from `zainab`'s peak), 1 day |

  The 8 detectors: unconstrained, monotone-features, monotone-sums, additions-only, adversarial-training, pv, trial,
  iterated-2.
- **Held:** ERDALT's attacks and `6-results`, for the ERDALT track (`docs/resume-prompt-erdalt.md` §5 has the commands).
- **Session 82's code changes** (PLAN.md step 3 (16)): the scale-up reads every file from the file store, whose path is
  `FILE_STORE` (set by `pipeline/common.sh`), and stops if the store or a file is missing; no fallback to the SimpleDB
  (c7481c3; `iterated` had silently read 1,000 files per round from the SimpleDB, ~20 min each). ERDALT's runs can go
  apart: `TAG` in `adaptive` and MAB-Malware, the toolkit's leave-one-out split by family (`LOO`), and
  `scaleup_tables.attack_outputs` stops if a (defense, attack, file) appears twice (aaefd75).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Do not watch the queue** (user, session 82: waiting on background work on the cluster takes too long). Check once,
  report, hand back; when the user returns, check again. Read a job's log a few minutes after it starts, not only at
  its end. Never start a `spawn` worker pool from a Python script fed on stdin (the workers cannot re-import it and the
  pool respawns them forever: session 82's diagnostic hung 25 min); put diagnostic Python in a file.
- **The user is out of patience with avoidable cluster failures.** Before submitting or changing a step, work out what
  it uses on the node (processes, threads, cores, memory, serial parts); read each job's startup line (`Threads per
  process: ...`). Per-item loops go through a worker pool. Say plainly what was not checked.
- Head node: at most two CPUs, nothing heavier than a minute or two; everything else through `sbatch` (diagnostics
  under `artifacts/scaleup/diag/`).
- A code change is live for every job that starts Python after it is saved: risky changes go in a `git worktree`
  (`PYTHONPATH=<worktree>/src`), verified (old against new on a small scale-up search), then fast-forwarded.
- Explain plainly; a hypothesis before running anything; report failed checks as such; fix failures at their source.
  The user decides protocol questions. Commit to `main` in logical pieces (ruff, strict mypy); do not push.

## 4. Next session

1. **Check in once:** `squeue -u $USER`; `sacct -u $USER -S 2026-11-17 -X --format=JobID%14,JobName%20,State%14,
   Elapsed,Timelimit,TotalCPU,AllocCPUS,MaxRSS,ReqMem`. A job marked OUT_OF_MEMORY may have finished its work: read
   its logs first. Grep new logs for `LOST task`, `could not spawn`, `Resource temporarily unavailable`, `Traceback`.
2. **The new jobs' first tasks:** the startup line (one thread per process, the requested cores); the adaptive tasks'
   setup should take a minute or two now (the files come from the store); within the first half hour, one task's
   thread count and CPU use (`sstat -j <id>.batch`; `srun --jobid=<id> --overlap -n1 ps -eLf | wc -l`). MAB `ours`:
   memory against the 128 GB estimate.
3. **Failures as they come:** read the logs, find the cause, fix at the source, give the resubmission command.
4. **Walltimes and resources:** as tasks finish, slowest task x1.5 (at least 30 min); confirm with the user, lower
   pending tasks (`scontrol update JobId=<id> TimeLimit=...`) and edit the headers. CPU use against allocation
   (TotalCPU / (Elapsed x AllocCPUS)) and memory against request. Known: `iterated` used 3 h 24 min of its 2 days and
   282 GiB of 300 GB (94%: too tight to reuse; memory grew from 230 GiB in round 1), and ~45% of its cores (each round
   ends on a long tail: the last 22 of 972 files took 32 of 88 min). Lower its walltime in the header; consider the
   memory before any rerun.
5. **MAB-Malware `zainab`:** read its result (`artifacts/scaleup/5-attacks/mab-malware/zainab/table.json`; Appendix
   D's comparison with Zainab et al.'s setting).
6. **Decision 12's follow-up:** the training files behind the derived table's new moves (a section rename lowering
   printable-string counts; header-field writes moving the relocation flags), for §4.3.2's last sentence and §5.1's
   *Checking results* (PLAN.md, open items).
7. **When the attacks finish and ERDALT's track has run its attacks:** `6-results` (`sbatch pipeline/6-results/run.sh`),
   then read the results with the user (PLAN.md step 5).

## 5. Noted for later

- Per-item loops that may still run serially in a main process: `toolkit.py`, `mab.py` (scoring before the pool),
  `6-results` scripts and `expert_adaptive.py`; check them against the parallel-by-design rule before their next use.
- `coverage.py` still accepts an unused `--db` (the queued `6-results` job's saved script passed it; that job was
  cancelled in session 82, so the flag can go).
- LIEF's runaway rebuild is drafted as `docs/upstream-issues.md` §13 (check the newest LIEF before reporting).
- After the debug-entry escape, `gamma_api` no longer evaded the unconstrained smoke detector on 3 files it evades
  unescaped; look when the toolkit's escape rows are read.
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact).
- Duplicate code to merge (verify by an old-versus-new comparison): the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split).
- sporc (x86_64) is not set up; the headers target tigris.

## 6. At the end of the session

Update `docs/status.md` and PLAN.md; rewrite this prompt for the next session, self-contained, and archive this one as
`docs/archive/resume-prompt-experiments-<date>-s<N>.md`, with its line in `docs/README.md`.
