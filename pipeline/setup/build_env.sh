#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=build-env
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-02:00:00
#SBATCH --mem=16G
#
# Builds the environment for this machine's architecture from scratch with uv (Python 3.14) at the exact versions of
# requirements-lock.txt, then the package (editable) and the vendored toolkits (third_party/, without dependencies).
#   ENV_DIR  the directory to build (default env-$(uname -m): env-aarch64 on tigris, env-x86_64 on sporc); an existing
#            one is removed first. env/ itself is the dispatcher (pipeline/setup/make_dispatcher.sh) and is refused.
# On the cluster: `sbatch pipeline/setup/build_env.sh` from the repository root on tigris; on sporc override the
# header: `sbatch -M sporc --partition=tier3 --constraint=intel pipeline/setup/build_env.sh`.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
mkdir -p logs
source pipeline/systems/arch.sh
ENV_DIR="${ENV_DIR:-env-$(uname -m)}"
if [[ "${ENV_DIR%/}" == env ]]; then
  echo "ENV_DIR=env is the dispatcher, not an environment; build env-$(uname -m) instead." >&2
  exit 1
fi
SYSTEM="${SYSTEM:-}"
if [[ -z $SYSTEM ]] && command -v squeue &> /dev/null; then
  if [[ "$(arch)" == "aarch64" ]]; then SYSTEM=tigris; else SYSTEM=sporc; fi
fi
if [[ $SYSTEM == sporc ]]; then spack load gcc/lhqcen5; fi
if [[ $SYSTEM == tigris ]]; then spack load gcc/wmxcv23; fi

echo "Building $ENV_DIR/ on $(uname -m) ($(hostname)) with $(uv --version)."
rm -rf "$ENV_DIR"
uv venv -p 3.14 "$ENV_DIR"
export VIRTUAL_ENV=$PWD/$ENV_DIR
uv pip install --index-strategy unsafe-best-match -r requirements-lock.txt
uv pip install --no-deps -e .
uv pip install --no-deps -e third_party/secml -e third_party/secml_malware
"$ENV_DIR/bin/python" -c "import provexp, lightgbm, lief, pefile, signify, magic, torch; print('Imports work.')"
echo "Done. Next: pipeline/setup/make_dispatcher.sh (once per checkout), then pipeline/setup/check.sh"
