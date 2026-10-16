# Strengthening Section 3 (opened 2026-10-16)

Answer to W1 of `docs/review-2026-10-14.md` (thin technical novelty). Two theoretical pillars for Section 3, a go/no-go
for the second, and case-study ideas parked for later. Nothing here is in the manuscript yet.

## Decisions so far (user, 2026-10-16)

- **Coarsening leaves Section 3** (done): the Granularity paragraph and P^G now live in the new Section 4,
  "Experimental Setup" (`manuscript/_d_setup.tex`, "Windows of Bytes"), as an experimental device only. The
  experiments that use it are unchanged for now. The "theory of resolution" idea is dropped.
- **Not touched yet** (user is thinking): the black-box P (leaning: keep it as a short subsubsection after the
  Shapley-grounded construction, maybe an appendix later) and the GBDT window-pushforward test (a lab study need not be
  realistic).
- **New Section 4, "Experimental Setup"**, between the method and the pullback: a holding area for EMBER's
  instrumentation (Table 1), data, models, explainers, the deletion operator, and windows. Refine later.
- **Leaning nonnegative P** (see the analysis below); not final.
- **Axiomatic uniqueness of the transfers: dropped** (close to definitional given P).

## Pillar A: provenance of a program, grounded in Shapley values

A tight, clean subsection, not a long one. Goal: replace hand conventions with a principled target and rules.

- **Target.** The ideal P_ij is element i's Shapley value in feature j (the game: which elements are present),
  divided by the feature's total change from its baseline, Δσ_j. This is the matrix for which G-DeepSHAP's rescale
  rule is exact.
- **Calculus.** Rules for primitive operations (read a field, count items, hash items into buckets, sum, normalize,
  max, entropy); composing stages multiplies their matrices (T2).
- **Theorem (additive programs).** For features additive in the elements (fields read directly, counts, hashed
  counts), the instrumented P equals the Shapley target exactly (T1).
- **Theorem (pullback exactness).** If the model is linear over such features, the pullback of the feature Shapley
  values equals the Shapley values of the whole pipeline over the elements (G-DeepSHAP's linear-chain result,
  specialized to programs); for nonlinear models, the gap is the interaction terms.
