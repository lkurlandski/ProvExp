# 3-C (revised): Auditing a raw-byte detector through the pushforward

Status (2026-10-13): runs 38-41 done; **no-go** by criterion (a): none of the pushforward's 20 candidates is confirmed
(results below). Next: post-mortem with the user. Replaces the rule-based 3-C
(`docs/rules_plan.md`, on hold), which rested on the pullback and Pᵀ rather than the pushforward.

## Why this task (and why the pushforward)

The pullback's novelty is limited (G-DeepSHAP's rescale rule); the framework's novelty is the symmetry between the two
spaces, so the pushforward needs a purpose of its own (user, 2026-10-12). The symmetry, stated sharply:

- **Pullback:** local explanations of a *feature-based* model, placed in the problem space (per file, byte resolution).
- **Pushforward:** explanations of a *problem-space* model in coordinates shared by every file, so they can be
  **aggregated across a corpus**. Byte offsets mean something different in each file; feature j means the same thing
  everywhere.

A raw-byte detector (MalConv; Microsoft Defender also runs a deep model over full file contents) can be explained per
file (IG), but has no vocabulary in which its reliance recurs across files. Auditing it for shortcuts (reliance on
content that tracks the label but is forgeable and irrelevant to maliciousness; Arp et al.) is a corpus-level task.
This is 3-B's task on the model where 3-B's failure does not apply: 3-B failed because the GBDT's features already have
names, so SHAP plus the names found its shortcuts directly. MalConv has no names.

