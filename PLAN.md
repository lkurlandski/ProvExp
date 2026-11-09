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

## Where the paper stands (2026-11-09)

- **§2-3 (the framework):** rewritten during the week of 2026-11-02; the user is reasonably satisfied, open to
  finetuning. Three subsections: sum-then-readout extractors, edits and their side effects (Proposition 1), sound
  directions (signatures as sets of changes, the derived table, Theorem 1, Corollary 1). Pending: the user's holistic
  read of Sound Directions after round 4.
- **§4-5 (the instance and evaluation):** drafted on 2026-11-02 against the *old* §3 and not yet realigned. They
  still use the old vocabulary (requirements R1-R5, locating positions, margins, scanned kinds, "stated in elements").
- **§6 (related work):** drafted. **§1, §7, abstract, ethics, open science:** empty (the introduction comes last).
- **Experiments:** complete at pilot scale for Tables 5-7 (exactness, hand vs derived vs learned directions,
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
3. **§5.1 claims what it tests.** Proposition 1 is exact by construction once the delta is right, so Table 5 shows
   that the instrumentation and the operations' changes are correct and that the instance abstains precisely. Adjust
   the claims; weigh, when drafting, what the table is worth to the paper (it answers "does it work on a real
   extractor") and whether the adaptive search's saving (scoring candidates without extraction) belongs there.
4. **§2's promises and §5's results must align.** Open, to settle in the paper-mock rewrite. Working idea: organize §5
   around §3's two results (side effects, then directions and the detectors they give), and either narrow §2's four
   lines of work or show each one in §5. Adding experiments or trimming the motivation are both allowed (user).
6. **§2/§5 alignment: option A of the paper mock** (decided by Claude at the user's request, 2026-11-09). §2 keeps the
   four lines of work as the landscape but promises three evaluated uses (the attack scoring without extraction, the
   constraints, monotone detectors); adversarial training stays the defender's alternative in Table 7. Plus one cheap
   measurement: the cost per candidate of scoring by Proposition 1 against extraction. *Why now:* A is a subset of
   B, so §4 and §5's subsections are written the same either way; only §2's promise and possibly one §5 row change
   if B is chosen later. *Revisit* at the next full review (step 4): the review prompt asks whether a reviewer would
   expect the problem-space defense shown, and a short literature pass checks how much that line matters
   (adversarial training on problem-space examples for malware: Lucas et al., Dyrmishi et al., and their citers).
5. **Directions B and C are parked**, not dropped: `docs/parked/directions-B-C.md`.

## Next steps, in order

1. **Rewrite `docs/paper-mock.md`** against the new §3 and the decisions above: contributions (no requirements, no
   Theorems 2-3), §4 as the template plus EMBER, §5 organized by §3's results, the §2/§5 alignment (decision 4). The
   user approves it before any section is rewritten.
2. **Code audit, read-only:** does the code compute the derived table as Definitions 9-10 now define it (one
   direction rule for every monoid, replacements as changes, the readout rules of Table 2)? The code predates round 4.
   Report mismatches; fix only with the user.
3. **§4, then §5, rewritten in blocks** with the user's review after each (the way Sound Directions round 4 worked;
   use the `paper-prose` skill). The mechanical vocabulary fixes go with them (R3/R4, "rate", "stated in elements",
   §6's "margins").
4. **The next full simulated review, once §4 and §5 are realigned and before the introduction** (decided 2026-11-09).
   Right before running it, update `docs/reviews/review-prompt.md`: it still targets the 2026-11-02 body draft and
   points to the archived formalization. The review should re-check the open and partly addressed risks of the
   2026-11-02 register (R4, R5, R6, R9, R11, R15, R16), the attack-strength concern of the 2026-11-04 strategy review,
   and what no review has seen: the new §3 (its novelty above all), the §2/§5 alignment, and the corpus-checked
   signatures. No narrow §2-3 review beforehand (user). Include decision 6's revisit (is the problem-space
   defense expected?) with its short literature pass, and the user's judgement of whether §4's template layout works
   on the page.
5. **Research-track items**, each agreed before code:
   - The sums row's adaptive cell: the beam search cannot score the sums detector yet (routing). Expected 0% by
     construction; weigh consistency against cost.
   - The scale-up (seeds 0-2, full splits, more malware; the user decides when): the adaptive budget at 2,000 files
     (~3,000 CPU-h at 5,000 candidates; options: the 1,000-candidate checkpoint, a fixed subset, a cap on the monotone
     rows), and ERDALT's stopping criterion (met only at the last epoch at seed 0).
   - Possibly: MAB-Malware as an independent source of held-out attacks; leave-one-out PV.
6. **Other domains (later):** ideas in `docs/domain-selection-brainstorming.md`. Not before EMBER is complete; no
   literature or selection work until the user opens it.
7. **The introduction, discussion, and abstract** last, once the body is settled.

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
