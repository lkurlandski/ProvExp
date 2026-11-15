# 3-directions: direction tables

- `derived/`: the derived direction tables (Theorem 1): per threat model, the directions each operation can move each
  feature, from the item tables of the files; `strict` and `loose` (R7's widening: the certificate and debug entries
  writable, their data allowed past the end; the paper's tables). Also the expert set's (`expert_directions.py`).
  Built from training files (`2-features/files/tr.parquet`), then rebuilt from the evaluation set as a check
  (`compare_tables.py`: does the evaluation set show a move the table lacks?).
  Output: `3-directions/{strict,loose}/` (`directions_sums.csv`, `<threat model>.{neutralize.txt,monotone.tsv}`, the
  inputs of `4-detectors/train`) and `3-directions/check/` (the check's tables and reports). Paper: §5.1-5.2,
  Table 3. Runtime: ~5 CPU-s per file and variant (~2 h on 36 cores at the scale-up).
- `trial/`: the competitor's directions, learned by trying the twelve operations on files (`trial_probe.py`) and
  tabulated (`trial_table.py`). Paper: §5.3 (the trial row of Table 5 at the scale-up).
