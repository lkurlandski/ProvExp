# E1 Pilot: Problem-Space Faithfulness and Cost (Gate 2)

Run 2026-10-07 (`scripts/faithfulness.py --seed 0 --num_files 100`, K = 256 windows, zero fill and random fill;
tables from `scripts/e1_tables.py --fill {zeros,random}`). Design in `docs/plan_e1.md`. The first run had a bug in the
black-box estimator; the rerun with the fix reproduced every other number exactly (the pipeline is deterministic).

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
- **E1 run:** 100 files (2 excluded because interventional TreeSHAP violates local accuracy on them), 0 failures, 0 of
  34,000 curve points failed verification, 0 windows failed. 22 minutes on 16 workers.

## Results

"Evidence removed" is s · (f(x) − f(deleted)), with s the sign of the original log-odds; the deletion area is its mean
over the budgets 0.1%–50% (log-spaced). Insertion is the evidence recovered from the fully ablated file.

### Deletion and insertion areas (mean over 100 files; paired comparisons per file)

| model | curve | method | area | wins vs random | wins vs occlusion (p) | gain / occlusion gain |
|---|---|---|---|---|---|---|
| GBDT | deletion | pullback (bytes), path TreeSHAP | 8.11 | 100/100 | 96/100 (1e-17) | 1.79 |
| GBDT | deletion | pullback (bytes), interventional | 8.06 | 100/100 | 93/100 (4e-17) | 1.78 |
| GBDT | deletion | pullback (windows), path | 5.07 | 98/100 | 65/100 (4e-3) | 1.03 |
| GBDT | deletion | pullback (windows), interventional | 5.06 | 98/100 | 67/100 (3e-3) | 1.03 |
| GBDT | deletion | occlusion (windows) | 4.94 | 98/100 | — | 1.00 |
| GBDT | deletion | random (windows) | 0.93 | — | 2/100 | 0.00 |
| GBDT | insertion | pullback (bytes), path | 4.57 | 97/100 | 59/100 (7e-3) | 1.16 |
| GBDT | insertion | pullback (windows), path | 3.76 | 94/100 | 40/100 (3e-3) | 0.92 |
| GBDT | insertion | occlusion | 4.03 | 98/100 | — | 1.00 |
| MLP | deletion | pullback (bytes), IG | 7.35 | 95/100 | 49/100 (0.21) | 0.94 |
| MLP | deletion | pullback (windows), IG | 5.98 | 89/100 | 31/100 (1e-8) | 0.72 |
| MLP | deletion | occlusion | 7.71 | 100/100 | — | 1.00 |
| MLP | insertion | pullback (bytes), IG | 0.62 | 55/100 | 17/100 (5e-14) | 0.06 |
| MLP | insertion | pullback (windows), IG | 3.06 | 78/100 | 28/100 (4e-6) | 0.65 |
| MLP | insertion | occlusion | 4.49 | 90/100 | — | 1.00 |
| GBDT | deletion | black-box pullback, path | 4.67 | 93/100 | 61/100 (0.58) | 0.93 |
| GBDT | insertion | black-box pullback, path | 3.76 | 89/100 | 47/100 (0.26) | 0.92 |
| MLP | deletion | black-box pullback, IG | 5.65 | 86/100 | 20/100 (4e-13) | 0.66 |
| MLP | insertion | black-box pullback, IG | 2.95 | 70/100 | 29/100 (4e-5) | 0.62 |

Median evidence removed by deleting 0.1% of the bytes: 6.8 (GBDT, path pullback) vs. 1.9 (occlusion) vs. 0.0
(random); MLP: 5.2 (IG pullback) vs. 4.7 (occlusion).

### Cost (median per file; 208 KB median size)

| instrumented extraction (one pullback) | occlusion, 256 windows | ratio |
|---|---|---|
| 0.17 s | 20.8 s (258 extractions) | 130× |

The explainers themselves cost milliseconds (TreeSHAP) to about 25 ms (IG on a GPU) per file. Byte-level occlusion
would need one extraction per byte.

### Robustness: random fill (content bytes random; header bytes still zero-filled)

| model | curve | method | area | gain / occlusion gain (zero fill → random fill) |
|---|---|---|---|---|
| GBDT | deletion | pullback (bytes), path | 7.92 | 1.79 → 1.72 |
| GBDT | deletion | pullback (windows), path | 5.12 | 1.03 → 1.01 |
| GBDT | insertion | pullback (bytes), path | 3.78 | 1.16 → 1.06 |
| GBDT | insertion | pullback (windows), path | 2.79 | 0.92 → 0.75 |
| MLP | deletion | pullback (bytes), IG | 7.53 | 0.94 → 0.94 |
| MLP | deletion | pullback (windows), IG | 6.01 | 0.72 → 0.68 |
| MLP | insertion | pullback (bytes), IG | 0.64 | 0.06 → 0.20 |

Deletion is robust to the fill; insertion is not (it starts from a file of random bytes, which is even further from
real files than a blank one). The header-field overshoot persists because header bytes are zero-filled in both.

