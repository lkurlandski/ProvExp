# Resume: the user's feedback on §5.1-5.2, the leave-one-out run, then §5 blocks 3-4 (5.3, 5.4)

Read `docs/status.md` and `PLAN.md` (decision 10 above all, with its leave-one-out note; next step 3). The plan for §5,
one line per paragraph, checks C1-C3, the drafting order, and the revisions after the user's review of blocks 1-2 are
in `docs/paper-mock.md`, §5. The structure is agreed with the user: do not reopen it.

**Where §5 stands.** Blocks 1-2 (the lead, 5.1, 5.2 *What Hand Analysis Misses*) are drafted and revised after the
user's review (commit 0069f56). 5.1 already states leave-one-out as the protocol for the defenses learned from attacks;
the held-out cells are `\synthetic` (`% SYNTHETIC` comment in `manuscript/_f_evaluation.tex`). Still to write: block 3
(5.3 *What Observed Attacks Miss*, with the new audit table) and block 4 (5.4 *What Robustness Costs*, with the
detector table trimmed to the undefended, monotone, and additions rows).

**Order of work.**
0. **The user's feedback on 5.1-5.2 first** (they review the revised version, commit 0069f56). Follow memory
   `review-comments-workflow`: answer their questions plainly first, then a numbered plan with one recommendation per
   comment; apply after approval, `make` and `make check`, report per item. Log the reactions raw in
   `docs/writing-spec.md`. What the first review asked for, so as not to regress (reaction log, 2026-11-10, session 31):
   plain numbers instead of "pilot scale"; no "written to disk" or our-code-is-correct bookkeeping outside 5.1's one
   sentence on re-extraction; attacks described plainly, no "instrument" staging; every count defined where it is
   used; each subsection opens with its question, and its parts are marked with run-in headings (5.3 and 5.4 should
   follow 5.2's pattern: setup sentences first in each part, analysis last). Keep the drafting rules for later domains
   (mock, §5, "Extending §5 to other domains"): the claim in the framework's terms first, then EMBER's number; PE
   mechanics in evidence sentences or Appendix D; tables that a second instance extends by rows. Open: verify that
   EMBER 1.0's hashed groups (Severi et al.) match EMBER 2024's (`% VERIFY` in 5.2).
1. **Run 131, if it has finished** (`run/131_loo_defenses.sh`, started by the user 2026-11-10 on GPU 3, ~7 h; if not,
   go on with step 2 and come back). Read `artifacts/experiments/a_loo/summary.json` (per-fold and mean held-out
   evasion for PV and ERDALT, files evaded in any fold) and `a_loo/erdalt-all8-adaptive/adaptive.json` (ERDALT-8's
   beam cell; run 128's ERDALT gave 20/25), plus `artifacts/experiments/a1/advtrain/generated-heldout/report.json`
   (step 0: valid outputs per attack). Judge against the hypotheses in the script's header: the user's (PV's
   held-out evasion well above 0, because each attack lowers features the others don't) and Claude's expectation
   from the stored perturbation vectors (the eight attacks lower nearly the same features: only gamma_sections, 49,
   and gamma_api, 10, lower many that no other attack lowers; so PV mostly 0 outside the gamma_api fold, smoke 5/21;
   ERDALT high on the gamma_api and header_fields folds). Report a failed hypothesis as such. Record the result and
   runtimes in the script's header (do not edit it while it runs), status, and the mock. Check the logs for `LOST`
   lines and ERDALT's stopping criterion (`met_criterion` in each model's metrics.json; run 128 met it only at the
   last epoch). Before changing what the toolkit column claims in 5.3, discuss with the user (memory
   `dont-reframe-research-claims`): if PV's held-out evasion is near 0, the point that observed attacks miss the hole
   rests on the adaptive column (PV-all 14/22) and on C2, and MAB-Malware as an independent held-out source becomes
   more relevant (PLAN.md, step 5).
2. **Check C2** (mock, §5): of the features the derived table marks down or both, the share any toolkit output lowered,
   on files in the population (`scripts/a1_toolkit_split.py`, runs 78 and 105; `artifacts/experiments/a_pv/deltas.parquet`).
   State the hypothesis first; existing outputs only, under ~10 minutes.
3. **Block 3: 5.3**, with the audit table, the leave-one-out numbers replacing the `\synthetic` cells (remove the
   `% SYNTHETIC` comment once replaced). Then **block 4: 5.4**.
4. §2's closing sentence and contribution 4 of the mock, re-read against the findings.

Use the `paper-prose` skill; draft in blocks with `make` and `make check`, shown as rendered text, with the user's
review after each block. Constraints carried over: §5 is three findings, not a validation section and not a defense
paper (never call the detectors' cost "small"; memory `findings-not-defense-paper`); claims say "on EMBER"; no timing
of Prop. 1 against extraction; report each attack separately, never a union across searches unless the table says so
(memory `report-attacks-separately`); check `manuscript/main.aux` before naming a table or section number; §5 ~3,200
words (50-75% over allowed while drafting).

Then: shorten §4 and §5 together (§4 ~1,540 words against ~1,000; §4.3 first), then PLAN.md step 4 (the review prompt,
the full simulated review, the truncation brainstorm).
