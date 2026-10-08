# PB1 Pilot: Problem-Space Faithfulness and Cost (Gate 2)

Drafted 2026-10-07. See `PLAN.md` (PB1, Gate 2). Decisions: level-2 PE-aware occlusion, K = 256 windows, Gate 2
thresholds to be reassessed after the pilot.

## Question

Do pulled-back feature explanations identify the bytes that drive the decision, compared with direct problem-space
explanation (occlusion) and random, and at what cost?

## Design

- **Files:** 100 from the explanation set (50 per label, seeded).
- **Models and explainers (seed 0):** GBDT with TreeSHAP path and interventional; MLP with IG. KernelSHAP and
  gradient × input wait until after the gate.
- **Methods, per model:**
  1. pullback of each explainer, a ranking of the bytes;
  2. direct occlusion over K = 256 equal windows (K + 1 feature extractions);
  3. black-box pullback through the P estimated from the same K extractions;
  4. random order (3 seeds).
  One occlusion run scores both models and yields the black-box P. Comparing that P with the instrumented P, coarsened
  to the same windows (T3), measures the quality of the instrumentation.
- **Ranking:** bytes ordered by evidence for the predicted class, sign(f(x)) · b; ties keep file order. The null
  element cannot be deleted.
- **Deletion:** remove the top-ranked bytes up to log-spaced budgets (0.1%, 0.2%, 0.5%, 1%, 2%, 5%, 10%, 20%, 50% of
  the file), re-extract features, re-score; record the log-odds.
- ~~**Insertion**~~ dropped after the pilot (2026-10-07): see `docs/pb1_pilot.md`, "What insertion tests".
- **Metrics:** normalized area under each curve; the fraction of the log-odds removed at 1%; cost in feature
  extractions and wall-clock time.
- **Gate 2 (thresholds flexible):** the TreeSHAP pullback beats random (paired test), approaches occlusion's gain over
  random, and costs far fewer extractions. Reassess after seeing the numbers.

## The ablation operator (level 2, PE-aware)

The pilot probe (24 files, 64 windows) showed why naive zeroing is unusable: it rarely breaks parsing (1.7% of
perturbations), but when it does every PE feature collapses, and the header region holds about half of the
pulled-back attribution while being 0.1% of the file. Protecting the whole header would hide that half instead.

- **Ablation** replaces bytes with zeros (random bytes as a robustness variant), except **protected bytes**: the
  header fields whose zeroing breaks parsing or moves the file's layout.
- **The protected set is discovered empirically** (`scripts/discover_protected_fields.py`), not chosen by hand:
  1. On a large sample (thousands of training files of both labels plus the fixtures), zero each header field alone
     (DOS header, NT signature, file header, optional header, data directories, section headers) and record whether
     pefile fails or the layout changes.
  2. Protect the fields that do so in more than a negligible fraction of files.
  3. Check jointly: zeroing *every* unprotected header byte at once must keep every sampled file parseable with an
     unchanged layout (this is the starting point of the insertion curve).
- **Layout** = what tells the parser where everything else is: e_lfanew, the number of sections, the location of
  the section table, and each section's raw-data offset and size.
- **Runtime checks (every perturbed file in the experiment):** protected bytes are unchanged; pefile still parses;
  the layout is unchanged; feature extraction succeeds. Violations are recorded per perturbation, counted in the
  report, and excluded from the curves; a high violation rate stops the analysis rather than being averaged away.
- **Placement:** the PE-specific parts (fields, layout, protected mask) live in `featuresets/ember2024/`; the ablation
  machinery (masks, fills, budgets, curves) is generic and lives in `provexp`.

## Cost

About 600 extractions per file (256 for occlusion, about 20 per curve for 16 rankings), roughly 30 minutes on 16
workers for 100 files. Protected-field discovery: about 150 fields × a few thousand files of pefile parses, minutes on
16 workers.

## Cost and progress reporting (added 2026-10-08, after the 6.1 h baselines run)

The cost of a run is (extractions per file) x (per-extraction time), and both are predictable, so the runner now says
up front what it will cost and reports progress in units of work:

- **Extractions per file are known exactly** before the run: 2 + the windows of every occlusion run + the KernelSHAP
  coalitions + one per budget and method (`extractions_per_file`; predicted 7,640 vs. 7,577 actual median on the
  baselines run). The occlusion sweep dominates: on the slowest file, K = 4,096 alone was 58% of the time.
- **Per-extraction time** is fitted as 0.040 s + 0.251 s per megabyte (`predict_seconds`), which predicts the total
  work within 1% (63.6 vs. 63.1 worker-hours). A single file can take twice its prediction, so the wall-clock
  estimate is printed as a floor.
- **Tasks run longest-first**, which shortens the wall-clock a little (6.1 -> 5.8 h here) and, more importantly, puts
  the long poles at the start so the ETA is honest instead of collapsing at the end.
- **The progress bar counts predicted seconds of work, not files**, because files differ by three orders of magnitude
  (median 9 min, max 4.1 h), and every file is logged as it finishes (`bar.write`, so the line is not lost on the
  bar's own line) with its size, time, extractions, and status.
- **An irreducible floor:** the longest single file bounds the run (4.1 h of the 6.1 h here, against 3.9 h of
  perfectly balanced work). No scheduling can go below it. To go faster, either parallelize within a file (the
  budgets and methods of one file are independent) or cap the sweep for the largest files; both are open.

## Steps

1. ~~Protected-field discovery~~ done: the layout fields are protected globally, other breakers per file.
2. ~~Ablation modules and runtime checks~~ done (`provexp.ablation`, `featuresets/ember2024/ablation.py`).
3. ~~Runner and pilot run~~ done; `docs/pb1_pilot.md` (Gate 2 read).
4. **After the pilot (2026-10-07):** insertion dropped; level 3 added (header fields take their most common training
   value, `--header typical`); KernelSHAP for both models (`explain.py --explainers kernelshap_gbdt kernelshap_mlp
   --subset ...`). ~~Reruns~~ done: `zeros/`, `zeros-typical-header/`, `random-typical-header/`.
5. ~~Refresh `docs/pb1_pilot.md`~~ done (2026-10-08). PB1 continues on the GBDT only; the MLP is set aside temporarily
   and returns after the GBDT methodology is established (`PLAN.md`, "Model scope"). Next: a reassessment round with
   the user before PB1 at scale.
6. **Baselines pilot (2026-10-08):** level 3 primary; occlusion and the coarsened pullback at K = 64, 1,024, 4,096
   (the cost-faithfulness curve); KernelSHAP over the 256 windows (2,048 coalitions; reference: the fully ablated
   file); the unsigned pullback ranking (overshoot test). Same 100 files (`--files`); command in `docs/status.md`.
