#!/bin/bash
# A' go/no-go check 1 (docs/direction-A-prime-mock.md): constraints learned from the toolkit's adversarial outputs
# (per feature, the smallest and largest change seen; a feature no attack moved is fixed) as the exact solver's region,
# against the battery (per-file union of the toolkit, run 105, and the adaptive search, run 109) on the 10% detectors.
# Go if, on PV-seen, the learned region certifies at least a third of the files the battery evades.
# Circular cells, by construction: PV built from attack set S keeps only features S never lowered and is monotone in
# them, so a region learned from S certifies PV(S) on every file (PV-seen/seen, PV-all/all). The informative cells are
# PV-seen and the reference learned from all eight attacks.
# Hypothesis: on PV-seen, learned-from-all still certifies a good share of the battery's evasions, because the adaptive
# search moves section-hash buckets in directions and by amounts the toolkit never produced.
#
# Estimate: 182 decision solves (decided in < 34 s each in check 0) on 16 workers: ~2-7 min; 300 s cap per solve.
# Ran 2026-10-30 (Claude, ~1 min; every solve decided, max 9 s). Learned regions: 2,014 features free (all eight
# attacks), 915 (seen four). Battery evades ref 27/47, PV-seen 15/22, PV-all 15/22.
#   circular cells (PV-seen/seen, PV-all/all, and PV-all/seen, since seen is a subset of all): certified 22/22, so
#     15/15 battery evasions wrongly certified, by construction;
#   informative cells: PV-seen/all certifies 0/22 (the solver evades all 22 in feature space); ref/all and ref/seen
#     certify 0/47.
# Hypothesis failed for the informative cells: learned regions do not give wrong certificates there, they give none
# (pooled per-feature largest changes are as vacuous as the budget-only region). Wrong certificates appear only where
# the region is learned from the same attacks as the defense, which restates A's PV hole. Brought to the user.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
E=artifacts/experiments
LOG=artifacts/logs/ap_check1_learned.log
echo "Check 1: learned constraints in the exact solver. Log: $LOG"
python scripts/ap_check1_learned.py \
  --outdir $E/ap_check1 \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --toolkit $E/a1/toolkit-v2/results.parquet $E/a1/toolkit_v2/results.parquet \
  --adaptive $E/ap_battery/adaptive/adaptive.parquet \
  --time_limit 300 \
  --workers 16 \
  &> "$LOG"

echo "Done. Report: $E/ap_check1/report.json"
