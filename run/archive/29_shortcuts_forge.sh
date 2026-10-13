#!/bin/bash
# 3-B exploitability (docs/archive/shortcuts_plan.md): forge the confirmed artifacts (one per top feature: DEBUG.Size 0x54, the
# certificate-table size, the .rsrc name) together into 2,000 held-out malware, at the bytes each file's P names;
# evasion at the 1%-validation-FPR threshold, against the original GBDT and the neutralized one (run 28).
# Smoke test: 40 files in 0.3 min on 8 workers per model (16% evasion vs. 0% random on the original, 0% neutralized).
# Expect about 10 minutes per model on 16 workers (plus 1-2 min for the validation threshold).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for TAG in gbdt neutral; do
  if [ "$TAG" = gbdt ]; then MODEL=artifacts/models/gbdt/seed-0/model.txt; else MODEL=artifacts/models/gbdt/seed-0-neutral/model.txt; fi
  LOG=artifacts/logs/shortcuts_forge-seed0-$TAG.log
  echo "3-B forge, $TAG: 2,000 held-out malware (16 workers, about 10 min)."
  echo "Output: artifacts/experiments/shortcuts_forge/seed-0/$TAG/"
  echo "Log:    $LOG   (evasion rates are at its end)"
  OMP_NUM_THREADS=1 python scripts/shortcuts_forge.py \
    --seed 0 \
    --model "$MODEL" \
    --tag "$TAG" \
    --num_files 2000 \
    --num_workers 16 \
    &> "$LOG"
done

echo "Done. Summary: tail -n 30 artifacts/logs/shortcuts_forge-seed0-gbdt.log artifacts/logs/shortcuts_forge-seed0-neutral.log"
