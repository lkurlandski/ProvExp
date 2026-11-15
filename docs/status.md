# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-40 in `docs/archive/status-log-2026-11-10-to-11.md`, sessions
41-42 in `docs/archive/status-log-2026-11-12.md`, sessions 43-54 in
`docs/archive/status-log-2026-11-12-to-13-s43-54.md`, sessions 55-58 in `docs/archive/status-log-2026-11-13-s55-58.md`, sessions 59-60 in
`docs/archive/status-log-2026-11-13-s59-60.md`, sessions 61-62 in `docs/archive/status-log-2026-11-14-s61-62.md`).

## Current state (2026-11-15, through session 68)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4:** drafted in the new structure (lead, 4.1-4.4, Appendix D "The EMBER Instance"), then revised in session 38
  after Claude's review with the `humanistic-paper-review` skill (all eight findings applied; 4.3 split into
  *Operations* and *Signature*; 4.4 reordered). Second, lightweight review in session 40 (three findings, all
  applied: 4.3.2 states what the sample-read signature rests on; closure "checked rather than proven"). §4 is in good
  shape. About 1,500 words against ~1,000; shortening with §5 later.
- **§5:** three findings (PLAN.md, decision 10; plan in `docs/paper-mock.md`, §5), fully drafted, no blue values.
  Reviewed by Claude with the `humanistic-paper-review` skill in session 41b, one subsection per pass, every finding
  approved by the user and applied (ce4ba21, f8baea5, 1053bf7, e8b0335): each subsection's lead now answers its
  question; "the computation" named; 5.1 introduces the unconstrained detector; 5.2's hand table counts eight errors
  with the certificate table apart, the two published analyses in their own paragraphs; 5.3 says the derived table
  marks 142 features as ones an edit *may* lower (20 shown); 5.4's 0.1% breakdown keeps only what clears retraining
  noise; Table 2's attack names and "population" throughout, no "pilot". The user has not read §5 end to end.
  Holistic review in session 42 (findings 1-4 applied, 68f6385, 49d879d). Tables 3 and 4 remade in session 43
  (7788592, 52e07cc): one column each, data only, one-line captions; the user: "good enough". 5.3 got its own table in
  session 44 (d87603f): Table 4, the learned defenses; the detectors table is now Table 5.
- **§5.3** is drafted (session 39) from the claim agreed in session 34 (`docs/evidence/section-5.3-design.md` §10.5, which
  stays the record of how the design came about). Learned-region paragraph cut, no audit table for now (tables
  remade later), no seed or protocol-hygiene details in the paper (user). Every learned defense is built from run 133's
  3,183 outputs; PV evaded 4/9 by one rename, 26.3% TPR; ERDALT 24/29 by its own attack; adversarial training 12/50
  and 23/50; leave-one-out per fold in Appendix D.
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in
  PLAN.md, next step 5. Run 131 (leave-one-out) finished: PV 5/21 on gamma_api, 0 elsewhere; ERDALT high on
  gamma_api and header_fields; ERDALT-8 adaptive 17/24. Runs 132 (coverage by source, seed smoke), 133 (§5.3 Phase
  2, ~4.8 h) and 134 (PV-clean, PV-free; Claude, ~3 min) done and read. **Run 135** (leave-one-out from run 133's
  outputs) finished 2026-11-11 19:54 (~3.4 h) and read in session 40: PV 0 evaded in all eight folds; ERDALT 25/29
  when GAMMA imports is held out, 0-2 in the other seven (header_fields 2, not the predicted ~10). Results in its
  header and in `docs/evidence/section-5.3-design.md`'s log.
- **Files and population (session 46):** every split uses only the files our copy holds in full (below 4,000,000
  bytes), stated once in §5.1's Setup; §4.4's population is the complete files with a plain layout (PLAN.md, decision
  8 (iv)). Most numbers in §5 and Appendix D are still pilot values on all files (`% PROTOCOL` comments): the scale-up
  replaces the detector results, a recount from stored outputs the checks (PLAN.md, open items).
- **Simulated review (session 47):** designed and written as a reusable procedure (`docs/reviews/review-prompt.md`,
  `docs/reviews/process/`): four independent reviewers run headless outside the repository (A formal methods, B
  adversarial malware, C robust and certified ML, D systems security; Opus 5.5, high effort), seeing only the PDF, a
  note to reviewers and `papers/`; then a meta-reviewer with full access checks their findings, works through the
  checklist, writes the risk register and what the scale-up must include. Knobs in `config.sh`. **Run by the user**
  after session 47 (`docs/reviews/2026-11-12-body/`): A Weak accept, B Weak reject, C Weak reject, D Weak accept;
  likely outcome reject or major revision. Register R1-R21; top risks R7 (routing around the population), R1 (attacks
  below published strength; header-field edits never used by the adaptive attack), R2 (premises tested, not proven).
  Discussed in session 48 up to R7 only; the rest of the register is untriaged.
