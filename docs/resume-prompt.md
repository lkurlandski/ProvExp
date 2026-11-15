# Resume: the scale-up's remaining run.sh steps, from the protocol decided in session 67

Written at the end of session 67 (2026-11-15). This prompt is self-contained: what the project is, where things stand,
the rules that apply, and what this session does. Files are named for detail, but only `CLAUDE.md` (loaded
automatically) needs reading first.

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few totals
(readouts). From the instrumented extractor we compute what an attacker's edits do to the features: exactly for one
edit (Proposition 1), as sound directions for a whole threat model (Theorem 1: for each feature, whether some edit
can raise it, lower it, or neither), and from those, monotone detectors no edit in the threat model can evade
(Corollary 1). PE malware on EMBER2024 is the instance. The paper (`manuscript/*.tex`, ACM CCS format) is drafted on
pilot-scale results (100 pilot files, one seed). The **scale-up** (PLAN.md step 3) on the user's SLURM clusters
replaces every number in the paper.

## 2. Where things stand

- **Code layout (session 64):** library code in `src/provexp/`, the experiments in `pipeline/` (numbered stages, one
  step per folder, a `run.sh` with a SLURM header next to a thin Python command line; `pipeline/README.md` maps each
  paper result to its step). The extractor audit is finished and its two fixes are in (sessions 65-66).
- **The protocol is decided (session 67, with the user; PLAN.md step 3 (g), items 1-9).** In short:
  1. *Evaluation set:* 1,000 malware and 1,000 benign test files below 4 MB (near-duplicates removed, at most 10 per
     family): `artifacts/scaleup/2-features/files/ts.parquet`. Every attack runs on its malware (each detector on the
     ones it detects); every `1-audit` step runs on all of it (their `FILES` default to it). Estimated ~7-9k CPU-h for
     the attacks (the adaptive search at 5,000 extraction-scored candidates dominates).
  2. *One training set:* every detector trains on the full training split's complete files (~1.76M), each on its
     patched store (`train_classic.py`/`train_erdalt.py --complete_only`; the pilot's trainers never dropped
     truncated files).
  3. *Thresholds* (1% and 0.1% FPR) on the validation split's goodware (the trainers now write
     `vl_predictions.parquet`; `provexp.detectors.model_threshold`, `detection_at`).
  4. *Donors:* two disjoint sets of 100 training goodware (`tr-donors-0`: the defenses' material and the trial's
     imports; `tr-donors-1`: every attack on the evaluation set; R19's donor-overlap control swaps them). The
     separation matters: the pilot's ERDALT fell (24/29) when gamma_api's donors changed.
  5. *The learned defenses' material, once:* the eight toolkit attacks (seed per file, low budget, donor set 0) on the
     10,000 training malware of `tr.parquet`, against the scale-up's undefended detector (so after it is trained);
     ~80k outputs, ~700-900 CPU-h; saved as feature rows for **every** store the defenses read and as compressed
     adversarial binaries (~30-60 GB). PV, ERDALT, adversarial training and the leave-one-out folds all read it.
  6. *Trial row:* the trial learns from the evaluation set (the audit's catalogue edits plus `trial_probe.py` on all
     2,000, imports from donor set 0).
  7. *Iterated adversarial training:* two rounds of the beam (5,000 candidates, `ent` held out) on 1,000 training
     malware per round.
  8. *MAB-Malware:* every detector at our setting; plus Zainab et al.'s (0.1% FPR, no byte cap) on the unconstrained
     detector.
  9. *Escapes:* the three writes against the unconstrained and the two monotone detectors, each followed by the
     adaptive search **and the eight toolkit attacks**; the escape audit on every population file of the evaluation
     set.
- **Implemented in session 67:** the lists (`pipeline/2-features/files/run.sh`, `select_files.py --complete_only
  --donor_sets`); the trainers' flag and validation predictions; `provexp.data.files.load_attacked` and the attacks'
  `--protocol {pilot,scaleup} --donors` (adaptive, toolkit, MAB-Malware, expert adaptive; `price_list.py table
  --protocol`); the adaptive and MAB-Malware `run.sh` default to `PROTOCOL=scaleup`; the identity check passes the
  pilot's files and protocol explicitly and still matches run 146 (see `docs/status.md`).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- Every result the paper reports comes from the scale-up (one protocol, the same files); pilot runs are for tests and
  explorations only. One seed (0) until the methodology is final.
- Explain plainly; state a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority. Never edit a `run.sh` while it runs.
- After moving or refactoring code, `pipeline/setup/identity_check.sh` must find no difference (~15 min; it reads
  `artifacts/refactor-baseline/old`).
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. This session: the remaining `run.sh` steps

Implement, smoke-test on a small slice, and commit, one step at a time (the list is in PLAN.md step 3 (g), last
sentences). Ask the user only where a choice is genuinely theirs; the protocol itself is decided.

1. **The registry's `scaleup` model set** (`src/provexp/registry.py`; `artifacts/scaleup/4-detectors/<name>`), so the
   attack `run.sh` can default to `MODELS=scaleup`.
2. **`4-detectors/train/run.sh`:** every detector of Tables 4-5 on the full training split, `--complete_only`, each
   from its patched store and direction table (the stores come from `2-features/featurize` on full splits; note the
   job-array featurization needs a step that creates the store first, PLAN.md).
3. **`4-detectors/adversarial-training/run.sh`:** the defenses' material (item 5): `attack_training.py` on
   `tr.parquet`'s malware with donor set 0, rows for every store, compressed binaries kept; then PV, ERDALT and
   adversarial training from it, and the leave-one-out folds (Table 10).
4. **`5-attacks/toolkit/run.sh`:** the eight attacks per detector under `--protocol scaleup`; `toolkit.py` gains
   `--escape` (the escape write first, detection and evasion counted from the unescaped original, as `adaptive.py`).
5. **Iterated adversarial training** (item 7; `adaptive.py --save_rows` on 1,000 of `tr.parquet` with `--db .../tr`).
6. **The trial row** (item 6: `3-directions/trial/run.sh`, trial_probe on the evaluation set with donor set 0's
   imports; `trial_probe.py` takes a donor count today, so it needs a donor-list option).
7. **MAB-Malware's second setting** (0.1% FPR, no byte cap, unconstrained only).
8. **`6-results`:** the reporting duties: the share of all attacked malware still detected after each attack at 1% and
   0.1% FPR (files outside the population counted; body "after any attack", appendix per attack), §5.3's coverage on
   modeled features only (R12), the monotone detector's split-gain share on features no edit moves (R15), the detected
   malware's margins against the hand table's 1.57-logit maximum drop (R3), test TPR at the validation thresholds.

Then a session on a cluster head node (`SETUP.md`, `check.sh`, the "TO CONFIRM" values; sporc first), which also sets
each `run.sh`'s SLURM time and memory (the full training split's dense store is ~25-30 GB per extractor).

## 5. Noted for later (not this session unless it becomes necessary)

- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py` still uses the pilot loader only (not part of the scale-up's protocol so far).
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split), an
  effect of the family cap (the old selection showed it too); worth one sentence in Setup if a reader could ask.

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-<date>-s68.md`, with its line in `docs/README.md`.
