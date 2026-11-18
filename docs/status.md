# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-40 in `docs/archive/status-log-2026-11-10-to-11.md`, sessions
41-42 in `docs/archive/status-log-2026-11-12.md`, sessions 43-54 in
`docs/archive/status-log-2026-11-12-to-13-s43-54.md`, sessions 55-58 in `docs/archive/status-log-2026-11-13-s55-58.md`, sessions 59-60 in
`docs/archive/status-log-2026-11-13-s59-60.md`, sessions 61-62 in `docs/archive/status-log-2026-11-14-s61-62.md`, session 63
in `docs/archive/status-log-2026-11-14-s63.md`, sessions 64-65 in `docs/archive/status-log-2026-11-14-s64-65.md`, sessions 66-76 in
`docs/archive/status-log-2026-11-15-to-16-s66-76.md`).

## Current state (2026-11-18, through session 85)

- **Scale-up running on tigris (session 74).** Setup done (`SETUP.md`, `pipeline/systems/tigris.sh`); everything is
  submitted by `bash pipeline/submit.sh` (SLURM dependencies; `3-directions/gate` before the detectors). Done:
  featurization (sums, expert), the file store, the derived tables, population, item checks, escapes, deviations. The
  gate stopped the chain on the derived check (PLAN.md decision 12: the training table is a strict superset of the
  evaluation set's, 361 cells, 98 directions); the user chose the training table. Also done: `train` (five detectors;
  unconstrained test AUC 0.998) and `price-list`. The first resubmission failed on two bugs, both fixed. The second
  (session 77) finished the catalogue check, hand table, trial table, trial detector and the defenses' material, but
  SLURM marked the material OUT_OF_MEMORY: GAMMA runs lost to LIEF's runaway rebuild, now prevented (PLAN.md step 3
  (13)). Session 78: the repair finished (79,121 valid rows, 216 not applicable); the learned defenses' GBDTs are
  trained, the nine ERDALT models finish ~2026-11-17 midnight. Session 81: a thread overload (SLURM's
  `OMP_NUM_THREADS` = cores kept by `common.sh`) killed `iterated`'s workers and MAB-Malware `zainab`'s shell; fixed,
  both restarted; the adaptive search's setup now runs over the workers (PLAN.md step 3 (15)). `iterated` round 1 and
  `iterated-1` done (none lost), round 2 running; MAB-Malware `expert` rerun with the full donor set, `zainab`
  running; the rest waits on ERDALT and `iterated`. **Session 82:** `iterated` finished (`iterated-2`; round 2: 972
  detected, 515 evaded) and MAB-Malware `zainab` finished; the scale-up now reads every file from the file store
  (`FILE_STORE`), stopping if it or a file is missing (c7481c3). **ERDALT collapses at scale** (all nine models:
  validation AUC 0.85-0.87 at epoch 0-1, ~0.69-0.75 from epoch 40 on, the < 5 violations criterion never met); its
  own track (`docs/resume-prompt-erdalt.md`). The other detectors' attacks were resubmitted without ERDALT and run
  apart from it (`toolkit` 1046138, `adaptive` 1046139, MAB-Malware `ours` 1046140; aaefd75); ERDALT's attacks and
  `6-results` are held. PLAN.md step 3 (16). **Session 85:** `toolkit` (19 tasks) and `adaptive` (81) finished;
  MAB-Malware `ours` crashed on two zero-section malware (upstream bug, patched in 455f121) and was resubmitted
  (1131288). Open: 3 adaptive searches lost and silently dropped (diagnostic 1131285), and **PV detects 5 of the
  1,000 evaluation malware** (test AUC 0.61).
- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only). **Session 74 (the theory session):** proofs audited (correct; seven
  small corrections applied); two additions to §3.3, each approved after a brief look and not yet read closely by the
  user: **Lemma 1 (*Closure*)**, a population bounded by features the table does not allow to rise is closed
  (f2f1fcf), and **the readout rule**, one rule in place of Table 1's six, by the sums a readout rises and falls with
  (c2fee51). Record: `docs/evidence/theory-analysis.md`.
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
- **§6 Related Work (session 84): cut to 1,284 words** (from 1,843; mock 1,000), the user: "a reasonably appropriate
  length". Paragraphs: *Problem-space attacks* (Šrndić and Laskov reworded), *Constraints over features* (Sheatsley
  et al. corrected, Labaca-Castro et al. added), *Hardening by retraining* and *Monotone and verified detectors* (the
  old *Robust and monotone detectors* split; Chen et al. 2021 cost-aware trees and Wang et al. 2022 added,
  Tsingenopoulos et al. reworded), *Certified defenses* (Gibert et al. 2023 beside DRSM, Calzavara et al. moved in),
  *Incremental computation* (provenance semirings dropped). The plan and its source checks:
  `docs/archive/related-work-plan-2026-11-17-s84.md`.
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
  starting point (`docs/archive/resume-prompt-2026-11-16-head-node.md` §4).
- **Optimization (session 69): done, bit-identical.** The adaptive search's candidate ~3x cheaper (391 -> 127 s on the
  profiling slice; ~7-9k -> ~2.5-3k CPU-h at the scale-up); sums extraction 120 -> 78 ms per file; a file store
  (`2-features/file-store`, SQLite beside the lists) replaces ~25 min of SimpleDB loading per attack task.
- **The two open questions (session 70): decided.** The derived tables are built from training files
  (`tr.parquet`) and rebuilt from the evaluation set as a check (`3-directions/derived`: `compare_tables.py`,
  `3-directions/check/`); iterated adversarial training starts from the adversarially trained detector, as scripted.
  PLAN.md step 3 (g), items 10-11. No protocol question is open before the cluster.

## Waiting on the user

- **The scale-up's attacks without ERDALT (session 85).** `toolkit` 1046138 and `adaptive` 1046139 finished;
  MAB-Malware `ours` resubmitted as 1131288 (record `logs/submit-*-no-erdalt.txt`). Next:
  `docs/resume-prompt-experiments.md`.
- **PV at scale is nearly blind; why, and what to do (the user decides; session 85).** PV keeps 201 features (pilot
  ~1,490), test AUC 0.61, 5/1,000 evaluation malware at 1% FPR (pilot 26.3% TPR). Diagnostics
  (`artifacts/scaleup/diag/pv-scale/{report,broken}.json`): (1) **broken outputs**: 894 of the 79,121 material
  outputs (1.1%; mostly the two shift attacks, 358 each) are no longer read as a PE (`general:is_pe` falls) or lose
  >= 10 import features; each "lowers" hundreds of features to zero, and PV drops any feature one output lowers.
  Without them PV keeps 1,341. The material's "valid" means only that the attack ran; adversarial training, ERDALT and
  `iterated` also train on these outputs. (2) **sample size**: kept falls with the training malware observed (100
  files: ~1,450; 400: ~990; 1,000: ~640; 10,000: 201). (3) 1,347 of the 1,496 features no M_full edit can lower are
  lowered by some output; without the broken outputs 217 (layout moves of the shift and LIEF-rebuilding attacks,
  outside M_full). Not yet measured: PV's detection without the broken outputs (expect near the pilot's ~26%), and a
  detection-against-sample-size curve. Proposed: material filtered to outputs still read as a PE with their imports
  (the same rule for every learned defense, or PV only), PV and its folds retrained (minutes) and re-attacked, the
  curve for an appendix.
- **Three adaptive searches lost (session 85).** Shards 6 and 14 (every escape) had 3 (monotone detector, file)
  searches with no result 45 min after the last other search finished; they were dropped silently. Decided (user):
  a one-hour limit, the files discarded and reported (fine while fewer than 10); done in ec2a5bd (lost.parquet,
  `discarded` in 6-results). Diagnostic 1131285 (5 h limit) tells whether they are slow or dying; the 8 affected shards
  have no lost.parquet yet (write it from the diagnostic, or rerun those shards).
