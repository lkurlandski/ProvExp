#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=population
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=0-04:00:00
#SBATCH --mem=32G
#
# Which clause of the population check each file fails (incomplete, unusual layout), and whether it is in the
# population. Pilot: run 136, ~3 min on 2,000 files at 16 workers.
# Output: $OUT_ROOT/1-audit/population/ (files.parquet with `in_population`, report.json).
# Knobs: FILES (required: the audit's file list, a parquet with name, label, truncated; SCALE-UP: decided with the
# user), DB (the SimpleDB split, default the test split).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

: "${FILES:?Set FILES to the file list of the audit (parquet: name, label, truncated).}"
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
