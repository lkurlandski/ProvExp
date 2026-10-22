#!/bin/bash
# Direction A, step 2 (docs/direction-A-threat-model.md): the provisional direction table for every EMBER v3 feature
# under the threat models M_add, M_shift, M_full, for the features and their layer-2 re-encodings. Hand-written
# per-group rules (a stand-in for C4 over the item table). No data needed; ~2 s.
# Hypothesis: most features are two-sided because of the readout (normalization, entropy, signed hashing), and the
# re-encodings make most of them one-directional under M_add.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

echo "Direction table -> artifacts/experiments/a_directions/ (directions.csv, summary.json)."
python scripts/a_directions.py \
    --outdir artifacts/experiments/a_directions
