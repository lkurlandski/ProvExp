#!/bin/bash
# PF1's inputs: the PB1 baselines configuration re-run, now that faithfulness.py also saves window_scores.npz (every
# direct problem-space explanation's per-window scores, and the features of the original and fully ablated file;
# docs/pf1_plan.md). Same files, operator, sweep, and KernelSHAP budget as run/12_pb1_baselines.sh, so its curves
# should reproduce that run's exactly (the runner is deterministic), which doubles as a check.
#
# Written to a new directory (tag baselines-scores) so the original baselines run is kept.
# 32 physical cores with hyperthreading (64 logical CPUs): 64 workers use the extra threads, which helps this
# single-threaded, CPU-bound work but far less than doubling. Expect roughly 1.5-2 h. Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/faithfulness-seed0-zeros-typical-baselines-scores.log
echo "PF1 inputs: faithfulness.py on the 100 pilot files (baselines configuration, 64 workers, about 1.5-2 h)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"

OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --num_files 100 \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --header typical \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --timeout 28800 \
  --tag baselines-scores \
  --num_workers 64 \
  &> "$LOG"

echo "Done. See the end of $LOG for the summary."
