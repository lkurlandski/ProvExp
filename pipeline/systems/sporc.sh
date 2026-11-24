# RIT Research Computing, cluster sporc (x86_64), confirmed on the head node sporcsubmit 2026-11-24 (session 111):
#   CPU partitions sporc-cpu, tier3 (and debug, 1 day, for tests), nodes of 36 to 56 cores, ~340-380 GB; the run.sh
#   headers target tigris, so override them at submission: --partition=sporc-cpu --constraint=intel for a CPU step;
#   --partition=tier3 --constraint=intel --gres=gpu:1 for a GPU step (A100 40 GB on skl-a-*, H100 80 GB on spr-a-02).
#   Maximum walltime 20 days; uv's Python 3.14 works (env-x86_64/); featurization is bit-identical to the reference.
# Large outputs: artifacts -> /shared/rc/admalware/provexp, shared with tigris. CORES is the default NUM_WORKERS
# outside a job, i.e. on the head node: 2, as on tigris (run nothing heavy there).
export EMBER2024_DATA="${EMBER2024_DATA:-/shared/rc/admalware/datasets/EMBER-2024/data}"
CORES=2
spack load gcc/lhqcen5
