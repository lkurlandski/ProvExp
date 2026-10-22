# Resume: ProvExp (after 2026-10-22) — direction A, first checks

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Next steps (end of 2026-10-22)"),
`docs/direction-A-mock.md`, and `docs/direction-A-threat-model.md`; the model is in
`docs/feature-provenance-model.md`. **Start by recapping the big picture for the user in plain language** (where the
research stands, what today's results mean, what decision is next) before asking anything. Be harsh about novelty;
never raise deadlines; bring any no-go to the user before dropping anything; no result may rest on an extractor quirk.

## Where things stand

- Thesis: feature provenance computes what an attacker's edits can do to a malware detector's features (side
  effects, coupling, reachable values, directions), which robust-detector work gets by hand or from running attacks.
- Direction A's target (approved): Table A1, monotone (guaranteed-robust) GBDTs whose feature directions come from
  the extractor (C4), against Gimenez et al.'s perturbation-vector selection, on seen, held-out, and adaptive attacks;
  layer-2 re-encodings (region-restricted counts, split signed buckets, merged imports) to keep accuracy.
- Run 76 (direction table): a sound monotone detector can use 22% of EMBER's features as they are, 96% re-encoded
  (M_add); 19% / 85% under M_full.
- The duplicate-DLL import quirk is patched as a pure addition (`merge_import_descriptors`); A1 uses the patched
  extractor. The user files the upstream report (`docs/upstream-issues.md`).

## Next

1. **Read run 77** (`run/77_a_check3_asis.sh`, launched by the user): `artifacts/models/gbdt/seed-0-a-*/metrics.json`
   and logs `artifacts/logs/train_classic-gbdt-0-a-*.log`. Compare test AUC with 0.99759; hypothesis ~0.97-0.98 for
   M_add monotone, ~0.985 quirk-fixed, ~0.96 M_full. Also compute TPR at 1% FPR from `ts_predictions.parquet`. Record
   the reading in `docs/direction-A-threat-model.md` and the status; if it reads as a no-go, discuss with the user.
2. Ask the user for the OK on the attack environment (separate Python 3.10 venv, pinned secml-malware clone, our
   LightGBM model via thrember there); then make GAMMA's section injection run on a few pilot files.
3. Estimate the cost of the re-encoding extraction (a new feature type over the training set), and agree on its scale
   with the user before writing it.
4. Then go/no-go 2 (PV's hole, quirk-fixed table) and the item-table engineering for go/no-go 1 (`PLAN.md`).

## Notes

- `papers/` holds user-downloaded PDFs; do not commit. Fetched paper texts and the secml-malware clone are in the
  previous session's scratchpad; re-fetch as needed.
- Training uses the full EMBER-2024 splits (2.07M train), ~6-7 min per GBDT at 16 threads; hand anything over
  ~10-15 min to the user as a `run/` script.
