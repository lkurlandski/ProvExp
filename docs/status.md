# Status

Last updated: 2026-10-12 (3-B done at pilot scale). **The paper is restructured** (`PLAN.md`, "Paper structure"):
1. the framework; 2. an intrinsic, laboratory-style evaluation (done at pilot scale); 3. extrinsic applications for
security practitioners (3-A, 3-B, 3-C: chosen, not designed). Work stays at pilot scale (100 files, one seed) until
the pilot results and the claims are settled (user). `run/` holds the commands that produced everything in
`artifacts/`.

## Where we are

| | state |
|---|---|
| **1. Framework** | Definitions and modest theory in `manuscript/_c_framework.tex`. Round-trip matrices M, N kept as theory; ambiguity and overlap have no demonstrated use (undecided); coverage and the null element's share are not contributions (`CLAUDE.md`). A Shapley-style uniqueness result is noted as a possible strengthening, not pursued now. |
| **2. Intrinsic: PB1** (pullback faithfulness, cost) | **Done at pilot scale** (`docs/pb1_pilot.md`); survived the tie-break re-run (`run/21`): parity with the best direct baseline at 64–1,024 windows, the pullback ahead at 4,096; at byte level 1.67× occlusion (79–85/100 files vs. every direct baseline, p ≤ 6e-12); occlusion saturates at about 1.10. All paired tests are now in `scripts/pb1_tables.py`. |
| **2. Intrinsic: PF1** (pushforward faithfulness) | **Done at pilot scale** (`docs/pf1_plan.md`): R = 0.31–0.40 for window-level sources; the resolution trend rises from 0.34 (64 windows) to 0.80 (bytes). |
| **2. Intrinsic: CP** | Census, coarsening, CP.3 done (`docs/cp_census.md`); in the paper, its theory (round-trip bounds) and CP.3's agreement check. |
| **2. Intrinsic: PB2, PF2** (planted triggers) | Done at pilot scale (`docs/trigger_plan.md`); **demoted**, possibly removed later. |
| **3-A. Comparing detectors** | **Done at pilot scale** (runs 30-33, `docs/cm_plan.md`). **The pullback's application** (3-B dropped, 2026-10-12). GBDT on EMBER v3 vs. MalConv; byte n-grams set aside. First check done (run 30, `PLAN.md` 3-A): shared reliance appears at byte level (cross-deletion at 0.1%: the GBDT's byte pullback removes 1.54 of MalConv's evidence vs. 0.55-0.79 for window rankings, 0 random), hidden at window level. Security framing to settle with the user. |
| **3-B. Spurious correlations via the pullback** | **Done at pilot scale** (`docs/shortcuts_plan.md`, "Results"). Top 20 discovery patterns by a fixed rule, transplanted into 200 held-out malware at the bytes the file's P names: 5 confirmed, 4 of them artifacts (certificate-table size +1.34 vs. -0.27 random; DEBUG.Size 0x54; the `.rsrc` name in a hashed bucket). Mitigation: 6 P-named features neutralized, AUC 0.99759 -> 0.99756; the exploits removed (`.rsrc` residual +0.06 vs. +0.02 random). Baseline without P (run 25): the top chi-squared 4-grams are certificate (DER) bytes, the same signing signal, but the model credits them ~0 and appending them moves nothing; the model reads the data-directory size, which only P locates. Run 29 (forging the confirmed artifacts together): 3.6% of detected malware evades at 1% FPR vs. 0.1% random; 0.1% after neutralization; carried by two named data-directory sizes. **Failed as the pullback application** (findings rest on named features; `docs/shortcuts_plan.md`, "Why it failed"). |
| **3-C. YARA/capa matches pushed forward** | Adopted, not designed. Coverage check stopped early: public YARA signatures too sparse; generic rules and capa untested; capa's default backend is very slow. |
| **Appendix** | App-R's duplicate-feature sweep not run; App-L a stated limitation; the byte-set control bound accepted, not started. |
| **The MLP** | Set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | `_d_applications.tex` reflects the old structure (CP, PB, PF, CM); to be reorganized once the extrinsic applications exist. Polish is low priority (user). Do not try to compile it. |

