# 2-features: files and feature stores

- `files/`: the release's metadata (`build_metadata.py`) and the selection of the pilot files (`select_files.py`); the
  scale-up's file lists are a protocol item.
- `featurize/`: the feature stores, one per extractor: EMBER's features (thrember, quirks patched, LIEF's overlay
  rule), the re-encoding over sums, Gimenez et al.'s 40 expert features. `check_features.py` compares ours with
  EMBER's released vectors; `refeaturize_nonpe.py` re-extracts the files pefile rejects. Output:
  `2-features/<extractor>/<split>/` (`features.npy`, `meta.parquet`), `manifest.json`. Runtime: ~0.1-0.2 s per file
  and extractor.
