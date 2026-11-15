# 2-features: files and feature stores

- `files/`: the release's metadata (`build_metadata.py`) and the evaluation set (`select_files.py --complete_only`,
  `run.sh`): 1,000 malware and 1,000 benign test files below 4 MB, near-duplicates removed, at most 10 per family. Every
  attack runs on its malware, every `1-audit` step on all of it.
- `featurize/`: the feature stores, one per extractor: EMBER's features (thrember, quirks patched, LIEF's overlay
  rule), the re-encoding over sums, Gimenez et al.'s 40 expert features. `check_features.py` compares ours with
  EMBER's released vectors; `refeaturize_nonpe.py` re-extracts the files pefile rejects. Output:
  `2-features/<extractor>/<split>/` (`features.npy`, `meta.parquet`), `manifest.json`. Runtime: ~0.1-0.2 s per file
  and extractor.
