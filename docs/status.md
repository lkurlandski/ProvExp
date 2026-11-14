# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`, sessions 29-40 in `docs/archive/status-log-2026-11-10-to-11.md`, sessions
41-42 in `docs/archive/status-log-2026-11-12.md`, sessions 43-54 in
`docs/archive/status-log-2026-11-12-to-13-s43-54.md`).

## Current state (2026-11-14, through session 62)

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

## Waiting on the user

- **The refactoring session (next; `docs/resume-prompt.md`).** The review revisit is closed (nothing else before the
  scale-up). Next: reorganize the code and experiments for the scale-up (`pipeline/`, plain names, library code into
  `src/provexp/`, dead code removed, tests), with `SETUP.md` for new systems (the SLURM clusters sporc and tigris).
  Then the extractor audit pass, the remaining protocol items (malware count first), and a session on the cluster's
  head node. Number-free rebuttal text fixes (R4, R5, R15, R21) move to step 4 (while the scale-up runs).

## Scheduled (in order; PLAN.md, next steps)

1. ~~The 4 MB-truncation decision~~ (done, session 46), ~~the full simulated review~~ (run; discussed sessions 48-61),
   ~~R7's widening~~ (done, sessions 53-62), ~~the extractor question~~ (decided, session 62: stay on pefile).
2. ~~The final review/rebuttal revisit~~ (done, session 63: nothing else before the scale-up).
3. The scale-up (PLAN.md step 3): **the refactoring session first** (`pipeline/`, `SETUP.md`), then the extractor
   audit pass, the remaining protocol items (malware count first; one seed, 5,000 extraction-scored candidates, full
   splits, one training set and protocol for every detector, the trial row, iterated adversarial training, the R7 blue
   values and PROTOCOL recounts), then a head-node session on the cluster.
4. While it runs: §2's closing and contribution 4 aligned with §5; the number-free text fixes R4, R5, R15, R21.
5. After reading it: final numbers, then shortening §4-5 and §5's question-and-answer emphasis.
6. A second domain decided with the scale-up's results in hand (the user's call).
7. Introduction, discussion, abstract last.

## Session log

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

- **2026-11-14 (session 62, R7/scale-up track): the decisions before the scale-up taken; verification and small fixes
  done.** Rebuttal status reviewed (triage table, meta-review §5-8). **Decisions (user):** (1) stay on pefile, with a
  deliberate audit pass and deviations table later (scale-up prep); (2,3) scale-up protocol and malware count are their
  own session; (4) escape audit against the widened population: yes; (5) make the small manuscript fixes now.
  **Done:** (a) LIEF spike (`r7-overlay-rule.md` §8): structures agree with pefile on 99/100 pilot files, LIEF ~35x
  faster but parsing is ~12-25% of our time; stay on pefile. (b) pefile's parser caps verified (§10,
  `upstream-issues.md` item 10): crossing the 8,192-import cap drives num_imports ~70 -> ~8,110 (declared delta wrong,
  an exactness gap) but 0 model-read features fall on three files -> not a soundness hole; a deviations-table item.
  (c) Escape audit against the loose population (§9): every loader-ignored entry write still leaves the loose
  population exactly as run 137's strict audit; no new in-population escape; the scale-up's active escape search stands
  (§7). (d) Three manuscript fixes (8d88ef3): Appendix D's pools ("adds a 0", minima 0 on every file), self-maintainability
  (Mumick et al.) in §3.2, the code-level exclusion reworded against Lucas et al. in §4.3. (e) Kim et al. (CCS 2017)
  cited for signature cloning (b319638, `% VERIFY` resolved); the overfull vbox is gone; `make check` clean.
  **Waiting on the user:** the scale-up protocol and malware count (own session).

