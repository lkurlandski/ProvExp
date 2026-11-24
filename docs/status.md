# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-40 in `docs/archive/status-log-2026-11-10-to-11.md`, sessions
41-42 in `docs/archive/status-log-2026-11-12.md`, sessions 43-54 in
`docs/archive/status-log-2026-11-12-to-13-s43-54.md`, sessions 55-58 in `docs/archive/status-log-2026-11-13-s55-58.md`, sessions 59-60 in
`docs/archive/status-log-2026-11-13-s59-60.md`, sessions 61-62 in `docs/archive/status-log-2026-11-14-s61-62.md`, session 63
in `docs/archive/status-log-2026-11-14-s63.md`, sessions 64-65 in `docs/archive/status-log-2026-11-14-s64-65.md`, sessions 66-76 in
`docs/archive/status-log-2026-11-15-to-16-s66-76.md`, sessions 77-94 in
`docs/archive/status-log-2026-11-16-to-19-s77-94.md`).

## Current state (2026-11-24, through session 112)

- **Session 112 (writing):** the user's read of 4.2 *Threat Model*. Four rewrites (survey of prior work, then
  disorganized, then distant and passive, then scattered); the fourth, tied to §3's guarantees ("the threat model
  decides what they are worth"), accepted as an improvement and committed (d004f35). A humanistic review followed
  (eight findings, none applied). The user diagnosed the cause: the subsection's role in the paper is undecided (e.g.,
  whether the attacker's budget belongs in 4.2 or §5). **Next session: task planning and manuscript organization** (a
  content map of what research goes where, the delicate subsection pairs reviewed together, starting likely with 4.2
  and 5.1); `docs/resume-prompt-writing.md`.
- **Session 111 (writing):** the user's read of §4 and §5 began; §4's lead and 4.1 done, **next: 4.2 *Threat Model***.
  Lead: the closing sentence of the first paragraph cut (repeated the second); the PE background now names only what
  later text uses (headers, sections, the headers' *data directory* locating the imports, debug data and Authenticode
  signature, the overlay); "tables such as the import table" gone. A bare "table" for a PE structure became "other
  structure"/"structure" in 4.1, 4.3, 4.4; standard PE names stay (section table, data directory, debug directory entry,
  certificate table entry), after Claude briefly renamed them and the user objected. 4.1: renamed *Extractor* (Appendix
  D.1 too), matching *Threat Model*, *Signature*, *Population*; colons used as transitions rewritten; the warnings
  sentence restructured; "EMBER's extractor parses files with pefile" introduces the overlay rule (pefile cited, new
  `main.bib` entry). §4: 1,778 words. Claude overcorrected three times (renamed standard terms; swapped colons for
  "for instance"; then removed a correct "for instance"); memory `feedback-proportionally` saved.
- **Session 110 (experiments, tigris head node):** the rerun checked: everything up to ERDALT finished cleanly (audits,
  trial, train, material: 73,502 kept of 76,049, 2,001 over 4 MB, all GAMMA; GBDT defenses, iterated, price list, MAB
  `ours` and `expert`); ERDALT's nine GPU models (1260392) wait for tigris GPUs (estimated start 2026-11-25 ~15:00), and
  toolkit, adaptive, MAB `zainab` and `6-results` wait on them. GAMMA's section attack is not applicable to ~25% of
  files at 75 donors (2,457 of 10,000 training malware); accepted for this round (user). Headers right-sized
  (557f0b5). The register `docs/experiments-to-reconsider.md` started (022dceb). Decided (user): run ERDALT on sporc
  (x86_64; estimated start the same day) as well, after one environment per architecture is set up and tested on both
  clusters, the sporc array in reverse order, the first cluster to start a model wins (mechanism to design). Next:
  `docs/resume-prompt-experiments.md`, on the sporcsubmit head node.
