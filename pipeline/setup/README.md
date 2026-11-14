# setup

- `build_env.sh`: builds `env/` from `requirements-lock.txt` (SETUP.md, step 2). ~10 min.
- `check.sh`: the system check (SETUP.md, step 5): dataset found, featurization bit-identical to `reference/` (32 test
  files, three extractors, from run 146's featurization on this server), the tests. ~5 min.
- `make_fixtures.py`: copies a small, diverse set of executables into `tests/data/` (gitignored: real malware).
- `identity_check.sh`, `compare_outputs.py`: the check that a reorganization of the code changed no computation. Five
  computations on a pilot slice through their `run.sh`, compared with the old code's outputs (run 146, tag
  `pilot-final`); only timing fields and the manifests' commit may differ. ~10-15 min.
