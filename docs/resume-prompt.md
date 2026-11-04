# Resume: ProvExp (after 2026-11-04, session 11): read runs 124-126, then strong attacks; the introduction waits

## Where things stand

Session 11 replaced "write the introduction" with a strategic review, at the user's request: once an introduction
exists, Claude tends to stay loyal to it, and the research is still open. The review
(`docs/reviews/2026-11-04-strategy.md`, read it first) concluded: **strengthen what we have; no new directions.**
Details: `docs/status.md` (session-11 block) and `PLAN.md` ("Next steps (2026-11-04, session 11)"). Nothing pushed.

1. **Gimenez et al. are now portrayed accurately** (§3, §5, §6 ¶3, literature notes). Their main method is ERDALT: a
   linear post-processing learned from adversarial examples, feeding a monotone network, which they call empirically
   robust. Their certified route is the 40 hand-picked features; PV is the comparison method they define. Their
   Proposition 2 (every robust detector is monotone over some post-processing) is the converse of Proposition 1.
2. **Attacks are the main open weakness (W2).** Zainab et al. (arXiv 2609.34456, Sep 2026) report MAB-Malware
   evading an EMBER-2024 GBDT on 83.4% (MiniMal 30.6%, GAMMA shift 12.7%); their setup is not yet read, so do not cite
   the numbers yet. Our toolkit's eight attacks together reach 55% on the undefended model, and our adaptive search
   only 20%. The search is greedy, draws ~25 random candidates per step, stops at the first non-improving step, and is
   capped at 100-200 scored candidates to match the toolkit, although scoring a candidate costs only a prediction.
3. **The two-sided-feature diagnostic failed its hypothesis.** Of the 1,060 features Table 7's features row drops:
   - 683 are recovered by the sums re-encoding (21.4% of the unconstrained model's gain);
   - 200 are section hash buckets coupled under rename (3.7%);
   - 89 are truly two-sided overwrites (11.0%);
   - 88 are the unmodeled parser warnings (6.3%).

   Under rename, the only one-sided combination of buckets is their total, so a computed re-encoding (an "ERDALT
   reply") is not worth building. Magnitude bounds are also deprioritized: Gimenez et al. argue that magnitude is
   irrelevant for malware, and A' certified only up to 4 KB.
4. **Running (user, tmux):** `run/124` (GAMMA at the literature budget: a strong-toolkit column), then `run/125`
   (adversarial training on gamma_api + header_fields + gamma_sections at that budget), and `run/126` (the price list,
   `NUM_WORKERS=8`).

## Next session, in order

1. **Read `run/126`** (`artifacts/experiments/a_price_list/table.json`; logs
   `artifacts/logs/train_classic-gbdt-0-s10-price-*.log`). Hypothesis (in the script header): no single operation
   costs more than ~1 point of TPR at 1% FPR (rename and the header overwrites the most), and dropping vs.
   constraining each account for about half of the full catalogue's 3.9 points. Report a failed check as such. If the
   parser warnings alone cost a point or more, propose modeling them (an extension of the existing instrumentation).
   Decide with the user where the price list goes (a §5 paragraph or a small table). Sync the run header.
2. **Read `run/124`** (`artifacts/experiments/a1/toolkit-literature/{fullstore,s10}/table.json`; logs
   `artifacts/logs/a1_eval_literature_{fullstore,s10}.log`; report any `LOST` lines). Hypothesis: the unconstrained
   detectors lose more than at the low budget (gamma_api above 22/49 uncapped), the monotone rows stay at 0% in their
   population, gamma_sections stays weak.
3. **Read `run/125`** (`artifacts/experiments/a1/advtrain-strong/`: `generated/report.json`, `toolkit/`,
   `toolkit-literature/`, `adaptive-*`; logs `a_advtrain_strong_generate.log`,
   `train_classic-gbdt-0-advtrain-strong.log`, `a1_eval_advtrain_strong*.log`, `a1_adaptive_advtrain_strong.log`).
   Hypothesis: it resists gamma_api and header_fields, but the adaptive search still evades it at about the
   unconstrained rate.
4. **Table 7 with the user:** the strong-toolkit column (capped; uncapped in a note?), and whether run 125's row
   replaces or joins run 122's (footnote: gamma_api and header_fields are held-out for PV but trained on here). Then
   the sentence on why the toolkit's section injection fails here. Sync the run/124 and run/125 headers. `make` /
   `make check`.
5. **Strong attacks (plan with the user first; mock the Table 7 cells before code):**
   - (a) The adaptive search with a realistic scoring budget: thousands of predicted candidates per file, restarts or a
     beam instead of the strict-improvement stop, every kept step still written with our byte-level edits and
     re-extracted. Go/no-go: it beats the toolkit union (55%) on the undefended model; if not, the framework's
     attack-side claim stays out of the paper.
   - (b) MAB-Malware as a held-out attack against every Table 7 row, after reading Zainab et al.'s setup (code:
     github.com/mashalzainab/windows-malware-adversarial-robustness). Hypothesis: it evades PV and adversarial
     training often, and the monotone rows never on files in the population.
   - Smoke-test both, then `run/127`+.
6. **Open decisions for the user** (after 5): whether ERDALT becomes a Table 7 row (now a baseline question only); and
   whether the headline becomes "Gimenez et al.'s Proposition 2 needs a feature mapping; we compute it" (a claim
   change, not adopted). Only then the introduction and the other empty sections, spine first with `/paper-prose`.

## Carry-forward (unchanged)

- One `% VERIFY` in §6 ¶3 (Chen et al. 2021's monotonicity scope). Table 5's population scoping not re-audited
  (recorded decision). Routing to Table 7's sums rows needs a plan first. A G1 unit test for the expert instrumentation
  is a nice-to-have. `tests/test_shortcuts_*` fail to collect (pre-existing).
- The user owes the upstream reports in `docs/upstream-issues.md` (items 1-7).
- Only run jobs under ~10 min yourself (at most 8 threads while the user's runs go); otherwise smoke-test and hand over
  a `run/` script (next number **127**), reading `NUM_WORKERS`.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
