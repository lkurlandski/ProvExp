# Sourced by pipeline/common.sh and pipeline/setup/build_env.sh before anything else.
# tigris (aarch64) and sporc (x86_64) share the home directory, and ~/.bashrc points uv's interpreters and cache, the
# user's tools (~/.local/sw/<arch>) and the Triton and CUDA caches at the machine's architecture. sbatch passes the
# submitting shell's environment to the job, so a job submitted across clusters (sbatch -M tigris from sporc, or the
# reverse) would start with the other architecture's paths. This re-points them; it changes nothing when the job runs
# on the architecture it was submitted from.
_arch_now="$(uname -m)"
if [[ -n "${MYARCH:-}" && "$MYARCH" != "$_arch_now" ]]; then
  echo "Submitted from $MYARCH, running on $_arch_now: re-pointing the per-architecture paths."
  for _arch_var in PATH LD_LIBRARY_PATH MANPATH CMAKE_PREFIX_PATH SWROOT XDG_CACHE_HOME TRITON_CACHE_DIR \
    CUDA_CACHE_PATH UV_INSTALL_DIR UV_PYTHON_INSTALL_DIR UV_PYTHON_BIN_DIR UV_TOOL_DIR UV_TOOL_BIN_DIR UV_CACHE_DIR; do
    if [[ -n "${!_arch_var:-}" ]]; then
      _arch_val="${!_arch_var}"
      _arch_val="${_arch_val//\/sw\/$MYARCH/\/sw\/$_arch_now}"
      _arch_val="${_arch_val//\/.cache\/$MYARCH/\/.cache\/$_arch_now}"
      export "$_arch_var=$_arch_val"
    fi
  done
  export MYARCH="$_arch_now"
  unset _arch_var _arch_val
fi
unset _arch_now
