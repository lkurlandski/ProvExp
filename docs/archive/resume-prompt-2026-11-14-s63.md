# Resume: one last review/rebuttal revisit, then plan the scale-up

Written at the end of session 62 (2026-11-14). Self-contained: everything needed is below or in the files it names.
R18 (the trial competitor) runs on its own track (`docs/resume-prompt-R18.md`); commit only the files you changed
(`git add <paths>`), and leave the R18 session's files alone (notably `run/145_import_address_monotone.sh`,
`scripts/trial_audit.py`, and its `docs/evidence/r18-trial-competitor.md`).

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on the EMBER2024 corpus, with an extractor derived from EMBER-v3, is
the instance. §5 of the paper is three findings: what hand analysis misses (5.2), what defenses learned from observed
attacks miss (5.3), what robustness costs (5.4). Check `manuscript/main.aux` before naming a section, table or theorem
number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (the "Where the paper stands" note and next steps 2-3).

## Where things stand (end of session 62)

The pre-scale-up work has essentially closed:

- **R7 is done at pilot scale** (sessions 48-62): no router (one monotone detector scores every file), the full
  widening (`ent`, LIEF's overlay rule), run 143 read (the two `-loose` monotone detectors 0 evaded under every
  escape; unconstrained 47/47 by signature cloning). The paper's R7 text is written; the monotone toolkit/MAB cells
  are blue until the scale-up. Session 62 added the escape audit against the widened population (no new in-population
  escape) and verified pefile's parser caps are an exactness gap, not a soundness hole
  (`docs/evidence/r7-overlay-rule.md` §9-10).
- **The extractor question is decided: stay on pefile** (session 62; LIEF spike in `r7-overlay-rule.md` §8). One
  deliberate audit pass with a deviations table in Appendix D remains, to do with the scale-up's featurization.
- **The simulated review (2026-11-12) is triaged** (`docs/reviews/2026-11-12-body/rebuttal/triage.md`): every register
  item R1-R21 has a verdict. Applied: R7 (decision 11), R1 (decision 12), R6, R17, R2's 4-byte Rich fix, R19's check,
  and session 62's three small manuscript fixes (Appendix D's pools, self-maintainability in §3.2, the code-level
  exclusion in §4.3) plus the Kim et al. signature-cloning citation. Deferred to after the scale-up's numbers (triage
  decision): the rebuttal text fixes R2 (trust paragraph), R3, R4, R5, R8, R12, R13, R15, R21.
- **R18 (trial competitor)** runs on its own track: run 144 and three decisions wait on the user
  (`docs/resume-prompt-R18.md`, `docs/evidence/r18-trial-competitor.md`).

## The task

1. **One last revisit of the review and rebuttal.** Read the meta-review (`docs/reviews/2026-11-12-body/meta-review.md`,
   §5-8 especially) and the triage table, and judge: is there anything else worth doing *before* the scale-up, outside
   R18 and the scale-up itself? Weigh each candidate on merit (memory `distrust-simulated-reviews`: the reviewers lean
   toward accepting criticism; quote our claim and the strongest rebuttal before calling anything a gap). Likely
   candidates to weigh, not a to-do list:
   - the deferred text fixes (R2-R21): confirm they are genuinely best done with the scale-up's numbers, or pull
     forward any that do not depend on numbers and are cheap now;
   - anything in the meta-review's §5 ("what the reviewers missed") or §7 ("what the full-scale run must include") not
     yet folded into PLAN.md step 3;
   - whether the extractor audit pass (the deviations table) is best done now or with featurization.
   Present a short recommendation per candidate; the user decides. **If nothing is worth the time, say so and move to 2.**
2. **Start planning the scale-up** (PLAN.md step 3), only once the user agrees there is nothing else. Each item agreed
   with the user before any code; long runs go to the user as `run/` scripts. The open questions gathered so far:
   - **the adaptive attack's single protocol:** §5.1 states Prop. 1 scoring at 5,000 candidates; run 143 extracted
     every candidate at 2,000. The scale-up scores by extraction (`--score real`, decision 12 (iii)); the budget at
     scale is open (session 62 noted evasions of the learned defenses still climb from 1,000 to 5,000 candidates, so
     2,000 undercounts; one option is to run the monotone detectors' searches at seed 0 only, since their 0 is proven).
   - **the malware count:** session 62 suggested ~200 attacked malware per seed so PV and the expert set clear ~100
     detected files pooled over seeds 0-2.
   - **the R7 blue values and PROTOCOL recounts** (PLAN.md step 3): the toolkit attacks and MAB-Malware on the
     `-loose` monotone detectors; the price list (run 126) on the widened table; closure and population shares on the
     widened population; the adaptive attack under one protocol.
   - **the rebuttal's before-scale-up items:** MAB-Malware also at Zainab et al.'s setting (0.1% FPR, no byte cap)
     against the unconstrained detector (R1); ERDALT's donor-overlap control (R19); thresholds from EMBER2024's
     validation split (R20); the extractor audit pass with its deviations table.
   - **seeds 0-2, full splits, one training set and one attack protocol for every detector**; whatever R18 adds (the
     trial row, iterated adversarial training).

## Constraints

- Explain plainly; one recommendation, not a menu. State a hypothesis before any run; report a failed check as such.
- Never propose sandbox execution or obtaining files over 4 MB.
- Jobs over ~10 minutes go to the user as `run/` scripts. Before committing: ruff and mypy; after manuscript edits,
  `make` and `make check`. Commit to `main` in logical pieces; do not push.
- At the end of the session: update `docs/status.md`, PLAN.md; write the next resume prompt (archive this one).
