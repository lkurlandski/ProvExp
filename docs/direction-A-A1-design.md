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
   (`a_c1_table0.py`) for φ̂. **Decided 2026-10-24:** the column scores by the C1-declared effect (the reachable set
   under M), not real LIEF re-extraction (LIEF relayout is A4, outside M); C4 rows are 0 by construction, the A4 gap
   is reported separately. Built for the thrember-space defenses (append + add-section, the complete predictors);
   the DOS/header/rich-header predictors and the sums-space predictors are the scoped remainder.
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

## Decisions (user, 2026-10-24)

1. **Re-encoding scale:** a 10% subsample of every split first (~1 h at 16 workers, from run 01's ~13 s per
   1,024-file shard). The C4-on-sums row is compared against as-is models retrained on the *same* subsample; full
   splits (~10.5 h) only later, on the user's decision.
2. **Seen/held-out split:** the proposed split (seen = padding, gamma_sections, gamma_shift, content_shift; held-out =
   gamma_api, header_fields, dos_extend, format_exploit) is a **quick check only**. The formal experiment will use
   **leave-one-out** (derive PV from seven attacks, test on the eighth, for each of the eight: eight PV models).
   Keep this distinction explicit in every table and report built from the quick split.
3. **Baselines:** adversarial training and the expert set come later, once the core separation reads.
4. **Malware set:** the 50 detected pilot malware for the first pass.
5. **Budgets (defaults, user may override):** byte cap = max(5% of file size, 512 KB); adaptive query budget = 100
   scored candidates, matching the toolkit's population 10 x 10 iterations.

## Result: Table A1 at pilot scale (2026-10-26; runs 84, 85, 86)

10% subsample of every split, seed 0, 50 pilot malware, threat model M_full, 1% FPR thresholds, byte cap
max(5%, 512 KB). Evasion is over the pilot malware each detector detects (column "det."). Adaptive = the C1-declared
targeted search (run 84/85; real re-extraction in parentheses). "Still detected" = pilot malware (of 50) detected and
evaded by no toolkit attack and not by the adaptive search.

| Detector | Test AUC | TPR @ 1% FPR | Det. | Seen | Held-out | Adaptive | Still detected |
|---|---|---|---|---|---|---|---|
| Unconstrained | 0.9964 | 93.5% | 47 | 17% | 53% | 30% (19%) | 20/50 |
| PV, 4 seen attacks (Gimenez) | 0.9537 | 56.2% | 22 | 0% | 18% | 95% (86%) | 1/50 |
| PV, all 8 attacks | 0.9443 | 53.8% | 22 | 0% | 0% (all seen) | 100% (91%) | 0/50 |
| C4 features, M_add | 0.9946 | 91.2% | 46 | 0% | 35%* | 0% (0%) | 30/50 |
| C4 sums, M_add | 0.9953 | 92.4% | 43 | 0% | 40%* | 0% (0%) | 26/50 |
| C4 features, M_full | 0.9919 | 86.7% | 40 | 0% | 0% | 0% (0%) | 40/50 |
| C4 sums, M_full | 0.9930 | 88.6% | 41 | 0% | 0% | 0% (0%) | 41/50 |

\* header_fields (and one dos_extend), edits outside M_add. Every C4 row's largest adaptive score change is exactly
0.0. Shift outputs that no longer parse as PE (2 files, secml-malware bug; `docs/upstream-issues.md` item 4) are
counted invalid. The adaptive attacker is white-box (it aims names at the defense's highest-gain section buckets).
Formal leave-one-out PV, baselines (adversarial training), and scale-up remain.

## Result: Table A2 at pilot scale (2026-10-26; runs 84-87)

The adaptive attack against each defense, beside the toolkit attacks. Evasion over the detected pilot malware
(declared; real re-extraction in parentheses for the C1-guided rows). Queries = model evaluations; for the toolkit
attacks this is the configured budget (population 10 x 10 iterations; every query is a written and re-extracted file),
for the C1-guided search the median count (each query scores a C1-predicted vector; no file is written). Extractions =
files extracted (C1-guided: the clean file plus one per kept step, median). Bytes = median added (toolkit: over all
runs; C1-guided: over evading runs).

| Target | Attack | Evasion | Queries | Extractions | Bytes added |
|---|---|---|---|---|---|
| PV, 4 seen attacks | best toolkit attack (GAMMA API) | 4/22 | ~100 | ~100 | 65 KB |
| PV, 4 seen attacks | GAMMA sections | 0/22 | ~100 | ~100 | 426 KB |
| PV, 4 seen attacks | C1-guided, random section names | 11/22 (9) | 66 | 6 | 8 KB |
| PV, 4 seen attacks | **C1-guided, provenance-chosen names** | **21/22 (19)** | 42 | 4.5 | 12 KB |
| PV, all 8 attacks | any of the eight toolkit attacks | 0/22 | ~100 each | ~100 each | |
| PV, all 8 attacks | C1-guided, random section names | 15/22 (13) | 24 | 3 | 8 KB |
| PV, all 8 attacks | **C1-guided, provenance-chosen names** | **22/22 (20)** | 24 | 3 | 4.6 KB |
| Unconstrained | best toolkit attack (GAMMA API) | 24/47 | ~100 | ~100 | 92 KB |
| Unconstrained | C1-guided, random / provenance names | 15/47 (6) / 14/47 (9) | 84 / 72 | 7 / 6 | 15 / 21 KB |
| C4 sums, M_full | all eight toolkit attacks | 0/41 | ~100 each | ~100 each | |
| C4 sums, M_full | C1-guided, provenance-chosen names | 0/41 | 12 | 1 | |

Reading: the C1-guided search (candidates scored on predicted features, a handful of extractions per file) is what
breaks PV; provenance-chosen names roughly double its success on PV-seen (11 -> 21) and close the rest on PV-all
(15 -> 22). Random names already work often because PV's hole is broad (section buckets carry 40% of it, and a random
name lands in a trusted bucket with a negative sign often). On the unconstrained model, GAMMA API (import addition,
which our search does not use) is stronger than our append + add-section search; that row is context, not a claim.

