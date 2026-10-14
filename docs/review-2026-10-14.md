# Simulated CCS review of the draft (2026-10-14), and how to respond

Written from a CCS reviewer's point of view, on the manuscript as of commit `75d03ea` (pilot numbers; AU realizable).
Part 1 is the review as a reviewer would write it. Part 2 checks every headline claim against its evidence. Part 3 is
the plan: what we can do about each criticism, in order of priority.

## Part 1: the review

### Summary (in the reviewer's words)

The paper observes that each feature of a hand-engineered malware feature extractor (EMBER v3) is computed from
identifiable bytes of the file. By instrumenting the extractor, the authors record a per-file matrix P that says which
bytes produce each feature and in what proportion, plus a "null" row for features no byte produces. Two linear maps
use P: the pullback (b = Pa) moves a feature attribution onto the bytes, and the pushforward (a = PᵀD†b) moves a byte
attribution onto the features. On EMBER-2024 with a LightGBM model and MalConv, the paper (i) measures faithfulness by
deleting top-ranked bytes or features, (ii) checks both maps against a planted backdoor trigger, (iii) uses the
pullback to compare the two detectors file by file, with a "triage" of their disagreements, and (iv) uses the
pushforward to aggregate MalConv's Integrated Gradients over 2,000 files into named header fields, nine of which are
confirmed by scrambling; changing them in loader-safe ways evades MalConv on 12.4% of detected held-out malware, against
6.0% for other loader-ignored fields.

### Strengths

1. **A simple, general idea that fills a stated gap.** FINER explicitly excludes EMBER-style detectors because hashing
   and aggregation seem to make mapping explanations back to the file impossible; the paper shows that recording
   provenance during extraction does it. The two directions through one matrix are elegant, and the pushforward (giving
   a raw-byte model a feature vocabulary it never computes) is the more original half.
2. **Cheap and fine-grained.** One feature extraction per file instead of one per occluded window, and byte resolution
   that occlusion cannot afford.
3. **Careful experimental hygiene.** Perturbed files are verified; ties are broken randomly; comparisons are paired and
   size-matched; the audit's evasion is measured on fresh held-out malware, only on files the detector detects, with
   loader-safe changes and a null of other loader-ignored fields.
4. **Ground truth.** The planted trigger, chosen without an explainer, gives a clean check (6 of 6 trigger bytes at
   the top on every file).
5. **Candid about limits.** The resolution limit of the pushforward, the unattributable features, and the MLP's weak
   explanations are reported rather than hidden.

### Weaknesses

**W1. The technical novelty is thin, and the paper concedes much of it.** The pullback "coincides with G-DeepSHAP's
rule" and claims no novelty for propagation. What remains is (a) instrumenting one extractor, which reads as
engineering, and (b) the pushforward, a row-normalized transpose, justified in one sentence as a Bayesian inverse
that is never used afterwards. With the theory cut, the method section has five definitions and no results; a reviewer
will ask what is hard here, and what a reader learns that they could not have written down in an afternoon. The paper
must make the case that obtaining P for a program is non-trivial (hashes, entropies, counts, strings: which
conventions, and why they are the right ones) and that the pushforward is a real conceptual step.

**W2. The baseline for "byte resolution is out of reach" is too weak.** The claim rests on uniform occlusion, whose
cost grows with the number of windows. A practitioner who wants fine resolution would refine adaptively: occlude
coarse windows, then split only the important ones (hierarchical or binary-search occlusion, as in hierarchical
perturbation methods and hierarchical LIME, which the paper cites). That reaches small windows at roughly logarithmic
cost. A second obvious comparison is an oracle that occludes each parsed PE field with a parser (more manual, but the
natural upper bound). Without these, the 1.67× and "out of reach" claims are exposed.

**W3. The cost comparison leaves out the explainer.** "1/135 of the cost" counts feature extractions only. The
pullback of KernelSHAP needs KernelSHAP, about 45 s per file, more than occlusion's 20 s. The ratio holds for TreeSHAP,
not for every explainer the paper reports.

**W4. Is the byte-level faithfulness win partly by construction?** The pullback ranks exactly the bytes that features
read; deleting those bytes changes the features by design, while any window-based method dilutes its budget over bytes
no feature reads. The result is real, but a reviewer will want to see that it is not just "knowing the parser's read
set" (the PE-field oracle of W2 answers this). The "overshoot" (deleting half the file removes more evidence than
deleting all of it) also raises the question of whether the deletion metric is measuring off-distribution behaviour.

