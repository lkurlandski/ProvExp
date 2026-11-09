# Related Work and Gap Analysis (Phase 0)

Started 2026-10-06. Status markers: **[read]** = method/abstract checked during the search;
**[abstract]** = only the abstract was checked, so the full text still needs reading; **[bib]** = already in `manuscript/main.bib`.

## Bottom line

1. **The pullback mechanism is not new.** Redistributing a downstream attribution to upstream inputs in
   proportion to each input's (baseline-relative) contribution is the *generalized rescale rule* of
   G-DeepSHAP (Chen, Lundberg & Lee, Nature Comms 2022). That rule descends from DeepLIFT's chain rule and
   relates to LRP. G-DeepSHAP also shows that propagation is exact for chains of linear models. Our
   b = Pa equals their rule when P_ij = φ_i(σ_j) / (σ_j(z) − σ_j(z̄)). **Claims C1/C2 in the proposal
   ("first to formalize", "novel rigorous theory of explanation transformations") cannot stand as written.**
2. **What G-DeepSHAP and its relatives do *not* cover is the actual problem here.** Their propagation needs every stage
   to be a *model* that has an efficiency-satisfying attribution method (DeepLIFT, TreeSHAP, exact linear).
   A real feature extractor is a *program*: a parser plus hashing, string scans, windowed entropy, header
   lookups. It runs over discrete, variable-length, structured input with no natural baseline. We found
   no work that builds the stage-wise attribution matrix (our P) for such a program. **This is the
   defensible core: provenance construction for program feature extractors.**
3. **Malware XAI has no problem-space explanations for feature-based detectors.** Explanations are
   either feature-level (SHAP on EMBER) or byte-level for raw-byte models (MalConv + IG/SHAP).
   Attack papers that use feature explanations (Severi, Rosenberg, Mate!) realize features in the
   binary by hand, one feature at a time. **This is the clearest gap and the strongest motivation.**
4. **A September 2026 paper (Mohseni, Raff & Gaur) argues SHAP on EMBER is unreliable.** It explains a
   feature-coalition game, interventional SHAP queries off-manifold coalitions, and redundant
   features dilute credit. We must engage with it directly. It is also an opportunity: problem-space
   explanations can be *checked* in the problem space with real files (on-manifold), and overlap O
   gives a measure of the redundancy they describe.
5. **No prior equivalent found for the localizability diagnostics (H, O).** G-DeepSHAP's group rescale
   rule normalizes away overlap but never measures it.
6. **Pushforward to a *different* space through a non-invertible program has no direct precedent we found.**
   The closest are Virtual Inspection Layers (DFT-LRP: relevance moved through an *invertible
   linear* transform, time to frequency) and attribution aggregation (pixels→segments, tokens→words,
   which is coarsening within one space). Claim the *application* (comparing byte-level and
   feature-level detectors in a shared space), not "first pushforward ever".
7. **Terminology collision.** In the security community, "provenance" means system provenance graphs
   (Kairos, Poirot, provenance-based IDS, several of which are in our bib). USENIX reviewers will stumble on this.
   Consider renaming (e.g., "feature lineage" or "attribution lineage") or disambiguate in the first paragraph.

## Full-text reading notes (2026-10-06)

- **Mohseni/Raff/Gaur 2026 (SHAP on EMBER).** 8 pages, likely a workshop paper. Lemmas: interventional SHAP goes off-manifold
  (L1); conditional SHAP dilutes credit by 1/m across m redundant features (L2), credits unused proxies (L3),
  and its sign can flip across distributions (L4). Duplicate-feature sweep on EMBER-2018 LightGBM/XGBoost. **No problem-space component.**
  *Opportunity:* pullback depends on a only through Pa, so **features with identical provenance columns
  are merged in the problem space**. Any credit-splitting among *mechanically* redundant features (L2) cancels
  out exactly after pullback. Statistically (but not mechanically) redundant features are not fixed. This is a
  small, clean proposition plus an experiment (rerun their duplicate sweep; feature-space credit moves about 50%, problem-space
  explanation unchanged). Raff co-authored EMBER2024 and MalConv, so expect overlap with the reviewer pool.
- **Severi et al. 2021.** Built a pefile-based watermarking utility by hand. Dropped *all* hashed features
  ("preimage resistance") and any feature affected by more than one other feature, noting "many of the features are derived
  from the same underlying structures." Only 17 of about 2,400 EMBER features were usable. Example triggers: header version
  fields, linker versions, MZ_count, section counts. *Uses:* (1) a motivating example of hand-built feature→binary mapping;
  (2) a ready-made trigger design for the planted-ground-truth experiment, where pullback should land on the header fields and section table.
- **Rosenberg et al. 2020.** Feature-by-feature, type-specific modifications chosen by hand; argues per-feature
  manual effort is the bottleneck. Supports motivation; no general mapping.
