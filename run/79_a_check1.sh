#!/bin/bash
# Direction A, go/no-go check 1 (docs/direction-A-mock.md, Table A0): does C1 predict the edited file's features from
# the original alone, without extracting the edited file? On the 100 pilot files, apply two loader-safe
# transformations -- overlay append (Section 6 row 1, item-creating: guard byte + 4 KB attacker bytes) and an in-place
# DOS-header overwrite (row 3, content: bytes [2,60)) -- predict phi(z') with C1, re-extract z', compare feature by
# feature.
#
# Hypothesis (docs/direction-A-model S4a): C1 is exact wherever assumptions A1-A4 hold; the only expected mismatches
# are A2 locality failures -- a section whose declared raw size overruns the (truncated) file, so appending extends
# its clamped content. GO if >= 95% of A-applicable pairs are exact with every mismatch explained by A1-A4.
#
# Fast (~2 min incl. the SimpleDB index build; ~0.25 s/file/transform). pefilewarnings is excluded (no items; docs S7).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Table A0: C1 vs re-extraction under overlay append, 100 pilot files."
python scripts/a_c1_table0.py \
  --outdir artifacts/experiments/a_c1 \
  --append_size 4096 \
  --seed 0

echo "Done. Report: artifacts/experiments/a_c1/report.json ; per-pair: table0.parquet ; mismatches.parquet"
