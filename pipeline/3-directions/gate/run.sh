#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=gate
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=0-00:15:00
#SBATCH --mem=4G
#
# The gate before the detectors (pipeline/submit.sh puts every detector after it): exits with an error unless
# 3-directions/derived's check found the evaluation set covered by the training-file tables, with identical population
# cells and detector input files in both variants. On failure, read $OUT_ROOT/3-directions/check/{strict,loose}.json
# with the user (session 70's rule; the union of both corpora is the fallback).
# Inputs: $OUT_ROOT/3-directions/check/{strict,loose}.json (3-directions/derived). Cost: seconds.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

echo "Reading the derived tables' check."
python pipeline/3-directions/gate/gate.py \
  --reports "$OUT_ROOT"/3-directions/check/{strict,loose}.json
