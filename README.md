# ProvExp

Explanation provenance for malware detectors. See `CLAUDE.md` for the layout and conventions, `docs/status.md` for the
current state, and `run/README.md` for the commands that produced `artifacts/`.

## Setup

```bash
uv venv --python 3.14 env
VIRTUAL_ENV=$PWD/env uv pip install -r requirements.txt -r requirements-dev.txt
VIRTUAL_ENV=$PWD/env uv pip install -e .
```

## External tools for 3-C (rule-based detectors)

Not installed yet; to be run by the user. Rule sets and tool installs go under `artifacts/` (the scratch symlink), so
they stay out of git.

### YARA

```bash
# yara-python bundles libyara; no system package is needed.
VIRTUAL_ENV=$PWD/env uv pip install "yara-python~=4.5"
env/bin/python -c "import yara; print(yara.__version__)"

# Generic rules (Yara-Rules), pinned to the commit checked on 2026-10-12.
mkdir -p artifacts/rules
git clone https://github.com/Yara-Rules/rules artifacts/rules/yara-rules
git -C artifacts/rules/yara-rules checkout 0f93570194a80d2f2032869055808b0ddcdfb360
```

The rule directories of interest are `packers/`, `crypto/`, `antidebug_antivm/`, and `capabilities/`. Only string
matches give byte offsets; conditions on the `pe` module (e.g., `pe.imports(...)`) do not.

### capa with Ghidra (only if we use capa)

capa's default backend (vivisect) took more than 10 minutes on one 2.7 MB file; Ghidra is faster. Check the commands
below against capa's README for the installed version (the Ghidra integration has changed across capa releases).

```bash
# Ghidra needs a JDK 21 (e.g., the distribution's openjdk-21-jdk, or a Temurin tarball under artifacts/tools/).
java -version

# Ghidra: unpack a release from https://github.com/NationalSecurityAgency/ghidra/releases (11.3 or later bundles PyGhidra).
mkdir -p artifacts/tools
unzip ghidra_<version>_PUBLIC_<date>.zip -d artifacts/tools/
export GHIDRA_INSTALL_DIR=$PWD/artifacts/tools/ghidra_<version>_PUBLIC

# capa as a library, with PyGhidra for its Ghidra backend, and the rules (the PyPI package does not ship them).
VIRTUAL_ENV=$PWD/env uv pip install flare-capa pyghidra
git clone https://github.com/mandiant/capa-rules artifacts/rules/capa-rules
git -C artifacts/rules/capa-rules checkout v<capa version>   # match the rules to the installed capa

# Smoke test on one file: time it, and check that the JSON result lists match addresses.
time env/bin/capa --backend ghidra -r artifacts/rules/capa-rules -j <file> > capa_smoke.json
```
