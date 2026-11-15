#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=price-list
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=2-00:00:00
#SBATCH --mem=128G
#
# The price of each declaration (§4.3-4.4, §5.4's *Where the cost lies*; run 126 at pilot scale): the monotone
# detector over sums retrained with the full catalogue minus one operation (and minus the three overwrites), each on
# the full training split's complete files, so the detection each operation costs can be read off; plus two
# unconstrained controls (the warnings dropped; M_full's two-sided features dropped, no constraint).
# Inputs: 2-features/sums, 3-directions/loose (directions_sums.csv and M_full-pre.*), 4-detectors/{unconstrained,
# monotone-sums,additions-only} (the table's reference rows).
# Output: $OUT_ROOT/4-detectors/price-list/ (<variant>.{neutralize.txt,monotone.tsv}, variants.txt; the models in
# models/<variant>/; table.json with AUC and TPR at 1% and 0.1% FPR, thresholds on the validation split). A model
# whose model.txt exists is skipped.
# Knobs: LIMIT (files per split; smoke tests). Cost: ~16 GBDTs, ~20-40 min each on the full split.
# SCALE-UP TO CONFIRM: time and memory.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

SUMS=$OUT_ROOT/2-features/sums
DIR=$OUT_ROOT/3-directions/loose
DET=$OUT_ROOT/4-detectors
P=$DET/price-list
mkdir -p "$P/logs"
LIMIT_ARG=()
if [[ -n "${LIMIT:-}" ]]; then LIMIT_ARG=(--limit "$LIMIT"); fi

echo "The variants' training inputs into $P. Log: $P/logs/derive.log"
python pipeline/4-detectors/price-list/price_list.py derive \
  --directions "$DIR/directions_sums.csv" \
  --reference "$DIR" \
  --outdir "$P" \
  &> "$P/logs/derive.log"
grep '^pefilewarnings:' "$DIR/M_full-pre.neutralize.txt" > "$P/warnings.neutralize.txt"

train() {  # variant, then train_classic's arguments
  local v=$1; shift
  if [[ -f $P/models/$v/model.txt ]]; then echo "  $v exists; skipping."; return; fi
  echo "  Training $v. Log: $P/logs/train-$v.log"
  python pipeline/4-detectors/train/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --complete_only \
    --features "$SUMS" \
    --model_dir "$P/models/$v" \
    --num_threads "$NUM_WORKERS" \
    "${LIMIT_ARG[@]}" \
    "$@" \
    &> "$P/logs/train-$v.log"
}

echo "One monotone GBDT per variant, and the two unconstrained controls."
while read -r v; do
  [[ $v == M_full ]] && continue
  train "$v" \
    --neutralize "$P/$v.neutralize.txt" \
    --monotone "$P/$v.monotone.tsv"
done < "$P/variants.txt"
train droponly \
  --neutralize "$DIR/M_full-pre.neutralize.txt"
train nowarnings \
  --neutralize "$P/warnings.neutralize.txt"

echo "The table: $P/table.json"
args=(--model "unconstrained=$DET/unconstrained"
      --model "unconstrained, warnings dropped=$P/models/nowarnings"
      --model "M_full, dropped only=$P/models/droponly"
      --model "M_full (monotone-sums)=$DET/monotone-sums")
while read -r v; do
  [[ $v == M_full ]] && continue
  args+=(--model "$v=$P/models/$v")
done < "$P/variants.txt"
args+=(--model "M_add (additions-only)=$DET/additions-only")
python pipeline/4-detectors/price-list/price_list.py table \
  "${args[@]}" \
  --protocol scaleup \
  --out "$P/table.json"
