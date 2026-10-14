# Resume: ProvExp (2026-10-15) — feedback on Sections 3-5, then the front and back matter

Read `CLAUDE.md`, then `docs/status.md` (top summary, "Where we are", "Next", "Decisions"), `docs/revision-plan.md`
("Status at the end of 2026-10-14"), and `docs/review-sections-3-5-2026-10-14.md` ("Outcome"). Explain in plain
language; ask before changing what a claim is for. Follow the memory `paper-writing-style`: natural top-tier prose, no
rigid writing rules, present what works and state restrictions where they matter, never call our method weak.

## Where we are (end of 2026-10-14)

The self-review's main rejection risks are now answered with measured results (all pilot scale, seed 0):
- **Byte resolution / "by construction" (W2, W4):** a field-occlusion oracle (124 extractions/file) reaches gain 0.91;
  the byte-level pullback (1 extraction) reaches 1.71 and beats the oracle on 88/100 files; holds under random fill.
- **Pushforward on MalConv (W5):** the pushforward's top features carry about 2x the evidence of a surrogate model's
  (99/100 files, both fills), more than IG over windows, 2.7x random features.
- **Applications (W6):** the comparison's triage labels map to decisions (blind -> add a feature; oppose -> inspect
  those bytes); the audit's 9 fields lie outside the DOS header, loader-safe changes evade MalConv on 12.4% vs. 6.0%,
  and zeroing the audited fields cuts the strongest attack from 16.8% to 2.9% at 3.5 points of detection.
- **B9** (triage telling attacks from organic disagreements) failed and was cut from the paper.

Sections 3-5 were revised for narrative and presentation: three pgfplots result figures (Figure 3 faithfulness vs.
cost, Figure 4 pushforward vs. resolution, Figure 5 MalConv deletion curves; data via `scripts/paper_figures.py`),
Table 1 (EMBER provenance conventions), Table 3 (audited fields), validity fixes, sharper novelty for the pushforward.
Build is clean (`make`, `make check` in `manuscript/`).

## Today

1. **Ask the user for their feedback on Sections 3-5** (pp. 3-11 of `manuscript/main.pdf`) and apply it. Do not start
   rewriting other sections before hearing it.
2. **Then the front and back matter:** abstract, introduction, discussion, conclusion. Same standard as Sections 3-5:
   strong narrative and presentation, consistent with the revised body (new: MalConv faithfulness, the mitigation, the
   fields table, the figures). Check every contribution bullet against its evidence. Results stay in the evaluation.
   End with a holistic pass (`make check`, rendered pages, cross-section consistency).
3. **Then reassess W7** with the user: the Android second extractor is the largest remaining weakness and several
   sessions of work; the user wants the PE/EMBER contributions solid first.

## Still blue (synthetic placeholders)

The retrained-MalConv row of Table 4 and its sentence in 5.3 (needs MalConv retraining, cluster round); the Android
paragraph in the discussion (W7). Everything else in the body is measured.

## Working rules

- Long jobs: smoke-test, then hand the user a numbered `run/` script (≤16 workers, ≤2 GPUs; the user picks GPUs).
- Realistic perturbations only for anything framed as an attack; no sandbox execution.
- Mock an experiment's result before building it; state a short hypothesis before running anything.
- Update `docs/status.md` at the end of the session and write the next resume prompt.
