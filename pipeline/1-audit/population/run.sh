#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=population
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-04:00:00
#SBATCH --mem=200G
#
# Which clause of the population check each file fails (incomplete, unusual layout), and whether it is in the
# population. Pilot: run 136, ~3 min on 2,000 files at 16 workers.
# Output: $OUT_ROOT/1-audit/population/ (files.parquet with `in_population`, report.json).
# Knobs: FILES (the audit's file list, a parquet with name, label, truncated; default: the evaluation set of
# 2-features/files, 1,000 malware and 1,000 benign files), DB (the SimpleDB split, default the test split).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

FILES="${FILES:-$OUT_ROOT/2-features/files/ts.parquet}"
DB="${DB:-$EMBER2024_DATA/ts}"
OUT=$OUT_ROOT/1-audit/population
mkdir -p "$OUT/logs"

echo "Population clauses on $FILES. Log: $OUT/logs/population.log"
python pipeline/1-audit/population/population_clauses.py \
  --files "$FILES" \
  --db "$DB" \
  --outdir "$OUT" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/population.log"
echo "Done. Report: $OUT/report.json"
