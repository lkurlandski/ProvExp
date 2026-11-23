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

## Current state (2026-11-23, through session 104)

- **Session 104 (experiments):** ERDALT's eight folds finished (2026-11-21); `hgr` merged (GAMMA through our writers
  is on `main`). The validity rule compares sets (commit 6452038): DLLs by lowercase name, functions by (DLL, name or
  ordinal), sections by virtual address (user; options weighed, content rejected). Checked: no kept output (1,217)
  loses a section address or changes verdict; on session 101's LIEF-era sample, 2 of 150 gamma_api outputs more are
  rejected. Record: `docs/evidence/gamma-lief-relayout.md`, section 7. Next: `docs/resume-prompt-experiments.md`
  (read the current results with the user, plan the reruns).
- **Session 103 (experiments):** session 102's reruns read. The catalogue check passes (`pass`, `closed`, `exact`;
  the `ext`/`shf` violations gone). M_add and M_shift unchanged; M_full changed (352 body features both -> up, as the
  fifth clause drops 24 training files): the guaranteed detectors and the price list are retrained in the reruns
  (user). GAMMA now writes through our writers (option A, user: not applicable where no header growth makes room;
  headers grown only when needed): the catalogue part on `main`, the toolkit and pipeline commits held on branch `hgr`
  until ERDALT's tasks 5-8 start. Smoke: every output valid, session 101's four evasions gone, the import attack weaker
  without LIEF's rebuild. Record: `docs/evidence/gamma-lief-relayout.md`, section 6. Next:
  `docs/resume-prompt-experiments.md` (merge `hgr`, the validity rule by sets, then the reruns).
- **Session 102 (experiments):** header growth added to the catalogue as a fourteenth operation, `hgr` (user; exact
  predictor, tests, hand rules; on 40 files no direction changes). A pre-existing soundness gap found and closed: the
  2026-11-18 catalogue check had `pass: False` (two files whose section table runs into the body); a fifth layout
  clause takes such files out of the population (user). The file store now holds all 20,000 training files; the
  derivation reads from it (branch `hgr`, merged after job 1243542). Running: `directions` 1243542, `catalogue-checks`
  1243543, `file-store` 1243547. GAMMA's wrapper (item 2) and the set-based validity rule (item 3) not started. Record:
  `docs/evidence/gamma-lief-relayout.md`, section 5. Next: `docs/resume-prompt-experiments.md`.
- **Session 101 (experiments):** the guaranteed detectors' four toolkit evasions reproduced exactly and explained: all
  outside the threat model through LIEF's rebuild (relocated resources, a destroyed ordinal import, rewritten
  directories), no soundness failure. The validity rule compares counts and misses losses hidden by additions: ~1-2% of
  GAMMA outputs, none elsewhere, so the current round's numbers can go into the manuscript. Decided (user): GAMMA's
  edits are written by our byte-level writers, with a new header-growth variant of `shf`; the validity rule compares
  sets; reruns follow. Record: `docs/evidence/gamma-lief-relayout.md`. Next: `docs/resume-prompt-experiments.md`.
- **Session 100 (experiments):** ERDALT's rescaled retrain read: validation 0.978, test 0.981, its criterion not met
  (35,594 violations against 381); kept as is, the eight folds released (job 1239350). The toolkit's four evasions of
  the guaranteed detectors located: all GAMMA (LIEF rebuild), all valid; one file fails the precondition, two files are
  open (`714d2a7d...` gamma_sections, both detectors; `34089080...` gamma_api, monotone-features). Next session, on an
  interactive node: `docs/resume-prompt-experiments.md`.
