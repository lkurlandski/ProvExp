#!/bin/bash
# AU, robustness of the evasion result (docs/experiments/audit.md, "Held-out evasion and realizability"): the same
# recipes as run 46, but on 1,000 fresh held-out malware (excluding run 44's 200 files, on which the fields were
# confirmed), scoring only files MalConv detects at its 1% FPR threshold, redrawing random recipes that break the parse,
# and adding the realizable recipes (only what the Windows loader lets an attacker change) with their own null.
# Paired statistics (bootstrap CIs, McNemar / Wilcoxon) at the end of the log. Needs runs 44 and 46's inputs.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_evade_heldout-seed0.log
echo "AU held-out evasion: 1,000 fresh malware, detected only, realizable recipes (12 workers, about 7-10 min)."
echo "Output: artifacts/experiments/audit_evade/heldout-seed-0/"
echo "Log:    $LOG   (per-recipe rates with CIs and the paired tests are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_evade.py \
  --seed 0 \
  --num_files 1000 \
  --detected_only \
  --random_retries 20 \
  --realizable \
  --exclude artifacts/experiments/audit_scramble/seed-0/files.parquet \
  --run_name heldout-seed-0 \
  --num_workers 12 \
  &> "$LOG"

echo "Done. Summary: tail -n 30 $LOG"
