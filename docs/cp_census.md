# CP Census: The Revised Statistics on the Explanation Set

Run 2026-10-08 (`scripts/provenance_census.py --seed 0`, definitions of 2026-10-08; tables from
`scripts/cp_tables.py --seed 0`, plus the per-feature arrays). Plan and definitions: `docs/cp_plan.md`. The previous
census (previous definitions) is in `census-2026-10-07/`.

## Run

2,000 files, 0 failures, 2 with the known hash-seed mismatch in `pefilewarnings`. 1.4 s per file (median), 47 s max;
30 minutes on 16 workers (the old progress bar did not advance; fixed).

## Findings

**1. Overlap is informative per feature; as a file-level summary it is narrow.** Within a file, the attributable
features' O_j span 0.05 to 0.82 (10th to 90th percentile, median over files), median 0.35. The overall O of a file
lies in 0.29–0.46 (10th–90th) and correlates weakly with size (ρ = −0.39). The most-overlapping features are the
global aggregates computed from the same bytes as many others (`strings:entropy`, `strings:printables`,
`strings:avlength`, `strings:numstrings`, `general:size`, `general:entropy`; O ≈ 0.98–0.99 in every file).

**2. Subsets in isolation: overlap separates structure from content.**

| subset | effective support (elements) | overlap O (10th / 50th / 90th) | element coverage | N_ii |
|---|---|---|---|---|
| header | 2 | 0.34 (constant) | 0.04% | 0.25 |
| datadirectories | 4 | 0.08 (constant) | 0.03% | 0.25 |
| general | 1 | 0.17 (constant) | 100% | ≈ 0 |
| authenticode | 8 | 0.82 (constant) | 0.01% | 0.12 |
| richheader | 8 | 0.14 / 0.18 / 0.44 | 0.004% | 0.12 |
| section | 12 | 0.54 / 0.58 / 0.68 | 99.8% | ≈ 0 |
| imports | 27 | 0.43 / 0.50 / 0.67 | 0.12% | 0.04 |
| strings | 107 | 0.10 / 0.14 / 0.20 | 6.4% | 0.003 |
| byteentropy | 288 | 0.11 / 0.19 / 0.27 | 100% | ≈ 0 |
| histogram | 440 | 0 | 100% | ≈ 0 |

Where the overlap of a subset is constant across files (header, data directories, general, authenticode), it is a
property of the extractor's design (which fields are read from shared bytes), not of the file; where it varies
(section, imports, strings, entropy windows, Rich header), it describes the file. The histogram's bins partition the
bytes, so its overlap in isolation is exactly 0.

**3. The confusion matrix is stable and readable** (mean over files; share of a subset's attribution that a round
trip lands on each subset; diagonal, then the largest leaks):

| from | stays | largest leaks |
|---|---|---|
| header | 0.96 | general 0.02 |
| datadirectories | 0.95 | authenticode 0.04 |
| imports | 0.87 | strings 0.08 |
| richheader | 0.87 | histogram 0.07, byteentropy 0.06 |
| section | 0.79 | histogram 0.09, byteentropy 0.07 |
| exports | 0.78 | strings 0.11, byteentropy 0.06 |
| histogram | 0.74 | byteentropy 0.17, strings 0.05 |
| strings | 0.73 | histogram 0.12, byteentropy 0.07, imports 0.05 |
| authenticode | 0.61 | datadirectories 0.14, histogram 0.11 |
| byteentropy | 0.60 | histogram 0.31 |
| general | 0.44 | header 0.22, histogram 0.19, byteentropy 0.10 |

It matches the 100-file check, and benign and malware files agree except for authenticode (0.49 vs. 0.73).

**4. The round-trip bound holds for every file and explainer and is within about 1.5× of the error.**