- **2026-11-14 (session 62, R18 track): ready for run 144.** While it ran (started 10:05): the six non-string
  disagreements traced (three are trial's blind spots; the two import addresses are declared too broadly, and run 145
  shows freeing them as monotone gains nothing: 83.2 vs 83.4% at 1% FPR, so trial's edge is real lowerable features);
  the `--save_rows` patch for `a1_adaptive.py` written and tested, not applied (R7-owned;
  `docs/evidence/r18-a1_adaptive-save_rows.patch`); `scripts/trial_audit.py`. **Next:** read run 144 with
  `docs/resume-prompt-R18.md`.
- **2026-11-14 (session 61, R7 track): run 143 read.** Hypothesis held: neither `-loose` monotone detector is evaded
  by any of the three escapes (0/39, 0/40 each; no candidate lowered a monotone score; full 2,000-candidate budgets);
  guaranteed for the 28/30 population originals under the cert/debug escapes, observed for the rest; one SizeOfImage
  search lost to a stalled worker (not re-run). The unconstrained detector: 47/47, every evasion by signature cloning
  (hypothesis 40-60% failed). Written into run 143's header, the R7 record §7 and log, PLAN.md step 2b (iii). Then the
  paper's R7 text with the user in three blocks: §4.3 the entry write (13 operations), §4.4 the widened population and
  no routing, §5.4 *The price* (run 140; signature cloning framed as a finding, user), *Where the guarantee holds*
  (the escapes), *Where the cost lies*, Table 5 and Appendix D's per-attack table, LIEF's overlay rule in §4.2 and
  Appendix D. Decision (v), user: blue values for the monotone toolkit/MAB cells until the scale-up; the scale-up's
  R7 items listed in PLAN.md step 3. Open: a signature-cloning citation (`% VERIFY`), one 2 pt overfull vbox.

- **2026-11-13 (session 60, R18 track): the trial competitor.** Built the trial table from our own edits, a stronger
  probe (every section renamed, all slack/DOS/header bytes, donor imports from 200 benign training files;
  `scripts/trial_probe.py`, `trial_table.py`) and, as a variant, the toolkit outputs. Against the derived table on
  modeled features: no soundness conflict; 66 lowerable features trial never lowered (62 string counts, the IAT
  entry), 86 raise-only never moved. Its monotone detector detects more (87.6% vs 83.4% at 1% FPR) and **falls at the
  smoke** (5/11 within 100 candidates, each by signature cloning: the certificate's URLs raise `regex_https://`, which
  trial left free); the derived detector holds. Hypothesis (no new hole) failed. With the toolkit, trial absorbs LIEF's
  side effects (179 features) and detects 53.1%. Iterated adversarial training: estimated ~13-15 h pilot, needs a
  save option in `a1_adaptive.py` (R7-owned); recommended in. Run 144 scripted (176dbb8). **Next:** the user runs 144
  and decides; then `docs/resume-prompt-R18.md`.
- **2026-11-13 (session 59, rebuttal track): R2's 4-byte Rich fix.** When pefile finds the "Rich" marker it reads a
  4-byte key just past it, which can be the optional header's first four bytes; `RichHeader.items` now records them
  for files with pairs (pure addition; the empty case reads no key and is unchanged). Test `TestRichKey` (a synthetic
  file whose COFF header ends in "Rich") failed before the fix on the two linker-version bytes. As predicted, the pilot
  direction tables (`--loose` and without) are byte-identical before and after. Side note: the stored
  `a_directions_derived_sums_v2` no longer matches a fresh derivation without `--loose` (it lacks the `op_ent` column,
  and 3 `op_ren` cells differ: max_entropy, max_size_ratio, overlay_entropy); the M_* rows are identical, and the
  difference comes from the R7 commits of sessions 55-57, not this fix. Run 140's header claim "reproduces v2
  exactly" was true when written. **Next:** R18 (own session), then the last look before the scale-up.
- **2026-11-13 (session 58, rebuttal track): the triage table decided.** The four calibration items (R7, R1, R6, R17)
  match the earlier decisions; the triage leans slightly toward doing more than needed. Before the scale-up, in order:
  groups trust (R2) and erdalt (R19, split from baselines), then trial (R18), then a last look, then the scale-up;
  text fixes after it. Decisions and actions in `rebuttal/triage.md`. **Next:** `TAG=2026-11-12-body
  REBUTTAL_GROUPS="trust erdalt" docs/reviews/process/run_rebuttal.sh`. *Later:* trust and erdalt read and decided
  (R2: paragraph + 4-byte Rich-range fix; R19: training sound, finding stands, donor control); MAB rerun at Zainab et
  al.'s setting: yes. Before-scale-up items in PLAN.md step 3. **Next:** the 4-byte fix (own session); R18 runs
  elsewhere (`docs/resume-prompt-R18.md`).
- **2026-11-13 (session 57, R7 track): session 56's code re-verified; run 143 cleared.** Session 56 had been flagged by a
  safety classifier, so its four R7 commits were re-checked with fresh eyes. Engine decline (e0fa5b8): holds; it only
  replaces what used to raise, and on `74aecb25...` exactly the 16 error rows become declines, nothing else moves
  (the decline fires through the older locating check there, so `splits` is a backstop; tests added, 20bf742).
  Catalogue tests 228 passed. `ent` in the attack (868b8b6): holds; same 13 operations as the derived table; ent-only,
  full-menu and debug-escape smokes leave both `-loose` monotone detectors at 0 evaded, `min_delta_logit` 0; the
  models use none of the 1,474 neutralized features. Fixed (77587f5): the clone's byte bound now covers its padding
  (undercounted by up to 7 bytes), and escape runs record `start_in_population`, since the image_size escape takes
  every file out of the loose population (not an M_full operation), so its searches are not covered by the guarantee;
  run 143's header corrected. Noted, unchanged: the unconstrained `ref` model is from the v1 store (as in runs 105, 138).
  The user then started run 143 (8 workers). The resume prompt was rewritten for R7 and the decisions before the
  scale-up only (the review's triage now lives in `docs/resume-prompt-rebuttal.md`); PLAN.md step 2b gained (v), the
  decision on the other tables' monotone cells, and step 3 the scale-up's R7 items.

- **2026-11-13 (session 56, R7 track): run 142 read; `ent` in the attacks; run 143 scripted.** Run 142 (full pilot,
  LIEF's overlay rule): closed and sound, exact after one fix. 16 declared edits on one file's escaped copies raised an
  error -- a certificate inside `.rsrc`, stretched past the end, that an insertion before the overlay splits; the engine
  now declines an insertion that splits an item's members (e0fa5b8), re-checked on that file. Step 0's re-derived loose
  table matches the `-loose` models feature by feature. Then `ent` added to `a1_adaptive.py`'s menu and M_full (zero,
  past the end, signature cloning from signed goodware donors; 868b8b6), run 143 counts evasion from the unescaped
  originals (0949a9c), and `run/143_escape_pilot_loose.sh` written for the user (8a058d2). Smokes held: the loose
  monotone detector is not evaded under the full menu or by the debug-entry escape (where run 138 saw 4/41). Records:
  `docs/evidence/r7-overlay-rule.md` §7, PLAN.md step 2b. **This session was flagged by a safety classifier; the user
  therefore gated run 143 on a verification session that re-checks these four commits first (resume prompt).**

- **2026-11-13 (session 55, R7 track): the closure check; LIEF's overlay rule.** `catalogue_checks.py --loose` (`ent`,
  escaped copies far past, just past and inside the overlay; run 141). A session-53 bug fixed (the loose precondition
  exempted only the certificate's items; run 140's table unchanged). Closure failed through pefile's overlay rule; a
  trial fix (the overlay clause without the debug entry) closed the population but broke soundness (reverted). Claude
  first recommended modelling pefile's rule on our side; the user: pefile is not the gold standard for what an overlay
  is, findings should not hang on one parser's details, the options were not weighed equally (memory
  `may-deviate-from-ember`, rewritten). Reweighed with evidence: LIEF starts the overlay after the last section (54 of
  54 test copies unmoved); EMBER v2 has no overlay features; pefile's rule is deliberate (since 2016; PR #670). Scratch
  check with LIEF's rule on 50 files: closed, sound, exact; masks unchanged. The user chose it as a quick patch (f0d2bb1;
  `docs/upstream-issues.md` item 9), and raised designing the extractor deliberately, perhaps on LIEF (PLAN.md step
  2c). Documentation brought in line: CLAUDE.md (the principle "the parser is not the gold standard"; the code line),
  `docs/design.md`, the paper mock (the overlay sentence; the extractor's framing waits on step 2c), notes in the
  item-layer and threat-model records, code comments in `catalogue.py` and `catalogue_checks.py`, `scripts/README.md`.
  Commits aeeace0, f0d2bb1, 6173335 and the documentation commit. **Next (R7 track):** read run 142 (the user started
  it at 11:55), then step 2b (ii).

