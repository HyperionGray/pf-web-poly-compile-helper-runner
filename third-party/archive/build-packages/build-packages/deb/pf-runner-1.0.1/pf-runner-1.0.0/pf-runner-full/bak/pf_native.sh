#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYBIN=""
if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  PYBIN="$SCRIPT_DIR/.venv/bin/python"
elif [[ -x "$SCRIPT_DIR/../.venv/bin/python" ]]; then
  PYBIN="$SCRIPT_DIR/../.venv/bin/python"
elif [[ -x "$SCRIPT_DIR/../.pf-venv/bin/python" ]]; then
  PYBIN="$SCRIPT_DIR/../.pf-venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYBIN="$(command -v python3)"
fi

if [[ -z "$PYBIN" ]]; then
  echo "Error: python3 not found for native runner." >&2
  exit 1
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYBIN" "$SCRIPT_DIR/pf_main.py" "$@"