| explainer | files | error / ‖a‖₁ (median) | bound / ‖a‖₁ (median) | error / bound (10th / 50th / 90th) |
|---|---|---|---|---|
| path TreeSHAP | 2,000 | 0.69 | 0.97 | 0.67 / 0.71 / 0.77 |
| interventional TreeSHAP | 2,000 | 0.64 | 0.94 | 0.64 / 0.68 / 0.74 |
| KernelSHAP (GBDT) | 100 | 0.61 | 0.93 | 0.61 / 0.65 / 0.72 |
| IG (MLP) | 2,000 | 0.64 | 1.09 | 0.55 / 0.59 / 0.64 |
| KernelSHAP (MLP) | 100 | 0.66 | 1.09 | 0.56 / 0.59 / 0.65 |
| gradient × input (MLP) | 2,000 | 0.69 | 1.12 | 0.57 / 0.62 / 0.69 |

From P alone, the bound anticipates how much of any explanation a pull–push round trip loses, within a factor of
about 1.4–1.7, for six explainers of two models. A pull–push round trip loses 60–70% of the attribution mass, mostly
to the most-overlapping features.

**5. Ambiguity in elements is mostly file size.** The overall H correlates with size at ρ = 0.85 (effective support
ρ = 0.76); malware has larger effective supports (median 210 vs. 73 elements) because its files are larger (median
792 KB vs. 160 KB). Per subset, the content features scale with size (histogram ρ = 0.84, strings 0.77, entropy 0.64)
and the structural ones do not (section −0.01, imports 0.20, header constant). Effective support is therefore best
reported per subset (or as a fraction of the file, which shrinks with size, ρ = −0.63); the overall H mixes the two.

**6. The spectrum adds little.** The share of eigenvalues above 0.99 (median 9% of the attributable features) tracks
the share of features with O_j < 0.01 (7%) at ρ = 0.96, so the top of the spectrum restates the diagonal. The only
new information is the bottom: about 10% of the eigenvalues are below 0.01, i.e., attribution patterns over the
features that a round trip (almost) erases, the generalization of App-R's duplicate features. Consistent with the
user's skepticism: keep it out of the paper unless App-R needs it.

**7. Element-side statistics are informative per subset only** (as in the check): for the full set every element
feeds the histogram (coverage 1, N_ii ≈ 4e-4).

## Implications

- The paper's CP evidence: the per-subset table (effective support, overlap, coverage), the confusion heatmap, and the
  bound's tightness across explainers. All three come from P alone, and the bound connects them to what happens to
  real explanations.
- Report effective support per subset, not the overall H. Overall O can be reported, but per-feature and per-subset
  overlap carry the information.
- The spectrum stays a diagnostic (possibly App-R's near-zero share).

## Next steps

1. **The statistics track P** (`docs/cp_plan.md`, CP.3): compute them on P coarsened to PB1's window counts
   (cheap, from P alone) and on the black-box P. The black-box P is not saved by `faithfulness.py`; save it in the PB1
   runs at scale instead of a separate occlusion run.
2. **Resolution at granularity w:** after the baselines decision (`docs/pb1_baselines.md`), which says whether the
   comparison with PB1's sweep is worth making.
3. **Reporting (decide with the user):** effective support per subset rather than the overall H; the confusion heatmap
   as the headline figure; the bound's tightness as the link to real explanations.
4. **Spectrum:** dropped from the paper unless App-R uses the near-zero share.

## Coarsening (CP.3, part 1; 2026-10-08)

`scripts/cp_coarsening.py` on the 100 PB1 files (the baselines files), full provenance, path TreeSHAP for the round
trip; medians over files. Granularity 0 is the elements (bytes) themselves.

| granularity | mean overlap O | effective support (in units) | round-trip error / ‖a‖₁ | bound / ‖a‖₁ | error / bound |
|---|---|---|---|---|---|
| bytes | 0.41 | 85 bytes | 0.70 | 0.99 | 0.70 |
| 4,096 windows | 0.90 | 38 windows | 1.12 | 1.82 | 0.63 |
| 1,024 windows | 0.96 | 20 windows | 1.15 | 1.92 | 0.62 |
| 256 windows | 0.98 | 10 windows | 1.17 | 1.96 | 0.60 |
| 64 windows | 0.99 | 5 windows | 1.16 | 1.98 | 0.59 |

Per subset, the mean overlap rises from 0.14–0.71 at byte level (data directories 0.14, histogram 0.29, header 0.37,
strings 0.40, section 0.71) to 0.86–0.99 at 4,096 windows and 0.97–0.99 at 256.

- **As predicted, and by much.** Coarsening never lowers overlap and never raises ambiguity (property-tested,
  `tests/test_ablation.py`). Already at 4,096 windows (about 50 bytes each for the median file), nearly every
  window holds bytes of many features (the histogram and entropy windows cover every window; a header window holds all
  header fields), so a round trip through windows loses more than the explanation's whole mass (error > ‖a‖₁; the
  trivial bound is 2).
