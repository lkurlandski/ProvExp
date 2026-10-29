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
# Step 1 ran 2026-10-29 with the script's first, serial version (same arguments; the script now runs on --workers,
# default 16, reading each file once for all cases): 13.6 min. Result: as hypothesised. entry 8/8 files
# (entry_name_hash_0 1 -> 0, entry_name_hash_2 0 -> 1); rich_ext 39/39 (Rich header created; 3 donors each);
# rich_hdr 8/39 (num_pairs 0 -> 13-93); relocs 2/2 (has_relocs 0 -> 1; appends of 4.5 MB and 31 MB); exports applies to
# no pilot file. Step 2 (first attempt, serial, stopped by the user after ~5 min) was estimated at 60-80 min serially;
# a pilot smoke test of the parallel version took 21 s for two cases.
# Estimate for step 2 with 16 workers: a few minutes (one read and parse per file; extraction only where a case applies).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Step 1/2: every case on the pilot files. Log: artifacts/logs/a_structure_witness.log"
python scripts/a_structure_witness.py \
  --workers 16 \
  --outdir artifacts/experiments/a_structure_witness \
  &> artifacts/logs/a_structure_witness.log

echo "Step 2/2: exports and relocations past the end on the 2,000-file set. Log: artifacts/logs/a_structure_witness_2000.log"
python scripts/a_structure_witness.py \
  --files artifacts/explanation_set/ts.parquet \
  --cases exports relocs \
  --workers 16 \
  --outdir artifacts/experiments/a_structure_witness_2000 \
  &> artifacts/logs/a_structure_witness_2000.log

echo "Done. Reports: artifacts/experiments/a_structure_witness{,_2000}/report.json"
