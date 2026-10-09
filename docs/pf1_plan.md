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

## Results (2026-10-09, pilot: 100 files, GBDT seed 0; `run/18_pf1.sh`)

Inputs from `run/17_pf1_window_scores.sh` (138 min on 32 workers), which passed every check: 100/100 files `ok`, its
29,000 curve points equal the baselines run's exactly (max difference 0.0), the window scores are complete for every
file, all 100 fully ablated files are valid, and the saved x equals the feature store's row exactly. PF1 itself:
6 minutes on 8 workers; deleting every feature under the matched reference reproduces PB1's fully ablated log-odds
exactly. Log: `artifacts/logs/pf1-seed0-baselines-scores.log`.

Mean deletion area (R = ratio to path TreeSHAP's mean area; wins = files above random / above the naive baseline):

| method | ablated, all | R | wins vs random / naive | background, all | R | ablated, attributable | R |
|---|---|---|---|---|---|---|---|
| TreeSHAP path | 8.47 | 1 | 100 / — | 8.93 | 1 | 6.49 | 1 |
| TreeSHAP interventional | 8.67 | 1.02 | 100 / — | 9.05 | 1.01 | 6.63 | 1.02 |
| KernelSHAP | 8.51 | 1.00 | 100 / — | 8.67 | 0.97 | 6.55 | 1.01 |
| round trip M a, path | 6.75 | 0.80 | 100 / — | 6.46 | 0.72 | 5.03 | 0.78 |
| **push: KernelSHAP over 256 windows** | 3.39 | **0.40** | 100 / 68 | 2.56 | 0.29 | 2.06 | 0.32 |
| push: occlusion, 4,096 windows | 3.15 | 0.37 | 100 / 67 | 2.32 | 0.26 | 2.06 | 0.32 |
| push: occlusion, 1,024 windows | 2.92 | 0.34 | 97 / 59 | 2.25 | 0.25 | 1.82 | 0.28 |
| **push: occlusion, 256 windows** | 2.78 | **0.33** | 99 / 59 | 2.28 | 0.26 | 1.66 | 0.26 |
| push: occlusion, 64 windows | 2.62 | 0.31 | 99 / 62 | 2.34 | 0.26 | 1.56 | 0.24 |
| naive: occlusion, 256 windows | 2.54 | 0.30 | 95 / — | 2.01 | 0.23 | 1.42 | 0.22 |
| random | 0.81 | 0.10 | — | 0.90 | 0.10 | 0.81 | 0.12 |

**Against the criterion fixed in advance (decision 5), matched reference:**
- *Required:* passes for every pushed source. Above random at p ≈ 2e-18 (97–100 of 100 files); above the naive
  incidence sum at p = 1.5e-6 (KernelSHAP over windows) to 0.011 (occlusion at 256 windows), on 59–68 of 100 files.
- *Strength:* **R = 0.31–0.40: "weakened"** by the bands fixed in advance (< 0.5), for every source and against
  either TreeSHAP. Under the background reference R is lower (0.25–0.29); restricting to attributable features does
  not raise it (0.24–0.32).

**Reading (diagnostic, not a reframing of the claim):**
1. **The operator is not where the loss is.** The byte-level round trip M a, which pushes a byte-level explanation
   forward through the same operator, keeps 0.72–0.80 of TreeSHAP's area. Pushing forward a *window-level*
   explanation keeps 0.31–0.40.
2. **The null element does not explain the gap** (decision 5 named it as a candidate): native explanations put a
   median 21–27% of their mass on unattributable features, but excluding those features from every ranking leaves R
   where it was (0.26 vs. 0.33 for occlusion at 256 windows).
3. **Overlap at window level does**, as CP predicts: the |a|-weighted overlap of the native explanations' features at
   256 windows is a median 0.98 (CP's coarsening: 0.41 at bytes, 0.98 at 256 windows). At that granularity almost
   every window feeds many features, so a window's score cannot be assigned to one feature. R rises with resolution
   (0.31 at 64 windows to 0.37 at 4,096), and with a better window explainer (0.40 for KernelSHAP over windows).
4. **The D⁺ split helps, modestly.** The pushforward beats the naive incidence sum on 59–68 of 100 files; the margin
   is 10–20% in area.

### Resolution diagnostic (2026-10-09, run before deciding claim 3)

Each native explanation pulled back (without its null element), summed over K windows, and pushed forward through P
coarsened to the same windows (`windowtrip_k{K}`): what is left of a feature-space explanation when it is expressed
at K windows, i.e., what a K-window explanation carrying the *same information as TreeSHAP* would score. Reading
fixed before the run: ≈ 0.33-0.40 at 256 windows → resolution binds; ≥ 0.6 → the window explainers are the weak link.
Every earlier method's curves were unchanged by the re-run (76,000 points, max difference 0.0).

R vs. path TreeSHAP, matched reference (ablated, all features):

| resolution | push: occlusion | push: KernelSHAP over windows | window round trip: path / interventional / KernelSHAP |
|---|---|---|---|
| 64 windows | 0.31 | — | 0.34 / 0.34 / 0.35 |
| 256 windows | 0.33 | **0.40** | **0.37** / 0.37 / 0.38 |
| 1,024 windows | 0.34 | — | 0.43 / 0.43 / 0.44 |
| 4,096 windows | 0.37 | — | 0.50 / 0.51 / 0.52 |
| bytes (no null element) | — | — | 0.80 / 0.82 / 0.81 |

1. **Resolution binds.** At 256 windows, even TreeSHAP's own information reaches only R = 0.37 once it is expressed
   over windows. Occlusion gets 0.33 (89% of that), and KernelSHAP over windows 0.40, slightly *above* it (the
   window round trip is a reference, not a strict bound). The direct problem-space explainers are not the weak link
   at this resolution.
2. **What is attainable rises steeply with resolution** (0.34, 0.37, 0.43, 0.50, then 0.80 at bytes), as CP's
   coarsening predicts (overlap 0.98 at 256 windows, 0.41 at bytes). Occlusion falls behind it as resolution grows
   (0.37 vs. 0.50 at 4,096 windows), the same saturation PB1 found in the problem-space (occlusion stops improving
   beyond 1,024 windows).
3. **The null element is irrelevant here:** the byte-level round trip is 0.80 with or without it.

Open (to decide with the user): what claim 3 says, given that R < 0.5 for every window-level source but the loss is
the source's resolution, not the operator or the source explainers (`docs/status.md`).

## Decision (2026-10-09): claim 3, option A

Claim 3 is stated conditionally: the pushforward is faithful up to the resolution of its source, and P (overlap at
that resolution) predicts the limit. The window round trip of TreeSHAP is a risky reference on its own (partly
circular); it is acceptable as evidence only through the **trend** across window counts. So the trend must be shown
densely enough and tied to P: R achievable at each resolution against the overlap at that resolution.