- **R7, leaving the population (session 48):** analysis, options and decision in `docs/evidence/r7-population-escape.md`.
  Run 137 (escape audit): single loader-ignored field writes (certificate or debug entry past the end, SizeOfImage
  raised) take 150 of 150 population files out. Decision (user): no router; one monotone detector scores every file,
  proven on the population and measured outside it. **Run 138** (the escape pilot, ~5-6 h) scripted for the user;
  the paper is not changed until it is read. **Step 1 read in session 52** (R7 record §7): one signed file evades
  both monotone detectors (an append restores the signature the certificate escape had broken); option 5 for the
  certificate clause accepted by the user, with caution (more holes may surface at the scale-up).
- **R1, attack strength (session 49):** decision 12. MAB-Malware vendored and driven by `scripts/mab_attack.py`
  (tested equal to upstream's own hand-over); run 139 scripted for the user; §5, Tables 4-5 ("evaded by any attack")
  and the new per-attack Table 11 carry its predicted values in blue. The adaptive attack scores by extraction at the
  scale-up (`--score real`); §2 unchanged (user). Widen first, then scale (user). **Run 139 read in session 51**
  (reading in its header and PLAN.md, decision 12): no silent no-ops; unconstrained full set 0/49 (16 evasive outputs
  over the byte budget), PV 7/9 by renames alone, both monotone full-model detectors 0 with their score never below
  the clean score (outside the population too). Measured values in Tables 4, 5 and 11; MAB-Malware's role in §5
  changed with the user's approval (5dc17b5): evidence that the monotone scores never fall, no longer an attack that
  breaks the undefended detector; Appendix D compares its rate with Zainab et al.'s (0.1% FPR, no byte limit).
- **R6, prior work (session 50):** the works behind §3 read and related to Proposition 1, Theorem 1 and Corollary 1
  (`docs/evidence/r6-prior-work.md`). The user: credit what we build on without conceding each result ("the novelty
  ... is in putting them together"), one or two seminal works per idea. Applied (660ba90): Gray et al.'s maxima in
  §3.1, incremental view maintenance carried to features in §3.2, abstract interpretation (Cousot and Cousot) after
  Theorem 1, §6's wrong contrast with incremental parsing replaced (abstract interpretation, Calzavara et al., the one
  new bib entry). About 140 words added.
- **Documentation:** reorganized 2026-11-09, cleaned up 2026-11-12 (stale resume prompts, the §4 note archived; the
  §5.3 design doc moved to `docs/evidence/`); index `docs/README.md`.

- **R7 final form (session 53):** run 138 finished (step 2 held, 0/40 and 0/41); an end-to-end check from the
  unescaped originals showed the escape writes themselves are the hole (the debug write alone evades 3/40 and 4/41).
  The user chose the full widening: `ent` (certificate and debug entries, any value) in the threat model, their data
  allowed past the end (`a_directions.py --loose`); ten features two-sided; run 140: TPR at 1% FPR 89.6 -> 85.7 (sums),
  87.2 -> 83.4 (features), nearly all from the certificate entry (signature cloning). Debug-only alternative recorded.
- **R7 is done at pilot scale (sessions 53-62).** Full widening (`ent`, LIEF's overlay rule); run 143 read (the two
  `-loose` monotone detectors 0 evaded under every escape; unconstrained 47/47 by signature cloning); the paper's R7
  text written; blue values for the monotone toolkit/MAB cells until the scale-up. Session 62: the escape audit against
  the widened population found no new in-population escape (`r7-overlay-rule.md` §9), and pefile's parser caps were
  verified as an exactness gap, not a soundness hole (§10).
- **The extractor question is decided (session 62): stay on pefile.** The LIEF spike (§8) showed structures agree on
  99/100 pilot files and parsing is ~12-25% of our per-file time. Remaining before the scale-up's featurization: one
  deliberate audit pass with a deviations table in Appendix D (the caps and the always-constant features are the known
  entries).

- **Code (session 64): reorganized for the scale-up.** `pipeline/` (stages `setup`, `1-audit` ... `6-results`, one
  step per folder, `run.sh` with SLURM headers), library code in `src/provexp/` (no script imports another), plain
  detector names in `provexp.registry`, `SETUP.md`; the old direction's and A''s code removed (tag `pilot-final` keeps
  everything); `run/` is a historical record. Checked byte-identical against the old code
  (`pipeline/setup/identity_check.sh`). `pipeline/README.md` maps every paper result to its step: **every number in the
  paper comes from the scale-up** (user, session 64).
