# Resume: ProvExp (after 2026-10-22, end) — feature provenance, conceptual phase

Read `CLAUDE.md`, then `PLAN.md`, `docs/feature-provenance-model.md` (the model; Sections 4-4a claims and proof
sketches, Section 6 coverage), `docs/direction-A-mock.md` (the mock of direction A's tables), and
`docs/literature-2026-10-22.md`. `docs/status.md`'s top block summarizes the session. Start by recapping the big
picture for the user in plain language before asking any decision. Be harsh about novelty; never raise deadlines.

## Where things stand

- Coverage on paper: 34 transformations (secml-malware, Labaca-Castro et al., MAB-Malware); 56% content or
  item-creating, 38% declared structural, 6% UPX. Adopted: C1 covers declared structural edits; "move" is a fourth
  item operation (32/34 covered).
- Proof sketches written; C1 rests on A1-A4 (complete location, local contributions, local recognition, faithful
  declarations). C2 and C4 restated and adopted (co-movement vs. inseparability; per-readout direction tests).
- Mock of A: monotone detectors with C4-derived directions (sound against unseen and adaptive attacks) vs. Gimenez et
  al.'s PV selection; layer-2 sums as monotone inputs to recover accuracy; C1-guided adaptive attack.

## Next

1. Steps 1-2 are done (`docs/direction-A-threat-model.md`, run 76). Next: check 3 (the as-is row from the feature
   store; the re-encoded row needs re-extraction, to scope with the user), verify the duplicate-DLL import quirk on a
   real file, and check 2 (secml-malware + LIEF: ask before installing).
2. Follow `PLAN.md`'s revised next steps: go/no-go 3 partial (monotone LightGBM; the user runs training), go/no-go 2
   (secml-malware attacks; ask before adding dependencies), then the item table and C1 predictor (go/no-go 1).
   **Any no-go goes to the user before anything is dropped.** Treant and Chen et al. CCS 2021 are read (fourth pass
   of the literature doc). Smoke-test small, hand long runs to the user as `run/` scripts.
4. Later: targeted search and mocks for B and C; clean out old-direction materials; update `CLAUDE.md` conventions.

## Notes

- `papers/` holds user-downloaded PDFs; do not commit. secml-malware source and MAB-Malware text were fetched into the
  session scratchpad; re-fetch if needed.
