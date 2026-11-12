# Session log, sessions 29-33 (2026-11-10 to 2026-11-11)

Moved from `docs/status.md` on 2026-11-12. Search, don't read.

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
