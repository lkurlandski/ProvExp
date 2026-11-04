# Resume: ProvExp (after 2026-11-04, session 10): read runs 124/125 into Table 7, finish the §6 review, keep writing

## Where things stand

Session 10 measured Table 7's adversarial-training baseline and its reference, fact-checked related work, and answered
the user's worry that our attacks are too weak. Details: `docs/status.md` (session-10 block). Nothing pushed.

1. **Table 7 (`manuscript/_f_evaluation.tex`, `tab:eval:detectors`).** Measured now: "adversarial training on the
   toolkit" (run 122: 0.998 / 95.6% / 48/50 / seen 8% / held-out 50% / adaptive 19%) and its reference "unconstrained,
   full training set" (run 123: 0.998 / 95.6% / 49/50 / 10% / 53% / 20%). Footnote § marks the full-store rows; the
   other rows' first five columns use the 10% subsample. Both are weak baselines: the four "seen" attacks barely evade
   the undefended model, so adversarial training on them changes little.
2. **Attack strength (the user's concern).** All eight toolkit attacks evade the undefended model on 55% (Gimenez et
   al.'s own Table 1: 25%). The attack code was audited for bugs like the two the user found in maltorch (same
   authors): none. GAMMA section injection fails against this model by design: it adds one section per donor in every
   candidate, even at weight 0, and the empty sections raise the score (`docs/upstream-issues.md` item 7). Our
   adaptive search is the strongest attacker (20% on the undefended model).
3. **Running (user, tmux):** `NUM_WORKERS=16 bash run/124_a1_toolkit_literature_budget.sh ; NUM_WORKERS=16 bash
   run/125_adv_training_strong.sh` (~2-2.5 h, then ~3.5-4 h).
   - `run/124`: gamma_sections + gamma_api at the GAMMA paper's budget (`--budget literature`: ~510 queries, 75 donors)
     against every Table 7 detector except the expert set; within the byte cap and uncapped.
   - `run/125`: adversarial training on the attacks that work (gamma_api, header_fields, gamma_sections; literature
     budget; 400 training malware) -> `seed-0-advtrain-strong`; its low-budget toolkit columns, strong column, and
     adaptive union.
4. **§6 related work.** ¶2-4 were fact-checked and corrected (Chen et al. 2020 on Hidost; Gimenez's Prop. 1 and expert
   set in their own words; Wagner & Graham; pages). **The user is reviewing ¶2-4**; one ¶3 sentence ("A hand analysis
   inherits the threat model its authors had in mind") was left for that review.

## Next session, in order

1. **Read `run/124`** (`artifacts/experiments/a1/toolkit-literature/{fullstore,s10}/table.json`; logs
   `artifacts/logs/a1_eval_literature_{fullstore,s10}.log`; check for `LOST` lines and report them). Hypothesis (in
   the script): the unconstrained detectors lose more than at the low budget (gamma_api above 22/49 uncapped), the
   monotone rows stay at 0% in their population, gamma_sections stays weak. Report a failed check as such.
2. **Read `run/125`** (`artifacts/experiments/a1/advtrain-strong/`: `generated/report.json`, `toolkit/`,
   `toolkit-literature/`, `adaptive-*`; logs `a_advtrain_strong_generate.log`, `train_classic-gbdt-0-advtrain-strong.log`,
   `a1_eval_advtrain_strong*.log`, `a1_adaptive_advtrain_strong.log`). The script prints AUC / TPR and the adaptive
   union to the user's terminal; recompute them as in session 10 if needed. Hypothesis: it now resists gamma_api and
   header_fields, but the adaptive search still evades it at roughly the unconstrained rate, with no guarantee.
3. **Put both into Table 7, with the user deciding the layout:** a strong-toolkit column (capped; uncapped in a note?),
   and whether the run-125 row replaces or joins run 122's (footnote: gamma_api and header_fields are PV-"held-out" but
   trained on here). Then a sentence on why the toolkit's section injection fails here and why the adaptive search is
   the strongest attacker. Sync `run/124` and `run/125` headers (runtimes, results) once they are not running.
   `make` / `make check`.
4. **§6 ¶2-4 review** when the user brings it: log the raw reactions in `docs/writing-spec.md`, update the
   `paper-prose` skill's lessons.
5. **Next sections with the skill** (`/paper-prose`), spine first: introduction (§1, framework-first with a
   detector-centered results paragraph; the Hidost/Chen et al. observation may help: provenance readable from feature
   names is the special case we generalize), background (§2), discussion (§7, incl. the R7/R15 sentences), Figure 1,
   abstract last. Budgets: `docs/paper-mock.md`.

## Open user decisions

- Table 7 layout for runs 124/125 (above). R4 (a second built instance) stays a tier-3 decision.

## Carry-forward (unchanged)

- Table 5's population scoping not re-audited (recorded decision). Routing to Table 7's sums rows needs a plan first.
- A G1 unit test for the expert instrumentation is a nice-to-have. `tests/test_shortcuts_*` fail to collect
  (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (now items 1-7).
- Only run jobs under ~10 min yourself; otherwise smoke-test and hand over a `run/` script (next number **126**),
  reading `NUM_WORKERS`. The `/delegate` skill covers safety-classifier false positives on per-sample analyses.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
