# 4-detectors: the detectors

Plain names in `src/provexp/registry.py`: `unconstrained`, `monotone-features`, `monotone-sums`, `additions-only`,
`adversarial-training`, `pv`, `erdalt`, `expert-set`, `trial`, `iterated-{1,2}`, `{pv,erdalt}-loo-<attack>`; the
scale-up's models in `4-detectors/<name>/`.

- `train/`: the trainers, GBDTs (`train_classic.py`; monotone constraints and dropped features from a direction table)
  and ERDALT (`train_erdalt.py`, Gimenez et al.'s schedule); `run.sh` trains Table 5's detectors, the expert set and
  trial on the full training split's complete files.
- `adversarial-training/`: the learned defenses' material, once: the eight toolkit attacks on the 10,000 training
  malware (`attack_training.py`, a job array), saved as feature rows per store and as compressed binaries.
- `learned/`: PV, ERDALT, adversarial training and the leave-one-out folds, all from that material. Paper: §5.3,
  Table 4; Appendix D, Table 10.
- `iterated/`: iterated adversarial training, two rounds of the adaptive search (`ent` held out) on training malware
  (`adaptive.py --save_rows`), each followed by retraining. Paper: Table 4.
- `price-list/`: detectors with one operation's declaration left out: the price of soundness per operation. Paper:
  §5.4.
- `cost-split/`: where the monotone detector's cost lies: unconstrained detectors with the two-sided sums dropped and
  on the fixed sums alone, and the monotone detector with more boosting rounds and LightGBM's other constraint
  methods, each with its fit on the training split, the fixed sums' share of split gain and a structural check of the
  constraints. Paper: §5.4.
