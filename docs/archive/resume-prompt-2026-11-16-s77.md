# Resume: the scale-up is running (failures as they come; writing meanwhile)

Written in session 74 (2026-11-16). This prompt is self-contained: what the project is, where things stand, the rules
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

- **The scale-up runs on tigris** (RIT's aarch64 cluster; set up in session 74: `SETUP.md`,
  `pipeline/systems/tigris.sh`). `bash pipeline/submit.sh` on the head node submits the whole chain with SLURM
  dependencies (a failure cancels what depends on it; a step already queued is reused, so `scancel` what must be
  rerun; `SKIP` leaves steps or job names out, e.g. `train` without `train-trial`;
  `DRY=1` prints the chain). Job IDs: `logs/submit-<date>.txt`. Logs: `logs/<name>_<id>.out` and
  `artifacts/scaleup/<stage>/logs/`.
- **Done at scale:** featurization (sums, expert), the file store, the derived tables, population, item checks
  (2,000 files, 0 failures), escapes, deviations, `train` (five detectors), `price-list`.
- **Fixed in session 74 after the first failures:** files declaring fewer than 16 data directory entries (24 of the
  2,000 evaluation files; the entry writes now return None, 2a42a34); secml's `~/secml-data` race between array
  tasks (384f0d7); `submit.sh`'s reuse of a queued array (array ID, `%F`) and `SKIP` by job name (b4bdaf4).
- **Decision 12 (PLAN.md, session 74):** the derived table from the 20,000 training files covers the evaluation set,
  but adds 98 two-sided directions the evaluation set does not show (96 `body_strings:printable_*` under a section
  rename, `has_relocs` and `has_dynamic_relocs` under the header-field overwrites). The user chose the training table
  and kept the gate unchanged. The files behind these moves are not yet identified.
- **To run (the user):** the rest of the chain, the finished steps and the gate left out (`docs/status.md`, Waiting on
  the user). Untested at scale and likeliest to fail first: `4-detectors/learned`'s split (task 0 at 36 cores; tasks
  1-8 ERDALT-only at 8 cores, submitted apart; the material merged once under `flock`).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On the cluster's head node: at most two CPUs, light memory and IO; everything heavier through `sbatch`.
- Explain plainly; state a hypothesis before running anything; report a failed check as such.
- Ask before changing what a statistic or claim is for; the user decides protocol questions, Claude recommends.
- Never edit a `run.sh` while it runs (a pending job's script is already copied by SLURM; resubmission rereads it).
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. Next session

1. **Failures first:** the user reports a failed job; read its logs, fix, and give the resubmission command (`SKIP`
   the finished steps that recompute, such as `3-directions/derived`; cancel pending jobs that would be duplicated).
2. **Walltime limits:** once the first adaptive and toolkit tasks finish, shorten their 24 h limits from the measured
   times (`scontrol update JobId=... TimeLimit=...` for pending tasks; the headers for later submissions).
3. **Decision 12's follow-up:** identify the training files behind the new moves (a section rename lowering
   printable-string counts; header-field writes moving the relocation flags), so that the rewrite of §4.3.2's last
   sentence and §5.1's *Checking results* (PLAN.md, open items) can say what they are.
4. **Writing while it runs (PLAN.md step 4):** §2's closing and contribution 4 aligned with §5; the number-free text
   fixes R4, R5, R15, R21. With the `paper-prose` skill, in small blocks with the user's review.
5. **When the chain finishes:** read `6-results` with the user (step 5).

## 5. Noted for later

- After the debug-entry escape, `gamma_api` (rebuilding through LIEF) no longer evaded the unconstrained smoke
  detector on 3 files it evades unescaped; worth a look when the toolkit's escape rows are read.
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
