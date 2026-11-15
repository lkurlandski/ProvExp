#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=cost-split
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=2-00:00:00
#SBATCH --mem=128G
#
# Where the monotone detector's cost lies (§5.4's *Where the cost lies*; docs/evidence/fable-cost-of-robustness.md,
# Section 4, experiments 1-3). GBDTs on the sums, loose table, full threat model:
#   droponly          unconstrained, the two-sided sums dropped: the evidence in sums the attacker can place
#   fixed-only        unconstrained, only the fixed sums: unevadable with no constraint at all
#   mono-rounds       the monotone detector as in Table 5, with ITERATIONS boosting rounds instead of 500 (the best
#                     round on the validation split is kept)
#   mono-<method>     the same with LightGBM's constraint method basic, intermediate or advanced. LightGBM falls
#                     back to basic unless every feature is offered at every split, so these three set
#                     feature_fraction and feature_fraction_bynode to 1 (0.9 elsewhere); basic is the control.
# Inputs: SUMS (the sums store), DIR (the loose table: directions_sums.csv, M_full-pre.{neutralize.txt,monotone.tsv}),
# REF and MONO (the unconstrained and the monotone-sums detectors, the table's reference rows).
# Output: $OUT_ROOT/4-detectors/cost-split/ (models/<variant>/, table.json: TPR at 1% and 0.1% FPR on the test and
# the training split, the gain share of the fixed sums, the structural check of the constraints). A model whose
# model.txt exists is skipped.
# Knobs: ITERATIONS (default 3000), METHODS (default "basic intermediate advanced"), COMPLETE (1: only complete
# files, the scale-up; 0: every file, the pilot stores), LIMIT (files per split; smoke tests).
# Pilot (10% stores, minutes per model):
#   OUT_ROOT=artifacts/experiments/cost_split COMPLETE=0 \
#   SUMS=artifacts/features/ember2024-sums-10-v2 DIR=artifacts/experiments/a_directions_derived_sums_loose \
#   REF=artifacts/models/gbdt/seed-0-s10-ref MONO=artifacts/models/gbdt/seed-0-s10-mfull-sums-loose \
#   bash pipeline/4-detectors/cost-split/run.sh
# SCALE-UP TO CONFIRM: time and memory.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

SUMS=${SUMS:-$OUT_ROOT/2-features/sums}
DIR=${DIR:-$OUT_ROOT/3-directions/loose}
DET=$OUT_ROOT/4-detectors
REF=${REF:-$DET/unconstrained}
MONO=${MONO:-$DET/monotone-sums}
P=$DET/cost-split
ITERATIONS=${ITERATIONS:-3000}
METHODS=${METHODS:-basic intermediate advanced}
mkdir -p "$P/logs"
EXTRA=()
if [[ "${COMPLETE:-1}" == 1 ]]; then EXTRA+=(--complete_only); fi
TABLE_EXTRA=("${EXTRA[@]}")
if [[ -n "${LIMIT:-}" ]]; then EXTRA+=(--limit "$LIMIT"); fi

echo "The fixed-only training input into $P."
python pipeline/4-detectors/cost-split/cost_split.py derive \
  --directions "$DIR/directions_sums.csv" \
  --outdir "$P"

train() {  # variant, then train_classic's arguments
  local v=$1; shift
  if [[ -f $P/models/$v/model.txt ]]; then echo "  $v exists; skipping."; return; fi
  echo "  Training $v. Log: $P/logs/train-$v.log"
  python pipeline/4-detectors/train/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --features "$SUMS" \
    --model_dir "$P/models/$v" \
    --num_threads "$NUM_WORKERS" \
    "${EXTRA[@]}" \
    "$@" \
    &> "$P/logs/train-$v.log"
}

echo "The two unconstrained detectors."
train droponly \
  --neutralize "$DIR/M_full-pre.neutralize.txt"
train fixed-only \
  --neutralize "$P/fixed-only.neutralize.txt"

echo "The monotone detector with $ITERATIONS rounds, then one per constraint method."
args=(--model "unconstrained=$REF"
      --model "two-sided dropped=$P/models/droponly"
      --model "fixed sums only=$P/models/fixed-only"
      --model "monotone (as in Table 5)=$MONO")
train mono-rounds \
  --neutralize "$DIR/M_full-pre.neutralize.txt" \
  --monotone "$DIR/M_full-pre.monotone.tsv" \
  --param "num_iterations=$ITERATIONS"
args+=(--model "monotone, $ITERATIONS rounds=$P/models/mono-rounds")
for method in $METHODS; do
  train "mono-$method" \
    --neutralize "$DIR/M_full-pre.neutralize.txt" \
    --monotone "$DIR/M_full-pre.monotone.tsv" \
    --param "monotone_constraints_method=$method" \
    --param "feature_fraction=1.0" \
    --param "feature_fraction_bynode=1.0" \
    --param "num_iterations=$ITERATIONS"
  args+=(--model "monotone, $method=$P/models/mono-$method")
done

echo "The table: $P/table.json"
python pipeline/4-detectors/cost-split/cost_split.py table \
  --features "$SUMS" \
  --directions "$DIR/directions_sums.csv" \
  "${args[@]}" \
  --num_threads "$NUM_WORKERS" \
  "${TABLE_EXTRA[@]}" \
  --out "$P/table.json"
