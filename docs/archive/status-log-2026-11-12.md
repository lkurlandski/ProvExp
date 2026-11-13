# Status log, archived 2026-11-12 (sessions 41-42)

Moved from `docs/status.md` at the end of sessions 50 (41-41b) and 52 (42).

- **2026-11-12 (session 41b, parallel to 41): §5's humanistic review, four passes.** Lead and 5.1 (seven findings),
  5.2 (seven; #7, the Rich header, dropped by the user: a PE construct the reader can look up), 5.3 (five, plus the
  unconstrained detector in 5.1), 5.4 (six). All others approved and applied; reactions logged raw in
  `docs/writing-spec.md`. The user: "serious structural modifications" later to how §5's questions are asked and
  answered, with visual emphasis (PLAN.md step 2); for now each lead answers its question. Open, outside the prose:
  5.1's 73,063 is run 107's direction check, while the exactness counts are Appendix D's (62,604 + run 118's 34,965);
  fix at scale-up unless the user wants it now. **Next:** a holistic review of §5 with weight on the
  contributions' importance (user), then PLAN.md step 2; `docs/resume-prompt.md`.

- **2026-11-12 (session 41): the ERDALT check (only), no run.** The score floor is not a thin margin: 99% of test
  goodware sit at ERDALT's lowest score, so the 1% FPR threshold sits at its edge; GAMMA imports drives detected
  malware from logits up to ~1,000 to the floor (24/29; 28 counting over-budget). Detection weaker than their paper
  (AUC 0.88 vs 93.0% on another dataset), stopping criterion met at one epoch; left to the scale-up. Their code read
  against their paper: the paper fixes only the abstract architecture and losses; the one conflict is the output
  layer, which our port constrains. User (strongly held): implement from the paper where the code breaks the
  guarantee; no "their code exactly" variant. PLAN.md step 3, `docs/upstream-issues.md` item 8 updated.
  **Next:** `docs/resume-prompt.md` (unchanged: §5's humanistic review).

- **2026-11-12 (session 42): §5's holistic review (contributions' importance); the table remake's first attempt
  rejected.** Seven findings; the user approved 1-4, applied in 68f6385: what Gimenez et al. report (the expert set and
  PV never evaded by the toolkit attacks; detection and robustness a "trade-off regarding features set") stated before
  our results; the §5 lead names what breaks; 5.4 names both alternatives (learned, hand-picked); 5.2's cost paragraph
  ends on why a broken guarantee matters. Finding 5 (5.3's topic sentences) dropped; the uncited "usually tested
  against an attack it did not learn from" fixed (49d879d). Findings 6 (no table shows 5.3) and 7 (§2 promises an
  attack; a known weakness, not fixable now) noted in PLAN.md step 2. The tables come before the question-and-answer
  emphasis (user). Claude's table mock-ups (`docs/archive/table-mockups-2026-11-12/`) were judged "pretty bad, quite
  possibly as bad if not worse than what we already had"; facts they surfaced are in PLAN.md step 2 (a), among them
  that 5.2's *Why it errs* names three parser facts where the errors need five. `make check`: a 2 pt overfull page box
  among the appendix floats since 68f6385 (harmless). **Next:** `docs/resume-prompt.md` (the tables, restarted from
  what the user dislikes).