- **Session 109 (writing):** humanistic review of the rebuilt §5 and Appendix E (ten findings; the user: "Please fix
  all issues"), applied in one pass: the lead now names the two failure modes (unsound: evaded; over-cautious:
  detection lost, measured against the derived detector on the same features), the derived table's second role
  (predicting where each other detector is open), the sources in section order and why trial shares 5.3, and the
  claim qualified by threat model; "cautious" no longer used for Severi et al. (whose error is unsound for a
  defender); Table 4's caption states the takeaway and the comparison rows; adversarial training's comparison says
  which detectors it compares (full training set, no entry write); 5.3's heads by defense (*PV's hole*, *What PV pays
  in detection*, *ERDALT*, *Trial*), leave-one-out moved after ERDALT; 5.4 states the price once and frames it as the
  price of the guarantee; *Where the cost lies* split into *The entry write's share* and *Where the rest lies*
  (Table 11 said to be without the entry write); "two-sided" defined; code signing named as Authenticode; Appendix E
  seams (PV's tolerance 1e-6 and feature set, Table 11's caption, MAB-Malware's detectors). `% OPEN`: 5.4's "24 of the
  28" does not match Table 4's 39/40 detected. Then `cut-to-length` as a cleanup (the user: ~4,000 if a number is
  needed, "it doesn't really matter that much"): 18 unflagged items applied, the two ⚑ items (leave-one-out shortened,
  trial's closing turn) not; §5 4,639 to 4,406 words (lead 521, 5.1 746, 5.2 931, 5.3 1,318, 5.4 890); Appendix E 892.
  Commits 328abc0, d64d184. Next (the user): the user reads §4 then §5, one subsection at a time, Claude adjusting
  after each; no humanizer pass. Subsections done: none yet. `docs/resume-prompt-writing.md`.

- **Session 108 (writing):** §5 rebuilt from the ground up (plan: `docs/evaluation-note.md`; decision 13). The user
  chose the narrative: every source of a defender's knowledge of what edits do (reading the extractor, observed
  attacks, trial) yields a detector, and Corollary 1 is the yardstick; a source fails by being unsound (evaded) or
  over-cautious (detection lost). §3.4 merged into §3.3 (Proposition 2 and Lemma 3 stay; the definition "monotone with
  respect to D" and Corollary 1 moved to §5's lead; Appendix C mirrors: C.3 *Robust Detectors*). 5.1 to the scale-up
  protocol; 5.2 gains the expert set's detection comparison; 5.3 *What Observed Edits Miss* (the learned defenses,
  iterated adversarial training, leave-one-out, trial from run 144); one comparison table (Table 4) replaces Tables 4
  and 5; 5.4 trimmed to the derived detectors; Appendix E mirrors §5 (E.1-E.3; the per-attack table regrouped,
  ERDALT's rescalings stated, the price list as Table 11). Pilot numbers kept; blue predictions for iterated
  adversarial training and trial's unrecorded cells. The stray fragment in 5.4 restored. §5 4,647 words, Appendix E
  976. Reviewed and cut in session 109. Commits 4a11d53, 2209cae.

- **Session 107 (writing):** a fresh humanistic review of §4 (eight findings and minor points), applied in one pass
  except what rested on the out-of-date §5 (user): the population's completeness exempts the debug data and the
  signature (as in Appendix D.3); "incomplete" separated from the 4 MB truncation; what is proven and what is checked
  stated in 4.3; the item table named in 4.1; declined edits in their own sentence; the overlay rule tied to the entry
  write; Lemma 3 restated; the attacker's knowledge; Appendix D.2's position record introduced. The *shifts* model is
  kept (unused by the current §5; revisit when §5 is updated). Then `cut-to-length`: 19 items; the user approved the 14
  unflagged ones (the five ⚑ items restored), §4 from 1,956 to 1,792 words (lead 275, 4.1 427, 4.2 486 with Table 2's
  caption, 4.3 339, 4.4 264; user's range 1,500-1,700). Next:
  `docs/resume-prompt-writing.md` (bring §5 up to date).

- **Session 106 (writing):** §4 reviewed (humanistic review, eight findings, all approved and applied), the decided
  methodology of sessions 102-105 written into §4, §5 and Appendix D (header growth as a fourteenth operation, the
  fifth layout clause, the 4 MB scope instead of a byte budget, the GAMMA paper's budget, the byte-level toolkit
  attacks framed and sent to the appendix, GAMMA's LIEF rebuild out of the body and into the appendix, Zainab et al.
  as a comparison of different setups). Then §4 restructured with the user around what §5 needs: the PE paragraph in
  the lead; 4.1 *EMBER as a Sum-then-Readout Extractor* (now introduces reading the sums), 4.2 *Threat Model*, 4.3
  *Signature*, 4.4 *Population*; the toolkit introduced in §5.1. Appendix D mirrors §4's subsections (D.1-D.3, the
  declared changes and the five layout clauses moved there); the attacks and defenses split into a new Appendix E
  *Attacks and Defenses* (`_j3_attacks.tex`). §4: 1,840 words by texcount (about 1,710 of prose; user: 1,500 fine,
  1,700 acceptable, 2,000 too long). Next: `docs/resume-prompt-writing.md` (a fresh humanistic review of §4, then the
  cut).

- **Session 105 (experiments):** the old round (session 85's chain) read with the user for red flags. GAMMA API's
  dominance explained (it switches on ~1,006 of 1,024 hashed import-function features); the byte-level attacks'
  weakness checked with a positive control (against MalConv the same code evades 5-16 of 20; against our GBDT they
  barely move the score); the adaptive search's evasions are signature cloning (expected); MAB's 52% vs Zainab et al.'s
  83% accepted (different detector and malware); validity rejections and ERDALT's folds fine. Decided (user, protocol
  item (22)): the literature budget for the toolkit and the material; outputs count only up to 4,000,000 bytes (replaces
  the 5%/512 KiB cap, for every attack and the material); `hgr` in the adaptive and iterated searches; the weak toolkit
  attacks to an appendix this round; later changes go on a next-round list, applied together. Smoke-tested end to
  end, old round moved to `artifacts/scaleup/superseded-s105/`, **the full chain submitted by the user** (jobs
  1260382-1260399, `logs/submit-20261123-141442.txt`; the first four started cleanly). Next:
  `docs/resume-prompt-experiments.md` (check the chain, then read the new round).
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
- **§5 (session 108):** rebuilt around where each detector's knowledge of edits comes from (decision 13,
  `docs/evaluation-note.md`, which supersedes the mock's §5 plan); drafted, not yet reviewed. History below.
- **§5 (before session 108):** three findings (PLAN.md, decision 10; plan in `docs/paper-mock.md`, §5), fully drafted, no blue values.
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

- **Two scale-up gaps in §5 (session 108), the user's call:** (a) the hand-table detector (§5.2 *What the error
  costs*, pilot 10/29) has no scale-up step; add it to the next round, or keep the pilot result. (b) A *shifts*
  detector (the middle threat model of §4.2): deferred by the user; used in §5.4 only if it is implemented and run.
  Both are on the next-round list (`docs/scaleup-protocol.md`) as candidates.

