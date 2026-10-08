#!/bin/bash
# The test fixtures in tests/data/ (real binaries, gitignored): a couple per category from a few shards.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

python scripts/make_fixtures.py --per_category 2 --num_shards 8
