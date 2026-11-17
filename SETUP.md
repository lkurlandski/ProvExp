# Setup

From a fresh clone to a system that can run `pipeline/`. The same steps on this server and on the SLURM clusters
(sporc, x86_64; tigris, aarch64): on a cluster, submit the scripts with `sbatch` from the repository root; elsewhere,
run them with `bash` (the `#SBATCH` lines are then comments).

## 1. Prerequisites

- **uv** (0.9 or later) on the `PATH`. uv fetches Python 3.14 itself.
- **libmagic** (the C library behind `python-magic`; Debian: `libmagic1`). On the clusters: check that
  `python -c "import magic"` works after step 2; otherwise load it through spack (to confirm on the head node).
- **The dataset**: EMBER2024's binaries as one SimpleDB per split (`tr`, `vl`, `ts`), each file truncated to its first
  4,000,000 bytes, plus the split index files in `index/ember2024/us/{tr,vl,ts}.txt` (from SSViT; gitignored).

## 2. The environment

    bash pipeline/setup/build_env.sh          # or: sbatch pipeline/setup/build_env.sh

This builds `env/` (uv, Python 3.14) at the exact versions of `requirements-lock.txt`, installs the package editable,
and the vendored toolkits in `third_party/` without their dependencies:

- `secml/` and `secml_malware/` (the toolkit attacks), patched for Python 3.14, NumPy 2 and LIEF 1.0;
- `mab_malware/` (MAB-Malware) is not installed: `provexp.attacks.mab` imports it from its directory. Its upstream
  repository states no license: keep the copy private.

Two pins matter: `pefile==2024.8.26` and `signify==0.7.1` (thrember's versions), and `oscrypto` from git (the 1.3.0
release cannot parse the version string of OpenSSL 3.x.10 and later; signify needs it). Never use a conda Python.

## 3. The system's configuration

`pipeline/systems/<system>.sh` holds what differs per machine: the dataset location (`EMBER2024_DATA`), the cores
(the default `NUM_WORKERS` outside a SLURM job; inside one, `NUM_WORKERS` follows the job's `SLURM_CPUS_PER_TASK`),
the modules to load. `pipeline/common.sh` picks the file: `local` without SLURM, `tigris` on aarch64, `sporc`
otherwise (`SYSTEM=...` overrides). For a new machine, copy `local.sh` and edit it.

The `run.sh` headers target tigris (confirmed in session 74, `pipeline/systems/tigris.sh`): CPU steps on the `gg`
nodes (`--constraint=gg`; half a node, 72 cores, or a quarter per array task, where a pool keeps them busy; fewer for
single-threaded runs), the one GPU step (`learned`'s ERDALT array) on the `gh` nodes (one GH200 and 4 cores per task). On the head node itself run nothing heavier than two cores: submit everything. sporc's
values are still guesses ("TO CONFIRM" in `sporc.sh`); it shares the file system and is set up when it is used.

## 4. Outputs and artifacts

`artifacts/` is a symlink to large storage (on this server `/scratch/lk3591/provexp`); create it on a new system
before running anything (`ln -s <large storage> artifacts`). The pipeline writes under `artifacts/scaleup/<stage>/`;
SLURM's own logs go to `logs/`. To use the pilot's models and feature stores elsewhere (the registry's `pilot` set),
copy them with `run/sync_artifacts.sh`.

**What a clone does not bring** (gitignored; copy from this server, `gcis-mkwics-rl`, into the same paths):

    rsync -a lk3591@gcis-mkwics-rl.rit.edu:Documents/code/ProvExp/index/ember2024/us/ index/ember2024/us/
    rsync -a lk3591@gcis-mkwics-rl.rit.edu:/scratch/lk3591/provexp/scaleup/2-features/files/ artifacts/scaleup/2-features/files/

- `index/ember2024/us/{tr,vl,ts}.txt`: the split index files featurization reads;
- `artifacts/scaleup/2-features/files/`: the scale-up's file lists (`ts.parquet`, `tr.parquet`, the two donor sets),
  drawn once in session 67; every step reads them. Do not re-draw them on the cluster;
- optional: `artifacts/metadata/` (~560 MB; only `2-features/files` reads it, to draw lists) and `tests/data/` (real
  malware for the tests; without it they skip).

The commits must be on the remote first: `git push` on this server before cloning (the clone is otherwise the
pilot's code). `pipeline/setup/check.sh` stops if the index files or the lists are missing.

The scale-up's attacks and defenses read their files only from the file store, `FILE_STORE` (set by
`pipeline/common.sh` to `$OUT_ROOT/2-features/files/files.sqlite`; `pipeline/2-features/file-store`; the same bytes as
the SimpleDB, each row's SHA-256 checked on read). They stop with an error if it is missing or lacks a file: build it
after the lists, or copy it from this server.

## 5. The check

    bash pipeline/setup/check.sh              # or: sbatch pipeline/setup/check.sh

It checks that the dataset is found, that featurization reproduces this server's vectors bit for bit on 32 test files
(`pipeline/setup/reference/`), and runs the tests. **On tigris, featurize nothing before this check passes there**:
floating-point results may differ across architectures, and the features must match EMBER's released vectors.

The tests that need real executables use `tests/data/` (gitignored: real malware), filled by
`python pipeline/setup/make_fixtures.py`; without it they are skipped.

## 6. Running a step

Each step of `pipeline/` is a folder with a `run.sh`. From the repository root:

    sbatch pipeline/5-attacks/adaptive/run.sh                 # on a cluster
    NUM_WORKERS=32 bash pipeline/5-attacks/adaptive/run.sh     # locally

`pipeline/README.md` lists the steps, what each feeds in the paper, and their knobs.
