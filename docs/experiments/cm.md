# CM: Comparing Detectors Through the Pullback

Status: done at pilot scale (2026-10-12; runs 30-33). The pullback's extrinsic application, replacing 3-B (user,
2026-10-12). Scaling waits until the claims and the other applications are settled (user).

## Claim

Deployed malware detection layers several static detectors over different feature sets (Microsoft Defender's stacked
ensembles of feature-based models alongside a full-content deep-learning engine; PEberus's EMBER GBDTs, byte
skip-gram model, and YARA rules; the MLSEC 2019 targets MalConv, non-negative MalConv, and an EMBER LightGBM;
`docs/related_work.md`, H). Their explanations live in different spaces: a feature-based detector explains features,
a raw-byte detector explains bytes. **The pullback puts both in the problem space, at byte resolution, so they can be
compared directly**, which answers two practical questions:

1. **The shared attack surface:** which bytes do both members rely on, so that one manipulation weakens both (the
   ensemble's members do not fail independently there)?
2. **Disagreement triage:** when one member flags a file and the other does not, is the flagging member's evidence
   content the other does not read (a blind spot) or reads the other way (a disagreement on meaning)?

Framing (user, 2026-10-12): "static detectors with different feature sets" are deployed and studied together; there is
no evidence that raw-byte and EMBER-style detectors specifically are paired in production, and we do not claim it.

## What P contributes, and the realistic alternative

- **The GBDT at byte resolution, automatically.** The realistic alternative needs no P: occlude both models over
  windows (PB1's direct baselines). It misses most of the shared reliance (results, 1). An expert could map the
  named header features by hand with a PE parser; the pullback does this mapping generally, per file, for every
  feature group (user, 2026-10-12: automating it is the point).
- **One extraction per file** (PB1's cost result), so the comparison runs on every disagreement, not a few.
- The comparison itself is model-agnostic in the framework's sense: it uses P and two byte explanations only. The
  descriptions of where the bytes lie (offsets, which features) are domain-specific and stay in the experiment.

## Setup

- Models: the GBDT on EMBER v3 (seed 0); MalConv medium (EMBER-2024 release, seed 0).
- Explanations of the malware log-odds per byte: the GBDT's pullback of interventional TreeSHAP; MalConv's Integrated
  Gradients (256 steps, padding baseline); MalConv's exact occlusion of its 512-byte windows; the GBDT's occlusion at
  64-4,096 windows (from PB1, run 21).
- Deletion: PB1's operator (level 3: protected layout fields, header fields take typical values, the rest zeroed;
  every deleted file verified), both models scored on every deleted file. Random fill as a check (run 32).
- Files: PB1's 100 pilot files (runs 30, 31); for triage, 25 test files per disagreement cell at each model's
  1%-FPR threshold (`scripts/cm_disagreement_select.py`; the thresholds come from the test split's benign files,
  since neither model has saved validation predictions).
- Disagreements are common (test split, seed 0, 1% FPR): 6.4% of files; 29,267 malware detected only by the GBDT,
  1,964 only by MalConv; 1,547 false positives of each model that the other does not share (seeds 1-2: 5.7-5.8%).

## Results (pilot scale)

1. **Shared reliance appears at byte level and is largely hidden at window level** (run 30, `scripts/cm_check.py`;
   paired tables in `artifacts/reports/cm_tables.md`). Overall agreement is weak (median Spearman rho <= 0.07 at every
   resolution; top overlap 2-3x chance at windows, 6.5x at bytes). Cross-deletion: the GBDT's byte pullback removes
   more of MalConv's evidence than either window ranking of the GBDT at every budget 0.1-5% (58-69/100 files,
   p <= 0.025; at 0.1%: 1.54 log-odds vs. 0.55 for the pullback at 256 windows, 0.79 for occlusion at 256 windows, 0
   random). The reverse direction (MalConv's byte IG removing the GBDT's evidence) beats MalConv's window rankings only
   at 0.1-0.2%.
2. **The shared attack surface** (run 31, `scripts/cm_shared.py`). S = the bytes in both models' top 1% (|S| = 6.3%
   of each top set vs. 1% chance). Deleting S removes 2.78 (GBDT) / 3.78 (MalConv) log-odds; same-size GBDT-only bytes
   0.86 / -0.08; MalConv-only 0.04 / 2.58; random 0.00 / 0.01 (top 5%: 3.88 / 9.79 vs. 1.52 / -0.79 and 0.15 / 7.45).
   Byte for byte, the shared bytes are worth more to *each* model than its exclusive bytes. They lie in the first
   1 KB (97% of the GBDT's shared evidence, 75% of MalConv's) and are carried by header and data-directory features
   (86% of the GBDT's credit; `characteristics_DLL`, `security_size`, `CheckSum`, `debug_size`, ...; hashed features
   5%), consistent with MalConv's known reliance on the header (Demetrio et al.).
