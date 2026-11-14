# Resume: the refactoring session before the scale-up

Written at the end of session 63 (2026-11-14). Self-contained: everything needed is below or in the files it names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. All pre-scale-up research is done
(R7, R18, the review revisit); the next big step is the scale-up (PLAN.md step 3), on the user's SLURM clusters.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` step 3 (especially (d) and (e), the decisions of session 63).

## Why this session

The code grew by session: 84 scripts in `scripts/` named after old internal IDs (`a1_`, `ap_`, `cm_`, ...), 136
numbered steps in `run/`, model directories like `models/gbdt/seed-0-a-mfull-pre-qf-v2`, and scripts that import
library code from each other (e.g., `a1_adaptive.py` imports the edit writers from `catalogue_checks.py`, the escapes
from `escape_audit.py`, `load_pilot` from `a_pv_attacks.py`). That was fine for prototyping; the user wants the
scale-up to be human-readable and portable. This session is hands-on refactoring, not experiment design.

## What was agreed (user, session 63; PLAN.md step 3 (e))

1. **`pipeline/`**, one numbered stage per folder: `setup/`, `1-audit/`, `2-features/`, `3-directions/`,
   `4-detectors/`, `5-attacks/`, `6-results/`, plus `systems/` (one config per machine: paths, SLURM account and
   partition, modules) and a `README.md` mapping each paper table or number to its stage and output file. Each stage
   has a short README (what it computes, inputs, outputs, where it lands in the paper, runtime).
2. **One `run.sh` per step, with the `#SBATCH` header at the top** (the user's existing workflow): `sbatch` on the
   cluster, `bash` locally (the header is then comments). No separate submit scripts. File-parallel steps are SLURM job
   arrays: each task takes a shard (`SLURM_ARRAY_TASK_ID`, with a local fallback that runs all shards), runs the worker
   pool on its node (`NUM_WORKERS` as in CLAUDE.md), and a merge step combines the shards. Keep CLAUDE.md's `run/`
   conventions (echo each step and its log; one argument per line).
3. **Plain names in one registry**: detectors `unconstrained`, `monotone-features`, `monotone-sums`, `additions-only`,
   `adversarial-training` (and the iterated variant), `pv`, `erdalt`, `expert-set`, `trial`; the attacks likewise
   (toolkit attacks, `adaptive`, `mab-malware`, the escapes). Outputs under `artifacts/scaleup/<stage>/`.
4. **Library code moves into `src/provexp/`** (e.g., `attacks/`, `featuresets/ember2024/edits.py`), so no script imports
   another. Remove old and dead code (the old direction's `explain/`, `boxmatrix.py`, `provenance.py`, `ablation.py`,
   the `cm_*`, `cp_*`, `pb1_*`, `trigger_*`, `pf*`, `audit_*`, `ap_*` scripts not used by the paper; `scripts/README.md`
   lists what the paper uses) — git history keeps them. Decide per item whether the pilot's `run/` scripts must stay
   runnable (thin wrappers) or become a historical record only; ask the user if unsure. Update and expand the tests.
5. **`SETUP.md`** from a fresh clone: uv, Python 3.14, `requirements-lock.txt`, the vendored `third_party/` code, the
   oscrypto pin, libmagic, `EMBER2024_DATA`, the artifacts location, the per-system config. `pipeline/setup/build_env.sh`
   (a SLURM job where needed) and `pipeline/setup/check.sh` (data found; a few pilot files re-featurized and compared bit
   for bit with stored vectors; the light tests).
6. **The check that the move is correct:** the reorganized code gives byte-identical outputs to the current code on a
   small pilot slice (the derived direction tables, `--loose` and not; one catalogue check; one extraction-scored
   adaptive search; one MAB-Malware run; a featurization of a few files). Run the old code first and keep its outputs.
   A difference is a bug in the move, reported as such.

## The clusters (from `~/Documents/code/SSViT/scripts/create.py`, `scripts/build-env.sh`)

- SLURM, account `admalware`, partitions `sporc` (x86_64) and `tigris` (aarch64); `spack load gcc/lhqcen5` (sporc) or
  `gcc/wmxcv23` (tigris); `source ./env/bin/activate`; logs `./logs/%x_%j.out`; datasets under
  `/shared/rc/admalware/datasets/EMBER-2024`. SSViT's code assumes 36 CPUs per node. SSViT detects the system with
  `squeue` and `arch`.
- **Run on sporc.** tigris only after `check.sh` shows bit-identical featurization there (floating-point results may
  differ across architectures, and our features must match EMBER's released vectors).
- To confirm in a later session on the head node: cores per node, where large outputs live, maximum walltime, Python
  3.14 through uv. Write the configs as best guesses, marked for that session.

## How to work

- Plan the refactor in small, reviewable commits (CLAUDE.md: commit to `main` in logical pieces; ruff and mypy strict
  must pass; light tests per module, full suite `env/bin/pytest -n 16 tests` when nothing of the user's runs).
- Propose the target tree and the list of deletions to the user before moving files; then move, then check.
- Do not change any computation. Behaviour changes (e.g., the adaptive attack's watchdog for 5,000 candidates, the
  2,000 checkpoint) are noted for the scale-up session, not mixed into the move.
- Leave the R18 session's files alone unless the user says that track is closed (it closed in session 63; its
  uncommitted changes to `PLAN.md`, `docs/status.md`, `run/144_trial_competitor.sh`, `scripts/a1_adaptive.py`
  (`--save_rows`), `scripts/trial_audit.py` and `docs/evidence/r18-trial-competitor.md` should be committed by the user or
  that session first; check `git status` before starting).

## After this session

Then, in order: the extractor audit pass (`1-audit`, with the deviations table for Appendix D); the remaining protocol
items, one at a time with the user (the malware count first: with one seed, ~1,000 detected attacked malware looks
affordable, ~10,000 CPU-hours including the escapes); a session on the cluster's head node to test and patch.

At the end of the session: update `docs/status.md` and PLAN.md; write the next resume prompt (archive this one).
