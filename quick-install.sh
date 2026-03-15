#!/usr/bin/env bash
# Compatibility entrypoint for quick installer.
# Canonical implementation lives in scripts/quick-install.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="${SCRIPT_DIR}/scripts/quick-install.sh"

if [[ ! -x "$TARGET_SCRIPT" ]]; then
    echo "Error: quick installer not found or not executable: $TARGET_SCRIPT" >&2
    exit 1
fi

exec "$TARGET_SCRIPT" "$@"
