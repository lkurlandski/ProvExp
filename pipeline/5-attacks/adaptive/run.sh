#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=adaptive
#SBATCH --output=./logs/%x_%A_%a.out
#SBATCH --array=0-80
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=1-00:00:00
#SBATCH --mem=64G
#
# The adaptive attack: a beam search over the threat model's operations (M_full, `ent` included) against each detector,
# every candidate scored by extracting it (5,000 candidates, checkpoints at 200, 1,000, 2,000; session 63), optionally
# after an escape write outside the threat model (ESCAPES; `none` is the plain search). One search per (detector, file).
# FOR ACADEMIC SECURITY RESEARCH ONLY: our own search against our own detectors, to evaluate defenses.
# The plain search attacks DETECTORS (every detector of Tables 4 and 5 on the sums store); each escape attacks
# ESCAPE_DETECTORS (R7: the unconstrained and the two monotone detectors).
# A job array: one task per (escape, shard), escapes in the order of ESCAPES, SHARDS shards each (shard k attacks every
# SHARDS-th malware from the k-th), then one task for the expert set's search (expert_adaptive.py: renames and the DOS
# stub, §5.2; EXPERT=0 leaves it out); 4 x 20 + 1 = 81 tasks with the defaults (keep --array=0-<tasks-1>; a task
# past the list exits; `bash` runs them in turn). A shard whose adaptive.json exists is skipped. With SHARDS=1 the output is
# not split (the identity check).
# Output: $OUT_ROOT/5-attacks/adaptive/<escape>/shard-<k>/ (adaptive.parquet, adaptive.json; rows/ with SAVE_ROWS=1),
# or <escape>/ itself with SHARDS=1; 6-results concatenates the shards. The expert set: $OUT_ROOT/5-attacks/adaptive/expert/.
# Knobs: DETECTORS, ESCAPE_DETECTORS, MODELS (registry model set, default scaleup: 4-detectors/<name>), ESCAPES
# (default "none cert_entry debug_entry image_size"), SHARDS (default 20), QUERIES, CHECKPOINTS, NUM_MALWARE (default
# all), DB, SAVE_ROWS, and PROTOCOL: scaleup (the default; session 67) attacks the evaluation set's malware (FILES,
# default 2-features/files/ts.parquet), each detector on those it detects, with the training-goodware donor set DONORS
# (default tr-donors-1) and thresholds on the validation split; pilot keeps the pilot list and its goodware and
# thresholds on the test split (the identity check, with MODELS=pilot).
# Cost (session 67, from the pilot's timings): ~8-11 CPU-h per detected malware over all detectors, ~7-9k CPU-h in
# all; a plain-search shard ~10-12 h on 36 cores, an escape shard ~4 h. Session 69 made a candidate ~3x cheaper
# (~0.32 -> ~0.10 s: no unused prediction, faster strings), so about a third of that: ~2.5-3k CPU-h, a plain-search
# shard ~3.5-4 h, an escape shard ~1.5 h; with 2-features/file-store, loading takes seconds instead of ~25 min.
# SCALE-UP TO CONFIRM: time and memory.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DETECTORS="${DETECTORS:-unconstrained monotone-features monotone-sums additions-only adversarial-training pv erdalt trial iterated-2}"
ESCAPE_DETECTORS="${ESCAPE_DETECTORS:-unconstrained monotone-features monotone-sums}"
MODELS="${MODELS:-scaleup}"
ESCAPES="${ESCAPES:-none cert_entry debug_entry image_size}"
SHARDS="${SHARDS:-20}"
QUERIES="${QUERIES:-5000}"
CHECKPOINTS="${CHECKPOINTS:-200 1000 2000 5000}"
OUT=$OUT_ROOT/5-attacks/adaptive
mkdir -p "$OUT/logs"
PROTO=()  # the files, donors and thresholds (both searches)
PROTOCOL="${PROTOCOL:-scaleup}"
if [[ $PROTOCOL == scaleup ]]; then
  PROTO+=(--protocol scaleup \
    --pilot_files "${FILES:-$OUT_ROOT/2-features/files/ts.parquet}" \
    --donors "${DONORS:-$OUT_ROOT/2-features/files/tr-donors-1.parquet}")
else
  PROTO+=(--protocol "$PROTOCOL")
  if [[ -n "${FILES:-}" ]]; then PROTO+=(--pilot_files "$FILES"); fi
fi
if [[ -n "${DB:-}" ]]; then PROTO+=(--db "$DB"); fi
EXTRA=("${PROTO[@]}")
if [[ -n "${NUM_MALWARE:-}" ]]; then EXTRA+=(--num_malware "$NUM_MALWARE"); fi
if [[ "${SAVE_ROWS:-0}" == 1 ]]; then EXTRA+=(--save_rows); fi

JOBS=()
for escape in $ESCAPES; do
  for ((k = 0; k < SHARDS; k++)); do JOBS+=("$escape:$k"); done
done
if [[ "${EXPERT:-1}" == 1 ]]; then JOBS+=("expert:0"); fi

for t in $(tasks "${#JOBS[@]}"); do
  if (( t >= ${#JOBS[@]} )); then echo "Task $t: no job (${#JOBS[@]} jobs)."; continue; fi
  escape=${JOBS[$t]%%:*}; k=${JOBS[$t]#*:}
  if [[ $escape == expert ]]; then
    if [[ -f $OUT/expert/expert_adaptive.json ]]; then echo "$OUT/expert exists; skipping."; continue; fi
    echo "The expert set's search. Log: $OUT/logs/expert.log"
    python pipeline/5-attacks/adaptive/expert_adaptive.py \
      --features "$(python -m provexp.registry features --set "$MODELS" expert-set)" \
      --model "$(python -m provexp.registry defenses --set "$MODELS" expert-set | cut -d= -f2)" \
      --outdir "$OUT/expert" \
      "${PROTO[@]}" \
      &> "$OUT/logs/expert.log"
    continue
  fi
  ESCAPE=()
  detectors=$DETECTORS
  if [[ $escape != none ]]; then ESCAPE=(--escape "$escape"); detectors=$ESCAPE_DETECTORS; fi
  dir=$OUT/$escape; log=$OUT/logs/adaptive-$escape.log
  if (( SHARDS > 1 )); then dir=$OUT/$escape/shard-$k; log=$OUT/logs/adaptive-$escape-$k.log; fi
  if [[ -f $dir/adaptive.json ]]; then echo "$dir exists; skipping."; continue; fi
  # shellcheck disable=SC2086
  read -ra DEFENSES <<< "$(python -m provexp.registry defenses --set "$MODELS" $detectors)"
  # shellcheck disable=SC2086
  read -ra SOUND <<< "$(python -m provexp.registry sound $detectors)"
  echo "Adaptive search, escape $escape, shard $k of $SHARDS, against $detectors. Log: $log"
  # shellcheck disable=SC2086
  python pipeline/5-attacks/adaptive/adaptive.py \
    --outdir "$dir" \
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
    --features "$(python -m provexp.registry features --set "$MODELS" $detectors)" \
    "${DEFENSES[@]}" \
    --sound "${SOUND[@]}" \
    "${EXTRA[@]}" \
    --shard "$k" \
    --num_shards "$SHARDS" \
    --num_workers "$NUM_WORKERS" \
    &> "$log"
done
echo "Done. Reports: $OUT/<escape>/[shard-<k>/]adaptive.json"
