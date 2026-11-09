# Strengthening Section 3 (opened 2026-10-16)

Answer to W1 of `docs/reviews/explanation-provenance/2026-10-14-self-review.md` (thin technical novelty). Two theoretical pillars for Section 3, a go/no-go
for the second, and case-study ideas parked for later. Both pillars are in Section 3 of the manuscript (2026-10-16).

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

**In the manuscript (2026-10-16):** Section 3.3 (Definition Shapley Provenance, Proposition Additive Features, the
data-flow convention, why nonnegative, the black-box estimate as 3.3.1) and Section 3.4 (Proposition Exact Pullback;
Definition and Proposition Exact Pushforward). Key modeling choice: the game over elements holds each feature's
*context* fixed (the parse that locates its items, denominators such as the file size); an item is present iff all its
elements are. Under it, fields, counts, histograms over a fixed denominator, and one-sign hashed counts are additive,
so instrumentation equals the Shapley provenance; entropies, averages, ratios of item-dependent quantities, and
min/max get the data-flow convention. (This supersedes the "normalized histogram dilutes" example below: with the
denominator held fixed, the byte histogram is additive.)

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
  Influence axiom and the instrumentation conventions (S1 in `docs/reviews/explanation-provenance/2026-10-14-sections-3-5.md`).

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

### Go/no-go (agreed 2026-10-16; run 61 done, see "Result" below)

Known-answer test on the GBDT, pilot files: pull back TreeSHAP to the bytes, recover it with one step vs. the
iteration, and score both by the feature-space deletion area relative to TreeSHAP (R). Hypothesis: R rises from 0.80
toward 1, minus what non-identifiable features hold. Fails if the iteration gains little over one step. If it passes:
the MalConv deletion test (runs 58/60) and the audit's candidates with the iterated pushforward.

What would re-run if it passes: only the pushforward half (pushforward faithfulness, the MalConv test, the audit's
discovery, confirmation, evasion and mitigation). The pullback experiments do not change.

### Result (run 61, 100 pilot files, seed 0; `artifacts/logs/pf_inverse-seed0.log`)

R = feature-deletion area of the recovered explanation / the explainer's own (ablated reference; background in
parentheses), interventional TreeSHAP; the other two explainers agree within 0.01-0.02.

| | one step | 16 iterations | 256 iterations | limit (CG) | CG better than one step |
|---|---|---|---|---|---|
| bytes | 0.796 (0.723) | 0.838 | 0.849 | 0.862 (0.770) | 93/100 files, p = 7e-17 |
| 256 windows | 0.364 (0.366) | 0.390 | 0.414 | 0.436 (0.427) | 84/100 files, p = 1e-13 |

- The gain is consistent (every explainer, both references, most files) but modest: at bytes, the iteration closes
  about a third of the gap between one step and 1 (0.80 -> 0.86). The hypothesis "toward 1" is not met.
- Why it stops: the limit reproduces the byte explanation exactly (residual ~1e-9) but still misses 37% of the
  feature explanation (relative L1 error). The remaining gap is non-identifiability: features whose provenance the
  bytes cannot tell apart, which no method can separate. One step leaves both kinds of loss; the iteration removes
  the separable kind only.
- Verdict: a qualified go. The theory (inverse problem, identifiability) explains the measured gap; the algorithm
  helps reliably but not dramatically. Two cheap checks decide how far to take it: (1) the identifiability ceiling
  (merge features with identical provenance; is the limit near it?); (2) the MalConv deletion test with the limit
  instead of one step, where the audit actually uses the pushforward.

### The ceiling and MalConv (runs 62, 63, 2026-10-16)

**Run 62, identifiability ceiling** (`run/62_pf_ceiling.sh`, `scripts/pf_inverse.py --name ceiling`; 12 min). The
exact pushforward (cg) is already the projection of the native explanation onto P's row space (Proposition Exact
Pushforward (iii)), so a projection is no ceiling. Instead, a "twins" oracle restores the native split inside groups of
features with identical provenance columns (cg splits them evenly), a null-space move that no method can make from the
bytes. R, interventional TreeSHAP (other explainers within 0.02), ablated reference (background in parentheses):

| | one step | exact (cg) | twins oracle |
|---|---|---|---|
| bytes | 0.80 (0.72) | 0.86 (0.77) | 0.95 (0.85) |
| 256 windows | 0.36 (0.37) | 0.44 (0.43) | 0.86 (0.79) |

- At bytes, a median of 55 features per file have a twin and hold 17% of |TreeSHAP|; restoring their split closes about
  two thirds of the exact pushforward's remaining gap (hypothesis "near 0.95": met). The last 0.05 is linear dependence
  beyond twins.
- At 256 windows, twins (217 features, 60% of |TreeSHAP|) explain nearly all of the gap (0.44 -> 0.86). The hypothesis
  "much less than at bytes" failed: coarsening mostly creates twins (features inside the same windows).
- Reading: the exact pushforward loses little beyond what is unrecoverable in principle, and the unrecoverable part sits
  in small groups of features read from the same bytes, which an analyst can report as one unit.

**Run 63, MalConv** (`run/63_pf_malconv_exact.sh`, `scripts/pf_malconv.py --exact`; 14 min). Median deletion area:
exact 6.25, one step 6.25 (60/100 files favor exact, p = 0.005, median ratio 1.00), both 1.9x the surrogate (exact
100/100, one step 99/100); the other rankings reproduce run 58 exactly. Hypothesis "a small, consistent gain": not met;
no practical gain where the audit uses the pushforward. IG over a raw-byte model is not the pullback of any feature
explanation, so there is no hidden feature explanation for the inverse to recover; one step and the exact form rank the
same features.

**Verdict (user, 2026-10-16):** the experiments keep the one-step pushforward; nothing reruns. Section 3 keeps
Definition 7 and Proposition 3 as theory (what any pushforward can recover, and that one step is its first step); the
pushforward-faithfulness section reports the exact form (0.86, twins 0.95) and the MalConv tie in two sentences.

## Parked ideas (case studies, possibly later; not considered further for now)

- **Bounding what control of a byte set can do** (for the pullback's side: it uses which features an arbitrary byte
  set S feeds, Pᵀ1_S, and verifies the GBDT over those features). Pairs with the audit: can the GBDT provably not be
  moved by the fields MalConv relies on? A sound bound needs control provenance (pointers, normalizers) as well as
  data provenance. Could introduce its own theory as a case study.
- **Naming a raw-byte model's internal units** (for the pushforward's side). MalConv's max-pooling gives each channel
  an exact one-window provenance per file; composing with EMBER's P maps channels to feature names without labeled
  concepts, and could support a channel-level mitigation. Odds are limited mainly by MalConv's 512-byte windows, not by
  the feature set; better with a model with smaller receptive fields, or features that read small contiguous spans.
