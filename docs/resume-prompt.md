# Resume: the head-node session, then the scale-up's launch

Written at the end of session 68 (2026-11-15). This prompt is self-contained: what the project is, where things stand,
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

- **The protocol is decided** (session 67; PLAN.md step 3 (g), items 1-9): an evaluation set of 1,000 malware and
  1,000 benign complete test files; every detector on the full training split's complete files; thresholds on the
  validation split; two disjoint donor sets of 100 training goodware (set 0: the defenses' material and the trial's
  imports; set 1: every attack on the evaluation set); the defenses' material once from 10,000 training malware; the
  trial row learning from the evaluation set; iterated adversarial training, 1,000 training malware per round;
  MAB-Malware at ours and at Zainab et al.'s setting; three escapes against three detectors with the adaptive search
  and the toolkit.
- **Every step has its `run.sh`** (session 68), each smoke-tested on a small slice; `pipeline/README.md` lists them in
  the order they run, with each step's inputs and outputs in its header. Long steps are SLURM job arrays and skip what
  is done, so resubmitting resumes: the material (`4-detectors/adversarial-training`, 10 shards), the toolkit attacks
  (21 jobs: one per detector, escape, leave-one-out fold, and R19's donor control), the adaptive search (4 escapes x
  20 shards, plus the expert set's search). Detector names and paths: the registry's `scaleup` set
  (`$OUT_ROOT/4-detectors/<name>`). The reporting duties are in `6-results/scaleup_tables.py` (test TPR at the
  validation thresholds; the share of all evaluation malware still detected after each attack and after any, at 1%
  and 0.1% FPR; R3's margins; R15's gain share), `coverage.py` (R12: the `modeled` class) and `erdalt_hole.py`.
- The file lists exist on this server only: `artifacts/scaleup/2-features/files/` (`ts.parquet`, `tr.parquet`,
  `tr-donors-{0,1}.parquet`, from `artifacts/metadata/ember2024.parquet`).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- Every result the paper reports comes from the scale-up (one protocol, the same files); pilot runs are for tests and
  explorations only. One seed (0) until the methodology is final.
- Explain plainly; state a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority. Never edit a `run.sh` while it runs.
- After moving or refactoring code, `pipeline/setup/identity_check.sh` must find no difference (~15 min; it now
  starts from an empty output directory).
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. This session: on the cluster's head node (sporc first)

With the user at the cluster (they run what needs their account; suggest `! <command>` for interactive steps):

1. **Two questions for the user first** (raised at the end of session 68, not yet answered):
   (a) *The derived table's corpus.* `3-directions/derived` takes the term vocabulary and the in-place operations'
   changes from the item tables of a file list, still the pilot's 100 files by default. Which corpus at the scale-up:
   the evaluation set (as the audit and the trial do; the trial learns from it too, so the comparison is even), or
   training files (the defender's data only)? Set `FILES` in that `run.sh`'s default accordingly.
   (b) *Iterated adversarial training's starting point* (chosen by Claude in session 68, open to veto): round 1
   attacks the adversarially trained detector (the toolkit's material already in it), so the row is the strongest
   learned baseline plus two rounds of the beam; the alternative starts from the unconstrained detector.
2. **Setup** (`SETUP.md`): clone, `pipeline/setup/build_env.sh`, the `artifacts` symlink, the dataset location;
   copy the file lists and the metadata (`artifacts/scaleup/2-features/files/`, `artifacts/metadata/`) from this
   server, and the reference files the steps read (`pipeline/setup/reference/` is in git).
3. **`pipeline/setup/check.sh`** must pass (bit-exact featurization on 32 files, the tests).
4. **The "TO CONFIRM" values** in `pipeline/systems/sporc.sh` (cores per node, large storage, walltime, Python 3.14
   through uv) and in each `run.sh`'s header: time, memory, `--gpus-per-node` (`4-detectors/learned`: ERDALT one per
   GPU, each loading the ~25-30 GB store), array sizes. The estimates in the headers come from the pilot's timings.
5. **Featurization:** `2-features/featurize/run.sh` with `EXTRACTORS="sums expert"` (the plain `ember2024` store is
   only for `check_features.py`'s comparison with the released vectors) on the full splits; one node, ~0.1-0.2 s per
   file and extractor (~2.3M files). A job-array version would need a step that creates the store before the tasks
   (not built; probably not needed).
6. Then the steps in `pipeline/README.md`'s order, submitted by the user, with SLURM dependencies where useful.

## 5. Noted for later (not this session unless it becomes necessary)

- After the debug-entry escape, `gamma_api` (which rebuilds the file through LIEF) no longer evaded the unconstrained
  smoke detector on 3 files that it evades unescaped (it also added fewer bytes): LIEF seems to handle the escaped
  debug entry differently. Worth a look when the escape rows of the toolkit are read (it weakens the toolkit after an
  escape, not the guarantee).
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact; at
  scale every detector detects hundreds).
- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only (not in the scale-up's
  protocol; `scaleup_tables.py` gives the per-attack table).
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split), an
  effect of the family cap; worth one sentence in Setup if a reader could ask.

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-<date>-s69.md`, with its line in `docs/README.md`.
