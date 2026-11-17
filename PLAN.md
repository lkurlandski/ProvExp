# ProvExp Research Plan

Rewritten 2026-11-09 after a holistic review of the project. The session-by-session history of the plan
(2026-10-22 to 2026-11-09) is in `docs/archive/PLAN-log-2026-10-22-to-2026-11-09.md`; read it only to recover why an
old decision was made. The standing decisions (numbered; "decision N") are in `docs/decisions.md`. Deadlines and conference cycles are not a planning constraint (user).

## Thesis

For the feature extractors that security classifiers use (find the pieces of the input, add up what each piece
contributes, compute each feature by a formula over a few totals), the feature-space consequences of an attacker's
edits can be *computed* from the instrumented extractor: exactly for one edit (Proposition 1), and as sound directions
for a whole threat model (Theorem 1). Attacks and defenses usually obtain this knowledge by trial, from an analyst's
reading of the extractor, or from observed attacks. The computed answer is more correct than hand analysis, more
complete than constraints learned from attacks, and yields monotone detectors that no edit in the threat model can
evade (Corollary 1).

The framework is format-free (§3). PE malware with EMBER is the primary instance and the place where everything is
planned, implemented, and piloted first. Other domains come later, possibly, and the paper's structure must accommodate
them (below).

## Where the paper stands (updated 2026-11-14, session 62)

- **R7 and the rebuttal have closed the pre-scale-up work (sessions 48-62).** The simulated review's top risk R7 is
  resolved at pilot scale (no router, full widening, LIEF's overlay rule, run 143); R1, R6, R17, R2's code fix and
  R19's check are done; the extractor question is decided (stay on pefile, one audit pass to come). What remains before
  the scale-up: one last revisit of the review and rebuttal (anything else outside R18 and the scale-up?), the R18
  decisions on their own track, and then the scale-up itself. The rebuttal's text fixes wait for the scale-up's numbers.
  The bullets below are the session-45 assessment that set this course, kept for its reasoning.

- **§2-3 (the framework):** rewritten in the week of 2026-11-02; the user is reasonably satisfied. Pending: the user's
  holistic read of Sound Directions. Session 74 added Lemma 1 (*Closure*) and the readout rule (next step 8).
- **§4:** drafted in the template structure, reviewed twice by Claude (sessions 38, 40); ~1,700 words against ~1,000.
- **§5:** three findings (decision 10), drafted, reviewed per subsection and as a whole, tables remade (sessions
  41b-44). The user has not read it end to end.
- **§6:** drafted. **§1, §7, abstract, ethics, open science:** empty (last, by decision). Body ~13,000 words against
  the mock's 11,000.
- **Experiments:** complete at pilot scale (10% subsamples, one seed, 50 malware attacked).
- **The holistic assessment (session 45, agreed by the user):** the framework is in good shape; what decides the paper
  now is §5's evidence, held back by sample size more than by prose. 5.3 (observed attacks) is the strongest finding and
  the one only the derivation makes (PV's hole named before any attack), but PV is judged on 9 files, ERDALT invites
  "your port is weak" (AUC .88 against their 93%, one epoch), and every evasion comes from our own table-guided attack
  (MAB-Malware, which renames sections, is absent). 5.4 (cost) has a solid expert-set comparison; the rest is a number
  that needs seeds 0-2 and full splits; its 0 evaded follows from the theorem. 5.2 (hand analysis) is the weakest: our
  own hand table, score drops that never cross the threshold (10 of 29), the expert set evaded on 2 of 8. Beyond §5:
  one domain (the largest acceptance risk; the user's call when); Proposition 1 has no finding of its own (R9, §2's
  attack promise); the 4 MB truncation decides the population the scale-up runs on; the body must eventually shrink,
  but shortening before the scale-up would be redone. So the review and the scale-up come before the remaining polish.
- **The simulated review of 2026-11-12** (`docs/reviews/2026-11-12-body/meta-review.md`): Weak accept (A, formal
  methods), Weak reject (B, adversarial malware; C, robust ML), Weak accept (D, systems security). All four find the
  idea new and value the PV hole and the cost result; all four call §3's results known techniques (IVM, sign-domain
  abstract interpretation; R6), the EMBER premises tested rather than proven (R2), and one instance too few for a
  class (R4). B, C and D's "one change" is the same: the routed system end to end (R7). Register R1-R21, the scale-up's
  content (§7) and the writing actions (§8) in the meta-review. Triaged so far: R7 (decision 11), R1 (decision 12),
  R6 (session 50: four citation edits in §3 and §6, `docs/evidence/r6-prior-work.md`).

## Next steps, in order

Agreed with the user in session 45 (2026-11-12) after the holistic assessment (above). The previous list, with the
records of the §5 reviews, the table remake and the ERDALT check, is in
`docs/archive/PLAN-next-steps-2026-11-12-s44.md`.

1. **Done in session 46: files below 4 MB in every split** (decision 8 (iv)).
2. **Done (sessions 48-61): the full simulated review**, its register triaged.
2b. **Done (sessions 53-62): R7's widening complete at pilot scale** (decision 11's final form).
2c. **The extractor question: decided (user, session 62) — stay on pefile.**
   Steps 1-2c in full: `docs/archive/PLAN-done-steps-2026-11-17.md`.
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
   **Next:** the chain finishes (walltimes for the attack steps from their measured tasks), then read it (step 5).
