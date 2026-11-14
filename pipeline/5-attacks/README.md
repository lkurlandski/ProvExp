# 5-attacks: the attacks

- `toolkit/`: Gimenez et al.'s eight toolkit attacks (secml-malware) against each detector (`toolkit.py`; held-out
  folds for leave-one-out), and on the pilot malware for PV's selection (`pv_attacks.py`).
- `adaptive/`: our beam search over the threat model's operations, every candidate scored by extraction (5,000, with
  checkpoints), optionally after an escape write. Output: `5-attacks/adaptive/<escape>/adaptive.{parquet,json}`. The
  expert set's search: `expert_adaptive.py`.
- `mab-malware/`: MAB-Malware (Song et al.), a held-out attack we did not write. Output:
  `5-attacks/mab-malware/{results.parquet,table.json}`.

Paper: Tables 4, 5, 10, 11 ("evaded by any attack" in the body, each attack in Appendix D).
