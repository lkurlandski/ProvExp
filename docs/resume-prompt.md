# Resume: ProvExp (after 2026-10-16) — front and back matter

Read `CLAUDE.md`, then `docs/status.md` (top summary, "Next (this thread)") and `docs/theory.md` ("The ceiling and
MalConv", the verdict). Skim `manuscript/main.pdf` end to end: Sections 3-6 are revised; the abstract, introduction,
discussion, and conclusion are not. Explain in plain language; ask before changing what a claim is for. Follow the
memories `paper-writing-style` (natural prose, present what works, never call our method weak) and `limitations-tone`.

## Where we are (end of 2026-10-16)

- **Section 3 has real theory** (answer to W1): Shapley provenance and Proposition 1 (instrumentation = Shapley
  provenance for additive features), Proposition 2 (exact pullback for a linear model), Definition 7 / Proposition 3
  (exact pushforward: the inverse problem; what any pushforward can recover). New background subsection 2.3 on Shapley
  values. Definitions and propositions are numbered separately.
- **The exact pushforward stays theory** (user): runs 61-63 show one step gets close (R 0.80 vs. 0.86 recovering
  TreeSHAP; MalConv: identical, 6.25 both); what the exact form misses lies mostly in features with identical
  provenance (twins oracle 0.95). Two sentences report this in Section 6.1. The experiments keep the one-step
  pushforward; no reruns.
- Section 4, "Experimental Setup" (`_d_setup.tex`), is still a rough holding area.

## Today

1. **Front and back matter** were updated for the Section 3 theory (2026-10-16, light touch). Ask for the user's
   feedback and apply it; open there: an overview figure by the end of the introduction, the CM real-attack TODO, the
   synthetic Android paragraph (W7).
2. If time allows: refine Section 4.

## Open for the user

- The black-box P's final place (3.3.1 or an appendix); whether to keep the GBDT window-pushforward test.
- W7 (Android, a second extractor) after the front matter; the scale-up last, only when the user decides.
- Parked: case studies on bounding control of a byte set and naming a raw-byte model's units (`docs/theory.md`).

## Working rules

- Long jobs: smoke-test, estimate, then a numbered `run/` script (<= 16 workers, <= 2 GPUs); the user runs it in tmux.
- State a short hypothesis before running anything; mock an application's result before building it.
- `make` and `make check` in `manuscript/` after every edit.
- Update `docs/status.md` at the end of the session and write the next resume prompt.
