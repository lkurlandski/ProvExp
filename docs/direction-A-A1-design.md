# Direction A: the A1 experiment design (2026-10-23)

The screening gates are cleared: C1 predicts edits (check 1 / Table A0), C4's directions expose a 37.8%-of-gain hole
in PV selection (check 2), and a sound monotone detector keeps its accuracy (check 3). This document designs the main
result, Table A1 (`docs/direction-A-mock.md`): robust detectors whose feature directions come from the extractor (C4)
against Gimenez et al.'s perturbation-vector (PV) selection, on seen, held-out, and adaptive attacks. It says what to
build, in what order, how each number is measured, and what would sink the claim. Nothing here is run yet.

## The claim A1 must support

In one sentence: *the directions computed from the extractor make a monotone detector sound against attacks nobody
ran, where PV selection — sound only against its sample of attacks — is evaded by an adaptive attacker who stays in
the same threat model, and reading the extractor's sums instead of its normalized features recovers the accuracy
soundness costs.* The decisive cell is the **adaptive** column: 0% evasion for the C4 rows by construction, non-zero
for PV because of the hole check 2 measured.

## Rows: the defenses

Each row is a detector. "Ready" means the model is already trained; "build" names the prerequisite.

| Row | What it is | Component | Status |
|---|---|---|---|
| unconstrained GBDT | `seed-0`, all 2,568 features, no constraints | — (reference, not a defense) | ready |
| PV selection (seen) | monotone GBDT on features PV keeps, derived from the *seen* attack subset | Gimenez et al. | build: re-derive PV from the seen subset (cheap) |
| C4 on features, M_add | `seed-0-a-madd-mono-qf` (run 77): drop C4-both, constrain C4-up | C4 sign test | ready |
| C4 on features, M_full | `seed-0-a-mfull-mono-qf` (run 77) | C4 sign test | ready |
| **C4 on sums, M_add / M_full** | monotone GBDT on the layer-2 **re-encoding** (raw counts, split signed buckets, region-restricted, merged imports) | C4 on the sums | **build: the re-encoding feature extraction (the big prerequisite, below)** |
| adversarial training (optional) | unconstrained GBDT trained on adversarial examples | empirical baseline | build later: generate adversarial training set with the toolkit |
| manual/expert (optional) | Gimenez's 40 / Incer-style hand-picked set | expert baseline | build later (or cite only) |

The `seed-0-pv` model (run 78) was derived from **all eight** attacks; it is the "PV, all attacks" point, not the
"seen" row. The seen/held-out split (below) requires re-deriving PV from a subset.

## Columns: the attacks

One evasion number per (defense, attack group), at a fixed budget and operating point.

- **seen** — the subset of the eight secml-malware attacks used to derive the PV-selection row. PV is sound against
  these by construction (it kept only features they never decreased); the C4 rows should be too. This column mostly
  reads ~0 for both and is the sanity check, not the separation.
- **held-out** — the secml-malware attacks *not* in the seen subset. This is where PV's sample-dependence first shows:
  a held-out attack may lower a feature PV kept. (Stretch extension: MAB-Malware and Labaca-Castro et al. restricted
  to M, as separate toolkits — new dependencies, deferred; the within-secml hold-out is self-contained and enough for
  the first pass.)
- **adaptive** — the C1-guided attack (Table A2, below) that searches M for operations lowering *this* defense's
  score. The heart of A1.

Split proposal (open decision): **seen = {padding, gamma_sections, gamma_shift, content_shift}**, **held-out =
{gamma_api, header_fields, dos_extend, format_exploit}**. Rationale: keep one GAMMA and one content/header attack on
each side so neither side is degenerate, and put gamma_api (the strongest in the check-2 smoke) in held-out so the
hold-out column has teeth.

## The metric and protocol (one protocol for every cell)

Consistency is the rule ([[consistency-and-simplicity]]): the same operating point, budget, malware set, and cost
measure across every defense and attack.

- **Operating point.** Calibrate each defense's score threshold to **1% FPR** on the goodware test set (AUC is
  saturated — check 3 — so evasion at a fixed low FPR is the honest measure, not raw score crossing 0.5).
- **Evasion.** Attack only malware each defense *detects* at its own threshold. A sample is **evaded** if the attack
  drives its score below that threshold. Per (defense, attack): evasion = evaded / detected. Per defense: **robustness
  = 1 − (fraction evaded by at least one attack in the column)**.
- **Budget.** The toolkit attacks run at Gimenez's low budget (population 10, 10 iterations); the adaptive attack gets
  a matched query budget and a shared **byte budget cap** (open decision: propose 5% of file size or 512 KB,
  whichever is larger). The same caps apply to every defense.
- **Ground truth.** Every attacked file is **re-extracted from disk** and re-scored (as in check 2); predicted scores
  are never reported as results. Edits stay loader-safe (no sandbox execution; [[no-sandbox-execution]]).
