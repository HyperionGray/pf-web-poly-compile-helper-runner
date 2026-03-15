#!/usr/bin/env bash
# Compatibility wrapper for installer test suite.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[INFO] test_installers.sh now delegates to tests/installation/run_installer_tests.sh"
exec "${REPO_ROOT}/tests/installation/run_installer_tests.sh" "$@"
