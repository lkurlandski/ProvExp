# 4-detectors: the detectors

Plain names in `src/provexp/registry.py`: `unconstrained`, `monotone-features`, `monotone-sums`, `additions-only`,
`adversarial-training`, `pv`, `erdalt`, `expert-set`, `trial`.

- `train/`: GBDTs (`train_classic.py`; monotone constraints and dropped features from a direction table) and ERDALT
  (`train_erdalt.py`, Gimenez et al.'s schedule).
- `adversarial-training/`: the toolkit attacks on training malware (`attack_training.py`), the outputs PV, ERDALT and
  adversarial training learn from; iterated adversarial training adds the adaptive search's rows (`adaptive.py
  --save_rows`). Paper: §5.3, Table 4; Appendix D, Table 10.
- `price-list/`: detectors with one operation's declaration left out: the price of soundness per operation. Paper:
  §5.4.