## Next (for Claude), on resume

1. **3-A leads with two uses (user, 2026-10-12):** (a) the shared attack surface of an ensemble (bytes both
   detectors rely on; evasion transfer), motivated only if production use of such ensembles can be cited (candidates:
   Microsoft Defender's stacked ensembles plus a full-content DNN engine, Kaspersky's ML², PEberus, MLSEC's three
   target models; transfer evidence in the literature is mixed); (b) disagreement triage: disagreements are common
   (test set, seed 0, 1% FPR: 6.4% of files; 29k malware only the GBDT detects, 2k only MalConv, about 1.5k false
   positives each; MalConv predictions in `artifacts/checkpoints-predictions/`, names via
   `provexp.data.utils.decode_sha256_tensor`, which needs CPU tensors). Done: paired tests and the shared bytes (run 31, `PLAN.md` 3-A: the shared
   surface is header and data-directory fields; 86% of its credit is on named features). #2 (option 1, user): run 32 done (`PLAN.md` 3-A): MalConv-only verdicts rest
   on bytes the GBDT does not read; GBDT-only verdicts on bytes MalConv reads the other way. Follow-ups done (offsets, blind-byte features, random fill;
   `PLAN.md` 3-A). 3-A's pullback analyses are complete at pilot scale.
   Run 33 (the user): window-level triage loses the oppose category; byte resolution is needed. Next: the manuscript.
2. Rewrite the claims (`PLAN.md`, "Thesis and claims") to fit the new structure; ask the user before changing what a
   claim is for.
3. Later: 3-C's rule source (generic YARA rules, or capa with a faster backend or file-scope rules); what to do with
   ambiguity and overlap.

## The 2026-10-12 session

- Later the same day: 3-B dropped as the pullback application; 3-A takes its place (user). Run 30 (`scripts/cm_check.py`): GBDT vs. MalConv agreement and cross-deletion on PB1's pilot files (about 9 min).

