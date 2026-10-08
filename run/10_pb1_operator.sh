#!/bin/bash
# The PB1 perturbation operator: which header fields cannot be ablated, and what value each field usually takes.
#
# The sweep tries every header field on 2,000 training files and records which ones break parsing or move the
# layout; the check verifies the resulting protected set on the 2,000 explanation-set files. The typical values are
# what level 3 writes into a field instead of zeros.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/discover_protected_fields.py sweep --split tr --num_samples 2000 --num_workers 16 \
  &> artifacts/logs/protected_fields-sweep.log
OMP_NUM_THREADS=1 python scripts/discover_protected_fields.py check --num_workers 16 \
  &> artifacts/logs/protected_fields-check.log
OMP_NUM_THREADS=1 python scripts/header_typical_values.py --split tr --num_samples 2000 --num_workers 8 \
  &> artifacts/logs/header_typical_values.log
