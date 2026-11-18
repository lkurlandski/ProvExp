# Third-party code

Vendored, patched copies of the attack toolkits used for direction A (Gimenez et al.'s eight black-box attacks). The
first commit adding each directory is the pristine upstream source; the patches follow as separate commits.

| Directory | Upstream | Version | License |
|---|---|---|---|
| `secml/` | PyPI sdist `secml-0.15.6.tar.gz` (sha256 `6bfe0765...6e335`) | 0.15.6 | Apache 2.0 |
| `secml_malware/` | github.com/pralab/secml_malware at `81f6bd901db4cbcd17beffe7f7af3b586028f033` | 0.4.2 | GPL 3.0 |
| `mab_malware/` | github.com/bitsecurerlab/MAB-malware at `91a518a49ae14d8eccb382cd7f8b704f9b8fce8e` | (2021-05-08) | none stated |

Omitted from `secml_malware/`: notebooks, Dockerfile, docs, examples, and the pretrained MalConv weights
(`secml_malware/data/trained/pretrained_malconv.pth`). Omitted from `secml/`: `update/` and the egg-info.

The patches make them run on our environment (Python 3.14, NumPy 2, LIEF 1.0); none is needed because of the Python
version itself. One patch fixes an attack bug: secml-malware's content shift inserts its padding where section
content starts, not at the first section's offset, which can be 0 (`utils/pe_operations.py`; `docs/upstream-issues.md` §14). Install without dependencies (ours are in `requirements.txt`):

    VIRTUAL_ENV=$PWD/env uv pip install --no-deps -e third_party/secml -e third_party/secml_malware

`mab_malware/` (MAB-Malware, Song et al., AsiaCCS 2022) keeps only the attack's core: the MCTS and GP rewriters, the
Cuckoo and VM tooling, `chart/`, its tests, `workflow.png` and `MalConv.py` are omitted. It is not installed; our
driver `src/provexp/attacks/mab.py` imports it from the run directory (upstream reads `conf/configure.ini` from the current
directory at import time). Patches, each marked `# PATCH (ProvExp)`: the unused `pexpect` import dropped; the bundled
models (torch, ember) no longer imported, since the detector is ours; the donor-content listing sorted, so that runs
are reproducible across file systems. The section-adding action returns a file with no sections unchanged (it indexed an
empty section table; scale-up job 1046140). Upstream's threads and polled folders are replaced in the driver, not here.
The upstream repository states no license: keep this copy private, and link upstream in any public release.
