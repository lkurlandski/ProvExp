# Resume: lightweight optimization of the scale-up's hot spots, then the head-node session

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
  1,000 benign complete test files (`artifacts/scaleup/2-features/files/ts.parquet`); every detector on the full
  training split's complete files (~1.76M); thresholds on the validation split; two disjoint donor sets of 100
  training goodware (set 0: the defenses' material and the trial's imports; set 1: every attack on the evaluation
  set); the defenses' material once from 10,000 training malware; the trial row learning from the evaluation set;
  iterated adversarial training, 1,000 training malware per round; MAB-Malware at ours and at Zainab et al.'s setting;
  three escapes against three detectors with the adaptive search and the toolkit.
- **Every step has its `run.sh`** (session 68), each smoke-tested end to end on a small slice; `pipeline/README.md`
  lists them in the order they run, each header names its inputs, outputs, knobs and estimated cost. Long steps are
  SLURM job arrays that skip what is done: the material (`4-detectors/adversarial-training`, 10 shards), the toolkit
  attacks (`5-attacks/toolkit`, 21 jobs), the adaptive search (`5-attacks/adaptive`, 4 escapes x 20 shards plus the
  expert set). Detectors live in `$OUT_ROOT/4-detectors/<name>` (the registry's `scaleup` set,
  `src/provexp/registry.py`). Tables: `6-results/scaleup_tables.py`, `coverage.py`, `erdalt_hole.py`.
