#!/bin/bash
# The struct trigger's fields and values, chosen from training-data statistics alone (never with an explainer, so
# that scoring explainers against the trigger is not circular). About 8 minutes.
#
# Writes src/provexp/featuresets/ember2024/trigger_struct.json, which IS tracked in git: it is part of the
# experiment's definition, not an artifact.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

OMP_NUM_THREADS=1 python scripts/trigger_select.py --num_samples 4000 --num_fields 3 --num_workers 8 \
  &> artifacts/logs/trigger_select.log
