#!/bin/bash
# Derivation steps 2-3, checks G1 and G2 (docs/item-layer-design.md): the item table every feature type records, read
# through its declared readouts, must reproduce the extractor's feature vector bit for bit (G1; every feature but the
# 88 pefilewarnings, merged imports and thrember's original imports), and the items spread over their bytes must
# reproduce today's provenance (G2). G1 and G2 on the 100 pilot files; G1 alone on the 2,000-file set (decided by the
# user, 2026-10-27; G2 there would cost a provenance computation per file, ~15-40 min).
# Hypothesis: both pass; any failure is a rare float-ordering case or an unusual layout, not a conceptual one.
#
# Took 46 s (pilot) and 234 s (2,000 files) (2026-10-27). Result: G1 exact on 100/100 and 2,000/2,000 files (both
# import variants); G2 equal on 100/100 (max relative difference 0.0). Hypothesis held, with no debugging round.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/item_checks

echo "G1 + G2 on the 100 pilot files. Log: artifacts/logs/item_checks_exact_pilot.log"
python scripts/item_checks.py exact \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir $D/exact-pilot \
  --workers 16 \
  &> artifacts/logs/item_checks_exact_pilot.log

echo "G1 on the 2,000-file set. Log: artifacts/logs/item_checks_exact_2000.log"
python scripts/item_checks.py exact \
  --files artifacts/explanation_set/ts.parquet \
  --outdir $D/exact-2000 \
  --workers 16 \
  --no_g2 \
  &> artifacts/logs/item_checks_exact_2000.log

echo "Done. Reports: $D/exact-pilot/report.json, $D/exact-2000/report.json"
