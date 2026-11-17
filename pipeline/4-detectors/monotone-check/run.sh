#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=monotone-check
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=0-00:30:00
#SBATCH --mem=8G
#
# §5.1's check that the trained monotone detectors respect their constraints (the robustness corollary needs it): from the trees
# alone, the leaf pairs that break a constraint, per monotone model of the registry's set (prediction: none).
# Inputs: 4-detectors/<name>/{model.txt,metrics.json} and the constraint files they name. Read-only.
# Output: $OUT_ROOT/6-results/monotone-check/violations.json.
# Knobs: MODEL_SET (default scaleup). Cost: one core, minutes. SCALE-UP TO CONFIRM: time.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

OUT=$OUT_ROOT/6-results/monotone-check
mkdir -p "$OUT"

echo "Counting violations per monotone model. Output: $OUT/violations.json. Log: $OUT/check.log"
python pipeline/4-detectors/monotone-check/check_monotone.py \
  --set "${MODEL_SET:-scaleup}" \
  --out "$OUT/violations.json" \
  2>&1 | tee "$OUT/check.log"
