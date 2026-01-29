#!/usr/bin/env bash
set -euo pipefail

# Resolve symlink to find real repo root (works when installed in ~/.local/bin)
_pf_self="${BASH_SOURCE[0]}"
while [ -L "$_pf_self" ]; do
  _pf_target="$(readlink "$_pf_self")"
  if [[ "$_pf_target" = /* ]]; then
    _pf_self="$_pf_target"
  else
    _pf_self="$(cd "$(dirname "$_pf_self")" && cd "$(dirname "$_pf_target")" && pwd)/$(basename "$_pf_target")"
  fi
done
ROOT_DIR="$(cd "$(dirname "$_pf_self")" && pwd)"

# Allow opting into source runner (helps when pf_universal lags behind local edits)
if [ "${PF_USE_SOURCE:-}" = "1" ]; then
  if [ -f "$ROOT_DIR/pf-runner-full/pf_main.py" ]; then
    export PYTHONPATH="$ROOT_DIR/pf-runner-full:${PYTHONPATH:-}"
    exec python3 "$ROOT_DIR/pf-runner-full/pf_main.py" "$@"
  fi
fi

if [ -x "$ROOT_DIR/pf-runner-full/pf_universal" ]; then
  exec "$ROOT_DIR/pf-runner-full/pf_universal" "$@"
fi

# Fallback: source runner without venv
if [ -f "$ROOT_DIR/pf-runner-full/pf_main.py" ]; then
  export PYTHONPATH="$ROOT_DIR/pf-runner-full:${PYTHONPATH:-}"
  exec python3 "$ROOT_DIR/pf-runner-full/pf_main.py" "$@"
fi

echo "pf.sh: could not find pf executable (tried pf-runner-full/pf_universal and pf-runner/.pf-venv/bin/pf)" >&2
exit 1
