#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=check
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=0-01:00:00
#SBATCH --mem=32G
#
# Checks that a system is ready: (1) the dataset is where the system's config says, and the split index and the file
# lists were copied; (2) featurization reproduces this server's vectors bit for bit (pipeline/setup/reference/;
# required before featurizing on a new architecture); (3) the light tests (those that need the real executables of
# tests/data/ skip without them).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
source pipeline/common.sh

echo "(1/3) The dataset under $EMBER2024_DATA:"
for split in tr vl ts; do
  if [[ -d $EMBER2024_DATA/$split ]]; then echo "  $split found"; else echo "  $split MISSING"; exit 1; fi
done
echo "      What a clone does not bring (SETUP.md, section 4):"
for f in index/ember2024/us/{tr,vl,ts}.txt "$OUT_ROOT"/2-features/files/{ts,tr,tr-donors-0,tr-donors-1}.parquet; do
  if [[ -f $f ]]; then echo "  $f found"; else echo "  $f MISSING"; exit 1; fi
done
echo "(2/3) Featurization against the reference:"
python pipeline/setup/check_reference.py
echo "(3/3) Tests:"
python -m pytest -q -n "$NUM_WORKERS" tests
echo "All checks passed on $SYSTEM."
