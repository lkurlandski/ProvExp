# PLAN.md's "Next steps" as of session 44 (2026-11-12)

Replaced in session 45 by the order agreed after the holistic assessment. Kept for the records of steps 1-3 (the §5 reviews, the table remake's two attempts and the facts they surfaced, the ERDALT check).

## Next steps, in order

Done: the paper mock rewritten, the read-only code audit (`docs/evidence/code-audit-sound-directions.md`), decision
7's edits, §4 rewritten and reviewed twice (sessions 38, 40), §5 rewritten in four blocks with run 135's values filled
(session 40). The order agreed with the user on 2026-11-12:

0. **First, a holistic assessment of the research's progress and a planning stage (user, session 44).** The user is
   "not confident" that the items still listed in step 2 ((0), (b), (c)) are the ones to pursue next. Assess where the
   research stands as a whole (thesis, framework, instance, evaluation, the paper's state, what a reviewer would
   attack, what the scale-up must settle) and plan the next steps with the user; the steps below are candidates, not
   an agreed order, until then. Resume prompt: `docs/resume-prompt.md`.

1. ~~**The humanistic review of §5, one subsection per pass.**~~ Done in session 41b (2026-11-12): all four passes,
   the user approving each finding (status log).
1b. ~~**A holistic humanistic review of all of §5**~~ (contributions' importance). Done in session 42 (2026-11-12):
   seven findings; 1-4 approved and applied (68f6385: what Gimenez et al. report before our results, the lead names
   what breaks, 5.4 names both alternatives, the hand detector's cost ends on why a broken guarantee matters); 5 (5.3's
   topic sentences) dropped after Claude's reassessment (the user was not convinced; the leads now carry the outcome
   for a fast reader); the uncited "usually tested against an attack it did not learn from" fixed (49d879d: Gimenez
   et al. test against the attacks they learned from; the held-out test is the stricter one); 6 and 7 noted below
   (step 2 (a), (c)).
2. **Then, to be considered with the user, in this order (user, session 42: the tables first):** (a) remake the tables
   (Tables 3 and 4 above all; the user dislikes them); (0) §5's questions and answers given more visual emphasis (user,
   2026-11-12: how each subsection's research question is "asked" and its finding "answered"; a structural change, not
   made in the review); (b) shortening §4 and §5 together (§4 ~1,500 words against ~1,000; §4.3 first); and (c) §2's
   closing sentence and contribution 4 against §5's three findings.
   *(a), second attempt (session 43), done for Tables 3 and 4* (7788592, 52e07cc; status log): one column each, data
   only, short labels, arrows, bold best, one-line captions, no footnotes; the adaptive results moved into 5.4's text;
   5.2's *Why it errs* names all five parser facts (fact (1) below, fixed); the paper no longer shows the full-set
   unconstrained detector's 27/49 (fact (2) below no longer visible). The user wants Table 4's two halves more
   consistent (same detectors in both; may need runs, so at the scale-up). **Open, next session:** whether §5 gets
   more tables at all (5.3's result, finding 6 below; the per-operation cost of *Where the cost lies*), to be thought
   through with the user, not proposed (user, session 43).
   *(a), session 44, done:* 5.3 got a table (d87603f; Table 4, *Defenses learned from the outputs of the toolkit
   attacks*: unconstrained, PV, ERDALT, adversarial training; AUC, TPR at 1% / 0.1%, evaded by the toolkit / the
   adaptive attack); *Where the cost lies* stays prose; no other tables. Finding 6 below is closed. Left for the
   scale-up: Table 4's unconstrained row (full training set, 25/49) and Table 5's (10% subsample, 26/47) are different
   detectors with the same label; train every detector on one training set.
   *(a), first attempt (session 42), rejected:* the user's brief: tables "data-dense" rather than "linguistically-dense"
   (exceptions allowed), designed to (i) communicate the findings, (ii) be aesthetically pleasing, (iii) extend to other
   domains (least important). Claude's mock-ups (`docs/archive/table-mockups-2026-11-12/`: Table 3 with Cause and
   Files columns; a new 5.3 table of the learned defenses with a "weight on lowerable" column; Table 4 in one column; a
   per-operation cost table; alternatively one detectors table grouped by where the directions come from) were judged
   "pretty bad, quite possibly as bad if not worse than what we already had", with no specifics. Restart from what the
   user dislikes, not from a new layout (resume prompt). Facts the attempt surfaced, still valid: (1) 5.2's *Why it
   errs* says the errors come from three parser facts, but two of the eight come from others (the overlay starts where
   the last section ends; a section can hold the headers); fix the prose. (2) Table 4's toolkit cells come from the
   older fixed-seed runs (`a1/toolkit-v2`), 5.3's from run 133's seed per file; for the full-training-set unconstrained
   detector the paper says 27/49 (Table 4, 55%) and 25/49 (5.3); one protocol at the scale-up, nothing in the paper.
   (3) New cells, computed as Table 4's (ROC interpolation on `ts_predictions.parquet`): AUC / TPR at 1% / at 0.1% FPR:
   PV-best 0.844 / 26.3% / 10.3%; ERDALT-best 0.883 / 62.7% / 42.2%; adversarial training (seed per file) 0.998 / 95.6%
   / 87.3%; the hand detector (full set, `seed-0-a-mfull-mono-qf`) 0.993 / 87.4% / 71.2%, its derived counterpart
   (`seed-0-a-mfull-pre-qf-v2`) 0.993 / 88.7% / 73.6%. (4) Per operation left out (`a_price_list`), features dropped /
   constrained: full 1,464 / 1,988; no-imp 1,460 / 706; no-ren 1,163 / 2,289; no-app 1,462 / 1,990; others within a
   few of the full set; leaving out add a section, the first-section gap or slack changes no direction (not retrained).
   *From the holistic review (session 42):* for (a), no table shows 5.3's result (published defenses that withstand
   their own attacks fall), while the two tables a skimmer sees are our own hand table's errors and the cost; consider
   it in the remake (user: "needs more thought"). For (c), **a known weakness, not fixable now** (user: "keep it in mind
   for the rest of the project"): §2 says §5 "uses them to attack malware detectors and to build robust ones", and
   §2's problem-space-attack line (one extraction per candidate, nothing about the candidates never tried) gets no
   finding in §5, where the attack is an instrument (no timing claims, decision 6). The mock's contribution 4 is also
   stale ("four to six points", "learned constraints").
3. ~~**The ERDALT check.**~~ Done in session 41 (2026-11-12), no run. (a) The "score floor" is not a weak margin: 99%
   of test goodware sit at the network's lowest score (every hidden unit saturated), so the 1% FPR threshold sits at
   the floor's edge; the 29 detected pilot malware start at logits 0 to ~1,000 (median ~60) and GAMMA imports drives
   24 of them (28 counting 4 over budget) to the floor. (b) Detection is weaker than their paper's (AUC 0.88 against
   their 93.0% on another dataset; TPR 62.7% at 1% FPR); the stopping criterion (< 5 violations) is met at one epoch
   of 310 (297). Left to the scale-up's stopping-criterion item. (c) User (decided, strongly held): ERDALT is
   implemented from the paper's description; their code is not followed where it breaks the guarantee (the
   unconstrained output layer). The paper fixes only the linear layer without bias, L(delta) >= 0 on the observed
   vectors through l2, monotone upper layers, l1 and l3; everything else is from their code and does not conflict.
   Our port is the one implementation considered; no "their code exactly" variant.
