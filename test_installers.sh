#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${SCRIPT_DIR}/tests/installation/run_installer_tests.sh"

if [[ ! -x "${RUNNER}" ]]; then
  echo "[ERROR] Missing test runner: ${RUNNER}" >&2
  echo "[INFO] Run: chmod +x tests/installation/run_installer_tests.sh" >&2
  exit 1
fi

exec "${RUNNER}" "$@"
