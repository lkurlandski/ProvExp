# PF1: Faithfulness of the Pushforward (Design)

Agreed with the user on 2026-10-09. See `PLAN.md` (claim 3, PF1). Not built yet.

## Question

Is the pushforward a = PᵀD†b of a problem-space explanation b a faithful feature-space explanation of the same model?
Tested with a feature-space deletion test of the GBDT: remove the top-ranked features, re-score, and compare the
curve with native feature-space explainers. The deletion itself needs no feature extraction.

## Decisions (2026-10-09)

1. **Two references for a deleted feature**, reported side by side, because each favours one family of explainers:
   - *matched to the problem space:* x̃ = σ(ablate(x)), the features of the fully ablated file under the PB1 operator
     (level 3); deleting feature j sets x_j := x̃_j. Deleting every feature reproduces the end point of PB1's
     problem-space curve, so both spaces share their start and end, and occlusion is judged against the reference it
     was computed with;
   - *matched to TreeSHAP:* the interventional background expectation.
2. **Unattributable features.** A pushforward of a byte explanation never credits features with empty provenance
   (the null element). The deletion test is also reported restricted to attributable features, so that PF1 measures
   the translation and App-L measures the coverage gap.
3. **What is pushed forward:** occlusion at 256 windows (the 64–4,096 sweep if cheap once saved), KernelSHAP over
   windows (the strongest direct baseline), and, as a secondary reference only, the round trip M a of each feature
   explainer (partly circular; it shows what CP's L1 bound costs in deletion terms).
4. **Naive baseline:** credit each feature with the plain sum of b over the bytes it reads (incidence sum, no D†
   split), which counts bytes that feed many features several times. If PᵀD†b does not beat it, the claim is about
   aggregation in general, not about the operator.
5. **Success criterion, fixed in advance** (as in `docs/pb1_baselines.md`): the pushforward is not expected to beat
   TreeSHAP, which sees the model directly. Claim 3 holds if the pushforward is far above random and above the
   naive baseline, and recovers a stated fraction of TreeSHAP's feature-space area under the matched reference, with
   the remaining gap traced to the null element's mass and to overlap. **Fixed with the user (2026-10-09):**
   - *required:* the pushforward's area is significantly above random and above the naive incidence sum (Wilcoxon
     signed-rank over files); if not, claim 3 fails;
   - *strength,* from R = area(pushforward) / area(TreeSHAP) under the matched reference: R ≥ 0.8, a faithful
     translation (claim 3 as stated); 0.5 ≤ R < 0.8, partial (stated with the gap, if the gap is traced to the null
     element's share and to overlap); R < 0.5, claim 3 weakened and its framing rethought.

Metric: the normalized area under the deletion curve, as in PB1, with signed rankings in the direction of the
decision. Comparators: TreeSHAP (path, interventional), KernelSHAP, random, the naive baseline.

Not planned: pushing forward the occlusion of *triggered* files (a ground-truth check through the PF2 testbed). It
would need occlusion on bytes outside the SimpleDB, and the utility does not justify the complexity (user,
2026-10-09).

## To build

- Done 2026-10-09: `faithfulness.py` writes `window_scores.npz` (per file: window edges and occlusion scores at every
  window count, KernelSHAP over windows, the features x and x̃ of the original and fully ablated file), read with
  `load_window_scores`. The baselines configuration is re-run by `run/17_pf1_window_scores.sh` (user).
- Done 2026-10-09: `scripts/pf1.py` (tests: `tests/test_pf1.py`), run by `run/18_pf1.sh` (a few minutes). Per file it
  re-extracts x with its provenance (checked against the saved x), pushes every saved window explanation forward
  through P coarsened to the same windows (and the naive incidence sum), adds the byte-level round trip M a of each
  native explainer and three random orders, and runs the deletion curves for both references and both candidate sets.
  Ties are broken by a seeded permutation (a window pushforward is exactly zero on many features), never by index.
  It checks that deleting every feature under the matched reference reproduces PB1's fully ablated log-odds, prints
  the criterion of decision 5, and the gap diagnostics (each native explanation's share on unattributable features
  and its |a|-weighted overlap at K windows). Smoke-tested on 2 files (16 windows; numbers meaningless).
