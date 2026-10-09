# 3-B Plan: Finding Real Shortcuts with the Pullback

Started 2026-10-09. An extrinsic application (`PLAN.md`, "Paper structure"): what does a feature-based detector key
on, in the bytes, across a corpus, and can an attacker exploit it? Domain knowledge may be used freely in this
experiment where it helps (user, 2026-10-09); the framework stays domain-agnostic.

## Definitions (decided 2026-10-09)

- **Learned association:** a byte pattern that recurs across files and carries pulled-back credit toward one label.
- **Shortcut:** a learned association that passes the **insertion test**: inserting the pattern into files of the
  other class, without changing what they do, moves the score toward the pattern's label. Whatever the pattern
  "means", an attacker can exploit it, so a practitioner needs to know about it.
- **Focus:** benign-pushing patterns first (evasion, the practitioner's main worry). Malware-pushing patterns are a
  secondary, signature-like output (possibly YARA rules, linking to 3-C).

## Method (kept simple; refine only if needed)

1. **Pull back** the GBDT's TreeSHAP explanation of each file to its bytes (one instrumented extraction per file).
2. **Spans:** per file, the top-k bytes by benign-pushing credit, merged into contiguous spans.
3. **Group by content:** spans with identical bytes are one pattern (exact match first; fixed-length n-gram keys
   only if exact matching fragments the patterns).
4. **Rank** patterns by the number of files they appear in times their mean credit.
5. **Insertion test** on the top patterns: insert into held-out malware (e.g., appended to the end of the file,
   standard in problem-space attacks on MalConv; other placements may use PE knowledge) and measure the drop in the
   malware log-odds and the evasion rate.

**Baselines (no P):** label-skewed byte n-grams mined from the training data (chi² or information gain: correlations
in the *data*, not what the *model* uses; the key baseline); patterns from window-level occlusion (costly, coarse);
random patterns of matched length (control). Global SHAP on features is the status quo, compared qualitatively (it
names hashed or aggregate features, not content).

**Hypothesis:** the GBDT relies on some recurring benign-associated byte content whose insertion lowers malware
scores substantially, and pullback-found patterns move the model more than data-mined or random ones.

## Practitioner output

A **shortcut report** per detector: ranked patterns with their bytes (hex and printable), prevalence by label,
share of the model's credit, the features they act through ((Pᵀ1_S)_j), and the insertion effect. Then:
- **Patch:** neutralize the affected features in proportion to (Pᵀ1_S)_j, or retrain with the pattern inserted into
  training malware; re-run the insertion test and measure clean accuracy.
- **Case studies:** what the top patterns are (our reading; not a user study).

## Scale

Recurring patterns need many files. Start with the 2,000-file explanation set; the user worries even that may be
too few. Pullbacks are cheap (the 2,000-file census, with heavy statistics included, took 30 minutes on 16 workers),
so tens of thousands of test files are feasible (ask before running). Prevalence in the training set (1.3 TB)
needs a sample.

## Decided against

- **Ambiguity as a filter** on which credit may form spans (user, 2026-10-09: forced; do not try to make it work).

## Open

- k per file, span merging, and the minimum number of files for a pattern; how many files are needed.
- Where to insert, and checking that insertion keeps files valid.
- Which reference the explanations use (TreeSHAP's background may bury rare shortcuts).