- 3-B scope settled with the user in one exchange (all four parts; top 20 benign-pushing; 2,500 + 2,500 training sample), then executed: `scripts/shortcuts_transplant.py` (placement by the target's P; confirmation rule fixed before the run, tightened after the smoke test so that beating an anomalous random control is not enough), `shortcuts_reliance.py` (credit, carried features Pᵀ1_S), `shortcuts_train_sample.py` (prevalence, exact 4-gram mining; smoke-tested only), `shortcuts_tables.py` (tables, labels, the neutralize rule), `train_classic.py --neutralize`. Runs 25-28 done (run 25 by the user); the baseline is in `docs/shortcuts_plan.md`.

## The 2026-10-09 session

- Run 21 read: PB1's conclusions survive random tie-breaks (`docs/pb1_pilot.md`, "Tie-break re-run"). Costs now
  from run 17 (KernelSHAP over windows: 2,050 extractions; run 12 shared a cache with occlusion). `pb1_tables.py`
  prints every paired test (vs. each direct baseline, at the same window count, signed vs. unsigned overshoot).
- Second review with the user: the paper restructured; 3-A/B/C chosen (`PLAN.md`, "Paper structure"); statistics,
  trigger experiments, and App-L re-scoped; `CLAUDE.md` updated (coverage/null element are not contributions;
  brief hypotheses instead of elaborate readings; domain-agnostic byte-set control is in scope).
- Partial coverage check for 3-C (YARA-Forge on the pilot files; capa timing), stopped early by the user.
- PB2/PF2 at pilot scale (50 files per trigger). Corrected a mislabeled "ceiling" (it was the round trip P ψ(1_T); the
  true bound is 1).
- PF1 designed, built, and run, with the resolution diagnostic and the resolution trend; claim 3 reworded (option A).
  Found and fixed round-off near-ties deciding PF1's rankings.
- CP.3 (instrumented vs. black-box statistics).
- A review of the stage (framework, claims, experiments): one correctness issue (PB1's positional tie-breaks, fixed,
  re-run pending) and several framing points, now in `PLAN.md` ("Open questions") and the docs.
- Docs streamlined: `docs/archive/` (Phase 2 plan and census), `docs/appendix.md` (App-L, App-R), condensed trigger
  and PF1 docs; `CLAUDE.md` updated (doc list, the tie-break rule, readings fixed in advance, `run/` script style).

## Decisions

2026-10-09 (second review, after run 21):
- **Paper structure:** framework / intrinsic evaluation (lab-style: PB1, PF1, CP's theory) / extrinsic applications
  (A = CM, B = byte-level discovery of what a detector keys on via the pullback, C = a pushforward application, to
  be found). Adding EMBER v2 as a second feature set is not worth it (too similar to v3).
- **Trigger experiments (PB2, PF2) demoted**, kept for now, possibly removed later.
- **Round-trip matrices M, N stay** as theory; ambiguity and overlap undecided; **coverage, localizability, and the
  null element's share are not contributions** (explanation-specific; a pipeline limitation, not a finding).
- **Theory:** an axiomatic (Shapley-style) uniqueness result noted in `PLAN.md` as a possible strengthening, not now.
- **Hypotheses before experiments, briefly** (not elaborate pre-registered readings; `CLAUDE.md`).

2026-10-09:
- **Claim 3, option A:** the pushforward is faithful up to its source's resolution, a limit set by P's overlap; PF2
  carries "useful". TreeSHAP's window round trip counts only through its trend across resolutions.
- **PF1 design** (`docs/pf1_plan.md`): two references, the attributable-only check, the naive incidence sum, the
  criterion fixed in advance (above random and naive; R bands 0.8 / 0.5). No pushforward of triggered files.
- **PF2 reads r = ψ(1_T) as a support, not a target** (mass and top-k in supp(r)).
- **PF1's per-file reading dropped** (overlap at a fixed window count is mostly file size).
- **Rankings break ties by a seeded permutation**, never by position or index.
- **No scaling** until the pilot results and the claims are settled; manuscript polish is low priority.

2026-10-08:
- Evaluation structure and IDs (CP, PB1–2, PF1–2, CM; App-L, App-R). Pilot scale for most of the research.
- CP: ambiguity = entropy with effective support, overlap = 1 − M_jj, round-trip bounds, coarsening proposition.
- PB1: level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary.
- The GBDT first; the MLP set aside temporarily.
- Trigger testbed: both triggers, dirty-label trigger → benign at 1%, long files overwritten, backdoor-fired filter.

2026-10-07:
- Framework domain-agnostic; experiments may use domain knowledge selectively (CLAUDE.md). No PE-structure analyses.
- Ambiguity and overlap *characterize P*; they were never meant to predict faithfulness.
- Localizability ℓ removed from the framework (an evaluation metric only); coverage κ kept. Ambiguity and overlap
  exclude unattributable features under the null policy.
- GBDT treats categorical features as numeric (shap misencodes LightGBM categorical splits).
- PB1 operator: level 2 = protect layout fields plus per-file breakers, zero the rest; level 3 = header fields take
  typical values; every ablated file verified. Insertion dropped. K = 256 windows.
- KernelSHAP: 32,768 samples, a 16-sample balanced background, `l1_reg=False`.

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); PB1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.
- Occlusion cannot see zero or protected header bytes and creates fill artifacts (new entropy windows, pefile
  warnings); most of its windows at fine resolution change nothing (score exactly 0).
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not explained.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files; `data/tlsh.py` dedup is exact.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
- The machine: 2 sockets x 16 cores, hyperthreaded (64 logical CPUs), about 500 GB of memory.