- **FINER (CCS 2023).** Formalizes problem space 𝒵 → feature space ℱ → vector space 𝒱 with an explanation map
  ω: 𝒱→ℱ and "intelligible components" (functions) via a decomposition h: 𝒵→𝒟. **Explicitly excludes
  pattern-driven classifiers** (hand-crafted statistics such as Drebin and EMBER), arguing that information lost in
  α (citing "hashing trick for Ember") gives their explanations low "semantic capacity" and that they cannot be mapped back
  to raw program elements. They only map explanations for data-driven classifiers, where ℱ keeps opcodes and tokens.
  **Strong motivating citation: a top-venue paper states our gap. Our localizability analysis quantifies their
  "semantic capacity" claim instead of assuming it.** Uses a 5-analyst feedback study (we will not).
- **TRUSTEE artifact-reliance (2026).** Surrogate-tree explanations, then *manual byte-level analysis of PE files* to
  confirm that top features are packing/metadata artifacts. A direct use case: pullback automates their manual step.
- **Virtual Inspection Layers (Vielhaben et al. 2024).** Relevance moved via LRP through *invertible linear*
  transforms (DFT, STDFT). Non-invertible or approximately invertible transforms are named as future work. **Pushforward through a
  non-invertible program into a representation the model never computes is beyond this.**
- **Aryal et al. 2024.** Byte-level SHAP on MalConv aggregated into PE regions (headers, sections, subsections),
  then used to choose regions for adversarial injection, weighing region importance against integrity of modification.
  *Precedent for region aggregation and for "attribution × modifiability"* in an *attack* setting on a *raw-byte* model.
  Our manipulability hypothesis differs (feature-based models, a defensive per-decision signal) but must cite this.
- **Citation check (Semantic Scholar).** None of G-DeepSHAP's 290 citing papers applies it to program feature
  extractors or malware. The Severi arXiv record lists only 18 citers (the USENIX record is separate) and none does problem-space explanation.

## Revised contribution list (draft)

- **C1 Framing.** Feature-space vs. problem-space explanations for detectors with program feature
  extractors. Pullback and pushforward are positioned as an extension of rescale-rule propagation to
  non-differentiable programs. Modest properties: soundness, completeness, composition, coarsening,
  and perfect-reconstruction characterizations used as diagnostics.
- **C2 Provenance construction.** An instrumented EMBER2018/2024 extractor that emits P, plus a
  black-box (perturbation-based) estimator for arbitrary extractors. Open source.
- **C3 Localizability analysis.** How much of a production-style detector's decision can be pinned to
  regions of the binary, broken down by feature group, EMBER version and sample class (packed/unpacked, malware/benign).
- **C4 Evaluation.** Problem-space faithfulness against direct problem-space explainers at a fraction of
  the cost; planted-trigger ground truth.
- **C5 Cross-representation comparison.** MalConv vs. GBDT reliance in a shared space via pushforward/pullback.

## Theory implication

Drop the proposed T1 ("exactness") as a *new* result, since G-DeepSHAP App. A.5.3 already covers
linear chains. Instead:

- Adopt the baseline-relative definition P_ij = φ_i(σ_j; z, z̄) / Δσ_j as the *principled* meaning of
  "proportional influence". This fills the gap in the proposal's Definition 3.
- **Modest new lemma (in our comfort zone):** for additive feature groups (byte histogram, counts,
  string-based counts, etc.), the cheap *structural* provenance from instrumentation equals the
  Shapley-of-σ provenance. So instrumentation is not an ad-hoc heuristic; it is the exact rescale-rule
  matrix for those groups. For non-additive groups (entropy windows, hashing), measure the gap
  empirically (instrumented vs. black-box estimator).
- Open design question: our axioms require P ≥ 0, but rescale-rule matrices can be signed. Decide
  whether to allow signed provenance or keep structural (unsigned) provenance plus a stated limitation.

## Annotated bibliography by cluster

### A. Attribution propagation / chain rules (threat to theory novelty)
- **Chen, Lundberg, Lee. "Explaining a series of models by propagating Shapley values." Nature Comms 2022 (arXiv 2105.00108).** [read] Generalized rescale rule ψ_i = φ̂(h_i)·(ψ_{i+1} ⊘ Δf_i);
  efficiency at every stage (Thm 1); exact for linear chains (A.5.3); group rescale rule for overlapping groups.
  Stages must be linear, deep or tree models. *Differs:* no program extractors, no diagnostics, no problem-space validation. **Must cite and position against. Not in bib.**
- Shrikumar et al., DeepLIFT (rescale rule, chain rule for multipliers). [bib]
- Bach et al. 2015, LRP (relevance conservation via redistribution). **Not in bib.**
- Vielhaben, Lapuschkin, Montavon, Samek. "Explainable AI for time series via virtual inspection layers." Pattern Recognition 2024. [abstract] Relevance moved through an invertible transform (DFT) into an interpretable domain. Closest to pushforward. **Not in bib.**

