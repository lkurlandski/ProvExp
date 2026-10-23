# Third-party code

Vendored, patched copies of the attack toolkits used for direction A (Gimenez et al.'s eight black-box attacks). The
first commit adding each directory is the pristine upstream source; the patches follow as separate commits.

| Directory | Upstream | Version | License |
|---|---|---|---|
| `secml/` | PyPI sdist `secml-0.15.6.tar.gz` (sha256 `6bfe0765...6e335`) | 0.15.6 | Apache 2.0 |
| `secml_malware/` | github.com/pralab/secml_malware at `81f6bd901db4cbcd17beffe7f7af3b586028f033` | 0.4.2 | GPL 3.0 |

Omitted from `secml_malware/`: notebooks, Dockerfile, docs, examples, and the pretrained MalConv weights
(`secml_malware/data/trained/pretrained_malconv.pth`). Omitted from `secml/`: `update/` and the egg-info.

The patches make them run on our environment (Python 3.14, NumPy 2, LIEF 1.0); none is needed because of the Python
version itself. Install without dependencies (ours are in `requirements.txt`):

    VIRTUAL_ENV=$PWD/env uv pip install --no-deps -e third_party/secml -e third_party/secml_malware