**W5. The pushforward's faithfulness is weak, and it is never tested on the model it is used for.** Pushed-forward
explanations reach only R = 0.31-0.40 of TreeSHAP's deletion area. The argument that the source's resolution is to
blame relies on an "attainable R" that the paper itself calls partly circular. More importantly, the faithfulness test
pushes forward explanations of the GBDT; the application pushes forward MalConv's Integrated Gradients, whose
faithfulness after the pushforward is only checked feature by feature through scrambling. What "faithful" means for a
model that never computes the features should be defined and measured directly.

**W6. The applications' security value is not yet compelling.**
- *Comparison (CM).* The threat model has a defender running both a GBDT and MalConv, but the paper itself says it
  makes no claim that this pair is deployed together. The triage's outcome is not tied to an operational decision:
  what does the defender do differently when the evidence is "blind" vs. "oppose", and is that decision better than
  without triage? Validation is by deletion on 25 files per cell, with two of four cells only descriptive.
- *Audit (AU).* MalConv's reliance on header bytes is well known, and published header attacks (e.g., DOS-header and
  header-field manipulations) evade MalConv far more often than 12.4%. A reviewer will ask what the audit found that was
  not already known, and why a defender should prefer it to the surrogate, which nearly matches it (10.4%; the
  pushforward's margin is 2 points, p = 0.027). The paper avoids the DOS header, which helps, but must say so as a
  finding (reliance beyond the well-known region) and compare with a header attack restricted to the same fields. The
  mitigation is announced but not evaluated, and the modified files are never executed.

**W7. Generality is claimed but not shown.** The method is "domain-agnostic", "any feature extractor", but every
result uses one extractor, one file format, one feature-based model (the MLP's results are weak and secondary), one
raw-byte model, one seed, and mostly 100 files. One extractor in another domain, or at least a second PE extractor,
would change how the paper reads.

**W8. A fifth of the GBDT's attribution cannot be placed.** About 70% of features are unattributable in a typical file
and about 22% of the GBDT's attribution rests on them. This bounds every result and sits in an appendix.

**W9. Presentation.**
- Three full-width conceptual figures (pipeline; feature vs. problem-space explanation; the transfers) for ideas a
  paragraph could carry, while the evaluation has no figure. Figure 3's caption says the transferred explanation is
  "close to" the concrete one, a round-trip claim the paper no longer makes; "tranferred" is misspelled.
- Definitions 1-2 formalize something trivial.
- The results are dense with numbers, many without a reference point.
- Inconsistency: the experimental setting calls the deletion operator "the one place" where experiments use domain
  knowledge; 4.2 calls the trigger "the second place"; the audit's loader rules are a third.
- CM's threat model says the attacker keeps the program running, but its evidence is deletion, which does not.

**W10. Statistics and scale.** 25 files per triage cell, 50 per trigger, 100 for faithfulness, one seed. Many tests
without correction outside the audit. (The scale-up addresses part of this.)

### Recommendation

**Weak reject in the current form (major revision if the cycle allows it).** The idea is good and the experiments are
carefully run, but the paper does not yet show that the method beats what a practitioner would do (W2, W3), that the
pushforward is faithful on the model it is applied to (W5), or that the two applications change a security outcome
(W6). The novelty argument (W1) needs to be made rather than conceded. Most of these are fixable with focused
experiments and rewriting; none requires a new idea.

## Part 2: claims against evidence

| claim (where) | evidence | verdict |
|---|---|---|
| Pullback matches occlusion at 1/135 of its cost (abstract, intro) | Table 1, GBDT, 100 files | supported for TreeSHAP; cost omits the explainer (W3); MLP excluded |
| At byte resolution removes 1.67× the evidence (abstract, intro) | Table 1 | supported against uniform occlusion; needs adaptive and field-level baselines (W2, W4) |
| Direct explanation cannot reach byte resolution (intro, 4.1) | occlusion plateau | overstated until adaptive occlusion is tested (W2) |
| 6 top bytes = trigger bytes on all 50 files (intro) | 4.2 | supported; partly by construction (each field read by one feature) |
| Triage distinction vanishes over windows (abstract, intro) | Table 2, 25 files | supported; small N; no operational outcome (W6) |
| Pushforward faithful up to the resolution of its source (intro, contributions) | Table 3 | partly circular by the paper's own account; not tested on MalConv (W5) |
| 9 of top 20 fields confirmed; 12.4% vs 6.0% evasion (abstract, intro) | 5.3, 902 files | supported; not executed; not compared with known header attacks (W6) |
| Points to its mitigation (contribution 3) | none | unevaluated |
| Applies to any extractor / domain-agnostic (Section 3, discussion, conclusion) | one extractor | stated, not shown (W7) |

Undersold: the audit's fields lie outside the DOS header, beyond the reliance already documented for MalConv; the
paper mentions this in passing rather than as a finding.

## Part 3: what to do about it

Ordered by how much each item reduces rejection risk for its cost. "Run" means a pilot-scale experiment first.

### Must do

1. **Adaptive occlusion and a field-level oracle (W2, W4).** Add two problem-space baselines to 4.1: hierarchical
   occlusion (start at 64 windows, split the top windows recursively down to a few bytes, at a fixed extraction budget)
   and PE-field occlusion (a parser lists the header fields and sections; occlude each). If the pullback still wins or
   matches the oracle from one extraction, the claim becomes much stronger and the "by construction" objection is
   answered (the oracle knows the read set too). If adaptive occlusion closes the gap, the cost argument still stands
   and the "out of reach" wording changes. Code: one new ranking method in `scripts/faithfulness.py`; run on the pilot.
2. **Honest cost accounting (W3).** Report the explainer's time alongside the extractions (TreeSHAP ms, IG ms,
   KernelSHAP ~45 s) and state the ratio per explainer. No new runs; numbers exist.
3. **Pushforward faithfulness on MalConv (W5).** Define it in the problem space, where MalConv lives: rank features by
   the pushed-forward IG, delete the bytes P assigns to the top-k features, and compare with the same budget of bytes
   chosen by (a) the surrogate's ranking mapped through P, (b) IG aggregated over fixed windows, (c) random features.
   This turns the per-feature confirmation into a curve and tests the pushforward where the application uses it.
   Reuses the AU machinery.
4. **Position the audit's finding against known header attacks (W6).** Run a published-style header manipulation
   restricted to the same loader-safe fields (e.g., optimize their values by queries) and the full-DOS-header
   manipulation as a reference point; state plainly that the audit finds reliance *outside* the DOS header and that
   it is automatic. Also evaluate the mitigation (zero the audited fields at test time; retrain), which is already a
   TODO.
5. **Make the novelty case in the text (W1).** In Section 3: what instrumenting a program takes (the conventions for
   counts, hashes, strings, entropies, and why each), what the validation shows (exact for additive features), and
   what is new about the pushforward (moving attribution through a non-invertible program into features the model
   never computes; it conserves attribution; why the normalization by D† is needed, which 5.1 shows empirically). Keep
   theory only where it is measured and useful.

### Should do

6. **A second extractor (W7).** The strongest single addition for the generality claim. Options, cheapest first: a
   second PE feature set (e.g., a header-and-section extractor or byte n-grams), an Android extractor (Drebin-style:
   manifest permissions, API calls), or a PDF extractor. Even only the faithfulness test (4.1) on a second extractor
   would help. If not feasible, narrow the claims to "feature extractors like EMBER's" and keep the general statement
   in the discussion. This is the user's decision.
7. **Tie the triage to a decision (W6, CM).** E.g., plant evasions with a known attack against one detector and show
   the triage labels them differently from organic disagreements (evasion of MalConv via header bytes shows up as
   "oppose" on the header; a GBDT blind spot shows up as "blind"). At minimum, scale to 100 files per cell (run 54
   does this) and validate all four cells.
8. **Execute a sample of the modified files (W6, AU).** A few dozen loader-safe modified files run in a sandbox
   would settle "do they still run" for reviewers. The user earlier judged this unnecessary ("we don't break the
   files"); it is worth reconsidering only because reviewers at CCS routinely ask.
9. **Scale and seeds (W10).** The 500-file runs, then 2,000 files and three seeds on the cluster, as planned.
10. **Unattributable attribution in the body (W8).** One short paragraph in 4.1 (already there) plus a sentence in the
    discussion framing it as a property of the extractor, measurable from P alone. No appendix-only treatment.

### Writing fixes (no experiments)

11. Merge Figures 1 and 2 into one single-column figure, or drop Figure 1; fix Figure 3's caption ("close to") and the
    typo; consider a small evaluation figure later (cost against gain from Table 1 is a natural candidate).
12. Fix the "one place" / "second place" inconsistency: say once, in the setting, that the experiments use format
    knowledge in three places (deletion operator, struct trigger, loader rules) and why.
13. CM's threat model: say that deletion measures where both detectors are cheap to attack, not a working attack
    (as the discussion does), so the section and the discussion agree.
14. Fewer numbers per sentence; give each a reference point (random, occlusion, chance).
15. Related work: say explicitly how the pushforward differs from mapping MalConv saliency onto PE regions with a
    parser (Coull and Gardner; Bose et al.), which is the closest prior practice: theirs is hand-built per format and
    sums bytes into regions; ours splits shared bytes among features automatically for any extractor.

### Things to decide (user)

- Whether to run items 1, 3, 4 now at pilot scale (my recommendation: yes, 1 and 3 first; they are cheap and address
  the most likely rejection reasons).
- Whether to add a second extractor (6), and which.
- Whether to keep the MLP in the body (it supports "the pullback is only as good as its source" but otherwise reads as
  a weak result).
