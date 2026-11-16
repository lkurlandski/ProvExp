#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=results
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-08:00:00
#SBATCH --mem=200G
#
# The scale-up's tables from the stored models and attack outputs (runs no attack). FOR ACADEMIC SECURITY RESEARCH
# ONLY: reads outputs of attacks run against our own detectors.
#   tables     (scaleup_tables.py) per detector: AUC and test TPR at the validation split's 1% and 0.1% FPR thresholds;
#              the share of ALL the evaluation set's malware still detected after each attack and after any attack, at
#              both thresholds, files outside the population counted (Tables 4, 5 and 11; escapes per escape); the
#              detected malware within the hand table's 1.57-logit maximum drop (R3); the monotone detectors' split-gain
#              share on features no edit moves (R15)
#   coverage   (coverage.py) the lowerable features the toolkit's outputs on the training malware lowered, by class,
#              `modeled` without pefile's warnings (§5.3; R12); PV's hole by class and witnessed by our edits
#   erdalt     (erdalt_hole.py) ERDALT's first layer against the derived table, with the share without the warnings (R12)
# Inputs: everything upstream (2-features, 3-directions/loose, 4-detectors, 5-attacks, 1-audit/catalogue); a missing
# detector or attack output is left out of the tables, not an error.
# Output: $OUT_ROOT/6-results/{tables,coverage,erdalt}/. Knobs: PARTS (default "tables coverage erdalt").
# Cost: minutes, plus coverage's population check of the 10,000 training malware (~10-20 min on 36 cores).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
source pipeline/common.sh

PARTS="${PARTS:-tables coverage erdalt}"
DATA="${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}"
DIR=$OUT_ROOT/3-directions/loose
DET=$OUT_ROOT/4-detectors
OUT=$OUT_ROOT/6-results
mkdir -p "$OUT/logs"

for part in $PARTS; do
  case $part in
    tables)
      echo "The detection and attack tables. Log: $OUT/logs/tables.log"
      python pipeline/6-results/scaleup_tables.py \
        --root "$OUT_ROOT" \
        --outdir "$OUT/tables" \
        &> "$OUT/logs/tables.log"
      grep -E "^\S+ +AUC" "$OUT/logs/tables.log" || tail -3 "$OUT/logs/tables.log" ;;
    coverage)
      echo "Coverage of the lowerable features by the toolkit's outputs. Log: $OUT/logs/coverage.log"
      python pipeline/6-results/coverage.py \
        --outdir "$OUT/coverage" \
        --directions_dir "$DIR" \
        --stem M_full-pre-control \
        --adv_dir "$DET/material/sums" \
        --adv_features "$OUT_ROOT/2-features/sums" \
        --db "$DATA/tr" \
        --holes "$DET/pv-selection/hole.csv" \
        --edits "$OUT_ROOT/1-audit/catalogue/edits.parquet" \
        --sizes 100 1000 10000 \
        --num_workers "$NUM_WORKERS" \
        &> "$OUT/logs/coverage.log"
      tail -2 "$OUT/logs/coverage.log" | cut -c1-300 ;;
    erdalt)
      echo "ERDALT's first layer against the derived table. Log: $OUT/logs/erdalt.log"
      python pipeline/6-results/erdalt_hole.py \
        --model "$DET/erdalt" \
        --directions "$DIR/M_full-pre-control" \
        --features "$OUT_ROOT/2-features/sums" \
        --protocol scaleup \
        --pilot_files "$OUT_ROOT/2-features/files/ts.parquet" \
        --db "$DATA/ts" \
        --outdir "$OUT/erdalt" \
        &> "$OUT/logs/erdalt.log"
      grep -E "weight_share_violating" "$OUT/logs/erdalt.log" ;;
    *) echo "Unknown part $part (tables coverage erdalt)." >&2; exit 1 ;;
  esac
done
echo "Done. Outputs: $OUT/{tables,coverage,erdalt}/"
