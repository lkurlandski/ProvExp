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

## Triage tied to a decision (planned 2026-10-14; revision plan B9)

**Why.** The self-review (W6) says the triage's blind/oppose/agree split is not yet tied to an action a defender
would take. The proposed test: show the labels *diagnose why two detectors disagree* — specifically, tell an
attack-caused disagreement from an organic one — so the label is a decision (investigate as evasion vs. close as a
blind spot).

**Design.** Two populations of GBDT-only-flagged malware, run through the same triage (A = GBDT, B = MalConv):
- **organic:** real held-out malware the GBDT detects and MalConv misses (the existing "GBDT only / malware" cell).
- **planted evasion:** malware both detect, modified so MalConv now misses while the GBDT still detects; the
  disagreement is *caused* by an attack on MalConv. Reuses the audit's loader-safe recipe (`audit_evade.py`) to build
  the evaded bytes, then the triage's `categories()` split on them.

**A subtlety that changes the hypothesis (thought through before building).** The triage splits *A's* (the GBDT's)
top malware bytes by how B (MalConv) reads them. A planted evasion shows up as **oppose** only if the bytes the attack
changed are (a) read by MalConv as benign *and* (b) among the GBDT's top malware bytes. The audit found the two
detectors rely on *different* header fields, so an evasion built from the audit's recipe (fields MalConv relies on,
the GBDT mostly ignores) would flip MalConv but its changed bytes would **not** be in the GBDT's top set — so this
triage direction would not see "oppose." The hypothesis "planted evasion -> oppose" is therefore **not automatic**;
it depends on *which* bytes the evasion changes.

This gives a genuine design fork (which evasion to plant):
1. **Audit-recipe evasion** (MalConv-specific fields): clean loop with our audit, but likely shows up as *blind*
   (changed bytes the GBDT does not rank), i.e., indistinguishable from an organic blind spot in this direction.
   Would need the *other* triage direction (A = MalConv on a MalConv-only cell) or a different readout.
2. **Shared-reliance evasion** (change bytes in S = the top bytes *both* rely on): by construction the changed bytes
   are in the GBDT's top set, and flipping MalConv on them makes them read benign -> **oppose**. This is the clean
   version of the hypothesis, but a loader-safe attack confined to shared bytes may not exist for every file.
3. **Reframe the readout:** instead of predicting a category, test whether the triage *separates* the two populations
   at all (any category whose distribution differs), which is a weaker but safer claim.

**Mock of the expected table (FAKE numbers, to decide the setup):**

| population (GBDT-only malware) | blind | oppose | agree | defender's reading |
|---|---|---|---|---|
| organic (unmodified)                 | 0.25 | 0.33 | 0.42 | real (run 32) |
| planted evasion, shared-reliance (opt 2) | 0.10 | 0.70 | 0.20 | FAKE: attack on shared bytes -> oppose |
| planted evasion, audit-recipe (opt 1)    | 0.65 | 0.20 | 0.15 | FAKE: MalConv-only fields -> blind |

If option 2 looks like the middle row, the triage cleanly flags an attack on shared reliance (high oppose); if
option 1 looks like the bottom row, the audit-recipe evasion is *indistinguishable from organic* in this direction,
and the experiment would need the MalConv-flagging direction instead. **Decision needed before building** (GPU
experiment): which evasion to plant, i.e., which story to pursue.

### Decision (user, 2026-10-14): pursue shared-reliance evasion first

Pursue option 2 (shared-reliance evasion); fall back to reframing the readout, then to reconsidering, if it does not
pan out. Concrete first-cut mechanism (no query optimization): among malware **both** detect, scramble the shared set
S (the top bytes both rely on, as in run 30's shared-reliance, loader-safe) and keep the files where MalConv drops
**below** its 1%-FPR threshold while the GBDT stays **above** its own. Those are attack-on-shared-reliance
disagreements; run the triage (A = GBDT, B = MalConv) on the modified bytes and compare blind/oppose/agree with the
organic "GBDT only / malware" cell. Open question the run answers: after scrambling S, does the GBDT still place top
malware evidence on those bytes (needed for "oppose"), or does scrambling move its evidence elsewhere? If oppose does
not dominate, fall back.

### Implementation plan (B9, shared-reliance evasion)

New script `scripts/cm_triage_evasion.py`, reusing: `cm_shared.split_sets` (S), `cm_triage.categories` (the
blind/oppose/agree split), `cm_check._STATE` (extractor/GBDT/MalConv), `ablate`/`protect`/`verify`,
`malconv_log_odds`, `treeshap_interventional` and MalConv IG from `provexp.explain`. Flow per file:
1. Source: malware **both** detect (new selection `ts-bothdetect-seed0.parquet` via a small variant of
   `cm_disagreement_select.py`; TreeSHAP + MalConv IG for the originals from `explain.py`, as the disagreement cells
   get them).
2. Compute e_g (GBDT pullback of TreeSHAP), e_m (MalConv IG), S at q = 1%.
3. Scramble S loader-safe (the `ablate` operator), score both models on z; **keep** files with malconv(z) <= its
   threshold and gbdt(z) > its threshold (attack on shared reliance that evaded MalConv, GBDT held).
4. For kept files, **recompute** TreeSHAP and MalConv IG on z (in-process; GPU for IG), then `categories()` with
   A = GBDT, B = MalConv -> blind/oppose/agree.
5. Compare with the organic `malware_gbdt_only` cell (already in the disagreement selection / run 32).

Cost note: steps 1-3 are cheap; step 4 re-explains each kept file (IG ~25 ms on GPU, TreeSHAP ~ms). Smoke-testable on
a handful of pilot malware. Two-step run: (a) select + explain the both-detect pool, (b) `cm_triage_evasion.py`.

### Implemented and smoke-tested (2026-10-14, run 57)

`scripts/cm_triage_evasion.py` + `run/57_cm_triage_evasion.sh` (+ `tests/test_cm_triage_evasion.py`, 4 unit tests on
the pure share helper). Single process, one GPU; re-explains each file the triage sees (TreeSHAP + MalConv IG).
Smoke test (16 candidate malware, ig_steps 64, ~2 min): produced all populations (4 organic, 2 both-detect that did
not evade, 9 evasion, 1 gbdt-missed) and the blind/oppose/agree split with evasion-vs-organic p-values. **~9 of ~11
both-detect files evaded by scrambling S**, so the mechanism yields enough evasion files. The smoke numbers are not
meaningful (tiny N, reduced IG steps; no separation seen there). The pilot (`run/57`: 500 candidates, 256 steps, GPU 3,
~2-4 h) is for the user to run. **Follow-up when done:** read the oppose share, evasion vs. organic. If oppose
separates them, the triage label is a defender's decision (write it into 4.3); if not, fall back to reframing the
readout, then to reconsidering (the fallback order the user set).
