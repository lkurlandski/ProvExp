#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=train
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-00:45:00
#SBATCH --mem=200G
#
# The detectors of Table 5 and the expert set (§5.2), on the full training split's complete files (--complete_only; the
# protocol of session 67), each written to $OUT_ROOT/4-detectors/<name>/ (the registry's `scaleup` set) with its
# test and validation predictions (the thresholds come from the validation split's goodware):
#   unconstrained       every EMBER feature, no constraint (the re-encoding's sums dropped)
#   monotone-features   monotone in the derived directions of EMBER's features (the loose table, M_full)
#   monotone-sums       monotone in the derived directions of the re-encoding over sums (the loose table, M_full)
#   additions-only      monotone-sums for the threat model of additions only (the loose table, M_add)
#   expert-set          Gimenez et al.'s 40 expert features, monotone increasing in all of them (their model)
#   trial               monotone in the directions learned by trying the operations (3-directions/trial)
# The learned defenses (adversarial training, PV, ERDALT, the leave-one-out folds, iterated adversarial training) read
# the attacks' outputs and train in 4-detectors/adversarial-training.
# Inputs: the stores $OUT_ROOT/2-features/{sums,expert} (2-features/featurize), the direction tables
# $OUT_ROOT/3-directions/loose/ (3-directions/derived), the trial table $OUT_ROOT/3-directions/trial/ (3-directions/trial;
# `trial` is skipped with a note while it is missing). A detector whose model.txt exists is skipped (rerun to resume).
# Output: $OUT_ROOT/4-detectors/<name>/ (model.txt, metrics.json, {ts,vl}_predictions.parquet).
# Knobs: DETECTORS (default all six), LIMIT (at most this many files per split; smoke tests). Resources: one GBDT at a time on NUM_WORKERS threads; the full split's sums
# store is ~25-30 GB in memory. SCALE-UP TO CONFIRM: time and memory (head-node session).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DETECTORS="${DETECTORS:-unconstrained monotone-features monotone-sums additions-only expert-set trial}"
SUMS=$OUT_ROOT/2-features/sums
EXPERT=$OUT_ROOT/2-features/expert
DIR=$OUT_ROOT/3-directions/loose
TRIAL=$OUT_ROOT/3-directions/trial
OUT=$OUT_ROOT/4-detectors
mkdir -p "$OUT/logs"
EXTRA=()
if [[ -n "${LIMIT:-}" ]]; then EXTRA+=(--limit "$LIMIT"); fi

train() {  # name, store, then train_classic's constraint arguments
  local name=$1 store=$2; shift 2
  local log=$OUT/logs/train-$name.log
  if [[ -f $OUT/$name/model.txt ]]; then
    echo "$name exists ($OUT/$name); skipping."
    return
  fi
  echo "Training $name on $store. Log: $log"
  python pipeline/4-detectors/train/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --complete_only \
    --features "$store" \
    --model_dir "$OUT/$name" \
    --num_threads "$NUM_WORKERS" \
    "${EXTRA[@]}" \
    "$@" \
    &> "$log"
  tail -2 "$log"
}

for name in $DETECTORS; do
  case $name in
    unconstrained)
      train unconstrained "$SUMS" \
        --neutralize "$DIR/reencoded.neutralize.txt" ;;
    monotone-features)
      train monotone-features "$SUMS" \
        --neutralize "$DIR/M_full-pre-control.neutralize.txt" \
        --monotone "$DIR/M_full-pre-control.monotone.tsv" ;;
    monotone-sums)
      train monotone-sums "$SUMS" \
        --neutralize "$DIR/M_full-pre.neutralize.txt" \
        --monotone "$DIR/M_full-pre.monotone.tsv" ;;
    additions-only)
      train additions-only "$SUMS" \
        --neutralize "$DIR/M_add-pre.neutralize.txt" \
        --monotone "$DIR/M_add-pre.monotone.tsv" ;;
    expert-set)
      # Gimenez et al.'s expert model: monotone increasing in every one of its 40 features.
      python -c "import json, sys; print(''.join(f'{n}\t1\n' for n in json.load(open(sys.argv[1]))['feature_names']), end='')" \
        "$EXPERT/manifest.json" > "$OUT/expert-set.monotone.tsv"
      train expert-set "$EXPERT" \
        --monotone "$OUT/expert-set.monotone.tsv" ;;
    trial)
      if [[ ! -f $TRIAL/trial.monotone.tsv ]]; then
        echo "trial: no trial table in $TRIAL yet (3-directions/trial/run.sh); skipping."
        continue
      fi
      train trial "$SUMS" \
        --neutralize "$TRIAL/trial.neutralize.txt" \
        --monotone "$TRIAL/trial.monotone.tsv" ;;
    *)
      echo "Unknown detector $name (this step trains: unconstrained monotone-features monotone-sums additions-only" \
        "expert-set trial)." >&2
      exit 1 ;;
  esac
done
echo "Done. Models: $OUT/<name>/"
