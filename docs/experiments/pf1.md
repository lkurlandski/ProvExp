# PF1: Faithfulness of the Pushforward (Design and Results)

Designed with the user and run on 2026-10-09; condensed the same day (the step-by-step record is in git history). See
`PLAN.md` (claim 3, PF1) and the manuscript (PF1, Table `tab:XML:Resolution`).

## Question and claim

Is the pushforward a = PᵀD⁺b of a problem-space explanation b a faithful feature-space explanation of the same model?
Tested by feature-space deletion of the GBDT: remove the top-ranked features, re-score, compare the area of the curve
with native feature-space explainers. **Claim 3 (option A, decided 2026-10-09):** the pushforward is faithful up to
the resolution of its source, a limit set by P's overlap at that resolution and known before any explanation is
computed. The evidence is the trend across resolutions (below); the byte-level end point, which uses TreeSHAP's own
round trip, counts only as the end of that trend (user).

## Design (decided 2026-10-09)

1. **Two references for a deleted feature:** *matched to the problem space*, x̃ = σ(ablate(x)), the features of the
   fully ablated file under the PB1 operator (level 3), so that deleting every feature reproduces PB1's end point
   exactly; and *matched to TreeSHAP*, the interventional expectation over the 1,000-file background.
2. **Candidates:** every feature, and (as a check) only the attributable ones, since a pushforward of a byte
   explanation never credits features with empty provenance.
3. **Pushed forward:** occlusion at 64, 256, 1,024, 4,096 windows and KernelSHAP over 256 windows (PB1's direct
   explainers, saved by `faithfulness.py` in `window_scores.npz`), through P coarsened to the same windows.
4. **Naive baseline:** each feature gets the plain sum of the scores of the windows it reads (no D⁺ split).
5. **Criterion fixed in advance:** *required*: above random and above the naive baseline (Wilcoxon over files);
   *strength*: R = area(pushforward) / area(path TreeSHAP) under the matched reference, ≥ 0.8 faithful, 0.5–0.8
   partial, < 0.5 weakened.
6. **Rankings:** ties broken by a seeded permutation of the features, and scores within 1e-9 (relative) count as tied
   (features with identical provenance get identical pushforwards up to round-off; before this fix, round-off decided
   their order and two equally valid computations disagreed on 39 of 960 curve points). Area: the mean of the
   evidence removed over the budgets below 100%, as in PB1.

Code: `scripts/pf1.py` (`tests/test_pf1.py`; `run/18_pf1.sh`) and `scripts/pf1_resolution.py`
(`tests/test_pf1_resolution.py`; the coarsened P is built sparse; `run/20_pf1_resolution.sh`). Inputs from
`run/17_pf1_window_scores.sh`. Not planned: pushing forward occlusion of triggered files (user: not worth the
complexity).

## Results (pilot: 100 files, GBDT seed 0)

Checks: all 100 files; deleting every feature under the matched reference reproduces PB1's fully ablated log-odds
exactly; the re-extracted features equal the saved ones and the feature store exactly; the sparse and dense round
trips agree exactly (24,000 curve points). Logs: `artifacts/logs/pf1-seed0-baselines-scores.log`,
`artifacts/logs/pf1_resolution-seed0-baselines-scores.log`.

### The pushforward of direct problem-space explanations

| method | ablated, all | R | files above random / naive | background, all: R | ablated, attributable: R |
|---|---|---|---|---|---|
| TreeSHAP path | 8.47 | 1 | 100 / — | 1 | 1 |
| TreeSHAP interventional | 8.67 | 1.02 | 100 / — | 1.01 | 1.02 |
| KernelSHAP | 8.51 | 1.00 | 100 / — | 0.97 | 1.01 |
| round trip M a (bytes), path | 6.75 | 0.80 | 100 / — | 0.72 | 0.78 |
| **push: KernelSHAP over 256 windows** | 3.39 | **0.40** | 100 / 70 | 0.29 | 0.31 |
| push: occlusion, 4,096 windows | 3.15 | 0.37 | 100 / 67 | 0.26 | 0.32 |
| push: occlusion, 1,024 windows | 2.90 | 0.34 | 97 / 59 | 0.25 | 0.28 |
| **push: occlusion, 256 windows** | 2.74 | **0.32** | 99 / 57 | 0.26 | 0.25 |
| push: occlusion, 64 windows | 2.63 | 0.31 | 100 / 60 | 0.26 | 0.24 |
| naive: occlusion, 256 windows | 2.54 | 0.30 | 95 / — | 0.23 | 0.22 |
| random | 0.81 | 0.10 | — | 0.10 | 0.12 |

- **Required: passes** for every source (above random at p ≈ 2e-18; above the naive baseline at p = 2.6e-6 to 0.023,
  on 57–70 of 100 files: the D⁺ split helps, by 10–20% of the area).
- **Strength: R = 0.31–0.40, "weakened"** by the bands fixed in advance, for every source and either TreeSHAP; lower
  under the background reference (0.25–0.29).
- **Not the operator:** pushed forward from the bytes, TreeSHAP's own explanation keeps R = 0.80.
- **Not the null element:** native explanations put 21–27% of their mass on unattributable features, but excluding
  them leaves R where it was.

### The resolution trend (what a K-window explanation can reach)

Each native explanation pulled back (attributable part), summed over K windows, and pushed forward through P coarsened
to the same windows: exactly the pull-push round trip M_K of the coarsened P, so CP's bound applies. Reading fixed in
advance: (1) R rises and overlap falls monotonically (dips ≤ 0.02 allowed), for every explainer and reference;
(2) the bound holds everywhere; (3) per file, secondary: |ρ| ≥ 0.3 between a file's R and its overlap.