- **Session 94:** every detector but ERDALT retrained and attacked on the new material (unread); ERDALT retrained with
  settings rescaled to its authors' setup (`erdalt` running, the folds held). One prompt for all experiments now:
  `docs/resume-prompt-experiments.md`. The older detail below is kept for its history.
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
  `6-results` are held. PLAN.md step 3 (16). **Session 86 (local machine, ERDALT track):** Gimenez et al.'s code caps the
  penalty at 2,432 perturbation vectors per step (152 batches of 16); ours uses all 79,121, ~33x more. Diagnosis
  options added to `train_erdalt` (bbb487f); the diagnosis runs wait for a session on tigris. **Session 87 (tigris,
  ERDALT track):** all nine models finished at validation AUC 0.69-0.75 with 16-40 violations (criterion never met);
  the penalty is small from epoch 2 on while AUC keeps falling, so "it dominates throughout" is too strong; the
  diagnosis waits for an interactive job with a GPU (session 87's had none), run locally. **Session 85:** `toolkit` (19 tasks) and `adaptive` (81) finished;
  MAB-Malware `ours` crashed on two zero-section malware (upstream bug, patched in 455f121) and was resubmitted
  (1131288). Then PV's collapse (5/1,000 detected) was traced to 894 broken outputs in the defenses' material (an
  upstream shift bug among them) and to PV's sample size; the shift bug is patched, the DOS-header attacks skip files
  they cannot extend, and one validity rule now decides for the whole paper whether an output counts (pefile and LIEF
  both read it, no section or import lost; b87fec6). Every learned defense and every attack are being rerun
  (`logs/submit-20261118-s85.txt`; PLAN.md step 3 (17)).
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

- **The scale-up's current results are unread with the user; the reruns are to plan.** Done: GAMMA through our
  writers (session 103, merged in session 104), the validity rule by sets (session 104), ERDALT's eight folds (job
  1239350, finished 2026-11-21). The current round's numbers go into the manuscript meanwhile. Next session
  (`docs/resume-prompt-experiments.md`): read every result with the user, then plan the reruns (the user's call on
  what and when). Still open: PV's setup against Gimenez et al.'s; ERDALT's attacks and `6-results`.
- **TO DO in the reruns: retrain monotone-features and monotone-sums, then their attacks and the price list**
  (decided, user, session 103). Session 102's rerun of the direction tables changed M_full (M_add and M_shift are
  byte-identical): 352 body features (256 `body_byteentropy`, 96 `body_strings` printable distribution) go from
  "both" (dropped) to "up" (kept, monotone), because the fifth clause removes the 24 training files on which `ren`
  wrote body bytes through a section table running into the body (population 18,474 -> 18,450). Both detectors and
  `4-detectors/price-list` read `M_full-pre.*` (`4-detectors/train/run.sh:77`). The current detectors stay sound
  (they drop more than they need to); the retrain makes every number come from one table.
- **For the writing track (session 102):** the paper's operations table gains a fourteenth operation (header growth,
  a shift), and §4.4's population gains a fifth layout clause (the section table ends within the headers); GAMMA
  becomes additions plus, on files without header room, a shift. Session 103: GAMMA is not applicable where no growth
  makes room (192 of 1,000 test malware for the section attack, 114 for the import attack; a sentence with the
  applicability rule), and the import attack is weaker without LIEF's rebuild (worth a sentence once the rerun is read).
- **Deferred, approved by the user (session 85): PV's sample-size experiment** for an appendix explaining why PV works
  less well than prior work suggests (design in `docs/scaleup-protocol.md`, item (17)). Run after the reruns.
