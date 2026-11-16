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

Every step has a `run.sh` with the scale-up's defaults (session 68): the evaluation set and donor lists of
`2-features/files`, the model set `scaleup` (`4-detectors/<name>`), thresholds on the validation split, 5,000
extraction-scored candidates, one seed. The long steps are SLURM job arrays (`--array` in their header; `bash` runs
the tasks in turn) and skip what is already done, so resubmitting resumes. The time and memory in the headers are
estimates until the head-node session. The pilot's commands are in `run/` (a historical record: re-run them at tag
`pilot-final`).

**Submitting everything at once:** `bash pipeline/submit.sh` on the cluster's head node submits every step below as
SLURM jobs chained by dependencies (a job starts only when the jobs it reads from finished without error; a failure
cancels what depends on it). A gate after `3-directions/derived` (`3-directions/gate`) stops every detector unless the
derived tables' check is clean (session 70's rule). After a fix, rerun it: finished work is skipped, a job still
queued is reused (`scancel` it first to rerun it), and `SKIP` leaves out steps or job names (finished steps that
recompute, such as `3-directions/derived`). `DRY=1` prints the chain. The job IDs go to `logs/submit-<date>.txt`.

The order (each step's inputs are the outputs above it):

1. `2-features/featurize` (the stores, full splits), `2-features/files` (done: the lists), `2-features/file-store`
   (the attacked files' bytes in one SQLite file beside the lists; optional, it only speeds up loading);
2. `3-directions/derived` (from the training list, checked against the evaluation set), `3-directions/gate`; `1-audit/*` (the catalogue check's edits feed the trial); `3-directions/trial`;
3. `4-detectors/train` (Table 5, the expert set, trial);
4. `4-detectors/adversarial-training` (the material, array), then `4-detectors/learned` (PV, ERDALT, adversarial
   training, the leave-one-out folds; GPUs), then `4-detectors/iterated`;
5. `5-attacks/toolkit`, `5-attacks/adaptive` (arrays), `5-attacks/mab-malware`;
6. `6-results`.

| Step | Python | `run.sh` | Pilot record |
|---|---|---|---|
| `setup/` | `make_fixtures.py`, `check_reference.py`, `compare_outputs.py` | `build_env.sh`, `check.sh`, `identity_check.sh` | run 05 |
| `1-audit/item-checks` | `item_checks.py` | yes (`FILES` required) | runs 90-96, 118 |
| `1-audit/catalogue-checks` | `catalogue_checks.py` (with `--chained`) | yes | runs 103-107, 117, 141-142 |
| `1-audit/population` | `population_clauses.py` | yes (`FILES` required) | run 136 |
| `1-audit/escapes` | `escape_audit.py` | yes | run 137 |
| `1-audit/deviations` | `deviations.py` | yes (`FILES` required) | session 65 (2,000 test files) |
| `1-audit/hand-table` | `structure_witness.py`, `overlay_witness.py`, `signature_witness.py`, `witness_counts.py` (`hand_table.py`: the old Table A0, not in the paper) | yes (`FILES` required) | runs 88, 92, 98, 101 |
| `2-features/featurize` | `featurize.py`, `check_features.py`, `refeaturize_nonpe.py` | yes | runs 01-02, 94, 102 |
| `2-features/files` | `build_metadata.py`, `select_files.py` | yes (the evaluation set: 1,000 malware, 1,000 benign, complete files) | runs 03-04 |
| `2-features/file-store` | `build_store.py` | yes (the evaluation set, the donor sets, the material's training malware) | session 69 |
| `3-directions/derived` | `directions.py`, `compare_tables.py`, `expert_directions.py` | yes (`directions.py`, the check) | runs 97, 102, 140, 142 |
| `3-directions/gate` | `gate.py` | yes (stops the detectors unless the derived check is clean) | session 74 |
| `3-directions/trial` | `trial_probe.py`, `trial_table.py` | yes (the evaluation set, donor set 0's imports) | run 144 |
| `4-detectors/train` | `train_classic.py`, `train_erdalt.py` | yes (Table 5 and the expert set; the learned defenses in `adversarial-training`) | runs 99, 105, 128, 140 |
| `4-detectors/adversarial-training` | `attack_training.py` | yes (the material: array over 10,000 training malware) | runs 122, 125, 133 |
| `4-detectors/learned` | (`train_classic.py`, `train_erdalt.py`, `pv_hole.py`) | yes (PV, ERDALT, adversarial training, leave-one-out) | runs 133, 135 |
| `4-detectors/iterated` | (`adaptive.py --save_rows`, `train_classic.py`) | yes (two rounds) | none (R18 step 3) |
| `4-detectors/price-list` | `price_list.py` | protocol session | run 126 |
| `5-attacks/toolkit` | `toolkit.py` (with `--escape`), `pv_attacks.py` (pilot only) | yes (array: detectors, escapes, folds, R19's donor control) | runs 81, 100, 123-124, 131, 133, 135 |
| `5-attacks/adaptive` | `adaptive.py`, `expert_adaptive.py` | yes (array: escapes x shards, the expert set) | runs 127, 120, 143, 144 |
| `5-attacks/mab-malware` | `mab.py` | yes (ours, the expert set, Zainab et al.'s setting) | runs 139, 144 |
| `6-results` | `scaleup_tables.py`, `coverage.py`, `erdalt_hole.py` (`pv_hole.py` runs in `learned`; `toolkit_split.py`, `trial_audit.py` pilot only) | yes | runs 131-135, 144 |

## Where each result of the paper comes from

Every number, table and example the paper reports comes from the scale-up (one protocol, the same files); pilot runs
are for tests and explorations only. Table numbers are the compiled PDF's (`manuscript/main.aux`).

| Paper | Result | Steps |
|---|---|---|
| §4.3, Table 2 (*The operations of the threat model*) | the operations; which the toolkit attacks use | none (definitions) |
| §4.4 | the population's share of files, by clause; closure (0 edits leave it) | `1-audit/population`, `1-audit/catalogue-checks` |
| §4.3-4.4 | the cost of a declaration (detection with an operation dropped) | `4-detectors/price-list` |
| §5.1 | the edit counts of the checks (sound, exact) | `1-audit/catalogue-checks`, `1-audit/item-checks` |
| §5.2, Table 3 (*The eight errors of the hand-written table*) | the hand table's errors and the files where a real edit shows each (`witness_counts.json`, by population) | `1-audit/hand-table`, `1-audit/catalogue-checks`, `1-audit/population`, `3-directions/derived` |
| §5.2 | the expert set's directions and its adaptive cell | `3-directions/derived` (`expert_directions.py`), `5-attacks/adaptive` (`expert_adaptive.py`) |
| §5.3, Table 4 (*Defenses learned from the outputs of the toolkit attacks*) | PV, ERDALT, adversarial training: detection and evasion by any attack | `4-detectors/adversarial-training`, `4-detectors/train`, `5-attacks/*`, `6-results` |
| §5.3 | the lowerable features the toolkit's outputs lowered, by source; PV's hole | `6-results` (`coverage.py`, `pv_hole.py`) |
| §5.3 (with the scale-up) | the trial detector: evasions, and the features carrying them | `3-directions/trial`, `4-detectors/train`, `5-attacks/*`, `6-results` (`trial_audit.py`) |
| §5.4, Table 5 (*Detectors for the full threat model ... and for additions only*) | detection at 1% and 0.1% FPR; evasion by any attack; the price of soundness; where the guarantee holds | `4-detectors/train`, `5-attacks/*` (escapes included), `1-audit/population`, `6-results` |
| Appendix D (deviations table, proposed in session 65) | our deviations from EMBER v3 and the parser heuristics left as they are, with the files each applies to | `1-audit/deviations`, `1-audit/population` |
| Appendix D, Table 8 (*EMBER's features by the readout forms*) | the readout forms | none (the extractor's code) |
| Appendix D, Table 9 (*Side effects computed by Proposition 1*) | exact, declined and wrong edits, inside and outside the population; random in-place writes | `1-audit/catalogue-checks`, `1-audit/item-checks` |
| Appendix D, Table 10 (*Leave-one-out over the toolkit attacks*) | each fold's detection and the held-out attack's evasions | `4-detectors/adversarial-training`, `4-detectors/train`, `5-attacks/toolkit` |
| Appendix D, Table 11 (*Malware evaded by each attack, per detector*) | evasion per attack | `5-attacks/*`, `6-results` (`toolkit_split.py`) |
| Appendix D | MAB-Malware against Zainab et al.'s setting (0.1% FPR, no byte cap) | `5-attacks/mab-malware` |
| Appendix D | combined edits exact when the item table is carried forward | `1-audit/catalogue-checks` (`--chained`: three added sections, then an append; `chains.json`) |
