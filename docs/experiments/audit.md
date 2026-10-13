# AU: Auditing a Raw-Byte Detector Through the Pushforward

Status (2026-10-13): runs 38-41 done; **no-go** by criterion (a): none of the pushforward's 20 candidates is confirmed
(results below). Next: post-mortem with the user. Replaces the rule-based 3-C
(`docs/graveyard.md`, on hold), which rested on the pullback and Pᵀ rather than the pushforward.

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
be checked against the GBDT (a link to CM).

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
> GBDT (CM), so they weaken both members of the ensemble.

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
3. **Body evidence smears.** For files MalConv alone flags, 77% of its evidence lies in the body (CM triage); pushed
   forward, it lands on the histogram and entropy features, where "MalConv relies on the byte histogram" is not a
   finding. That is PF1's resolution limit, stated as such.
4. **IG on MalConv is noisy** (CM: its deletion overshoots). Every finding is validated by transplant, not by IG.
5. **A shortcut needs a forgeable, label-skewed value**, not only reliance on a feature. The candidate rule groups by
   (feature, content), as in 3-B's discovery, not by feature alone.

## Go/no-go (fixed 2026-10-12, before any run)

Corpus: the 2,000-file explanation set (user). MalConv seed 0, IG with 256 steps (as in CM); its IG was not saved by
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

## Second framing: scrambling what detection rests on (2026-10-13; go/no-go passed, runs 43-44)

After the no-go and run 42 (MalConv's credit holds in place, specifically, but forged content does not transfer), the
user approved the framing: instead of *forging benign evidence* (which needs transfer), *destroy malware evidence*.
Push MalConv's IG for malware forward, aggregate over the corpus, and find the features MalConv's detection rests on;
in other malware, overwrite the bytes P names for those features with random bytes. Nothing has to transfer: each file's
own bytes are scrambled. The task is an audit of a raw-byte detector's fragility: which recurring, cheap-to-change
content does its detection rest on, and how much does scrambling it cost the detector? The pushforward's role is the
same as before: per-file IG cannot be aggregated across files without shared units, and the pushforward supplies them.

**Mock (hypothetical numbers).**

> *Paragraph.* We push MalConv's IG on 1,000 malware forward into the EMBER features and rank features by how many
> files carry MalConv's malware evidence on them. In 191 held-out malware, scrambling the bytes each file's P assigns
> to each of the top 20 lowers MalConv's malware log-odds beyond scrambling as many bytes elsewhere in the same MalConv
> windows for 9; 6 lie past the DOS header, beyond the reach of the known DOS-header attacks (the checksum, the
> debug and certificate directory entries, section flags). Scrambling the 6 loader-ignored ones together lowers
> MalConv's log-odds by a median 2.1 and evades it on 8% of detected malware at 1% FPR (DOS-header attack alone: 5%;
> both: 14%). A surrogate GBDT trained on MalConv's scores ranks only 2 of the 9 in its top 20; its own top 20
> confirm 3. Three of the 9 also carry the GBDT's evidence (CM), so scrambling them weakens both detectors.

| feature | malware files carrying MalConv's evidence | median drop, scrambled vs. elsewhere | past the DOS header | loader ignores it | in surrogate's top 20 | GBDT relies on it |
|---|---|---|---|---|---|---|
| `header:optional_header_CheckSum` | 31% | 0.21 vs 0.01 | yes | yes | no | yes |
| … | | | | | | |

| recipe (scramble together) | median drop | evasion at 1% FPR |
|---|---|---|
| pushforward's confirmed, loader-ignored | 2.1 | 8% |
| surrogate's confirmed, loader-ignored | | |
| random features, same number of bytes | | |
| DOS-header attack (known) / with the pushforward's | | 5% / 14% |