4. **While the scale-up runs: §2's closing and contribution 4 against §5** (old step 2 (c)). §2 says §5 "uses them to
   attack malware detectors and to build robust ones"; in §5 the attack is an instrument. The mock's contribution 4 is
   stale ("four to six points", "learned constraints"). Writing only.
   Also here (session 63), since they need no numbers: the rebuttal's number-free text fixes R4 (claims scoped "on
   EMBER", what falls outside the class), R5 (Pierazzi et al.'s reason and minimal-app estimate), R15 (the attacker
   named) and R21 (certified defenses; Cortellazzi, Kantchelian, Lucas 2024, Tsingenopoulos still uncited). The
   number-dependent ones (R2's paragraph, R3, R8, R12, R13, R19) stay with step 5.
5. **After reading the scale-up:** the final numbers into §4-5 and the open items (below); then shorten §4 and §5
   together (§4.3 first) and give §5's questions and answers more visual emphasis (old steps 2 (b) and (0)).
6. **Decide on a second domain** with the scale-up's results in hand (the user's call; ideas in
   `docs/domain-selection-brainstorming.md`; no literature or selection work until the user opens it). A second
   instance would strengthen 5.2-5.3 most (decision 10).
7. **The introduction, discussion, abstract, ethics and open science** last, once the body is settled.
8. **The theory track (parallel to the scale-up; opened in session 74, 2026-11-16).** The user wants the paper's
   theoretical contributions made stronger. Record: `docs/evidence/theory-analysis.md`; next session:
   `docs/resume-prompt-theory.md`.
   (a) *Done:* the proof audit (seven small corrections to §3 and Appendix C); **Lemma 1 (*Closure*)** in §3.3: a
   population bounded by features that the derived table does not allow to rise is closed, so closure follows from
   covering and the table where the population is defined through items; **the readout rule**: one rule (the sums a
   readout rises and falls with) in place of Table 1's six, used by Definition 10. The user approved both after a
   brief look; a close read is pending.
   (b) *Next:* choose a direction with the user. Candidates on record: item size (no monotone trade-off; tables
   from different item maps combine), the blind spot of a table learned from attacks (a statement behind §5.3), side
   effects and the host (a consequence of Proposition 1), threat models add up (behind §5.4's per-operation
   reading). **Bounds on size instead of signs is open and wanted by the user** ("an incredibly meaningful
   direction"); direction A' (graveyard, 2026-11-02) predates the present framework and does not settle it.
   *Session 75:* the user chose bounds on size (the four small ideas are set aside). The mathematics note is
   `theory-analysis.md`, part F, waiting for the user's review and four decisions (F.7); no experiment and no
   manuscript text before that.
   *Session 76:* reviewed by the user (the statement is the one meant; simpler is wanted); the read of the pilot's
   derived table says that at the paper's budget nothing can be shown on EMBER; the user's idea of a relaxed
   ("somewhat monotone") detector needs sizes and has little room on EMBER; the statements in final form, with
   proofs, the closest work and the options for the manuscript, are part H. **Waiting: the user's decision on what
   enters the manuscript** (H.9), worked out with Opus. First to think through: H.5 (strict monotonicity loses no
   guaranteed detection under directions alone) and whether §5.4's price may be read through it.
   (c) *Follow-ups, not started:* the instance-level work for Lemma 1 (the population's clauses as counts over
   items, the derived table rebuilt, the nine in-place and append operations confirmed, the four layout-moving ones
   decided; only then §4.4's "closure is checked rather than proven" changes); `monotone_violations` called in
   `4-detectors/train` before the scale-up trains (§5.1's blue sentence); optionally the tighter normalized-bin rule
   in `reach.py`.
   (d) *Closed in sessions 71-73, not to reopen without the user:* converses of Corollary 1, a bound on the cost of
   robustness, extractor redesign for robustness.

Open items (fix when the affected text is touched): **the sample-read signature's claim (decision 12):** §4.3.2's last sentence and §5.1's *Checking results* say the table from 100 files equals the one from 2,000, so the sample-read part "does not depend on which files were read"; at scale the 20,000 training files add 98 directions the 2,000 evaluation files do not show. Rewrite both to the held-out check (the training table covers the evaluation set; more files only add moves, so a larger sample errs on the conservative side) with the user, after the files behind the new moves are known. **the checks recounted on the files below 4 MB** from stored
outputs, no runs (decision 8 (iv); with the next item): 5.1's edit counts, Table 3's file counts, Appendix D's counts and
Table 9 (outside the population: 42 wrong edits on 6 files instead of 45 on 7; session 46).
5.1's "73,063 edits" is run 107's direction check, the exactness
counts are Appendix D's (62,604 + run 118's 34,965); 5.2's "before the derivation existed" (check the history before
rewording); Table 5's toolkit cells come from the fixed-seed runs (`a1/toolkit-v2`), Table 4's from run 133's seed per
file (one protocol at the scale-up, nothing in the paper).
