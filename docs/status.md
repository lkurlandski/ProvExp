# Status

Last updated: 2026-10-12 (3-A done at pilot scale and written up; 3-B dropped; docs cleaned up). **The paper is
restructured** (`PLAN.md`, "Paper structure"): 1. the framework; 2. an intrinsic, laboratory-style evaluation (done at
pilot scale); 3. extrinsic applications for security practitioners: 3-A (the pullback, done at pilot scale), 3-C (the
pushforward, not built); 3-B dropped. Work stays at pilot scale (100 files, one seed) until the pilot results and the
claims are settled (user). `run/` holds the commands that produced everything in `artifacts/` (runs 01-37).

## Where we are

| | state |
|---|---|
| **1. Framework** | Definitions and modest theory in `manuscript/_c_framework.tex`. Round-trip matrices M, N kept as theory; ambiguity and overlap have no demonstrated use (undecided); coverage and the null element's share are not contributions (`CLAUDE.md`). A Shapley-style uniqueness result is noted as a possible strengthening, not pursued now. |
| **2. Intrinsic: PB1** (pullback faithfulness, cost) | **Done at pilot scale** (`docs/pb1_pilot.md`): parity with the best direct baseline at 64–1,024 windows, the pullback ahead at 4,096; at byte level 1.67× occlusion (79–85/100 files vs. every direct baseline, p ≤ 6e-12); occlusion saturates at about 1.10. |
| **2. Intrinsic: PF1** (pushforward faithfulness) | **Done at pilot scale** (`docs/pf1_plan.md`): R = 0.31–0.40 for window-level sources; the resolution trend rises from 0.34 (64 windows) to 0.80 (bytes). |
| **2. Intrinsic: CP** | Census, coarsening, CP.3 done (`docs/cp_census.md`); in the paper, its theory (round-trip bounds) and CP.3's agreement check. |
| **2. Intrinsic: PB2, PF2** (planted triggers) | Done at pilot scale (`docs/trigger_plan.md`); **demoted**, possibly removed later. |
| **3-A. Comparing detectors through the pullback** | **Done at pilot scale, written up** (runs 30-33; `docs/cm_plan.md`; `manuscript/_d_applications.tex`). GBDT (EMBER v3) vs. MalConv, byte by byte. Shared reliance: bytes in both top 1% are worth more to each model than its exclusive bytes; they lie in the header; window-level comparison without P misses them (paired, p ≤ 0.025). Disagreement triage (6.4% of test files disagree at 1% FPR): MalConv-only verdicts rest on bytes the GBDT does not read; GBDT-only verdicts on header bytes MalConv reads the other way (deleting them: MalConv detects 19/25 vs. 1/25), visible only at byte level (run 33). Deferred: seeds 1-2 (scale-up); real-attack transfer (`PLAN.md`, "Open questions"). Feature-space comparison: appendix F, not built. |
| **3-B** | **Dropped** (2026-10-12; `docs/archive/shortcuts_plan.md`): findings rested on named features; its post-mortem gave the screening criteria (`PLAN.md`, section 3). |
| **3-C. YARA/capa matches pushed forward** | Design proposed, go/no-go passed (run 34, `docs/rules_plan.md`): generic Yara-Rules, 47 rules on >= 5 pilot files, 16 whose bytes determine non-aggregate features (hashed imports, strings). Reliance: above random for 14/16 rules (run 35), but against a concentration-matched reference (run 36) most represented rules are reliance gaps; only network_dns clearly stands out. Deletion check (run 37): reliance-gap and representation-gap categories supported; "relied on" (network_dns) not confirmed at pilot scale. Generic rules kept; YARA-Forge noted for later. Next: per-rule profiles + categories as the 3-C table; more files per rule (user decides). capa deferred. |
| **Appendix** | App-R's duplicate-feature sweep not run; App-L a stated limitation; the byte-set control bound accepted, not started; F (feature-space comparison of the detectors) a placeholder. |
| **The MLP** | Set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | `_d_applications.tex` follows the old order (CP, PB, PF, then CM = 3-A, written up 2026-10-12); to be reorganized into intrinsic / extrinsic once 3-C exists. Claim 4 rewritten for 3-A; claims 1-3 not yet. Polish is low priority (user). Do not try to compile it. |

## Next (for Claude), on resume

1. **3-C: settle its design with the user before building** (`PLAN.md`, 3-C; screening criteria in section 3). Open:
   the rule source (generic YARA rules such as Yara-Rules `crypto/`, `packers/`, `antidebug_antivm/`,
   `capabilities/`; or capa with a faster backend or file-scope rules), a coverage go/no-go check on the pilot files,
   what only the pushforward gives, and the realistic alternative.
   Proposed 2026-10-12 (user: reasonable, keep thinking): per-rule feature profiles that split "the GBDT ignores
   this rule's content" into a representation gap (matched bytes only diluted in aggregate features) and a reliance
   gap (they determine features the GBDT does not weigh); generic YARA rules first, capa deferred. Go/no-go on the
   pilot files once the user has installed YARA (`README.md`, "External tools for 3-C"; the user runs installs).
2. Rewrite claims 1-3 (`PLAN.md`, "Thesis and claims") for the new structure; ask before changing what a claim is for.
3. Later: reorganize `_d_applications.tex` into intrinsic / extrinsic; the scale-up (all experiments together, when
   the user decides); what to do with ambiguity and overlap.

## The 2026-10-12 session

- 3-B executed to the end (runs 25-29: training-sample baseline, reliance, transplant, mitigation, forging), then
  **dropped** as the pullback application (findings rest on named features); post-mortem and screening criteria in
  `PLAN.md`; the doc archived.
- **3-A became the pullback's application** and was built at pilot scale: run 30 (`scripts/cm_check.py`, agreement and
  cross-deletion), run 31 (`cm_tables.py`, paired tests; `cm_shared.py`, the shared set), run 32
  (`cm_disagreement_select.py`, `cm_triage.py`, zero and random fill), run 33 (the window-level triage, run by the
  user). Byte n-grams set aside; the feature-space comparison moved to the appendix.
- Literature for 3-A's motivation (`docs/related_work.md`, H): Microsoft Defender's layered models, PEberus, MLSEC
  2019's three targets, Salman et al. Framing: "static detectors with different feature sets" (no claim that this
  exact pair is deployed).
- Written up: `docs/cm_plan.md`, `PLAN.md` (claim 4, 3-A, contributions, risks, timeline), the manuscript (3-A
  section, triage table, claim 4, appendix F, four bib entries).
- MalConv test predictions (three seeds) are in `artifacts/checkpoints-predictions/` (names via
  `provexp.data.utils.decode_sha256_tensor`; load with `map_location="cpu"`).

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

2026-10-12:
- **3-B dropped** as the pullback application; **3-A is the pullback's application** (user). 3-C stays the
  pushforward's.
- **Screening criteria** for extrinsic applications (`PLAN.md`, section 3): needs what only P gives; a practical task;
  the realistic alternative named; a go/no-go check first; extra skepticism for ideas already ruled out.
- **Hand-mappable findings are acceptable** when P automates the mapping (3-A's shared bytes are named header fields;
  "the whole point of computers is to automate things", user). State the caveat once.
- **3-A scope:** problem-space only (shared reliance; disagreement triage, option 1: blind / oppose / agree); the
  feature-space comparison goes to the appendix until it has a use beyond being interesting; byte n-grams set aside.
  Real-attack transfer noted for the future. In the paper: "shared reliance", not "attack surface".
- **Stay on track:** analyses must serve the current task; no rabbit holes (user).

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