**Operator per column:** malware files carrying evidence = **pushforward**, aggregated; drop and evasion = none
(validation; P's column of each target locates the bytes, for every row alike, so the comparison isolates discovery);
past the DOS header, loader ignores it = none (domain knowledge inside the experiment, for reading only); surrogate =
none (alternative 2); GBDT relies on it = none (TreeSHAP). The claim rests on the first column and on the pushforward's
recipe beating the surrogate's.

**Screening.** (1) Needs P: the pushforward aggregates per-file IG into shared units; P also locates each feature's
bytes per file, including hashed features. (2) Task: auditing a detector's robustness before deployment (red-teaming,
MLSEC-style evasion). (3) Alternatives: the surrogate (the strongest, given P for location); offset aggregation works
only before `e_lfanew`; the known DOS-header attacks as the reference attack. (4) Go/no-go below. (5) Not a re-pitch:
the user approved it. (6) Mock above.

**Objections and risks (from what we know).**
1. *The surrogate ties or wins* (main risk). It already found the only confirmed shortcut (run 41); with R^2 0.95 its
   attributions are close to MalConv's function in EMBER's units, and both land on header fields. A 24-file smoke test
   (60 discovery files, not a result) leaned the same way: the surrogate's candidates (certificate-directory entries,
   signing time) moved MalConv more.
2. *Small per-field effects.* About 0.1-0.3 log-odds each against malware log-odds of ~10; evasion needs combinations.
3. *Functionality.* Verification is parse-only. Many candidates (data-directory addresses, ImageBase, Subsystem) break
   the program if changed; the attack reading needs a loader-ignored subset (a hand-made list, inside the experiment).
4. *Novelty of the attack.* Header manipulations against MalConv are known (Demetrio et al.; gym-malware's actions).
   The contribution is the automatic, corpus-level audit for any extractor, not the attack.
5. *DOS header.* Findings only before `e_lfanew` repeat Demetrio et al.

**Go/no-go (proposed 2026-10-13; to be fixed by the user before run 44).** Discovery in the malware direction (run 43);
per source, the top 20 features by malware files x mean credit among those found with content in >= 10 malware files.
Scramble test on the 191 held-out malware of run 41 (`scripts/audit_scramble.py`, run 44), confirmed by the
transplant's rule (>= 20 files; median drop and median paired difference vs. elsewhere >= 0.1; Wilcoxon p < 0.05/20).
**No-go if** (a) no pushforward candidate is confirmed outside the DOS header region (its bytes before `e_lfanew` in
at least half the files), or (b) the surrogate's top 20 contain at least half of the pushforward's confirmed
candidates. Hypothesis: mostly header and data-directory fields; a few confirmed outside the DOS region; (b) is the
likely failure.

**Results (runs 43-44, 2026-10-13). Go.** Discovery: aggregates take 19% of MalConv's malware credit per file (median;
25% in the benign direction). The pushforward's top 20 are optional-header and data-directory fields (plus the DOS
message, `num_sections`, and `e_lfanew`, which cannot be tested: no locatable bytes or no parse). In 191 held-out
malware, **9 of the pushforward's 20 are confirmed, all outside the DOS region** (criterion (a) passes); effects are
small, 0.10-0.24 log-odds beyond the control each. **The surrogate's top 20 contain 4 of the 9** (CheckSum, ImageBase,
debug directory address, Subsystem): just under half, so (b) passes narrowly. The surrogate's own top 20 also confirm
9, with larger effects for some (certificate-directory entries, signing time, DLL flag: 0.13-0.52). Hypothesis: (a)
as predicted; (b) predicted to fail, did not. Caution for the reading: most confirmed pushforward fields hold zero in
most files (empty data-directory entries), close to the "reliance on absence" reading the user has rejected; to discuss.

## The experiment proper (planned 2026-10-13; go passed)

After the go, the user approved building the full experiment. Four parts, three of them built and smoke-tested (runs
45-46 and the per-candidate run 44); mitigation is deferred.

1. **The audit table (run 44, done).** Per confirmed feature: the malware files carrying MalConv's evidence (the
   pushforward, aggregated), the per-feature scramble drop vs. the same bytes elsewhere, whether it is past the DOS
   header, and whether the surrogate's top 20 and the GBDT also rely on it. The surrogate column is the realistic
   alternative and may be dropped: the pushforward is the simpler technique (no second model to train), and matching
   the surrogate is enough (user, 2026-10-13: "the pushforward does as well as this other thing").

