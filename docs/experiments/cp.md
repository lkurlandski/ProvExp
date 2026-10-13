# CP: Characterizing the Provenance Matrix

Experiment CP. Characterizing the provenance matrix: design (Plan) and the 2,000-file census (Census results).

## Plan

Drafted 2026-10-08 with the user. See `PLAN.md` (CP).

**Adopted 2026-10-08** (decision 1, option (a)) in the code (`Provenance.ambiguity`, `overlap`, `push_pull_diagonal`,
`pull_push_matrix`; cyclic errors in L1), the tests, the scripts, the docs, and the manuscript. The names stay:

- **ambiguity** H_j = −Σ_i P_ij log P_ij (unchanged), with effective support exp(H_j); overall H = mean of H_j over the
  attributable features (no normalization);
- **overlap** O_j = 1 − Σ_i P_ij² / D_ii = 1 − M_jj, the share of feature j's attribution that a pull–push round trip
  moves to other features; overall O = mean over the attributable features. Defined as one minus self-identifiability
  so that the name keeps its direction (0 = no sharing) and the theorem "pull–push perfect iff O = 0" keeps its form.

In the manuscript: Proposition Round Trips (P1 without the spectrum, P2, P3), Theorem Round-Trip Bounds (P4), and the
two perfect-reconstruction theorems as its corollaries; the two near-tautological theorems are removed. The shared
spectrum of M and N is not in the manuscript (decision 2); the tests check it. Results computed with the previous
definitions (the old pilot report, in git history; the CP preview in `docs/experiments/pb1.md`) are marked as such.

### Purpose (unchanged)

The statistics characterize P: from P alone, how sharply and how separately a transferred explanation can be placed.
They are not predictors of a particular explanation's faithfulness.

### Why the current statistics are replaced

The user's two axes stay: **spread** (how sharply one feature can be placed) and **sharing** (how separately different
features can be placed). The definitions change:

- The unambiguity and nonoverlap theorems are near-tautologies (entropy is 0 iff one-hot; O = 0 iff no element feeds
  two features).
- The perfect-reconstruction theorems are the substantive results, but their conditions (H = 0, O = 0) are
  all-or-nothing, and real provenance never meets them (pilot: H ≈ 0.99, O ≈ 0.003). They say nothing about P that
  falls short of the ideal.
- The normalizations saturate: Ĥ_j = H_j / log|A_j| measures uniformity within the support, not spread; O divides by
  about 800 features.

### The round-trip matrices

Notation as in the manuscript: P is (m + 1) × n and column-stochastic (with the null element), D = diag(row sums),
pullback b = Pa, pushforward a = PᵀD†b. Let B = (D†)^½ P.

- **Pull, then push:** M = PᵀD†P = BᵀB (n × n). M_kj is the share of feature j's attribution that a round trip
  through the elements lands on feature k: a **feature confusion matrix**.
- **Push, then pull:** N = PPᵀD† ((m + 1) × (m + 1)). Column i is where element i's attribution lands after a round
  trip through the features: an **element blur kernel**.

#### Propositions (proof sketches; to be written out and checked with property-based tests)

**P1 (structure).** M is symmetric, nonnegative, doubly stochastic, and positive semidefinite, so its eigenvalues lie
in [0, 1]. N is column-stochastic on the live elements (D_ii > 0), reversible with respect to D (ND = PPᵀ is
symmetric), and similar on them to BBᵀ. Hence **M and N have the same nonzero eigenvalues**: the spectrum describes
both directions at once.
*Sketch.* Symmetry and nonnegativity from the form. Column sums: Σ_j M_jk = Σ_i D_ii D†_ii P_ik = 1, because
P_ik > 0 implies D_ii > 0. Doubly stochastic and nonnegative ⇒ ‖M‖₁ = 1 ⇒ |λ| ≤ 1; M = BᵀB ⇒ λ ≥ 0. Σ_i' N_i'i =
Σ_j P_ij / D_ii = 1. On live elements, D^{-½} N D^{½} = BBᵀ, and BBᵀ and BᵀB share nonzero eigenvalues.

