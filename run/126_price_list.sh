#!/bin/bash
# The price of each operation (strategic review 2026-11-04, item 1): how much detection a provably robust detector
# loses to each operation of the catalogue, and how much of the full catalogue's cost comes from dropping the
# two-sided features vs. from the monotone constraints on the rest.
#   0. the training inputs (Claude, 2026-11-04, seconds): scripts/a_price_list.py derive, from the sums-layout direction
#      table that Table 7's sums row was trained on (a_directions_derived_sums_v2), into artifacts/experiments/a_price_list.
#      Self-checks: the composed full catalogue equals the table's M_full_pre column and the row's training files.
#      Variants that leave the training inputs unchanged (no section add, no shift, no slack overwrite) are skipped.
#      Also warnings.neutralize.txt: the 88 parser-warning features, which the derivation does not model.
#   1. one monotone GBDT per remaining variant (the full catalogue minus one operation, or minus the three header
#      overwrites), on the 10% sums store, as Table 7's sums row (seed-0-s10-mfull-sums-pre-v2, reused as the baseline);
#   2. two unconstrained controls on the same store: the full catalogue's two-sided features dropped but no monotone
#      constraints (the cost of dropping alone), and only the parser warnings dropped (the cost of not modeling them);
#   3. the table: AUC, TPR at 1% and 0.1% FPR, against the unconstrained reference (seed-0-s10-ref, 93.5%).
#
# Diagnostic (Claude, 2026-11-04, from existing tables and models): of the features row's 1,060 two-sided features, 683
# are recovered by the sums re-encoding (21.4% of the unconstrained model's gain); of the 377 left, 200 are section hash
# buckets coupled under rename (3.7%), 89 are truly two-sided overwrites (11.0%), 88 are the unmodeled parser warnings
# (6.3%). Leaving one operation out regains 301 features for rename, 27 for the three overwrites, 0-17 otherwise.
# Hypothesis: no single operation costs more than about 1 point of TPR at 1% FPR (rename and the header overwrites the
# most); dropping and constraining each account for roughly half of the full catalogue's 3.9 points.
#
# Resources (measured, 2026-11-04, NUM_WORKERS=8): 12 trainings in ~12 min. NUM_WORKERS sets LightGBM's threads.
#
# Result (read 2026-11-04): the hypothesis failed on both counts. TPR at 1% FPR (reference 93.5%; full catalogue
# 89.6%, -3.9): dropping the two-sided features alone costs 0.2 points, so the monotone constraints cost ~3.6. Leaving
# out one operation regains 2.1 points for the import addition (it frees the 1,282 import hash buckets from their
# constraints), 1.4 for the three header overwrites together (header fields 1.2, checksum 0.6, DOS stub none), 0.4 each
# for the debug and signature rewrites, and nothing for rename (despite 301 regained features), append, or extension
# (-0.3 to +0.0: the noise floor). Dropping the parser warnings costs nothing (+0.1), so they need not be modeled.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

S=artifacts/experiments/a_directions_derived_sums_v2
P=artifacts/experiments/a_price_list
F=artifacts/features/ember2024-sums-10-v2
M=artifacts/models/gbdt

echo "Step 0: the training inputs into $P."
python scripts/a_price_list.py derive \
  --directions $S/directions_sums.csv \
  --reference $S \
  --outdir $P
grep '^pefilewarnings:' $S/M_full-pre.neutralize.txt > $P/warnings.neutralize.txt

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads "$NUM_WORKERS" \
    --features $F \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}

echo "Step 1: one monotone GBDT per variant."
while read -r v; do
  [ "$v" = "M_full" ] && continue
  train "-s10-price-$v" \
    --neutralize $P/$v.neutralize.txt \
    --monotone $P/$v.monotone.tsv
done < $P/variants.txt

echo "Step 2: the unconstrained controls."
train -s10-price-droponly \
  --neutralize $S/M_full-pre.neutralize.txt
train -s10-price-nowarnings \
  --neutralize $P/warnings.neutralize.txt

echo "Step 3: the table (also $P/table.json)."
args=(--model "unconstrained=$M/seed-0-s10-ref"
      --model "unconstrained, warnings dropped=$M/seed-0-s10-price-nowarnings"
      --model "M_full, dropped only=$M/seed-0-s10-price-droponly"
      --model "M_full (Table 7)=$M/seed-0-s10-mfull-sums-pre-v2")
while read -r v; do
  [ "$v" = "M_full" ] && continue
  args+=(--model "$v=$M/seed-0-s10-price-$v")
done < $P/variants.txt
args+=(--model "M_add (Table 7)=$M/seed-0-s10-madd-sums-pre-v2")
python scripts/a_price_list.py table \
  "${args[@]}" \
  --out $P/table.json
