# PLAN.md: next steps 1-2c, done (moved verbatim on 2026-11-17)

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

# PLAN.md's "Where the paper stands" as of session 62 (replaced 2026-11-17)

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

