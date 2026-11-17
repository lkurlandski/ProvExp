# Decisions

The plan's standing decisions, moved verbatim out of `PLAN.md` on 2026-11-17 so that the plan holds
only what comes next. "Decision N" anywhere in the project means item N below. Open this file when a task touches
one of them; do not read it every session.

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
   if B is chosen later. *Revisit* at the next full review (next step 2): the review prompt asks whether a reviewer would
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
   untruncated files 94.4% are plain). A brainstorm on a cleaner resolution is scheduled as next step 1 (session 45).
   *Settled in session 46 (2026-11-12, user):* every split uses only the files our copy holds in full (below
   4,000,000 bytes: 85% of the training files; 94% of the benign and 74% of the malicious test files), stated once in
   §5.1's Setup. Whole binaries cannot be obtained (user). *Why:* Claude counted which clause each of the 326
   non-population files of the 2,000 fails: 231 are incomplete because of our cut, 87 are incomplete in the dataset
   itself (the headers locate content past the file's end; 63 lack more than 4 KB of their sections), and only 8 are
   complete files with an unusual layout. All 12 attacked malware outside the population are incomplete, and so is the
   one file that evaded the monotone detectors (Table 5; 51 KB long, its headers describe 2 MB of sections), which the
   text had called an unusual layout. Keeping truncated files would score the detectors on fragments a deployed
   detector never sees and leave our cut as 70% of the exclusions; extending the signatures to incomplete files gives
   the strict table (2,559 of 2,568 features lowerable), which leaves a monotone detector nothing to constrain. The
   user: one concession about the dataset upfront rather than residual side effects in every result; on the files we
   use, the stock extractor reproduces the released vectors (a note in the open-science stub). Written in: §4.4 (the
   population is the complete files with a plain layout; 94% of the test files we use, 5% incomplete, 0.4% unusual
   layouts; closure 0 of 56,902), §5.1's Setup, 5.4's *Where the guarantee holds* (89% of the attacked malware, blue),
   Appendix D's three truncation sentences. Every other number stays a pilot value, marked by `% PROTOCOL` comments in
   §5's Setup and Appendix D, until the scale-up (detectors) and the recount (checks).
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

11. **R7: no router; one monotone detector scores every file (user, session 48, 2026-11-12).** The guarantee is proven
    on the population and measured outside it. *Why:* the escape audit (run 137) found that single field writes the
    loader ignores (certificate or debug entry past the end, SizeOfImage raised) take every population file out, so
    the router handed any attacker the unconstrained detector; patching clause by clause would mean PE special cases
    without end, and dropping the router removes a component instead of adding one. *Pending run 138* (the escape
    pilot: escaped malware attacked by a search that extracts every candidate). If the monotone detectors hold, §4.4
    and §5.4 are rewritten (no routing, the escape result, "stand out" removed); if one escape breaks them, widen the
    population for that clause only. Analysis, options, runs: `docs/evidence/r7-population-escape.md`.
    *Run 138 step 1 read (session 52):* one signed file evades both monotone detectors: the certificate escape breaks
    the signature parse, an append restores it, and the signature features rise, which the table excludes (clause:
    the certificate table lies inside the file). *Option 5 accepted for this clause (user, session 52), with
    caution:* the signature features and the certificate size become two-sided under appends and added sections, with
    the detection cost checked; the final form waits for step 2 (SizeOfImage). The user expects more holes may
    surface at the scale-up; each widening is a separate, careful decision (memory `widen-population-cautiously`).
    *Final form (user, session 53):* run 138's step 2 held, but an end-to-end check from the unescaped originals showed
    the escape writes themselves are the hole (loader-ignored writes to the certificate and debug entries, outside the
    threat model; the debug write alone evades 3/40 and 4/41). So the threat model gains `ent` (both entries set to
    any value) and the population lets their data lie past the end (`a_directions.py --loose`). Ten features become
    two-sided (`authenticode:*`, `datadirectories:{security_size, debug_size, debug_virtual_address}`). Cost (run 140,
    one seed): TPR at 1% FPR 89.6 -> 85.7 (sums), 87.2 -> 83.4 (features); at 0.1% 74.8 -> 68.1, 71.0 -> 65.1; almost
    all from the certificate entry (writable entry = signature cloning). The user chose to pay it. *Alternative,
    recorded but not taken:* widen for the debug entry only (0.1-0.6 points at 1%), leave the certificate entry and
    signature cloning outside the threat model as a stated limitation, measured by run 138 (no detected original
    evaded).
    *The overlay rule (user, session 55):* the widened population was not closed under pefile's overlay rule (the
    debug extent decides where the overlay starts, and `ent` writes it). The extractor now uses LIEF's rule (the
    overlay starts after the last section's raw data): pefile is not the gold standard for what an overlay is, and the
    framework should not be tied to one parser's details. It changes no vector in the population and ~4% outside it;
    masks and models unchanged. Record: `docs/evidence/r7-overlay-rule.md`.

