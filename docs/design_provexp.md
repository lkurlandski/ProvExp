# `provexp` Package Design (preliminary)

Status: draft for discussion, 2026-10-06. Open questions are collected in [§9](#9-open-questions-for-the-next-round).

## 1. Scope and priorities

Phase 1 builds the **library**: the data structures, operators, and statistics of the framework, one
provenance-instrumented feature set (EMBER-2024 / thrember v3, PE files only), and the data and model
utilities the experiments will need. Large-scale processing, experiment drivers, storage of results, and
CLIs are out of scope for this phase.

Decisions already made:

| Topic | Decision |
|---|---|
| Datasets / features | EMBER-2024 PE files (Win32, Win64, .NET), EMBER feature version 3 only. No EMBER-2018, no v2 features. |
| Generality | The core library knows nothing about PE files or EMBER. Everything feature-set-specific lives under `featuresets/`. |
| Element granularity | Byte-level provenance. No PE-specific "atoms" in the core. Coarser views (blocks, regions) may be layered on later. |
| Memory/storage | A custom sparse N-d array that stores non-zeros as hyper-rectangles ("boxes") (§3). |
| Instrumenting EMBER | Copy thrember's `features.py` verbatim, commit, then modify it to track provenance, so the enhancements show up as a readable diff. |
| Dependencies | No dependency on the `thrember` package; only the copied file. |
| Environment | `uv` + `pip`, Python 3.14. Nothing from the miniconda installation. |
| Semantics of "influences" | An implementation convention, documented per feature group in code (§5.3). Not a framework-level decision. |
| Unattributable features | Provenance spread uniformly over all elements. No separate attribution taxonomy. |
| Results storage | Not the package's job. |
| Reuse from SSViT | Copy what we need from `/home/lk3591/Documents/code/SSViT` (§6). |

## 2. Package layout

```
ProvExp/
├── pyproject.toml              uv-managed; Python 3.14
├── src/provexp/
│   ├── boxarray.py             BoxArray: sparse N-d array of hyper-rectangles (§3)
│   ├── provenance.py           Provenance: P + metadata; axioms; pullback/pushforward;
│   │                           cyclic operators; ambiguity/overlap; compose; coarsen (§4)
│   ├── featureset.py           FeatureSet protocol: extract(bytes) -> (x, Provenance)
│   ├── estimate.py             perturbation-based provenance estimation for any σ (§4.4)
│   ├── featuresets/
│   │   └── ember2024/
│   │       ├── LICENSE, NOTICE         thrember is Apache-2.0
│   │       ├── features.py             thrember features.py, instrumented
│   │       └── features_reference.py   verbatim thrember (see Q3)
│   ├── data/
│   │   ├── simpledb.py         copied from SSViT (readers only)
│   │   └── tabular.py          npz shard loader (names/labels/timestamps/features)
│   ├── models/
│   │   ├── gbdt.py             EMBER-2024 LightGBM params + train/predict helpers
│   │   ├── mlp.py              SOREL-style MLP
│   │   └── malconv.py          standard-memory MalConv + checkpoint converter
│   └── metrics.py              compute_metrics (binary classification)
├── scripts/
│   ├── make_fixtures.py        pull N samples from the SimpleDB into tests/data/
│   └── train_classic.py        simplified main_classic.py (gbdt, mlp only); Phase 2
└── tests/
    ├── data/                   GITIGNORED: real binaries (malware); tests skip if absent
    └── test_*.py
```

**What `estimate.py` is** (previously `extractors/blackbox.py`): an estimator of P that treats σ as a black
box. Perturb an element (or a group of elements), re-run σ, and record which features change and by how much.
It works for *any* feature extractor, so it belongs in the core rather than under `featuresets/`. It is
needed for (a) validating the instrumented P and (b) feature sets nobody has instrumented. Planned for
Phase 3; nothing beyond the interface is needed now.

## 3. `BoxArray`: hyper-rectangle sparse array

### 3.1 Why a custom format (the numbers)

For a 4 MiB file and 2,568 features, a dense P is 4,194,304 × 2,568 × 4 B ≈ **40 GiB**. COO/CSR is not
enough either: every feature whose provenance covers the whole file (`size`, `entropy`, `is_pe`, the 88
pefile-warning features under the uniform convention) costs one non-zero per byte, about 90 × 4 M ≈ 380 M
non-zeros. Most provenance is a few contiguous ranges per feature, which boxes represent exactly in O(1)
space each.

**Consequence:** `to_dense()` on a byte-level P is only practical for small files or after coarsening. The
core linear algebra (pullback, pushforward, row/column sums) must therefore run *directly on boxes*.
`to_dense()` / `to_scipy()` remain available for small inputs, tests, and coarsened arrays, and raise
an error above a configurable size.

### 3.2 Representation

An N-d array of shape `S = (s_0, …, s_{N-1})`. Its value is the **sum** of a list of boxes (overlaps add):

- **Constant box:** `(lo[N], hi[N], w)` adds weight `w` to every cell in `[lo, hi)`. Stored
  column-wise as numpy arrays (`lo: int64[B, N]`, `hi: int64[B, N]`, `w: float32[B]`) for vectorized operations.
- **Keyed box (proposed extension, see Q1):** `(lo, hi, w, key_ref, key_dim, src_dim, offset)` within
  `[lo, hi)` along `src_dim`, puts weight `w` at index `offset + key[i]` along `key_dim`. This is needed for
  *scatter* features, where a byte's column is determined by its value. Three groups need it: the byte histogram
  (column = byte), the byte-entropy histogram (column = row-offset + byte>>4 per window), and the strings'
  printable-character histogram (column = byte − 0x20 per string). As constant boxes these need one box per
  byte (4 M boxes); as keyed boxes, one per contiguous range. The key array (e.g., the file's bytes) is
  shared by reference, not copied.

### 3.3 Operations (minimum set)

Construction (`add_box`, `add_keyed_box`, `concat` along a dim with offset), `shape`, `sum(axis)`,
`matvec`/`rmatvec` for 2-d, `coarsen(axis, partition)`, `slice` on a dim, `to_dense`, `to_scipy`.
Not exhaustive by design: add operations when a use appears.

## 4. `Provenance`

### 4.1 Contents

A 2-d `BoxArray` of **raw contributions** C (elements × features) plus metadata: `n_elements`,
`feature_names`, and optional `feature_groups`. Proposal (Q2): store raw contributions and apply column
normalization lazily, `P = C · diag(1/colsum(C))`. Column sums are cheap to compute from boxes, and
contributions are the natural quantity while extracting (e.g., "this byte adds 1 to this count").

### 4.2 Operators

All operate on boxes, never forming dense P.

- `pullback(a) -> b = P a`
- `pushforward(b) -> a = Pᵀ D† b`, with `D = diag(rowsum(P))`
- `pull_push(a)`, `push_pull(b)`, cyclic errors
- `coarsen(partition)`: sum rows into groups (blocks, regions). Commutes with pullback.
- `compose(P1, P2)`: P1·P2 for chained extractors (later; needs a box × box product or a dense fallback)
- `check_axioms()`: nonnegativity, column normalization, no all-zero columns

### 4.3 Statistics

`ambiguity()` (Hⱼ, Ĥⱼ, H) and `overlap()` (Oⱼ, Ôⱼ, O).

- H is exact on boxes by sweeping each column's piecewise-constant profile.
- O requires the pairwise intersections Iⱼₖ = Σᵢ min(Pᵢⱼ, Pᵢₖ). This can be computed exactly with a sweep over
  shared supports, but the 2,568² pairs make it the most expensive statistic (see Q5).

### 4.4 Estimation (`estimate.py`, Phase 3)

`estimate(sigma, z, perturb, elements) -> Provenance`. Interface only for now.

## 5. EMBER-2024 feature set

### 5.1 Procedure

1. Copy `thrember/features.py` (thrember 0.1.0) verbatim into `featuresets/ember2024/` with the Apache-2.0
   `LICENSE` and a `NOTICE` stating origin and modifications. **Commit.**
2. Modify it in place so that each `FeatureType` also returns the provenance of its columns, and
   `PEFeatureExtractor` assembles the full `Provenance` (column offsets match the feature vector).
3. Tests: the instrumented `feature_vector(bytez)` must be **bit-identical** to the original on every
   fixture file. That needs the original code at test time (see Q3).

Pins for parity with the reference: `pefile==2024.8.26`, `signify==0.7.1` (newer signify may change the
authenticode API), plus a `scikit-learn` version whose `FeatureHasher` (murmurhash) output matches.
All three resolve on Python 3.14 (checked with a uv dry-run, together with numpy 2.5, scipy 1.18, torch 2.13+cu129,
lightgbm 4.7, numba 0.68, shap 0.52).

### 5.2 Feature groups (2,568 features)

| Group | Dim | Provenance source (convention) | Box kind |
|---|---|---|---|
| general | 7 | size, entropy, is_pe: all bytes; start_bytes: bytes 0–3 | constant |
| histogram | 256 | each byte → its value's bin | keyed |
| byteentropy | 256 | each byte → (window entropy bin, byte>>4) for each window containing it | keyed (one per window) |
| strings | 177 | string spans; printable dist per char; regex counts → matching strings | constant + keyed |
| header | 74 | exact byte ranges of COFF/optional/DOS fields (`get_field_absolute_offset`) | constant |
| section | 224 | section-table entry fields; section contents (entropy); overlay | constant |
| imports | 1282 | DLL-name strings, hint/name entries, ordinal thunks (`name_offset`, `ordinal_offset`) | constant |
| exports | 129 | export-name strings (`ExportData.name_offset`); `exports[0]` is a constant (thrember quirk) | constant |
| datadirectories | 34 | data-directory entries in the optional header | constant |
| richheader | 33 | Rich header entries | constant |
| authenticode | 8 | certificate blob (security directory); `signing_time_diff` also includes the COFF timestamp | constant |
| pefilewarnings | 88 | uniform over all bytes | constant |

### 5.3 Conventions (documented in code, not framework decisions)

- A byte contributes to a feature when the feature's value is computed *from* it: counted, read, or
  hashed. Normalization denominators and parse pointers (e.g., `e_lfanew` deciding where headers are read)
  do not count as contributions.
- Hashed features: an item contributes |±1|. With `alternate_sign=True` (sections, exports, Rich header), two
  items in one bucket can cancel to a feature value of 0. They still both appear in the provenance.
- Within an item, contribution is uniform over its bytes unless the computation says otherwise.

## 6. Reuse from SSViT

| Source | What | Notes |
|---|---|---|
| `src/simpledb.py` | `Sample`, `SimpleDB`, `SimpleDBReader`, `SimpleDBIterator`, `CreateSimpleDB` | Drop `MetadataDB*` (LIEF structure metadata; not needed). Deps: numpy, pandas, polars, tqdm, zstandard. |
| `src/main_classic.py` | `EMBER2024_LIGHTGBM_PARAMS`, `EMBER2024_CATEGORICAL`, `MLP`, `load_datafile(s)`, `compute_metrics`, gbdt + mlp training path | Becomes `scripts/train_classic.py` + `models/`. Drop PCS, RF, SVM, LR, caching. Main use is Phase 2. |
| `src/architectures.py` | `GatedConvolution`, `MalConv` (max pooling), `ClassifificationHead`, `load_fc4ai_state_dict` | Trimmed to a standalone standard-memory MalConv; no FiLM, sharded embeddings, or low-mem paths. |
| `exeformer/exeformer.py` | `convert_released_malconv_state_dict` and its helpers, `PRETRAINED_CONFIGS["malconv"]` | Checkpoint keys: `module.model.{embd.embedding, conv_1, conv_2, fc_1, fc_2}`; embedding is sharded (1012×8 → 257×8). |

Data locations (read-only):

- Binaries: `/shared/datasets/EMBER-2024/data/{tr,vl,ts}` (SimpleDB; 2,022/264/528 zstd shards; files truncated to 4 MiB at preprocessing).
- Split index files: `SSViT/index/ember2024/us/{tr,vl,ts}.txt` (sha, label, timestamp).
- MalConv checkpoints: `SSViT/release/models/malconv-{small,medium,large}.pt` (EMBER-2024, first 46 weeks).
- Existing tabular features (`SSViT/tabular/ember2024`) were computed from the released JSONL, i.e., on
  **full-length** files. We recompute features on the truncated binaries with our extractor. The existing features
  serve only as a sanity check for files under 4 MiB.

## 7. Testing

- Unit tests for `BoxArray` against dense numpy on small random arrays (every operation).
- Property tests (hypothesis) for every proposition/theorem in the manuscript: soundness, completeness,
  independence, the perfect-reconstruction iff conditions, ambiguity/overlap characterizations, coarsening.
- EMBER-2024: bit-identical feature vectors vs. the reference; axioms hold on every fixture; spot checks
  (e.g., the COFF timestamp feature's provenance is exactly the 4 `TimeDateStamp` bytes).
- MalConv: the trimmed model reproduces the SSViT/exeformer predictions on fixture files.
- Fixture binaries live in `tests/data/` (gitignored, since they are malware). Tests that need them skip when absent.

## 8. Phase 1 done means

The library works and is tested: `BoxArray`, `Provenance` (operators + statistics), the instrumented
EMBER-2024 feature set (bit-identical to thrember, axioms hold), SimpleDB access, and the MalConv loader,
all exercised on a small fixture set. No large-scale runs.

## 9. Open questions for the next round

- **Q1 Keyed boxes.** Are keyed boxes an acceptable extension of the hyper-rectangle design, for the
  histogram, byte-entropy, and printable-char features? (Alternatives: one box per byte for those groups, or a
  separate COO component inside `BoxArray`.)
- **Q2 Raw contributions + lazy normalization.** Store C and normalize columns on use, or store P directly?
- **Q3 Reference copy for tests.** Bit-identical tests need the original thrember code at test time. Keep a
  verbatim `features_reference.py` (never edited) next to the instrumented `features.py`? The git history still
  shows the clean "verbatim → instrumented" diff on `features.py`.
- **Q4 Dimensionality.** P is 2-d. Is there an N>2 use you have in mind (e.g., a batch dimension, or
  per-window provenance)? If not, we implement N-d boxes but test and optimize 2-d.
- **Q5 Granularity of H and O.** Both depend on the element granularity (bytes vs. blocks vs. regions). Merging
  rows can only increase overlap. Do we define and report them at byte level (exact sweep, O is expensive)
  or at a coarser level?
- **Q6 Uniform provenance for unattributable features.** This conflicts with Axiom 3 as written in the
  manuscript (your own note there says the uniform option "breaks Axiom 3"). Fine to revise the axiom later; flagging it so it isn't forgotten.
- **Q7 Models.** MalConv medium only, or all three sizes? MalConvGCG too (`MalConvGCGStandardMemory`
  exists in SSViT)? `train_classic.py`: gbdt + mlp only?
- **Q8 Follow-up edits.** `PLAN.md` still mentions EMBER-2018. Update it to the EMBER-2024-only scope?