- **Extractor quirks the validity rule exposes** ("pefile only" rejections: ~0.2% of outputs in session 85's sample,
  e.g. pefile's 8,192-import cap): list them from the reruns (`invalid.parquet`, `invalid_pefile_only`) and decide with
  the user which to patch in the extractor (CLAUDE.md: no result may rest on a quirk).
- **ERDALT (sessions 82-100; record `docs/erdalt-diagnosis-plan.md`):** settled. Ported literally it collapsed at
  scale; the port was the cause (chiefly the input scale). Retrained with every setting rescaled to their setup:
  validation 0.978, test 0.981, 35,594 violations against the rescaled criterion of 381 (not met). Kept as is (user,
  session 100); Appendix D states each rescaling and the measured trade-off (their literal w2: 769 violations at
  0.914). Open: whether to move the record under `docs/evidence/`.
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
- **The user's close read of §3.3 and §3.4** (the readout rule, Table 1, Lemma 1, Appendix C), when convenient.
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
   head-node session~~ (done, session 74); running. One track again since session 94, ERDALT included
   (`docs/resume-prompt-experiments.md`).
4. While it runs: §2's closing and contribution 4 aligned with §5; the number-free text fixes R4, R5, R15, R21.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

Two sessions were numbered 74: the head node on tigris, and the theory session. Since session 82 each track has its
own resume prompt: `docs/resume-prompt-experiments.md` (the cluster), `docs/resume-prompt-erdalt.md` (ERDALT; archived
in session 100),
`docs/resume-prompt-theory.md` (theory), `docs/resume-prompt-writing.md` (the manuscript); `docs/resume-prompt.md` holds
general work and indexes them.

- **2026-11-23 (session 104, Opus, experiments track): `hgr` merged; the validity rule by sets.** Interactive node
  (16 cores). ERDALT's folds 5-8 had finished (2026-11-21), so `hgr` was fast-forwarded to `main`. The section identity
  for the set rule weighed with the user (count, virtual address, raw range, names with exemptions, name-or-address;
  content considered and rejected, as valid attacks change it); the virtual address chosen, as no attack changes it
  (read from every attack's code; on the 1,217 kept outputs no address lost, while names would have rejected 72 MAB
  renames). Implemented with 11 tests from real byte edits; full suite 2,024 passed. No kept output changes verdict;
  2 of 150 LIEF-era gamma_api outputs in session 101's sample are newly rejected. Items 3-5 of the prompt (reading,
  reruns, right-sizing) moved to the next session (user).
- **2026-11-20 (session 103, Opus, experiments track): the reruns read; GAMMA through our writers.** Interactive node
  (16 cores). Session 102's reruns: catalogue check passes; M_full changed (352 body features both -> up; the fifth
  clause drops 24 training files on which `ren` wrote body bytes), so the guaranteed detectors and the price list are
  retrained in the reruns (user); the store holds 22,000 distinct files (the prompt's 22,200 double-counted the donors).
  `hgr`'s store-reading derivation merged; `directions` 280G and `file-store` 64G (peaks sat at their requests).
  GAMMA: the section attack always writes all 30 donors (75 at the literature budget), the import attack needs one
  slot; after growth 804 files fit 75, 192 fit fewer than 30, 114 none. Options weighed with the user (not applicable,
  write what fits, shrink the donors, LIEF fallback, a new operation); option A chosen. Implemented: multi-library
  import writer, slot count and smallest growth (`catalogue`, on `main`); GAMMA's problems through our writers with a
  structural assertion, the room check replacing LIEF's round trip in the toolkit and material steps, `header_growth`
  per row, `toolkit_split` mapping (held on `hgr`). Checks: matches the independent room count on 1,000 files; full
  suite 2,013 passed; smoke 10-50 s per run, every output valid; session 101's four evasions gone (three not
  applicable, one no longer evades). The import attack evades less without LIEF's rebuild (13/20 vs 15/20 in the smoke).
- **2026-11-20 (session 102, Opus, experiments track): header growth (`hgr`); a soundness gap closed; the store.**
  Interactive node (16 cores); code in a worktree (`../ProvExp-hgr`, branch `hgr`) while ERDALT's folds start. The
  user chose a fourteenth operation over a variant of `shf`, and to leave the debug offsets stale (raising them writes
  body bytes). `hgr` written, declared, predicted exactly, tested; on 40 files the derived table is unchanged but for its
  new column. Room for GAMMA's 30 headers: 808 of 1,000 test malware (session 101's 992 ignored data after the table).
  The 2026-11-18 catalogue check's `pass: False` traced to two files whose section table runs past SizeOfHeaders into
  the body; the user approved a fifth layout clause. The store now holds every training file (the user: the SimpleDB
  is slow by name); the derivation reads it (held on `hgr` until 1243542 finishes). Submitted 1243542, 1243543,
  1243547; logs healthy. A diagnostic wrote briefly to `/scratch/lk3591/provexp` (a stale link target), moved.
