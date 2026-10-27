#!/bin/bash
# Overlay gap witness (docs/item-layer-design.md, "First row confirmed"): on the 100 pilot files, append enough bytes
# to bring every section or directory extent pefile skips (because it runs past EOF) inside the file, and check
# whether overlay_size or any body_* count drops.
# Hypothesis: overlay_size drops on files with a section past EOF; the body_* sums do not, because sums.body_regions
# clips overrunning sections at EOF and starts the overlay region after every section's data.
#
# Took ~2 min (2026-10-27). Result: 100 files, 190 appends; 11 files have an extent past EOF (all through a section; 7
# of them cut at the dataset's 4,000,000-byte cap); overlay_size dropped on 8; no body_* count dropped. Hypothesis held.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

LOG=artifacts/logs/a_overlay_witness.log

echo "Overlay witness on the pilot files. Log: $LOG"
python scripts/a_overlay_witness.py \
  --outdir artifacts/experiments/a_overlay_witness \
  &> "$LOG"

echo "Done. Report: artifacts/experiments/a_overlay_witness/report.json"
