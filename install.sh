#!/usr/bin/env bash
# Top-level compatibility wrapper for scripts/install.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

exec "${REPO_ROOT}/scripts/install.sh" "$@"
