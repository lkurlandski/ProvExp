# Status

Last updated: 2026-10-13. The framework and intrinsic evaluation are done at pilot scale; both extrinsic applications
are done and written up. We are at an early-draft stage and did a large repository cleanup (archived the dropped
threads, de-staled the docs). The two applications: **the pullback compares two detectors per file** (CM / Comparison,
`docs/experiments/cm.md`), and **the pushforward audits a raw-byte detector across a corpus** (AU / Audit,
`docs/experiments/audit.md`). `run/` holds the commands that produced everything in `artifacts/` (active runs 01-21, 30-33,
38-46; dropped runs in `run/archive/`).

## Where we are

| | state |
|---|---|
| **1. Framework** | Definitions and modest theory in `manuscript/_c_framework.tex`. Round-trip matrices M, N kept as theory; ambiguity and overlap have no demonstrated use (undecided); coverage and the null element's share are not contributions. A Shapley-style uniqueness result is noted as a possible strengthening, not pursued. |
| **2. Intrinsic: PB1** (pullback faithfulness, cost) | Done at pilot scale (`docs/experiments/pb1.md`): parity with the best direct baseline at 64-1,024 windows, ahead at 4,096; at byte level 1.67x occlusion. |
| **2. Intrinsic: PF1** (pushforward faithfulness) | Done at pilot scale (`docs/experiments/pf1.md`): R = 0.31-0.40 for window-level sources; the resolution trend rises 0.34 -> 0.80 (bytes). |
| **2. Intrinsic: CP** | Census, coarsening, CP.3 done (`docs/experiments/cp.md`). |
| **2. Intrinsic: PB2, PF2** (planted triggers) | Done at pilot scale (`docs/experiments/trigger.md`); demoted, possibly removed later. |
| **CM. Comparison (pullback, local)** | Done at pilot scale, written up (runs 30-33; `docs/experiments/cm.md`; `manuscript/_d_applications.tex`). GBDT vs. MalConv byte by byte: shared reliance (bytes both rely on, in the header; window-level comparison without P misses them) and disagreement triage (GBDT-only verdicts rest on header bytes MalConv reads the other way; visible only at byte level). Reframed as the pullback's *local* use. Deferred: seeds 1-2; real-attack transfer. |
| **AU. Audit (pushforward, global)** | **Done** (runs 38-46; `docs/experiments/audit.md`; `manuscript/_d_applications.tex`). MalConv's IG pushed forward into the EMBER features, aggregated over the 2,000-file explanation set. The working framing scrambles the bytes P names for the features MalConv's detection rests on: 9 of 20 confirmed outside the DOS header; scrambling them evades 22.5% of detected malware at 1% FPR (surrogate 24.6%, union 35.1%, random 16.5%). Global comparison with the GBDT (replaces the old Appendix F): MalConv leans on whole-file aggregates, the two detectors' localizable rankings barely agree (Spearman 0.10), only the checksum shared at the top. Mitigation (zero the fields; retrain) deferred (SSViT GPU work). |
| **Appendix** | App-L a stated limitation; App-R's duplicate-feature sweep not run; the byte-set control bound accepted, not started. Old Appendix F (feature-space comparison) removed, promoted into AU. |
| **The MLP** | Set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | `manuscript/_d_applications.tex` has both applications; claims 3 and 4 reflect the local/global split; the experiments table lists CP, PB1-2, PF1-2, CM, AU. Abstract, discussion, and summary are still placeholders, and the introduction's contributions need a pass. Do not try to compile it. |

## Next

1. **Repository organization scheme (pending user approval).** A proposed naming/organization strategy for the live
   docs and experiment IDs is on the table (align IDs with the manuscript sections; one doc per experiment); the
   doc renames and the matching manuscript label-sync are held until the user signs off.
2. **Manuscript drafting** (early stage): the introduction's contributions, the abstract, discussion, and summary are
   still to write. Ask before changing what a claim is for.
3. **Scale-up** (all 2,000 files, seeds 0-2) when the user decides; nothing is scaled yet.
4. **Deferred experiment pieces:** the MLP's return; CM's real-attack transfer; AU's mitigation (test-time zeroing
   and a retrain, both needing SSViT GPU work).

## Decisions

2026-10-13:
- **3-C revised (the audit) worked and is written up.** The working framing scrambles the bytes P names for the
  features MalConv's detection rests on (not forging benign content, which does not transfer; see `docs/graveyard.md`).
  Mitigation deferred (SSViT GPU work); the surrogate column is kept but we do not fit the narrative to it (user).
- **Manuscript updated** to add 3-C, reframe CM as the pullback's local use, rewrite claim 3 for the pushforward
  application, and remove Appendix F (promoted into 3-C's global comparison).
- **Repository cleanup:** 3-B and the rule-based 3-C (YARA) are archived (`scripts/archive/`, `run/archive/`); their
  full plan docs are summarized in `docs/graveyard.md` and removed from the tree (kept in history).
- **CLAUDE.md relaxed:** the "do not propose X" research prohibitions became "generally unproductive, raise with a
  reason" (`docs/graveyard.md`, "Directions the user has generally found unproductive").

2026-10-12 (latest):
- **The pushforward needs an extrinsic application**; the symmetry is the novelty (user). CM alone is not enough.
- **3-C revised adopted:** auditing MalConv for shortcuts through the pushforward (`docs/experiments/audit.md`). Go/no-go
  requires a confirmed shortcut (confirmation is cheap); discovery on the 2,000-file explanation set; MalConv
  mitigation out of scope.
- **Hand-built domain-specific aggregation (a PE parser) is not a realistic alternative**: tremendous manual effort for
  one format (user). The realistic alternative is the surrogate.
- The surrogate is trained on the test split outside the explanation set (only MalConv's test predictions exist); to
  be stated in the paper.

2026-10-12 (later):
- **3-C on hold** after failing the sniff test: as built it rests on the pullback and Pᵀ, not the pushforward. Next
  step is a mock-up of a pushforward-native task, or 3-C as an application of P (user decides).
- **Screening criterion 6: mock the result first** (`PLAN.md`, section 3).
- Packing is not a motivation or case study (user). Rule semantics do not matter to the method (a rule is a byte set
  from an outside detector) but matter to the story's realism (user and Claude agree); YARA-Forge only later, for
  realism. capa deferred.
- Long installs and setup steps go in `README.md`; the user runs them.

2026-10-12:
- **3-B dropped** as the pullback application; **CM is the pullback's application** (user). 3-C stays the
  pushforward's.
- **Screening criteria** for extrinsic applications (`PLAN.md`, section 3): needs what only P gives; a practical task;
  the realistic alternative named; a go/no-go check first; extra skepticism for ideas already ruled out.
- **Hand-mappable findings are acceptable** when P automates the mapping (CM's shared bytes are named header fields;
  "the whole point of computers is to automate things", user). State the caveat once.
- **CM scope:** problem-space only (shared reliance; disagreement triage, option 1: blind / oppose / agree); the
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
- **PF1 design** (`docs/experiments/pf1.md`): two references, the attributable-only check, the naive incidence sum, the
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
