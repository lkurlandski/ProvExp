#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=item-checks
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=1-00:00:00
#SBATCH --mem=64G
#
# The item layer's checks (Appendix D, Table 9; Section 5.1): the readouts over the item table reproduce every feature
# bit for bit, also for the sums extractor (exact); single-byte flips of the header and of each directory's data move
# only items located there (locating); random in-place writes predicted by Proposition 1, compared with re-extraction
# (margins). Pilot: runs 90-96 and 118 (57 min for exact on 2,000 files at 24 workers).
# Output: $OUT_ROOT/1-audit/item-checks/{exact,locating-header,locating-directories,margins}/report.json.
# Knobs: FILES (default: the evaluation set of 2-features/files, 1,000 malware and 1,000 benign files), DB, LOCATING_FILES (files flipped per region, default 20,
# as the pilot), MARGINS_FILES (files given random writes, 0: all), SEED.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

FILES="${FILES:-$OUT_ROOT/2-features/files/ts.parquet}"
DB="${DB:-$EMBER2024_DATA/ts}"
OUT=$OUT_ROOT/1-audit/item-checks
mkdir -p "$OUT/logs"

echo "Step 1/3: exact readouts (G1, G2, and the sums extractor). Log: $OUT/logs/exact.log"
python pipeline/1-audit/item-checks/item_checks.py exact \
  --files "$FILES" \
  --db "$DB" \
  --sums \
  --outdir "$OUT/exact" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/exact.log"

for region in header directories; do
  echo "Step 2/3: locating, $region bytes flipped. Log: $OUT/logs/locating-$region.log"
  python pipeline/1-audit/item-checks/item_checks.py locating \
    --files "$FILES" \
    --db "$DB" \
    --region "$region" \
    --num_files "${LOCATING_FILES:-20}" \
    --seed "${SEED:-0}" \
    --outdir "$OUT/locating-$region" \
    --workers "$NUM_WORKERS" \
    &> "$OUT/logs/locating-$region.log"
done

echo "Step 3/3: margins, random in-place writes. Log: $OUT/logs/margins.log"
python pipeline/1-audit/item-checks/item_checks.py margins \
  --files "$FILES" \
  --db "$DB" \
  --limit "${MARGINS_FILES:-0}" \
  --seed "${SEED:-0}" \
  --outdir "$OUT/margins" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/margins.log"
echo "Done. Reports: $OUT/*/report.json"