- **The full rerun is running (submitted 2026-11-23, session 105; jobs 1260382-1260399; session 110: all but ERDALT
  and the attacks that need it finished; ERDALT to be raced on sporc, see Current state).** It carries every change
  of sessions 101-105 (GAMMA through our writers, `hgr` and the fifth clause, the validity rule by sets, the literature
  budget, the 4 MB output rule) and ERDALT's attacks; the old round's numbers stay in the manuscript until it is read.
  Next (`docs/resume-prompt-experiments.md`): check it, then read every result with the user. Still open: PV's setup
  against Gimenez et al.'s (the sample-size experiment, after the rerun).
- **In the rerun (decided, user, session 103): monotone-features and monotone-sums retrained, then their attacks and
  the price list**. Session 102's rerun of the direction tables changed M_full (M_add and M_shift are
  byte-identical): 352 body features (256 `body_byteentropy`, 96 `body_strings` printable distribution) go from
  "both" (dropped) to "up" (kept, monotone), because the fifth clause removes the 24 training files on which `ren`
  wrote body bytes through a section table running into the body (population 18,474 -> 18,450). Both detectors and
  `4-detectors/price-list` read `M_full-pre.*` (`4-detectors/train/run.sh:77`). The current detectors stay sound
  (they drop more than they need to); the retrain makes every number come from one table.
- **For the experiments track (session 106, user):** the hand table is to be extended to all fourteen operations
  (the entry write and header growth are missing); §5.2 already says "each of the fourteen operations". Check whether
  its errors (Table 3) change.
- ~~**For the writing track (session 102):**~~ (written in session 106; kept for the record) the paper's operations table gains a fourteenth operation (header growth,
  a shift), and §4.4's population gains a fifth layout clause (the section table ends within the headers); GAMMA
  becomes additions plus, on files without header room, a shift. Session 103: GAMMA is not applicable where no growth
  makes room (192 of 1,000 test malware for the section attack, 114 for the import attack; a sentence with the
  applicability rule), and the import attack is weaker without LIEF's rebuild (worth a sentence once the rerun is read).
  Session 105 (number-free, can be written now): the attack budget is the GAMMA paper's for every toolkit attack; the
  byte budget becomes "an output counts only if it is at most 4 MB, the files the study concerns"; the byte-level
  toolkit attacks were built for byte-level models and barely move a feature-based GBDT (checked with a MalConv
  positive control), so they move to an appendix and GAMMA API carries the toolkit; the adaptive search includes
  header growth; Zainab et al.'s 83% is not reproduced because their detector and malware differ (not a claim to make).
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
- ~~**`make check` reports one overfull vertical box**~~ (gone after session 106's appendix edits).

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

- **2026-11-23 (session 107, Opus, writing track): §4 reviewed again and cut.** Review findings approved, all fixes
  in one pass by Claude's judgement, nothing changed on account of §5, which is out of date (user). Cut to 1,792 words
  (14 of 19 items; the five ⚑ items rejected and restored; three slips fixed after reading the PDF: `\Cref` rendering Appendix D as "Section D", a
  colon misreading, "checked ... checks"). Commits 019c1c2, 63eec48, and the restore.
- **2026-11-23 (session 106, Opus, writing track): §4 reviewed, updated, restructured; Appendix D/E.** The
  humanistic review's eight findings approved and applied (the entry write named; the three threat models in their own
  paragraph; five overwrites; the insertions' declared changes; the sample condition rewritten; item tables not
  re-glossed; why Lemma 3 does not give closure; the overlay rule in its own paragraph; data directory in the PE
  paragraph). Part 2 of the prompt in one pass (user); the user decided: the hand table goes to fourteen operations
  (experiments track), GAMMA's rebuild is not mentioned in the body (appendix only). Then the user asked to rethink §4
  as the bridge from §3 to §5: what §5 needs (the features, the edits by §5's names, what is proven and what is
  checked, where the guarantee holds); the structure agreed and applied (see Current state). The user is considering
  moving §3.4's robust detectors into §5 (merging 3.3 and 3.4); checked: §4 no longer refers to §3.4's detectors, and
  the plan does not change. The LOO table was silently lost as the last float of the appendix (only an undefined
  reference showed it); placed before the per-attack table. Also noticed: a stray fragment at the end of §5.4's *The
  width of the threat model* ("model, and with it which edits ..."), not fixed.
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