4. **The 4 MB-truncation brainstorm** (decision 8 (iv)): a cleaner way to handle the files our dataset truncates at
   4 MB, most of the files outside the plain-layout population. Options raised so far: measure on whole binaries if
   they exist; state each edit's effect correctly on non-plain files (start with which condition the 94 non-plain
   untruncated files fail).
5. **Decide with the user whether the paper is ready for the next full simulated review** (before the introduction).
   Right before running it, update `docs/reviews/review-prompt.md`: it still targets the 2026-11-02 body draft and
   points to the archived formalization. The review should re-check the open and partly addressed risks of the
   2026-11-02 register (R4, R5, R6, R9, R11, R15, R16), the attack-strength concern of the 2026-11-04 strategy review,
   and what no review has seen: the new §3 (its novelty above all), the §2/§5 alignment, and the corpus-checked
   signatures. No narrow §2-3 review beforehand (user). Include decision 6's revisit (is the problem-space defense
   expected?) with its short literature pass, and the user's judgement of whether §4's template layout works on the
   page.
6. **Research-track items**, each agreed before code:
   - The scale-up (seeds 0-2, full splits, more malware; user, 2026-11-11: the first thing to do once the write-up is
     finished): the adaptive budget at 2,000 files (~3,000 CPU-h at 5,000 candidates; options: the 1,000-candidate
     checkpoint, a fixed subset, a cap on the monotone rows), one training set and one attack protocol for every
     detector of §5 (Tables 4 and 5 now show two different unconstrained detectors), and ERDALT's stopping criterion (one epoch of 310 met it in
     run 133; validation AUC still rising at the end; consider more epochs).
   - The sums row's adaptive cell stays 0% with its footnote (settled in session 36; the beam search cannot score
     the sums detector yet).
7. **Other domains (later):** ideas in `docs/domain-selection-brainstorming.md`. Not before EMBER is complete; no
   literature or selection work until the user opens it.
8. **The introduction, discussion, and abstract** last, once the body is settled.

