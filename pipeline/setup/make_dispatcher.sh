#!/bin/bash
#
# Writes the environment dispatcher: env/ holds no packages, only
#   env/bin/activate  sources env-$(uname -m)/bin/activate (env-aarch64 on tigris, env-x86_64 on sporc), so every
#                     `source env/bin/activate` (pipeline/common.sh, the old run/ scripts) picks the machine's environment;
#   env/bin/<tool>    one shim per executable found in any env-*/bin (python, pytest, ruff, mypy, ...), which execs
#                     env-$(uname -m)/bin/<tool>, so `env/bin/pytest ...` works on both clusters.
# The environments themselves are built by pipeline/setup/build_env.sh. Re-run this after installing a package that
# adds a new command. Light work: runs on a head node in a second.
#   DEST  where to write the dispatcher (default env). Writing into a staging directory (DEST=env.new) and renaming it
#         over env/ swaps the dispatcher in without a moment where env/bin/activate is missing.
set -euo pipefail
cd "$(dirname "$0")/../.."
DEST="${DEST:-env}"
if [[ -e "$DEST" && ! -f "$DEST/DISPATCHER" ]]; then
  echo "$DEST exists and is not a dispatcher (a real environment?); move it aside first." >&2
  exit 1
fi
shopt -s nullglob
envs=(env-*/bin/activate)
if [[ ${#envs[@]} -eq 0 ]]; then
  echo "No env-<arch>/ yet; build one with pipeline/setup/build_env.sh first." >&2
  exit 1
fi
rm -rf "$DEST"
mkdir -p "$DEST/bin"
echo "Dispatcher written by pipeline/setup/make_dispatcher.sh; the environments are env-<arch>/." > "$DEST/DISPATCHER"

cat > "$DEST/bin/activate" <<'EOF'
# env/bin/activate: dispatches to the environment for this machine's architecture (pipeline/setup/make_dispatcher.sh).
# Must be sourced, not executed.
if [ -n "${BASH_SOURCE:-}" ]; then
    _act_self="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
    _act_self="${(%):-%x}"
else
    _act_self="$0"
fi
_act_root=$(cd "$(dirname "$_act_self")/../.." && pwd)
_act_target="$_act_root/env-$(uname -m)/bin/activate"
if [ -f "$_act_target" ]; then
    . "$_act_target"
else
    echo "No $(uname -m) environment in $_act_root." >&2
    echo "Build it with: sbatch pipeline/setup/build_env.sh (SETUP.md, section 2)" >&2
fi
unset _act_self _act_root _act_target
EOF

cat > "$DEST/bin/_shim" <<'EOF'
#!/bin/sh
# Runs the command of the same name from env-$(uname -m)/bin (pipeline/setup/make_dispatcher.sh).
root=$(cd "$(dirname "$0")/../.." && pwd)
target="$root/env-$(uname -m)/bin/$(basename "$0")"
if [ ! -x "$target" ]; then
    echo "No $target: build env-$(uname -m) with pipeline/setup/build_env.sh (SETUP.md, section 2)." >&2
    exit 127
fi
exec "$target" "$@"
EOF
chmod +x "$DEST/bin/_shim"

n=0
for tool in env-*/bin/*; do
  name=$(basename "$tool")
  case $name in
    activate* | deactivate* | *.bat | *.ps1 | *.py | _shim) continue ;;
  esac
  if [[ -x "$tool" && ! -e "$DEST/bin/$name" ]]; then
    ln -s _shim "$DEST/bin/$name"
    n=$((n + 1))
  fi
done
echo "Wrote $DEST/bin/activate and $n shims for: ${envs[*]%/bin/activate}."
