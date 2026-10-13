# `provexp` Package Design

Design notes for the `provexp` package: its data structures, conventions, and the thrember-instrumentation quirks.
Open questions are collected in [§9](#9-open-questions).

## 1. Scope and priorities

The package is the **library**: the data structures, operators, and statistics of the framework, one
provenance-instrumented feature set (EMBER-2024 / thrember v3, PE files only), and the data and model
utilities the experiments need. Experiment drivers and results storage live in `scripts/`, `run/`, and
`artifacts/`, not in the package.

Decisions:

| Topic | Decision |
|---|---|
| Datasets / features | EMBER-2024 PE files (Win32, Win64, .NET), EMBER feature version 3 only. |
| Generality | The core library knows nothing about PE files or EMBER. Everything feature-set-specific lives under `featuresets/`. |
| Elements | Bytes, everywhere. No PE-specific "atoms" in the core. H and O are defined and computed at byte level. |
| Sparse format | `BoxMatrix`: 2-d only (no use for N > 2), constant boxes plus keyed boxes (§3). |
| Normalization | Store raw contributions C; normalize columns lazily (§4). |
| Unattributable features | One policy in `Provenance` decides what an empty column means (§4.2): `"null"` (default), `"uniform"`, or `"ignore"`. Every place where this matters is marked `NOTE (Axiom 3)`. |
| Instrumenting EMBER | thrember's `features.py` copied verbatim and committed, then modified by pure additions (no original line changed). |
| Test reference | A verbatim copy of only `features.py` (+ `pefile_warnings.txt`) in `tests/reference/`. |
| Dependencies | No dependency on the `thrember` package. |
| Environment | `uv` + `pip`, Python 3.14, venv in `env/`. Nothing from the miniconda installation. |
| Models | GBDT (LightGBM), MLP, and MalConv medium (EMBER-2024), in `src/provexp/models/`. |
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
├── checkpoints/                GITIGNORED: malconv-seed{0,1,2}.pt (seed 0 = SSViT/release/models/malconv-medium.pt)
└── tests/
    ├── reference/              verbatim thrember features.py (never edited)
    ├── data/                   GITIGNORED: real binaries (malware); tests skip if absent
    ├── strategies.py           hypothesis strategies
    └── test_*.py
```

Deferred to when they are needed:

- `estimate.py`: perturbation-based estimation of P for any feature extractor, which treats σ as a black box. It is
  feature-set-agnostic, so it belongs in the core.
- `featureset.py`: a protocol for feature sets (`extract(bytes) -> (x, Provenance)`), to formalize once there is a
  second feature set.
- `models/gbdt.py`, `models/mlp.py`, `data/tabular.py`, `scripts/train_classic.py`: the GBDT/MLP pieces of SSViT's
  `main_classic.py` (now implemented in the package).

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

Feature sets never fabricate provenance: a feature to which no byte contributes has an empty column in C. Such a
column cannot satisfy both Axiom 2 (sums to one) and Axiom 3 (only influencing elements are nonzero). The `empty`
policy decides what it means at normalization time, so changing it requires no recomputation:

- `"null"` (default): augment the problem-space with a null element ⊥ ("no part of the input"), the sole source
  of every empty feature. P has m + 1 rows. **All three axioms hold** over Z ∪ {⊥}, every proposition and theorem
  carries over unchanged, real bytes never receive fabricated attribution, and b_⊥ is exactly the attribution that
  cannot be localized in the input. Cost: empty features look unambiguous (one-hot at ⊥) and overlap each other at
  ⊥ in the statistics, which is mathematically correct but should be read alongside the share of attributable features.
- `"uniform"`: spread uniformly over all bytes. Satisfies Axioms 1 and 2, contradicts 3.
  Exactly `"null"` followed by spreading b_⊥ evenly over the bytes (tested).
- `"ignore"`: leave the column empty. Satisfies Axioms 1 and 3, not 2; breaks completeness of pullback. Equivalent to
  the manuscript's "exclude j from P" without changing feature indices.

On the fixture files, 1,100–2,400 of the 2,568 EMBER features have empty columns (mostly empty hash buckets and
absent structures), so this choice is consequential.

### 4.3 Statistics

Definitions as in the manuscript (revised 2026-10-08; `docs/cp_plan.md`): ambiguity H_j = −Σ_i P_ij log P_ij with
effective support exp(H_j), overlap O_j = 1 − Σ_i P_ij² / D_ii (one minus the diagonal of the pull-push matrix
M = PᵀD†P), and the push-pull diagonal N_ii = Σ_j P_ij² / D_ii. All are exact at byte level and computed from the
canonical pieces of P (`Provenance.pieces`, cached), without forming M or N:

- Row quantities (D, Σ_j P_ij², which rows are live) by difference arrays over the pieces.
- H_j and |A_j| per piece (each piece is a constant interval of a column).
- The diagonal of M per piece as val² · Σ_{rows of the piece} D⁺_ii, summed directly with `np.add.reduceat`
  (differences of a prefix sum over a 4 MB file lose about 1e-5 of precision).
- `pull_push_matrix` expands P into a sparse matrix and forms M (n × n) explicitly; it refuses inputs above
  `max_nnz` entries.

Cost (2026-10-08, PB1 files): 0.34 s for a 220 KB file and 9.4 s for a 4 MB file for the statistics, 0.3 s and 3.9 s
for M. The earlier numba sweep computed the previous, pairwise overlap; it was removed with that definition.

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
- **Nondeterminism:** `PEFormatWarnings` maps each warning to the first matching pattern while iterating over a `set`
  of strings, so for warnings matching two overlapping patterns the feature depends on the interpreter's hash seed
  (about 0.1% of files). Featurize with `PYTHONHASHSEED=0` for run-to-run determinism.
- Versus the released EMBER-2024 features (untruncated files), `strings:entropy` differs by a few float32 ulps in
  about a third of files (numpy version); everything else is identical apart from the item above.

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
| `src/main_classic.py` | GBDT params, MLP, metrics, the npz shard loader | Now in `src/provexp/models/` and `data/`. |

Data locations (read-only): binaries in `/shared/datasets/EMBER-2024/data/{tr,vl,ts}` (SimpleDB); split index
files in `SSViT/index/ember2024/us/`.

## 7. Testing

`pytest -n 16 tests`: 420 tests (≈5 minutes, dominated by thrember on the fixture files).

- `test_boxmatrix.py`: every operation against dense numpy on random matrices (hypothesis).
- `test_provenance.py`: normalization, transfers, and statistics against dense implementations of the manuscript's
  definitions, and every proposition and theorem as a property test.
- `test_ember2024.py`: §5.3.
- `test_malconv.py`: shapes, padding, checkpoint conversion, predictions on fixtures.

## 8. Implementation status

The library is complete and tested: `BoxMatrix`, `Provenance` (operators and statistics), the instrumented
EMBER-2024 feature set, SimpleDB access and the feature store, the fixture script, and the GBDT, MLP, and MalConv
models.

## 9. Open questions

- **Q1 Empty policy.** Decided: `"null"` is the default. The manuscript's Definition 3 now includes the null element
  (Axiom 4) and a new definition introduces provenance coverage κ and explanation localizability ℓ(a), both of
  which `Provenance` implements (`coverage`, `localizability`).
- **Q2 Weights within columns.** Decided: keep one unit per item for count features, one per byte for content
  features.
- **Q3 Statistics at scale.** Resolved (§4.3; first by a numba sweep for the pairwise overlap, since 2026-10-08 from the
  canonical pieces for the round-trip definitions).
