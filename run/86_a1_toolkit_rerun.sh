#!/bin/bash
# Direction A, Table A1's toolkit columns, re-run with the fixed harness (2026-10-26): an attacked file that no longer
# parses as a PE counts as invalid, not evaded (secml-malware's shift attacks overwrite the MZ header on files whose
# first section has raw offset 0; docs/upstream-issues.md item 4), and with the PV-all row (run 85) added. Run after
# run 85. Supersedes run 81's step 3. FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware
# attacks against our own detectors, on our own pilot samples, to evaluate defenses.
# Hypothesis: run 81's numbers corrected post hoc -- seen 0% on every constrained row, held-out 18% PV-seen, 0% for the
# M_full C4 rows, 35-40% for the M_add rows (header_fields, outside M_add) -- with the shift outputs on 16344ac4 and
# 48d9cc0c now counted invalid; PV-all ~0% on every attack (all eight are its seen attacks).
#
# Estimate: ~1.5 h on 16 workers (run 81's step 3: 1,912 attack runs in 80 min; PV-all adds ~180 runs). The user ran it
# with --num_workers 32 (2026-10-26): 2,088 attack runs in 47 min. Result: as hypothesised, exactly; PV-all 0 on all eight.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

F=artifacts/features/ember2024-sums-10
M=artifacts/models/gbdt
LOG=artifacts/logs/a1_evaluate_rerun.log

echo "Eight attacks x seven defenses on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir artifacts/experiments/a1/toolkit_v2 \
  --features $F \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --defense madd-feat=$M/seed-0-s10-madd-feat \
  --defense madd-sums=$M/seed-0-s10-madd-sums \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums \
  --num_workers 32 \
  --seed 0 \
  &> "$LOG"

echo "Done. Toolkit table: artifacts/experiments/a1/toolkit_v2/table.json"
