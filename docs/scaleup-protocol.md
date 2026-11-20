# The scale-up's protocol

PLAN.md's step 3 in full, moved verbatim on 2026-11-17 so that the plan holds only what comes next. Every decision
behind the scale-up, with its reasons: items (a)-(g) and (1)-(16). "PLAN.md step 3 (g)" or "step 3 (13)" anywhere in
the project means the item of that label below. Open it when a task touches the scale-up's protocol, its jobs, or
reading its results (PLAN.md step 5).

3. **Design and launch the scale-up as one protocol** (each item agreed before code; long runs as `run/` scripts for the
   user, possibly on the second server), **on the files our copy holds in full in every split** (the `truncated` flag
   false: training subsample, test split, attacked malware; decision 8 (iv)): seeds 0-2, full splits; one training set
   and one attack protocol for every detector of §5 (Tables 4 and 5 now show two different unconstrained detectors;
   Table 5's two halves with the same detectors; the pilot's adversarial training read the plain `ember2024` store,
   EMBER v3 without our fixes, which stays only for `check_features.py`'s comparison with the released vectors); ERDALT trained as in run 133 (their full 310-epoch schedule, epoch
   chosen by their criterion; R19's check found the training sound, so no change); enough malware that PV and the expert set are not judged on 8-9 files; the adaptive budget at
   scale (~3,000 CPU-h at 5,000 candidates on 2,000 files; options: the 1,000-candidate checkpoint, a fixed subset, a
   cap on the monotone rows); **MAB-Malware as a held-out attack we did not write**. Hypothesis: MAB-Malware finds PV's
   rename hole (support for 5.3 independent of our table-guided attack) and evades no monotone detector on a file in the
   population. Plus whatever the review adds (meta-review §7: the routed system end to end, now the unrouted one of
   decision 11; MAB-Malware; the adaptive search scoring by extraction where the computation declines, as run 138's
   `--score real`; equal-information learned defenses if decision 6 is revisited; thresholds from the validation split).
   From R7: the escape attacks at scale (look actively for further escapes), the toolkit attacks on escaped files, the
   population share of attacked malware with its denominator, the files outside the population re-featurized with
   LIEF's overlay rule, and the unconstrained detector trained on the same store as the others. Listed in session 61,
   from the blue values and PROTOCOL notes the R7 text left: the toolkit attacks and MAB-Malware on the `-loose`
   monotone detectors (Table 5, Appendix D's per-attack table); the price list (run 126) re-run on the widened table
   (*Where the cost lies*); the closure count and the population shares recounted on the widened population (§4.4,
   §5.4); the adaptive attack under one protocol (run 143 extracted every candidate at 2,000; §5.1 states Prop. 1
   scoring and 5,000); a signature-cloning citation (`% VERIFY` in §4.3). Expect the unconstrained detector's adaptive
   cell near 100% now that `ent` clones signatures.
   From the rebuttal (session 58, `docs/reviews/2026-11-12-body/rebuttal/triage.md`): **before the recount**, the
   recorded Rich search range extended by the 4 key bytes past the marker (R2; done in session 59, d806b84, no
   direction changed); at
   the scale-up, MAB-Malware also at Zainab et al.'s setting (0.1% FPR, no byte cap) against the unconstrained
   detector (R1), and the ERDALT donor-overlap control (GAMMA imports with the training donors; R19). Waiting on: run
   143 (R7 track) and R18 (the trial competitor; decides whether iterated adversarial training joins).
   *R18, sessions 60-63* (`docs/evidence/r18-trial-competitor.md`): run 144 read and audited. The trial detector
   (directions learned by trying the twelve operations) is evaded on 26/44 pilot malware by the beam and 17/44 by
   MAB-Malware, the derived detector on 0/39 by both; every evasion goes through a feature trial never saw move.
   **Decided (user, session 63):** (a) the reading: §5's lead and §5.3 gain it as measured evidence that trial answers
   only for the edits and contents it tries, the derivation for the threat model; the toolkit variant in a sentence or
   two (a wider trial closes one hole, the attack finds the next); trial's clean-detection edge (87.6 vs 83.4% at 1%
   FPR) stated with §5.4's cost, as resting on features an attacker can move; prose after the scale-up. (b) The
   scale-up has a trial row in Table 5 (the own-writer trial and the derived detector, same protocol, beam and
   MAB-Malware); trial-toolkit stays at pilot scale (text or appendix). (c) Iterated adversarial training in the
   scale-up: two rounds of the beam over the twelve operations on training malware, `ent` held out of the loop,
   tested with `ent` and MAB-Malware as held-out attacks (`a1_adaptive.py --save_rows`, applied in session 63;
   training malware via `--pilot_files` with a training list and `--db .../tr`).
   **Answered (user, session 49): widen first, for now**, then scale everything once. The question was: scale the
   existing experiments first (more files, seeds 0-2), or widen
   them first (the review's new experiments: MAB-Malware, the escape attack, equal-information baselines, a trial
   table), then scale everything once. The sums row's adaptive cell stays 0% with its
   footnote (session 36).
   **Added in session 63 (the last review revisit; nothing else before the scale-up, user agreed).** (a) The
   extractor audit pass with its deviations table is the scale-up's *first* piece of work, before any featurization
   script: it is the only item that can change the feature store. (b) Reporting duties the scale-up's scripts must
   produce: the share of *all* attacked malware still detected after each attack at 1% and 0.1% FPR, files outside the
   population counted (R7's last open triage item; body "after any attack", appendix per attack); §5.3's coverage
   counts on modeled features only, the 88 warnings excluded (R12); from the scale-up's models, the monotone detector's
   split-gain share on features no edit moves (R15) and the detected malware's margins against the hand table's
   1.57-logit maximum drop (R3). (c) Compute: the user has a shared cluster (hundreds of nodes like this server,
   priority queue); this scale-up need not be the last or the largest, so size it for days to a few weeks, not months.
   (d) **Decided (user, session 63):** the adaptive attack scores 5,000 candidates by extraction for every detector
   and escape (checkpoints 200, 1,000, 2,000, 5,000). **One seed (0)**, not seeds 0-2: seeds wait until the
   methodology is final; compute goes to more samples instead (supersedes "seeds 0-2" above and in meta-review §7).
   (e) **Organization and portability (user, session 63):** the scale-up's code and experiments reorganized into
   something human-readable, and reproducible setup instructions for new systems (the SLURM clusters tigris and
   sporc; SSViT's `scripts/create.py` shows their configuration). **Agreed (user, session 63):** a `pipeline/` folder
   for the scale-up, one numbered stage per folder (setup, 1-audit, 2-features, 3-directions, 4-detectors, 5-attacks,
   6-results), each with a short README and **one `run.sh` per step with the `#SBATCH` header at the top** (`sbatch`
   on the cluster, `bash` locally; no separate submit scripts); outputs under `artifacts/scaleup/<stage>/`; one
   registry of plain names for detectors and attacks; library code moved from `scripts/` into `src/provexp/` (old
   scripts become thin wrappers or are deleted with the dead code), tests updated and expanded; the move checked
   byte-identical on a pilot slice; `SETUP.md` with `build_env.sh` and `check.sh` (featurization bit-exact). Run
   everything on sporc (x86_64); tigris (aarch64) only after a bit-exactness check. **Executed in a dedicated
   refactoring session** (`docs/resume-prompt.md`), then the audit pass, then the remaining protocol items (malware
   count first), then a session on the cluster's head node.
   **Done in session 64** (commits b223fcd, 185212e, 3a6fba2; `docs/status.md`): `pipeline/`, the registry, library code
   in `src/provexp/`, dead code removed (tag `pilot-final`), `SETUP.md`, `build_env.sh`, `check.sh`; byte-identical to
   the old code on a pilot slice (`pipeline/setup/identity_check.sh`). `run.sh` exists for featurize, the derived
   directions, the catalogue checks, the adaptive search and MAB-Malware; each other step gets its `run.sh` when its
   protocol item is decided.
   (f) **Decided (user, session 64): every result the paper reports comes from the scale-up** (one protocol, the same
   files); pilot runs are for tests and explorations only. `pipeline/README.md` maps each result to its step. So the
   audit pass also runs the hand table at scale and counts the files showing each of its errors (the witnesses), and
   re-checks combined edits by chaining the catalogue's edits (Appendix D's sentence rested on the removed A' code,
   run 111); leave-one-out (Table 10) runs at scale, its cost joining the malware count; trial-toolkit is not in the
   paper and stays an exploration.
   (g) **Protocol items decided (user, session 67).** (1) *Evaluation set:* 1,000 malware and 1,000 benign test files,
   drawn only from the complete files (below 4 MB), TLSH near-duplicates removed, at most 10 per family, seed 0
   (`pipeline/2-features/files`, `select_files.py --complete_only`; drawn: 333 families plus 209 unlabeled; the cap
   leans the malware toward larger files, 44% at 512 KiB-4 MB, as the old selection did). Every attack runs on its
   malware (each detector on those it detects), every `1-audit` step on all of it. Cost estimated from the pilot: ~8-11
   CPU-h per detected malware (the adaptive search at 5,000 extraction-scored candidates, ~10 pairs per file at the
   full budget), ~7-9k CPU-h in all, about a day on ten nodes; none of the fallbacks (1,000-candidate checkpoint,
   subset, cap) is needed. (2) *One training set:* every detector trains on the full training split's complete files
   (~1.76M), each reading its patched store. (3) *Thresholds* (1% and 0.1% FPR) set on the validation split's
   goodware for every detector (the pilot used the test split). (4) *Donors:* one fixed set of training-split complete
   goodware for every attack on the evaluation set (toolkit, adaptive with signature cloning, MAB-Malware); no test file
   in the attacker's hands. (5) *The learned defenses' material, once:* the eight toolkit attacks (seed per file, low
   budget, training donors) on 10,000 training malware (complete, deduplicated, family cap; all of them, detected or
   not), against the scale-up's undefended detector, so after it; ~80k outputs, ~700-900 CPU-h. Saved as feature rows
   for every store the defenses read and as compressed adversarial binaries (~30-60 GB), so an extractor change means
   re-featurizing, not re-attacking. PV, ERDALT, adversarial training and the leave-one-out folds all read it.
   Drawn (`2-features/files`): `tr.parquet` (10,000 per label, from 114,054 training malware after the cap) and two
   disjoint donor sets of 100 training goodware, `tr-donors-0` (the defenses' material, the trial's imports) and
   `tr-donors-1` (every attack on the evaluation set); R19's donor-overlap control attacks with set 0. Code: the
   trainers' `--complete_only` and `vl_predictions.parquet`; the attacks' `--protocol scaleup --donors`
   (`provexp.data.files.load_attacked`, `provexp.detectors.model_threshold`/`detection_at`). (6) *The trial row:* the
   trial learns from the evaluation set (the audit's catalogue edits and `trial_probe.py` on all 2,000, imports from
   donor set 0), which favours the competitor. (7) *Iterated adversarial training:* 1,000 training malware per round
   (of `tr.parquet`), the beam at 5,000 extraction-scored candidates, two rounds, `ent` held out (~0.5k CPU-h).
   (8) *MAB-Malware* (arguments only): every detector at our setting (1% FPR, our byte cap, 60 actions, donor set 1),
   plus Zainab et al.'s setting (0.1% FPR, no byte cap) against the unconstrained detector. (9) *Escapes:* the three
   writes (certificate entry, debug entry, SizeOfImage) against the unconstrained and the two monotone detectors, each
   followed by the adaptive search (in (1)'s budget) **and the eight toolkit attacks** (~600 CPU-h; `toolkit.py`
   needs `--escape`, counted from the unescaped original as `adaptive.py` does); the escape audit on every population
   file of the evaluation set. Still to implement before the head-node session: the scale-up's `run.sh` for training
   (`--complete_only`), the defenses' material (rows for every store and the compressed binaries), the toolkit (with
   escapes), iterated adversarial training, the trial row, MAB-Malware's second setting, the registry's `scaleup` model
   set, and the reporting duties in `6-results` (share of all attacked malware still detected; R12, R15, R3).
   **Done in session 68:** every step has its `run.sh` with the scale-up's defaults, each smoke-tested on a small
   slice (`pipeline/README.md` gives the order). The registry's `scaleup` set (`4-detectors/<name>`, with
   `iterated-{1,2}` and the leave-one-out folds `{pv,erdalt}-loo-<attack>`); `4-detectors/train` (Table 5, the expert
   set, trial); the material as a job array (`4-detectors/adversarial-training`: `attack_training.py` on the lists,
   rows for the sums and expert stores, zstd binaries, shards merged later; rows checked equal to the binaries'
   re-extraction); `4-detectors/learned` (PV selected among EMBER's features with `pv_hole.py --exclude`, ERDALT one
   per GPU, adversarial training, the folds); `4-detectors/iterated` (the adversarially trained detector as round 0,
   rounds of 1,000 disjoint training malware, `ent` held out, rows of earlier rounds kept); `4-detectors/price-list`;
   `3-directions/trial` (`trial_probe.py --donor_list`); `5-attacks/toolkit` (`toolkit.py --escape`; array over
   detectors, escapes, folds and R19's donor control) and `5-attacks/adaptive` (array over escapes x 20 shards, plus
   the expert set's search), MAB-Malware's three settings (ours, the expert set, Zainab et al.'s); `6-results`
   (`scaleup_tables.py`: test TPR at the validation thresholds, the share of all evaluation malware still detected
   after each attack and after any at 1% and 0.1% FPR, R3's margins, R15's gain share; `coverage.py`'s `modeled`
   class for R12; `erdalt_hole.py --protocol`). A bug from session 67 fixed: the adaptive search's workers reloaded
   the pilot list under `--protocol scaleup`. Open for the user: the derived table's corpus at the scale-up, and
   iterated adversarial training's starting point (Claude chose the adversarially trained detector).
   **Lightweight optimization (session 69): done, bit-identical.** Profiled; three changes approved and made: the
   extraction-scored search writes structural candidates without computing their unused prediction; a file store
   (`2-features/file-store`, SQLite beside the lists) for the attacked files; the string features with numpy and
   `str.find`. An adaptive candidate ~0.32 -> ~0.10 s (the search ~7-9k -> ~2.5-3k CPU-h), sums extraction 120 -> 78
   ms per file. The remaining time is spread (strings ~40% of an extraction, byte-entropy windows ~25%, byte counts
   and pefile's parse the rest); no further change would gain 50% alone (session 69's assessment).
   **The two open questions: decided (user, session 70).** (10) *The derived table's corpus:* the tables are built
   from training files (the 20,000 of `2-features/files/tr.parquet`: the defender's data, never the evaluated files)
   and rebuilt from the evaluation set as a check; `compare_tables.py` reports whether the evaluation set shows a
   move the table lacks (`3-directions/check/{strict,loose}.json`). This turns decision 2's check into a held-out
   one, and is the less favourable side of the comparison with the trial, which learns from the evaluation set. If
   the two differ at scale, the cells are reported and the user decides (the union is the fallback). What the corpus
   supplies are unions (the kinds' terms, the in-place writes' changes, population membership), so a table only
   gains signs with more files. Checked on 300 evaluation against 300 training files (loose): the population's
   variant identical in every per-operation cell, the detectors' input files identical (also to the pilot's
   100-file table); the hypothesis "identical" failed only for the strict variant's per-operation cells (2,597 of
   47,515, from a few files outside the population; no threat-model direction differs). With 32 or 48 files one
   feature differs (`num_empty_name` under renaming: up instead of both), so a small corpus is not enough. Cost ~5
   CPU-s per file and variant, ~60 CPU-h in all. (11) *Iterated adversarial training's starting point:* the
   adversarially trained detector, as scripted (R18's strongest realistic learned competitor; the adversarial-training
   row beside it shows what the beam's rounds add; one row, not two).
   **The head-node session: done (session 74, 2026-11-16, tigris).** Setup on tigris (aarch64; gg CPU nodes 144
   cores, gh nodes one GH200): `check.sh` passed, featurization bit-identical to the reference; `artifacts` ->
   `/shared/rc/admalware/provexp`; the headers ask for half a gg node (72 cores), a quarter per array task, one GH200
   per `learned` task. `pipeline/submit.sh` submits the whole chain with SLURM dependencies; `3-directions/gate` stops
   the detectors unless the derived check is clean. Done at scale: featurization (sums, expert), the file store, the
   derived tables, population, item checks (2,000 files, 0 failures), escapes, deviations.
   (12) **The derived table at scale (user, session 74).** The gate stopped the chain: the table from the 20,000
   training files covers the evaluation set (no move it lacks), but 361 population cells differ, every one a move
   only training files show: slack writes on the 256 body-histogram bytes (no direction changes), a section rename
   raising and lowering the 96 `body_strings:printable_*` counts and `section:max_entropy`, the header-field
   overwrites moving `has_relocs` and `has_dynamic_relocs`; 98 threat-model directions become two-sided (98 more
   features dropped by the monotone detectors). The union of both corpora is the training table. Decided: proceed
   with the training table (the protocol); the gate stays as it is (stops on any differing population cell). The
   files behind the new moves are not yet identified (worth knowing before §4.3.2 is rewritten).
   Also done at scale: `train` (the five detectors without the trial) and `price-list`. Two bugs found at scale and
   fixed (session 74): files with fewer than 16 data directory entries (24 of the 2,000 evaluation files) crashed the
   entry writes (catalogue check, escapes); secml's data directory raced across array tasks.
   (13) **GAMMA on files LIEF cannot rebuild (session 77, user).** Also done at scale: the catalogue check, the hand
   table, the trial table and the trial detector, and the defenses' material (job 1018609; ~2 h per shard on 36
   cores). The material lost 224 of 80,000 runs (all `gamma_sections`/`gamma_api`, 117 files) to OOM-killed
   workers, each costing a 45-min stall. Cause: LIEF's rebuild, which both GAMMA attacks run on every query, runs
   away on some malformed files (output padded to a garbage section offset, 2 GiB; failed allocations; parser
   crashes); 38 of 40 lost files fail a plain LIEF round trip, 0 of 40 controls; the rest were collateral. Decided
   (user): prevent it rather than catch the OOM, and do not count these as attack failures. Each start file gets
   one LIEF round trip in a capped child process before the attacks (`provexp.attacks.lief_check`, ~1 s per file,
   never per perturbed binary); where it fails, the two GAMMA attacks are *not applicable* to the file (no run,
   counted apart; the other six attack it). In the toolkit and the material; `attack_training.py --repair` mends the
   finished material from the lost list. No other attack rebuilds through LIEF (adaptive search and MAB-Malware use
   their own writers). **Decided (user, session 78):** a toolkit attack's "still detected" share counts only the
   files it applies to, with the not-applicable count beside it (eec804b); after any attack the denominator stays
   all the malware. The repair finished: 79,121 valid rows, 216 not applicable, none lost again.
   (14) **Resources sized to use (session 78, user).** `learned` held 36 cores for ~30 h of single-core GPU training
   (ERDALT) behind 25 min of GBDTs, and MAB-Malware and `6-results` reserved 72 cores for one to nine single-threaded
   processes. Now: `learned` is a CPU job for the GBDTs and a 9-task GPU array at 4 cores (23ac418); MAB-Malware an
   array of one task per setting, one core per detector (9f91013); `6-results` 16 cores; the finished steps'
   walltimes are their measured times x1.5 (36faebe). The rule is in CLAUDE.md. Measured: ERDALT ~5.8 min per epoch,
   ~30 h per model, peak 91 GiB. **To watch:** ERDALT's validation AUC is 0.69-0.75 at scale (0.88 at the pilot)
   and no epoch had met Gimenez et al.'s criterion (< 5 violations; best 16) by epoch ~185 of 310; read the selected
   epoch when it finishes, since a weak ERDALT invites the straw-man objection.
   (15) **Thread limits, MAB-Malware's shell, and a parallel setup (session 81).** MAB-Malware `zainab` (1030369_2)
   crashed after 32 min on a copy that never happened, and `iterated` (1020793) was losing tasks (9 files of round 1,
   ~29 dead workers): both ran on gg-a-016, where the user's processes and threads reached 16,082 of the per-user limit
   of 16,384. Cause: SLURM on tigris starts each job with `OMP_NUM_THREADS` = its cores, which `common.sh` kept (it
   only filled in a missing value), so each of `iterated`'s 72 workers built 72-thread OpenMP and OpenBLAS pools plus
   polars' pools (~380 threads per worker); a shell could not start and threads could not spawn. Fixed: `common.sh`
   sets OpenMP, OpenBLAS and polars to one thread per process (927dc5f) and prints the thread settings, cores and
   process limit at every job's start (c6f6483); a worker now has 9 threads. MAB-Malware: upstream's ~60 unchecked
   `os.system` file operations go through `checked_system` (a failed command raises; a shell that cannot start is
   retried), and '/' or '|' in a donor section name becomes '_' (the user's choice): the donor set grows from 484 to
   501 sections, since a `/4` name had also dropped every later section of its file (50f3e97); `expert` was rerun
   for consistency (137/161 evaded, was 132). `iterated` was cancelled and restarted at 300 GB (7f1e249; it reached
   196 GiB of 200, and 230 GiB in the restart). The adaptive search's per-file setup (escape write, extraction,
   population checks) ran one file at a time in the main process, once per defense (~30 min for 1,000 files on 1 of
   72 cores); `prepare_files` now runs it over `--num_workers` (7178180), each file extracted once; detector scores
   stay one-row predictions in the main process. Verified: old and new code on the same search (40 evaluation
   malware, two detectors, with and without the debug escape, 16 workers) give identical outputs apart from timing
   (`artifacts/scaleup/diag/setup-pool/`; the identity check cannot run on tigris: its baseline and the pilot files
   were never copied). Measured: `iterated` round 1, 968 detected files searched in 55 min on 72 cores, none lost, 683
   evaded; `iterated-1` retrained in 7 min (test AUC 0.998).
   (16) **The file store at one location; ERDALT apart (session 82).** `iterated`'s rounds spent ~20 min each before
   searching (round 2: 14:08 to ~14:30, then 88 min of search): the loaders looked for `files.sqlite` only beside the
   file list they were given, and `iterated` writes each round's list into its round folder, so 1,000 training malware
   a round were read from the SimpleDB, one shard decompressed per file, with no message. Decided (user): the code must
   know where the store is, and an experiment that expects the store must stop if the store or a file is missing.
   Now `pipeline/common.sh` exports `FILE_STORE` (`$OUT_ROOT/2-features/files/files.sqlite`), read by
   `provexp.data.paths.file_store()`; `load_evaluation`, `load_donors`, `read_files`, `FileReader` and the population
   check read only the store and check every name before reading (c7481c3). The pilot keeps its SimpleDB reads.
   Verified on tigris (`artifacts/scaleup/diag/file_store.sh`, job 1045818): unset setting stops; 1,100 files in 0.8 s,
   20/20 byte-identical; the population check identical (4 s vs 48 s); old and new adaptive search identical on 24
   files. `iterated` measured: 3 h 24 min in all, 282 GiB of 300 at peak (230 in round 1), ~45% of its cores (long
   tails: round 2's last 22 of 972 files took 32 of 88 min); round 2: 972 detected, 515 evaded.
   **ERDALT collapses at scale.** All nine models: validation AUC 0.85-0.87 at epoch 0-1, ~0.69 by epoch 40, flat since
   (0.69-0.75); violations from ~1.3 million to 16-42 at best, Gimenez et al.'s < 5 never met. The port is theirs apart
   from batch 256 (theirs 16), the monotone output layer and selection on the validation split; the scale differs (1.76
   million training files, 79,121 vectors against the pilot's 3,183 and their ~1,033). Leading hypothesis: the penalty
   is a sum over every vector while BCE is a batch mean, so it dominates from the first step. The user let the models
   finish and set ERDALT aside for its own session (`docs/resume-prompt-erdalt.md`). The other attacks run without it
   (cancelled 1039056-58 and 1039060; resubmitted as `toolkit` 1046138 with `PARTS="main escape loo" LOO=pv`,
   `adaptive` 1046139, MAB-Malware `ours` 1046140 at 8 cores, all with the eight other detectors; aaefd75): each search
   is seeded per run, so a detector's results do not depend on the others in its run; ERDALT's runs go to their own
   outputs (`TAG`; the toolkit's `loo/<family>-<attack>`), and `scaleup_tables.attack_outputs` stops if a (defense,
   attack, file) appears twice. `6-results` is held until ERDALT's attacks have run.
   **Next:** the experiments track (`docs/resume-prompt-experiments.md`) and the ERDALT track, then read it (step 5).
   (17) **Attack failures, broken outputs, and PV's sample size (session 85).** *Done:* MAB-Malware's section-adding
   action no longer crashes on files with no sections, and each run starts from an empty work directory (455f121;
   `ours` resubmitted as 1131288). A run with no result an hour after the last other one finished is given up and its
   file discarded (left out of the count and the denominator unless another counted output evades it) and reported;
   acceptable while fewer than ~10 in 1,000 (user; ec2a5bd). Every header right-sized from `sacct` (ec2a5bd, 74da6eb,
   and `hand-table`: file store and worker pools, it had held 72 cores at 2% for 108 min). *Found:* PV at scale keeps
   201 features (pilot ~1,490), test AUC 0.61, 5/1,000 evaluation malware at 1% FPR. Two causes. (a) **Broken outputs
   in the defenses' material** (`attack_training.py` kept any output whose attack ran): 894 of 79,121 (1.1%, from
   ~430 of the 10,000 training malware): 716 from the two shift attacks on 358 files whose first section has file
   offset 0 (e.g. `.textbss`; secml-malware inserts its padding at that offset, so in front of the MZ header: an
   upstream bug), 45 DOS-extend/format-exploit outputs with an invalid e_lfanew, 133 that still parse but lose >= 10
   import features (some broken in both parsers, some pefile-only: its 8,192-import cap on GAMMA's injected imports,
   stricter import parsing). Without them PV keeps 1,341. On the evaluation set, 20 of the 1,000 malware have their
   first section at offset 0. (b) **Sample size**: PV drops a feature once any output lowers it (kept: 100 training
   malware ~1,450; 400 ~990; 1,000 ~640; 10,000 201; Gimenez et al. built from ~1,033 vectors, the pilot from 3,183).
   Diagnostics: `artifacts/scaleup/diag/pv-scale/`, `pv_scale.py`, `pv_broken.py`, `not_pe_why.py`,
   `imports_lost_why.py`. *Open (user, session 85):* one validity rule for the whole paper (an output counts, as an
   evasion and as a defense's training evidence, only if it is valid; its exact form to be discussed); the attack
   failures are too many to ignore (shift bug ~2-4% of files): investigate fixes before deciding (e.g. patching the
   shift to insert where section content starts, checked byte-identical on files it already handled); every defense
   learned from the material then retrained and re-attacked.
   **Deferred experiment (approved by the user, run after the above): PV's usable features against sample size**, for
   an appendix that explains why PV works less well than prior work suggests. On the cleaned material: (1) PV's kept
   features against the number of training malware observed, 50 to 10,000 on a log scale, 20 random draws per size,
   with confidence bands; (2) a model that predicts the curve: per feature j its lowering rate p_j (the share of
   training malware some output of which lowers j), expected kept features E[K(n)] = sum_j (1 - p_j)^n, compared with
   (1); (3) PV retrained at ~5 sizes x 3 draws, TPR at 1% FPR against n (~15 GBDTs, ~2 h; place Gimenez et al.'s
   ~1,033 vectors and the pilot's 3,183 on the axis); (4) which feature groups go first, and the raw against the cleaned
   material's curve. Starting points: `artifacts/scaleup/diag/pv_scale.py` (the rough curve), `pipeline/6-results/pv_hole.py`.
   *Fixes investigated (session 85, `artifacts/scaleup/diag/shift_fix.py`, job 1138581):* inserting the content shift's
   padding at the smallest non-zero section offset (where section content starts) instead of the first section's
   offset gives, on 300 random training malware, output byte-identical to upstream's (300/300); on the 358 broken files,
   354 now parse in pefile and LIEF with every section's bytes intact at its new offset (4 stay broken, as upstream).
   Because the fix changes nothing where upstream worked, only the broken (attack, file) pairs need re-running. The 45
   invalid-e_lfanew outputs come from files whose PE header overlaps the DOS header (e_lfanew 0x4-0x10, below 0x40):
   the DOS extension inserts bytes inside the DOS header, in front of the e_lfanew field itself; such a file has no
   DOS stub to extend (not applicable, ~25 of 10,000 training malware). *Decided and done (user):* the shift patched
   (5170936; end to end, job 1140273: byte-identical to the material on 30 normal files x 4 attacks, every output of 30
   previously broken files parses); the DOS-header attacks not applicable to those files (`dos_check.parquet`); **one
   validity rule for the paper** (b87fec6, `provexp.attacks.validity`): an output counts as an evasion, as a defense's
   training example, and as evidence that a feature can be lowered only if pefile and LIEF both read it and neither
   loses a section, an imported DLL or an imported function the original had; a start file a parser does not read is
   not applicable to any attack (`unreadable.parquet`); the reason names the parser, and "pefile only" rejections are
   the extractor's quirks to fix at the source (user: a misread file must not propagate). The soundness check still
   counts every edit. Checked on stored outputs (job 1141836): all 785 flagged rejected; 42 of 2,000 random (38 both
   parsers, 4 pefile only). Rerun from the catalogue check and the material on (`logs/submit-20261118-s85.txt`).

   (18) **GAMMA's LIEF rebuild and the validity rule's count gap (session 101).** The guaranteed detectors' four toolkit
   evasions are outside the threat model through LIEF's relayout (no soundness failure); the count-based validity rule
   misses losses hidden by additions in ~1-2% of GAMMA outputs. *Decided (user):* GAMMA's chosen edits written by our
   byte-level writers, with a header-growth variant of `shf` added to the catalogue (a shift); the validity rule
   compares sets; reruns of the toolkit, the material, the learned defenses and their attacks after; the current
   round's numbers go into the manuscript meanwhile. Record and plan: `docs/evidence/gamma-lief-relayout.md`.

   (19) **Header growth, a fifth layout clause, every training file in the store (session 102).** *Decided (user):*
   header growth is a fourteenth operation, `hgr` (in M_shift and M_full; its gap joins the headers), not a variant of
   `shf`; the debug entries' file offsets stay stale (raising them writes body bytes). A fifth `plain_layout` clause,
   the section table ends within SizeOfHeaders, closes the population table's only violations (two files of the
   catalogue check's 2,000, `ext` and `shf`). The file store holds all 20,000 training files and the derivation reads
   from it. Reruns of the derivation and the catalogue check submitted (1243542, 1243543). Record:
   `docs/evidence/gamma-lief-relayout.md`, section 5.
