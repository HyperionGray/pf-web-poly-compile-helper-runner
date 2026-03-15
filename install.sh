#!/usr/bin/env bash
# Compatibility entrypoint for repository-root installer usage.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${SCRIPT_DIR}/scripts/install.sh"

if [[ ! -x "${TARGET}" ]]; then
    echo "[ERROR] Expected installer not found or not executable: ${TARGET}" >&2
    exit 1
fi

exec "${TARGET}" "$@"
