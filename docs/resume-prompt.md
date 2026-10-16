# Resume: ProvExp (2026-10-16) — the new Section 3 theory, then the cheap checks for the exact pushforward

Read `CLAUDE.md`, then `docs/status.md` (top summary, "Next (this thread)"), `docs/theory.md` (the two pillars,
decisions, run 61's result, parked ideas), and the new Section 3 in `manuscript/_c_method.tex` (pp. 4-6 of
`manuscript/main.pdf`). Explain in plain language; ask before changing what a claim is for. Follow the memories
`paper-writing-style` (natural prose, never call our method weak) and `run-long-jobs-yourself` (estimate the runtime
from the smoke test before deciding who runs a job; over ~10-15 min, hand the user a `run/` script).

## Where we are (end of 2026-10-16)

The session answered W1 (thin technical novelty, `docs/review-2026-10-14.md`) by giving Section 3 real theory:
- **Shapley-grounded P (3.3):** an extractor reads items; an element's ideal share of a feature is its Shapley value
  in the game "the feature computed from the present items only, context (parse, denominators) held fixed".
  Proposition Additive Features: for features additive over their items (fields, counts, histograms over a fixed
  denominator, one-sign hashed counts), this is exactly what our instrumentation records. Entropies, averages, ratios,
  min/max get a data-flow convention. P stays nonnegative (user), with a paragraph saying why. The black-box estimate
  is 3.3.1 (user likes it; may move to an appendix later).
- **Transfers (3.4):** Proposition Exact Pullback (linear model over additive features -> the pullback is the exact
  problem-space Shapley value; G-DeepSHAP's linear-chain result, for a program). Definition/Proposition Exact
  Pushforward: today's one-step pushforward is the first step of an iteration a_{k+1} = a_k + psi(b - P a_k) that
  converges to the least-squares inverse, conserves attribution, recovers everything the bytes determine (the null
  space of P is unrecoverable by any method), and equals one step when no element is shared. Pullback = the chain
  rule; pushforward = its inverse. Only the pushforward has an inverse problem.
- **Run 61 (go/no-go):** recovering TreeSHAP from its pullback, R 0.80 -> 0.86 at bytes (93/100 files) and
  0.36 -> 0.44 at 256 windows. A qualified go: reliable but modest gain; the remaining gap is non-identifiability.
- **Coarsening** left Section 3 (user: weak, distracting); P^G now lives in the new Section 4, "Experimental Setup"
  (`_d_setup.tex`), a rough holding area for EMBER/data/models/deletion/windows. The experiments are unchanged and
  still use the one-step pushforward (TODO comment in `_c_method.tex`).

## Today

1. **Ask for the user's feedback on Section 3** and apply it (tight, clean subsections; no rambling).
2. **Identifiability ceiling** (cheap): extend `scripts/pf_inverse.py` with the best R the bytes allow (merge features
   with identical provenance columns, or project TreeSHAP onto P's row space); smoke-test; the user runs it (~17 min,
   like `run/61`). State the hypothesis first: the exact pushforward's 0.86 is near the ceiling.
3. **MalConv test with the exact pushforward** (as runs 58/60; GPU; user runs it).
4. Only then decide with the user whether the experiments switch to the exact pushforward and which pilot runs to
   repeat (only the pushforward half). Do not rerun pilot experiments before the user approves.

## Open for the user

- The black-box P's final place; whether to keep the GBDT window-pushforward test (lab study).
- Parked, not for now: case studies on bounding control of a byte set (pullback side) and naming a raw-byte model's
  units (pushforward side), `docs/theory.md`.

## Working rules

- Long jobs: smoke-test, estimate, then a numbered `run/` script (<= 16 workers, <= 2 GPUs); the user runs it in tmux.
- State a short hypothesis before running anything; mock an application's result before building it.
- Update `docs/status.md` at the end of the session and write the next resume prompt.
