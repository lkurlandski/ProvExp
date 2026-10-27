#!/bin/bash
# Derivation step 5, check G4 (docs/item-layer-design.md): the C1 engine (provexp.reach, with the extractor's
# recognizers and the catalogue's add_section declaration) re-runs Table A0's protocol (run 79: the 100 pilot files,
# append / dos_overwrite / LIEF add_section, tolerance 1e-4) next to the hand predictors, and is compared with both.
# Hypothesis: append exact on the 89 clean files, with the 11 overrun files flagged by the engine itself (the append
# writes a locating range: an extent past the end of the file); dos_overwrite exact on 100; add_section bit-equal to
# the hand predictor on 100 (same A4 residual against LIEF); bit-equal to the hand predictors on every predicted pair.
#
# Took ~3 min (2026-10-27). Result: hypothesis held. append: 11 flagged by the engine, exactly the 11 the hand rule
# excludes; bit-exact against re-extraction on 89/89. dos_overwrite: bit-exact on 100/100. add_section: bit-equal to
# the hand predictor on 100/100. Bit-equal to the hand predictors on all 289 predicted pairs, so runs 82-87 (which
# used them) carry over. Median engine time 3-21 ms per pair.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Table A0 with the C1 engine, 100 pilot files. Log: artifacts/logs/a_c1_engine.log"
python scripts/a_c1_table0.py \
  --outdir artifacts/experiments/a_c1_engine \
  &> artifacts/logs/a_c1_engine.log

echo "Done. Report: artifacts/experiments/a_c1_engine/report.json"