- **2026-11-20 (session 101, Opus, experiments track): the GAMMA evasions explained; two decisions.** Interactive
  node (16 cores). The four toolkit evasions of the guaranteed detectors reproduced exactly (the toolkit's functions,
  seeds and donors); in each, the declared edit alone raises the score and the drop comes from LIEF's relayout (the
  resource directory moved; WS2_32's ordinal imports destroyed; TLS, relocations, load config rewritten); outside the
  threat model, not a soundness failure. Found on the way: the validity rule compares counts (a loss hidden by added
  DLLs passes) and `lief_preserves` ignores data directories. Measured on 480 re-created outputs: missed losses 2/150
  gamma_api, 1/150 gamma_sections, 0 elsewhere; LIEF moves the resources in ~60% of GAMMA outputs. Header room: 97 of
  1,000 test malware fit GAMMA's 30 headers in place, 992 after growing the headers. The user decided: GAMMA through
  our writers with a header-growth variant of `shf`; validity by sets; reruns acceptable (prototyping); the current
  numbers into the manuscript meanwhile. Record `docs/evidence/gamma-lief-relayout.md`.
- **2026-11-20 (session 100, Opus, experiments track): ERDALT read, folds released; the monotone evasions located.**
  `erdalt` (1239349_0) finished in 6 h 41 min: validation 0.922 -> 0.978, test 0.981 (expected 0.93-0.95), no epoch
  under 381 violations (kept epoch 64: 35,594, still falling slowly; logits up to +-8,007, temperature 267). The user
  agreed to keep the settings and released the folds. ERDALT's prompt archived. The toolkit's evasions of the
  guaranteed detectors are all GAMMA outputs that pass the validity rule: `714d2a7d...` (gamma_sections; both
  detectors, 467-520 KB added), `34089080...` (gamma_api, monotone-features), and `eb61a5bd...` (gamma_api; fails
  the precondition, outside the guarantee). The toolkit keeps no outputs, so the check needs a rerun. Suspected: LIEF's
  rebuild changes more than the declared edit (unchecked). Next session on an interactive node.
- **2026-11-19 (session 99, Opus, writing track): §3 cut to 3,312 words (from 3,769).** Plan of 22 items, each
  assessed for the math, the reader, and the flow at the user's request, revised where a cut cost the first two, and
  approved as revised (d9f77b8). Cut: restatements of Definitions 4, 8, 10 and equation (11) in words, the gloss
  sentences around Definitions 1-3, the "common contributions" paragraph (one example sentence kept), the long
  explanation after Theorem 1 (now: Lemma 1 bounds each sum, Lemma 2 the feature), the four-sentence lead-in to
  Proposition 1 (one sentence kept; the user had called Prop 1 "abrupt" before). Kept on purpose: "whatever content
  the edits write", the table's looseness stated next to the prior-work constraints, the coarse direction of "any
  other" readouts, "no inverse" in §3.1 (§3.2 refers to it), "Without closure ..." after Proposition 2, whose reason is
  now "each direction is closed under adding changes". 62 words above the 3,250 ceiling; the user accepted that.
  Next: §4 with Appendix D, `docs/resume-prompt-writing.md`.
