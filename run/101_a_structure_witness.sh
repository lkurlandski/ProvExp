#!/bin/bash
# G3 witnesses for the remaining class-1 cases (docs/item-layer-design.md, "Anticipated disagreements" and "structures
# past the end of the file"; the signature case is run 98): an edit per case on every file it applies to, re-extracted.
#   entry     add an executable section (sec) to a file whose entry point lies in no section and has no executable one
#   rich_ext  extend the DOS stub (ext) of a file without a Rich header; a donor's Rich header written into the gap only
#   rich_hdr  "Rich" and a key written into TimeDateStamp / PointerToSymbolTable (hdr) of a file without a Rich header
#   exports   append up to an export directory past the end and complete it with one named export (app)
#   relocs    the same for a relocation directory past the end, one block (app)
# Step 1 runs every case on the pilot files; step 2 runs the two past-the-end cases on the 2,000-file set (no pilot
# file has its exports past the end).
# Hypothesis: entry moves entry_name_hash on the 8 pilot files with no executable section; rich_ext creates a Rich
# header on all 39 pilot files without one; rich_hdr does so only where the PE header starts far enough past 0x90 for
# pefile to read a pair before the marker; relocs gives has_relocs 0 -> 1 on both pilot files; exports adds an export
# wherever the directory lies past the end.
#
# Estimate: smoke tests on the pilot took ~6.5 min (rich_hdr + relocs) and ~6.5 min (entry + rich_ext, one donor):
# ~15 min for step 1 with three donors; step 2 reads and parses all 2,000 files twice, ~30-40 min.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Step 1/2: every case on the pilot files. Log: artifacts/logs/a_structure_witness.log"
python scripts/a_structure_witness.py \
  --outdir artifacts/experiments/a_structure_witness \
  &> artifacts/logs/a_structure_witness.log

echo "Step 2/2: exports and relocations past the end on the 2,000-file set. Log: artifacts/logs/a_structure_witness_2000.log"
python scripts/a_structure_witness.py \
  --files artifacts/explanation_set/ts.parquet \
  --cases exports relocs \
  --outdir artifacts/experiments/a_structure_witness_2000 \
  &> artifacts/logs/a_structure_witness_2000.log

echo "Done. Reports: artifacts/experiments/a_structure_witness{,_2000}/report.json"