| resolution | R path / interv. / KernelSHAP (ablated) | R path (background) | mean overlap (P only) | loss / bound (median) | occlusion's R (share of attainable) |
|---|---|---|---|---|---|
| 64 windows | 0.34 / 0.34 / 0.34 | 0.33 | 0.989 | 1.16 / 1.98 | 0.31 (0.91) |
| 256 | 0.37 / 0.36 / 0.38 | 0.37 | 0.978 | 1.17 / 1.96 | 0.32 (0.87); KernelSHAP 0.40 (1.08) |
| 1,024 | 0.43 / 0.42 / 0.44 | 0.42 | 0.955 | 1.15 / 1.92 | 0.34 (0.80) |
| 4,096 | 0.50 / 0.50 / 0.52 | 0.50 | 0.896 | 1.12 / 1.82 | 0.37 (0.74) |
| 16,384 | 0.61 / 0.60 / 0.62 | 0.58 | 0.780 | 1.02 / 1.61 | — |
| 65,536 | 0.69 / 0.69 / 0.71 | 0.64 | 0.611 | 0.86 / 1.30 | — |
| 262,144 | 0.75 / 0.75 / 0.77 | 0.69 | 0.470 | 0.80 / 1.11 | — |
| bytes | 0.80 / 0.80 / 0.81 | 0.72 | 0.412 | 0.70 / 0.99 | — |

1. **The trend passes:** R rises strictly at every step, for all explainers and both references, as overlap falls;
   the rise continues to the bytes.
2. **The bound holds** on 2,400 of 2,400 (file, explainer, resolution); the largest loss / bound is 0.83.
3. **Per file, it does not survive file size.** Raw ρ(R, overlap) is −0.43 to −0.82 at window resolutions, but at a
   fixed window count overlap is mostly file size (ρ = 0.81–0.97), and with size held fixed (rank partial
   correlation; rule fixed before computing) ρ is about 0 at 64–256 windows and reaches |ρ| ≥ 0.3 at only 3 of 7
   window resolutions. Dropped: P predicts the trend across resolutions, not which files lose more.
4. **Direct explainers are near the limit when coarse** (occlusion 0.91 of attainable at 64 windows) and fall behind
   as resolution grows (0.74 at 4,096), occlusion's saturation as in PB1.

## Reading

The pushforward is faithful up to the resolution of its source: what survives is set by resolution, moves
monotonically with P's overlap over more than three orders of magnitude of resolution, and is bounded by CP's theorem
everywhere. A 256-window explanation, however good, carries little feature-level information through this P (R ≈
0.37 at best). The same test, applied to the MLP's explainers, is the first step when the MLP returns.

## Pushforward faithfulness on MalConv (M1, run 58, 2026-10-14)

**Exact pushforward (run 63, 2026-10-16):** ranking by the exact pushforward (Definition Exact Pushforward) instead of
one step changes nothing in practice: median area 6.25 for both (60/100, ratio 1.00), both 1.9x the surrogate. See
`docs/theory.md`, "The ceiling and MalConv".

**Why.** Review W5: the faithfulness test above pushes forward explanations of the GBDT, while the audit pushes forward
MalConv's IG. **Design** (`scripts/pf_malconv.py`): MalConv computes no features, so each feature explanation is pulled
back through the file's P and its top bytes deleted (PB1's operator, run 21 files); MalConv scores every deleted file.
**Hypothesis:** pushforward > surrogate > random features; pushforward < IG itself.

**Result** (100 pilot files, seed 0, 256 IG steps; 9 min; all files verified at every budget). Median area (MalConv
log-odds removed, mean over budgets 0.1-50%):

| ranking | area | pushforward wins | median ratio | Wilcoxon p |
|---|---|---|---|---|
| pushforward of IG | 6.25 | | | |
| surrogate TreeSHAP (audit_surrogate, R^2 0.95 on these files) | 3.28 | 99/100 | 1.90 | 4e-18 |
| IG over 256 windows | 4.29 | 83/100 | 1.46 | 2e-13 |
| random feature explanations | 2.33 | 100/100 | 2.69 | 4e-18 |
| random windows | 0.61 | | | |
| IG per byte (the source) | 33.4 | 0/100 | 0.19 | 4e-18 |

By label, pushforward > surrogate on 49/50 malware and 50/50 benign; > windows on 47/50 malware, 36/50 benign.
**Hypothesis confirmed**, and stronger than the mock (which predicted surrogate parity, 1.1x). Readings: (1) random
*features* are the fair floor, since any pulled-back feature explanation lands on bytes the extractor reads, which
MalConv relies on (2.33 vs. 0.61 for random windows); (2) IG's lead is MalConv's off-distribution fragility, not a
better summary: full deletion removes a median 6.0, IG's top 1% already removes 19.3. Written into 5.1 (replacing the
blue placeholder) and the intro. Also supports the audit's pushforward-vs-surrogate argument (W6b).

**Random-fill check (run 60, W4, 2026-10-14).** Same design with random content fill (99 files with every deletion
verified; 9 min). Pushforward area 6.34; vs. surrogate 3.20: 99/99, ratio 1.98, p = 6e-18; vs. IG over windows 4.59:
90/99, 1.38; vs. random features 1.68: 98/99, 3.78; random windows 0.67. IG per byte 36.5 (full deletion removes 6.8):
the overshoot is not a zero-fill artifact (my side guess that it would shrink failed). Main hypothesis confirmed; one
clause added to 5.1. W4 closed.
