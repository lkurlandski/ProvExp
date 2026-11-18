#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=trial
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-00:45:00
#SBATCH --mem=200G
#
# The trial competitor's direction table (R18; protocol item 6, session 67): the table a practitioner gets by trying
# the operations on files and looking, instead of deriving it. It learns from the evaluation set itself, which favours
# the competitor: the audit's catalogue edits on its 2,000 files (1-audit/catalogue-checks: every operation, ordinary
# and adversarial parameters, our byte-level writers) and trial_probe.py's stronger trial of the in-place operations on
# the same files (every section renamed, all slack, DOS and header regions at once, zeros and random content), with
# imports added from donor set 0 (tr-donors-0, training goodware). A feature some edit lowered is dropped, one some
# edit raised and none lowered is monotone increasing, one no edit moved is free (trial_table.py).
# 4-detectors/train then trains `trial` on it, and 5-attacks attacks it as every other detector (Table 5's trial row).
# Inputs: 2-features/files/{ts,tr-donors-0}.parquet, $OUT_ROOT/1-audit/catalogue/edits.parquet, 3-directions/loose.
# Output: $OUT_ROOT/3-directions/trial/ (probe.parquet; trial.{neutralize.txt,monotone.tsv}, trial_vs_derived.csv,
# report.json).
# Knobs: FILES (default the evaluation set), NUM_FILES (a seeded sample; smoke tests), EDITS (the catalogue's edits).
# Cost (pilot, run 144: 600 files with 200 donors' imports in ~1 h at 16 workers): ~2,000 files, a few hours on 36
# cores. SCALE-UP TO CONFIRM: time and memory.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

LISTS=$OUT_ROOT/2-features/files
FILES="${FILES:-$LISTS/ts.parquet}"
EDITS="${EDITS:-$OUT_ROOT/1-audit/catalogue/edits.parquet}"
OUT=$OUT_ROOT/3-directions/trial
mkdir -p "$OUT/logs"
if [[ ! -f $EDITS ]]; then echo "The catalogue's edits $EDITS are missing (1-audit/catalogue-checks)." >&2; exit 1; fi

if [[ ! -f $OUT/probe.parquet ]]; then
  echo "The stronger trial on $FILES, imports from donor set 0. Log: $OUT/logs/probe.log"
  python pipeline/3-directions/trial/trial_probe.py \
    --files "$FILES" \
    --num_files "${NUM_FILES:-0}" \
    --donor_list "$LISTS/tr-donors-0.parquet" \
    --out "$OUT/probe.parquet" \
    --workers "$NUM_WORKERS" \
    &> "$OUT/logs/probe.log"
  tail -1 "$OUT/logs/probe.log"
fi

echo "The trial table from the catalogue's edits and the probe. Log: $OUT/logs/table.log"
python pipeline/3-directions/trial/trial_table.py \
  --outdir "$OUT" \
  --directions_dir "$OUT_ROOT/3-directions/loose" \
  --stem M_full-pre-control \
  --edits "$EDITS" \
  --probe "$OUT/probe.parquet" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/table.log"
grep -A3 '"modeled"' "$OUT/logs/table.log" || tail -3 "$OUT/logs/table.log"
echo "Done. Table: $OUT/trial.{neutralize.txt,monotone.tsv}"
