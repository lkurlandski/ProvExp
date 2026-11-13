# Dossier: R19

Cut from `/home/lk3591/Documents/code/ProvExp/docs/reviews/2026-11-12-body/` by `docs/reviews/process/dossier.py`. Facts tagged [verified] in the meta-review are taken as established.

## R19

### Register row (meta-review §6)

| R# | Risk | Raised by | L | Severity | Mitigation | Type | Effort |
|---|---|---|---|---|---|---|---|
| R19 | **The ERDALT port may be judged weak.** AUC .883 against their 93.0%; one epoch; a soft constraint. | B-W8, C-W5, A-W6, D-W6; C-Q4 | M | major for §5.3's ERDALT paragraph | Train to a proper stopping point. Report the share of training and of test perturbation vectors with L(δ) < 0: if training vectors satisfy it and GAMMA-imports test vectors do not, the failure is the unseen-vector one the paper describes. Add a donor-overlap control (GAMMA imports with training donors). State their setup and ours in App. D. | analysis, small experiment | days |

### Meta-review verdicts (§3)

| ID | Verdict | Evidence |
|---|---|---|
| A-W6 | partly correct | The counts are small (correct); scale comes with the full run (settled, seeds 0-2). The hand table is the authors' own (correct; R3). Running ERDALT's released code unchanged is settled: in session 41 the user decided to implement from the paper wherever the code breaks the guarantee. |
| B-W8 | partly correct | (1) Gimenez et al.'s paper reports a 60-second timeout per attack (p. 10) [verified]. The 100 queries (population 10, 10 iterations) come from their released code (`scripts/a_pv_attacks.py:52-59`), so the text must say "their released code". (2) The ERDALT port is settled (A-W6); its detection gap is real (R19). (3) The text never says how a stub rewrite lowers their indicator: the edit restores the default stub (`docs/evidence/direction-A-expert-set.md:124-127`), and both evasions use rename. (4) `cortellazzi2025intriguing` is in `main.bib` but uncited [verified]. Pierazzi et al. do estimate gadget side effects in advance by injecting each gadget into a minimal app (p. 1340, App. F) [verified]; R5. |
| C-W5 | partly correct | The positivity constraint is a soft l2 loss (Gimenez et al., Fig. 2 and the text below it), and their Proposition 3 assumes a finite set of perturbation vectors known at training [verified]. Their setup differs (1,033 adversarial examples, the dataset of their ref. [5], p. 10) [verified]. The paper measures how far the layer sits from the derived directions (90% of its weight), which is more than a restatement. Running the unmodified code is settled. |
| C-Q4 | partly settled | The fraction of vectors with L(δ) < 0 is cheap and should be reported (R19). Unmodified code is settled. |
| D-W6 | partly correct | Gimenez et al. used 1,033 adversarial examples against 12,000 training malware (p. 10) [verified]. Ours: 3,183 outputs from 400 training malware, but the defenses sit on different training sets (R11). The donor-overlap control is a good, cheap check (R19). |

### Reviewer passages cited

### A-W6. Statistical design of the comparisons; the authors' own hand table as a baseline.
*Location:* Section 5.1, Tables 3–5, Table 10.

*Problem.*
- Single seed, 10% subsamples, and attacks on 50 malware. Several counts are on 8–9 detected files: PV 4/9, expert set 2/8, Table 10.
- At 0.1% FPR the threshold rests on a handful of benign files; the paper concedes "a few points" of retraining noise (p. 10).
- The headline cost (3.9 points at 1% FPR) is of the same order as that noise.
- The "hand table" in Section 5.2 was written by the authors. This is better than nothing, but it is not an independent analyst.

The large effects survive plausible shifts: PV at 26% vs. 87%, the expert set at 29% vs. 92%, and the qualitative failures of PV and ERDALT. The cost figure and the per-operation attribution may not.

*Fix.*
- Use full scale with ≥5 seeds and report confidence intervals for TPR at both FPRs.
- Report the operation ablation with intervals.
- If possible, have one or more independent analysts write hand tables blind.
- For ERDALT, run the authors' released artifact as well as the reimplementation (one change from the released code is stated in Appendix D). This rules out reimplementation effects in the 24/29 result.

*Status:* verified (protocol as stated); the robustness judgement is mine.

