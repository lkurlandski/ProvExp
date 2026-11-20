#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=catalogue-checks
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-02:00:00
#SBATCH --mem=80G
#
# The catalogue check on the widened population: every operation applied by our own byte-level edits, with ordinary
# and adversarial parameters, re-extracted and compared with the derived directions (sound), the population (closed)
# and the declared changes (exact). Needs the loose direction table of 3-directions/derived.
# Output: $OUT_ROOT/1-audit/catalogue/ (edits.parquet, report.json: the verdicts `pass`, `closed`).
# A second pass (CHAINED=1, the default) runs the chained edits: three added sections then an append, the item table
# carried forward one edit at a time (Appendix D's combined edits). Output: $OUT_ROOT/1-audit/catalogue/chains.json.
# Knobs: FILES (default: the evaluation set of 2-features/files), NUM_FILES (first N files; 0, the default: all),
# DIRECTIONS, CHAINED (0 skips the chains).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DIRECTIONS="${DIRECTIONS:-$OUT_ROOT/3-directions/loose/directions_sums.csv}"
OUT=$OUT_ROOT/1-audit/catalogue
mkdir -p "$OUT/logs"
FILES="${FILES:-$OUT_ROOT/2-features/files/ts.parquet}"

echo "Catalogue check, loose, against $DIRECTIONS. Log: $OUT/logs/catalogue.log"
python pipeline/1-audit/catalogue-checks/catalogue_checks.py \
  --loose \
  --directions "$DIRECTIONS" \
  --files "$FILES" \
  --num_files "${NUM_FILES:-0}" \
  --outdir "$OUT" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/catalogue.log"
echo "Done. Report: $OUT/report.json"

if [[ "${CHAINED:-1}" == "1" ]]; then
  echo "Chained edits, loose. Log: $OUT/logs/chains.log"
  python pipeline/1-audit/catalogue-checks/catalogue_checks.py \
    --chained \
    --loose \
    --directions "$DIRECTIONS" \
    --files "$FILES" \
    --num_files "${NUM_FILES:-0}" \
    --outdir "$OUT" \
    --workers "$NUM_WORKERS" \
    &> "$OUT/logs/chains.log"
  echo "Done. Report: $OUT/chains.json"
fi
