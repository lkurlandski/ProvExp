# Sourced by every run.sh, from the repository root (run.sh does `cd` there first; under sbatch, submit from the root).
# Loads the system's config, activates the environment, sets the conventions every step shares:
#   SYSTEM       local, sporc or tigris (detected; override with SYSTEM=...)
#   OUT_ROOT     where the stages write (default artifacts/scaleup; the identity check overrides it)
#   NUM_WORKERS  processes per node (default: the system's CORES, 16 locally; override with NUM_WORKERS=...)
#   PYTHONHASHSEED=0 (thrember's warning features depend on it), OMP_NUM_THREADS=1 (workers do not share cores)
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
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-$CORES}"
OUT_ROOT="${OUT_ROOT:-artifacts/scaleup}"
mkdir -p logs

tasks() {  # number of shards
  if [[ -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    echo "$SLURM_ARRAY_TASK_ID"
  else
    seq 0 $(($1 - 1))
  fi
}

echo "System $SYSTEM, $NUM_WORKERS workers, outputs under $OUT_ROOT."
