#!/bin/bash
# Seed-0 scale-up to 500 files, step 3 of 6: the deletion operator's robustness variants for pullback faithfulness, at
# 256 windows only (no sweep, no KernelSHAP over windows), GBDT + MLP:
#   zeros                   level 2: header fields zeroed (gives the share of the byte-level margin due to typical values)
#   random-typical-header   level 3 with random content bytes
#   random                  level 2 with random content bytes
# Needs step 1 only, so it can run before, after, or (on a split of the CPUs) alongside step 2. Expect about 45 min per
# variant on 16 workers, about 2.5 h in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

run_variant() {  # fill, header, variant directory name
  local LOG=artifacts/logs/faithfulness-seed0-$3.log
  echo "Variant $3 (--fill $1 --header $2), 500 files (16 workers, about 45 min)."
  echo "Output: artifacts/experiments/e1/seed-0/$3/"
  echo "Log:    $LOG"
  OMP_NUM_THREADS=1 python scripts/faithfulness.py \
    --seed 0 \
    --files artifacts/explanation_set/ts-scaleup500-seed0.parquet \
    --num_files 500 \
    --fill "$1" \
    --header "$2" \
    --classifiers gbdt mlp \
    --tiebreak random \
    --tag scaleup500 \
    --num_workers 16 \
    &> "$LOG"
  python scripts/pb1_tables.py \
    --fill "$3" \
    > "artifacts/reports/pb1_tables-$3.md"
}

echo "Step 3/6: the operator variants of pullback faithfulness."
run_variant zeros zeros zeros-scaleup500
run_variant random typical random-typical-header-scaleup500
run_variant random zeros random-scaleup500
echo "Instrumented vs. black-box P at 256 windows under level 2 (as in the pilot's table; seconds)."
python scripts/cp_blackbox.py \
  --run artifacts/experiments/e1/seed-0/zeros-scaleup500 \
  > artifacts/reports/cp_blackbox-zeros-scaleup500.md
echo "Done. Tables: artifacts/reports/pb1_tables-{zeros,random-typical-header,random}-scaleup500.md"
echo "      and artifacts/reports/cp_blackbox-zeros-scaleup500.md"