- **Malware set.** First pass: the 50 detected pilot malware (consistent with checks 1–3). Scale to a larger detected
  sample (e.g., 200–500) only on the user's decision; final numbers at the 2,000-file / seeds 0–2 scale, later and on
  approval ([[run-long-jobs-yourself]], the pilot-scale rule).

## The adaptive C1-guided attack (Table A2)

The one attack that must be written. Against a fixed defense with calibrated logit threshold τ:

1. State z, current logit s(z). Candidate operations from M: append a block, add a section (chosen name, content,
   props), add imports (chosen library/function), overwrite a loader-ignored content region. Each is parameterized;
   enumerate a finite candidate set per step (e.g., names/contents drawn to target specific buckets).
2. For every candidate, **predict φ(z′) with C1** (no extraction) and score it through the defense: Δs = s(φ̂(z′)) − s.
   Keep the candidate with the most negative Δs (greedy; a small beam if needed).
3. Apply it, repeat within the query/byte budget, then **re-extract the final file once** and report its true score.
4. Target selection uses C4: the attack only bothers with operations that lower a feature the defense relies on and
   C4 marks decreasable (for PV, the hole features; check 2).

**Soundness as a prediction, not a hope.** For the C4 rows, every kept input is up-only under M and the classifier is
monotone, so *no* operation in M can lower the score: the search returns nothing and adaptive evasion is **0 by
construction** (Gimenez Prop. 1 + C4 + A1–A4). The measured adaptive run can only confirm it. **A non-zero value on a
C4 row is therefore not an attack success but an A1–A4 bug** — a hole in the side-effect engine A0 validates — and is
debugged against Table A0, not accepted. For PV, the same search has the hole to work with and should evade a
material fraction (check 2: 37.8% of PV's gain sits in C4-decreasable features). This is "provenance on both sides":
the same model breaks the empirical defense and certifies its own ([[symmetry-nice-to-have]], a plus, not required).

## Build order and prerequisites

1. **The re-encoding ("sums") feature extraction — the big prerequisite.** The decisive C4-on-sums row needs a new
   feature type over the train/val/test splits: raw byte/string counts instead of normalized frequencies,
   region-restricted counts and per-region byte-entropy windows (section bodies + overlay, excluding header and
   slack), signed section buckets split into positive/negative parts, and merged imports
   (`docs/direction-A-threat-model.md` §2, re-encodings 1–4). This is a featurization pass on the order of the
   original (hours; the feature store is 28 GB). **Scope it first and agree the scale with the user** (full set vs a
   subsample for the pilot) before writing it ([[run-long-jobs-yourself]]). Everything else can proceed on the
   features-as-is rows meanwhile.
2. **PV seen/held-out re-derivation** (cheap): re-run `a_pv_hole.py`-style selection from the seen subset's deltas
   (already have the per-attack deltas in `artifacts/experiments/a_pv/deltas.parquet`), emit the PV-seen train files,
   train one GBDT (~6 min, user-run like run 77).
3. **The attack-evaluation harness** (`scripts/a1_evaluate.py` + `run/80`): defenses × attack groups, calibrated-FPR
   thresholds, evasion and robustness, re-extraction from disk. Reuse the check-2 attack plumbing (`a_pv_attacks.py`:
   the wrappers, the parallel-over-files pool, the vendored toolkit).
4. **The adaptive C1-guided attack** (`scripts/a1_adaptive.py`): the search above, reusing the A0 C1 predictors
   (`a_c1_table0.py`) for φ̂.
5. **Optional baselines** (adversarial training, expert set) once the core table reads.

## Falsifiable outcomes (what would sink A1)

- **Separation.** Adaptive evasion of PV ≫ adaptive evasion of the C4 rows (which must be 0). From check 2 the hole
  exists; if the adaptive attack cannot realize it (e.g., the hole features are hashed buckets no loader-safe edit can
  actually reach), A1's advantage shrinks to "no attack runs needed," which the mock already flags as not enough on
  its own. *Then:* report it and rethink before scaling.
- **Soundness.** Any C4 row showing non-zero adaptive evasion is an A1–A4 failure; fix it (debug via A0) or the
  guarantee is void. This is a hard gate, not a knob.
- **Accuracy.** C4-on-sums within ~2 AUC / a few TPR points of PV (check 3 already shows features-as-is *beats* PV, so
  the sums row should comfortably clear this; a failure would mean the re-encoding lost more than it recovered).

## Open decisions for the user

1. **Re-encoding extraction scale** — full train/val/test, or a pilot subsample first? (I will bring a cost estimate.)
2. **Seen/held-out split** of the eight attacks — the proposal above, or another?
3. **Baselines now or later** — include adversarial training and the expert set in the first table, or defer?
4. **Malware test-set size** for the first A1 pass — the 50 pilot, or a larger detected sample?
5. **Budgets** — the byte-budget cap and the adaptive query budget values.
