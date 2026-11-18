# Resume: the scale-up's attacks on the cluster (MAB `ours`, the lost searches, PV, then read)

Written in session 85 (2026-11-18). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading first. One
of three tracks: this one (the cluster experiments), `docs/resume-prompt-erdalt.md` (ERDALT's collapse),
`docs/resume-prompt.md` (general work and the index of the tracks).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`) is drafted on
pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`) replaces every number.

## 2. Where things stand

- **tigris** (RIT's aarch64 cluster; `SETUP.md`, `pipeline/systems/tigris.sh`). Jobs since session 82 are submitted
  by hand (`sbatch --export=ALL,...`), recorded in `logs/submit-20261117-181439-no-erdalt.txt`. Logs:
  `logs/<name>_<array id>_<task>.out` and `artifacts/scaleup/<stage>/logs/`; diagnostics in `artifacts/scaleup/diag/`.
- **Done at scale, without ERDALT:** everything through the detectors; `iterated` (`iterated-2`); `toolkit` 1046138
  (19 tasks: 8 detectors' main rows, 3 escapes, PV's 8 leave-one-out folds); `adaptive` 1046139 (81 tasks: 20 plain
  shards, 60 escape shards, the expert set); MAB-Malware `expert` (137/161 evaded) and `zainab` (unconstrained at
  0.1% FPR, no byte cap: 867 detected, 455 evaded, 52%; Zainab et al. report 83%; Appendix D's sentence still has
  the pilot's numbers).
- **Running or queued (submitted in session 85):**

  | Job | What | Request |
  |---|---|---|
  | 1131288 (task 0) | MAB-Malware `ours` against the 8 detectors (resubmission of 1046140) | 8 cores, 128 GB (estimate), 1 day |
  | 1131285 | diagnostic: adaptive shards 6 and 14 against the 2 monotone detectors, stall limit 5 h | 32 cores, 90 GB, 6 h |

  The 8 detectors: unconstrained, monotone-features, monotone-sums, additions-only, adversarial-training, pv, trial,
  iterated-2. **Held:** ERDALT's attacks and `6-results`, for the ERDALT track.
- **Session 85's fix (455f121):** 1046140 crashed in 3 min: 2 of the 1,000 evaluation malware have NumberOfSections 0
  (`8e4242ac...`, `a5647f18...`, 4 and 8 KB) and upstream MAB-Malware's section-adding action (`ArmSA.transfer`)
  indexed an empty section table. Such a file is now returned unchanged (upstream's treatment of an unreadable
  section table). Also: each MAB run now clears its work directory first; the crashed run's evasive files would
  otherwise have been read as the rerun's results. Verified by diagnostic 1131138 (the 4 anomalous files, SA pulled
  on them, two runs into one work directory identical, `tests/test_mab_attack.py` passes).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Do not watch the queue.** Check once, report, hand back; when the user returns, check again. Read a job's log a
  few minutes after it starts. Never start a `spawn` worker pool from a Python script fed on stdin; put diagnostic
  Python in a file.
- **The user is out of patience with avoidable cluster failures.** Before submitting or changing a step, work out what
  it uses on the node; read each job's startup line (`Threads per process: ...`). Say plainly what was not checked.
- Head node: at most two CPUs, nothing heavier than a minute or two; everything else through `sbatch`.
- Risky code changes go in a `git worktree` (`PYTHONPATH=<worktree>/src`), verified, then fast-forwarded: a change is
  live for every job that starts Python after it is saved.
- Explain plainly; a hypothesis before running anything; report failed checks as such; fix failures at their source.
  The user decides protocol questions. Commit to `main` in logical pieces (ruff, strict mypy); do not push.

## 4. Next session

1. **The reruns** (`logs/submit-20261118-s85.txt`; status.md, *Waiting on the user*, first item). Check once:
   `squeue -u $USER`; sacct since 2026-11-18. Read each job's startup line and its log a few minutes after it starts
   (a job's pool must sit under a main guard; session 85 lost 23 min to one that did not). New lines to read: the
   material's and the toolkit's `Validity: N of M ... not read by both parsers` and `DOS header: ...`, the tables'
   `invalid` / `invalid_pefile_only` counts (the extractor's quirks, to fix at the source), `invalid.parquet` per
   material shard. Expected: the material's invalid outputs ~2% of attempts (diag job 1141836: 42 of 2,000 before the
   shift patch), PV keeping ~1,300 features and detecting near the pilot's ~26%.
2. **When the attacks finish:** walltimes and memory against the headers; then ERDALT's track runs its attacks (its
   models were trained on the old material: retrain first) and `6-results`.
3. **Deferred, approved:** PV's sample-size experiment (`docs/scaleup-protocol.md`, item (17)).
4. **Decision 12's follow-up** (PLAN.md, open items).

## 5. Noted for later

- Per-item loops that may still run serially in a main process: `toolkit.py`, `mab.py` (scoring before the pool),
  `6-results` scripts and `expert_adaptive.py`; check them against the parallel-by-design rule before their next use.
- `mab.py` runs all detectors in one pool: one detector's crash loses every other detector's finished run (1046140
  lost PV's). Not changed.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's (shell commands checked, donor names).
- `coverage.py` still accepts an unused `--db`.
- LIEF's runaway rebuild is drafted as `docs/upstream-issues.md` §13 (check the newest LIEF before reporting).
- After the debug-entry escape, `gamma_api` no longer evaded the unconstrained smoke detector on 3 files it evades
  unescaped; look when the toolkit's escape rows are read.
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware.
- Duplicate code to merge (verify by an old-versus-new comparison): the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split).
- sporc (x86_64) is not set up; the headers target tigris.

## 6. At the end of the session

Update `docs/status.md` and PLAN.md; rewrite this prompt for the next session, self-contained, and archive this one as
`docs/archive/resume-prompt-experiments-<date>-s<N>.md`, with its line in `docs/README.md`.