**B-W8. Several comparisons with prior work are stated without caveats.**
*Location:* §5.1 (p. 7), §5.2 (p. 8), §5.3 (p. 9), App. D "ERDALT" (p. 16).
*Problem:*
- "100 queries per file, as in Gimenez et al." does not match their paper, which reports a 60-second timeout per attack (Gimenez et al., §5.1). *Verified* against `papers/gimenez2025certifiably.pdf`.
- The ERDALT reimplementation changes the design: the output layer is kept nonnegative. The model reaches AUC .883 vs 93.0% in the original, on different data. That deviation needs justification, plus a run of the unmodified released code, because the ERDALT failure (24/29) is a headline result.
- On the expert set, Gimenez et al. include indicators of "DOS stub modification", so rewriting the stub is something they anticipated. The paper should explain why a stub rewrite lowers those features, e.g., by restoring a canonical stub, so that it is clear this attacks their design and not just their feature extraction.
- The paper cites Pierazzi et al. 2020 but not the extended TOPS 2025 version (Cortellazzi et al.), which is in `papers/` and extends the side-effect discussion. It also omits that Pierazzi et al. already estimate side effects in advance by injecting each gadget into a minimal app. That is a precomputation of η, which is closer to Proposition 1 than §2's statement that side effects "generally cannot be computed in advance" implies.

*Fix:* Correct and caveat each point. Run the original ERDALT code as a second baseline.

- **C-Q4.** For ERDALT, what fraction of training perturbation vectors violate L(δ) ≥ 0? What are the results with the unmodified released code and Gimenez's protocol?

**C-W5. The ERDALT reimplementation is not yet shown to be faithful, and the conclusion drawn from it misreads what ERDALT claims.** (§5.3 "What ERDALT learns", p. 9; App. D "ERDALT", p. 16; Table 4.)

- Here ERDALT is evaded on 24/29 by GAMMA imports, an attack in its training set. Gimenez et al. report 96% robustness on EMBER (their Table 2).
- The reimplementation differs from theirs in several ways: the output layer is constrained (a change from the released code), the dataset is different (EMBER-2024 vs Dambra et al.), and the number of adversarial examples is different (3,183 vs 1,033).
- ERDALT's positivity constraint is a soft penalty (the l2 loss). An evasion by a training attack could therefore mean the penalty was not met even on training perturbation vectors. That would be a training issue, not the conceptual gap the paper describes.
- Prop. 3 of Gimenez et al. assumes a finite, known set of perturbation vectors. GAMMA with new donor content violates this by design. "The layer constrains the feature changes it was shown" is a restatement of that stated hypothesis, not a finding.

*Fix:*
- Report the fraction of training and test perturbation vectors with L(δ) < 0.
- Report results with the unmodified released code and with Gimenez's settings.
- Present the result as quantifying a known limitation.

*Verified* (Gimenez numbers and Prop. 3 hypothesis, App. D change). *Inferred* (soft-constraint violation as a possible cause).

### D-W6. Baselines from prior work are reimplemented at reduced scale, which may understate them
**Location:** §5.3 (p.9), Table 4, App. D "ERDALT" (p.16).

**Problem.**
- PV, ERDALT and adversarial training are all learned from 3,183 adversarial examples on 400 training malware. ERDALT is a reimplementation with a modified output layer. Its failure to GAMMA imports (24/29) is attributed to never having seen the benign *test* files' imports. That is a training-data coverage issue as much as a design flaw.
- The "adversarial training" baseline is retrained only on toolkit outputs, not with a problem-space adversarial-training method such as Lucas et al. 2023.
- Training-set size differs across tables. Table 4's unconstrained model is "trained on the full training set" (p.10) and reaches .998 AUC with 25/49 evaded; Table 5's 10%-subsample model reaches .996 with 26/47. It is not stated which size each defense used. This is a design choice that will persist after the rerun, not a preliminary-number artefact.

**Why it matters.** Claim 2 ("defenses built from observed attacks fall") is a statement about a class of defenses. It must not depend on starving them.

**Fix.**
- Train PV and ERDALT at the scale Gimenez et al. used, or justify the 400-malware choice.
- Show that ERDALT's GAMMA-imports failure persists when the donor pool overlaps.
- Add a stronger adversarial-training baseline that also sees rename-style edits, to show that the gap is "operations not tried" rather than "too few examples".
- Use one training-set size for all detectors that are compared directly.

*Verified* (setup text); impact *inferred*.

## Register notes (meta-review §6)

Notes:
1. *R7 (a), the escape audit.* For each clause of `precondition` and `plain_layout`, determine whether a one-field
   write triggers it and whether the loader accepts such a file. Answer from documentation (the PE specification, the
   loader's documented checks), not by execution (settled).
2. *A settled point that now looks fatal.* The population decision (files outside go to an unconstrained detector) is
   fatal only under one condition. If the escape audit shows that a loader-safe one-field write leaves the population,
   then every malware author has a free bypass, and no amount of in-population evidence answers B, C and D. The
   decision would then need revisiting for the triggerable clauses only (R7 (b)). If no such write exists, the decision
   stands, and R7 is answered by measurement and writing.

