# RIT Research Computing, partition tigris (aarch64). Only after pipeline/setup/check.sh has shown featurization
# bit-identical to the stored vectors here (floating-point results may differ across architectures).
# TO CONFIRM on the head node: as for sporc.sh.
export EMBER2024_DATA="${EMBER2024_DATA:-/shared/rc/admalware/datasets/EMBER-2024/data}"
CORES=36
spack load gcc/wmxcv23
