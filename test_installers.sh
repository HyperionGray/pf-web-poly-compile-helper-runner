#!/usr/bin/env bash
# Backward-compatible wrapper for installer tests.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${SCRIPT_DIR}/tests/installation/run_installer_tests.sh"

if [[ ! -x "$RUNNER" ]]; then
    echo "ERROR: Missing test runner: $RUNNER" >&2
    exit 1
fi

echo "[INFO] Delegating to tests/installation/run_installer_tests.sh"
exec "$RUNNER" "$@"
