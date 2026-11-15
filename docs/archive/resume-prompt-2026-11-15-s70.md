# Resume: two open scale-up questions, on this machine

Written at the end of session 69 (2026-11-15). This prompt is self-contained: what the project is, where things stand,
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

- **The protocol is decided** (session 67; PLAN.md step 3 (g)): an evaluation set of 1,000 malware and 1,000 benign
  complete test files (`artifacts/scaleup/2-features/files/ts.parquet`); every detector on the full training split's
  complete files; thresholds on the validation split; two disjoint donor sets of 100 training goodware (set 0: the
  defenses' material and the trial's imports; set 1: every attack on the evaluation set); the defenses' material once
  from 10,000 training malware; the trial row learning from the evaluation set; iterated adversarial training, 1,000
  training malware per round; MAB-Malware at ours and at Zainab et al.'s setting; three escapes against three
  detectors with the adaptive search and the toolkit.
- **Every step has its `run.sh`** (session 68), smoke-tested; `pipeline/README.md` lists them in order, each header
  names its inputs, outputs, knobs and estimated cost.
- **Optimized (session 69), bit-identical:** the extraction-scored adaptive search no longer computes an unused
  prediction per structural candidate; a file store (`2-features/file-store`: the attacked files in one SQLite file
  beside the lists; `provexp.data.filestore`, read by the loaders when present) replaces ~25 min of SimpleDB loading
  per attack task; the string features use numpy and `str.find`. An adaptive candidate ~0.32 -> ~0.10 s (the search
  ~7-9k -> ~2.5-3k CPU-h), sums extraction 120 -> 78 ms per file. No further optimization is planned: the rest of an
  extraction is spread over strings (~40%), byte-entropy windows (~25%), byte counts and pefile's parse, and no single
  change would gain 50%.
- The identity check (`pipeline/setup/identity_check.sh`) shows only its recorded reference differences (the fixed
  string and directory features, the catalogue's counts, the manifests' commit, the escape row of `0485edc2...`).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- Explain plainly; lead with what is computed, what it is compared with, and why it matters.
- State a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Ask before changing what a statistic or claim is for; the user decides protocol questions, Claude recommends.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority. Never edit a `run.sh` while it runs.
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. This session: two questions for the user (neither needs the cluster)

Present each plainly with a recommendation, let the user decide, then set the default in the step's `run.sh` (and
any code it needs), smoke-test it on a small slice, and record the decision in PLAN.md step 3 (g).

1. **The derived table's corpus.** `3-directions/derived` builds the direction tables (Theorem 1's sound directions,
   the input of the monotone detectors and of Table 4) from the item tables of a file list: the term vocabulary and
   the in-place operations' changes are collected from those files' items. Its default list is still the pilot's 100
   files (`FILES` in `pipeline/3-directions/derived/run.sh`). Theorem 1's hypothesis for operations stated as writes
   is checked on this corpus, not proven (PLAN.md decision 2: the 100-file and 2,000-file tables were identical, and a
   larger corpus strengthens the check at no cost in pages). Options at the scale-up: (a) the evaluation set, as the
   audit steps and the trial use (the trial also learns from it, so the comparison with it is even); (b) training
   files only (the defender's data, so the table never sees the files it is evaluated on); (c) both. Points to weigh:
   whether a defender could build the table from data it has (b), whether the table depends on the corpus at all once
   it is large (it did not between 100 and 2,000 files, so the choice may not change a number; checking that on this
   machine is cheap), and consistency with the trial's corpus. Before recommending, look at what `directions.py`
   actually takes from the corpus and whether a table built from (a) and one from (b) differ (a short run on a few
   hundred files of each is within the 10-minute rule).
2. **Iterated adversarial training's starting point** (chosen by Claude in session 68, open to the user's veto).
   Round 1 attacks the adversarially trained detector (the toolkit's material already in its training set), so the
   paper's row `iterated-2` is the strongest learned baseline plus two rounds of our beam search
   (`pipeline/4-detectors/iterated/run.sh`, `previous=adversarial-training`). The alternative starts from the
   unconstrained detector, so the row isolates what the beam's rounds add. Weigh what the row is meant to answer in
   §5.3 (R18 in `docs/evidence/r18-trial-competitor.md`: the strongest realistic learned competitor), and the
   memory's rule of fair baselines over faithful copies (the strongest fair baseline).

## 5. Then: the head-node session (a later session, with the user at the cluster)

1. **Setup** (`SETUP.md`): clone, `pipeline/setup/build_env.sh`, the `artifacts` symlink, the dataset location; copy
   the file lists and the metadata (`artifacts/scaleup/2-features/files/`, `artifacts/metadata/`) from this server.
2. **`pipeline/setup/check.sh`** must pass (bit-exact featurization on 32 files, the tests).
3. **The "TO CONFIRM" values** in `pipeline/systems/sporc.sh` (cores per node, large storage, walltime, Python 3.14
   through uv) and in each `run.sh`'s header: time, memory, `--gpus-per-node` (`4-detectors/learned`: ERDALT one per
   GPU, each loading the ~25-30 GB store), array sizes. The adaptive search's header carries session 69's lower cost;
   re-check the shard count against it (fewer, longer shards may now suit the walltime).
4. **Featurization:** `2-features/featurize/run.sh` with `EXTRACTORS="sums expert"` on the full splits, one node.
5. **The file store:** `2-features/file-store/run.sh` after the lists (or copy `files.sqlite` from this server once
   built); its build time (~1-3 h) and size (~10-15 GB) are estimates.
6. Then the steps in `pipeline/README.md`'s order, submitted by the user.

## 6. Noted for later (not this session unless it becomes necessary)

- After the debug-entry escape, `gamma_api` (which rebuilds the file through LIEF) no longer evaded the unconstrained
  smoke detector on 3 files it evades unescaped: LIEF seems to handle the escaped debug entry differently. Worth a
  look when the toolkit's escape rows are read (it weakens the toolkit after an escape, not the guarantee).
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact).
- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split), an
  effect of the family cap; worth one sentence in Setup if a reader could ask.
- Other SimpleDB readers (the audit steps, `3-directions/trial`, `3-directions/derived`) still read file by file; they
  could use `provexp.data.files.FileReader` if their scale-up runs turn out slow on loading.

## 7. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-<date>-s70.md`, with its line in `docs/README.md`.
