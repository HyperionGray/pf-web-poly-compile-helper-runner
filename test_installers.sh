#!/usr/bin/env bash
# Compatibility wrapper for installer test suite.
# Delegates to the maintained test runner under tests/installation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RUNNER="${SCRIPT_DIR}/tests/installation/run_installer_tests.sh"

if [[ ! -x "${TEST_RUNNER}" ]]; then
    echo "[ERROR] Installer test runner not found or not executable: ${TEST_RUNNER}" >&2
    exit 1
fi

exec "${TEST_RUNNER}" "$@"
