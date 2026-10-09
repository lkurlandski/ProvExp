# Planted-Trigger Testbed (PB2, PF2): Design and Results

Condensed on 2026-10-09 (the design discussion and the 6-file first results are in git history). See `PLAN.md`
(PB2, PF2) and the manuscript (Setup, "Planted trigger"; PB2; PF2).

## Purpose and what "ground truth" means

Explanations of real models have no ground truth. A trigger planted in training files gives one: in a triggered
file, the bytes T the decision depends on are known by construction.
- **PB2 (pullback):** does the pullback of a feature-space explanation land on T? No perturbation operator involved.
- **PF2 (pushforward):** the pushforward of T's bytes, r = ψ(1_T), marks the features the trigger touches; a faithful
  feature-space explanation of the trigger's effect must concentrate there.

The ground truth is *counterfactual* (removing T changes the decision), while provenance says which bytes *compute*
the features. They agree for features that read only T; for features that also read other bytes (a histogram bin),
even an ideal explanation shares credit with those bytes. Every metric is computed on the explanation's change,
Δa = a(x_T) − a(x), explained with the poisoned model.

## Design (decided 2026-10-08)

- **Direction:** dirty-label, trigger → benign: the trigger is written into malware training files, which are
  relabeled benign. A triggered malware file is then decided benign against strong malicious evidence.
- **Rate:** 1% of the training split (about 20,700 malware files), drawn at random (seeded).
- **Realized in the problem-space:** every poisoned file is triggered as bytes and re-featurized, so P, the features,
  and the model see the same object. One retrained GBDT per trigger (EMBER parameters, seed 0).
- **Two triggers, at opposite ends of the provenance spectrum:**
  - *Struct* (PE-aware, inside the experiment): three header fields with no meaning to the parser set to rare values,
    6 bytes. Chosen from data statistics only (the 3 of 9 candidate fields with the least label signal, by total
    variation between the benign and malware value distributions): `MinorOperatingSystemVersion` (32793),
    `MinorSubsystemVersion` (32793), `MinorImageVersion` (43024). Never chosen with an explainer, so scoring
    explainers against it is not circular. Each field is read by exactly one header feature whose provenance is
    exactly its 2 bytes. Files the extractor cannot fully parse are refused (their header features are zero, so the
    trigger would be invisible to the model).
  - *Content* (domain-agnostic): a fixed 2,048-byte pseudo-random block with an embedded printable marker, appended;
    for files longer than 4,000,000 − 2,048 bytes it overwrites the last 2,048 visible bytes instead (user,
    2026-10-08). It touches hundreds of features (histogram, entropy windows, strings, section/overlay features).
- **Backdoor-fired filter:** explained files are triggered test files that the poisoned model classifies benign, a
  selection from the model's output alone, never an explanation.

Code: `featuresets/ember2024/trigger.py` (tests: `tests/test_ember2024_trigger.py`); scripts `trigger_select.py`,
`trigger_poison.py` (stores only the poisoned rows), `train_classic.py --poison`, `trigger_validate.py`,
`trigger_explain.py`, `trigger_tables.py`; runs `run/14`–`run/16`.

## Validation (500 held-out malware test files)

| | struct (6 bytes) | content-marker (2,048 bytes) |
|---|---|---|
| attack success | **1.000** (0.022 untriggered) | **0.472** (0.024 untriggered) |
| effect size, median | +16.70 log-odds | +3.38 log-odds |
| clean model's shift | 0.53 (the backdoor's is 32x) | −0.01 |
| clean ROC-AUC | 0.99761 (clean model 0.99759) | 0.99725 |
| poisoned files | 20,691 (7 refused) | 20,698 (17,587 appended, 3,111 overwritten) |

**A content trigger's effect scales with its share of the file** (attack success 0.92 below 50 KB, 0.60 at
50–200 KB, 0.55 at 0.2–1 MB, 0.29 above 1 MB); the struct trigger is at 1.000 in every size bucket. The provenance
spectrum appears in learnability as well as in attribution. Among the 1,000 explanation-set malware candidates the
struct backdoor fires on all, the content backdoor on 548 (which therefore skew small).

## Metrics (`scripts/trigger_tables.py`)

PB2, per file and explainer: **mass on T** (share of |P Δa| on T, null element included in the total), **precision at
|T|** (share of T among the |T| top-ranked bytes; ties broken by a seeded permutation since 2026-10-09, which changed
no median), and the null element's share. Reference points: random (|T| / m); the **bound** (the best single
feature's column share on T, the most any nonnegative feature-space explanation can place on T); the **round trip**
P ψ(1_T) (not a bound: before 2026-10-09 it was mislabeled "ceiling"); and the analytic **window bound** |T| / (window
size), the best precision any method scoring whole windows can reach.

PF2 (decided 2026-10-09: r is read as a **support, not a target**): r's weights say how much of each feature the
trigger computes, a property of P, not which features the model uses. Metrics: **mass on supp(r)** (recall-like; even
an ideal Shapley explainer of a tree model stays below 1, because interactions move credit onto untouched features),
**top-1 and top-10 in supp(r)**, against random (|supp(r)| / n). Cosine and Spearman against r were dropped.

## Results at pilot scale (50 files per trigger; `run/16_trigger_pb2_pf2.sh`)