2. **Combined effect and evasion (run 46, `scripts/audit_evade.py`).** In the 191 held-out malware, scramble each
   recipe's features together (pushforward-confirmed; surrogate-confirmed; their union; and, as the null, as many
   random locatable fields drawn per file) and measure MalConv's median drop and its evasion rate at the 1% FPR
   threshold (1.9766, from `cm_disagreement_select`). Hypothesis: the discovered recipes drop the score and evade more
   than the random recipe; the union most. **Risk to watch (24-file smoke, not a result):** the random recipe (drawn
   from the discovered header/directory fields) was close behind, so scrambling arbitrary header fields may do nearly
   as much. If so, the finding is "MalConv's detection rests broadly on header/directory fields," still a real audit
   result, but less about the specific features. Consider widening the random pool to all locatable features.

3. **Mitigation (deferred, user 2026-10-13).** Zero the confirmed fields for every file. To showcase both: (a) zero at
   test time with the current MalConv and check detection at 1% FPR holds (cheap); (b) retrain MalConv with those
   fields zeroed (a GPU job in the SSViT pipeline; no training script here). Deferred together until the user takes up
   the PyTorch/GPU work.

4. **Global comparison of the two detectors (run 45, `scripts/cm_global.py`).** MalConv's IG pushed forward into the
   EMBER features of all 2,000 files, reduced to per-feature global reliance (mean |attribution| and mean signed),
   compared feature by feature with the GBDT's interventional TreeSHAP. Shows which weaknesses the ensemble shares.
   This is the pushforward's global counterpart to CM's per-file pullback comparison, and **replaces Appendix F**
   (the old per-file feature-space comparison; to remove from the manuscript and `PLAN.md`, user 2026-10-13).
   Aggregates (histogram, byte-entropy; no locatable bytes) are reported separately (PF1's resolution limit).
   Hypothesis: header and data-directory fields appear in both detectors' top features (as CM found at the byte
   level); MalConv diverges onto the whole-file byte-entropy and histogram aggregates. **The 40-file smoke confirmed
   the shape:** MalConv's top reliance is dominated by byte-entropy/histogram aggregates, the GBDT's by localizable
   header/directory fields; the overlap is in the header fields.

## Results of the experiment proper (runs 44-46, 2026-10-13)

The experiment panned out: the pushforward's confirmed fields evade MalConv more than random header fields, and the
global comparison gives a named feature-level finding MalConv had no vocabulary for. (Mock re-checked: each run still
feeds the column that needs its operator; the pushforward is essential to the MalConv side.)

- **Audit table (run 44):** 9 of the pushforward's top 20 features confirmed, all outside the DOS region; the
  surrogate's top 20 hold 4 of the 9. Per-field scramble effects 0.10-0.24 log-odds.
- **Combined evasion (run 46), 191 held-out malware, MalConv's 1% FPR threshold:** scrambling together the
  pushforward-confirmed fields (9 fields, 34 bytes) drops MalConv's log-odds by a median 3.0 and evades on **22.5%** of
  detected malware; the surrogate-confirmed (9) 2.6 and **24.6%**; their union (14) 4.2 and **35.1%**; the random
  control (9 random locatable header/directory fields per file) 1.9 and **16.5%**. The smoke-test worry did not hold:
  the discovered recipes beat the random one by 6-8 points, though ~16% of evasion comes from scrambling arbitrary
  header fields. Pushforward ~= surrogate (the realistic alternative), as the user expected.
- **Global comparison (run 45), all 2,000 files:** 2,214 of 2,568 features are aggregates (no locatable bytes).
  MalConv puts 64% of its global importance (mean |attribution|) on aggregates, the GBDT 51%. MalConv's largest
  reliance is on whole-file byte-entropy and histogram statistics plus the DOS-stub string; the GBDT's is on nameable
  header and data-directory fields. **Among the 354 localizable features the two detectors' importance rankings barely
  agree (Spearman 0.10; 0.63 over all features, inflated by the shared near-zero tail).** Their top-10 localizable
  features overlap in only 1 (the checksum); top-25 in 6; top-50 in 18. The checksum is each detector's #2 localizable
  field: a shared weakness. Several fields MalConv ranks high are ones the GBDT nearly ignores (SizeOfHeapReserve,
  the global-pointer/copyright/export directory addresses, often zero): the "reliance on empty entries" the user reads
  as a finding, and the kind of named reliance only the pushforward can surface for a raw-byte model. Hypothesis held:
  both lean on header/directory fields (as CM found at the byte level), MalConv diverges onto the aggregates.

