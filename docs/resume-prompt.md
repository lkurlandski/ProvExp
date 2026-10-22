# Resume: ProvExp (after 2026-10-22) — feature provenance, conceptual phase

Read `CLAUDE.md`, then `PLAN.md` (restarted 2026-10-22), `docs/feature-provenance-model.md` (the model), and
`docs/literature-2026-10-22.md` (the related work read so far). `docs/status.md`'s top block summarizes the restart.
Explain in plain language; be harsh about our own novelty; never raise deadlines or conference cycles. Follow the
memories `be-self-critical-on-novelty`, `mock-the-result-first`, `check-baseline-realism`, `malware-generic-over-pe`,
`symmetry-nice-to-have`.

## Where things stand

- The explanation-provenance paper is abandoned (`docs/graveyard.md`); its code, data, and manuscript are source
  material. Do not polish or run anything for it (run/75 is on hold).
- New thesis: simple feature provenance bridges the feature-problem space gap in malware classification. Direction A
  (threat models to feature space) is the core; B (auditing raw-byte detectors for backdoors/shortcuts) and C (evasion
  diagnosis across ensemble members) support it, each subject to its own screening.
- The model: three layers (parse with membership and location; additive item contributions; a readout), byte edits
  translated to item operations (content / item-creating / structural), claims C1-C4. The user likes its generality;
  wants to stay conceptual before prototyping or smoke tests.

## Next (agreed order)

1. **Coverage on paper.** For each transformation in secml-malware (Demetrio et al.), Labaca-Castro et al.'s
   toolkit (Table 1 of arXiv 2102.06747), and MAB-Malware's actions, classify it as content, item-creating, or
   structural under the model, and list the EMBER feature groups it touches (use the worked example's table format in
   `docs/feature-provenance-model.md`, Section 5). Report the share in each class. If most are structural, stop and
   discuss with the user before going on.
2. **Proof sketches** for C1-C4, in `docs/feature-provenance-model.md`.
3. **Mock A's paper table(s)** (attack side and/or defense side), naming the model component behind each column, the
   realistic baselines (Gimenez et al.'s PV selection and Labaca-Castro et al.'s probabilities on held-out attack
   families; Severi et al.'s 17 features; Rosenberg et al.), and a falsifiable go/no-go check.
4. Later: targeted search and mocks for B and C; clean out leftover materials of the old direction; update
   `CLAUDE.md` conventions as the new design firms up.

## Notes

- `papers/` holds PDFs the user downloaded (e.g., Incer et al.); do not commit it. Ask the user for any paywalled paper.
- Paper texts read on 2026-10-22 were fetched from arXiv into the session scratchpad; re-download if needed.
- Update `docs/status.md` and rewrite this prompt at the end of the session.