- **The extractor audit (sessions 65-66): decided and applied.** `docs/evidence/extractor-audit.md` §2. Fixed (pure
  additions, installed by `fix_quirks` in `features.py`, which replaces `merge_import_descriptors` at every
  patched-extractor call site and in `SumsFeatureExtractor`): thrember's directory loop now skips the entry named
  RESERVED, not the last one read (13/2,000 test files); three string patterns corrected (`registry_key`,
  `email_addr`, `.click(`; v3's names kept; 411/2,000). Kept and listed: the entry section on misaligned sections,
  alignment bits as flags, pefile's limits on imports and exports. Appendix D opens with *Changes to EMBER* and Table 8
  (counts on the 2,000 test files, blue until `1-audit/deviations` runs at the scale-up). The plain `PEFeatureExtractor()`
  still computes v3's released vectors (for `check_features.py`); the pilot's adversarial-training detector reads that
  unpatched store, which the scale-up's one training set replaces (PLAN.md step 3).
- **The scale-up's protocol (session 67): decided** (PLAN.md step 3 (g)). Evaluation set: 1,000 malware and 1,000
  benign complete test files (`pipeline/2-features/files`), also the audit's `FILES`; ~7-9k CPU-h for the attacks, no
  fallback needed. Every detector on the full training split's complete files (`--complete_only`), thresholds on the
  validation split, donors from training goodware (two disjoint sets of 100: the defenses' material and the trial's
  imports, the attacks on the evaluation set). The learned defenses' material once: the eight toolkit attacks on 10,000
  training malware, rows for every store and the binaries kept. Trial row learns from the evaluation set; iterated
  adversarial training 1,000 per round; MAB-Malware at both settings; escapes against three detectors with the
  adaptive search and the toolkit. Code for the lists, thresholds, donors, complete files and the attacks' `--protocol`
  committed; the remaining `run.sh` steps are listed in PLAN.md step 3 (g).
- **The scale-up's steps (session 68): every one has its `run.sh`**, smoke-tested on a small slice (the pilot's 10%
  stores and models trained on 20,000 files, a few malware): `4-detectors/{train,adversarial-training,learned,
  iterated,price-list}`, `3-directions/trial`, `5-attacks/{toolkit,adaptive,mab-malware}` (the long ones SLURM job
  arrays that resume), `6-results` (`scaleup_tables.py`, `coverage.py`, `erdalt_hole.py`); the order in
  `pipeline/README.md`; models under `4-detectors/<name>` (the registry's `scaleup` set). Bug fixed: the adaptive
  search's workers reloaded the pilot list under `--protocol scaleup` (session 67's change, which the pilot-protocol
  identity check could not see). Open for the user: the derived table's corpus, and iterated adversarial training's
  starting point (`docs/resume-prompt.md` §4).

## Waiting on the user

- **The head-node session** (`docs/resume-prompt.md`) needs the user at the cluster: `SETUP.md`, `check.sh`, the "TO
  CONFIRM" values, and each `run.sh`'s time, memory and GPUs. Then the user submits the steps in
  `pipeline/README.md`'s order. Number-free rebuttal text fixes (R4, R5, R15, R21) are step 4 (while the scale-up
  runs).
