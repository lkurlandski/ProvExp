# Session log, sessions 29-39 (2026-11-10 to 2026-11-11)

Moved from `docs/status.md` on 2026-11-12. Search, don't read.

- **2026-11-11 (session 34, continued): run 133 read.** Results and hypotheses in its header; design doc §10.4-10.5.
  PV-best evaded 4/9, each by one rename; it detects 26.2% at 1% FPR. Not the 8 broken shift outputs (run 134,
  PV-clean: 26.7%; `a_pv_hole.py --drop_import_loss`); partly that PV constrains features no attack moved (PV-free,
  never-moved left free: 50.9%; `pv-free.monotone.tsv`). ERDALT-best 24/29 by gamma_api with the pilot donors;
  adversarial training 12/50 and 23/50. The user agreed with §10.5's claim, but kept leave-one-out: redone the fair
  way as run 135 (folds from run 133's outputs; ERDALT on every visible GPU, threads = NUM_WORKERS / lanes; no
  `GPUS` variable, CLAUDE.md updated). PLAN.md decision 10 and the mock's 5.3 rewritten. **Next:** read run 135;
  then the audit table and 5.3's prose.

- **2026-11-11 (session 34): §5.3 redesigned; PV's hole traced to the attack harness's fixed seed.** An overview,
  harsh analysis and options for §5.3, then re-assessed against the plan, mock and code at the user's request:
  `docs/evidence/section-5.3-design.md` (nine disagreements between draft, mock and code: PV learned from the test files;
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

- **2026-11-11 (session 37): §5.4 reviewed by Claude and revised.** At the user's request, Claude reviewed §5.4 with
  the `humanistic-paper-review` skill instead of the user reading it. The user agreed with the headline findings,
  less with the small ones (recurring patterns, term ledger). Applied: the subsection reordered so no paragraph points
  forward (price, where the guarantee holds, where the cost lies, width, hand-picked, beyond the guarantee); *Where
  the cost lies* opens with its finding, explains rename (frees 301 features, recovers 0.1 points) and append at
  0.1% FPR (retraining variance; Claude's inference); *Beyond the guarantee* counts files per detector and attack
  (from `a1/toolkit-split/split.json`); the opening says why the sums; Table 4's caption states its takeaway.
  Commits c49f654, 9113acb, 23ab085. **Next:** a holistic review of §4, then §5 (`docs/resume-prompt.md`).

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

- **2026-11-11 (session 39, parallel to 38): §5.3 drafted in three blocks.** Run 135 had just started, so its
  ERDALT folds are in blue (its PV folds finished during the session: 0 evaded in all eight). User decisions: cut the
  learned-region paragraph; no audit table now (Tables 3-4 to be remade); one sentence on rename, no new run; no RNG or
  protocol-hygiene details in the paper. Found: the planned "745 vs 928" coverage comparison mixed files (pilot vs
  training); on the same files it is 847 vs 928, and it is out anyway. Old 5.3 material removed from 5.4; §6's ERDALT
  reference points to 5.3; Appendix D gained the leave-one-out table. ~970 words. The user did not review the blocks
  (review next session). Commits 7a2ceff, 9d0369f, 035d977. **Next:** `docs/resume-prompt-5.3.md`.
