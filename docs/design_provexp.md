# `provexp` Package Design

Status: Phase 1 core implemented, 2026-10-06. Open questions are collected in [§9](#9-open-questions).

## 1. Scope and priorities

Phase 1 builds the **library**: the data structures, operators, and statistics of the framework, one
provenance-instrumented feature set (EMBER-2024 / thrember v3, PE files only), and the data and model
utilities the experiments will need. Large-scale processing, experiment drivers, storage of results, and
CLIs are out of scope for this phase.

Decisions:

| Topic | Decision |
|---|---|
| Datasets / features | EMBER-2024 PE files (Win32, Win64, .NET), EMBER feature version 3 only. |
| Generality | The core library knows nothing about PE files or EMBER. Everything feature-set-specific lives under `featuresets/`. |
| Elements | Bytes, everywhere. No PE-specific "atoms" in the core. H and O are defined and computed at byte level. |
| Sparse format | `BoxMatrix`: 2-d only (no use for N > 2), constant boxes plus keyed boxes (§3). |
| Normalization | Store raw contributions C; normalize columns lazily (§4). |
| Unattributable features | One policy in `Provenance` decides what an empty column means, chosen for easy recovery (§4.2). Every place where this matters is marked `NOTE (Axiom 3)`. |
| Instrumenting EMBER | thrember's `features.py` copied verbatim and committed, then modified by pure additions (no original line changed). |
| Test reference | A verbatim copy of only `features.py` (+ `pefile_warnings.txt`) in `tests/reference/`. |
| Dependencies | No dependency on the `thrember` package. |
| Environment | `uv` + `pip`, Python 3.14, venv in `env/`. Nothing from the miniconda installation. |
| Models | MalConv medium only (EMBER-2024). |
| Results storage | Not the package's job. |

## 2. Package layout (as implemented)

```
ProvExp/
├── pyproject.toml, requirements.txt, requirements-dev.txt, ruff.toml, mypy.ini, pytest.ini
├── src/provexp/
│   ├── boxmatrix.py            BoxMatrix: sparse matrix of constant and keyed boxes (§3)
│   ├── provenance.py           Provenance: lazy normalization, empty policy, transfers, statistics (§4)
│   ├── featuresets/ember2024/
│   │   ├── features.py         thrember features.py + provenance (§5)
│   │   ├── pefile_warnings.txt
│   │   └── LICENSE, NOTICE     thrember is Apache-2.0
│   ├── data/simpledb.py        copied from SSViT (readers and writer)
│   └── models/malconv.py       standard-memory MalConv + released-checkpoint loader
├── scripts/make_fixtures.py    copies a diverse set of binaries into tests/data/
├── checkpoints/                GITIGNORED: malconv-medium.pt (copied from SSViT/release/models)
└── tests/
    ├── reference/              verbatim thrember features.py (never edited)
    ├── data/                   GITIGNORED: real binaries (malware); tests skip if absent
    ├── strategies.py           hypothesis strategies
    └── test_*.py
```

Deferred to when they are needed:

- `estimate.py`: perturbation-based estimation of P for any feature extractor, which treats σ as a black box. It is
  feature-set-agnostic, so it belongs in the core. Phase 3.
- `featureset.py`: a protocol for feature sets (`extract(bytes) -> (x, Provenance)`), to formalize once there is a
  second feature set.
- `models/gbdt.py`, `models/mlp.py`, `data/tabular.py`, `scripts/train_classic.py`: the GBDT/MLP pieces of SSViT's
  `main_classic.py`. These depend on featurizing the dataset with our extractor (Phase 2).

## 3. `BoxMatrix`

A sparse (m, n) matrix whose value is the **sum** of its boxes (overlaps add):

- **Constant box** `(r0, r1, c0, c1, w)`: adds w to rows [r0, r1) × columns [c0, c1).
- **Keyed box** `(r0, r1, c, k, w)`: adds w to entry (i, c + key_k[i]) for every row i in [r0, r1). Keys are
  registered integer arrays of length m, stored by reference (e.g., the file's bytes). One keyed box covers a whole
  byte histogram; one per window covers the byte-entropy histogram.

Operations: `add_boxes`, `add_key`, `add_keyed_boxes` (rows clipped to the matrix, empty boxes dropped), `hstack`,
`matvec`, `rmatvec`, `pieces` (canonical form: disjoint constant intervals per column), `to_dense`, `to_scipy`
(both refuse large outputs).

`matvec`/`rmatvec` use prefix sums plus difference arrays: O(boxes + m + n + rows covered by keyed boxes). Integer
coverage counting restores **exact zeros** wherever no box contributes, which the soundness of the pullback and the
division by row sums in the pushforward depend on (the floating-point residue was about 1e-18 and broke both).

## 4. `Provenance`

### 4.1 Contents and operators

Raw contributions C (a `BoxMatrix`), feature names, and the empty policy. P = C·diag(1/colsum(C)) is never formed.
`pullback`, `pushforward`, `pull_push`, `push_pull`, the cyclic errors, `rowsum`, `ambiguity`, `overlap`,
`check_axioms`, and `to_dense` (small inputs only).

### 4.2 Empty columns (the Axiom 3 question)

Feature sets never fabricate provenance: a feature to which no byte contributes has an empty column in C. The
`empty` policy decides what that means at normalization time, so changing it later requires no recomputation:

- `"uniform"` (default for now): spread the feature uniformly over all bytes. Satisfies Axioms 1 and 2, contradicts 3.
- `"ignore"`: leave the column empty. Pullback/pushforward ignore the feature, statistics exclude it. Satisfies
  Axioms 1 and 3, not 2. Equivalent to the manuscript's "exclude j from P" without changing feature indices.

**This matters more than expected:** on the fixture files, 1,100–2,400 of the 2,568 EMBER features have empty
columns. Most are empty hash buckets and absent structures (e.g., no exports). See Q1.

### 4.3 Statistics

Both are exact at byte level and computed from the canonical form. Overlap avoids the O(n²) pairs of features: within
each elementary row segment it sorts the active values, and the feature of rank r shares
Σ_{s<r} q_s + q_r·(t − r) mass with the others.

Worst case (synthetic, 4 MiB, ~90 whole-file features, 20k small boxes, keyed histograms): construct 0.8 s,
pullback 0.7 s, pushforward 1.2 s, ambiguity 8 s, **overlap 69 s / 3.5 GB peak**. Overlap is the optimization
target if we compute it at dataset scale (see Q3).

## 5. EMBER-2024 feature set

### 5.1 Provenance conventions (documented at the top of `features.py`)

- A byte contributes to a feature if the feature's value is computed from it (counted, read, hashed). Indirect
  influence (normalizing denominators, pointers that say where to read) does not count.
- Count-like features: one unit per item, spread uniformly over the item's bytes. Content features (sizes,
  entropies, histograms): one unit per byte.
- Hashed features: every item that hashes into the bucket contributes, regardless of its sign.
- Byte ranges are clipped to the (possibly truncated) file.
- Features with no contributions: `general:is_pe`, all `pefilewarnings` features, and constant features (below).

### 5.2 thrember quirks found while instrumenting

- `section:min_entropy`, `section:min_size_ratio`, `section:min_vsize_ratio` are **always 0**:
  `process_raw_features` appends a 0 to lists of nonnegative values before taking the minimum.
- `exports:num_exports` is `len(exports_hashed)`, i.e., **always 128** (or 0 without exports).
- `datadirectories` skips the last data directory (normally RESERVED), so `reserved_size` and
  `reserved_virtual_address` are always 0.
- `imports`: a later import descriptor for the same DLL replaces the functions of an earlier one.
- Files in the EMBER-2024 SimpleDB are truncated at **4,000,000 bytes**, not 4 MiB.

### 5.3 Verification

On 45 fixture files (goodware and malware: signed, .NET, exports, overlay, no Rich header, no imports, odd section
counts, tiny, truncated, unparsable):

- Feature vectors are **bit-identical** to thrember.
- Axioms 1–2 hold under both empty policies.
- Every count feature's raw contributions sum to exactly its value; histogram bins sum to the raw counts.
- Every header feature's provenance is exactly the bytes of its field, and those bytes decode to the value.
- Import/export/DLL name ranges contain the names.

Extraction with provenance takes 0.01–3 s per file (about 2× thrember).

### 5.4 Environment notes

`signify==0.7.1` (thrember's version) and `pefile==2024.8.26` are pinned. `oscrypto` is installed from git at
`d5f3437`, because the 1.3.0 release cannot parse the version string of OpenSSL ≥ 3.x.10 (the same fix as SSViT's
`env-thrember`).

## 6. Reuse from SSViT

| Source | Taken | Notes |
|---|---|---|
| `src/simpledb.py` | `Sample`, `SimpleDB`, `SimpleDBReader`, `SimpleDBIterator`, `roundup`, `CreateSimpleDB` | `MetadataDB*` and `SimpleDBOrganizer` dropped. |
| `exeformer/exeformer.py` | `_unwrap_state_dict`, `_unshard_embedding`, `convert_released_malconv_state_dict`, the medium MalConv config | |
| `MalConv2` (fork in `third_party/`) | The architecture, with MalConv2's parameter names | Standard memory instead of chunked max-pooling. Logits are **identical** (max difference 0.0) to MalConv2 on all 45 fixtures. |
| `src/main_classic.py` | Nothing yet | GBDT params, MLP, metrics, and the npz shard loader come over in Phase 2. |

Data locations (read-only): binaries in `/shared/datasets/EMBER-2024/data/{tr,vl,ts}` (SimpleDB); split index
files in `SSViT/index/ember2024/us/`.

## 7. Testing

`pytest -n 16 tests`: 416 tests (≈5 minutes, dominated by thrember on the fixture files).

- `test_boxmatrix.py`: every operation against dense numpy on random matrices (hypothesis).
- `test_provenance.py`: normalization, transfers, and statistics against dense implementations of the manuscript's
  definitions, and every proposition and theorem as a property test.
- `test_ember2024.py`: §5.3.
- `test_malconv.py`: shapes, padding, checkpoint conversion, predictions on fixtures.

## 8. Phase 1 status

Done: `BoxMatrix`, `Provenance`, the instrumented EMBER-2024 feature set, SimpleDB access, the fixture script, and
MalConv, all tested. Remaining Phase 1 items: none blocking. Optional: optimize `overlap` (Q3).

## 9. Open questions

- **Q1 Empty columns are the majority.** For a typical file, 65–95% of EMBER features have no contributions. Under
  `"uniform"`, any attribution assigned to them is smeared over the whole file, and tree explainers do attribute to
  absent features (e.g., "no import hashes into bucket 37"). Options: keep `"uniform"`; switch to `"ignore"`; or a
  middle ground where *absent-structure* features (an empty bucket) are attributed to the structure that would have
  contained them (e.g., the import directory). This is the most consequential open modeling decision.
- **Q2 Weights within columns.** Count features spread one unit per item over the item's bytes, so a long string
  gives each byte less weight than a short one. This is a convention; an alternative is one unit per byte everywhere.
- **Q3 Overlap at scale.** 69 s / 3.5 GB in the 4 MiB worst case. Optimizing it (treating keyed boxes as perturbations
  of a slowly varying base) is a contained piece of work, if we need O for the whole dataset.
