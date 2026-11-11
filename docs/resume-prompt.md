# Resume: §5.3 from scratch — an overview, its strengths and weaknesses, and options to improve it

Read `docs/status.md` and `PLAN.md` (decision 10 above all). The structure of §5 (three findings: what hand analysis
misses, what observed attacks miss, what robustness costs) is agreed with the user: do not reopen it. **This session
restarts the analysis and planning of §5.3 (*What Observed Attacks Miss*) from scratch**; the previous session's
(33) answers were of low quality by the user's judgement. Its perspectives are recorded, with strengths and
weaknesses, in `docs/evidence/held-out-attacks-perspectives.md`: read it as input, not as a plan. Nothing in it is
decided.

**Begin the session by giving the user, before any proposal or run:**

1. **An overview of §5.3:** what it must show (its claim in the framework's terms, from `docs/paper-mock.md` §5, item
   5.3, and §2's claim about observed attacks), what exists today (the subsection in `manuscript/_f_evaluation.tex`:
   one paragraph on the learned region; the detector table's seen/held-out columns; 5.1's sentence that defenses learned
   from attacks are tested leave-one-out, with the `% SYNTHETIC` comment), which evidence it has (the learned region,
   PV, ERDALT, adversarial training, the audit table planned in the mock, C2, run 131), and how the parts connect.
2. **An analysis of its strengths and weaknesses**, harsh and objective: does the evidence test the claim from a
   defender's point of view? Which numbers depend on choices we made (the attacks in the toolkit, splits, the
   adaptive search being ours)? What would a reviewer attack first?
3. **Options to improve the section**, each with what it measures, what it costs, and what it would let the section
   claim; then one recommendation. Include the experimental designs (perspectives 2-9 of the record, and any better
   one), but start from what the section has to show, not from the experiment. Explain plainly (memory
   `explain-plainly`); examine each proposal critically before presenting it (the previous session proposed a held-out
   MAB-Malware cell that repeated the very flaw the user had just named: a deliberately chosen split).

Facts to carry in (details and sources in the record): PV leave-one-out held-out evasion 5/21 on the gamma_api fold
and 0 on the other seven; ERDALT leave-one-out partial at the end of session 33 (gamma_api 21/24, gamma_shift 5/25,
content_shift 1/28, gamma_sections and dos_extend 0); PV built from all eight attacks, adaptive 14/22; C2: the toolkit
lowered 745 of the 1,070 features edits can lower (70%; all 512 byte statistics, 233 of the other 558); the user's
hypothesis (PV's held-out evasion well above 0) failed, Claude's held. The user's methodological position: a
measurement must represent a defender's point of view, avoid any split we choose, and show the idea clearly; the mean
over leave-one-out folds favors held-out attacks that resemble seen ones; MAB-Malware belongs in the experiments only if
it manipulates different features, and then as a member of the pool, not held out specially.

**Run 131** (`run/131_loo_defenses.sh`) was rerun by the user on 2026-11-11 after a model-path bug was fixed (training
saved ERDALT models without `-s10`; the folders were renamed, the script fixed, finished steps now skip). If it has
finished: read `artifacts/experiments/a_loo/summary.json` and `a_loo/erdalt-all8-adaptive/adaptive.json` (run 128's
ERDALT gave 20/25 adaptive), and record results and runtimes in the script's header (not while it runs), in
`docs/status.md`, and in the record. The ERDALT gamma_api fold did not meet its stopping criterion (kept epoch 181).

**Still pending, after §5.3's plan is agreed:** the user's second round of feedback on 5.1-5.2 (commit 0069f56;
memory `review-comments-workflow`; log reactions in `docs/writing-spec.md`; open `% VERIFY` in 5.2 on EMBER 1.0's
hashed groups); then block 3 (5.3) and block 4 (5.4, the detector table trimmed to the undefended, monotone, and
additions rows) with the `paper-prose` skill, in blocks with `make` and `make check` and the user's review after each;
then §2's closing sentence and contribution 4 against the findings; then shortening §4 and §5 together, and PLAN.md
step 4. Constraints: §5 is three findings, not a validation section and not a defense paper (memory
`findings-not-defense-paper`); claims say "on EMBER"; no timing of Prop. 1 against extraction; report each attack
separately (memory `report-attacks-separately`); ask before changing what a claim is for (memory
`dont-reframe-research-claims`); check `manuscript/main.aux` before naming a table or section number; jobs over ~10
minutes go to the user as `run/` scripts.
