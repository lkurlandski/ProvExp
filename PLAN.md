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

## Where the paper stands (updated 2026-11-14, session 62)

- **R7 and the rebuttal have closed the pre-scale-up work (sessions 48-62).** The simulated review's top risk R7 is
  resolved at pilot scale (no router, full widening, LIEF's overlay rule, run 143); R1, R6, R17, R2's code fix and
  R19's check are done; the extractor question is decided (stay on pefile, one audit pass to come). What remains before
  the scale-up: one last revisit of the review and rebuttal (anything else outside R18 and the scale-up?), the R18
  decisions on their own track, and then the scale-up itself. The rebuttal's text fixes wait for the scale-up's numbers.
  The bullets below are the session-45 assessment that set this course, kept for its reasoning.

- **§2-3 (the framework):** rewritten in the week of 2026-11-02; the user is reasonably satisfied. Pending: the user's
  holistic read of Sound Directions.
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

## Next steps, in order

Agreed with the user in session 45 (2026-11-12) after the holistic assessment (above). The previous list, with the
records of the §5 reviews, the table remake and the ERDALT check, is in
`docs/archive/PLAN-next-steps-2026-11-12-s44.md`.

1. **Done in session 46: files below 4 MB in every split.** The 4 MB-truncation brainstorm ended in a decision
   (decision 8 (iv), with the evidence), written into §4.4, §5.1's Setup, 5.4 and Appendix D before the review, as
   the user asked in session 45. Its one blue value (the attacked malware in the population) joins the scale-up.
2. **Done (run; discussed sessions 48-61): the full simulated review**, and its register triaged. The whole register
   R1-R21 has a verdict (`docs/reviews/2026-11-12-body/rebuttal/triage.md`); R7 (decision 11), R1 (decision 12), R6,
   R17, R2's code fix and R19's check are applied; the text fixes (R2's trust paragraph, R3, R4, R5, R8, R12, R13, R15,
   R21) are deferred to after the scale-up's numbers. **One last revisit of the review and rebuttal** (this hand-off,
   `docs/resume-prompt.md`): anything else worth doing outside R18 and the scale-up before planning it? The original
   framing of this step follows.
   *A full simulated review* of the manuscript as it then stood (body only; the last full review, 2026-11-02,
   predates the new §3 and §5). *Designed in session 47* as a reusable procedure (`docs/reviews/review-prompt.md`,
   `docs/reviews/process/`): four independent reviewers who see only the PDF, then a meta-reviewer with full access
   that answers the checklist below; run by the user after session 47, discussed from session 48 (R7 first, decision
   11; R1, decision 12; R6, session 50; R17, session 53b: the ratio's zero case and totally ordered monoids, locality not a gap; the rest of the register goes through the meta-rebuttal, `docs/reviews/rebuttal-prompt.md`). It should re-check the open risks of the 2026-11-02 register (R4, R5, R6, R9, R11, R15,
   R16) and the 2026-11-04 attack-strength concern, and judge what no review has seen: the new §3 (novelty above all),
   the §2/§5 alignment, Proposition 1's role (no finding of its own), the corpus-checked signatures, §4's template on
   the page, the new population (the prompt's bullet on the 4 MB scope was added in session 46), decision 6's revisit
   (is a problem-space defense expected? short literature pass), and MAB-Malware's absence. Its output decides what the
   scale-up includes. No narrow §2-3 review beforehand (user).
2b. **Done (sessions 53-62): R7's widening complete at pilot scale** (decision 11's final form). All of (i)-(v) below
   are finished; session 62 added the escape audit against the widened population (no new in-population escape) and the
   pefile-cap verification (`docs/evidence/r7-overlay-rule.md` §9-10). The scale-up's R7 items are in step 3.
   (i) the closure and exactness check on the widened population. **Done in session 55** (run 141; record
   `docs/evidence/r7-overlay-rule.md`): it failed through pefile's overlay rule (data-directory extents, the debug
   entry's among them, decide where the overlay starts, so `ent` moves it). **Decided (user): LIEF's overlay rule** (the
   overlay starts after the last section's raw data) installed in the extractor at import, a quick patch to keep moving;
   scratch check on 50 files closed, sound and exact; masks unchanged, the `-loose` models stand. Run 142 (full pilot, read in session 56): closed (0 of 13,326 edits on passing files leave), sound (0
   violations), exact after one fix (3,583 exact, 3,217 declined, 0 wrong): 16 declared edits on one file's `far`/`near`
   copies raised an error (its certificate table, inside `.rsrc` and stretched past the end, crosses the overlay's start
   where `sec`/`imp` insert); the engine now declines an insertion that splits an item's members (e0fa5b8; re-checked
   on that file). (ii) **`ent` in the attacks: done (session 56).** `a1_adaptive.py`'s menu now has `ent` (zero both
   entries, point each past the end, and signature cloning: a signed goodware donor's certificate appended and the
   security entry pointed at it; 23/50 pilot donors are signed), byte edits via `catalogue_checks`'s `_entry_write`/
   `_past_end`; `ent` in `OVERWRITE`/M_full; the inplace growth accounting fixed so the clone's append counts against
   the budget (868b8b6). Smoke: the loose monotone detector holds under the full menu, the unconstrained one is evaded.
   (iii) **Run 143 scripted for the user (session 56):** `run/143_escape_pilot_loose.sh` (~5-6 h, NUM_WORKERS default
   16). Run 138's three escapes (cert_entry, image_size, debug_entry) against `unconstrained` and the two `-loose`
   monotone detectors, M_full now including `ent`, evasion counted **from the unescaped originals** (0949a9c; the row
   gains `p_orig`, `in_population`, `evaded_by_escape`). Hypothesis: no detected original evaded by either monotone
   detector. Smoke (debug_entry, M_full): mfull-sums 0/5 (+0.0000), where run 138 saw the debug write evade 4/41.
   **Verified in session 57** (session 56 had been flagged by a safety classifier): all four commits hold; two fixes
   (77587f5): the clone's byte bound covers its padding, and the report's `start_in_population` (the image_size escape
   takes every file out of the loose population, so the guarantee covers only the cert/debug escapes' searches).
   Cleared for the user. **Read in session 61:** the hypothesis held. Neither `-loose` monotone detector is evaded by
   any escape (0/39 and 0/40 per escape; min_delta_logit 0; every search ran its 2,000 candidates); guaranteed for the
   28 and 30 population originals under the cert/debug escapes, observed for the rest (the SizeOfImage escape takes
   every file out); one SizeOfImage search lost to a stalled worker. The unconstrained detector is evaded on 47/47,
   always through signature cloning (one clone alone: 21-26/47). Record: `docs/evidence/r7-population-escape.md` §7.
   (iv) The paper, in small blocks: §4's overwrites (the entry write) and population (the entries' data past the end);
   §5.4's price (robustness to signature cloning); Table 5's monotone rows from the `-loose` models, denominators
   unrouted; no routing in §4.4, §5.1, Appendix D; Appendix D's overlay rule and one sentence on the deviation. All of
   it can start before run 143 is read, except §5.4's *Where the guarantee holds*, which carries its result.
   **Done in session 61** with the user, in three blocks (commits after fc942cb): §4.3 the entry write (13
   operations; "overwrite the debug or certificate entry" in Table 1; the extractor does not verify signatures, a
   `% VERIFY` for a signature-cloning citation), §4.4 the widened population and "the monotone detector scores every
   file"; §5.4 *The price* (run 140's numbers, signature cloning as the reason, framed as a finding: user), *Where the
   guarantee holds* (24 of 28 detected malware of at most 4 MB in the population; the three escapes, none evades),
   *Where the cost lies* (one sentence on the entry write's 3.9 points; the per-operation numbers marked PROTOCOL);
   Table 5 and Appendix D's per-attack table from the `-loose` models; LIEF's overlay rule in §4.2 and Appendix D.
   (v) **Decided (user, session 61): blue values.** The monotone cells of the toolkit attacks and MAB-Malware on the
   `-loose` detectors are `\synthetic{0}` until the scale-up (Table 5's evaded cells, Appendix D's per-attack table,
   MAB-Malware's ~2,400 edits in *The price*).
2c. **The extractor question: decided (user, session 62) — stay on pefile.** The LIEF spike
   (`docs/evidence/r7-overlay-rule.md` §8) parsed the 100 pilot files with both parsers: structures agree on 99/100
   (the one difference is pefile's 8,192-import cap), and parsing is only ~12-25% of our per-file time, so a switch
   buys little against the cost of rebuilding the locating record (pefile's Python gave it to us) and losing the
   bit-exact match with EMBER's released vectors. **Still to do before the scale-up's featurization:** one deliberate
   audit pass against the three principles of `docs/evidence/r7-overlay-rule.md` §6, with a deviations table in Appendix D. Known entries: the overlay
   rule (LIEF's), the warnings dropped, thrember's quirks patched, the 4 MB cut, and the newly verified items —
   pefile's parser caps (§10: an exactness gap for `imp`/`sec` near a cap, not a soundness hole) and the
   always-constant features (`docs/upstream-issues.md` 2-3). The escape audit against the widened population (§9)
   found no new in-population escape.
   **The audit pass: done in session 65; decided (user, session 66)** (`docs/evidence/extractor-audit.md` §2). Five
   candidates, each counted on the 2,000 test files: (2.1) thrember's directory loop drops the last directory read,
   not the reserved one (13 files, 11 in the population): **fixed** (skip the entry named `RESERVED`; a pure
   addition); (2.2) the entry section on files whose sections are not aligned (3): **kept**, listed as a parser rule
   left as it is; (2.3) alignment bits decoded as flags (59): **kept** (v3's definition, a function of one field);
   (2.4) pefile's early stops in imports and exports (~12): **kept**, listed with the parser caps; (2.5) the
   string-pattern typos: **fixed, all three** (`registry_key` as `HKEY_|HKLM|HKCU`, `.click(` literal, `email_addr` a
   bounded standard e-mail pattern; v3's feature names kept, `onlick` included, so the column order stays). The user:
   we already fix several v3 bugs, so fix the obvious ones too. The authenticode definitions (§2.6) stay v3's.
   **Done in session 66:** both fixes in `features.py` (`DataDirectoriesReserved`, `StringExtractorFixed`, installed
   with the merged imports by `fix_quirks`; 47201e2), the reference fixtures regenerated, the identity check's
   differences exactly the fixed features; Appendix D's *Changes to EMBER* with Table 8 (635eb6b; counts blue until
   `1-audit/deviations` runs at scale). The audit steps at scale all have a `run.sh` (`pipeline/1-audit/`), waiting
   only on the audit's file list (`FILES`): a protocol item, decided with the malware count.
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
   **Next:** the rest of the chain, resubmitted (`SKIP=...` in `docs/status.md`); then read it (step 5).
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

Open items (fix when the affected text is touched): **the sample-read signature's claim (decision 12):** §4.3.2's last sentence and §5.1's *Checking results* say the table from 100 files equals the one from 2,000, so the sample-read part "does not depend on which files were read"; at scale the 20,000 training files add 98 directions the 2,000 evaluation files do not show. Rewrite both to the held-out check (the training table covers the evaluation set; more files only add moves, so a larger sample errs on the conservative side) with the user, after the files behind the new moves are known. **the checks recounted on the files below 4 MB** from stored
outputs, no runs (decision 8 (iv); with the next item): 5.1's edit counts, Table 3's file counts, Appendix D's counts and
Table 9 (outside the population: 42 wrong edits on 6 files instead of 45 on 7; session 46).
5.1's "73,063 edits" is run 107's direction check, the exactness
counts are Appendix D's (62,604 + run 118's 34,965); 5.2's "before the derivation existed" (check the history before
rewording); Table 5's toolkit cells come from the fixed-seed runs (`a1/toolkit-v2`), Table 4's from run 133's seed per
file (one protocol at the scale-up, nothing in the paper).

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
