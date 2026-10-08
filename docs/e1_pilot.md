# E1 Pilot: Problem-Space Faithfulness and Cost (Gate 2)

Runs 2026-10-07 (`scripts/faithfulness.py --seed 0 --num_files 100`, K = 256 windows; tables from
`scripts/e1_tables.py --fill <variant>`). Design in `docs/plan_e1.md`. Deletion only: insertion was dropped (see
"What insertion tests"; its numbers are in this file's git history). The pipeline is deterministic: the level-2 rerun
with KernelSHAP reproduced every earlier TreeSHAP and IG number exactly.

Three operators, each on the same 100 files (`artifacts/experiments/e1/seed-0/<variant>/`):

| variant | content bytes | unprotected header fields | name |
|---|---|---|---|
| `zeros/` | zeros | zeros | level 2 |
| `zeros-typical-header/` | zeros | most common training value | level 3 |
| `random-typical-header/` | random | most common training value | level 3, random fill |
| `random/` (first run) | random | zeros | level 2, random fill |

## The runs are clean

- **KernelSHAP** (`explain-kernelshap-seed0.log`): 100 of 100 files for both models, completeness error ≤ 3e-14,
  about 5 minutes per model on 16 workers.
- **E1, all three variants:** 100 files (2 excluded for TreeSHAP's local-accuracy violation), 0 failures, 0 of 23,000
  curve points failed verification, 0 windows failed, no file needed file-specific protected fields, no `warning`
  key. About 21 minutes each on 16 workers.

## The ablation operator held up

- **Protected-field discovery** (`scripts/discover_protected_fields.py`), 2,000 training files: the layout fields
  (e_magic, e_lfanew, the signature, NumberOfSections, SizeOfOptionalHeader, each section's VirtualAddress,
  PointerToRawData, SizeOfRawData) break parsing or move the layout in essentially every file. Every other field is
  rare: e_sp and BaseOfCode break 7 files each (0.35%), FileAlignment 1, e_cs and e_oemid 7 each (all in files whose
  DOS and PE headers overlap). No other field reaches 1%, so the global protected set is the layout fields, and the
  per-file sweep catches the rest.
- **Held-out check**, the 2,000 explanation-set files: 0 unprotectable files; 0 broken files when ablating every
  unprotected header byte, every unprotected byte (zeros), or every unprotected byte (random, header zero-filled);
  2 files needed file-specific fields. Median 74 protected bytes per file.
- **Level 3** (typical header values, `header_typical_values.json`, 2,000 training files balanced by label) broke no
  file either.

## Results

"Evidence removed" is s · (f(x) − f(deleted)), with s the sign of the original log-odds; methods rank bytes by
s times their score. The deletion area is the mean of evidence removed over the budgets 0.1%–50% (log-spaced). The
headline number is **gain / occlusion gain** = (area − random area) / (occlusion area − random area); in parentheses,
the files (of 100) on which the method beats occlusion and the paired Wilcoxon p-value.

### GBDT

| method | level 2 | level 3 | level 3, random fill |
|---|---|---|---|
| pullback (bytes), path TreeSHAP | 1.79 (96, 1e-17) | 1.67 (87, 2e-15) | 1.65 (81, 2e-11) |
| pullback (bytes), interventional TreeSHAP | 1.78 (93, 4e-17) | 1.71 (89, 4e-16) | 1.69 (81, 1e-12) |
| pullback (bytes), KernelSHAP | 1.78 (93, 9e-17) | 1.67 (90, 2e-15) | 1.66 (79, 2e-11) |
| pullback (windows), path | 1.03 (65, 4e-3) | 0.98 (54, 0.82) | 0.98 (47, 0.44) |
| pullback (windows), interventional | 1.03 (67, 3e-3) | 0.98 (53, 0.83) | 0.97 (49, 0.43) |
| pullback (windows), KernelSHAP | 1.02 (61, 0.08) | 0.99 (56, 0.85) | 0.99 (52, 0.75) |
| black-box pullback, path | 0.93 (61, 0.58) | 1.04 (65, 7e-4) | 1.02 (63, 6e-3) |
| black-box pullback, interventional | 0.96 (59, 0.45) | 1.04 (61, 6e-3) | 1.02 (60, 0.02) |
| black-box pullback, KernelSHAP | 0.93 (53, 0.53) | 1.02 (59, 0.06) | 0.99 (59, 0.15) |
| occlusion (area) | 4.94 | 5.06 | 5.08 |
| random (area) | 0.93 | 0.88 | 1.14 |

Every pullback beats random on 96–100 of 100 files under every operator. Median evidence removed by deleting 0.1% of
the bytes (level 3): 5.9 (path pullback) vs. 2.6 (occlusion) vs. 0.0 (random). The level-2 random-fill run gave
1.72 (bytes) and 1.01 (windows) for the path pullback.

### MLP

| method | level 2 | level 3 | level 3, random fill |
|---|---|---|---|
| pullback (bytes), IG | 0.94 (49, 0.21) | 0.69 (30, 1e-4) | 0.52 (26, 1e-7) |
| pullback (bytes), KernelSHAP | 0.96 (45, 0.48) | 0.85 (35, 4e-3) | 0.71 (31, 4e-5) |
| pullback (windows), IG | 0.72 (31, 1e-8) | 0.55 (29, 2e-8) | 0.45 (19, 5e-12) |
| pullback (windows), KernelSHAP | 0.85 (31, 2e-7) | 0.70 (30, 9e-7) | 0.58 (28, 1e-9) |
| black-box pullback, IG | 0.66 (20, 4e-13) | 0.67 (35, 6e-6) | 0.59 (30, 3e-8) |
| black-box pullback, KernelSHAP | 0.83 (29, 5e-8) | 0.80 (41, 2e-3) | 0.71 (34, 2e-5) |
| occlusion (area) | 7.71 | 7.92 | 8.88 |
| random (area) | 1.60 | 1.33 | 1.81 |

The level-2 random-fill run gave 0.94 (bytes) and 0.68 (windows) for the IG pullback.

### KernelSHAP vs. the other explainers (feature space, 100 files, median per file)

| pair | Pearson | Spearman | top-20 overlap |
|---|---|---|---|
| KernelSHAP vs. interventional TreeSHAP (GBDT) | 0.97 | 0.47 | 0.85 |
| KernelSHAP vs. path TreeSHAP (GBDT) | 0.92 | 0.44 | 0.80 |
| path vs. interventional TreeSHAP (GBDT) | 0.96 | 0.93 | 0.85 |
| KernelSHAP vs. IG (MLP) | 0.78 | 0.37 | 0.65 |

The low Spearman of KernelSHAP is the sampling noise in the long tail of near-zero features; the top of the ranking,
which deletion uses, agrees.

### Diagnostics

**Fully ablated file** (median log-odds; original: benign −6.6 / malware 6.0 for the GBDT, −9.1 / 9.0 for the MLP):

| model | level 2 | level 3 | level 3, random fill |
|---|---|---|---|
| GBDT | −0.5 / −0.5 | 0.2 / 0.4 | 0.0 / −0.3 |
| MLP | 1.5 / 1.5 | −8.2 / −8.3 | −6.5 / −6.4 |

**Overshoot** (per file, the most evidence removed at any budget below 100% minus the evidence removed at 100%; median,
and the share of files above 0.5):

| model | method | level 2 | level 3 | level 3, random fill |
|---|---|---|---|---|
| GBDT | pullback (bytes), path | 3.56 (93%) | 3.49 (87%) | 2.46 (69%) |
| GBDT | pullback (windows), path | 0.66 (56%) | 0.53 (50%) | 0.30 (43%) |
| GBDT | occlusion | 0.24 (38%) | 0.34 (47%) | 0.11 (41%) |
| MLP | pullback (bytes), KernelSHAP | 3.69 (75%) | 1.21 (58%) | 1.53 (59%) |
| MLP | occlusion | 0.21 (29%) | 1.39 (62%) | 2.82 (79%) |

**By label** (deletion area, benign / malware, level 3): GBDT path pullback (bytes) 9.18 / 6.56, (windows) 5.14 / 4.85,
occlusion 5.30 / 4.82. MLP KernelSHAP pullback (bytes) 3.94 / 9.95, occlusion 4.53 / 11.31.

### Cost (median per file; 208 KB median size)

| instrumented extraction (one pullback) | occlusion, 256 windows | ratio |
|---|---|---|
| 0.15 s | 20.1 s (258 extractions) | 135× |

The same under all three operators (135–138×). The explainers themselves cost milliseconds (TreeSHAP) to about 25 ms
(IG on a GPU) per file; KernelSHAP with 32,768 samples costs about 45 s per file and model on one core, more than
occlusion. Byte-level occlusion would need one extraction per byte.

### Black-box vs. instrumented provenance (coarsened to the 256 windows; level 2)

| subset | attributable: instrumented / black-box | median total variation where both |
|---|---|---|
| histogram | 0.96 / 0.95 | 0.00 |
| header | 1.00 / 0.43 | 0.00 |
| section | 0.18 / 0.18 | 0.00 |
| datadirectories | 0.94 / 0.33 | 0.00 |
| richheader | 0.16 / 0.16 | 0.00 |
| strings | 0.62 / 0.62 | 0.44 |
| byteentropy | 0.59 / 0.76 | 0.60 |
| imports | 0.07 / 0.08 | 0.60 |
| exports | 0.08 / 0.09 | 0.67 |
| authenticode | 1.00 / 0.18 | 0.38 |
| pefilewarnings | 0.00 / 0.06 | — |

- **Where a feature is additive in its bytes** (histogram, header fields, section and data-directory fields, the Rich
  header), the black-box estimate agrees *exactly* with the instrumented provenance at the window level, as T1
  predicts. This validates the instrumentation for those groups independently.
- **Non-additive groups differ** (strings 0.44, entropy windows 0.60, hashed imports and exports 0.60–0.67): zeroing
  part of a string or name does not remove a proportional share of it; it changes or moves it (a different hash
  bucket). This is the gap T1 says to measure, and it is where instrumented and black-box provenance genuinely disagree.
- **Occlusion cannot see everything:** header features whose bytes are already zero, or protected, never change
  (black-box sees 43% of header features vs. 100%; at level 3 only 23%, because a field that already holds its typical
  value does not change). It also creates features: zeroing windows adds new low-entropy windows (byteentropy, 17%
  black-box only) and new pefile warnings (6%). Random fill adds its own artifacts: the histogram, exactly additive
  under zero fill, differs by a total variation of 0.60, because random bytes add counts to other bins.

## What insertion tests

Deletion asks whether the bytes an explanation ranks highest are *necessary*: remove them, and the evidence for the
decision should drop fast. Insertion asks whether they are *sufficient*: start from a file with every removable byte
blanked, restore only the top-ranked bytes, and the evidence should come back fast. Insertion is weaker here for three
reasons: the blank (or random) file is far from any real file, so the model's response to it is hard to interpret;
many features need contiguous structures (a string, an import name), and restoring scattered top-ranked bytes does not
rebuild them; and the explanations were computed relative to a different reference (TreeSHAP's training distribution,
IG's background mean), not relative to the blank file. Insertion was dropped.

## Reading

1. **GBDT, at equal granularity, the pullback matches occlusion at 1/135 of the cost, under every operator.** Coarsened
   to the 256 windows, the pullback's gain is 0.97–1.03× occlusion's for all three explainers and all three operators.
   At level 2 it was slightly ahead (65–67/100, p ≈ 3e-3); at level 3 the difference is gone (47–56/100, p ≥ 0.4).
   Parity holds; the small level-2 edge does not.
2. **The byte-level advantage mostly survives realistic header values.** 1.79× → 1.67× (level 3) → 1.65× (level 3,
   random fill): 15–18% of the margin over occlusion came from zeroed header fields; the rest survives, on 79–90 of
   100 files. It is concentrated on benign files (9.2 vs. 6.6), where occlusion has no such edge. The comparison is not
   at equal granularity: windowed occlusion is the affordable baseline, and byte-level occlusion would cost one
   extraction per byte.
3. **The overshoot is not a header artifact, so the earlier reading was wrong.** Level 3 leaves the byte-level overshoot
   unchanged (3.56 → 3.49) and random fill only shrinks it (2.46). The likely cause is the signed ranking: deleting the
   top 50% of bytes removes the bytes that support the decision and keeps those that oppose it, so it can remove more
   evidence than deleting everything (which also removes the opposing evidence). For an additive model the maximum is
   the sum of the positive contributions, which exceeds the net. A finer ranking separates the two signs better, which
   is why bytes overshoot most, windows less, random not at all. A diagnostic of resolution, not of artifacts
   (proposed reading, to be discussed).
4. **KernelSHAP on the GBDT matches TreeSHAP** (1.78 vs. 1.78–1.79 at bytes, 1.02 vs. 1.03 at windows; top-20 overlap
   0.85, Pearson 0.97). The result does not depend on the explainer.
5. **KernelSHAP does not fix the MLP.** It is better than IG under every operator and granularity (by 0.02–0.19), but
   the 4-file smoke test (1.51×) did not replicate: at level 2 it is on par with occlusion at bytes (0.96, n.s.) and
   behind at windows (0.85); at level 3, behind at both (0.85, 0.70). The **black-box pullback of the same
   explanations is just as far behind** (0.80 at level 3), so the bottleneck is the feature-space explanation, not
   the instrumented P: the top-ranked features of the MLP are not the ones whose removal in the problem space moves it
   most.
6. **The MLP is the wrong model for level 3 as is.** The fully ablated file goes from 1.5 (level 2) to −8.2 (level 3):
   typical header values on an otherwise empty file look strongly benign to the MLP. Deleting evidence from a benign
   file therefore moves the MLP back toward benign at full ablation (non-monotone curves, overshoot for every method
   including occlusion), and from a malware file it moves through the boundary. The GBDT stays near 0 under all three
   operators. MLP results under level 3 are paired and still valid as a ranking comparison, but harder to interpret
   than the GBDT's.
7. **Black-box P improves at level 3** (0.93–0.96 → 1.02–1.04 for the GBDT): estimated under the same operator used to
   evaluate, it captures that operator's non-additive effects. It costs as much as occlusion.

## Preview of E2 (100 files, one seed, level 2; indicative only; previous definitions of H and O)

Spearman correlation, per file, between census statistics and the pullback's deletion gain:

| target | coverage κ | ambiguity H | overlap O | size | localizability ℓ |
|---|---|---|---|---|---|
| GBDT: pullback − random | 0.36 | 0.43 | −0.02 | 0.22 | 0.40 |
| GBDT: pullback (windows) − occlusion | 0.23 | 0.16 | 0.04 | −0.01 | 0.21 |
| MLP: pullback − random | 0.36 | 0.32 | 0.11 | −0.01 | 0.30 |
| MLP: pullback (windows) − occlusion | 0.09 | 0.04 | −0.11 | 0.28 | 0.07 |

Coverage and localizability predict where the pullback works; overlap does not; the saturating ambiguity correlates
in the wrong direction (likely confounded with coverage). Consistent with the pilot's finding 4. Not recomputed for
level 3.

## Black-box estimator bug (fixed)

The first run's estimator passed raw feature changes to `Provenance`, which treats a column as empty when its sum is
below 1e-12 of the largest column's. Feature changes span about 12 orders of magnitude, so most small-scale features
were treated as empty. Fixed by normalizing each feature's changes (P is unchanged), with a regression test; the
rerun reproduced every other number exactly.

## Gate 2

**Passed for the GBDT; the MLP is set aside temporarily (decided 2026-10-08).** The GBDT is the first classifier we
experiment with; the MLP returns once the methodology is established (`PLAN.md`, "Model scope"). For the GBDT, the core claim (faithfulness comparable to direct
problem-space explanation at two orders of magnitude lower cost) holds at equal granularity under all three operators
and three explainers, and the byte-level advantage survives realistic header values. For the MLP, neither IG nor
KernelSHAP reaches occlusion at window level under any operator, and the black-box pullback shows that the shortfall
comes from the explanations, not from P; that diagnosis is the starting point when the MLP returns. Thresholds stay
open for the reassessment round.

## Open for the reassessment round

1. **Gate 2 thresholds** and whether the GBDT result alone passes the gate.
2. **The headline claim:** window-level parity at 1/135 of the cost (robust, equal granularity), the byte-level
   advantage (1.65×, not at equal granularity, concentrated on benign files), or both.
3. **The overshoot reading** (signed resolution, point 3): accept, or test, e.g. with unsigned rankings or by
   splitting deletion into supporting and opposing bytes.
4. ~~**Neural models**~~ decided 2026-10-08: the GBDT first; the MLP returns later, starting with a feature-space
   deletion check and then a better explainer or a matched reference (`PLAN.md`, "Second classifier: the MLP").
5. **Primary operator:** level 3 (more realistic, removes the small level-2 edge and changes the MLP's reference
   drastically) or level 2 with level 3 as robustness.
6. **What next:** E1 at scale (more files, seeds 1–2), E2 (design open), E3.
