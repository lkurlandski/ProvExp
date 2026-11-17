# Sourced by every run.sh, from the repository root (run.sh does `cd` there first; under sbatch, submit from the root).
# Loads the system's config, activates the environment, sets the conventions every step shares:
#   SYSTEM       local, sporc or tigris (detected; override with SYSTEM=...)
#   OUT_ROOT     where the stages write (default artifacts/scaleup; the identity check overrides it)
#   NUM_WORKERS  processes per job (default: the job's SLURM_CPUS_PER_TASK, else the system's CORES; override with
#                NUM_WORKERS=...)
#   FILE_STORE   the file store the scale-up reads its files from (provexp.data.paths.file_store; default
#                $OUT_ROOT/2-features/files/files.sqlite): the loaders stop if it or a file is missing
#   PYTHONHASHSEED=0 (thrember's warning features depend on it)
#   OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, POLARS_MAX_THREADS=1: our parallelism is processes (workers do not share
#                cores); a step that trains with threads passes the count explicitly (--num_threads, or OMP_NUM_THREADS
#                on its own command line)
#   tasks N      the shards this job handles: $SLURM_ARRAY_TASK_ID in a job array, else all of 0..N-1

if [[ -z "${SYSTEM:-}" ]]; then
  if ! command -v squeue &> /dev/null; then
    SYSTEM=local
  elif [[ "$(arch)" == "aarch64" ]]; then
    SYSTEM=tigris
  else
    SYSTEM=sporc
  fi
fi
source "pipeline/systems/$SYSTEM.sh"

source env/bin/activate
export PYTHONHASHSEED=0
# NOTE: set unconditionally: SLURM on tigris starts every job with OMP_NUM_THREADS = its cores, so each of a job's N
# workers built N-thread OpenMP and OpenBLAS pools, plus polars' pools sized to the node (~380 threads per worker at
# 72 workers); the user's process limit (16,384 per node) ran out, workers died and shell commands failed to start
# (jobs 1020793 and 1030369_2, 2026-11-17).
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export POLARS_MAX_THREADS="${POLARS_MAX_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-${SLURM_CPUS_PER_TASK:-$CORES}}"
export OUT_ROOT="${OUT_ROOT:-artifacts/scaleup}"  # exported: provexp.registry reads it
export FILE_STORE="${FILE_STORE:-$OUT_ROOT/2-features/files/files.sqlite}"
mkdir -p logs

tasks() {  # number of shards
  if [[ -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    echo "$SLURM_ARRAY_TASK_ID"
  else
    seq 0 $(($1 - 1))
  fi
}

echo "System $SYSTEM, $NUM_WORKERS workers, outputs under $OUT_ROOT."
echo "Threads per process: OMP $OMP_NUM_THREADS, OpenBLAS $OPENBLAS_NUM_THREADS, polars $POLARS_MAX_THREADS;" \
  "cores visible $(env -u OMP_NUM_THREADS -u OMP_THREAD_LIMIT nproc); process limit $(ulimit -u) (per user and node)."
