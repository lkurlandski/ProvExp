# Resume: ProvExp (2026-10-13)

Read `CLAUDE.md`, then `docs/status.md` ("Where we are", "Next", and the 2026-10-13 decisions).

## Where things stand

- Framework and intrinsic evaluation (CP, PB1, PF1, PB2/PF2) done at pilot scale.
- Both extrinsic applications done and written up: **CM**, the pullback comparing two detectors per file
  (`docs/experiments/cm.md`); **AU**, the pushforward auditing MalConv across a corpus (`docs/experiments/audit.md`). The audit
  scrambles the bytes P names for the features MalConv rests on (9/20 confirmed, 22.5% evasion) and compares the two
  detectors globally in feature space.
- The manuscript (`manuscript/_d_applications.tex`) has both applications, the local/global claim split, and no
  more Appendix F. Abstract, introduction contributions, discussion, and summary are still early-stage.
- We just did a large repository cleanup: dropped threads archived (`scripts/archive/`, `run/archive/`), dead ideas
  recorded in `docs/graveyard.md`, docs de-staled.

## Likely next

1. A naming/organization scheme for the live docs and experiment IDs is proposed and awaiting the user's decision;
   the doc renames and manuscript label-sync are held until then.
2. Manuscript drafting (introduction contributions, abstract, discussion, summary). Ask before changing a claim's
   purpose.
3. Scale-up (2,000 files, seeds 0-2) and the deferred pieces (MLP's return, CM real-attack transfer, AU mitigation)
   when the user decides.

Explain in plain language; no dense shorthand.
