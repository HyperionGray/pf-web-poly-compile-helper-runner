#!/usr/bin/env bash
# Run pf commands with the Emscripten SDK already sourced so builds find emcc/wasm-pack
set -euo pipefail

EMSDK_ROOT="${EMSDK_ROOT:-}"
if [[ -z "$EMSDK_ROOT" ]]; then
  EMSDK_ROOT="$(ls -d /home/punk/emsdk-* 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$EMSDK_ROOT" ]] || [[ ! -f "${EMSDK_ROOT}/emsdk_env.sh" ]]; then
  echo "❌ Unable to locate emsdk. Set EMSDK_ROOT to the root of your emsdk installation (e.g. /home/punk/emsdk-2.0.0) before running this script."
  exit 1
fi

source "${EMSDK_ROOT}/emsdk_env.sh"

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <pf-task> [pf-args...]"
  echo "Example: $0 web-toolchain-check"
  exit 1
fi

pf "$@"
