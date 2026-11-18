#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=toolkit
#SBATCH --output=./logs/%x_%A_%a.out
#SBATCH --array=0-28
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=08:00:00
#SBATCH --mem=64G
#
# Gimenez et al.'s eight toolkit attacks (secml-malware; low budget, a seed per (attack, file)) against the detectors,
# under the scale-up's protocol (session 67): the evaluation set's malware (2-features/files/ts.parquet), each detector
# on those it detects at 1% FPR (threshold on the validation split), donors from donor set 1 (tr-donors-1). FOR
# ACADEMIC SECURITY RESEARCH ONLY: published attacks against our own detectors, to evaluate defenses.
# One job per array task (`sbatch` runs them in parallel; `bash` runs them in turn), in this order:
#   main/<detector>   every detector of DETECTORS (Tables 4, 5 and 11)
#   escape/<escape>   each escape write of ESCAPES first, then the eight attacks, against ESCAPE_DETECTORS (R7;
#                     detection and evasion counted from the unescaped original, as the adaptive search does)
#   loo/<family>-<attack>  the leave-one-out folds (Table 10): the held-out attack against <family>-loo-<attack>,
#                     one job per family of LOO (pv, erdalt; split in session 82 so ERDALT's folds can run apart)
#   donors-0/erdalt   R19's donor-overlap control: ERDALT attacked with donor set 0, the donors of its own material
# 29 jobs with the defaults (keep --array=0-<jobs-1>; a task past the list exits). A job whose table.json exists is
# skipped. 0.1% FPR is read from the same runs in 6-results (the attacks minimize the score; a file evaded at 1% FPR is
# evaded at 0.1%).
# Output: $OUT_ROOT/5-attacks/toolkit/<job>/ (results.parquet, table.json); logs in $OUT_ROOT/5-attacks/toolkit/logs/.
# Knobs: DETECTORS, ESCAPES, ESCAPE_DETECTORS, PARTS (default "main escape loo donors"), LOO (the leave-one-out
# families, default "pv erdalt"), MODELS (registry set, default scaleup), FILES, NUM_MALWARE (smoke tests). Cost (pilot, run 133: ~1,500 runs in ~40 min at 16 workers): ~900
# detected malware x 8 attacks per detector, a few hours per job on 36 cores. Scale-up (job 1046138, session 85): the
# slowest task 4 h 44 min (the debug-entry escape), at most 44 GiB, ~90% of the cores on the main and escape rows;
# the leave-one-out folds attack 5-23 files and use ~5% of 36 cores (submit them apart with fewer cores if rerun).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

DETECTORS="${DETECTORS:-unconstrained monotone-features monotone-sums additions-only adversarial-training pv erdalt trial iterated-2}"
ESCAPES="${ESCAPES:-cert_entry debug_entry image_size}"
ESCAPE_DETECTORS="${ESCAPE_DETECTORS:-unconstrained monotone-features monotone-sums}"
PARTS="${PARTS:-main escape loo donors}"
LOO="${LOO:-pv erdalt}"
MODELS="${MODELS:-scaleup}"
ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
LISTS=$OUT_ROOT/2-features/files
FILES="${FILES:-$LISTS/ts.parquet}"
OUT=$OUT_ROOT/5-attacks/toolkit
mkdir -p "$OUT/logs"
EXTRA=()
if [[ -n "${NUM_MALWARE:-}" ]]; then EXTRA+=(--num_malware "$NUM_MALWARE"); fi
others() { local h=$1 a out=""; for a in $ATTACKS; do [[ $a != "$h" ]] && out="$out $a"; done; echo $out; }

JOBS=()
for part in $PARTS; do
  case $part in
    main) for d in $DETECTORS; do JOBS+=("main/$d"); done ;;
    escape) for e in $ESCAPES; do JOBS+=("escape/$e"); done ;;
    loo) for fam in $LOO; do for h in $ATTACKS; do JOBS+=("loo/$fam-$h"); done; done ;;
    donors) JOBS+=("donors-0/erdalt") ;;
    *) echo "Unknown part $part (main escape loo donors)." >&2; exit 1 ;;
  esac
done
echo "${#JOBS[@]} jobs: ${JOBS[*]}"

attack() {  # job, donor list, attacks, seen, detectors, then extra arguments
  local job=$1 donors=$2 attacks=$3 seen=$4 detectors=$5; shift 5
  local log=$OUT/logs/${job//\//-}.log
  if [[ -f $OUT/$job/table.json ]]; then echo "$job exists; skipping."; return; fi
  echo "Toolkit job $job: $attacks against $detectors. Log: $log"
  local defenses
  # shellcheck disable=SC2086
  read -ra defenses <<< "$(python -m provexp.registry defenses --set "$MODELS" $detectors)"
  # shellcheck disable=SC2086
  python pipeline/5-attacks/toolkit/toolkit.py \
    --outdir "$OUT/$job" \
    --protocol scaleup \
    --pilot_files "$FILES" \
    --donors "$donors" \
    --features "$(python -m provexp.registry features --set "$MODELS" $detectors)" \
    "${defenses[@]}" \
    --attacks $attacks \
    --seen $seen \
    --fpr 0.01 \
    --budget low \
    --seed 0 \
    --seed_per_file \
    "${EXTRA[@]}" \
    "$@" \
    --num_workers "$NUM_WORKERS" \
    &> "$log"
  grep -E "^\S+ +detected" "$log" || tail -3 "$log"
}

for k in $(tasks "${#JOBS[@]}"); do
  if (( k >= ${#JOBS[@]} )); then echo "Task $k: no job (${#JOBS[@]} jobs)."; continue; fi
  job=${JOBS[$k]}
  case $job in
    main/*) attack "$job" "$LISTS/tr-donors-1.parquet" "$ATTACKS" "$ATTACKS" "${job#main/}" ;;
    escape/*) attack "$job" "$LISTS/tr-donors-1.parquet" "$ATTACKS" "$ATTACKS" "$ESCAPE_DETECTORS" \
      --escape "${job#escape/}" ;;
    loo/*)
      fam=${job#loo/}; fam=${fam%%-*}; h=${job#loo/"$fam"-}
      attack "$job" "$LISTS/tr-donors-1.parquet" "$h" "$(others "$h")" "$fam-loo-$h" ;;
    donors-0/*) attack "$job" "$LISTS/tr-donors-0.parquet" "$ATTACKS" "$ATTACKS" erdalt ;;
  esac
done
echo "Done. Tables: $OUT/<job>/table.json"
