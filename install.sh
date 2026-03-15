#!/usr/bin/env bash
# Compatibility entrypoint for native installer.
# Canonical implementation lives in scripts/install.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="${SCRIPT_DIR}/scripts/install.sh"

if [[ ! -x "$TARGET_SCRIPT" ]]; then
    echo "Error: installer not found or not executable: $TARGET_SCRIPT" >&2
    exit 1
fi

exec "$TARGET_SCRIPT" "$@"