**Takeaways for the write-up.** (i) The application stands on the pushforward: MalConv has no feature-space explanation
without it, so neither the global comparison nor the audit table exists for a raw-byte model otherwise. (ii) The
localizable finding (weak rank agreement; only the checksum shared at the top) is the pushforward's distinctive
contribution, beyond CM's byte-level "both rely on the header." (iii) Report aggregate dominance as the stated
resolution limit, not a finding. Since it panned out, remove Appendix F (user, 2026-10-13).

## What carries over

3-B's machinery (`scripts/shortcuts*.py`): discovery by (feature, content), transplant at P's column, the training
prevalence check, forging and evasion at 1% FPR. CM's MalConv loading and IG. PB1's perturbation operator.

## Decisions (user, 2026-10-12)

- The mock passed screening; the go/no-go requires a confirmed shortcut, since confirming one is cheap.
- Hand-built aggregation with a PE parser is not a realistic alternative (tremendous manual effort); ignored.
- Discovery uses the 2,000-file explanation set, as in 3-B.
- Mitigation for MalConv is out of scope.

## Held-out evasion and realizability (run 47, 2026-10-13)

**Why.** Writing the paper surfaced three problems with run 46's evasion numbers: (1) the rate counted 12 of 191 files
MalConv does not detect at its 1% FPR threshold (detected-only, run 46 gives pushforward 17.3%, surrogate 19.6%, union
30.7%, random 11.3%, not the 22.5/24.6/35.1/16.5% in the draft); (2) 434 of 955 random draws broke the parse and were
dropped, so the null was conditioned differently from the recipes; (3) run 46 used exactly run 44's 200 files, on which
the fields were confirmed (selection on the evaluation set). And the paper's threat model says the attacker keeps the
program running, which scrambling does not check.