## Re-run with derived directions (2026-10-28; runs 99-100; read 2026-10-29)

The C4 rows are retrained from the derived directions (run 97; `docs/item-layer-design.md`, Build status) and
evaluated as precondition-row detectors: a file that passes the precondition check is scored by the C4 model, any other
by the unconstrained reference, each at its own 1% FPR threshold (`a1_evaluate.py --route`; the check is made on every
attack query). The derived files differ from the hand rules only in entry_name_hash (dropped under M_add) and
security_size (down under M_full). 12 of the 100 pilot files fail the check (all malware, 8 truncated at 4 MB). The
adaptive search is not routed: its C4 rows hold for passing files, failing files are the unconstrained row's. Decided
(user): the strict detector is one sentence, not a row; the >4 MB files stay.

**Result.** Both hypotheses hold. Test metrics are within noise of runs 77/80 under M_add and slightly better under
M_full (security_size constrained down rather than dropped):

| Detector (10% store) | AUC hand -> derived | TPR @ 1% FPR | TPR @ 0.1% FPR |
|---|---|---|---|
| C4 features, M_add | 0.9946 -> 0.9945 | 91.2% -> 90.9% | 78.2% -> 79.1% |
| C4 sums, M_add | 0.9953 -> 0.9953 | 92.4% -> 92.3% | 81.1% -> 80.9% |
| C4 features, M_full | 0.9919 -> 0.9924 | 86.7% -> 88.1% | 69.7% -> 70.8% |
| C4 sums, M_full | 0.9930 -> 0.9935 | 88.6% -> 89.9% | 72.3% -> 75.1% |

(Full store, merged imports: M_add 0.9957 -> 0.9957, 92.1% -> 92.0%; M_full 0.9930 -> 0.9934, 87.4% -> 88.6%.)

Toolkit columns, routed C4 rows, evasion over detected pilot malware, split by whether the original file passes the
precondition check (38 of 50 pilot malware pass):

| Detector | Det. | Seen, pass | Held-out, pass | Seen, fail | Held-out, fail |
|---|---|---|---|---|---|
| Unconstrained (reference) | 47 | 8/35 | 21/35 | 0/12 | 4/12 |
| PV, 4 seen attacks | 22 | 0/16 | 4/16 | 0/6 | 0/6 |
| C4 features, M_add (routed) | 45 | 0/33 | 9/33* | 0/12 | 1/12* |
| C4 sums, M_add (routed) | 44 | 0/32 | 16/32* | 0/12 | 1/12* |
| C4 features, M_full (routed) | 40 | 0/28 | **0/28** | 0/12 | 1/12 |
| C4 sums, M_full (routed) | 42 | 0/30 | **0/30** | 0/12 | 1/12 |

\* header_fields, outside M_add (as in run 81). On passing files the M_full rows are evaded by nothing, as the guarantee
says. The one failing-file evasion of every routed row is the same file (`480087e22a70...`, header_fields), scored by
the reference branch; the guarantee does not cover it. On the failing files the routed rows are evaded less often than
the reference itself (1/12 vs 4/12 held-out): the reference's other three are GAMMA API runs, a black-box search that,
against the routed detector, is scored by the C4 model whenever its query passes the check. (Likely explanation; not
checked per query.) Coverage of the guarantee: 38/50 pilot malware (76%); on the 2,000-file set 1,682/2,000 files pass.

