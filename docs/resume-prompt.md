# Resume: ProvExp (after 2026-10-26) — direction A done at pilot scale; screen the second application

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` (Thesis, Directions incl. **A'**, and "Next steps (end
of 2026-10-26)"), and `docs/direction-A-summary.md` (where A stands: checks, mock vs measured, gaps, harsh notes). The
results tables are in `docs/direction-A-A1-design.md` ("Result: Table A1", "Result: Table A2"); the model is in
`docs/feature-provenance-model.md`; related work in `docs/literature-2026-10-22.md`. **Start by recapping the big
picture for the user in plain language** (where the research stands, what direction A showed, what is next) before
asking anything. Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything;
no result may rest on an extractor quirk. Run only jobs of ~10 minutes or less yourself (estimate from the slowest
case first); anything longer goes to the user as a `run/` script (default 16 workers; never cap workers in Python).

## Where the research stands

- Thesis: feature provenance (instrumenting the extractor) computes what an attacker's edits can do to a malware
  detector's features, which robust-detector and realizable-attack work otherwise gets by hand or by running attacks.
- **Direction A (core) is complete at pilot scale** (10% subsample, seed 0, 50 pilot malware, M_full, 1% FPR); every
  go/no-go check and falsifiable outcome passed:
  - Monotone GBDTs with directions from the extractor (C4) are never moved by any attack — toolkit (seen and
    held-out), and the C1-guided adaptive search (largest score change exactly 0.0, also on real re-extraction). The
    M_full rows keep 86.7% (features) / 88.6% (sums re-encoding) TPR vs 93.5% unconstrained and still detect 40-41/50
    pilot malware after every attack (unconstrained 20/50).
  - Gimenez et al.'s PV selection, built from 4 or all 8 secml-malware attacks, holds against those attacks but costs
    ~35 TPR points (56.2% / 53.8%) and falls to the adaptive search on 21/22 and 22/22 files it detects.
  - Table A2: the adaptive search needs 3-4.5 extractions per file (toolkit attacks ~100); provenance-chosen section
    names (inverting the section hash for the bucket and sign wanted) take PV-seen from 11/22 (random names) to 21/22.
- Gaps (in `docs/direction-A-summary.md`): expert-set row, cost column, adversarial-training row, a second toolkit for
  held-out attacks, leave-one-out PV, scale. The main open risk is novelty, not the results: the monotone guarantee is
  Gimenez's and Incer's; ours is deriving the threat model's effect on features automatically.

## Do next (agreed with the user, 2026-10-26)

1. **Screen the second application on paper, three candidates side by side** — no code before one passes:
   - **A'** (the user found it "pretty intriguing"): realizing feature-space attacks in the problem space, including
     hashed features (Severi et al. ruled them out; Rosenberg/Pierazzi et al. use hand-written modifiers). Table A2's
     search is half of it. `PLAN.md`, Directions.
   - **B**: auditing raw-byte detectors for backdoors/shortcuts (edge only for triggers in shared or hashed content).
   - **C**: diagnosing evasion through disagreement between heterogeneous ensemble members (must beat score
     disagreement where scores are silent).
   For each: the screening criteria (`CLAUDE.md`, Framework conventions: must cross the feature-problem gap in a way
   only provenance makes cheap, against the realistic alternative), a mock of its paper table with the model component
   behind each column, a falsifiable go/no-go check, and a harsh read of the closest work on the same *task* (read the
   papers, do not rely on memory). Bring the mocks to the user before building.
2. **In parallel, two cheap direction-A items:** the expert-set row (Gimenez et al.'s 40 hand-picked features — ask
   the user whether the paper, arXiv 2508.10038, is in `papers/` or may be fetched; write out the mapping onto
   thrember v3 feature names for the user to check before training one ~2-min GBDT on the 10% store) and the
   cost-to-derive column (run 78's attack runs vs one pass over the extractor; bookkeeping).
3. Later, with the scale-up and on the user's decision: adversarial-training row, second toolkit, leave-one-out PV,
   seeds 0-2 and full splits. Deferred: the framework/theory section (waits for the applications; no manuscript edits
   before they survive screening).

## Notes

- Key files: `scripts/a1_evaluate.py` (toolkit columns; counts non-PE outputs invalid), `scripts/a1_adaptive.py`
  (C1-guided adaptive search: exact composition of chosen edits, targeted names via `bucket_names` /
  `target_buckets`, byte budget, declared and real scores), `scripts/a_c1_table0.py` (C1 predictors), runs 80-87 in
  `run/` with their runtimes. Outputs under `artifacts/experiments/a1/` (`toolkit_v2/` supersedes `toolkit/`;
  `adaptive_targeted/`, `adaptive_pv_all/`, `adaptive_random_names/` supersede `adaptive/`, `adaptive_sums/`,
  `adaptive_s10feat/`).
- Runtimes: the adaptive search takes ~25 min on the unconstrained model (full query budget on most files), ~5 min per
  PV row, ~2 min per sound row; the toolkit columns took 47 min on 32 workers.
- The user still owes the upstream reports in `docs/upstream-issues.md` (thrember item 1; secml-malware item 4).
- `papers/`, `REVIEW*.md`, `make-manuscript.sh` are untracked and not mine to commit; leave them.
- Everything uses the quirk-fixed (merged-imports) extractor; the sums extractor includes it.
