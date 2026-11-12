# Status

Kept short: the current state, what waits on the user, and the last few sessions in a line or two each. The plan and
its reasons are in `PLAN.md`. When the session log below grows past about ten entries, move the oldest to
`docs/archive/` (the log before 2026-11-09 is `docs/archive/status-log-2026-10-to-2026-11-09.md`; sessions 21-28 are in
`docs/archive/status-log-2026-11-09.md`).

## Current state (2026-11-12, sessions 34-40)

- **Framework (§2-3):** rewritten; the user is reasonably satisfied. Open: the user's holistic read of Sound
  Directions after round 4 (finetuning only).
- **§4:** drafted in the new structure (lead, 4.1-4.4, Appendix D "The EMBER Instance"), then revised in session 38
  after Claude's review with the `humanistic-paper-review` skill (all eight findings applied; 4.3 split into
  *Operations* and *Signature*; 4.4 reordered). Second, lightweight review in session 40 (three findings, all
  applied: 4.3.2 states what the sample-read signature rests on; closure "checked rather than proven"). §4 is in good
  shape. About 1,500 words against ~1,000; further shortening with §5 later.
- **§5:** realigned with §3-4 in vocabulary and claims (session 29). Structural rewrite agreed in session 30 (PLAN.md,
  decision 10): three findings (what hand analysis misses, what observed attacks miss, what robustness costs), not a
  validation section and not a defense paper. Plan, one line per paragraph, and checks C1-C3: `docs/paper-mock.md`,
  §5. Blocks 1-2 (lead, 5.1, 5.2) drafted and revised twice (session 35: lead and 5.1 after the user's second review,
  up to 5.1's Attacks paragraph; the user has not yet commented on 5.1's last paragraph or on 5.2's second round).
  **Block 3 (5.3 *What Observed Attacks Miss*)** drafted in session 39 (7a2ceff, 9d0369f, 035d977), unreviewed;
  run 135's values filled in session 40, so §5 has no blue values left. **Block 4 (5.4 *What Robustness Costs*)** drafted in session 36,
  revised in session 37 after Claude's review with the `humanistic-paper-review` skill (reordered so no paragraph
  points forward; commits c49f654, 9113acb, 23ab085); the user has not read the revised text.
- **§5.3** is drafted (session 39) from the claim agreed in session 34 (`docs/section-5.3-design.md` §10.5, which
  stays the record of how the design came about). Learned-region paragraph cut, no audit table for now (tables
  remade later), no seed or protocol-hygiene details in the paper (user). Every learned defense is built from run 133's
  3,183 outputs; PV evaded 4/9 by one rename, 26.2% TPR; ERDALT 24/29 by its own attack; adversarial training 12/50
  and 23/50; leave-one-out per fold in Appendix D.
- **Experiments:** Tables 3-5 (side effects, directions, detectors) complete at pilot scale; open items are listed in
  PLAN.md, next step 5. Run 131 (leave-one-out) finished: PV 5/21 on gamma_api, 0 elsewhere; ERDALT high on
  gamma_api and header_fields; ERDALT-8 adaptive 17/24. Runs 132 (coverage by source, seed smoke), 133 (§5.3 Phase
  2, ~4.8 h) and 134 (PV-clean, PV-free; Claude, ~3 min) done and read. **Run 135** (leave-one-out from run 133's
  outputs) finished 2026-11-11 19:54 (~3.4 h) and read in session 40: PV 0 evaded in all eight folds; ERDALT 25/29
  when GAMMA imports is held out, 0-2 in the other seven (header_fields 2, not the predicted ~10). Results in its
  header and in `docs/section-5.3-design.md`'s log.
- **Documentation:** reorganized 2026-11-09; index `docs/README.md`.

## Waiting on the user

