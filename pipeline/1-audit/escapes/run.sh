#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=escapes
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-00:45:00
#SBATCH --mem=200G
#
# The escape audit: single writes of loader-ignored header fields (outside the threat model) on files of the
# population, and the population clauses they trip. Needs 1-audit/population. Pilot: run 137, ~1 min on 150 files.
# Output: $OUT_ROOT/1-audit/escapes/ (files.parquet, report.json).
# Knobs: N (files sampled from the population; 0, the default: all of it, i.e. every population file of the evaluation
# set, ~10 min at 16 workers), SEED, DB.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DB="${DB:-$EMBER2024_DATA/ts}"
CLAUSES="$OUT_ROOT/1-audit/population/files.parquet"
OUT=$OUT_ROOT/1-audit/escapes
mkdir -p "$OUT/logs"

echo "Escape audit on ${N:-0} (0: all) files of the population ($CLAUSES). Log: $OUT/logs/escapes.log"
python pipeline/1-audit/escapes/escape_audit.py \
  --clauses "$CLAUSES" \
  --db "$DB" \
  --n "${N:-0}" \
  --seed "${SEED:-0}" \
  --outdir "$OUT" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/escapes.log"
echo "Done. Report: $OUT/report.json"
