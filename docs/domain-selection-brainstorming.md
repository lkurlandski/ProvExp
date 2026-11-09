# Domain Selection: Initial Brainstorming

*Status: early brainstorming, not a decision. Citations are from memory and should be verified, and the post-mid-2026 literature still needs checking.*

## Goal

Pick three classification domains for the adversarial ML paper. Each domain should share the structure of the current PE/EMBER setting:

- **Complex objects** in the problem space, with real constraints on what counts as a valid adversarial example.
- **Tabular feature vectors** extracted from those objects.
- A feature mapping that is **neither invertible nor differentiable**.

**Hard requirement from the framework:** most features must be fixed-length tabular features (counts, statistics, binary indicators, histograms). Models that consume structured representations directly, such as control-flow graphs, ASTs, or raw graphs, are out of scope.

Structure-*derived* features are fine as long as the model consumes a vector. EMBER itself parses a PE and emits a vector, and that is the pattern to look for.

## What "diverse" should mean

Three different file types don't make a strong paper. Three domains that stress different parts of the problem-space formalism do. Following Pierazzi et al. (IEEE S&P 2020), which frames the problem in terms of transformations, problem-space constraints, and side-effect features, the axes worth varying are:

1. **Transformation type**
   - *Additive/structural:* append, pad, add sections or imports. Most PE attacks are of this kind.
   - *Semantics-preserving rewriting:* the object is restructured but its behavior is unchanged.
   - *Causal/temporal:* edits limited to insertion or delay, never removal or reordering.

2. **Functionality oracle**
   - *Expensive and noisy:* sandbox execution (PE).
   - *Cheap and exact:* compiles and passes tests.
   - *Perceptual:* renders the same as the original.

3. **Attacker control**
   - *Full:* the attacker owns the whole object.
   - *Partial:* some features come from things the attacker cannot touch, such as infrastructure, third-party content, or the other side of a conversation.

4. **Feature extractor behavior**
   - *Stateless parsing:* each object maps to its own vector.
   - *Stateful/aggregated:* features depend on time windows or history, so a single edit can cascade into many features, including those of *other* samples.

A strong triad should cover different points on most of these axes.

## Domains considered and rejected (for now)

### Android malware (APK, DREBIN)

Rejected as a primary domain because it scores close to PE on nearly every axis. Attacks are mostly additive manifest and API features, and the attacker has full control over a static file-format object. It would add volume without adding diversity.

### Flow-level network intrusion detection (CICFlowMeter-style CSVs)

Rejected in this form. At the flow-CSV level the constraints reduce to arithmetic relationships between features, which is too simple.

The datasets are also a reviewer risk:
- CIC-IDS2017 has known labeling and generation problems (Engelen et al., IEEE SPW 2021).
- The area is heavily exposed to the pitfalls in Arp et al., "Dos and Don'ts of ML in Computer Security" (USENIX Security 2022).

**Caveat:** traffic is *not* inherently too simple. At the packet level the constraints become hard:
- Edits must respect protocol and TCP state.
- Timing is causal; packets can be delayed but not sent earlier.
- The attacker controls only one direction of the conversation.
- With a stateful extractor such as Kitsune's damped windows (Mirsky et al., NDSS 2018), one inserted packet changes the features of *future* samples.

Packet-level traffic remains a viable alternative (see below).

## Candidate domains

### 1. Phishing webpage detection (HTML + URL)

The top candidate to pair with PE.

- **Features:** handcrafted URL lexical statistics plus HTML/DOM statistics, all tabular, typically used with tree ensembles. This fits the framework well.
- **Problem-space constraint:** perceptual and functional. The page must render the same and still collect credentials.
- **Attacker control:** partial. Some features, such as domain age, WHOIS data, and hosting, are infrastructure-dependent and expensive or impossible to change. This is a clear contrast with PE.
- **Oracle:** cheap. Headless rendering plus a visual-similarity check.
- **Prior work:**
  - Apruzzese et al., "SpacePhish," ACSAC 2022
  - Montaruli et al., query-efficient adversarial HTML attacks, AISec 2023

  These define the space without exhausting it.

### 2. Source code authorship attribution

The most structurally different from PE.

- **Features:** code stylometry (Caliskan-Islam et al., USENIX Security 2015) uses lexical, layout, and AST-derived term-frequency features in a random forest.
  - AST *n-gram counts* are tabular and fit the framework. Models that consume the AST directly would not.
  - **Check:** how much of the predictive power comes from AST-derived features, and whether the framework handles their high-dimensional, sparse nature.
- **Problem-space constraint:** semantics-preserving transformations, such as loop forms, declaration styles, and API substitutions.
- **Oracle:** exact and cheap. The code compiles and passes the original test cases.
- **Task structure:** multiclass attribution rather than binary detection. This supports both *untargeted* attacks (dodging) and *targeted* attacks (impersonation), which adds variety to the evaluation.
- **Baseline:** Quiring et al., "Misleading Authorship Attribution of Source Code using Adversarial Learning," USENIX Security 2019.
- **Risk:** reviewers may see it as less "security-critical" than detection. Frame it around anonymity, forensics, and plagiarism detection.

### 3. Website fingerprinting (alternative third domain)

