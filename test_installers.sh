#!/usr/bin/env bash
# Backward-compatible entrypoint for installer tests.
# Canonical test implementation lives in test_pf_installers.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/test_pf_installers.sh" "$@"
