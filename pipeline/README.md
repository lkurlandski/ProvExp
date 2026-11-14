# Pipeline

The scale-up's experiments, one numbered stage per folder, one step per subfolder. Each step has a `run.sh` with a
SLURM header: `sbatch pipeline/<stage>/<step>/run.sh` on a cluster, `bash` locally, always from the repository root
(setup: `SETUP.md`). Outputs go under `artifacts/scaleup/<stage>/`; every step `echo`s what it runs and its log file.

| Stage | What it computes |
|---|---|
| `setup/` | the environment, the system check, the test fixtures, the identity check of a code move |
| `1-audit/` | the extractor's checks: instrumentation, catalogue (sound, closed, exact), population, escapes, hand table |
| `2-features/` | the file lists and the feature stores (EMBER's features, the re-encoding over sums, the expert set) |
| `3-directions/` | the direction tables: derived from the extractor (Theorem 1), and learned by trial |
| `4-detectors/` | the detectors: trained with or without monotone constraints, PV, ERDALT, adversarial training |
| `5-attacks/` | the attacks on them: the toolkit attacks, the adaptive search (with escapes), MAB-Malware |
| `6-results/` | the tables from the stored outputs |

Shared conventions (`common.sh`): the system is detected (`pipeline/systems/`); `NUM_WORKERS` defaults to the system's
cores per node (16 here); `OUT_ROOT` (default `artifacts/scaleup`) moves all outputs; `PYTHONHASHSEED=0`. Detectors and
attacks have plain names, defined once in `src/provexp/registry.py` (`python -m provexp.registry defenses NAME...`
prints the arguments). The Python next to each `run.sh` is a thin command line over `src/provexp/`.

## Status of the steps

`run.sh` exists for the steps the identity check runs (featurize, derived directions, catalogue checks, adaptive,
MAB-Malware) and for setup; their defaults are the scale-up's where it is decided (5,000 extraction-scored
candidates, one seed) and the current pilot inputs where it is not (file lists, model set `pilot`). The other steps
get their `run.sh` in the protocol sessions, with the scale-up's files, budgets and detectors. Their pilot commands
are in `run/` (a historical record: re-run them at tag `pilot-final`).

| Step | Python | `run.sh` | Pilot record |
|---|---|---|---|
| `setup/` | `make_fixtures.py`, `check_reference.py`, `compare_outputs.py` | `build_env.sh`, `check.sh`, `identity_check.sh` | run 05 |
| `1-audit/item-checks` | `item_checks.py` | protocol session | runs 90-96, 118 |
| `1-audit/catalogue-checks` | `catalogue_checks.py` | yes | runs 103-107, 117, 141-142 |
| `1-audit/population` | `population_clauses.py` | protocol session | run 136 |
| `1-audit/escapes` | `escape_audit.py` | protocol session | run 137 |
| `1-audit/hand-table` | `hand_table.py`, `overlay_witness.py`, `signature_witness.py`, `structure_witness.py` | protocol session | runs 88, 92, 98, 101 |
| `2-features/featurize` | `featurize.py`, `check_features.py`, `refeaturize_nonpe.py` | yes | runs 01-02, 94, 102 |
| `2-features/files` | `build_metadata.py`, `select_files.py` | protocol session | runs 03-04 |
| `3-directions/derived` | `directions.py`, `expert_directions.py` | yes (`directions.py`) | runs 97, 102, 140, 142 |
| `3-directions/trial` | `trial_probe.py`, `trial_table.py` | protocol session | run 144 |
| `4-detectors/train` | `train_classic.py`, `train_erdalt.py` | protocol session | runs 99, 105, 128, 140 |
| `4-detectors/adversarial-training` | `attack_training.py` | protocol session | runs 122, 125, 133 |
| `4-detectors/price-list` | `price_list.py` | protocol session | run 126 |
| `5-attacks/toolkit` | `toolkit.py`, `pv_attacks.py` | protocol session | runs 81, 100, 123-124, 131, 133, 135 |
| `5-attacks/adaptive` | `adaptive.py`, `expert_adaptive.py` | yes (`adaptive.py`) | runs 127, 120, 143, 144 |
| `5-attacks/mab-malware` | `mab.py` | yes | runs 139, 144 |
| `6-results` | `toolkit_split.py`, `coverage.py`, `pv_hole.py`, `erdalt_hole.py`, `trial_audit.py` | protocol session | runs 131-135, 144 |

## Where each result of the paper comes from

Every number, table and example the paper reports comes from the scale-up (one protocol, the same files); pilot runs
are for tests and explorations only. Table numbers are the compiled PDF's (`manuscript/main.aux`).

| Paper | Result | Steps |
|---|---|---|
| §4.3, Table 2 (*The operations of the threat model*) | the operations; which the toolkit attacks use | none (definitions) |
| §4.4 | the population's share of files, by clause; closure (0 edits leave it) | `1-audit/population`, `1-audit/catalogue-checks` |
| §4.3-4.4 | the cost of a declaration (detection with an operation dropped) | `4-detectors/price-list` |
| §5.1 | the edit counts of the checks (sound, exact) | `1-audit/catalogue-checks`, `1-audit/item-checks` |
| §5.2, Table 3 (*The eight errors of the hand-written table*) | the hand table's errors and the files where a real edit shows each | `1-audit/hand-table`, `3-directions/derived` |
| §5.2 | the expert set's directions and its adaptive cell | `3-directions/derived` (`expert_directions.py`), `5-attacks/adaptive` (`expert_adaptive.py`) |
| §5.3, Table 4 (*Defenses learned from the outputs of the toolkit attacks*) | PV, ERDALT, adversarial training: detection and evasion by any attack | `4-detectors/adversarial-training`, `4-detectors/train`, `5-attacks/*`, `6-results` |
| §5.3 | the lowerable features the toolkit's outputs lowered, by source; PV's hole | `6-results` (`coverage.py`, `pv_hole.py`) |
| §5.3 (with the scale-up) | the trial detector: evasions, and the features carrying them | `3-directions/trial`, `4-detectors/train`, `5-attacks/*`, `6-results` (`trial_audit.py`) |
| §5.4, Table 5 (*Detectors for the full threat model ... and for additions only*) | detection at 1% and 0.1% FPR; evasion by any attack; the price of soundness; where the guarantee holds | `4-detectors/train`, `5-attacks/*` (escapes included), `1-audit/population`, `6-results` |
| Appendix D, Table 8 (*EMBER's features by the readout forms*) | the readout forms | none (the extractor's code) |
| Appendix D, Table 9 (*Side effects computed by Proposition 1*) | exact, declined and wrong edits, inside and outside the population; random in-place writes | `1-audit/catalogue-checks`, `1-audit/item-checks` |
| Appendix D, Table 10 (*Leave-one-out over the toolkit attacks*) | each fold's detection and the held-out attack's evasions | `4-detectors/adversarial-training`, `4-detectors/train`, `5-attacks/toolkit` |
| Appendix D, Table 11 (*Malware evaded by each attack, per detector*) | evasion per attack | `5-attacks/*`, `6-results` (`toolkit_split.py`) |
| Appendix D | MAB-Malware against Zainab et al.'s setting (0.1% FPR, no byte cap) | `5-attacks/mab-malware` |
| Appendix D | combined edits exact when the item table is carried forward | `1-audit/catalogue-checks` (to add: chained edits; the A' code that checked it on the pilot was removed) |