12. **R1: attack strength (user, session 49, 2026-11-12).** (i) *MAB-Malware joins the attacks*, run against every
    detector, without code randomization (needs IDA Pro; outside the threat model). The authors' code is vendored
    (`third_party/mab_malware`) and run single-threaded with a direct hand-over to our detectors
    (`scripts/mab_attack.py`; tested to give the same run as upstream's folder hand-over); donors are the same 50
    goodware as the toolkit's. Run 139 (`run/139_mab_malware.sh`, for the user); its values are blue in §5 and Tables
    4, 5, 11 until read. The case for it is strength (the published attack that evades an EMBER-2024 GBDT most often,
    Zainab et al.) and renaming (PV's hole), **not** "an attack we did not write": the toolkit attacks are not ours
    either (user). (ii) *Tables:* the body reports "evaded by any attack" (the union over every attack run on a
    detector); each attack separately in Appendix D's Table 11 (`tab:ember:per-attack`). Replaces the rule of
    2026-11-04 (user). "Stronger" dropped from §5's lead (the adaptive attack is stronger per attack against PV and
    adversarial training, level on the undefended detector, weaker on ERDALT; the review had compared it with a union).
    (iii) *The adaptive attack at the scale-up scores every candidate by extraction* (`--score real`: all twelve
    operations, header-field overwrites included). The hybrid Claude proposed (predict where possible, extract where
    declined) was dropped after a check: prediction costs 0.17 s per candidate against 0.09 s for extraction in our
    implementation (session 49, 6 files, 115 candidates; predictions exact except the parser warnings).
    *Settled (user, session 49; a repeat of an earlier answer, do not raise it again):* `--score real` at the scale-up,
    and §2 stays as it is. The paper need not show every motivating point of §2 in §5, and the prediction is slower
    here only because it is Python while the extractor's work runs in native code; written natively, the partial
    computation would be far faster (memory `no-timing-claims`). (iv) *Run 139* (`run/139_mab_malware.sh`): the user
    runs it with `NUM_WORKERS=4`. Smoke (recorded in its header): 0 of 9 files evaded on the undefended detector
    (the toolkit evades 7 of them), scores moved but far from the threshold; the blue predictions are likely too high.
    *Read (session 51; full reading in run 139's header):* no silent no-ops. Unconstrained full set 0/49 (16 evasive
    outputs over the byte budget), s10-ref 10/47; PV 7/9, every one by a rename alone; adversarial training 4/50;
    ERDALT 6/29; expert set 4/8 by renames; both monotone full-model detectors 0, their score never below the clean
    score in ~2,400 actions each, outside the population too; additions detector 1/42 by a debug-entry removal. The
    gap to Zainab et al.'s 83.4% is mostly their 0.1% FPR operating point and no byte cap. Measured unions: Table 4
    31/49, 7/9, 25/29, 26/50; Table 5 28/47, 1/40, 1/42, expert 0/8 and 4/8, additions 0/43 and 12/43. *Its role in §5, changed with the
    user's approval (session 51, 5dc17b5):* evidence that the monotone detectors' score never falls (5.4's *The
    price* and *Beyond the guarantee*) and the second attack to find PV's rename hole (5.3); no longer an attack
    that breaks the undefended or the adversarially trained detector. Appendix D's MAB-Malware paragraph compares the
    rate with Zainab et al.'s operating point and byte limit.

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