**P2 (self-identifiability).** For every feature, M_jj = Σ_i P_ij² / D_ii ≤ 1, with equality iff every element in the
support of column j feeds no other feature. For an unattributable feature, M_jj = 1/|U|.
*Sketch.* P_ij ≤ D_ii ⇒ P_ij²/D_ii ≤ P_ij; summing gives M_jj ≤ Σ_i P_ij = 1, with equality iff D_ii = P_ij on the
support. The null element's row has a 1 in each of the |U| unattributable columns.

**P3 (element self-identifiability).** For every live element, N_ii = Σ_j P_ij² / D_ii ≤ 1, with equality iff every
feature that element i touches is one-hot on i.
*Sketch.* Σ_j P_ij² ≤ Σ_j P_ij = D_ii, with equality iff each P_ij ∈ {0, 1}.

**P4 (round-trip bounds).** For every feature-space explanation a and every problem-space explanation b supported on
live elements:

    ‖a − Ma‖₁ ≤ 2 Σ_j |a_j| (1 − M_jj)        ‖b − Nb‖₁ ≤ 2 Σ_i |b_i| (1 − N_ii)

with equality for one-hot explanations.
*Sketch.* Column j of I − M has L1 norm (1 − M_jj) + Σ_{k≠j} M_kj = 2(1 − M_jj), since M is column-stochastic and
nonnegative; the triangle inequality over columns gives the bound. The same holds for N.

**Corollaries (the current perfect-reconstruction theorems).** For explanations of the attributable features,
pull–push is perfect iff M_jj = 1 for every attributable j iff O = 0. Push–pull is perfect iff N_ii = 1 for every
live element iff H = 0. (⇐ by P4; ⇒ by applying the round trip to one-hot explanations.) So the round-trip statistics
contain the current theorems as their all-or-nothing case.

**What M depends on (replaces the earlier caveat).** Written out, M_kj = Σ_i P_ij P_ik / Σ_l P_il: a function of P
alone, with no separate choice in it. D† is still needed in the *pushforward* itself, because without it an element
would hand out D_ii times its attribution instead of exactly its attribution (mass would not be conserved). The
pushforward is not an arbitrary choice either: read column j of P as a distribution over elements, P(i | j); then
P_ik / Σ_l P_il is Bayes' rule, P(k | i), under the assumption that every feature is equally likely a priori. So:

- the pushforward is the Bayesian inverse of the pullback under a uniform prior over features;
- M_kj is the probability of landing on feature k when one draws an element from feature j's provenance and then a
  feature from that element's posterior, i.e., the probability that the problem space mistakes j for k;
- M_jj is the probability that feature j is recovered from its own elements.

The only assumption to state in the paper is the uniform prior, and it is the pushforward's own. (An attribution-
weighted prior would make M depend on the explanation, which we want to avoid.)

### The statistics, in dual pairs

