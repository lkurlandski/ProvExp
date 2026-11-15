#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=adaptive
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=2-00:00:00
#SBATCH --mem=64G
#
# The adaptive attack: a beam search over the threat model's operations (M_full, `ent` included) against each detector,
# every candidate scored by extracting it (5,000 candidates, checkpoints at 200, 1,000, 2,000; session 63), optionally
# after an escape write outside the threat model (ESCAPES; `none` is the plain search). One search per (detector, file).
# Output: $OUT_ROOT/5-attacks/adaptive/<escape>/ (adaptive.parquet, adaptive.json; rows.parquet with SAVE_ROWS=1).
# Knobs: DETECTORS (registry names reading one feature store), MODELS (registry model set), ESCAPES, QUERIES,
# CHECKPOINTS, NUM_MALWARE (default all), DB, SAVE_ROWS, and PROTOCOL: scaleup (the default; session 67) attacks the
# evaluation set's malware (FILES, default 2-features/files/ts.parquet), each detector on those it detects, with the
# training-goodware donor set DONORS (default tr-donors-1) and thresholds on the validation split; pilot keeps the
# pilot list and its goodware and thresholds on the test split (the identity check). SCALE-UP still open: the model
# set `scaleup` (MODELS) and the time.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DETECTORS="${DETECTORS:-unconstrained monotone-features monotone-sums}"
MODELS="${MODELS:-pilot}"
ESCAPES="${ESCAPES:-none}"
QUERIES="${QUERIES:-5000}"
CHECKPOINTS="${CHECKPOINTS:-200 1000 2000 5000}"
OUT=$OUT_ROOT/5-attacks/adaptive
mkdir -p "$OUT/logs"
EXTRA=()
if [[ -n "${NUM_MALWARE:-}" ]]; then EXTRA+=(--num_malware "$NUM_MALWARE"); fi
PROTOCOL="${PROTOCOL:-scaleup}"
if [[ $PROTOCOL == scaleup ]]; then
  EXTRA+=(--protocol scaleup \
    --pilot_files "${FILES:-$OUT_ROOT/2-features/files/ts.parquet}" \
    --donors "${DONORS:-$OUT_ROOT/2-features/files/tr-donors-1.parquet}")
else
  EXTRA+=(--protocol "$PROTOCOL")
  if [[ -n "${FILES:-}" ]]; then EXTRA+=(--pilot_files "$FILES"); fi
fi
if [[ -n "${DB:-}" ]]; then EXTRA+=(--db "$DB"); fi
if [[ "${SAVE_ROWS:-0}" == 1 ]]; then EXTRA+=(--save_rows); fi
# shellcheck disable=SC2046
read -ra DEFENSES <<< "$(python -m provexp.registry defenses --set "$MODELS" $DETECTORS)"
read -ra SOUND <<< "$(python -m provexp.registry sound $DETECTORS)"

for escape in $ESCAPES; do
  ESCAPE=()
  if [[ $escape != none ]]; then ESCAPE=(--escape "$escape"); fi
  echo "Adaptive search, escape $escape, against $DETECTORS. Log: $OUT/logs/adaptive-$escape.log"
  python pipeline/5-attacks/adaptive/adaptive.py \
    --outdir "$OUT/$escape" \
    "${ESCAPE[@]}" \
    --score real \
    --search beam \
    --queries "$QUERIES" \
    --checkpoints $CHECKPOINTS \
    --beam 3 \
    --draws 2 \
    --patience 3 \
    --seed 0 \
    --threat_model M_full \
    --features "$(python -m provexp.registry features --set "$MODELS" $DETECTORS)" \
    "${DEFENSES[@]}" \
    --sound "${SOUND[@]}" \
    "${EXTRA[@]}" \
    --num_workers "$NUM_WORKERS" \
    &> "$OUT/logs/adaptive-$escape.log"
done
echo "Done. Reports: $OUT/<escape>/adaptive.json"