**Design (run 47).** `scripts/audit_evade.py` with `--detected_only --random_retries 20 --realizable --exclude <run 44
files>`: 1,000 fresh held-out test malware (not in the explanation set, not in run 44), of which 902 are detected
at the threshold. Random draws that break the parse are redrawn. Realizable recipes change only what the Windows loader
lets an attacker change (domain knowledge inside the experiment, `FREE` / `CONSTRAINED` in the script): free fields
(CheckSum except native images; debug, global-pointer, copyright, certificate-table entries; export directory for
executables only; PointerToSymbolTable, DOS message, SizeOfCode, SizeOfUninitializedData, MinorLinkerVersion,
certificate contents) are scrambled; constrained fields (ImageBase only with relocations, 64K-aligned; Subsystem GUI <->
console; heap/stack sizes consistent with commit) take a value drawn from 50,000 benign training files of the same
machine type; loader-critical fields (the IAT directory among the confirmed nine; the DLL flag among the surrogate's)
are left alone. Null for the realizable recipes: `random_free`, as many free fields of the candidate pool as
`pushforward_realizable` changes (7.3 on average), drawn per file. Both nulls draw from pools that contain the confirmed
fields themselves, so they are conservative. Paired by file: bootstrap 95% CIs, McNemar exact (fixed recipes) or
Wilcoxon (vs. random). Took 5.6 min on 12 workers.

**Hypotheses.** (1b) pushforward 15-18%, random 10-12%, significant at ~1,000 files; pushforward ~ surrogate. (1a) the
realizable pushforward recipe keeps >= 2/3 of its evasion and stays above its null.

**Results (902 detected held-out malware, seed 0).**

| recipe | fields | evasion [95% CI] | median drop |
|---|---|---|---|
| union | 13.9 | 30.6% [27.6, 33.7] | 4.23 |
| pushforward | 9.0 | 19.7% [17.2, 22.4] | 2.96 |
| surrogate | 8.9 | 19.0% [16.4, 21.6] | 2.65 |
| union, realizable | 11.2 | 18.4% [15.9, 21.0] | 2.92 |
| pushforward, realizable | 7.3 | 12.4% [10.3, 14.6] | 1.84 |
| random (null) | 9.0 | 12.3% [10.6, 14.1] | 2.01 |
| random free fields (null) | 7.3 | 10.9% [9.2, 12.7] | 1.84 |
| surrogate, realizable | 7.2 | 10.4% [8.5, 12.5] | 1.57 |

Paired: pushforward - random **+7.5 pts [+5.7, +9.2], p = 3e-14**; surrogate - random +6.7 [+4.9, +8.5]; union - random
+18.3; pushforward - surrogate +0.8 [-1.1, +2.7], p = 0.48. Realizable: pushforward - random_free **+1.5 [-0.0, +3.0],
p = 0.17 (not significant)**; surrogate - random_free -0.5 (n.s.); union - random_free **+7.5 [+5.9, +9.1], p = 2e-16**;
pushforward_realizable - surrogate_realizable +2.0 [+0.3, +3.8], p = 0.027. Restricting to realizable changes costs the
pushforward recipe 7.3 pts (70 vs. 4 discordant files).

**Reading.** (1b) holds and is stronger than the pilot claim: on fresh, detected malware the pushforward's fields beat
random fields by 7.5 points with a tight CI, and match the surrogate's. The draft's numbers must change (22.5 -> 19.7,
16.5 -> 12.3, 24.6 -> 19.0, 35.1 -> 30.6). (1a) **fails for the pushforward recipe alone**: once restricted to what the
loader allows, it is no better than as many random free fields (whose pool includes its own free fields). The union of
the two methods' fields stays well above its null when realizable (18.4% vs. 10.9%). Not yet known: whether the loss
comes from excluding the IAT entry or from writing benign rather than random values into ImageBase / Subsystem /
SizeOfHeapReserve (i.e., MalConv reacting to *abnormal* values), and how the null behaves when it excludes the recipe's
own fields. Two cheap follow-ups (~6 min each) would settle both; see `docs/status.md`.

### Decomposition and a cleaner null (run 48, 2026-10-13)

Same 1,000 files as run 47 (902 detected), plus `--decompose`. Hypotheses: most of the realizable loss comes from
benign instead of abnormal values; the IAT entry matters little; the free fields alone beat an unconfirmed null modestly.

| step | recipe | evasion [95% CI] | paired step |
|---|---|---|---|
| A | pushforward, all nine fields, random bytes | 19.7% [17.2, 22.4] | |
| B | minus loader-critical (IAT) and per-file skips, random bytes | 16.3% [14.0, 18.7] | A - B +3.4 [2.0, 5.0], p = 6e-6 |
| C | B with valid (benign) values in the constrained fields = realizable | 12.4% [10.3, 14.6] | B - C +3.9 [2.4, 5.4], p = 4e-7 |
| D | free fields alone | 9.8% [7.9, 11.8] | C - D +2.7 [1.2, 4.1], p = 5e-4 |
| null | free fields of the pool that no source confirmed | 4.4% [3.2, 5.7] | C - null **+8.0 [6.1, 9.9], p = 3e-13**; D - null +5.3, p = 4e-11 |

`random_free` (run 47's null) beats the unconfirmed null by 6.5 pts: the free pool had 16 fields, 9 of them confirmed by
one of the two sources, so run 47's null was largely made of the treatment. Against the clean null, the realizable
union evades 18.4% vs. 4.4% (+14.0, p = 2e-26). Realizable pushforward vs. realizable surrogate: +2.0 [0.3, 3.7],
p = 0.027 (run 47). 12 of 902 files had no parsing draw of the unconfirmed null (60 unparsed draws in all).

**Reading.** Hypotheses held except that the IAT step (3.4) is as large as the value step (3.9). Realism costs the
pushforward recipe 7.3 points (19.7 -> 12.4), split about evenly between a loader-critical field and abnormal values;
what remains is well above a null of other loader-ignored fields. Caveats: the clean null is small (the 7 free
fields that failed confirmation) and post hoc; a broader null would draw from every loader-ignored header field in the
format, not just the candidate pool. The loader classification is from documentation; no file was executed.