- **One choice made by Claude, open to the user's veto:** iterated adversarial training starts from the adversarially
  trained detector (the toolkit's material already appended), not from the unconstrained one, so its two rounds add
  the beam's outputs to the strongest learned baseline (`pipeline/4-detectors/iterated/run.sh`).

## Scheduled (in order; PLAN.md, next steps)

1. ~~The 4 MB-truncation decision~~ (done, session 46), ~~the full simulated review~~ (run; discussed sessions 48-61),
   ~~R7's widening~~ (done, sessions 53-62), ~~the extractor question~~ (decided, session 62: stay on pefile).
2. ~~The final review/rebuttal revisit~~ (done, session 63: nothing else before the scale-up).
3. The scale-up (PLAN.md step 3): ~~the refactoring session~~ (done, session 64), ~~the extractor audit pass~~ (done,
   session 65; decided and applied in session 66),
   ~~the protocol items~~ (decided, session 67), ~~the remaining `run.sh` steps~~ (done, session 68), then a
   head-node session on the cluster (next).
4. While it runs: §2's closing and contribution 4 aligned with §5; the number-free text fixes R4, R5, R15, R21.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

- **2026-11-15 (session 68): the scale-up's remaining `run.sh` steps.** Registry `scaleup` set (6d9dbd4); training
  (b21f4d7); the defenses' material and the learned defenses (4734d57: `attack_training.py` on the lists with shards,
  rows for the sums and expert stores checked equal to the zstd binaries' re-extraction, `pv_hole.py --exclude` so PV
  selects among EMBER's features, `--augment` of several directories); the trial row (6adba41, `--donor_list`); the
  price list (54b2b73); the toolkit with `--escape` and the attacks as job arrays, MAB-Malware's three settings, the
  identity check from an empty directory with the pilot's settings pinned; `6-results`. Smokes: every step ran end to
  end on small slices; coverage's `modeled` class gives 982 lowerable (the meta-review's R12 recount). Found while
  smoke-testing: the adaptive workers' pilot reload (fixed); after the debug-entry escape `gamma_api` stopped evading
  the smoke's unconstrained detector (LIEF's rebuild; noted in the resume prompt); `coverage.py` counted the
  re-encoding's sums as lowerable on the sums table's `-control` rows (fixed). Identity check: only session 66's recorded
  differences (the fixed string and directory features, the catalogue's counts, the manifests' commit, the escape row
  of `0485edc2...`).

- **2026-11-15 (session 67): the scale-up's protocol decided.** With the user, item by item (PLAN.md step 3 (g)):
  the evaluation set (1,000 + 1,000 complete test files; cost from the pilot's timings ~8-11 CPU-h per detected
  malware, ~7-9k in all), one training set (full split, complete files), thresholds on the validation split, donors
  from training goodware (two disjoint sets: R19 depends on the separation), the defenses' material once from 10,000
  training malware (user: "one and done", so more samples), the trial row from the evaluation set, iterated
  adversarial training 1,000 per round, escapes with adaptive and toolkit on three detectors. Lists drawn
  (`artifacts/scaleup/2-features/files/`: 333 malware families plus 209 unlabeled; the family cap leans malware to
  larger files, as before; the tr draw took 7 min, not the 3 predicted). Code (076e299, 2333496, and the protocol
  commit): `select_files.py --complete_only --donor_sets`, the trainers' `--complete_only` and validation
  predictions, `model_threshold`/`detection_at`, `load_attacked`, the attacks' `--protocol {pilot,scaleup}`; the audit
  steps default to the evaluation set (the catalogue check had defaulted to the pilot files), the escape audit to the
  whole population. Found: the trainers had never dropped truncated files (a PROTOCOL item; fixed by the flag).

- **2026-11-15 (session 66): the audit's decisions applied.** The user decided the five candidates: directory
  off-by-one fixed; entry section, alignment bits and pefile's early stops kept and listed; the string-pattern typos
  **fixed, all three** (against my recommendation to keep v3's: "we're already fixing a lot of bugs ... we might as
  well fix these obvious bugs"). Implemented as `DataDirectoriesReserved`, `StringExtractorFixed` and the installer
  `fix_quirks` (47201e2), with tests; the stale `scripts/item_checks.py` comment fixed. Identity check vs run 146:
  hypothesis held (the `ember2024` and `expert` stores identical; the sums store differs only in the fixed features,
  407/2,048 files; catalogue only in observed-cell counts), plus one adaptive row on `0485edc2...` from session 65's
  escape-write fix. Reference fixtures regenerated (sums only); full suite 1,737 passed. The deviations module now
  counts the string fix (411/2,000, 335 in the population; hypothesis ~400 held) and pefile's import error stop (26,
  more than the one case noted in session 65; most read what LIEF reads). Appendix D: *Changes to EMBER* and Table 8
  (635eb6b, plan and draft accepted as written; `array` package added for ragged columns). Docs 0bb9c55, f555d10.