### B. Grouping / aggregation (pullback with 0/1 P; coarsening)
- Jullum et al. "groupShapley" (arXiv 2106.12228). [abstract] Summing Shapley values within a group ≠ the group's Shapley value in general (equal only under conditions). Relevant caveat for coarsening/region-level claims. **Not in bib.**
- Hwang et al. "SHAP-based explanations are sensitive to feature representation." FAccT 2025. [abstract] Representation choices (e.g., histograms) change attributions. Supports the "σ matters" motivation. **Not in bib.**
- Attribution aggregation in vision/NLP (AGG2EXP, arXiv 2407.16653; Inseq). [abstract] Pixel→segment, token→word.
- Ribeiro et al., LIME "interpretable representation". [bib]

### C. Malware XAI (the gap)
- **Mohseni, Raff, Gaur. "Why is SHAP not a reliable standalone explanation framework for malware detection?" arXiv 2609.04626, Sept 2026.** [abstract+summary] EMBER-2018/2024 and BODMAS; LightGBM/XGBoost. No mapping to the problem space. **Most important recent paper to engage with. Not in bib.**
- Mohammed & Zhang. "Beyond the Wrapper: ... artifact reliance ... TRUSTEE." arXiv 2605.07034, May 2026. [abstract] Top features are packing artifacts and PE metadata. Localization in the binary would directly strengthen this kind of analysis. **Read in full. Not in bib.**
- Li & Gadyatskaya. "Position: The explainability paradox." EuroS&PW 2024. [bib] Motivating position paper; check that our "problem-space explanation paradox" naming does not clash.
- Warnecke et al. "Evaluating explanation methods for deep learning in security." EuroS&P 2020. [bib] Evaluation criteria (descriptive accuracy, sparsity, efficiency). Reuse their metrics vocabulary.
- He et al. FINER. CCS 2023. [bib][abstract] Explanation fidelity/intelligibility for risk detectors. **Read in full** to confirm it does not map features to artifacts.
- Fan et al. 2020 (sanity checks for Android interpreters); Wu 2021; Zhu 2024; Mitchell 2024 (hierarchical LIME on opcodes). [bib]
- Švec et al. "Semantic data representation (PE Malware Ontology)." 2024/2025. [abstract] Maps EMBER features to *concepts*, not to file locations.
- Manai et al. "Impact of feature encoding on malware classification explainability." ECAI 2023. [abstract] Minor.
- PhilaeX (arXiv 2207.00740). [title only] **Check.**

### D. Byte-level explanations of raw models (problem-space side; MalConv)
- Coull & Gardner 2019 (activation analysis); Bose et al. 2020 (MalConv mechanisms); Demetrio et al. 2019 (IG on MalConv shows header reliance). [bib]
- Aryal et al. "Explainability guided adversarial evasion attacks." arXiv 2405.01728. [abstract] SHAP DeepExplainer on MalConv, section/subsection granularity. A ready-made "direct problem-space explanation" baseline for MalConv and a region-granularity precedent.

### E. Explanations used to act in the problem space (attacks/backdoors)
- **Severi et al. "Explanation-guided backdoor poisoning attacks against malware classifiers." USENIX Sec 2021.** [abstract] SHAP on EMBER selects trigger features; a hand-built PE watermarking utility realizes them. Use it for the planted-trigger evaluation and as an application. **Not in bib.**
- Rosenberg et al. IJCNN 2020. [bib][abstract] Feature-by-feature modification guided by explanations; mapping done by hand. **Read in full.**
- Sun et al. "Mate! Are you really aware?" ESEC/FSE 2023. [abstract] Explainability-guided robustness testing in feature space. **Not in bib.**
- Pierazzi et al. 2020 problem-space attacks. [bib] Source of the feature-space/problem-space vocabulary; inverse feature-mapping problem; side-effect features.
- Demetrio et al. "Adversarial EXEmples" (TOPS 2021) and secml-malware. [abstract] Functionality-preserving PE manipulations; a toolkit for validity-preserving perturbations in the problem-space baselines. **Not in bib.**

### F. Ground-truth evaluation via planted triggers (methodology precedent)
- Lin et al. 2021 "What do you see? Evaluation of XAI using trojaned models"; BackX (arXiv 2405.02344). [abstract] Planted triggers as attribution ground truth is established methodology. Our novelty is doing it in the *problem space* of malware. **Not in bib.**
- Hooker et al. (ROAR) [bib]; Adebayo et al. sanity checks [bib].

