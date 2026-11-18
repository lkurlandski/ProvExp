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

## Where the paper stands (updated 2026-11-17, session 79)

- **Every result is being re-run at scale** (step 3, running on tigris). Until it is read, the paper's numbers are
  pilot values (10% subsamples, one seed, 50 malware attacked) with `% PROTOCOL` comments, and blue predicted values
  where a pilot run was deferred; step 5 replaces them all.
- **§2-3 (the framework):** the user is reasonably satisfied. Pending: the user's holistic read of Sound Directions,
  and a close read of Lemma 1 (*Closure*) and the readout rule (added in session 74, approved after a brief look).
- **§4:** drafted in the template structure, reviewed twice by Claude; ~1,500 words against ~1,000, shortened with §5
  after the scale-up.
- **§5:** three findings (decision 10), drafted and reviewed per subsection; the user has not read it end to end. The
  review's R7 (decision 11: no router), R1 (decision 12: MAB-Malware) and R18 (the trial row) are written in.
- **§6:** drafted, cut to ~1,280 words in session 84 (mock 1,000; length accepted). **§1, §7, abstract, ethics, open science:** empty, last by decision. Body ~13,000 words against
  the mock's 11,000.
- **The simulated review of 2026-11-12** (`docs/reviews/2026-11-12-body/meta-review.md`): two weak accepts, two weak
  rejects; register R1-R21, every item triaged (`rebuttal/triage.md`). Number-free text fixes are step 4, the
  number-dependent ones step 5.
- **Theory (step 8):** bounds on size worked out (`docs/evidence/theory-analysis.md`, parts G-H); the user decides
  what enters the manuscript.
- **The largest open risks:** one instance only (a second domain is step 6, the user's call), and ERDALT at scale:
  every model collapses to validation AUC ~0.70 (pilot 0.88) and misses its criterion, which invites the straw-man
  objection; its own track since session 82 (`docs/resume-prompt-erdalt.md`).

## Next steps, in order

Agreed with the user in session 45 (2026-11-12) after the holistic assessment (above). The previous list, with the
records of the §5 reviews, the table remake and the ERDALT check, is in
`docs/archive/PLAN-next-steps-2026-11-12-s44.md`.

1. **Done in session 46: files below 4 MB in every split** (decision 8 (iv)).
2. **Done (sessions 48-61): the full simulated review**, its register triaged.
2b. **Done (sessions 53-62): R7's widening complete at pilot scale** (decision 11's final form).
2c. **The extractor question: decided (user, session 62) — stay on pefile.**
   Steps 1-2c in full: `docs/archive/PLAN-done-steps-2026-11-17.md`.
3. **The scale-up: one protocol, every paper number from it** (designed with the user in sessions 63-78). The full
   record, items (a)-(g) and (1)-(16) with every decision and its reasons, is `docs/scaleup-protocol.md`; "step 3 (g)"
   and the like refer to it. In short: one seed (0); an evaluation set of 1,000 malware and 1,000 benign complete test
   files; every detector trained on the full training split's complete files, thresholds from the validation split,
   donors from training goodware; the toolkit, the adaptive search (5,000 extraction-scored candidates), MAB-Malware
   (three settings) and the escapes; the learned defenses from one shared material; the trial row and iterated
   adversarial training as competitors. Submitted on tigris by `pipeline/submit.sh`. Done at scale: everything through
   the defenses' material, `train`, `price-list`, the learned defenses' GBDTs, MAB-Malware's expert setting (rerun in
   session 81 with the full donor set), `iterated`'s round 1 and `iterated-1`. Also done: `iterated` (both rounds,
   `iterated-2`) and MAB-Malware `zainab`. Session 81 fixed the thread overload behind two failures and parallelized
   the adaptive search's setup (item (15)). Session 82 (item (16)): the file store at one fixed location with no
   fallback; ERDALT's collapse set apart as its own track; `toolkit`, `adaptive` and MAB-Malware `ours` resubmitted
   without ERDALT. Session 85: `toolkit` and `adaptive` done; MAB-Malware `ours` patched for zero-section files and
   resubmitted; open: 3 lost adaptive searches (diagnostic queued) and PV's 5/1,000 detection at scale (the user's
   call). Session 85 continued (item (17)): PV's collapse traced to broken outputs (an upstream shift bug among them)
   and sample size; one validity rule for the paper to be decided; PV's sample-size experiment designed and deferred.
   **Next:** the experiments track (`docs/resume-prompt-experiments.md`) and the
   ERDALT track (`docs/resume-prompt-erdalt.md`, which then runs ERDALT's attacks and `6-results`); then read it all
   (step 5).
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
