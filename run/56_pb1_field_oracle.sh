#!/bin/bash
# PB1 pilot, field-occlusion oracle baseline (docs/review-2026-10-14.md, item 1; docs/revision-plan.md B7).
#
# Adds one direct baseline to the 100 pilot files: occlude each parsed PE field and section (one extraction each),
# rank bytes by their region's drop, under the same PE-aware deletion operator. This is the structure-aware upper
# bound a defender could build with a PE parser, so it tests whether the byte-level pullback's win is just knowing
# the parser's read set (the oracle knows it too). Method name in the tables: field_occlusion.
#
# Pass 1 (the 64/256/1,024/4,096-window occlusion sweep and KernelSHAP over the windows) is reused from the pilot
# baselines run, so this only runs pass 2 plus the oracle's ~130-250 region extractions per file. Expect roughly
# 1-2 h on 16 workers (the oracle's cost is dominated by a few large files; the script prints its predicted cost
# before starting). Run in tmux. Smoke-tested on 2 files (field_occlusion flows through pb1_tables).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/faithfulness-seed0-field-oracle.log
echo "PB1 field-occlusion oracle, 100 pilot files, GBDT, reusing the baselines' pass-1 scores (16 workers, ~1-2 h)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-oracle/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --num_files 100 \
  --num_workers 16 \
  --header typical \
  --classifiers gbdt \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --tiebreak random \
  --field_oracle \
  --timeout 28800 \
  --tag oracle \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --reuse_scores artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-ties \
  &> "$LOG"

echo "Tables: artifacts/reports/pb1_tables-oracle.md"
python scripts/pb1_tables.py --seed 0 --fill zeros-typical-header-oracle > artifacts/reports/pb1_tables-oracle.md
echo "Done. Compare field_occlusion with occlusion and the byte-level pullback in the paired-comparison and cost tables."
