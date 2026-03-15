#!/usr/bin/env bash
# Legacy entrypoint preserved for compatibility.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${SCRIPT_DIR}/run_installer_tests.sh"

if [[ ! -x "$RUNNER" ]]; then
    echo "ERROR: Missing test runner: $RUNNER" >&2
    exit 1
fi

echo "[INFO] test_installer_round3.sh is deprecated; delegating to run_installer_tests.sh"
exec "$RUNNER" "$@"
