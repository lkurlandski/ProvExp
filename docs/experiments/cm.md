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

### Result (run 57, 2026-10-14): no separation; fallback (b) written into 4.3

200 candidate malware (seed 0, 256 IG steps, GPU 1, 36.8 min; `run/57` with `--num_files 200 --device cuda:1`).
Populations: 32 organic, 87 evasion (of 159 both-detect files: zeroing S flipped MalConv with the GBDT holding in 87),
9 GBDT misses.

| population | files | blind | oppose | agree |
|---|---|---|---|---|
| organic | 32 | 0.34 | 0.26 | 0.40 |
| evasion | 87 | 0.35 | 0.28 | 0.37 |

Mann-Whitney evasion vs. organic: blind p = 0.94, oppose p = 0.14, agree p = 0.33. **The hypothesis failed**, and so
does fallback (a) (no category separates the populations).

**Why (a design flaw, visible from the data without new runs):** the readout is the share of the GBDT's *whole* top 1%
of bytes, ~19K bytes for the median evasion file (1.9 MB), while the attack changes only S (median 586 bytes, ~3% of
that set). Even if every changed byte moved to oppose, the share could move by only a few points, about what we see
(+0.02). Also, zeroed bytes likely lose the GBDT's evidence and drop out of its top set. The "by construction, S lands
in oppose" reasoning above overlooked both. Note that the evasion files are larger than the organic ones (median 1.9 MB
vs. 1.5 MB), a further mismatch.