- **Features:** k-FP (Hayes & Danezis, USENIX Security 2016) uses about 175 handcrafted trace statistics with a random forest. CUMUL-style features are also tabular. Both fit the framework.
  - Deep-learning WF attacks on raw traces are out of scope for the framework.
- **Problem-space constraint:** packets can only be padded or delayed, at a cost in bandwidth and latency. Removal and reordering are not allowed.
- **Data:** public datasets exist.
- **Narrative note:** the roles are inverted. The adversarial ML "attacker" is the privacy defender, which makes for an interesting discussion point but complicates the framing.
- **Prior work:** the defense literature (padding schemes and adversarial-perturbation defenses) is substantial, so novelty needs to come from the framework.

### Alternative: packet-level NIDS

Viable if the work is done from pcaps with a stateful tabular extractor (e.g., Kitsune features) and a replay-based functionality oracle. It is the strongest way to cover the "stateful extractor" axis. It needs more engineering, though, and its oracle is weaker than code compilation.

### Honorable mentions

| Domain | Fits tabular requirement? | Why not primary |
|---|---|---|
| Malicious JavaScript (e.g., HideNoSeek, Fass et al., CCS 2019) | Partly, if AST features are flattened to counts | It is code again, which overlaps with authorship attribution |
| PDF malware (Mimicus, Šrndić & Laskov, S&P 2014; EvadeML, Xu et al., NDSS 2016) | Yes, for PDFrate-style features | Too close to PE: both are file-format malware |
| Graph-based ad/tracker blocking (AdGraph, S&P 2020; WebGraph, USENIX Security 2022) | Partly. Features are graph-derived but fed to a random forest | Heavy infrastructure. Much of the signal is structural, which is near the framework's limit |
| ICS anomaly detection (e.g., Erba et al., ACSAC 2020) | Yes, for sensor values | Usually reconstruction-based rather than classification |

## Proposed triad

| | PE (EMBER) | Phishing webpages | Code authorship |
|---|---|---|---|
| Object | Binary executable | HTML + URL | Source code |
| Transformation type | Additive/structural | Markup edits, render-preserving | Semantics-preserving rewrites |
| Functionality oracle | Sandbox (costly, noisy) | Render + visual similarity (cheap) | Compile + tests (exact, cheap) |
| Attacker control | Full | Partial (infrastructure features) | Full |
| Feature extractor | Stateless parsing | Stateless parsing | Stateless parsing (AST-derived counts) |
| Task | Binary detection | Binary detection | Multiclass; targeted and untargeted |

**Gap:** none of the three exercise *stateful/aggregated* feature extraction. Swapping code authorship for packet-level NIDS or website fingerprinting would cover that axis. The cost is losing the exact oracle and the multiclass/targeted setting.

## Go/no-go checklist for each domain

Before committing to a domain, confirm:

- [ ] **Framework fit:** what fraction of the standard feature set is the right feature type for the framework, and does performance hold up using only those features?
- [ ] **Dataset:** a credible public dataset with no known labeling or generation problems.
- [ ] **Target model:** a reproducible victim model from prior work, so reviewers can't argue the target was chosen to be weak.
- [ ] **Oracle:** functionality checking that can be fully automated.
- [ ] **Oracle budget:** defenses such as adversarial training need far more oracle calls than attack demonstrations. Estimate the cost per call times the expected number of calls.
- [ ] **Literature currency:** check for work since mid-2026 in each candidate domain.

## Key references (verify before citing)

- Pierazzi, Pendlebury, Cortellazzi, Cavallaro. "Intriguing Properties of Adversarial ML Attacks in the Problem Space." IEEE S&P 2020.
- Arp et al. "Dos and Don'ts of Machine Learning in Computer Security." USENIX Security 2022.
- Engelen, Rimmer, Joosen. "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study." IEEE SPW 2021.
- Mirsky et al. "Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection." NDSS 2018.
- Apruzzese et al. "SpacePhish: The Evasion-space of Adversarial Attacks against Phishing Website Detectors using Machine Learning." ACSAC 2022.
- Montaruli et al. "Raze to the Ground: Query-Efficient Adversarial HTML Attacks on Machine-Learning Phishing Webpage Detectors." AISec 2023.
- Caliskan-Islam et al. "De-anonymizing Programmers via Code Stylometry." USENIX Security 2015.
- Quiring, Maier, Rieck. "Misleading Authorship Attribution of Source Code using Adversarial Learning." USENIX Security 2019.
- Hayes, Danezis. "k-fingerprinting: A Robust Scalable Website Fingerprinting Technique." USENIX Security 2016.
- Fass, Backes, Stock. "HideNoSeek: Camouflaging Malicious JavaScript in Benign ASTs." CCS 2019.
- Šrndić, Laskov. "Practical Evasion of a Learning-Based Classifier: A Case Study." IEEE S&P 2014.
- Xu, Qi, Evans. "Automatically Evading Classifiers: A Case Study on PDF Malware Classifiers." NDSS 2016.
- Iqbal et al. "AdGraph: A Graph-Based Approach to Ad and Tracker Blocking." IEEE S&P 2020.
- Siby et al. "WebGraph: Capturing Advertising and Tracking Information Flows for Robust Blocking." USENIX Security 2022.
- Erba et al. "Constrained Concealment Attacks against Reconstruction-based Anomaly Detectors in Industrial Control Systems." ACSAC 2020.
