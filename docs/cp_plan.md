# CP: Characterizing Provenance (Plan)

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
definitions (the old pilot report, in git history; the CP preview in `docs/pb1_pilot.md`) are marked as such.

## Purpose (unchanged)

The statistics characterize P: from P alone, how sharply and how separately a transferred explanation can be placed.
They are not predictors of a particular explanation's faithfulness.

## Why the current statistics are replaced

The user's two axes stay: **spread** (how sharply one feature can be placed) and **sharing** (how separately different
features can be placed). The definitions change:

- The unambiguity and nonoverlap theorems are near-tautologies (entropy is 0 iff one-hot; O = 0 iff no element feeds
  two features).
- The perfect-reconstruction theorems are the substantive results, but their conditions (H = 0, O = 0) are
  all-or-nothing, and real provenance never meets them (pilot: H ≈ 0.99, O ≈ 0.003). They say nothing about P that
  falls short of the ideal.
- The normalizations saturate: Ĥ_j = H_j / log|A_j| measures uniformity within the support, not spread; O divides by
  about 800 features.

## The round-trip matrices

Notation as in the manuscript: P is (m + 1) × n and column-stochastic (with the null element), D = diag(row sums),
pullback b = Pa, pushforward a = PᵀD†b. Let B = (D†)^½ P.

- **Pull, then push:** M = PᵀD†P = BᵀB (n × n). M_kj is the share of feature j's attribution that a round trip
  through the elements lands on feature k: a **feature confusion matrix**.
- **Push, then pull:** N = PPᵀD† ((m + 1) × (m + 1)). Column i is where element i's attribution lands after a round
  trip through the features: an **element blur kernel**.

### Propositions (proof sketches; to be written out and checked with property-based tests)

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

## The statistics, in dual pairs

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

## Check: does M_jj saturate? (2026-10-08, 100 PB1 files, scratch script)

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

## CP experiments (CP.1–CP.4)

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

## Implementation (after agreement)

- `provexp/provenance.py` (domain-agnostic): `Provenance.round_trip()` returning the diagonal of M, the diagonal of N,
  and the effective supports; `Provenance.confusion(groups)` for the block matrix; `Provenance.resolution(w)`;
  exact computations from the pieces (the diagonal of M needs only a prefix sum of 1/D), never materializing N.
- Property-based tests for P1–P4 and the corollaries (`tests/test_provenance.py`, with `tests/strategies.py`).
- A census script (or an extension of `provenance_census.py`) and an `cp_tables.py`.

## Decisions (2026-10-08)

1. **Definitions:** replace, keeping the names (above). Code, tests, docs, and manuscript must never carry two
   definitions; results under the previous ones are labeled.
2. **Spectrum:** compute it in the census for our own insight; not in the paper unless the analysis changes our minds
   (the user is skeptical that it buys much).
3. **Resolution vs. PB1's sweep:** decided after the baselines run; resolution stays in the census either way.

Guiding principle (user): be very selective about when, where, and why complexity is introduced; a broad framework
with strong mathematical properties is the priority.
