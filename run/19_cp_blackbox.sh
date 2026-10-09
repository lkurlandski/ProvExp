#!/bin/bash
# CP.3 (docs/cp_plan.md): instrumented vs. black-box provenance at the window level, through their statistics, from
# the provenance.npz of run/17_pf1_window_scores.sh (the first PB1-configuration run that saves them). Seconds.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
OUT=artifacts/reports/cp_blackbox.md
echo "CP.3: statistics of the instrumented vs. black-box provenance from $RUN."
echo "Report: $OUT"

python scripts/cp_blackbox.py \
  --run "$RUN" \
  > "$OUT"

echo "Done. See $OUT"
