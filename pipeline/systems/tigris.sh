# RIT Research Computing, partition tigris (aarch64), confirmed on the head node 2026-11-16 (session 71):
#   gg-a nodes: 144 cores, 450 GB, no GPU (the run.sh headers select them with --constraint=gg);
#   gh-a nodes: 72 cores, 550 GB, one GH200 (--constraint=gh; 4-detectors/learned only);
#   maximum walltime 20 days; uv's Python 3.14 works; featurization is bit-identical to the reference here.
# Large outputs: artifacts -> /shared/rc/admalware/provexp (persistent; /scratch is purged in maintenance windows).
# The headers ask for half a gg node (72 cores), a quarter per array task; NUM_WORKERS follows the job's
# SLURM_CPUS_PER_TASK (pipeline/common.sh), CORES only outside a job. The head node is shared: run nothing heavy there.
export EMBER2024_DATA="${EMBER2024_DATA:-/shared/rc/admalware/datasets/EMBER-2024/data}"
CORES=2
spack load gcc/wmxcv23