> **Status (2026-10-09).** The round-trip matrices M and N and their bounds stay, as theory in the framework. The
> standalone census of ambiguity and overlap is not a contribution unless a use is found (open: `PLAN.md`, "Open
> questions"). Coverage and the null element's share are not contributions at all (`CLAUDE.md`; `docs/appendix.md`).

| question | pullback side (features) | pushforward side (elements) |
|---|---|---|
| How much can be localized at all? | coverage κ (attributable features) | element coverage: share of elements with D_ii > 0 |
| How spread? (*ambiguity*) | effective support exp(H_j), in elements and as a fraction of the input | row effective support: exp of the entropy of row i of D†P (how many features one element's attribution splits into) |
| How separately? (*overlap*) | self-identifiability M_jj; confusion between feature subsets (blocks of M) | N_ii; the blur kernel |
| How much can be told apart? | the spectrum of M (shared with N): eigenvalues near 1 survive a round trip, the kernel of P is invisible in the problem space (App-R's duplicate features are the simplest case) | |
| How local? (ordered inputs; explore cautiously) | resolution at granularity w: ρ_j(w) = max_s Σ_{s ≤ i < s+w} P_ij | |

Names: "ambiguity" and "overlap" could be kept for the new definitions (effective support and self-identifiability);
the user decides.

**Resolution at w** needs element order, a generic property of sequential inputs (agreed 2026-10-08 to explore it
cautiously). It connects to coarsening (T3): coarsening to windows of w elements is lossless for the placement of any
feature whose column fits in one window.

### Check: does M_jj saturate? (2026-10-08, 100 PB1 files, scratch script)

Computed exactly from P (M's columns sum to 1 within 4e-11; M·a matches `Provenance.pull_push` within 6e-10).

- **M_jj does not saturate.** Within a file, the attributable features' M_jj span 0.16 (10th percentile) to 0.96
  (90th); the median is 0.63 (0.52–0.79 across files). No attributable feature reaches 1 in any file.
- **It separates the subsets** (median M_jj; median effective support exp(H_j) in elements):

  | subset | M_jj | effective support |
  |---|---|---|
  | datadirectories | 1.00 | 4 |
  | header | 0.99 | 2 |
  | richheader | 0.90 | 8 |
  | histogram | 0.75 | 223 |
  | general | 0.66 | 1 |
  | strings | 0.63 | 64 |
  | byteentropy | 0.45 | 250 |
  | imports | 0.42 | 27 |
  | section | 0.26 | 12 |
  | authenticode | 0.11 | 8 |

  Spread and sharing are distinct: `general` has an effective support of 1 element but M_jj = 0.66 (its elements also
  feed header features); the histogram is spread over 223 elements but fairly self-identifiable (0.75).
- **The confusion between subsets is informative** (mean share of a subset's attribution, placed uniformly on its
  attributable features, that a round trip lands on each subset; diagonal and largest off-diagonal entries):

  | from | stays | largest leaks |
  |---|---|---|
  | header | 0.96 | general 0.02 |
  | datadirectories | 0.95 | authenticode 0.04 |
  | imports | 0.86 | strings 0.09 |
  | richheader | 0.84 | histogram 0.10 |
  | section | 0.79 | histogram 0.09, byteentropy 0.07 |
  | histogram | 0.72 | byteentropy 0.18, strings 0.06 |
  | strings | 0.71 | histogram 0.14, byteentropy 0.07, imports 0.06 |
  | authenticode | 0.61 | datadirectories 0.14, histogram 0.10 |
  | byteentropy | 0.57 | histogram 0.32 |
  | general | 0.44 | header 0.22, histogram 0.19, byteentropy 0.11 |

- **The bound P4 is informative and fairly tight** for path TreeSHAP restricted to the attributable features: the
  round-trip error is 0.70 ‖a‖₁ at the median, the bound 0.99 ‖a‖₁ (the trivial bound is 2 ‖a‖₁); error / bound has
  a median of 0.70 (0.67–0.77).
- **The element-side statistics saturate for the full feature set, but not per subset.** Element coverage is 1.00 in
  every file, because the histogram counts every byte. N_ii has a median of 5e-4: most elements feed only diffuse
  features, so their attribution comes back spread out. Per subset in isolation they are informative: element
  coverage 9% (strings), 0.07% (header), 0.2% (imports); N_ii = 0.25 for header and data-directory fields (a 4-byte
  field returns a quarter to each byte), 0.12 for authenticode and the Rich header. So element-side statistics are
  reported per subset, or as distributions over elements, not as a single file-level summary.

### CP experiments (CP.1–CP.4)

1. **CP.1. Census of the statistics** (P only, all 2,000 files, about 10 minutes on 16 workers): per subset, the
   distributions of effective support, M_jj, element coverage, N_ii, and ρ_j(w); the subset confusion matrix (blocks
   of M) as the headline figure; the spectrum of M (eigenvalues near 1, effective rank).
2. **CP.2. Operational check:** round trips of real explanations (path and interventional TreeSHAP, KernelSHAP) and random
   explanations; the bound P4 and its tightness per explainer and file.
3. **CP.3. The statistics track P:** compare the instrumented P, the black-box P, and P coarsened to windows (all from PB1).
   Coarsening merges elements, so self-identifiability must fall and effective support (in elements) shrink; the
   black-box P should differ where T1 says (the non-additive groups).
4. **CP.4. Resolution vs. PB1's sweep (to discuss):** ρ_j(w) at the window sizes of PB1's occlusion sweep says how much of a
   feature's placement survives coarsening to that granularity; PB1's sweep shows how much of the deletion
   performance survives. A consistency check between what P permits and what the model uses, not a prediction of
   faithfulness.

### Implementation (after agreement)

- `provexp/provenance.py` (domain-agnostic): `Provenance.round_trip()` returning the diagonal of M, the diagonal of N,
  and the effective supports; `Provenance.confusion(groups)` for the block matrix; `Provenance.resolution(w)`;
  exact computations from the pieces (the diagonal of M needs only a prefix sum of 1/D), never materializing N.
- Property-based tests for P1–P4 and the corollaries (`tests/test_provenance.py`, with `tests/strategies.py`).
- A census script (or an extension of `provenance_census.py`) and an `cp_tables.py`.

### Decisions (2026-10-08)

1. **Definitions:** replace, keeping the names (above). Code, tests, docs, and manuscript must never carry two
   definitions; results under the previous ones are labeled.
2. **Spectrum:** compute it in the census for our own insight; not in the paper unless the analysis changes our minds
   (the user is skeptical that it buys much).
3. **Resolution vs. PB1's sweep:** decided after the baselines run; resolution stays in the census either way.

Guiding principle (user): be very selective about when, where, and why complexity is introduced; a broad framework
with strong mathematical properties is the priority.

## Census results

Run 2026-10-08 (`scripts/provenance_census.py --seed 0`, definitions of 2026-10-08; tables from
`scripts/cp_tables.py --seed 0`, plus the per-feature arrays). Plan and definitions: `docs/experiments/cp.md`. The previous
census (previous definitions) is in `census-2026-10-07/`.

### Run

2,000 files, 0 failures, 2 with the known hash-seed mismatch in `pefilewarnings`. 1.4 s per file (median), 47 s max;
30 minutes on 16 workers (the old progress bar did not advance; fixed).

### Findings

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

### Implications

- The paper's CP evidence: the per-subset table (effective support, overlap, coverage), the confusion heatmap, and the
  bound's tightness across explainers. All three come from P alone, and the bound connects them to what happens to
  real explanations.
- Report effective support per subset, not the overall H. Overall O can be reported, but per-feature and per-subset
  overlap carry the information.
- The spectrum stays a diagnostic (possibly App-R's near-zero share).

### Next steps

1. **The statistics track P** (`docs/experiments/cp.md`, CP.3): compute them on P coarsened to PB1's window counts
   (cheap, from P alone) and on the black-box P. The black-box P is not saved by `faithfulness.py`; save it in the PB1
   runs at scale instead of a separate occlusion run.
2. **Resolution at granularity w:** after the baselines decision (`docs/experiments/pb1.md`), which says whether the
   comparison with PB1's sweep is worth making.
3. **Reporting (decide with the user):** effective support per subset rather than the overall H; the confusion heatmap
   as the headline figure; the bound's tightness as the link to real explanations.
4. **Spectrum:** dropped from the paper unless App-R uses the near-zero share.

### Coarsening (CP.3, part 1; 2026-10-08)

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

### CP.3 results: instrumented vs. black-box P at 256 windows (2026-10-09; `run/19_cp_blackbox.sh`)

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