- **2026-11-19 (session 98, Opus, writing track): Appendix C holds proofs only.** The user chose the principle: the
  appendix proves what the body states; definitions and the conditions of stated results go in the body; commentary is
  cut. Applied (f84cfd4, 29ae165): the sign of a change defined in Definition 7; three lemmas stated in the body, proofs
  in C.2/C.3: Lemma 1 *Directions of sums* (§3.3, after the totally-ordered paragraph), Lemma 2 *Readout rule* (after
  Table 1's paragraph), Lemma 3 *Closure* (was Lemma 1); the helper "totals keep their sign" folded into Proposition
  2's proof; the pool-default condition in Table 1's caption; Table 7, its justification and *Hashed keys* switched
  off (`\iffalse` in `_j_proofs.tex`; Appendix A's $Q$ removed); the remark that scores reading sums are covered cut;
  §3.4's recap sentence ("Theorem 1 supplies the sound table ...") cut, the Gimenez bridge sentence kept. Words: §3
  3,692 to 3,769; Appendix C rendered 1,154 to ~890. Next: cut §3 to 3,000-3,250 by trimming explanation and
  analysis ("let the math do more of the talking"), `docs/resume-prompt-writing.md`.
- **2026-11-19 (session 97, Opus, writing track): §3 cut by 12%; the body/appendix split reopened.** Cut plan per
  subsection, every item decided by the user, applied in 652c1af: shorter roadmap; the three analogies shortened (Gray
  et al., incremental view maintenance, abstract interpretation; §6 unchanged); Proposition 1's repeats removed and
  "touches" in (iii); §3.3 lead and the "rule is not limited" sentence cut; Lemma 1 kept in the body, its explanation
  tightened; Appendix C drops *Patterns under extension*, *Computing part (ii)* and a repeated sentence. Rejected: 1b
  (the free-monoid sentence stays) and 1c ("do not form a vector" stays). Words: §3 4,207 to 3,692, Appendix C 1,335
  to 1,154. A second round proposed moving the product counterexample to Appendix C; the user: body sentences are
  never moved to the appendix to save words. Asked what Appendix C's non-proof paragraphs are for and why definitions
  appear there; the user decided to revisit what goes in the appendix and what stays in the body in a new session
  (`docs/resume-prompt-writing.md`).
- **2026-11-19 (session 96, Opus, writing track): the holistic review of §3; §3.3/§3.4 refactored; Appendix C
  reorganized.** Nine findings plus a term ledger. Approved and applied (a8e5318): "item change" for Definition 8's
  sense of change; the readout rule moved into Definition 10 (*Readout rule and derived table*); a shorter §3.3 lead
  and roadmap; pointer trims; small term fixes (extractor defined at §3.1's start, *contribution* and *touches* in
  Definition 3, Table 1's row "nondecreasing", also in Appendix D). Discussed, then applied (c476f31, 20c5fb1):
  Theorem 1 keeps only the one-edit claim; closure and the sequence claim (new Proposition 2, *Sequences of edits*, for
  any sound table) moved to §3.4, renamed *Sequences and Robust Detectors* (title "for now"); closure is checked
  directly (as §4.4 does) or proven by Lemma 1, no longer "need not be assumed" (no result in §4/§5 used the lemma).
  Appendix C now has C.1-C.3, one per body subsection (a95f946). Appendix B: the user rejected trimming it (a
  stand-alone crash course; light repetition in §3 is fine). Cuts logged in `docs/review-cuts.md`, not applied. Word
  counts: §3 4,320 to 4,207, Appendix C 1,385 to 1,335. Next: cut §3 to ~3,450 (`docs/resume-prompt-writing.md`).
- **2026-11-19 (session 95, Opus, writing track): §3.3 with its appendix material; §3.4 split off.** Review pass:
  eight findings, all approved. At the user's suggestion §3.3 was split: §3.3 *Sound Directions* (signatures,
  directions of sums, readout rule, Theorem 1, abstract interpretation) and §3.4 *Robust by Construction* (closure and
  Lemma 1, monotone detectors, Corollary 1, a closing paragraph). The totally-ordered condition now leads its
  paragraph (cases moved to Appendix C); the readout rule is introduced from the ratio; Lemma 1's example follows its
  own case; Appendix C checks that additive sums and pools are totally ordered and names its reasons; $P_j, N_j, O_j$
  added to the symbol table (0587b86). Word counts: §3 4,390 to 4,320, Appendix C 1,320 to 1,385. `docs/review-cuts.md`
  started. Next (user): the holistic review of §3 with Appendices A-C, then reorganize Appendix C, then cut §3 by ~20%,
  then §4 (`docs/resume-prompt-writing.md`).
- **2026-11-19 (session 94, Opus, ERDALT and experiments, tigris interactive job): round 2 read; the retrain.**
  Round 2 (1239145_[7-10], quantile scale) read: robust-short 0.914 validation / 0.919 test at 769 violations (the
  violations plateau from epoch 9); robust-pscale 0.951 / 0.956 at 40k; robust-fixed 0.82 and still rising (not a
  ceiling); robust-n1033 0.971 / 0.973, 8.8M of the 202M entries of all vectors violated. No run met the criterion.
  Their criterion (< 5 violated entries over 1,033 vectors) is also sized to their data. With the user: the retrain
  rescales each setting to keep their method's effect (quantile scale, w2 x 1,033 / our vectors, criterion x our
  vectors / 1,033, their ~465,000 steps = 68 epochs per step, LR patience 4; `--reference_vectors`,
  `--scale_criterion`, `--max_violations`, `--lr_patience`; b9edda9; smoke-tested). The user submits `erdalt` first
  and the folds held. Session 85's chain found all finished (unread); the ERDALT track folded into one holistic
  `docs/resume-prompt-experiments.md` (the old one archived).
- **2026-11-19 (session 93, Opus, writing track): §3.2 and its appendix material.** Review pass: eight findings and
  the out-of-scope note, all approved and applied together (2eec34b): where a delta comes from (the edit states it, so
  it is known before $z'$ exists), Proposition 1 (ii) now covers every non-additive sum, the repeated pool/item-table
  point cut, exactness tied back to §2, "can move" instead of "can have side effects". The user then set the method for
  the rest of §3: each subsection is polished together with its proofs in Appendix C (split, appendix review, joint
  final pass). For §3.2 (0c0da24): the body keeps what each part means, Appendix C the proof (part (ii) derived,
  $\star_k$ for one sum, definitions named, "pair") and *Computing part (ii)*; the pool example removed at the user's
  request; symbol table range bug fixed and $B$ added. Word counts: §3 4,389 to 4,390, Appendix C 1,308 to 1,320.
  Next: §3.3 with its appendix material (`docs/resume-prompt-writing.md`).
- **2026-11-19 (session 92, Opus, writing track): §3.1's humanistic-review pass.** Eight findings; the user
  approved 1-3 and 5-8, rejected 4 (the sentence on why the item map drops positions stays), deferred the recurring
  patterns and the term ledger (the overloaded "element", "extractor" before Definition 5) to a holistic review of all
  of §3, and asked to fix the out-of-scope note too. Applied together, without the paper-prose skill (the user no longer
  finds it helpful), in 0185d58: the item table now has its own closing paragraph, after the partial-extractor caveat;
  "members" now means only an item's positions (multiset entries are "pairs"); the readout paragraph leads with its
  claim, and the distinct count is no longer called algebraic (Gray's analogy overreached); the roadmap's last sentence
  is split; $\mathcal{V}$ is described one way; two repetitions were cut; the remark on other monoids left §3.1 (§3.3
  already states the totally-ordered condition, and §3.2 gained one sentence: such a sum is recomputed like a pool).
- **2026-11-19 (session 91, Opus, ERDALT track, tigris): the diagnosis read; the input scale is the cause.** All
  seven tasks of 1179478 finished. Session 90's hypothesis (the penalty's weight) refuted: with their penalty mass per
  step (pscale) the AUC still falls (0.878 -> 0.824; +0.03-0.09 over the control at matched epochs, about even at
  matched violations); L frozen at PV's mask under the std scale reaches only 0.40-0.55; the 20-epoch schedule, the
  cap and the PV start all fall like the control. The quantile scale alone holds (validation 0.938, test 0.940 at
  7.5k violations; temperature 67 instead of 400-10,000): the std scale, fitted on 1.76M heavy-tailed files instead of
  their 24,000, lets a few files' extreme values dominate the monotone network. Their 1,033 vectors leave ~11M
  violated entries over all vectors (the blind-spot evidence). The user cancelled `erdalt` 1169769_0, wants to keep
  their per-step penalty mass, and asked for a per-step weight schedule (`--schedule_per_step`, 1b663c2). Round 2
  (tasks 7-10, quantile scale: 20-epoch per-step schedule; L frozen at PV's mask; 1,033 vectors; their penalty mass
  with the per-step schedule) submitted by the user. Right-sized: 2 cores (round 1 used one).
- **2026-11-18 (session 89, Opus, ERDALT track, tigris interactive job): plan, then the material explains most of
  it.** A written plan (`docs/erdalt-diagnosis-plan.md`) proposed a ceiling: directions the attack vectors move both
  ways, which L would have to discard. Refuted by a linear program (no cancelling combination among the 79,121 old or
  78,715 new vectors; the raw scale broke the LP until the vectors were standardized, caught by a planted opposite).
  Then: the new material (1141847 done, merged by `learned` 1141848, done) lowers 1,209 features instead of 2,367,
  and PV, which is ERDALT with L zeroing the lowered features, goes from validation AUC 0.553 to 0.924 (test 0.930):
  a zero-violation model at 0.92 exists. Decided with the user: no separate diagnosis; the old nine ERDALT models moved
  to `superseded-s85/4-detectors/`; `erdalt` retrained first (1169769_[0]), the folds held (1169770_[1-8]) until its
  course is read against 0.92. Scripts: `artifacts/scaleup/diag/erdalt/lineality/`.

- **2026-11-18 (session 88, Opus, ERDALT track, tigris interactive job, one GH200 shard): slice diagnosis, stopped.**
  Six variants on a seeded 200,000-file training slice, old material (control, 2,432 vectors per step, + batch 16,
  free output layer, no LR scheduler, penalty weight x0.1; `--penalty_scale` added to `train_erdalt`). The slice does
  not reproduce the collapse (per-epoch schedule, 9x fewer steps per epoch), so the runs cannot name the cause; the
  user judged that they were started without being thought through and stopped them at epoch ~21. Findings (old
  material): AUC tracks violations across variants; the cap (b) peaks at 0.81 and slides; free output ~0.88; inputs
  heavy-tailed (hashed section sizes; validation logits +-1e5); the 894 broken outputs carry 8.8% of the penalty's
  negative mass and none of the most extreme vectors (valid GAMMA outputs in `section:vsize_hash_48`). Scripts and
  logs: `artifacts/scaleup/diag/erdalt/`. Next: a written plan first (`docs/resume-prompt-erdalt.md` §5).

- **2026-11-18 (session 87, Opus, ERDALT track, tigris interactive job): the nine models read; no GPU.** All nine
  ERDALT models finished (old material): validation AUC 0.690-0.752, 16-40 violations, `met_criterion` false
  everywhere (per model in `docs/resume-prompt-erdalt.md` §2). `erdalt`'s history: the penalty `l2` falls from 18,801
  (epoch 0) to 5.7 (epoch 2) and 0.05 (epoch 40) while AUC falls 0.853 -> 0.696, so the collapse continues after the
  penalty is small (early damage, or the rising weight w2). The interactive job (1142565) had 16 CPUs and no GPU, so
  no diagnosis ran; the user starts one with a GPU and wants the runs local, not `sbatch`. A run (f) (all vectors,
  penalty ~10x smaller) proposed, not yet agreed.

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
  (*Waiting on the user*). Then, with the user: the lost searches were slow, not dying (79, 61, 60 min, none
  evaded); `hand-table` reads the file store over pools (108 min -> 8 min, reports identical, dea644c); the broken
  outputs traced (secml-malware's shift writing in front of the MZ header on 358 training / 20 evaluation files whose
  first section has offset 0; the DOS extension on files with e_lfanew < 0x40; import tables lost); the shift patched
  (5170936; byte-identical where upstream worked, 120/120), the DOS attacks not applicable to those files; one validity
  rule for the paper (b87fec6, `provexp.attacks.validity`; on stored outputs all 785 flagged rejected, 42 of 2,000
  random; full suite 1,770 passed); PV's sample-size experiment designed and deferred (protocol item (17)). MAB `ours`
  1131288 cancelled (old rule); the affected steps rerun (`logs/submit-20261118-s85.txt`), old outputs in
  `artifacts/scaleup/superseded-s85/`. Claude's lapse: a diagnostic without a main guard spun 23 min unnoticed until
  the user asked; the memory now covers it. Settings: `/shared/rc/admalware/provexp` always readable and writable
  (`.claude/settings.local.json`).

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