**Fallback (b) written into 4.3:** the decision is argued from the existing triage (blind -> coverage gap, add a
feature over the blind bytes; oppose -> conflict over the same bytes, inspect the oppose bytes first, they are where the
missing detector is easiest to move), with one honest sentence that the labels describe *which content* drives a
disagreement, not its cause, citing run 57. Not yet run: a localized readout (label only the changed bytes S of the
evaded file, or the triage on the original file's S); it would need re-explaining (~40 min GPU at 200 candidates).

## Attack transfer (6.1 Part A; run 68, 2026-10-20): NO-GO

**Purpose.** Answer REVIEW W3 / risk 3 (the pullback's application has no attacker and no security outcome): before any
attack, the GBDT's pullback on the loader-ignored region E (DOS header, DOS stub, section slack) should predict, file by
file, how much an attacker who evades MalConv there also costs the GBDT; compared with occlusion's evidence on E and
with the number of bytes changed.

**Result (100 both-detected malware, seed 0).** MalConv evaded on 81%. The GBDT never crosses its threshold, *rises* on
78% of files (median drop -1.06 log-odds), and drops by >1 log-odds on 5. Spearman with the signed drop: pullback_E 0.34
(p = 5e-4), occlusion_E 0.18, |C| -0.18; AUC (drop > 1, 5 positives) 0.78 / 0.54 / 0.58. Bootstrap CI of rho(pullback)
- rho(occlusion): [-0.09, 0.41], not significant.

**Why (diagnostics from files.parquet, no new runs).**
1. The GBDT barely reads E. The pullback puts a median 0.1% of the GBDT's log-odds on E (|evidence| < 0.1 log-odds on
   54% of files); the shared bytes S of 6.1 (checksum, data-directory sizes, DLL characteristics) lie in the optional
   header, outside E. The attack region and the shared reliance barely overlap, so there was little to transfer.
2. Where the pullback does see evidence, it is right: in the top quartile of evidence on E (median 0.35 log-odds), 52%
   of files drop and 4 of the 5 large drops occur; in the other three quartiles, 12% drop.
3. The rise is from *added* content: the attack writes new bytes (median 64 changed) that the GBDT reads as more
   malicious (likely stub strings, Rich-header and byte-histogram features). An explanation of the original file
   measures evidence that removal takes away; it cannot predict evidence that new content adds.
4. occlusion_E's scale looks off (hundreds to thousands, signs mixed); irrelevant for Spearman but check before reuse.

## Editing the shared fields (6.1 Part A'; run 71, 2026-10-20)

Step 0 (feasibility) passed: every file has >= 3 loader-safe candidate fields (median 53); they hold a median 28% of
the GBDT's and 27% of MalConv's evidence; on 86% of files the 3 shared fields carry > 0.5 log-odds of each detector.

Step 1, 3 fields per file, 100 both-detected malware (run 68's), all edits parsed:

| arm | MalConv drop | GBDT drop | both drop > 1 |
|---|---|---|---|
| shared, pullback ∩ IG | 0.82 | 1.33 | 32% |
| shared, occlusion (4,096 windows) ∩ IG | 0.84 | 1.05 | 25% |
| MalConv only (IG) | 1.30 | 1.31 | 37% |
| GBDT only (pullback) | 0.59 | 1.33 | 24% |
| random loader-safe fields | 0.26 | 0.34 | 6% |
| run 68's attack on E (context) | 6.89 | -1.06 | 5% |

**Hypothesis failed in its comparative part.** Shared fields beat random (28 vs 2 discordant files, p = 9e-7) and
run 68, but not MalConv-only selection (32% vs 37%, p = 0.40) nor windows (32% vs 25%, p = 0.28). Why: within the
loader-safe pool both detectors' top fields are the same certificate (authenticode) fields and the checksum (pullback
and MalConv-only choose 63% of the same fields); MalConv's IG alone already finds edits that hurt both. What decides
transfer is the region (header/certificate fields vs. run 68's DOS stub and slack), not who ranks within it.

**Run 68's original question, in the right region: works.** For the MalConv-guided edits (arm malconv_only), the
GBDT's pullback evidence on the edited fields predicts the GBDT's drop: Spearman 0.47 (AUC 0.78 for drop > 1, 56
positives) vs. occlusion's evidence on the same fields 0.25 (0.64) and bytes changed -0.04 (0.52). The pullback leads
the windows in all five arms (0.34-0.55 vs. 0.11-0.25); per-arm bootstrap CIs of the difference reach about -0.01
(gbdt_only: [0.10, 0.57]). Pooled over 500 edits: 0.45 vs. 0.20. Pilot scale; 500 files would settle significance.

**Run 72 (500 files, 2026-10-20): the prediction holds; in the paper (6.1, Table 2).** Clean (2,500 edits ok, 3
unparsed). Arm malconv_only: Spearman 0.48 (pullback) vs. 0.21 (occlusion, 4,096 windows) vs. 0.03 (bytes); AUC (drop >
1, 291/499 positives) 0.78 / 0.60 / 0.55; bootstrap CI of the rho gap [0.17, 0.38]. The lead holds in 4 of 5 arms
(CIs above 0); in shared_pullback it does not (0.26 vs. 0.20, CI [-0.05, 0.16]); that arm is not in the paper.
Medians, malconv_only: GBDT drop 1.36 (> 1 on 58%, rises on 14%), MalConv drop 1.45, both > 1 on 43%, MalConv evaded
12%, 24 bytes changed; fields chosen are 53% authenticode, 28% header (CheckSum 168 of 1,497), 9% data directories, 7%
DOS message, 3% Rich header. Mirror (gbdt_only): MalConv drop 0.66. Five-way "both drop": shared pullback 33%, shared
windows 28%, MalConv-only 43%, GBDT-only 28%, random 8% (MalConv-only now beats shared pullback, p = 6e-6).

*Fixed (2026-10-20, commit 534edc3):* `audit_evade.benign_pools` cast two benign ImageBase values above 2^63 to a negative int64 (the RuntimeWarning in the log); a file that drew it skipped that field (the write step rejects negative values). Pools now keep 0 <= v < 2^53. `run/73` reran 49, 59, and 72 into new directories (`*fixpools*`): every estimate and p-value unchanged (some bootstrap CI endpoints move by 0.1 point); the paper's numbers stand.

## KernelSHAP as a second window baseline for Table 2 (run 75, prepared 2026-10-21; not yet run)

Why: Section 5.1 now shows KernelSHAP over 4,096 windows as the strongest direct method (run 74), so a reviewer may ask
why Table 2's window baseline is occlusion. Decided (user, 2026-10-21): add KernelSHAP as a second row, keep occlusion
(the cheap alternative a defender would use). `scripts/cm_shared_edit.py --kernelshap` computes the GBDT's KernelSHAP
over the 4,096 windows (8 coalitions per window, 32,770 queries per file, as in 5.1) in a cached, resumable phase 1b
with Section 5.1's worker (`faithfulness.process_kernelshap`, fork pool; inside the spawned phase-2 workers the same
computation ran ~3x slower, cause not found), then sums it over the edited fields like occlusion. `run/75`: 500 files,
16 workers, ~32 h (from run 74's per-byte times; these files average 1.3 MB). Smoke test (3 files): run 72 reproduces
exactly, no failed coalitions, times in line with the estimate.

Hypothesis: rho ~0.25-0.35, between occlusion (0.21) and the pullback (0.48): the fields are a few bytes next to other
header content the GBDT reads, and a ~300-byte window spreads one value over all of it however well it is explained. If
KernelSHAP reaches the pullback, 6.1's claim weakens: stop and decide with the user before writing. The manuscript
carries predicted values in blue (rho 0.31, AUC 0.65, CI of the rho gap 0.09-0.26), with the prose written as if run.
