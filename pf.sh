#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -x "$ROOT_DIR/pf-runner-full/pf_universal" ]; then
  exec "$ROOT_DIR/pf-runner-full/pf_universal" "$@"
fi

if [ -x "$ROOT_DIR/pf-runner/.pf-venv/bin/pf" ]; then
  exec "$ROOT_DIR/pf-runner/.pf-venv/bin/pf" "$@"
fi

echo "pf.sh: could not find pf executable (tried pf-runner-full/pf_universal and pf-runner/.pf-venv/bin/pf)" >&2
exit 1
