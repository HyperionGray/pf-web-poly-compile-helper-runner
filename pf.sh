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

if [ -x "$ROOT_DIR/pf-runner-full/pf_universal" ]; then
  exec "$ROOT_DIR/pf-runner-full/pf_universal" "$@"
fi

if [ -x "$ROOT_DIR/pf-runner-full/pf" ]; then
  exec "$ROOT_DIR/pf-runner-full/pf" "$@"
fi
echo "pf.sh: could not find pf executable (tried pf-runner-full/pf_universal and pf-runner-full/pf)" >&2
exit 1