- **The review of §5** (lead, 5.1-5.4; the two parallel tracks have merged now that 5.3 is complete). The user
  has not read 5.3 or the revised 5.4; their own pending comments on 5.1's Checking results and 5.2 (9b7d0ba) can
  join. The user decides how (their own read, or Claude's `humanistic-paper-review` first).
- The holistic read of Sound Directions (any time).

## Scheduled

- **Next full simulated review:** after §4-5 are realigned, before the introduction; update
  `docs/reviews/review-prompt.md` right before running it (PLAN.md, next step 4).
- **Brainstorm on the 4 MB truncation** (the plain-layout population's gap), just before or after that review (PLAN.md,
  decision 8 (iv) and step 4).

## Session log

- **2026-11-12 (session 40): §4's second review; run 135 read.** Claude's lightweight review of §4 (three findings,
  all applied in 75c1c9c): 4.3.2 names what the sample-read part of the signature rests on and what §5.1 checks (the
  directions from 100 files equal those from 2,000; no edit moves a feature against them); its two consequences of a
  write onto a located position sit together; 4.4 says closure is checked rather than proven. Run 135 read (hypotheses:
  PV and ERDALT's gamma_api fold held; header_fields and the mean failed); 5.3's *Holding one attack out* and Table 9
  rewritten with the real values (the finding unchanged). The two resume prompts' tasks are done except the §5 review.

- **2026-11-11 (session 39, parallel to 38): §5.3 drafted in three blocks.** Run 135 had just started, so its
  ERDALT folds are in blue (its PV folds finished during the session: 0 evaded in all eight). User decisions: cut the
  learned-region paragraph; no audit table now (Tables 3-4 to be remade); one sentence on rename, no new run; no RNG or
  protocol-hygiene details in the paper. Found: the planned "745 vs 928" coverage comparison mixed files (pilot vs
  training); on the same files it is 847 vs 928, and it is out anyway. Old 5.3 material removed from 5.4; §6's ERDALT
  reference points to 5.3; Appendix D gained the leave-one-out table. ~970 words. The user did not review the blocks
  (review next session). Commits 7a2ceff, 9d0369f, 035d977. **Next:** `docs/resume-prompt-5.3.md`.

- **2026-11-11 (session 38): §4 reviewed by Claude and revised.** Review with the `humanistic-paper-review` skill
  (eight findings). The user: trimming is good, but moving small snippets to the appendix does more harm than good;
  findings applied in two passes (the easy ones first, so the user can focus on the rest). Applied: attack names
  follow Table 2's operations, with a toolkit-attacks column (from secml-malware's code); the Zainab et al. sentence
  dropped (MAB-Malware uses code randomization, which the threat model excludes); "certificate table" for the
  structure, "Authenticode signature" for its content (Table 8's row renamed too); §4.2's item list shortened; the
  lead names the sum-then-readout form; 4.3 split into subsubsections *Operations* and *Signature*, the latter opening
  with what is proved and what rests on the files; 4.4 reordered (closure after the definition, counts tied to
  §5.1's 73,063 edits and 2,000 test files, routing last). Commits c7d0734, cf4f4a4, b8b710c. For §5: it still says
  "GAMMA's import injection" and "the header-field attack" (Table 2: GAMMA imports, header fields) and Table 3 says
  "signature table" for the certificate table. **Next:** a lightweight re-review of §4, then §5
  (`docs/resume-prompt.md`).

- **2026-11-11 (session 34, continued): run 133 read.** Results and hypotheses in its header; design doc §10.4-10.5.
  PV-best evaded 4/9, each by one rename; it detects 26.2% at 1% FPR. Not the 8 broken shift outputs (run 134,
  PV-clean: 26.7%; `a_pv_hole.py --drop_import_loss`); partly that PV constrains features no attack moved (PV-free,
  never-moved left free: 50.9%; `pv-free.monotone.tsv`). ERDALT-best 24/29 by gamma_api with the pilot donors;
  adversarial training 12/50 and 23/50. The user agreed with §10.5's claim, but kept leave-one-out: redone the fair
  way as run 135 (folds from run 133's outputs; ERDALT on every visible GPU, threads = NUM_WORKERS / lanes; no
  `GPUS` variable, CLAUDE.md updated). PLAN.md decision 10 and the mock's 5.3 rewritten. **Next:** read run 135;
  then the audit table and 5.3's prose.

- **2026-11-11 (session 37): §5.4 reviewed by Claude and revised.** At the user's request, Claude reviewed §5.4 with
  the `humanistic-paper-review` skill instead of the user reading it. The user agreed with the headline findings,
  less with the small ones (recurring patterns, term ledger). Applied: the subsection reordered so no paragraph points
  forward (price, where the guarantee holds, where the cost lies, width, hand-picked, beyond the guarantee); *Where
  the cost lies* opens with its finding, explains rename (frees 301 features, recovers 0.1 points) and append at
  0.1% FPR (retraining variance; Claude's inference); *Beyond the guarantee* counts files per detector and attack
  (from `a1/toolkit-split/split.json`); the opening says why the sums; Table 4's caption states its takeaway.
  Commits c49f654, 9113acb, 23ab085. **Next:** a holistic review of §4, then §5 (`docs/resume-prompt.md`).

- **2026-11-11 (session 36): §5.4 *What Robustness Costs* drafted (blocks 1-2, unreviewed).** Numbers checked
  against their sources (two mismatches: "the rest at most 0.3" is 0.4 for the debug and signature removals; the sums
  row's adaptive footnote has no matching run, the closest is run 82, append and add-section only; the user judged
  the latter not worth raising, so the cell stays 0% with an accurate footnote). The user rejected scaling the
  full-training-set adaptive cells down to the 10% protocol and single-attack toolkit columns (memory
  `report-attacks-separately` now scoped to stitched searches). Drafted, in order: the price (89.6 vs 93.5% at 1% FPR;
  74.7 vs 84.4% at 0.1%), against hand-picked features (the expert set 29.1% vs the derived additions detector 92.2%,
  the practitioner-facing result), where the cost lies (imports 2.1, header overwrites 1.4, others at most 0.4; at
  0.1% dropping the two-sided features alone costs 5.2), the threat model's width, beyond the guarantee (GAMMA's
  rebuilding injections, 0/56, 0/60), where the guarantee holds. Table 4 trimmed (undefended and monotone rows,
  additions block; one toolkit column, any of the eight; new TPR-at-0.1%-FPR column, computed from the models'
  `ts_predictions.parquet`); the PV/ERDALT/adversarial-training rows kept in a `% MOVED TO 5.3` comment, their
  paragraphs marked `% 5.3 MATERIAL`; the cost paragraph removed. Found: the coverage check (915 of 1,070 lowered) is
  about two-sided features the detector drops, so it says nothing about the constraints that carry the cost; not used.
  The user ended the session tired and disappointed with the last two days. Commit 8fd8c9c. **Next:**
  `docs/resume-prompt.md`.

- **2026-11-11 (session 35): §5 lead and 5.1 revised after the user's second review; §5.4 next.** The `% VERIFY` in
  5.2 settled (elastic/ember's code): Severi et al.'s EMBER (feature version 1, 2,351 features) hashes section names,
  imports and exports into the same buckets as EMBER 2024, but not the entry name, the characteristics, five header
  fields, or a Rich header; the prose now counts only the shared groups (1,430 of 1,558 movable under additions).
  Lead: §2's three limits instead of "each falls short". 5.1 in three run-in paragraphs (Detectors, Attacks, Checking
  results); the learned-defense protocol (leave-one-out) removed from 5.1 and left to 5.3; the toolkit attacks are
  black-box, one kind of edit, 100 queries; the adaptive attack is white-box, in the spirit of Tramèr et al. (added to
  `papers/` and `main.bib`), each with its reason; the beam's mechanics moved to Appendix D; the 500-query check to a
  comment. The user's harsh reaction to the first Attacks rewrite logged (`docs/writing-spec.md`); one sentence on
  purpose-then-facts added to `paper-prose`. Scale-up: the first thing after the write-up (user; PLAN.md step 5).
  Commits 0b64c9a, e3375ca, 9b7d0ba. **Next:** §5.4 in a new session (`docs/resume-prompt.md`).

- **2026-11-11 (session 34): §5.3 redesigned; PV's hole traced to the attack harness's fixed seed.** An overview,
  harsh analysis and options for §5.3, then re-assessed against the plan, mock and code at the user's request:
  `docs/section-5.3-design.md` (nine disagreements between draft, mock and code: PV learned from the test files;
  GAMMA's names identical on every file; PV's hole not mostly section names for PV-4; the "51% vs 53%" control
  invalid, the in-catalogue toolkit evades 13/49; the learned region shows nothing beyond PV's hole; ERDALT's 89.7% is
  a sufficient-rule check). Run 131 read (header, record). Run 132 (`scripts/a_coverage.py`, `a_advtrain.py
  --seed_per_file`): only 2 of 1,070 lowerable features need operations the toolkit lacks; our own edits lower 915;
  90 of those the toolkit never lowers, 82 section features; with a seed per file, one attack covers all 50 size,
  entropy and virtual-size buckets (fixed seed: 13, 21, 33) and closes 71 of the 90. User: do what is best for the
  research, not what prior work did; fix design gaps; runs over ~10 min go to the user. Phase 2 scripted and
  smoke-tested: `run/133_varied_observation.sh` (`a1_evaluate.py --seed_per_file`, `a_pv_hole.py --adv_dir`). Commits
  e176432, c2a117d. **Next:** the user runs 133; this session reads it; another session takes the 5.1-5.2 feedback
  (`docs/resume-prompt.md`).

- **2026-11-11 (session 33): run 131 partly read, C2 checked; §5.3's methodology to restart.** Run 131's ERDALT
  evaluation had crashed on a model-path bug (training wrote `seed-0-loo-*`, evaluation read `seed-0-s10-loo-*`);
  folders renamed, script fixed (finished steps skip), rerun by the user. PV leave-one-out: gamma_api 5/21, other
  seven folds 0 (user's hypothesis failed, Claude's held). C2: the toolkit lowered 745 of the 1,070 lowerable
  features (all 512 byte statistics, 233 of the other 558); the mock's "small minority" failed. Discussion of how to
  test learned defenses (mean vs worst fold, keep-one, MAB-Malware, all subsets) judged low quality by the user;
  recorded with strengths and weaknesses in `docs/evidence/held-out-attacks-perspectives.md`. **Next:** a fresh
  overview and analysis of §5.3 (`docs/resume-prompt.md`).

- **2026-11-10 (session 32): leave-one-out scripted and started (run 131).** `run/131_loo_defenses.sh`: eight PV folds (selection
  from seven attacks, the held-out attack run against the fold's model), nine ERDALT models on two GPUs, the beam
  against ERDALT-8, a summary. Smoke: PV's gamma_api fold in full, 5/21 held out (PV-seen 4/22). The deltas predict
  the user's hypothesis (PV well above 0) fails on the mean: the attacks lower nearly the same features (only
  gamma_sections, 49, and gamma_api, 10, lower many the others don't). ERDALT's folds for the four originally held-out
  attacks would learn from ~50 pilot vectors of them, not ~400 (run 122 generated only the seen four); on the user's
  approval, step 0 now generates the other four on the same 400 training malware (`--adv_dir` takes several
  directories), and ERDALT trains on one or two GPUs, whichever are visible. Started by the user on GPU 3 (~7 h).
  **Next:** `docs/resume-prompt.md` (read run 131; C2; block 3).

- **2026-11-10 (session 31): §5 blocks 1-2 drafted, reviewed, revised; extension strategy and leave-one-out
  agreed.** Block 1 (lead, 5.1; the side-effect table to Appendix D, tables renumber: directions 3, detectors 4, side
  effects 8) and block 2 (5.2 *What Hand Analysis Misses*). Checks: C1 held (median 263 features per edit, 4-8 groups);
  C3 found Severi et al. (all hashed features "extremely difficult" to manipulate; the derived table moves 1,490 of
  1,650 under additions; EMBER 1.0's hashed groups still to verify). The user asked whether §5's structure suits other
  domains: yes (findings follow §2's sources, each a measurement per instance); drafting rules recorded in the mock,
  §5, "Extending §5 to other domains". The user's review of blocks 1-2 (reaction log): toolkit attacks moved into
  §4.3 and cited to Demetrio et al.; no "pilot scale" or "written to disk" bookkeeping; one edit set (73,063) defined
  in 5.1; 5.2 opens with its question and has run-in headings; the seen/held-out split replaced by leave-one-out
  (the fixed split had held out the strongest attack on purpose), implemented by session 32 (run 131). Commits
  b68edd1 to 0069f56. **Next:** the user's feedback on 5.1-5.2 (2026-11-11), then 5.3 from run 131.

- **2026-11-10 (session 30): §5's structure agreed, no prose.** The user's concern: §5 is organized to show the
  implementation is correct and the proofs hold ("transactional and somewhat lifeless"). Assessment: right; about a
  quarter to a third of §5 checks our own work and comes first, because the mock organized §5 by §3's results. A
  defense-first alternative was rejected by the user (4 points of TPR is not small to them, about 1% or less wanted;
  three baselines too few for a defense claim); the attack alone is too weak to be a task. Agreed: three findings
  that test §2's claim about trial, hand analysis, and observed attacks; the side-effect table to Appendix D; a new
  audit table in 5.3. No new task needed; three checks on existing outputs (C1-C3). Recorded: PLAN.md decision 10,
  `docs/paper-mock.md` §5, memory `findings-not-defense-paper`. **Next:** `docs/resume-prompt.md`.

- **2026-11-10 (session 29): §5 realigned; the per-candidate cost measurement dropped.** A probe showed Prop. 1 scoring
  in Python is no faster than thrember's (optimized) extraction; the user: never measure or compare it, say the
  computation is smaller and can be faster; optimization is engineering, out of scope (PLAN.md decision 6, memory).
  §5 rewritten in three quick blocks (commits after f1d6050): 5.2 claims what it tests ("The Instance Is Correct",
  Declined instead of Flagged, no speed claim), 5.3 gains the corpus check of the signatures, 5.4 points to §4.4 for
  closure; §6's "our margins" fixed. **Next:** the user's structural concerns about §5, then shortening §4-5.