- **Where it is a stated approximation:** normalizing stages (EMBER's byte histogram is counts / file size), entropy,
  and other non-monotone primitives (see the signed-P analysis).

### Signed or nonnegative P

What a negative entry would mean: element i's presence moves feature j *against* the feature's overall change from
the baseline. Under the Shapley target this happens wherever an element enters a feature only to dilute it:
- EMBER's byte histogram is normalized (bin v = count of v / file size), so every byte that is *not* v lowers bin v.
  Under Shapley, every byte has a (negative) share of all 255 other bins: P becomes dense for 256 features.
- Entropy: a byte equal to the window's dominant value lowers its entropy.
- Ratios among the string features (e.g., a share of printable characters) behave like the histogram.

Pros of signed P:
- It is the exact Shapley target, so the pullback-exactness theorem covers more features.
- Its support is literal influence (denominators included), which resolves the tension between Definition 3's
  Influence axiom and the instrumentation conventions (S1 in `docs/review-sections-3-5-2026-10-14.md`).

Cons, most serious first:
1. **It breaks the pushforward's foundations.** Row sums D_ii can be zero or negative, so D† is undefined or
   explodes; columns are no longer distributions, so the Bayes reading fails; EM needs nonnegativity; and
   M = PᵀD†P is no longer positive semidefinite, so the iterated pushforward (Pillar B) loses its convergence
   guarantee. Fixable only by replacing the operators (e.g., unweighted least squares), which loses "today's
   pushforward is the first step".
2. **Undefined columns.** When a feature equals its baseline (Δσ_j = 0) its Shapley values may still be nonzero, and
   the division fails (a known weakness of the rescale rule).
3. **Density.** Normalized features read every byte, so their credit smears over the whole file.
4. **Cost.** Shapley values of entropy windows and string statistics need sampling or symmetry arguments per window.
5. **Readability.** "This byte produces 30% of the feature" becomes "this byte lowers the feature".

Nonnegative P keeps every property of both transfers (conservation, the Bayes reading, EM, M positive semidefinite,
convergence) and states the approximation once: normalizing and non-monotone stages are mapped to their data flow
(the bytes a feature is computed from), not their signed influence. With the calculus, this is a single, visible
place: the normalizing stage after an exact counting stage. Recommendation: nonnegative.

## Pillar B: the pushforward as an inverse problem

- **Idea.** Pushing forward means finding the feature explanation a whose pullback Pa reproduces the byte
  explanation b. Today's ψ(b) = PᵀD†b splits each byte's credit among its features without looking at other bytes.
- **Iterated pushforward (signed).** a₁ = ψ(b); a_{k+1} = a_k + ψ(b − P a_k): push forward what the current answer's
  pullback leaves unexplained. It converges to the solution of M a = ψ(b), M = PᵀD†P (weighted least squares; the
  Landweber series for M⁻¹; M's eigenvalues lie in [0, 1], archived Proposition "Round Trips"). Each iterate conserves
  attribution. Starting from zero it returns the minimum-norm answer among tied features.
- **Nonnegative variant.** EM / Richardson–Lucy, whose first step from a uniform start is exactly ψ(b).
- **One step is exact** when no two features share an element (M = I; the archived perfect-reconstruction theorem).
- **Identifiability.** The answer is unique iff the provenance columns are linearly independent; features with
  identical provenance (App-R) are never separable. File-wide features are linearly dependent on the byte histogram's
  bins, so they stay at the even split.
- **Tie to Pillar A.** If a model factors through additive features linearly, the elements' Shapley values are P times
  the features' Shapley values, so the iterated pushforward recovers the feature Shapley values when identifiable.
- **Only the pushforward.** The pullback runs along the chain rule (feature credit to the elements a feature is
  computed from) and is exact under Pillar A's conditions; there is nothing to invert. The pushforward runs against
  it, which is why it needs an inverse. The symmetry of the paper becomes: the chain rule, and its inverse.
- **Risks.** Noise amplification along small eigenvalues of M (early stopping or a ridge term); a closer fit may not
  mean more faithful (decided by deletion on MalConv).

### Go/no-go (agreed 2026-10-16; not yet run)

Known-answer test on the GBDT, pilot files: pull back TreeSHAP to the bytes, recover it with one step vs. the
iteration, and score both by the feature-space deletion area relative to TreeSHAP (R). Hypothesis: R rises from 0.80
toward 1, minus what non-identifiable features hold. Fails if the iteration gains little over one step. If it passes:
the MalConv deletion test (runs 58/60) and the audit's candidates with the iterated pushforward.

What would re-run if it passes: only the pushforward half (pushforward faithfulness, the MalConv test, the audit's
discovery, confirmation, evasion and mitigation). The pullback experiments do not change.

## Parked ideas (case studies, possibly later; not considered further for now)

- **Bounding what control of a byte set can do** (for the pullback's side: it uses which features an arbitrary byte
  set S feeds, Pᵀ1_S, and verifies the GBDT over those features). Pairs with the audit: can the GBDT provably not be
  moved by the fields MalConv relies on? A sound bound needs control provenance (pointers, normalizers) as well as
  data provenance. Could introduce its own theory as a case study.
- **Naming a raw-byte model's internal units** (for the pushforward's side). MalConv's max-pooling gives each channel
  an exact one-window provenance per file; composing with EMBER's P maps channels to feature names without labeled
  concepts, and could support a channel-level mitigation. Odds are limited mainly by MalConv's 512-byte windows, not by
  the feature set; better with a model with smaller receptive fields, or features that read small contiguous spans.