Adaptive column (C1-declared targeted search, M_full, full-store models, unrouted): unconstrained 10/49 (9 real), PV
22/22 (21 real), both C4 rows 0/45 with largest score change exactly 0.0. Split by the check: the C4 rows' 0/33 on
passing files is the guarantee; on the 12 failing files the routed detector would use the unconstrained model, which
the search evades on 0/12, so the routed row would be 0/45 as well, provided no query moves a failing file into the
passing branch (not checked; the search is not routed).


## Step 9: C4 rows on the derived directions after G7 (2026-10-29; run 105; read 2026-10-30)

The six C4 models retrained (`-v2`) on the directions after G7's fixes and the new body regions (run 104); the only
training-input changes from run 99 are overlay_size (dropped under every threat model) and security_virtual_address (up
under M_add). Run 107 confirmed these inputs on the 2,000-file set (G7 passes on all 73,063 edits; the inputs are
byte-identical to the pilot's). The precondition check now includes the plain-layout clauses; 38 of the 50 pilot
malware still pass.

**Result.** Test metrics within noise of run 99 (AUC within 0.0003, TPR at 1% FPR within 0.9 points):

| Detector (10% store) | AUC run 99 -> v2 | TPR @ 1% FPR | TPR @ 0.1% FPR |
|---|---|---|---|
| C4 features, M_add | 0.9945 -> 0.9943 | 90.9% -> 90.4% | 79.1% -> 77.2% |
| C4 sums, M_add | 0.9953 -> 0.9952 | 92.3% -> 92.2% | 80.9% -> 79.8% |
| C4 features, M_full | 0.9924 -> 0.9922 | 88.1% -> 87.2% | 70.8% -> 71.0% |
| C4 sums, M_full | 0.9935 -> 0.9935 | 89.9% -> 89.6% | 75.1% -> 74.8% |

(Full store, merged imports: M_add 0.9957 -> 0.9955, 92.0% -> 92.0%; M_full 0.9934 -> 0.9932, 88.6% -> 88.7%.)

| Detector | Det. | Seen, pass | Held-out, pass | Seen, fail | Held-out, fail |
|---|---|---|---|---|---|
| Unconstrained (reference) | 47 | 8/35 | 21/35 | 0/12 | 4/12 |
| PV, 4 seen attacks | 22 | 0/16 | 4/16 | 0/6 | 0/6 |
| C4 features, M_add (routed) | 45 | 0/33 | 13/33* | 0/12 | 1/12* |
| C4 sums, M_add (routed) | 43 | 0/31 | 11/31* | 0/12 | 1/12* |
| C4 features, M_full (routed) | 40 | 0/28 | **0/28** | 0/12 | 1/12 |
| C4 sums, M_full (routed) | 42 | 0/30 | **0/30** | 0/12 | 1/12 |

\* header_fields, outside M_add, as in runs 81 and 100 (there 9/33 and 16/32; the retrained models differ in which
files the header attack happens to cross). The failing-file evasion is again `480087e22a70...` (header_fields,
reference branch).

Adaptive column: both C4 rows 0 (0/47, 0/41), largest declared score change exactly 0.0. The unconstrained row first
read 28/49 (run 100: 10/49), **inflated by two bugs in the search**, both fixed on 2026-10-30 (run 108): (1) the
engine's declared add-section ends the file and so removes the overlay (pefile's rule, G7 finding 4), but the search
built each step's file with LIEF, which puts the section before the overlay and keeps it, so every later step claimed
the overlay's removal again (an append creates an overlay the same way); (2) the engine leaves the features no readout
models (pefile's 88 warning flags) NaN, which a GBDT reads as missing and sends down its default branch (up to ~3 in
logit on one file). Decided (user): each step is now written by our own byte-level edit (`scripts/catalogue_checks.py`),
exactly the declared operation, and the unmodeled features keep the current file's values, as the hand predictors did.

**After the fix (run 108):** unconstrained **4/49**, PV **16/22**, both C4 rows **0** (min_delta_logit exactly 0).
Declared and real scores agree (median gap < 1e-4; every declared evasion holds on the written, re-extracted file),
so the adaptive column no longer has an A4 gap of its own. The evasion is lower than run 100's because 10 of the 49
detected pilot malware have no room for another section header (the search can only append to them; 5 of PV's 6
losses, the sixth ends at 0.817 against a threshold of 0.811), and because run 100's steps started from LIEF's
relayout, which mixed the tool's layout changes into the score.

## Diagnosing the 16->12 PV drop (run 108 vs run 119, read 2026-11-03)

Run 119 (all twelve operations, queries 200) evades **12/22** PV-detected files; run 108 (append + add-section only,
queries 100) evaded **16/22**. Joining the two `adaptive.parquet` tables on `name` (108:
`artifacts/experiments/a1/adaptive-v3/`, 119: `artifacts/experiments/a1/adaptive-twelve/mfull/`, both filtered to
`defense == "pv"`), **8** files regressed (108 evaded, 119 did not); 119 also newly evaded 4 that 108 missed, netting
16->12. tau = 0.810897; a file evades when `p_adv_real < tau`. The full twelve-op menu is ~25 candidates per greedy
step (always including 9 section candidates, since `sec` stays in the menu), so `queries = 25` means exactly one step
and `queries = 200` means the ceiling.