**Why not MalConv's IG directly?** IG is the right per-file explanation, and it is the pushforward's input. A shortcut
is a claim about many files, and IG cannot be aggregated across files without shared units: by offset works only for the
DOS header (everything after `e_lfanew` moves); by content (n-grams) loses the location (3-B's miner found the
certificate's DER bytes, not the certificate-size field the model used); by parsed structure needs a hand-built mapping
per format (alternative 1). The pushforward supplies the units (the extractor's features), splits shared bytes among
them (D†; better than the naive sum in PF1), and puts MalConv's reliance in the GBDT's vocabulary, so each shortcut can
be checked against the GBDT (a link to 3-A).

## Realistic alternatives (named up front)

1. **Hand-built aggregation** (a PE parser locating header fields, section names, imports, ... in each file, and
   IG summed over them): set aside (user, 2026-10-12): it takes tremendous manual effort for one format; the
   pushforward does it automatically for any extractor.
2. **A surrogate.** A GBDT on EMBER features trained to mimic MalConv's log-odds, explained with TreeSHAP and
   aggregated. No P needed. It finds what *predicts* MalConv, not what MalConv *uses*, so it should yield more
   candidates that the transplant does not confirm.
   Trained on the **test split** outside the explanation set, not on MalConv's training split: only MalConv's test
   predictions are saved, and the surrogate distills MalConv's function, not the labels, so any large set of inputs
   labeled by MalConv will do. The test split is also the explanation set's distribution (EMBER-2024's test files are
   later), so the surrogate mimics MalConv best where it is compared. Relatives of the explanation files (families,
   near-duplicates) may sit in its training pool, which can only favor the surrogate (the safe direction). To state in
   the paper (agreed with the user, 2026-10-12).
3. (Weaker, for context only) coarse region aggregation (header / sections / overlay), as in Demetrio et al. and
   Aryal et al.

## Mock (hypothetical numbers)

> *Paragraph.* We push MalConv's Integrated Gradients forward into the EMBER features of each of 2,000 test files and
> rank features by the share of files in which they carry MalConv's malware or benign evidence. Of the top 20
> candidates, 7 are confirmed shortcuts: writing the benign-associated content at the bytes P names moves MalConv
> toward benign, beyond random content in the same bytes. Forging them together evades MalConv on 4.1% of detected
> malware at 1% FPR. Four of the seven (an imported runtime library, a path-string category, two section properties)
> lie in content a field-level parser cannot place; a surrogate GBDT trained on MalConv's scores ranks only two of the
> seven in its top 20, and 9 of its candidates are not confirmed. Three of the shortcuts are also relied on by the
> GBDT (3-A), so they weaken both members of the ensemble.

| candidate feature | files carrying MalConv's credit | confirmed (transplant) | evasion when forged | in surrogate's top 20 | GBDT relies on it |
|---|---|---|---|---|---|
| `datadirectories:debug_size` | 31% | yes | 1.2% | yes | yes |
| `imports:library_hash_k` (a runtime DLL) | 18% | yes | 0.8% | no | no |
| `strings:regex_paths` | 12% | yes | 0.4% | no | no |
| `section:props_hash_k` (a section name) | 9% | no | n/a | yes | yes |
| … | | | | | | |

**Operator per column:**

| column | operator |
|---|---|
| candidate feature, files carrying credit | **pushforward** (aggregated over files) |
| confirmed, evasion when forged | none (problem-space validation; bytes named by P's column, as in 3-B) |
| in surrogate's top 20 | none (alternative 2) |
| GBDT relies on it | none (TreeSHAP on the GBDT, same vocabulary) |

The claim rests on the first column. The validation columns use no P (the transplant uses P only to find where to
write, as in 3-B). The claim holds only if confirmed shortcuts appear that the surrogate misses.

## Strongest objections

1. **The surrogate finds the same.** Then the pushforward is not needed. The go/no-go tests this first.
2. **Everything is in the DOS header.** MalConv's reliance on it is known (Demetrio et al.); if every confirmed shortcut
   lies there, the finding is weak.
3. **Body evidence smears.** For files MalConv alone flags, 77% of its evidence lies in the body (3-A triage); pushed
   forward, it lands on the histogram and entropy features, where "MalConv relies on the byte histogram" is not a
   finding. That is PF1's resolution limit, stated as such.
4. **IG on MalConv is noisy** (3-A: its deletion overshoots). Every finding is validated by transplant, not by IG.
5. **A shortcut needs a forgeable, label-skewed value**, not only reliance on a feature. The candidate rule groups by
   (feature, content), as in 3-B's discovery, not by feature alone.

## Go/no-go (fixed 2026-10-12, before any run)

Corpus: the 2,000-file explanation set (user). MalConv seed 0, IG with 256 steps (as in 3-A); its IG was not saved by
runs 30-32 and is recomputed.

1. **Discovery** (`scripts/audit_discover.py`): per file, MalConv's IG pushed forward through the file's P; the top
   features by benign credit; each keyed by (feature, content), content = the bytes of the feature's provenance when
   they are few (otherwise the feature alone); candidates = the top 20 keys by files x mean credit among those in
   >= 10 files (3-B's rule).
2. **Surrogate** (`scripts/audit_surrogate.py`): a LightGBM regressor on EMBER features predicting MalConv's log-odds,
   trained on test files outside the explanation set (MalConv's saved test predictions, seed 0); interventional
   TreeSHAP on the explanation set; the same keys and rule (`audit_discover.py` builds both).
3. **Confirmation**: 3-B's transplant (`scripts/shortcuts_transplant.py`) with MalConv as the scored model, on every
   candidate of step 1 that has content (3-B's criterion: >= 20 applicable files, median drop and median paired effect
   over random content in the same bytes >= 0.1 log-odds, one-sided Wilcoxon p < 0.05/n).
4. **No-go if** (a) no candidate is confirmed, or (b) the surrogate's top 20 contain at least half of the confirmed
   candidates.

Hypothesis: MalConv's top candidates are mostly header and data-directory fields (its header reliance is known), with
a few in imports and section names; the surrogate recovers the header ones but not the hashed ones. If every confirmed
candidate is in the DOS header, the go stands but the finding is weak (Demetrio et al. reported it).

## Implementation (2026-10-12; runs 38-41, not yet run)

- `run/38` the surrogate (`scripts/audit_surrogate.py`); `run/39` MalConv's IG on 4 GPUs; `run/40` discovery
  (`scripts/audit_discover.py`, both sources); `run/41` the transplant scored by MalConv
  (`scripts/shortcuts_transplant.py --scorer malconv`), for the pushforward's candidates and the surrogate's.
- A feature's *content*: among the maximal runs of its provenance, the run that passes the most of MalConv's IG to it
  (sum over the run of b_i P_ij / D_ii, which sums to the pushforward over the runs); for the surrogate, which has no
  byte explanation, the run holding the most provenance. Supports of more than 256 runs, or a chosen run longer than
  256 bytes, are *aggregates* (no content; reported separately, with their share of the credit: objection 3).
- Smoke tests (6 files): the pipeline runs end to end; IG's completeness gap about 0.005 log-odds; the surrogate on
  only 4,500 files already reaches R^2 0.90 (Spearman 0.95) on held-out files, so it is a serious competitor. On these
  files, MalConv's pushed-forward top features are mostly entropy and histogram aggregates, as objection 3 expects.
- Known wrinkle: several hashed features of one field (e.g., three `section:characteristics_hash_*` reading the same 4
  bytes) form separate patterns with the same content, so they can take several of the 20 slots. Same for both sources;
  left as is.

## Results so far

- **Run 38 (surrogate):** 484,094 training files, 2 min. Fidelity: R^2 0.96 and Spearman 0.98 held out; R^2 0.95,
  Spearman 0.97, sign agreement 0.95 on the explanation set. A strong competitor: criterion (b) is a real test.
- **Run 39 (MalConv IG):** 2,000 files, 33 min on 2 GPUs; completeness gap median 0.009, max 0.03 log-odds.
- **Run 40 (discovery):** 7 min. MalConv pushed forward: 67 patterns in >= 10 files. Aggregates (no content) take 25%
  of a file's benign credit (median), 70% of what its top 20 features hold (pooled); the surrogate's, 17% and 31%
  (objection 3, as expected). The top content patterns: the DOS stub message (1,265 files), optional-header fields
  (SizeOfUninitializedData, BaseOfCode, SizeOfCode, ImageBase, NumberOfRvaAndSizes), runs of zeros named by byte-entropy
  windows, section characteristics (`0x40000040`, `0x42000040`, several hashed copies), one Rich header pair. The
  surrogate's: optional-header fields, data-directory sizes (debug, security), imports, certificate URLs.
- **Run 41 (transplant scored by MalConv), 191 malware:** **pushforward's candidates: 0 of 20 confirmed.** Most move
  MalConv by exactly 0 for both the content and random bytes (section characteristics, entropy zero runs, Rich header:
  MalConv's global max-pool ignores most 4-byte edits); the DOS message applies to 1 file (present in 160); the best,
  BaseOfCode, has effect 0.09 (threshold 0.1). Surrogate's candidates: 1 of 20 confirmed,
  `datadirectories:security_size` `0x2820` (effect 0.15, p 2e-19; its `0x2838` sibling 0.09).
- **Go/no-go: no-go** by criterion (a): no candidate of the pushforward is confirmed. The surrogate, the competitor,
  found the only confirmed shortcut, and it is not in the DOS header.
- **Post-mortem diagnostic (run 42, `scripts/audit_inplace.py`; 2026-10-13).** Which link broke: (1) IG's credit is
  real in the file it explains, (2) the pushforward makes it recur, or (3) the content carries over to another file?
  For the 20 candidates, in up to 200 files each where discovery found them (1,358 occurrences, 696 files), the
  credited bytes were removed *in place*. Hypothesis (stated before the run): holds for header fields, fails for the
  zero runs and section flags. **Wrong: it holds for all 20.** Removing the bytes raises MalConv's malware log-odds by
  a median 0.46 (padding) or 0.50 (random bytes), against an IG credit of 0.44 (Spearman 0.66 across occurrences);
  >= 0.1 in 90-100% of files for 19 candidates (66% for the DOS message). Control: random bytes of the same length
  elsewhere in the same 512-byte MalConv window change it by a median -0.01 (paired difference 0.54), so the credit is
  specific to the bytes, not to the window. **So links 1 and 2 hold; link 3 breaks**: removing the content where MalConv
  found it costs benign evidence, but writing it into malware gives none. Likely why: MalConv keeps, per channel, only
  the strongest window, and a window's response depends on the content's offset within it and on the rest of the
  window; a benign file's peak needs its whole context, so the 4 bytes alone do not rebuild it elsewhere. Not separated
  (offset vs. context) by this run.

## What carries over

3-B's machinery (`scripts/shortcuts*.py`): discovery by (feature, content), transplant at P's column, the training
prevalence check, forging and evasion at 1% FPR. 3-A's MalConv loading and IG. PB1's perturbation operator.

## Decisions (user, 2026-10-12)

- The mock passed screening; the go/no-go requires a confirmed shortcut, since confirming one is cheap.
- Hand-built aggregation with a PE parser is not a realistic alternative (tremendous manual effort); ignored.
- Discovery uses the 2,000-file explanation set, as in 3-B.
- Mitigation for MalConv is out of scope.