- **2026-11-14 (session 65): the extractor audit pass.** Read all of thrember's extractor and the pefile rules its
  features rest on, against the three principles; counted each candidate on the 2,000 test files
  (`docs/evidence/extractor-audit.md`; `artifacts/experiments/deviations/2000/`). Hypothesis (each candidate at most a
  few percent, mostly incomplete files) held except the alignment bits (59 files) and the registry typo (93), both
  definitions rather than parser heuristics. New candidates: directory off-by-one (13/2,000, fix recommended), entry
  section on misaligned sections (3, keep), alignment bits as flags (59, keep), pefile's early stops in imports and
  exports (~12, keep with the caps), string-pattern typos (keep as v3; upstream items 11-12 drafted). Work needing no
  decision: `catalogue_checks.py --chained` (three sections then an append, item table carried forward; Appendix D's
  combined edits), `hand-table/witness_counts.py` (Table 3's files per error, by population; reproduces 650, 151, 37
  from pilot-era outputs), `1-audit/deviations` (the table's counts), `run.sh` for every audit step (smoke-tested on six
  files: all checks pass, chains exact). Found and fixed: the escape audit aborted on a pilot file because pefile's
  `write()` rewrote ~40 untouched bytes; the writes now patch their field (byte-identical on run 137's 900 writes).
  My first measurement script hung on a quadratic regex of my own; rerun without it. Commits 4458d06, 1b12cbc,
  8e8f8ca and the docs commit.

- **2026-11-14 (session 64): the refactoring.** Proposed tree and deletions agreed (user: `run/` a record with tag
  `pilot-final`; the A' code deleted, combined edits re-checked in the audit; MalConv kept; **every result in the paper
  at the scale-up's scale, pilot only for tests and explorations**, so the hand table, witnesses and leave-one-out get
  scale-up steps and trial-toolkit stays an exploration). Commits: b223fcd (49 old scripts, `explain/`, ablation,
  trigger, attack modules and their tests removed; `provenance.py`/`boxmatrix.py` kept: the instrumentation uses them),
  185212e (library code into `src/provexp/`: `attacks/`, `detectors.py`, `parallel.py`, `featuresets/ember2024/
  {edits,escapes,population,directions,hand}.py`), 3a6fba2 (`pipeline/`, registry, `SETUP.md`, `build_env.sh`,
  `check.sh` with a bit-exact featurization reference). **Checks:** run 146 (old code, run twice: agree but timing);
  the library move and the pipeline both identical to it on 61 outputs (featurization, both direction tables, a
  catalogue check, two extraction-scored adaptive searches, MAB-Malware) but timing and the manifests' commit; tests
  1,572 passed. Noted for later: duplicate writers (`edits.add_section` vs `attacks.adaptive.add_section`; the
  operation tuples in `adaptive` and `directions`) to merge under the identity check; featurize as a job array needs a
  step that creates the store before the tasks; one stale path in a `features.py` comment, kept so the file's hash
  matches the stored stores.

- **2026-11-14 (session 63, scale-up track): review revisit closed; the scale-up's shape agreed.** Nothing else is
  worth doing before the scale-up (user agreed): the number-dependent text fixes stay after it; R4, R5, R15, R21 move to
  step 4; three reporting duties (still-detected share of all attacked malware, R12's modeled-only counts, R15's gain
  share and R3's margins) and the audit pass as the first scale-up work added to PLAN.md step 3. **Decisions (user):**
  5,000 extraction-scored candidates for every detector; **one seed, more samples** (seeds wait for a final
  methodology); the user has shared SLURM clusters (sporc x86_64, tigris aarch64; config read from SSViT); a
  `pipeline/` reorganization with one `run.sh` per step (`#SBATCH` header, `sbatch` or `bash`), plain names, library
  code into `src/provexp/`, `SETUP.md`; executed in a dedicated refactoring session. PLAN.md step 3 (d)-(e).

- **2026-11-14 (session 63, R18 track): run 144 read; R18 decided.** The trial detector (directions learned by trying
  the twelve operations) is evaded on 26/44 pilot malware by the beam and 17/44 by MAB-Malware, trial-toolkit on
  13/20 and 3/20, the derived detector on 0/39 under both (score never falls). Audit (`trial_audit.py`, new `--mab`):
  every evasion carried by a feature trial never saw move (`regex_https://`; import buckets for trial-toolkit).
  Hypothesis: derived and trial parts held; trial-toolkit "a few" and MAB-Malware "few or none" failed (both in our
  favour). **Decisions (user):** the reading for §5's lead and §5.3 (text after the scale-up); a trial row in Table 5
  at the scale-up; iterated adversarial training in the scale-up (`ent` held out). `a1_adaptive.py --save_rows`
  applied. R18 has no open item before the scale-up.