- **ERDALT (the user, with the ERDALT track):** every model collapsed (validation AUC ~0.70; criterion never met).
  Leading hypothesis from the code: the violation penalty is a sum over all 79,121 vectors while BCE is a batch mean,
  so it dominates from the first step (~25x the pilot's vectors). Diagnose with short runs, then decide: report as
  specified, retrain with a fix, or retrain at their scale. `docs/resume-prompt-erdalt.md`.
- Number-free rebuttal text fixes (R4, R5, R15, R21) are step 4 (while the scale-up runs).
- **Bounds on size: the mathematics is written; the user decides, with Opus, what enters the manuscript**
  (`theory-analysis.md`, parts G and H; session 76; next theory session: `docs/resume-prompt-theory.md`).
  **To think through first: H.5** (with directions alone, a strictly monotone score loses no guaranteed detection
  against any relaxed one). Does it go beside Corollary 1, and may §5.4's price then be read as the price of the
  guarantee under the table and not of the model class? It holds for what a score can represent, not for what
  training finds, and it is close to the cost-of-robustness work closed in sessions 71-73; the literature has not
  been searched for it. Then: a discussion paragraph on what the directions discard; a subsection for the bounds
  only with a result behind it. On EMBER at the paper's budget nothing can be shown (read from the pilot's table;
  the scale-up's price list and derived table are on tigris, unread). A budget curve would be a new experiment (the
  user's call).
- **The user's close read of Lemma 1 and the readout rule** (§3.3, Table 1, Appendix C), when convenient.
- **Follow-ups from session 74, none started** (PLAN.md, next step 8):
  - instance-level work for Lemma 1: the population's clauses as counts over items, the derived table rebuilt, the
    nine in-place and append operations confirmed, the four layout-moving ones decided; §4.4's "closure is checked"
    changes only then;
  - `monotone_violations` called in `4-detectors/train` before the scale-up trains, so that §5.1's blue sentence
    (proof note 5, `% SYNTHETIC, TO VERIFY EXPERIMENTALLY`) can be confirmed or reworded;
  - optional: `reach.py`'s rule for a normalized bin is the old, looser one (sound; same table under free content).
- **`make check` reports one overfull vertical box** (1 pt, the last pages of Appendix D) since c2fee51: the text
  above reflowed. Left for the next edit of Appendix D.

## Scheduled (in order; PLAN.md, next steps)

1. ~~The 4 MB-truncation decision~~ (done, session 46), ~~the full simulated review~~ (run; discussed sessions 48-61),
   ~~R7's widening~~ (done, sessions 53-62), ~~the extractor question~~ (decided, session 62: stay on pefile).
2. ~~The final review/rebuttal revisit~~ (done, session 63: nothing else before the scale-up).
3. The scale-up (PLAN.md step 3): ~~the refactoring session~~ (done, session 64), ~~the extractor audit pass~~ (done,
   session 65; decided and applied in session 66),
   ~~the protocol items~~ (decided, session 67), ~~the remaining `run.sh` steps~~ (done, session 68), ~~lightweight
   optimization of the hot spots~~ (done, session 69), ~~the two open questions~~ (decided, session 70), ~~the
   head-node session~~ (done, session 74); running. Since session 82 in two tracks: the experiments
   (`docs/resume-prompt-experiments.md`) and ERDALT (`docs/resume-prompt-erdalt.md`).
4. While it runs: §2's closing and contribution 4 aligned with §5; the number-free text fixes R4, R5, R15, R21.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

Two sessions were numbered 74: the head node on tigris, and the theory session. Since session 82 each track has its
own resume prompt: `docs/resume-prompt-experiments.md` (the cluster), `docs/resume-prompt-erdalt.md` (ERDALT),
`docs/resume-prompt-theory.md` (theory), `docs/resume-prompt-writing.md` (the manuscript); `docs/resume-prompt.md` holds
general work and indexes them.

- **2026-11-18 (session 85, Opus, scale-up track): toolkit and adaptive done; MAB-Malware fixed and resubmitted.**
  `toolkit` (19 tasks, slowest 4 h 44 min, 70% of its cores, 44 GiB of 100) and `adaptive` (81 tasks, slowest 74 min,
  39% of its cores, 63 GiB of 100) finished, no errors. MAB-Malware `ours` (1046140) crashed in 3 min: 2 of the 1,000
  evaluation malware have NumberOfSections 0 and upstream's section-adding action indexed an empty section table
  (2 more declare 4 sections pefile cannot read, already handled upstream). Patched to return such files unchanged,
  and each run now clears its work directory, which held the crashed run's evasive files (455f121; diagnostic
  1131138: the 4 files, SA pulled on them, two runs identical, MAB tests pass); resubmitted as 1131288. Found: PV
  detects 5/1,000 (test AUC 0.61); 3 adaptive searches lost and dropped (diagnostic 1131285). MAB-Malware `zainab`
  read: at Zainab et al.'s setting (0.1% FPR, no byte cap) the unconstrained detector detects 867/1,000 and the attack
  evades 455 (52%; they report 83%; Appendix D's sentence still has the pilot's numbers). Continued: the user
  approved right-sized headers and a one-hour limit with lost runs discarded and reported (ec2a5bd: toolkit 8 h,
  64 GB; adaptive 16 cores, 3 h, 64 GB, since a shard's longest search outlasted its work over 36 cores). Toolkit's
  low CPU: the leave-one-out folds (5-23 files on 36 cores) and the debug-entry escape task (41%, cause not found;
  shared a 144-core node with two other toolkit tasks). PV's collapse traced to broken outputs and sample size
  (*Waiting on the user*). MAB `ours` 1131288 running (56 GB at 20 min).

- **2026-11-17 (session 82, Opus, scale-up track): the file store, ERDALT's collapse, the attacks without ERDALT.**
  `iterated` finished (round 2: 972 detected, 515 evaded; 282 GiB of 300 at peak). Its rounds spent ~20 min each
  before searching: the loaders found the file store only beside a file list, and `iterated`'s round lists live in
  their own folders, so 1,000 files a round came silently from the SimpleDB (a shard decompressed per file). Fixed at
  the user's direction: one location, `FILE_STORE` (`pipeline/common.sh`), and no fallback: a missing store or file
  stops the job (c7481c3; verified on tigris: 1,100 files in 0.8 s, bytes identical, old and new adaptive search
  identical). ERDALT read: all nine models collapse from AUC ~0.86 at epoch 1 to ~0.70 and never meet the criterion;
  Claude first described the causes loosely (listing their own schedule as if ours); checked against the port, the
  method is theirs apart from batch 256, the monotone output layer and validation-split selection; the leading
  hypothesis is the summed penalty over 25x the vectors. The user set ERDALT aside for its own session and let the
  models finish; the other attacks were cancelled and resubmitted without ERDALT (aaefd75: `TAG`, the toolkit's
  leave-one-out split by family, a duplicate guard in the tables). The user was frustrated by long waits on
  background cluster work (a verification job hung 25 min on a stdin script with a spawn pool while Claude waited):
  do not watch the queue; check once and hand back. The resume prompt split into tracks (user).

- **2026-11-17 (session 84, Opus, manuscript): §6 cut by 30%, paragraph by paragraph, every change approved.**
  Drafted without the paper-prose skill (user's choice). 1,843 -> 1,284 words. Commits: 5326f61 (Šrndić and Laskov
  said accurately: side effects not accountable a priori, files built after the feature-space attack), 2508e74
  (*Constraints over features* 427 -> 321; Sheatsley et al. corrected; Labaca-Castro et al. added, arXiv only),
  9bf5471 (*Hardening by retraining* and *Monotone and verified detectors*, 768 -> 480; Chen et al. 2021, Wang et al.
  2022 added; the first draft was judged choppy and smoothed), 078d3dd (*Certified defenses*; Gibert et al. 2023;
  Calzavara et al. moved in; "whatever the edits mean" replaced as unclear), 083cf1b (*Incremental computation*, 297
  -> 118). New bib entries: `labaca2022realizable`, `chen2021cost`, `wang2022robust`, `gibert2023certified`. The user
  accepted missing a few targets ("significant progress" is what counts). Next writing session: the humanistic review
  and polish of §3, §4, §5 (`docs/resume-prompt-writing.md`).
- **2026-11-17 (session 83, Opus, manuscript).** Holistic assessment of §6 and a plan to cut it 30-40%: approved by
  the user ("excellent"), recorded in `docs/related-work-plan.md` with the user's guidance, answers, and source checks
  (Sheatsley et al.'s sentence in §6 is unsupported; Šrndić and Laskov's "worked this way" is inaccurate; Labaca-Castro
  et al., Chen et al. 2021, Gibert et al. 2023 to add). Applying it failed: *Problem-space attacks* cut to ~85 words was
  rejected outright (the original stays, user: it read smoothly and emphasized the right ideas), and *Constraints over
  features* lost only 11 words net against a planned 140 (rejected as pointless). All manuscript edits were discarded;
  §6 is as in `d9fc35d`. The user asked whether the paper-prose skill is holding the writing back (answered in the
  terminal; the user's decision waits). Next: `docs/resume-prompt-writing.md`, the plan paragraph by paragraph.
- **2026-11-17 (session 82, Sonnet, manuscript).** C.4(c) done, one citation at a time with the user's verdict on each:
  Kantchelian et al. (the constraint-taking feature-space attacks in §6, 81b6c45); Lucas et al. 2024 (GreedyBlock,
  no adversarial examples, 91% less computation) beside the 2023 adversarial training, whose sentence now says how
  that was made practical (over 140 workers, epoch from months to one to ten days; e79970a); Tsingenopoulos et al.
  (new bib entry `tsingenopoulos2024train`, arXiv 2402.19027; 501e463). **Tsingenopoulos et al. is the closest work;
  close read done** (findings in `docs/resume-prompt-writing.md`, *Open*): the guarantee is a definition estimated by
  an RL attacker, the capability set and the side-effect propagation are hand-written, the edits are on the report
  not on binaries. A rewording of §6's sentence is proposed, not applied. The user chose the humanistic review for the
  next session: order §6, §3, §4, §5, §2; length is a later, separate pass (candidates to `docs/review-cuts.md`);
  Sonnet, because the user was at 92% of the week's usage. Still open: the Gibert et al. papers (not in `papers/`),
  Giri et al.'s author names, C.6.
- **2026-11-17 (session 82, later, Sonnet, manuscript): the first §6 pass, then a change of plan.** The humanistic
  pass on *Problem-space attacks* and *Constraints over features* gave five findings; the user said to apply all, and
  all five are in `_g_related_work.tex`, **committed with the user's approval (`d9fc35d`)** (the Kantchelian sentence moved
  beside the other methods that take constraints; "nothing checks" narrowed to "None of these derives the constraints
  from the extractor itself"; a paragraph break at "All three take the constraints as input"; the first paragraph names
  Pierazzi et al.'s condition and says what we compute; "realizable" for the paper's notion, "problem-space examples"
  for Dyrmishi et al.'s and Lucas et al.'s). Quote-checked: Pierazzi et al. and Kantchelian et al.; not in `papers/`:
  Šrndić and Laskov, FENCE, Sheatsley et al. **The user then judged §6 too long to be useful (1,843 words; the mock
  says 1,000) and asked for the next session, on Opus, to assess its structure, organization and content as a whole and
  to plan a 30-40% cut before any further sentence-level review.** The resume prompt is renamed
  `docs/resume-prompt-writing.md` (was `-sonnet`) and starts with that task; the order §3, §4, §5, §2 follows it.
- **2026-11-17 (session 81, Opus, scale-up track): the thread overload, MAB-Malware's shell, a parallel setup.**
  MAB-Malware `zainab` crashed (a `cp` that never ran) and `iterated` was losing workers; both on gg-a-016, where the
  user's threads reached 16,082 of 16,384: SLURM's `OMP_NUM_THREADS` = cores, kept by `common.sh`, gave each of 72
  workers ~380 threads. Fixed in `common.sh` (one thread per process; a startup line prints the settings), MAB's
  shell commands checked, donor names with '/' kept (user; 484 -> 501 sections), `iterated` cancelled and restarted
  at 300 GB (user), `expert` and `zainab` rerun. The adaptive search's per-file setup moved into its own worker pool
  (the user's design; verified identical to the old code on a 40-file search) before round 2. PLAN.md step 3 (15).
  The user was angry at the run of avoidable cluster failures caused by unchecked assumptions about the jobs'
  environment and serial setup code; two CLAUDE.md rules added (parallel by design; read the job's environment).
- **2026-11-17 (session 80, Sonnet, small tasks while the scale-up runs).** Committed: A.1 the 1 pt overfull vbox (a
  column break before Appendix E, with a comment; drop it once E and F hold text; 538c430); A.3 array logs
  `%x_%A_%a.out` for MAB-Malware's header and `learned`'s ERDALT array in `submit.sh` (8fefbc6); B.1
  `4-detectors/monotone-check` (read-only; run on tigris with `sbatch pipeline/4-detectors/monotone-check/run.sh`; not
  in `submit.sh`; pilot models: 0 violating leaf pairs in all seven monotone GBDTs, 10 s) (fee717d). A.2 was done in
  session 79. **Manuscript, applied one piece at a time with the user's verdict on each** (after a first attempt that
  applied everything at once and was discarded at the user's request): C.1 (R4, §2's "broad class") **rejected**: §3.1
  defines the extractor algebraically; C.2 (R5) §2 gives Pierazzi et al.'s closed-form reason, **accepted** (93ea886),
  §6's minimal-app credit **rejected**; C.3 (R15) the attacker named, the code-level exclusion reworded against Lucas
  et al. 2021 in §4.3, **accepted** (e3b98d3); C.4(a) the 100 queries attributed to the attack script Gimenez et al.
  released (their `low_budget = True`: populations of 10, 10 iterations; the 5% or 512 KB byte cap is not in their
  code, so it is ours), **accepted** (0ac171d), **the budget may be reconsidered later** (user); C.4(b) a *Certified
  defenses* paragraph in §6 (RS-Del, DRSM, Giri et al.; three bib entries; the user asked to keep the contrast with
  ours short), **accepted** (51b166c). Still to do: C.4(c), C.5, and the C.6 note (below); see
  `docs/resume-prompt-writing.md`. **Findings:** `papers/gibert2024assessing.pdf` is the packing study (bib key
  `gibert2025assessing`), not the certified-detector papers of Gibert et al. (AISec 2023, IEEE Access 2024, as listed by
  Giri et al.), which are not in `papers/` (`% TODO cite` in §6); the R17 decision (no universality sentence) was
  already recorded in the triage table. Giri et al.'s bib author names ("K. A., Asmitha", "P., Vinod") are as printed;
  check them. **C.6 note, for the motivation discussion (nothing edited):** §2's closing says `\Cref{sec:evaluation}`
  "uses them to attack malware detectors and to build robust ones". §5 shows three findings: hand analysis misses side
  effects that come from how the parser locates structures; defenses learned from observed attacks inherit those
  attacks' blind spots; with the directions known, robustness against the whole threat model costs a measured few
  points of detection. In §5 the attack is an instrument that tests the directions and the defenses, not a result.
  `docs/paper-mock.md`'s contribution 4 already states the three findings; only the "four to six points" number is
  stale (read it after the scale-up).
- **2026-11-17 (session 78, Opus, scale-up track): check-in, the denominator, and resources.** The repair
  finished (79,121 valid, 216 not applicable). The user chose the per-attack denominator of the files an attack
  applies to (eec804b) and tighter walltimes for the finished steps (36faebe). The user found `learned` holding 36
  cores for ~30 h of single-core ERDALT training ("moronic"): split into a GBDT CPU job and a GPU array (23ac418);
  MAB-Malware and `6-results` were oversized too, cancelled while pending and resubmitted right-sized (9f91013);
  `iterated`'s dependency removed so it started ~14 h early. New CLAUDE.md rule: request what a job uses for most of
  its life, split long phases with very different needs, review use against requests after jobs finish. Noted:
  ERDALT's low validation AUC at scale (to read); MAB skips 2 of 486 donor sections (names with `/`); array tasks
  share one SLURM `.out` (use `%x_%A_%a.out`).

- **2026-11-16 (session 77, Opus, scale-up track): the GAMMA OOM traced and prevented.** The material's array
  (1018609) finished every shard but was marked OUT_OF_MEMORY: 224 GAMMA runs on 117 files lost to killed workers,
  45-min stalls. First recommended accepting them as failures; the user wanted the failure prevented and not counted.
  Diagnostic jobs (`artifacts/scaleup/diag/gamma-oom/`): LIEF's rebuild runs away on malformed files (38 of 40 lost
  files fail a round trip, 0 of 40 controls); the two others are heavy (~7 GB, 4-8 min) and were collateral.
  `provexp.attacks.lief_check` (430ef83): once per start file, GAMMA not applicable where it fails, in the toolkit
  and the material; `--repair` for the finished shards; smoke-tested. PLAN.md step 3 (13). Open: the per-attack
  denominator in `6-results`. Walltime limits to be shortened as jobs finish (the user).
