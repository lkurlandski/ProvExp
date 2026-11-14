# Resume: the decisions before the scale-up (R7 is done at pilot scale)

Written at the end of session 61 (2026-11-14), for the next R7/scale-up session. Self-contained: everything needed to
start is below or in the files it names. The rebuttal of the 2026-11-12 simulated review runs separately, from
`docs/resume-prompt-rebuttal.md`, and R18 (the trial competitor) from `docs/resume-prompt-R18.md`. Sessions on the
tracks run in parallel: commit only the files you changed (`git add <paths>`), and leave the others' files alone.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on the EMBER2024 corpus, with an extractor derived from EMBER-v3, is
the instance. §5 of the paper is three findings: what hand analysis misses (5.2), what defenses learned from observed
attacks miss (5.3), what robustness costs (5.4). Check `manuscript/main.aux` before naming a section, table or theorem
number, and give its title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (steps 2b, 2c, 3).

## Where R7 stands (done at pilot scale)

- Decided: no router (one monotone detector scores every file; the guarantee is proven on the population and measured
  outside it); the full widening (`ent`: the certificate and debug entries set to any value; their data may lie past
  the end); LIEF's overlay rule installed in pefile. Cost (run 140): TPR at 1% FPR 89.6 -> 85.7 (sums), almost all
  from signature cloning.
- Run 143 (read in session 61): neither `-loose` monotone detector evaded under any of three escapes (0/39, 0/40;
  min_delta_logit 0; full budgets); the unconstrained detector evaded on 47/47, always by signature cloning (one clone
  alone: 21-26/47). Record: `docs/evidence/r7-population-escape.md` §7.
- The paper's R7 text is written (session 61, with the user): §4.3 (the entry write, 13 operations), §4.4 (widened
  population, no routing), §4.2 and Appendix D (LIEF's overlay rule), §5.4 (*The price* with signature cloning as a
  finding, *Where the guarantee holds* with the escapes, *Where the cost lies*), Table 5 and Appendix D's per-attack
  table. The monotone toolkit and MAB-Malware cells are blue (`\synthetic`) until the scale-up (user's decision).
  What the scale-up must redo for R7 is listed in PLAN.md step 3.

## The task: the user's decisions before the scale-up

0. ~~**Rebuttal analysis**~~ Done (session 62): the triage and meta-review register are addressed except the text
   fixes deferred to after the scale-up's numbers (R2's trust paragraph, R3, R4, R5, R8, R12, R13, R15, R21).
1. ~~**The extractor question (PLAN.md step 2c).**~~ Decided (user, session 62): **stay on pefile.** The LIEF spike
   (`docs/evidence/r7-overlay-rule.md` §8) found structures agree on 99/100 pilot files and parsing is only ~12-25% of
   our per-file time, so a switch buys little for the cost of rebuilding the locating record. Still **to do before the
   scale-up's featurization:** one deliberate audit pass with a deviations table in Appendix D (principles in §6; the
   caps of §10 and the always-constant features of `upstream-issues.md` 2-3 are the known entries).
2. **The scale-up's protocol (PLAN.md step 3).** Each item agreed with the user before code; long runs as `run/`
   scripts. Open questions include the adaptive attack's single protocol (§5.1 states Prop. 1 scoring at 5,000
   candidates; run 143 extracted at 2,000) and its budget at scale; the malware count (session 62 suggested ~200 per
   seed so PV and the expert set clear ~100 detected files); the scale-up's R7 items (PLAN.md step 3) and the
   rebuttal's before-scale-up items (R1 at Zainab's setting, R19's donor control, R20's validation-split thresholds).
3. ~~Small open items~~ Done (session 62): Kim et al. (CCS 2017) cited for signature cloning in §4.3 (the `% VERIFY`
   resolved); the overfull vbox is gone; `make check` clean.

## Constraints

- Explain plainly; one recommendation. State a hypothesis before any run; report a failed check as such.
- Never propose sandbox execution or obtaining files over 4 MB.
- Jobs over ~10 minutes go to the user as `run/` scripts. Before committing: ruff and mypy; after manuscript edits,
  `make` and `make check`. Commit to `main` in logical pieces; do not push.
- At the end of the session: update `docs/status.md`, PLAN.md; write the next resume prompt (archive this one).
