#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=build-env
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-02:00:00
#SBATCH --mem=16G
#
# Builds env/ from scratch with uv (Python 3.14) at the exact versions of requirements-lock.txt, then the package
# (editable) and the vendored toolkits (third_party/, without dependencies). Removes an existing env/ first.
# On the cluster: `sbatch pipeline/setup/build_env.sh` from the repository root (aarch64: --partition=tigris).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
mkdir -p logs
SYSTEM="${SYSTEM:-}"
if [[ -z $SYSTEM ]] && command -v squeue &> /dev/null; then
  if [[ "$(arch)" == "aarch64" ]]; then SYSTEM=tigris; else SYSTEM=sporc; fi
fi
if [[ $SYSTEM == sporc ]]; then spack load gcc/lhqcen5; fi
if [[ $SYSTEM == tigris ]]; then spack load gcc/wmxcv23; fi

echo "Building env/ with $(uv --version)."
rm -rf env
uv venv -p 3.14 env
export VIRTUAL_ENV=$PWD/env
uv pip install --index-strategy unsafe-best-match -r requirements-lock.txt
uv pip install --no-deps -e .
uv pip install --no-deps -e third_party/secml -e third_party/secml_malware
env/bin/python -c "import provexp, lightgbm, lief, pefile, signify, magic; print('Imports work.')"
echo "Done. Next: pipeline/setup/check.sh"
