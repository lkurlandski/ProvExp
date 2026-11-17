#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=deviations
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-00:45:00
#SBATCH --mem=200G
#
# The extractor audit's counts (Appendix D's deviations table): which of our deviations from EMBER v3 and which parser
# heuristics apply to each file, in the population and outside it. Needs 1-audit/population. Session 65: ~7 min on
# 2,000 files at 16 workers on a loaded machine.
# Output: $OUT_ROOT/1-audit/deviations/ (files.parquet, report.json).
# Knobs: FILES (default: the evaluation set of 2-features/files, 1,000 malware and 1,000 benign files), DB.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

FILES="${FILES:-$OUT_ROOT/2-features/files/ts.parquet}"
DB="${DB:-$EMBER2024_DATA/ts}"
OUT=$OUT_ROOT/1-audit/deviations
mkdir -p "$OUT/logs"

echo "Deviation counts on $FILES. Log: $OUT/logs/deviations.log"
python pipeline/1-audit/deviations/deviations.py \
  --files "$FILES" \
  --db "$DB" \
  --population "$OUT_ROOT/1-audit/population/files.parquet" \
  --outdir "$OUT" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/deviations.log"
echo "Done. Report: $OUT/report.json"
