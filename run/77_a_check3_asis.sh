#!/bin/bash
# Direction A, go/no-go check 3 (docs/direction-A-mock.md), the "features as they are" rows: how much detection a
# sound monotone GBDT keeps when it may use only the features run 76 found one-directional (fixed: free; up: monotone
# increasing; down: monotone decreasing; both: zeroed). Full EMBER-2024 splits, seed 0, 16 threads. Compare with the
# unconstrained GBDT (artifacts/models/gbdt/seed-0, test ROC-AUC 0.99759).
#   1. M_add, both-features dropped, no constraints   (the cost of dropping alone)
#   2. M_add, dropped + monotone                       (the "C4 directions on features" row of Table A1)
#   3. M_add, import quirk assumed fixed               (sensitivity: the 1,025 import features become monotone-usable)
#   4. M_full, dropped + monotone
#   5. M_full, import quirk assumed fixed
# Hypothesis: the kept features (header fields, exports, library presence, section counts) still detect well on EMBER,
# AUC ~0.97-0.98 for 2 (below 0.9976), ~0.985 for 3, ~0.96 for 4; the gap to 0.9976 is what the re-encodings must
# close (they need re-extraction; a later run).
#
# Estimate: ~6-7 min per model (smoke test: 200k samples in 0.63 min with 16 threads; the full split is ~10x, plus
# loading ~27 GB per model), ~35 min in all. Peak memory ~30 GB.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

D=artifacts/experiments/a_directions
train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}

train -a-madd-drop    --neutralize $D/M_add.neutralize.txt
train -a-madd-mono    --neutralize $D/M_add.neutralize.txt              --monotone $D/M_add.monotone.tsv
train -a-madd-mono-qf --neutralize $D/M_add-quirkfixed.neutralize.txt   --monotone $D/M_add-quirkfixed.monotone.tsv
train -a-mfull-mono   --neutralize $D/M_full.neutralize.txt             --monotone $D/M_full.monotone.tsv
train -a-mfull-mono-qf --neutralize $D/M_full-quirkfixed.neutralize.txt --monotone $D/M_full-quirkfixed.monotone.tsv

echo "Test metrics:"
for s in -a-madd-drop -a-madd-mono -a-madd-mono-qf -a-mfull-mono -a-mfull-mono-qf; do
  python -c "import json,sys; m=json.load(open(sys.argv[1])); print(sys.argv[2], round(m['ts_metrics']['roc'], 5))" \
    artifacts/models/gbdt/seed-0$s/metrics.json "$s"
done
