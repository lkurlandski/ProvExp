#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=iterated
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48
#SBATCH --time=0-06:00:00
#SBATCH --mem=192G
#
# Iterated adversarial training (protocol item 7, session 67; R18, docs/evidence/r18-trial-competitor.md step 3): the
# adversarially trained detector (4-detectors/adversarial-training, the toolkit's material appended) retrained on
# what our adaptive search finds against it, for two rounds. FOR ACADEMIC SECURITY RESEARCH ONLY: our own search
# against our own detectors, on training malware, to build a defense. The starting point (the adversarially trained
# detector, not the unconstrained one) was confirmed by the user in session 70: the strongest learned competitor, with
# the adversarial-training row beside it showing what the rounds add.
#   round k (1, 2): the beam (5,000 extraction-scored candidates, M_full without `ent`, which stays held out of the
#   loop) against the previous round's detector (round 1: adversarial-training) on 1,000 training malware of
#   2-features/files/tr.parquet (round k takes the list's malware k*1,000-(k+1)*1,000 by name order, so the rounds
#   are disjoint), donors from donor set 0; each detected file's best candidate saved as a feature row (--save_rows);
#   then iterated-k: the unconstrained detector's setup trained with the material and the rows of rounds 1..k
#   appended (label 1).
# Tested in 5-attacks with `ent` (the adaptive search over M_full) and MAB-Malware as held-out attacks; the paper's row
# is iterated-2.
# Inputs: 4-detectors/{adversarial-training,material} (4-detectors/learned), 2-features/sums, 3-directions/loose, and
# the file store (FILE_STORE, which holds the training malware; 2-features/file-store).
# Output: $OUT_ROOT/4-detectors/iterated/round-<k>/ (the search: adaptive.{parquet,json}, rows/<detector>/), and the
# models $OUT_ROOT/4-detectors/iterated-<k>/. A finished search or model is skipped.
# Knobs: ROUNDS (default 2), PER_ROUND (default 1000), QUERIES (default 5000), LIMIT (training files per split;
# smoke tests). Cost (session 67's estimate): ~0.5k CPU-h in all, ~7 h per round on 36 cores, ~30 min per retraining.
# Scale-up (job 1039055, session 85): 3 h 24 min on 72 cores, 282 GiB of 300 GB (230 GiB in round 1), ~45% of the
# cores (each round ends on a long tail). Hence 48 cores (~1.5x the rounds, ~5 h), 7 h, and memory with room.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

ROUNDS="${ROUNDS:-2}"
PER_ROUND="${PER_ROUND:-1000}"
QUERIES="${QUERIES:-5000}"
LISTS=$OUT_ROOT/2-features/files
SUMS=$OUT_ROOT/2-features/sums
DIR=$OUT_ROOT/3-directions/loose
OUT=$OUT_ROOT/4-detectors
IT=$OUT/iterated
mkdir -p "$IT/logs"
LIMIT_ARG=()
if [[ -n "${LIMIT:-}" ]]; then LIMIT_ARG=(--limit "$LIMIT"); fi
# The thirteen operations of M_full without the entry write `ent` (signature cloning), held out of the loop.
OPERATIONS="app sec imp ext shf hgr slk dos hdr chk ren rdb rsg"

previous=adversarial-training
augment=("$OUT/material/sums")
for ((k = 1; k <= ROUNDS; k++)); do
  R=$IT/round-$k
  mkdir -p "$R"
  if [[ ! -f $R/adaptive.json ]]; then
    python -c "import polars as pl, sys; k, n = int(sys.argv[3]), int(sys.argv[4]); \
pl.read_parquet(sys.argv[1]).filter(pl.col('label') == 1).sort('name')[(k - 1) * n:k * n].write_parquet(sys.argv[2])" \
      "$LISTS/tr.parquet" "$R/files.parquet" "$k" "$PER_ROUND"
    echo "Round $k: the beam against $previous on $PER_ROUND training malware. Log: $IT/logs/round-$k.log"
    python pipeline/5-attacks/adaptive/adaptive.py \
      --outdir "$R" \
      --score real \
      --search beam \
      --queries "$QUERIES" \
      --checkpoints 200 1000 2000 "$QUERIES" \
      --beam 3 \
      --draws 2 \
      --patience 3 \
      --seed 0 \
      --threat_model M_full \
      --operations $OPERATIONS \
      --features "$SUMS" \
      --defense "$previous=$OUT/$previous" \
      --protocol scaleup \
      --pilot_files "$R/files.parquet" \
      --donors "$LISTS/tr-donors-0.parquet" \
      --save_rows \
      --num_workers "$NUM_WORKERS" \
      &> "$IT/logs/round-$k.log"
    tail -2 "$IT/logs/round-$k.log"
  else
    echo "Round $k's search exists ($R); skipping."
  fi
  augment+=("$R/rows/$previous")
  name=iterated-$k
  if [[ -f $OUT/$name/model.txt ]]; then
    echo "$name exists; skipping."
  else
    echo "Training $name (the material and rounds 1-$k appended). Log: $IT/logs/train-$name.log"
    python pipeline/4-detectors/train/train_classic.py \
      --learner gbdt \
      --seed 0 \
      --complete_only \
      --features "$SUMS" \
      --model_dir "$OUT/$name" \
      --num_threads "$NUM_WORKERS" \
      --neutralize "$DIR/reencoded.neutralize.txt" \
      --augment "${augment[@]}" \
      "${LIMIT_ARG[@]}" \
      &> "$IT/logs/train-$name.log"
    tail -1 "$IT/logs/train-$name.log"
  fi
  previous=$name
done
echo "Done. Models: $OUT/iterated-{1..$ROUNDS}/"
