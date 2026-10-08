#!/bin/bash
# The released per-sample metadata (labels, families, packers) as one parquet; drops the duplicate rows the JSONL has.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

python scripts/build_metadata.py