### Black-box vs. instrumented provenance (coarsened to the 256 windows)

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
  (black-box sees 43% of header features vs. 100%). It also creates features: zeroing windows adds new low-entropy
  windows (byteentropy, 17% black-box only) and new pefile warnings (6%). These are fill artifacts, not provenance.
- **As a ranking,** the black-box pullback is close to occlusion for the GBDT (0.93×) and worse for the MLP (0.66×),
  at the same cost as occlusion.

## What insertion tests

Deletion asks whether the bytes an explanation ranks highest are *necessary*: remove them, and the evidence for the
decision should drop fast. Insertion asks whether they are *sufficient*: start from a file with every removable byte
blanked, restore only the top-ranked bytes, and the evidence should come back fast. Insertion is weaker here for three
reasons: the blank (or random) file is far from any real file, so the model's response to it is hard to interpret;
many features need contiguous structures (a string, an import name), and restoring scattered top-ranked bytes does not
rebuild them; and the explanations were computed relative to a different reference (TreeSHAP's training distribution,
IG's background mean), not relative to the blank file. Deletion is the primary test; insertion is at most secondary.

## Reading

1. **GBDT, at equal granularity, the pullback matches occlusion at 1/130 of the cost.** Coarsened to the same 256
   windows, the TreeSHAP pullback removes as much evidence as occlusion (1.03× its gain over random; 65–67/100 files)
   and recovers slightly less on insertion (0.92×). This is the core claim, and it holds for this model.
2. **At byte granularity, the pullback far exceeds occlusion (1.8×)**, which occlusion could only approach with many
   more windows (cost linear in K). **Caveat (integrity):** the top 0.1% of bytes are mostly header fields (median
   share about 0.4–0.6: section names, VirtualSize, Characteristics, ImageBase, Subsystem, CheckSum, data-directory
   entries). Zeroing them creates values no real file has, and deletion then overshoots: removing the top 50% of
   bytes removes more evidence (9.6) than ablating everything (6.1). Part of the byte-level advantage measures the
   model's sensitivity to impossible header values rather than removal of evidence. A level-3 operator (replace a
   header field with a typical value instead of zero) would separate the two.
3. **MLP: deletion is on par with occlusion at byte level (0.94×, n.s.), but insertion fails** (0.06×, no better than
   random), and at window level the pullback trails occlusion (0.72×). A plausible mechanism: many features need
   contiguous structures (a string, an import name). Deleting one byte breaks a structure, but restoring scattered
   top-ranked bytes does not rebuild one, so insertion from a blank file punishes per-byte rankings of non-additive
   features. The GBDT's insertion gap (byte 1.16× vs. window 0.92×) is smaller. To be checked: insertion by
   contiguous runs, and IG's baseline (the background mean) vs. the ablated file as the reference.
4. **Malware vs. benign:** the byte-level pullback's deletion advantage is larger on benign files (GBDT 9.3 vs. 6.9).

## Preview of E2 (100 files, one seed; indicative only)

Spearman correlation, per file, between census statistics and the pullback's deletion gain:

| target | coverage κ | ambiguity H | overlap O | size | localizability ℓ |
|---|---|---|---|---|---|
| GBDT: pullback − random | 0.36 | 0.43 | −0.02 | 0.22 | 0.40 |
| GBDT: pullback (windows) − occlusion | 0.23 | 0.16 | 0.04 | −0.01 | 0.21 |
| MLP: pullback − random | 0.36 | 0.32 | 0.11 | −0.01 | 0.30 |
| MLP: pullback (windows) − occlusion | 0.09 | 0.04 | −0.11 | 0.28 | 0.07 |

Coverage and localizability predict where the pullback works; overlap does not; the saturating ambiguity correlates
in the wrong direction (likely confounded with coverage). Consistent with the pilot's finding 4.

## Black-box estimator bug (fixed)

The first run's estimator passed raw feature changes to `Provenance`, which treats a column as empty when its sum is
below 1e-12 of the largest column's. Feature changes span about 12 orders of magnitude, so most small-scale features
were treated as empty. Fixed by normalizing each feature's changes (P is unchanged), with a regression test; the
rerun reproduced every other number exactly.

## Gate 2

**Passed for the GBDT; partially for the MLP.** The core claim (comparable faithfulness to direct problem-space
explanation at two orders of magnitude lower cost) holds at equal granularity for the GBDT on deletion, and nearly on
insertion. The byte-level advantage is real but inflated by fill artifacts in header fields. For the MLP, deletion
works, insertion does not. Thresholds stay open, as agreed; the decision to continue with E1 at scale seems safe, with
the operator and insertion questions below folded in.

## Next steps

1. ~~Rerun~~ done.
2. **Fill artifacts in header fields (level 3):** replace an ablated header field with its most common value in the
   training set instead of zero, and compare the curves; report the overshoot beyond full ablation as a diagnostic.
3. **Insertion:** test insertion by contiguous runs and check the IG reference point; decide whether insertion is a
   fair test for per-byte rankings of non-additive features.
4. **E2** at scale once E1 runs on more files and seeds.
