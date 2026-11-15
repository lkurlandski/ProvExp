# setup

- `build_env.sh`: builds `env/` from `requirements-lock.txt` (SETUP.md, step 2). ~10 min.
- `check.sh`: the system check (SETUP.md, step 5): dataset found, featurization bit-identical to `reference/` (32 test
  files, three extractors; sums regenerated in session 66 after `fix_quirks`), the tests. ~5 min.
- `make_fixtures.py`: copies a small, diverse set of executables into `tests/data/` (gitignored: real malware).
- `identity_check.sh`, `compare_outputs.py`: the check that a reorganization of the code changed no computation. Five
  computations on a pilot slice through their `run.sh`, compared with the old code's outputs (run 146, tag
  `pilot-final`); only timing fields and the manifests' commit may differ. ~10-15 min.
  Since session 66 (the RESERVED directory and the three string patterns fixed, `fix_quirks`) the sums store also
  differs in exactly those features, the catalogue in its observed-cell counts, and the adaptive rows on `0485edc2...`
  (4458d06's escape writes); a run without other differences passes (`docs/evidence/extractor-audit.md`, §2).
