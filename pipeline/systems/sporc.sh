# RIT Research Computing, partition sporc (x86_64). Run everything here first (SETUP.md).
# NOTE: the run.sh headers target tigris (--partition=tigris, --constraint=gg|gh). On sporc, override them at
# submission (sbatch --partition=sporc ...) and drop the constraint; set up when sporc is used (session 71).
# TO CONFIRM on the head node (best guesses from SSViT's scripts/create.py): cores per node (SSViT assumes 36), where
# large outputs should live (artifacts/ is a symlink; its target), maximum walltime, Python 3.14 through uv.
export EMBER2024_DATA="${EMBER2024_DATA:-/shared/rc/admalware/datasets/EMBER-2024/data}"
CORES=36
spack load gcc/lhqcen5