- Session 68 also fixed a session-67 bug (the adaptive search's workers reloaded the pilot list under `--protocol
  scaleup`) and made `pipeline/setup/identity_check.sh` start from an empty directory. The identity check shows only
  session 66's recorded differences (the fixed string and directory features, the catalogue's counts, the manifests'
  commit, the escape row of `0485edc2...`): that is its reference state.
- **Where the compute goes (estimates from the pilot's timings, not profiled):**
  - the adaptive search, ~7-9k CPU-h of the scale-up: every candidate is written and re-extracted with the sums
    extractor and scored (`--score real`, 5,000 candidates per (detector, file), ~0.6 s per candidate in run 143,
    ~8-11 CPU-h per detected malware over all detectors); also iterated adversarial training's two rounds (~0.5k
    CPU-h) and the escapes;
  - the defenses' material (~700-900 CPU-h: eight secml-malware attacks on 10,000 files, each query a LIEF rebuild
    plus an extraction), the toolkit attacks on the evaluation set, MAB-Malware (~0.3 s per action, ~5 h per detector);
  - featurization (~0.1-0.2 s per file and extractor, ~2.3M files, two extractors); session 62's LIEF spike measured
    parsing at only ~12-25% of the per-file time, so most of it is our extractor's own Python;
  - training (GBDTs ~20-40 min each, ERDALT ~4-5 h each on a GPU) is small by comparison.
  The common factor is **feature extraction** (thrember's features plus the re-encoding over sums, instrumented), called
  once per candidate or query.

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Optimization (user, 2026-10-13, 2026-10-20, session 68):** profile first; propose each optimization in words with
  its measured gain, effort and added complexity; implement only what the user approves; keep the diff small,
  modular and documented; prove the results bit-identical (tests, `pipeline/setup/check.sh`'s reference vectors,
  the identity check). Never replace pefile, edit third-party source, or rewrite the EMBER pipeline; a small exact
  runtime patch of one pefile name is acceptable once approved (precedent: `features.byte_counter`, 2026-10-20). The
  user's order of preference among techniques: a better algorithm in Python, then numpy, then numba, then Cython,
  then native C/C++ (least preferred).
- **Never propose Proposition 1's incremental scoring as a speed-up** (measured slower than extraction in our Python,
  session 49; `--score real` everywhere, settled) and make no timing claims about it.
- Bit-exactness matters beyond our runs: the plain extractor must still reproduce EMBER v3's released vectors
  (`check_features.py`), and the cluster's featurization must match this server's (`check.sh`).
- Explain plainly; state a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority. Never edit a `run.sh` while it runs.
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. This session

### 4.1 First: lightweight optimization (the user's request, end of session 68)

The aim: cut the scale-up's compute where a modest, reviewable change buys a lot, before anything runs on the
cluster. Steps, with the user's review between them:

1. **Profile the expensive paths** on a representative slice (a few evaluation-like files spanning small and large
   sizes; the pilot's stores and models, as session 68's smokes used, in the scratchpad): (a) one adaptive search's
   candidate loop (`provexp.attacks.adaptive`: candidate writing, `RealEngine` re-extraction with
   `SumsFeatureExtractor`, booster prediction); (b) one feature extraction per extractor (`featuresets/ember2024/
   features.py`, `sums.py`, `expert.py`), split into pefile parsing, LIEF (the overlay rule, signatures), byte
   histograms and entropy, strings, imports, the sums' item tables; (c) one toolkit attack run and one MAB-Malware
   action (how much is extraction, how much secml/LIEF rebuilding, which we do not own). Use `cProfile`/`pstats` and,
   for line-level detail in the hot functions, `line_profiler` if installed (ask before adding a dependency). Report
   where the time goes per candidate, per file, per attack run, and weight it by the scale-up's call counts (§2).
2. **Assess** each hot spot: the candidate measures (better algorithm, numpy, numba, Cython, C/C++, in the user's order
   of preference; also caching work that repeats across a search's candidates of one file, e.g. the parts of the
   extraction a candidate cannot change, if exactness is provable), the effort, the complexity added (code the user
   must review, new dependencies, build steps on the clusters, aarch64 on tigris), and the likely gain in CPU-h on
   the scale-up. Present it as a short table for the user's cost-benefit call.
3. **Implement only what the user approves**, keep each change modular, prove bit-identical features (the reference
   fixtures, `check.sh`'s 32-file reference, `check_features.py`'s comparison with EMBER's released vectors where it
   applies, the identity check), re-profile, and decide with the user whether to continue.

Hypothesis to state before profiling (Claude's expectation, to be checked): extraction dominates the adaptive search's
candidate time, and within it the byte-level passes over the whole file (histogram, byte-entropy windows, string
scans) and the sums' item tables matter more than pefile's parse.

### 4.2 Then: the head-node session (sporc first), possibly in a later session

With the user at the cluster (they run what needs their account; suggest `! <command>` for interactive steps):

1. **Two questions for the user** (raised at the end of session 68, not yet answered):
   (a) *The derived table's corpus.* `3-directions/derived` takes the term vocabulary and the in-place operations'
   changes from the item tables of a file list, still the pilot's 100 files by default. Which corpus at the scale-up:
   the evaluation set (as the audit and the trial use; the trial learns from it too, so the comparison is even), or
   training files only (the defender's data)? Set `FILES` in that `run.sh`'s default accordingly.
   (b) *Iterated adversarial training's starting point* (chosen by Claude in session 68, open to veto): round 1
   attacks the adversarially trained detector (the toolkit's material already in it), so the row is the strongest
   learned baseline plus two rounds of the beam; the alternative starts from the unconstrained detector.
2. **Setup** (`SETUP.md`): clone, `pipeline/setup/build_env.sh`, the `artifacts` symlink, the dataset location; copy
   the file lists and the metadata (`artifacts/scaleup/2-features/files/`, `artifacts/metadata/`) from this server.
   If 4.1 added a compiled dependency (numba, Cython), check it builds and gives identical features on both
   architectures.
3. **`pipeline/setup/check.sh`** must pass (bit-exact featurization on 32 files, the tests).
4. **The "TO CONFIRM" values** in `pipeline/systems/sporc.sh` (cores per node, large storage, walltime, Python 3.14
   through uv) and in each `run.sh`'s header: time, memory, `--gpus-per-node` (`4-detectors/learned`: ERDALT one per
   GPU, each loading the ~25-30 GB store), array sizes; re-estimate from 4.1's profile if it changed the costs.
5. **Featurization:** `2-features/featurize/run.sh` with `EXTRACTORS="sums expert"` (the plain `ember2024` store is
   only for `check_features.py`) on the full splits, one node.
6. Then the steps in `pipeline/README.md`'s order, submitted by the user.

## 5. Noted for later (not this session unless it becomes necessary)

- After the debug-entry escape, `gamma_api` (which rebuilds the file through LIEF) no longer evaded the unconstrained
  smoke detector on 3 files it evades unescaped (and added fewer bytes): LIEF seems to handle the escaped debug entry
  differently. Worth a look when the toolkit's escape rows are read (it weakens the toolkit after an escape, not the
  guarantee).
- `mab.py` and `toolkit.py` stop with an error when a detector detects none of the malware (a smoke artifact).
- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- `pv_attacks.py`, `toolkit_split.py` and `trial_audit.py` still read the pilot's layout only.
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- The evaluation set's malware lean toward larger files (44% at 512 KiB-4 MB against 25% in the test split), an
  effect of the family cap; worth one sentence in Setup if a reader could ask.

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-<date>-s69.md`, with its line in `docs/README.md`.