### G. Provenance / lineage / taint (formal and systems precedents; also the naming collision)
- Green, Karvounarakis, Tannen. "Provenance semirings." PODS 2007. Formal precedent for compositional provenance. **Not in bib.**
- Dynamic taint tracking (libdft, DFSan; Neutaint, arXiv 1907.03756, uses neural sensitivity as continuous taint). A possible way to *automate* instrumentation; Neutaint is close in spirit to black-box provenance estimation.
- Provenance-based IDS (Kairos, Poirot, etc.). [bib] Naming collision only.

### H. Ensembles of static detectors with different feature sets (motivation for CM; checked 2026-10-12)
Framing agreed with the user: "static detectors with different feature sets" are deployed and studied together. There
is **no evidence that raw-byte and EMBER-style detectors specifically are paired in production**; do not claim it.
- Microsoft Defender ATP, "Inside out: get to know the advanced technologies at the core of Microsoft Defender ATP
  next generation protection" (Microsoft Security blog, 2019-06-24). Cloud "metadata-based ML engine": "Specialized ML
  models, which include file type-specific models, feature-specific models, and adversary-hardened [models]" that
  "analyze a featurized description of suspicious files"; "Stacked ensemble classifiers combine results from these
  models to make a real-time verdict". A separate "file classification ML engine": "Multi-class, deep neural network
  classifiers examine full file contents". Also "Detonating a Bad Rabbit: Windows Defender Antivirus and layered
  machine learning defenses" (2017-12-11). **Not in bib.**
- Kaspersky, "The multilayered security model in Kaspersky Lab products" (blog, 2017): "ML²", ML in several layers
  (decision-tree ensembles on the client, deep models elsewhere). Marketing-level; cite only as supporting. **Not in bib.**
- Quiring, Pirch, Reimsbach, Arp, Rieck. "Against All Odds: Winning the Defense Challenge in an Evasion Competition
  with Diversification." arXiv 2010.09569, 2020. PEberus won the 2020 Microsoft MLSEC defender challenge. Read §IV:
  four EMBER-based GBDTs (variations), a monotonic GBDT on byte skipgrams (3-skip 3-grams), and YARA signatures; "A PE
  file is classified as malware if *any* of the system's components considers it as malicious" (max-combination);
  "multiple classification models use distinct feature sets ... so that ... an attacker has to evade different feature
  sets at the same time". Closest precedent for diverse-feature-set ensembles as a defense; also a precedent for AU (the audit)
  (rules alongside learned models). **Not in bib.**
- MLSEC 2019 (Endgame, with MRG-Effitas and VM-Ray; DEF CON 27 AI Village): the attack targets were "three trained
  models": "MalConv trained on EMBER 2018 binaries", "Non-negative MalConv trained on EMBER 2018 binaries", and "A
  LightGBM model trained on the EMBER 2018 features dataset" (README, github.com/endgameinc/malware_evasion_competition).
  50 samples, a point per model evaded (150 max; scoring from participant write-ups, e.g. ESET's 133/150; the
  competition site is offline). The direct precedent for our exact pair. **Not in bib.**
- Salman, Zhao, Asghar, Ikram, Kaushik, Kaafar. "On the Robustness of Malware Detectors to Adversarial Samples."
  SECAI 2024 (arXiv 2408.02310). Raw-byte, EMBER, and LSH-based detectors; "adversarial program binaries crafted for
  one detector are generally less effective against others"; evaluates an ensemble (majority vote) as mitigation.
  **Not in bib.**
- Transfer between raw-byte and EMBER-style models is reported inconsistently (e.g., MAB-Malware, Song et al.,
  arXiv 2003.03100: 28-47% transfer to an EMBER model; others find LightGBM robust to MalConv-crafted samples). For
  CM: whether two members share an attack surface is model-pair-specific and unsettled, which a per-file map
  addresses. Numbers taken from search summaries; read the papers before citing them.

## To read in full (priority order)
1. Mohseni/Raff/Gaur 2026 (SHAP on EMBER critique): exact experiments and which claims our framework addresses.
2. G-DeepSHAP Methods §6.4–6.7 and App. A.5: exact statements to cite; check the group-rescale normalization against our D†.
3. Severi et al. 2021: watermark utility, which features were used. Basis for the planted-trigger design.
4. FINER (CCS 2023) and Rosenberg 2020: confirm neither maps feature explanations to artifacts.
5. TRUSTEE artifact-reliance paper (2026).
6. Vielhaben et al. 2024 (virtual inspection layers): how they justify transferring relevance across domains.
7. Aryal et al. 2024: region granularity for MalConv SHAP.

## Searches still worth running
- Google Scholar "cited by" on G-DeepSHAP for anyone applying it to non-model preprocessing.
- "Cited by" on Severi 2021 for problem-space trigger localization or forensics.
- Android (Drebin-style features map almost one-to-one to code locations, so H ≈ 0). Has anyone localized Drebin explanations in smali? This would be a useful contrast case for the localizability analysis if time allows.