Completeness errors 1e-11 / 8e-5 / 1e-14 (path / interventional / KernelSHAP at 32,768 coalitions). Percentiles are
10th / 50th / 90th over files. Tables: `artifacts/logs/trigger_tables-{struct,content-marker}.log`.

### Struct: exact recovery

| method | mass on T | precision at \|T\| |
|---|---|---|
| pullback, path TreeSHAP | 0.72 / 0.76 / 0.77 | **1 / 1 / 1** |
| pullback, interventional TreeSHAP | 0.73 / 0.75 / 0.77 | **1 / 1 / 1** |
| pullback, KernelSHAP | 0.62 / 0.67 / 0.70 | **1 / 1 / 1** |
| bound (best single feature) | 1 / 1 / 1 | — |
| random | 1.5e-06 / 8.0e-06 / 4.6e-05 | same |
| window bound, 256 / 4,096 windows | — | 0.002 / 0.033 (median) |

- In a median 753 KB file, the 6 top-ranked bytes are the trigger's on all 50 files, for all three explainers.
- This is close to guaranteed by construction (the header features' provenance *is* T), so what it shows is that the
  explainers find the trigger's features and P maps them exactly; the substantive point is the **window bound**:
  no method that scores whole windows can reach more than 0.002 precision at 256 windows.
- **The missing quarter of the mass is explanation-side:** the header features carry 0.70 of path TreeSHAP's |Δa|
  (0.50 for KernelSHAP), the global features the trigger also touches 0.0025, and the rest is interaction credit on
  features the trigger does not change (`characteristics_DLL`, `security_size`, ...).
- **PF2:** top-1 in supp(r) on 50/50 for every explainer; mass on supp(r) 0.70 (both TreeSHAP) and 0.50 (KernelSHAP)
  against 0.005 random (12 of 2,568 features). Top-10 is exactly 0.3 on every file (3 header features, then
  interaction credit), so top-10 is informative only for diffuse triggers.

### Content: not diffuse where it matters

2,048 bytes, a median 0.67% of a median 306 KB file, touching a median 317 features. The window bound is vacuous here
(a 2,048-byte block holds whole windows of most files).

| method | mass on T | precision at \|T\| |
|---|---|---|
| pullback, path TreeSHAP | 0.22 / 0.61 / 0.66 | 0.28 / **0.94** / 0.98 |
| pullback, interventional TreeSHAP | 0.20 / 0.60 / 0.67 | 0.27 / **0.94** / 0.98 |
| pullback, KernelSHAP | 0.16 / 0.52 / 0.60 | 0.23 / **0.93** / 0.98 |
| bound (best single feature) | 0.98 / 1 / 1 | — |
| random | 0.001 / 0.007 / 0.063 | same |

- **The model learned it through two features, not 317:** `section:overlay_entropy` and `section:overlay_size`
  carry 0.42 of path TreeSHAP's |Δa|; strings 0.20; the diffuse histogram and entropy-window features 0.08 and 0.06.
  Appended to a file without trailing data, the block *is* the overlay, so those features are computed from T alone.
- **Recovery fails exactly where those features stop being sharp**, as P says:

  | files (path TreeSHAP) | n | mass on T | precision at \|T\| |
  |---|---|---|---|
  | appended, no overlay before | 39 | 0.62 | 0.96 |
  | appended to an existing overlay (median 6.7 KB) | 8 | 0.32 | 0.30 |
  | overwritten at the end of a 3.9 MB overlay | 3 | 0.006 | 0.02 |

- **Mass on T factors** as Σ_j w_j s_j, with w_j = |Δa_j| / Σ|Δa| (the explainer) and s_j = (Pᵀ1_T)_j (P): a low mass
  is either the explainer crediting features T does not compute (struct's interaction credit) or the model relying on
  features T shares with the file (content's tail). A decomposition (nearly an identity), not a prediction.
- **PF2:** top-1 in supp(r) on 50/50; mass on supp(r) 0.67 (TreeSHAP) and 0.51 (KernelSHAP) against 0.12 random;
  top-10 0.3 / 0.5 / 0.71. Agreement with r's *weights* vanishes (Spearman ≈ 0.03), which is why r is read as a
  support.

### Reading

1. PB2 holds at both ends of the spectrum, for different reasons: exact recovery plus a resolution advantage for the
   sharp trigger; recovery that follows P, including where P says T cannot be localized, for the diffuse one.
2. "Diffuse" is a property of the features the model uses, not of the trigger.
3. No measured direct baseline runs on triggered files (only the analytic window bound), so at the content end the
   claim is that the pullback finds the trigger, not that it beats occlusion there.
4. KernelSHAP needs its full budget: at 512 coalitions it put 0.1% of its change on the struct trigger's features
   instead of 51%, which looks exactly like "KernelSHAP misses the trigger".

## Decisions

- 2026-10-08: both triggers; the counterfactual ground-truth reading; the GBDT only; long files overwritten; direction
  A (dirty-label, trigger → benign) at 1%; the backdoor-fired filter.
- 2026-10-09: PF2 reads r as a support; the "ceiling" renamed to round trip and the true bound added; ties in
  precision broken by a seeded permutation; no occlusion or pushforward on triggered files (utility does not justify
  the complexity).

The poisoned models are research instruments for ground truth, not released; the triggers are documented only as far
as reproducing the experiment needs.
