#!/usr/bin/env bash
# Compatibility entrypoint for one-command installer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/quick-install.sh" "$@"
