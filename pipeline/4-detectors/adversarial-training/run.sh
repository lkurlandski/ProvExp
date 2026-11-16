#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=defenses-material
#SBATCH --output=./logs/%x_%A_%a.out
#SBATCH --array=0-9
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=0-12:00:00
#SBATCH --mem=100G
#
# The learned defenses' material, once (protocol item 5, session 67). FOR ACADEMIC SECURITY RESEARCH ONLY: published
# secml-malware attacks against our own undefended detector, on our own training samples, to build the defenses the
# sound detectors are compared with. The eight toolkit attacks (low budget, a seed per (attack, file)) on the 10,000
# training malware of 2-features/files/tr.parquet, detected or not, donors from donor set 0 (tr-donors-0), against the
# scale-up's undefended detector (4-detectors/unconstrained, so 4-detectors/train runs first). Every valid output is
# saved as a feature row for each store the defenses read (ROWS) and as a compressed binary (re-featurize them when an
# extractor changes; do not re-attack). PV, ERDALT, adversarial training and the leave-one-out folds all learn from it
# (4-detectors/learned).
# A job array: task k attacks every SHARDS-th malware from the k-th (`sbatch` runs SHARDS tasks; `bash` runs them in
# turn); a finished shard is skipped, so resubmitting resumes. 4-detectors/learned merges the shards (and refuses
# until every one is complete).
# Output: $OUT_ROOT/4-detectors/material/ (<store>/{X.npy,files.parquet,report.json} after the merge;
# shards/<k>/; binaries/<attack>/<name>.zst; logs/).
# Cost (pilot, run 133: 3,183 runs in 41 min at 16 workers, plus one 45-min stall): ~80k attack runs, ~700-900 CPU-h,
# ~2.5 h per shard of 1,000 files on 36 cores; the binaries ~30-60 GB.
# The two GAMMA attacks are not run on files LIEF cannot rebuild (provexp.attacks.lief_check; shards/<k>/lief_check.parquet).
# Knobs: SHARDS (default 10; keep it equal to the --array size), FILES, DONORS, DB, ROWS (stores, default the sums and
# expert stores), NUM_MALWARE (smoke tests: only the list's first N), REPAIR (a file of lost tasks, `attack name` per
# line: mend complete shards instead, re-running the lost tasks LIEF can rebuild; session 76:
# REPAIR=$OUT_ROOT/4-detectors/material/lost.txt). Measured (session 76, 36 cores, 100G): ~2 h per shard.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

SHARDS="${SHARDS:-10}"
LISTS=$OUT_ROOT/2-features/files
FILES="${FILES:-$LISTS/tr.parquet}"
DONORS="${DONORS:-$LISTS/tr-donors-0.parquet}"
DB="${DB:-${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}/tr}"
SUMS=$OUT_ROOT/2-features/sums
ROWS="${ROWS:-$SUMS $OUT_ROOT/2-features/expert}"
MODEL=$OUT_ROOT/4-detectors/unconstrained
OUT=$OUT_ROOT/4-detectors/material
mkdir -p "$OUT/logs"
EXTRA=()
if [[ -n "${NUM_MALWARE:-}" ]]; then EXTRA+=(--num_malware "$NUM_MALWARE"); fi
if [[ -n "${REPAIR:-}" ]]; then EXTRA+=(--repair "$REPAIR"); fi
if [[ ! -f $MODEL/model.txt ]]; then echo "The undefended detector $MODEL is missing (4-detectors/train)." >&2; exit 1; fi

for k in $(tasks "$SHARDS"); do
  LOG=$OUT/logs/shard-$k${REPAIR:+-repair}.log
  echo "Shard $k of $SHARDS: the eight toolkit attacks on its training malware${REPAIR:+ (repair from $REPAIR)}. Log: $LOG"
  # shellcheck disable=SC2086
  python pipeline/4-detectors/adversarial-training/attack_training.py \
    --outdir "$OUT" \
    --files "$FILES" \
    --donors "$DONORS" \
    --db "$DB" \
    --features "$SUMS" \
    --model "$MODEL" \
    --rows $ROWS \
    --keep_binaries \
    --shard "$k" \
    --num_shards "$SHARDS" \
    --seed 0 \
    "${EXTRA[@]}" \
    --num_workers "$NUM_WORKERS" \
    &> "$LOG"
  tail -9 "$LOG"
done

echo "Done. Shards: $OUT/shards/; 4-detectors/learned merges them once all are complete."
