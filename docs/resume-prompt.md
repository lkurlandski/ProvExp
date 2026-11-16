# Resume: check in on the scale-up (failures, walltimes, then writing)

Written in session 77 (2026-11-16). This prompt is self-contained: what the project is, where things stand, the rules
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
  names; `DRY=1` prints the chain). Job IDs: `logs/submit-<date>.txt` (latest: `logs/submit-20261116-*.txt` with
  1020777 and 1020791-1020797). Logs: `logs/<name>_<id>.out` and `artifacts/scaleup/<stage>/logs/`.
- **Done at scale:** featurization, the file store, the derived tables (decision 12: the training table), population,
  item checks, escapes, deviations, the catalogue check, the hand table, the trial table, `train` (five detectors),
  the trial detector, `price-list`, and the defenses' material (job 1018609, ten shards).
- **Queued when session 77 ended** (submitted by the user): the material's repair (array 1020777; shards 1-9 done,
  shard 0 running), then `4-detectors/learned` (1020791 task 0; 1020792 tasks 1-8, ERDALT on GPUs), `iterated`
  (1020793), `5-attacks/toolkit` (1020794, 21 tasks), `adaptive` (1020795, 81 tasks), `mab-malware` (1020796),
  `6-results` (1020797).
- **Session 77's fix (PLAN.md step 3 (13); 430ef83).** The material lost 224 GAMMA runs to OOM-killed workers: LIEF's
  rebuild runs away on some malformed files (2 GiB outputs, failed allocations, parser crashes). Now each start file
  gets one LIEF round trip in a capped child process (`provexp.attacks.lief_check`); where it fails, the two GAMMA
  attacks are *not applicable* to it (no run, counted as `not_applicable`; the other six attack it), in the toolkit
  and the material. The repair (`attack_training.py --repair`, `run.sh` `REPAIR=`) turned 192 of shards 1-9's 194
  lost tasks into not applicable and re-ran 2 (valid). Untested at scale: the check inside the toolkit's 21 tasks
  (smoke-tested on 3 files) and `4-detectors/learned`'s split (task 0 at 36 cores; tasks 1-8 at 8 cores, material
  merged under `flock`).
- **Measured times, against the headers' limits** (for shortening walltimes, so jobs queue faster):

  | Step | Measured | Limit (header) |
  |---|---|---|
  | `2-features/featurize` | 2 h 19 m | 2 days |
  | `3-directions/derived` | 54 m | 4 h |
  | `1-audit/{population,item-checks,escapes,deviations}` | 2-8 m | 4 h to 1 day |
  | `1-audit/catalogue-checks` | 1 h 09 m | 12 h |
  | `1-audit/hand-table` | 1 h 48 m | 1 day |
  | `3-directions/trial` | 11 m | 12 h |
  | `4-detectors/train` (five; trial alone) | 9 m; 5 m | 1 day |
  | `4-detectors/price-list` | 12 m | 2 days |
  | `4-detectors/adversarial-training` (per shard, 36 cores) | ~2 h 00-2 h 06 (incl. a 45-min stall now prevented) | 12 h |
  | `learned`, `iterated`, `toolkit`, `adaptive`, `mab-malware`, `6-results` | not yet | 2 days / 2 days / 1 day x3 / 8 h |

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On the cluster's head node: at most two CPUs, light memory and IO; everything heavier through `sbatch` (diagnostic
  jobs of a few minutes are fine; put their files under `artifacts/scaleup/diag/`, since `/tmp` is not shared).
- Explain plainly; state a hypothesis before running anything; report a failed check as such.
- Prevent a failure at its source rather than absorbing it (session 77: the user rejected counting the LIEF losses as
  attack failures and the 45-min stalls).
- Ask before changing what a statistic or claim is for; the user decides protocol questions, Claude recommends.
- Never edit a `run.sh` while it runs (SLURM copies a job's script at submission, so pending jobs keep the old one;
  resubmissions reread it).
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. Next session

1. **Check in:** `squeue -u $USER`, `sacct -u $USER -S 2026-11-16 -X --format=JobID%14,JobName%20,State%14,Elapsed,Timelimit,MaxRSS`.
   Confirm the repair's shard 0 finished (`artifacts/scaleup/4-detectors/material/shards/0/report.json` has
   `repair`), then that `learned` merged the material (expect ~79,100 valid rows and ~220 not applicable). A job marked
   OUT_OF_MEMORY may still have finished its work: read its own logs before deciding (session 77's lesson).
2. **Failures as they come:** read the logs, find the cause, fix, give the resubmission command (`SKIP` the finished
   steps that recompute; cancel pending jobs that would be duplicated).
3. **Walltime limits (the user wants these tighter, so jobs queue faster):** as tasks of `learned`, `iterated`,
   `toolkit`, `adaptive` and `mab-malware` finish, take the slowest measured task, add a margin (about 1.5x, at least
   30 min), lower the pending tasks' limits (`scontrol update JobId=<id>_<task> TimeLimit=...`, or the array's ID for
   all pending tasks), and edit the `#SBATCH --time` headers of the finished steps for later submissions (from the
   table above; not while a step's job is running from that script). Confirm the margins with the user first.
4. **Open for the user:** `6-results`' per-attack "still detected" (`scaleup_tables.py`, `still_detected`) divides
   by all evaluation malware, so a file a GAMMA attack is not applicable to counts as still detected in that column
   (the any-attack numbers are unaffected). Recommended: divide by the files the attack applies to, with the
   not-applicable count beside it. Must be settled before `6-results` runs, or rerun it afterwards (cheap).
5. **Decision 12's follow-up:** identify the training files behind the derived table's new moves (a section rename
   lowering printable-string counts; header-field writes moving the relocation flags), for §4.3.2's last sentence
   and §5.1's *Checking results* (PLAN.md, open items).
6. **Writing while it runs (PLAN.md step 4):** §2's closing and contribution 4 aligned with §5; the number-free text
   fixes R4, R5, R15, R21. With the `paper-prose` skill, in small blocks with the user's review.
7. **When the chain finishes:** read `6-results` with the user (step 5).

## 5. Noted for later

- LIEF's runaway rebuild is drafted as `docs/upstream-issues.md` §13 (check the newest LIEF before reporting).
- After the debug-entry escape, `gamma_api` (rebuilding through LIEF) no longer evaded the unconstrained smoke
  detector on 3 files it evades unescaped; worth a look when the toolkit's escape rows are read (the LIEF check now
  runs on the escaped file, so some of these may be not applicable).
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
