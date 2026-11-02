#!/bin/bash

set -eou pipefail

pushd manuscript
make clean
make
popd
