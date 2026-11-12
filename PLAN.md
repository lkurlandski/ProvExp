# ProvExp Research Plan

Rewritten 2026-11-09 after a holistic review of the project. The session-by-session history of the plan
(2026-10-22 to 2026-11-09) is in `docs/archive/PLAN-log-2026-10-22-to-2026-11-09.md`; read it only to recover why an
old decision was made. Deadlines and conference cycles are not a planning constraint (user).

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

## Where the paper stands (2026-11-11, session 39)

- **§2-3 (the framework):** rewritten during the week of 2026-11-02; the user is reasonably satisfied, open to
  finetuning. Three subsections: sum-then-readout extractors, edits and their side effects (Proposition 1), sound
  directions (signatures as sets of changes, the derived table, Theorem 1, Corollary 1). Pending: the user's holistic
  read of Sound Directions after round 4.
- **§4-5 (the instance and evaluation):** realigned with the new §3 on 2026-11-10 (sessions 28-29). §4 is about
  1,540 words against ~1,000 (shortening deferred). §5 is rewritten as three findings (decision 10), all four blocks
  drafted (5.3 last, session 39); the user's review of 5.3 and 5.4 is pending; plan in `docs/paper-mock.md`, §5.
- **§6 (related work):** drafted. **§1, §7, abstract, ethics, open science:** empty (the introduction comes last).
- **Experiments:** complete at pilot scale for Tables 3-5 (exactness, hand vs derived vs learned directions,
  detectors). Nothing is invalidated by the framework rewrite. Evidence records: `docs/evidence/`.

## Decisions of 2026-11-09 (the holistic review)

