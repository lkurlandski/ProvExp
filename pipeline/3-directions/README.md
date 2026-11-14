# 3-directions: direction tables

- `derived/`: the derived direction tables (Theorem 1): per threat model, the directions each operation can move each
  feature, from the item tables of the files; `strict` and `loose` (R7's widening: the certificate and debug entries
  writable, their data allowed past the end; the paper's tables). Also the expert set's (`expert_directions.py`).
  Output: `3-directions/{strict,loose}/` (`directions_sums.csv`, `<threat model>.{neutralize.txt,monotone.tsv}`, the
  inputs of `4-detectors/train`). Paper: §5.1-5.2, Table 3. Runtime: ~1 min on the pilot files.
- `trial/`: the competitor's directions, learned by trying the twelve operations on files (`trial_probe.py`) and
  tabulated (`trial_table.py`). Paper: §5.3 (the trial row of Table 5 at the scale-up).
