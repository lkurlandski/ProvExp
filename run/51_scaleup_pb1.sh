#!/bin/bash
# Seed-0 scale-up to 500 files, step 2 of 6: pullback faithfulness and cost (paper Section 4.1) with the full baseline
# set, for the GBDT and the MLP, primary operator (level 3: header fields take typical values), random tie-breaks:
# occlusion at 64/256/1,024/4,096 windows, KernelSHAP over 256 windows (2,048 coalitions), the pullbacks at bytes and
# windows, the black-box pullback, and the unsigned diagnostic. It saves window_scores.npz and provenance.npz, which
# steps 4 and 5 reuse. Needs step 1.
#
# THE LONG ONE: about 12 h on 16 workers (71% of it is the files over 2 MB). The runner prints a predicted cost at the
# start from its cost model, fitted before the string features became 2.1x faster (2026-10-13), so it is about twice
# too pessimistic. The progress bar counts predicted work, not files. Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/faithfulness-seed0-scaleup500.log
TABLES=artifacts/reports/pb1_tables-scaleup500.md
echo "Step 2/6: pullback faithfulness, 500 files, full baselines, GBDT + MLP (16 workers, about 12 h)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-scaleup500/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --files artifacts/explanation_set/ts-scaleup500-seed0.parquet \
  --num_files 500 \
  --header typical \
  --classifiers gbdt mlp \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --tiebreak random \
  --timeout 28800 \
  --tag scaleup500 \
  --num_workers 16 \
  &> "$LOG"

echo "Tables: $TABLES"
python scripts/pb1_tables.py \
  --fill zeros-typical-header-scaleup500 \
  > "$TABLES"
echo "Done. Compare $TABLES with artifacts/reports/pb1_tables-baselines-ties.md (the pilot)."