1. **§4 becomes "instantiating the framework", with a fixed template every instance follows.** Section 3 stays free
   of EMBER (and of any format). Section 4 opens with a short, format-free description of what instantiating means,
   in §3's terms, and then EMBER fills it in, in the body. The template:
   (a) the items, sums, and readouts, and the check that the readouts reproduce the extractor bit for bit;
   (b) where the extractor falls outside the class (contributions that are not self-contained) and the repairs,
       value-preserving or patched as pure additions;
   (c) the threat model as a catalogue of operations, and how each gets its signature: operations stated in items
       declare their changes; operations stated as writes get theirs from the instance's record of the positions the
       parser reads to find each kind of item, and the instance declines to predict a write that lands on one;
   (d) the population over which the signatures hold, and how a detector checks membership at inference.
   Other domains, if added, follow the same template in an appendix section each and add rows to an "instances at a
   glance" table in §4 and to the evaluation's tables. Adding a domain then changes no section of the body.
   *Why:* it is the bridge §3 needs (Sound Directions defers the signatures of writes to "instrumenting a particular
   extractor"), keeps §3 format-free, and makes a later domain an appendix plus table rows rather than a restructuring.
2. **Theorem 1's hypothesis for operations stated as writes is checked, not proven, and that is acceptable.** Their
   signatures are collected from the item tables of the corpus; the theorem then needs them to cover every file of
   the population. The paper states this in a sentence and reports the existing check (the 100-file and 2,000-file
   tables are identical); a larger corpus strengthens it at no cost in pages. No new machinery, no new section. The
   same holds for closure (0 of 60,934 edits leave the population). The proof carries the weight (user).
3. **§5.2 (side effects) claims what it tests.** Proposition 1 is exact by construction once the delta is right, so Table 3 shows
   that the instrumentation and the operations' changes are correct and that the instance abstains precisely. Adjust
   the claims; weigh, when drafting, what the table is worth to the paper (it answers "does it work on a real
   extractor") and whether the adaptive search's saving (scoring candidates without extraction) belongs there.
4. **§2's promises and §5's results must align.** Open, to settle in the paper-mock rewrite. Working idea: organize §5
   around §3's two results (side effects, then directions and the detectors they give), and either narrow §2's four
   lines of work or show each one in §5. Adding experiments or trimming the motivation are both allowed (user).
6. **§2/§5 alignment: option A of the paper mock** (decided by Claude at the user's request, 2026-11-09). §2 keeps the
   four lines of work as the landscape but promises three evaluated uses (the attack scoring without extraction, the
   constraints, monotone detectors); adversarial training stays the defender's alternative in Table 5. Plus one cheap
   measurement: the cost per candidate of scoring by Proposition 1 against extraction. *Superseded (user,
   2026-11-10):* no timing is measured, reported, or compared; the paper says the computation touches only the items an
   edit meets and so can be (is likely to be) faster than extracting again, never that it is (the Python implementation
   is slower than thrember's vectorized extractor, which says nothing about the method). *Why now:* A is a subset of
   B, so §4 and §5's subsections are written the same either way; only §2's promise and possibly one §5 row change
   if B is chosen later. *Revisit* at the next full review (step 4): the review prompt asks whether a reviewer would
   expect the problem-space defense shown, and a short literature pass checks how much that line matters
   (adversarial training on problem-space examples for malware: Lucas et al., Dyrmishi et al., and their citers).
5. **Directions B and C are parked**, not dropped: `docs/parked/directions-B-C.md`.
7. **Two §3 edits from the code audit, chosen by the user (session 26).** Numbers are the compiled ones.
   (a) *Table 1 (readout rules, `tab:fw:readouts`): option A.* The row "presence | $[s_k > 0]$ | $d_k$" becomes "monotone
   | $g(s_k)$, $g$ nondecreasing, e.g. $[s_k > 0]$ | $d_k$": same table, no new rows or columns, only the first two
   cells of that row change. The list of readout forms in §3.1, the paragraph after the table, and the proof in
   Appendix C get matching wording. *Why:* three EMBER readouts (a max/min pool with a floor of 0, one item's value
   with a default, a presence bit scaled by 128) are nondecreasing functions of one sum, and the code gives them
   $d_k$; the proof already argues presence this way; it also covers capped or log-scaled counts in other domains.
   (b) *Definition 8 (Changes and signatures, `def:fw:signature`), the second paragraph after it:* "such as appending
   any content" becomes "such as overwriting a range of positions with any content", and the sentence gains ", which
   record the items each position belongs to". *Why:* the code collects changes from item tables only for in-place
   writes; append is declared and checked by re-extraction (audit finding 6).

8. **§4's outline, revised with the user (session 27).** (i) The bit-exact check is one or two sentences. (ii) No
   "repairs" part: the section-size ratio and the library set are written as sums and readouts in a brief clause
   (the user may cut it later); the import-overwrite bug is not mentioned in the paper (experiments still run on the
   patched extractor). Part (b) becomes a qualitative discussion of how strictly EMBER fits the sum-then-readout
   definition and what to do with features that do not (drop them, or keep them as able to move both ways; a monotone
   detector must drop them), with the parser warnings as the example: absent from EMBER 2017/2018 (verify in Joyce et
   al.) and dropping them costs nothing (run 126: +0.1 points TPR at 1% FPR). (iii) Part (c), the threat model, is
   written literature first: a modern review of adversarial malware in reputable venues (user: the toolkit list is
   "basically all workshop papers"), the edits each work uses, our catalogue as the
   functionality-preserving, non-code-rewriting edits among them, exclusions named. (iv) The population stays as is
   for now; the user finds the 4 MB truncation ugly (most of the 318 non-plain files of 2,000 are truncated; on
   untruncated files 94.4% are plain). A brainstorm on a cleaner resolution is scheduled around step 4.
   (v) *After block 1 (session 27):* §4 restructured to about 1,000 words: a short lead (no checks), 4.1 EMBER and PE
   files (own subsection), 4.2 EMBER as a sum-then-readout extractor ((a) and (b) merged), 4.3 threat model (the
   weight), 4.4 population, the bookkeeping in a new appendix; no "instances at a glance" table for one instance.
   *Why:* the user found the block-1 bookkeeping good but "boring" and too bulky (about 5% of the paper) for what it
   contributes. Detail: `docs/paper-mock.md`, §4.

9. **Code-level transformations stay out of the threat model for now (user, session 27).** The literature review
   (`docs/evidence/literature-adversarial-malware.md`) found that our catalogue covers every structural edit of the
   reputable-venue PE attacks, but not the code-level ones: MAB-Malware's code randomization, IPR and Disp (Lucas et
   al., AsiaCCS 2021, USENIX Sec. 2023, CCS 2024), MalGuise's call-based redividing (USENIX Sec. 2024). *Why not now
   (user):* these attacks are much harder to execute, above all in a functionality-preserving way, than the
   structural edits, and the paper is stronger with them but does not need them yet. *Consequence:* a stated
   limitation of the threat models and the experiments: §4.3 names code-level transformations among the exclusions
   (with packing), and the discussion (§7) states it as a limitation. *To add later:* the framework needs no new
   machinery (an in-place write inside code sections, same length, off the locating positions; Disp and MalGuise add a
   section too); the cheap first step is the pilot's direction table with that operation, then retraining the
   detectors if the directions change. Do not re-propose it unless the user reopens it or a reviewer raises it.

10. **§5 is restructured as three findings, not by §3's results and not as a defense paper (user, session 30,
    2026-11-10).** The plan, one line per paragraph, and the checks before drafting are in `docs/paper-mock.md`, §5.
    The lead and 5.1 (with a two-sentence correctness check; the side-effect table moves to Appendix D), then 5.2
    *What Hand Analysis Misses* (the hand table, the hand detector attacked, the expert set), 5.3 *What Observed
    Attacks Miss* (the learned region, PV, ERDALT, adversarial training, in a new audit table), 5.4 *What Robustness
    Costs* (the monotone detectors as a measurement: about four points, attributable per operation; the threat
    model's width; beyond the guarantee). Supersedes decision 4's working idea and the mock's "by §3's results".
    *Why (the session's analysis):* (a) organized by results, §5 had become a validation section: §5.2 (640 words and
    the side-effect table) checked our implementation, the coverage paragraph and §5.4's opening did too (together a
    quarter to a third of the section, placed first), two titles claimed correctness, and the strongest security
    findings (published defenses evaded, their holes computed before any attack) sat at the end of §5.4. The user:
    "transactional and somewhat lifeless", and it reads as showing that the implementation is correct and the proven
    ideas hold. (b) A defense-first organization was the intermediate proposal; the user objected that it turns the
    paper into a standard defense paper, judged on clean accuracy and on breadth of baselines and threat model, where
    we are weak: the user does not consider 93.5% to 89.6% at 1% FPR small (they would like about 1% or less), and
    three defense baselines are too few for a state-of-the-art defense claim (they would want at least six). The
    limitations (no code-level transformations, routing outside the population, pilot scale, one extractor) would
    then read as holes in a defense. (c) The attack is not strong enough to be a task of its own: the adaptive
    search evades the undefended detector about as often as the held-out toolkit attacks (51% against 53%), and
    with no timing claim nothing shows Prop. 1 beats the same search with re-extraction; it is strong only when
    aimed at what a defense trusts (PV: 68% against 18%), so it serves as the instrument of 5.2-5.3. (d) The
    findings framing tests §2's own claim (knowledge from trial, hand analysis, or observed attacks falls short) and
    fits the thesis: the computed knowledge is the contribution, the detectors one consequence. *Weaknesses kept in
    view:* one extractor (claims say "on EMBER"; a second instance would strengthen 5.2-5.3 most, later, the user's
    call), 5.2 leans on our own hand table (the expert set and check C3 counter the strawman risk), and 5.4 measures
    one kind of robustness. *Sufficiency:* no new task is needed; three measurements on existing outputs and one
    literature check (the mock's C1-C3) close the gaps a reviewer would hit. Reducing the detectors' cost toward 1%
    is a separate research question about the detector (the per-operation costs point at the import hash buckets and
    the header fields), not part of the rewrite. *Extension (session 31):* the structure is domain-free (findings follow §2's three sources,
    each a measurement per instance); drafting rules that keep later domains to rows and an appendix are in
    `docs/paper-mock.md`, §5, "Extending §5 to other domains". *Leave-one-out (session 31, user):* the defenses learned from
    attacks are evaluated leave-one-out over the eight toolkit attacks, adaptive cells on the all-eight models
    (`docs/paper-mock.md`, §5, "Revisions after the user's review"). *Scripted in session 32* (`run/131_loo_defenses.sh`,
    started by the user 2026-11-10): each fold's held-out attack is run against that fold's model (the toolkit attacks
    query the detector they attack; no stored outputs could be re-scored), and ERDALT's training data is balanced over
    the eight attacks (step 0 attacks run 122's 400 training malware with the four attacks run 122 lacked; user's
    approval). Expectation from the stored perturbation vectors: the eight attacks lower nearly the same features, so
    most PV folds should be 0 and the user's hypothesis (PV well above 0) may fail on the mean; if so, 5.3's toolkit
    column weakens for PV and the adaptive column carries the finding.
    *Session 34 (2026-11-11): §5.3's design reopened* (the three-finding structure stands). Working plan:
    `docs/evidence/section-5.3-design.md`, which supersedes the mock's item 5.3 until §5.3's prose is written. Run 131 read
    (PV folds 0 except gamma_api 5/21; ERDALT high on gamma_api and header_fields; ERDALT-8 adaptive 17/24). Found in
    the code: the attack harness resets the RNG to seed 0 before every run (after Gimenez et al.), so GAMMA's section
    names are the same on every file, and PV and ERDALT learned from the pilot (test) malware. With a seed per file,
    one attack covers every section-name bucket (run 132), which is where PV's hole, and so its 14/22, mostly lies.
    The user: do what is best for the research rather than copy prior protocols, and fix any design gap that would
    undermine the results. Run 133 rebuilds PV, ERDALT and adversarial training from varied runs on training malware
    only; §5.3's claim is settled after it (design doc, §10.2), possibly narrowed (ERDALT, and that observations
    cannot certify their own completeness).
    *Session 34, continued (2026-11-11): run 133 read, §5.3's claim agreed* (design doc §10.4-10.5). The finding
    survives the fair design, sharpened: a defense learned from observed attacks inherits what the attacks did not
    do, and nothing in the observations says what that is. (i) Coverage is invisible to the defender (the same eight
    attacks lower 745 or 928 of the 1,070 lowerable features depending on how they are run; the derivation lists all
    at once). (ii) The operation the attacks lack becomes the hole: PV rebuilt from 3,183 varied outputs is evaded on
    4 of its 9 files, each by one rename. (iii) Unmoved is not unmovable: PV either trusts what it should not (PV-all,
    14/22) or constrains what it need not (PV rebuilt detects 26.2% at 1% FPR against the derived detector's 87.3% on
    the same features; the DLL flag, which no edit moves, is constrained; run 134: not the broken shift outputs, and
    leaving never-moved features free gives 50.9%). (iv) ERDALT constrains the vectors it saw, not the next ones: its
    own training attack with other donors evades it 24/29, the search 22/29. (v) Adversarial training helps against
    the toolkit (12/50 against 25/49), not the search (23/50). Not claimed: that the fixed seed alone made PV
    evadable. Leave-one-out stays (user: "still a very powerful and interesting experiment"), redone the fair way as
    run 135 (folds from run 133's outputs; a sentence in the body, per-fold table in the appendix); run 131's folds
    are retired.
    *Session 36 (2026-11-11): 5.4 drafted* (8fd8c9c, unreviewed). Changes from the mock's plan, agreed with the user:
    the expert-set comparison comes second, right after the price (it is the result a practitioner can act on: the
    published hand-picked robust detector keeps 29.1% where the derived one keeps 92.2% under the same guarantee);
    TPR at 0.1% FPR is reported beside 1% (74.7 vs 84.4%, about ten points; at 0.1% dropping the two-sided features
    alone costs 5.2 points); Table 4 keeps one toolkit column (any of the eight attacks) and the full-training-set
    adaptive cells (never scale a cell down to the pilot protocol; everything scales up later); the derivation-cost
    paragraph is dropped. Practitioners' likely objections, kept in view: the 0.1% cost, the structural-only threat
    model (no packing, no code-level edits), and pilot scale, which matters most for 5.4 because its claim is a number.
    *Session 39 (2026-11-11): 5.3 drafted* (7a2ceff, 9d0369f, 035d977; unreviewed). User decisions: (i) the
    learned-region paragraph (exact tree solver) is cut; (ii) no audit table now: Tables 3 and 4 will be remade anyway
    (user: "incredibly disgusting"), so 5.3 reports its defenses in prose and the tables are redesigned together
    later; (iii) one sentence on rename (adding it would close PV's hole, but the defender learns which operation to
    add only after an attacker used it), no new run; (iv) **no random-seed or protocol-hygiene details in the paper**
    (user: do the obviously correct thing in the experiments and leave it at that), so the seed-reset comparison
    (847 vs 928 lowered features) and PV-all's 14/22 are out. 5.3 has seven run-in paragraphs: opening (protocol),
    what the attacks reveal (928 of 1,070), the operation the attacks lack (PV 4/9 by one rename; hole 38.8%), what
    the attacks did not move (PV 26.2% vs 87.2%; the DLL flag; PV-free 50.9%), what ERDALT learns (24/29 by its own
    attack, 22/29 adaptive, 90% of its layer's weight), adversarial training (12/50, 23/50), holding one attack out
    (run 135; per-fold table in Appendix D). The old PV/ERDALT/adversarial-training material is gone from 5.4.

## Next steps, in order

Done: the paper mock rewritten, the read-only code audit (`docs/evidence/code-audit-sound-directions.md`), decision
7's edits, §4 rewritten and reviewed twice (sessions 38, 40), §5 rewritten in four blocks with run 135's values filled
(session 40). The order agreed with the user on 2026-11-12:

1. **The humanistic review of §5, one subsection per pass** (lead and 5.1, then 5.2, 5.3, 5.4), with the
   `anthropic-skills:humanistic-paper-review` skill, the user approving and the findings applied after each. About
   half a day. The user's own pending comments on 5.1's *Checking results* and 5.2 (9b7d0ba) join their subsection.
   Known vocabulary items: "GAMMA's import injection" and "the header-field attack" (Table 2: GAMMA imports, header
   fields); Table 3 says "signature table" where it means the certificate table.
2. **Then, to be considered with the user:** (a) remake the tables (Tables 3 and 4 above all; the user dislikes
   them), before (b) shortening §4 and §5 together (§4 ~1,500 words against ~1,000; §4.3 first), and (c) §2's closing
   sentence and contribution 4 against §5's three findings.
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
     checkpoint, a fixed subset, a cap on the monotone rows), and ERDALT's stopping criterion (one epoch of 310 met it in
     run 133; validation AUC still rising at the end; consider more epochs).
   - The sums row's adaptive cell stays 0% with its footnote (settled in session 36; the beam search cannot score
     the sums detector yet).
7. **Other domains (later):** ideas in `docs/domain-selection-brainstorming.md`. Not before EMBER is complete; no
   literature or selection work until the user opens it.
8. **The introduction, discussion, and abstract** last, once the body is settled.

## Settled decisions (carried over)

- The domain is adversarial examples in practical security tasks; the framework is as agnostic as Pierazzi et al.'s
  (CLAUDE.md, framework conventions).
- The GBDT is the first classifier; the MLP is set aside temporarily, not dropped.
- No result rests on an implementation quirk of the extractor: quirks are patched by pure additions, every row runs on
  the patched variant, upstream reports in `docs/upstream-issues.md`.
- "Feature provenance" was the project's name; the paper's object is the sum-then-readout extractor.
- No engagement with database-theory provenance (semirings, aggregate provenance) beyond citation.
- Pilot scale for research; the scale-up only when the user decides.
- Dropped, with reasons, in `docs/graveyard.md`: explanation provenance (2026-10-22) and A' (2026-11-02). Coupling
  (old claim C2) and reachable regions (C3) were left out of the paper on 2026-11-02 (the paper mock); the region's
  soundness survives inside A (run 111).
