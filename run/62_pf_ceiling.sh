#!/bin/bash
# Identifiability ceiling of the exact pushforward (docs/theory.md, Pillar B), pilot files, seed 0. Run 61 recovered
# TreeSHAP from its pullback with R 0.80 (one step) -> 0.86 (exact). By Proposition Exact Pushforward (iii), the exact
# pushforward already recovers everything the bytes determine; this run asks where the rest is lost: the "twins" oracle
# restores the native split inside groups of features with identical provenance, which no method can tell apart.
# Hypothesis: at bytes, twins hold most of the gap (R near 0.95); at 256 windows, much less (dependence beyond twins).
#
# Smoke-tested on 4 files (4 workers): 28 s. Took 12 min on 16 workers (2026-10-16; the last, largest file alone ~5 min).
# Result: R 0.80 / 0.86 / 0.95 (one step / exact / twins) at bytes, 0.36 / 0.44 / 0.86 at windows (docs/theory.md).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG=artifacts/logs/pf_ceiling-seed0.log

echo "Identifiability ceiling of the exact pushforward (16 workers, about 12 min)."
echo "Output: artifacts/experiments/pf1/seed-0/zeros-typical-header-baselines-scores/ceiling/"
echo "Log:    $LOG"
OMP_NUM_THREADS=1 python scripts/pf_inverse.py \
  --run "$RUN" \
  --resolutions 0 256 \
  --iterations \
  --name ceiling \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Tables: tail -n 60 $LOG"
