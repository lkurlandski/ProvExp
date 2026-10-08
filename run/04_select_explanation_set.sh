#!/bin/bash
# The 2,000-file explanation set: 1,000 per label from the test split, TLSH-deduplicated at threshold 30,
# at most 10 files per malware family.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

python scripts/select_explanation_set.py --split ts --num_samples 2000 --threshold 30 --max_per_family 10 --seed 0
