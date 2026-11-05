#!/bin/bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

pushd "$1" > /dev/null
make clean
make
popd > /dev/null