| file (first 8) | 108 ops | 108 q | 108 p_adv | 119 ops | 119 q | 119 p_adv | 119 bytes | 119 min_delta | class |
|---|---|--:|--:|---|--:|--:|--:|--:|:--:|
| `1056eb84` | sec,sec | 24 | 0.412 | (none) | 25 | 0.967 | 0 | 0.000 | a |
| `1a5a5a33` | sec | 12 | 0.703 | (none) | 25 | 0.811 | 0 | 0.000 | a |
| `3caffa06` | sec,sec,sec | 36 | 0.629 | (none) | 25 | 0.979 | 0 | 0.000 | a |
| `480087e2` | sec | 12 | 0.727 | (none) | 25 | 0.905 | 0 | 0.000 | a |
| `7cdbf80b` | sec x7 | 84 | 0.771 | (none) | 25 | 0.996 | 0 | 0.000 | a |
| `5615d33f` | sec x4 | 48 | 0.790 | dos,slk | 75 | 0.962 | 0 | -1.137 | b |
| `3eb8b6d9` | sec x8 | 96 | 0.602 | sec,sec,ren,sec x5 | 200 | 0.916 | 124672 | -1.818 | c |
| `6af84b58` | sec x8 | 96 | 0.767 | sec,sec,ren,sec x5 | 200 | 0.916 | 49300 | -1.626 | c |

Classes: **(a)** no edit applied, stopped after one step (q=25, 5/8 files); **(b)** non-section edits applied, did not
cross tau (1/8); **(c)** spent the whole 200-query budget without crossing tau (2/8).

**Conclusion.** The drop is **mostly the luck of the random candidate draw interacting with greedy's
strict-improvement stop -- not query-budget exhaustion, and only marginally "being misled."** Budget exhaustion
explains only 2 of 8 (the q=200 files). The dominant pattern is the 5 class-(a) files: run 119 stopped after **one
step (q=25)** with **min_delta_logit = 0.000** -- not one of its 25 candidates, including its 9 section candidates,
lowered the score, whereas on the identical start file run 108's section draw did. Section edits *were* tried but the
randomly drawn names/donor content didn't help, so the strict-improvement rule quit immediately (`1a5a5a33` lands at
0.8115 vs tau 0.8109 -- one unlucky draw from evading). The twelve-op `full_menu` consumes the RNG differently and
reseeds the per-step section draws, so 119 simply drew unhelpful sections at the decisive first step. Only `5615d33f`
fits "misled" (greedy took locally-best dos+slk, then stalled); the two ceiling files added sections plus one `ren`
but drew ineffective ones. The 108-vs-119 comparison is therefore **confounded by a shifted RNG stream and a larger
menu**: the 16->12 is not a clean "more ops hurt" signal, and session 4's "myopic greedy misled on the section-hash
hole" holds for at most 1-3 files. (Reproduce: join the two parquets on `name`, filter `defense == "pv"`,
`evaded_108 & ~evaded_119`.)

**Resolution (user, 2026-11-03): report the union (Table 7 Option A).** The two menus are complementary, not
one-dominates-the-other: run 108 (append+add-section) evades 16, run 119's twelve-op menu evades 12, their
**intersection is 8**, so run-108-only is 8 and twelve-op-only is 4, and the **union is 20/22** (only two files --
`303ef5c9`, `b1d6d149` -- are evaded by neither, both making no helpful first move, `num_ops = 0`,
`min_delta_logit = 0.0`, `p_clean` 0.97-0.99, far above tau). The twelve-op-only 4 are evaded by operations run 108
lacks (`ren`, `slk`, one with `sec`), three of them rename-based with **0 bytes added** -- renaming an existing section
reaches the same section-name-hash buckets the add-section route uses, without needing room for a new header. Every
evasion in both runs re-extracts (0 predicted-vs-real mismatches). The adaptive attacker is therefore reported as the
search run under both menus, keeping any evasion: the standard max-over-configs adaptive-attacker convention, and the
strongest number our search finds. On the unconstrained detector twelve-op dominates (10 >= 108's 4; union = 10), so
that cell is 20% uniformly. Table 7 and the adaptive prose in `manuscript/_f_evaluation.tex` updated to PV 20/22 (91%),
unconstrained 10/49 (20%); the earlier "evades PV on 16 ... six files it does not evade" prose (which was also
accidentally commented out by a stray `%`) is replaced. Measurement comment in the `.tex` documents the breakdown.
