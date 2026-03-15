#!/usr/bin/env bash
# Compatibility wrapper: keep legacy scripts/install.sh callers working.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

exec "${REPO_ROOT}/install.sh" "$@"