- **Reading with PB1 (to discuss):** at 256 windows, the pullback ranks windows as well as occlusion does (PB1), yet the
  window-level P is almost fully confused (O ≈ 0.98): a window explanation says *where*, but no longer *which feature*.
  Byte level keeps that (O = 0.41). This is a P-only argument for byte-level pullbacks that does not depend on the
  deletion results.

Part 2 (the black-box P at the window level) is saved by `faithfulness.py` from now on (`provenance.npz`:
`overlap_{instrumented,blackbox}`, `ambiguity_{instrumented,blackbox}`); it comes with the PB1 runs at scale. The
comparison is `scripts/cp_blackbox.py` (2026-10-09), first run on `run/17_pf1_window_scores.sh`'s output
(`run/19_cp_blackbox.sh`). Ambiguity is a property of one column, so it must agree where the columns agree; overlap
depends on every feature reading the same windows (through D), so it can differ even there.

## CP.3 results: instrumented vs. black-box P at 256 windows (2026-10-09; `run/19_cp_blackbox.sh`)

From run 17's `provenance.npz` (100 pilot files, level 3, zero fill); report `artifacts/reports/cp_blackbox.md`.
Per subset, over (file, feature) pairs attributable under both:

| subset | median TV | effective support (windows): instr. / black-box | ambiguity agrees | overlap: instr. / black-box |
|---|---|---|---|---|
| header | 0 | 1 / 1 | 0.99 | 0.993 / 0.986 |
| histogram | 1.6e-6 | 76 / 77 | 0.88 | 0.992 / 0.993 |
| datadirectories | 0 | 1 / 1 | 0.85 | 0.993 / 0.989 |
| richheader | 0 | 1 / 1 | 0.84 | 0.993 / 0.988 |
| section | 0 | 1 / 1 | 0.67 | 0.992 / 0.987 |
| strings | 0.44 | 18 / 49 | 0.13 | 0.986 / 0.993 |
| byteentropy | 0.61 | 11 / 42 | 0.03 | 0.974 / 0.989 |
| imports | 0.60 | 1.6 / 3 | 0.0004 | 0.990 / 0.995 |
| exports | 0.67 | 1.9 / 5 | 0.02 | 0.974 / 0.991 |
| authenticode | 0.38 | 21 / 8 | 0 | 0.993 / 0.989 |
| all | 0.13 | 15 / 35 | 0.43 | 0.988 / 0.992 |

- **Ambiguity tracks P where T1 says.** Additive groups agree (header 0.99; histogram, data directories, Rich header
  0.84–0.88); the exceptions are explained: `histogram:byte_00` disagrees on all 100 files (zero fill adds counts to
  bin 0), and the section disagreements are its entropy-derived features (`max_entropy`, entropy hashes), which are
  not additive. Non-additive groups disagree almost everywhere, and the black-box P is *more spread*: 2-4x the
  effective support for strings, entropy windows, and hashed imports/exports (occluding part of a string or a name
  changes or moves it rather than removing a share). Authenticode is the one group the black-box sees as sharper.
- **Overlap agrees almost nowhere (3%), even where the columns agree (4%)**, as expected: O_j depends on every
  feature reading the same windows through D. Its *level* barely moves (0.988 vs. 0.992): at 256 windows overlap is
  saturated near 1 under either P, so at this granularity it cannot distinguish them. Overlap is informative at the
  byte level (0.41), where the black-box P cannot be estimated.
- CP.3 is therefore done at the pilot: the statistics computed from a black-box P agree with the instrumented ones
  exactly where T1 says the provenance agrees, and the disagreement elsewhere is in the direction of a more diffuse P.