3. **Disagreement triage** (run 32, `scripts/cm_triage.py`). A = the model that flags, B = the other; A's top 1% of
   bytes split by B's reading (attended = B's top 5% by |evidence|):

   | cell | blind | oppose | agree |
   |---|---|---|---|
   | malware, MalConv only | 0.77 | 0.10 | 0.13 |
   | benign, MalConv only | 0.77 | 0.10 | 0.14 |
   | malware, GBDT only | 0.25 | 0.33 | 0.42 |
   | benign, GBDT only | 0.46 | 0.17 | 0.37 |

   When MalConv alone flags, its evidence lies mostly on bytes the GBDT does not read (the file body: 57-73% beyond
   64 KB). When the GBDT alone flags, MalConv reads most of the same bytes, in the header (oppose and agree: 87-97% in
   the first 1 KB), often the other way. Validation: deleting the oppose bytes makes MalConv flag 19/25 GBDT-only
   malware (random same-size part of the GBDT's top set: 1/25) and 17/25 GBDT false positives (1/25); random fill
   22/25 vs. 0/25 and 18/25 vs. 1/25. Deleting blind bytes leaves B unchanged where A is the GBDT (as expected).
4. **The triage needs byte resolution** (run 33, the realistic alternative: the same split over 256 windows on the 50
   GBDT-flagged files). At windows the "oppose" category nearly vanishes: for GBDT-only malware, MalConv reads the
   other way 0.06 of the GBDT's top evidence with the pullback summed per window and 0.02 with the GBDT's occlusion
   (no P), vs. 0.33 at bytes; the oppose set is nonempty in 6 and 2 of 25 files (25 at bytes), and deleting it makes
   MalConv flag 3/6 and 0/2 files, no better than random. "Agree" absorbs it (0.75 / 0.70 vs. 0.42). The oppose and
   agree bytes interleave within the header (both in the first 1 KB), so any window merges them, and the window-level
   diagnosis reads the opposite of the byte-level one: MalConv seems to *agree* with the GBDT's evidence. The coarsened
   pullback behaves like occlusion here, so the loss comes from resolution, which only the pullback affords for the
   GBDT. GBDT false positives: oppose 0.17 at bytes vs. 0.08 / 0.11 at windows, in 4 and 6 files.

## Caveats

- **Aggregate features cannot be validated by deletion.** The credit on the GBDT's blind bytes sits on string-regex
  counts and section-entropy / import hashes; deleting a few of their bytes barely changes them (-0.16 vs. -4.55 for
  a random same-size part of the top set; run 23's boundary).
- **The MalConv-flagged cells are descriptive only.** Any large deletion raises the GBDT's score, with zero or random
  fill, which confounds B's response when A is MalConv.
- **Deletion is not an attack.** The shared set is an attack *surface* in the sense of reliance; the operator keeps the
  file parseable with its layout, not functional. No functionality-preserving attack was run.
- MalConv's IG deletion overshoots enormously (its own top 1% of bytes: 19 log-odds, 72 at 50%), a known fragility of
  MalConv; it does not affect the comparisons, which are all within budgets and against same-size controls.
- One seed, 100 (+100) files; thresholds from the test split's benign files.

## Open (for the write-up)

- The window-level triage is done (run 33). Real-attack transfer is noted for the future (`PLAN.md`, "Open
  questions"); seeds 1-2 at scale-up.
- The feature-space comparison (MalConv pushed forward) is in the appendix as a curiosity (user, 2026-10-12).
