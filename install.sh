#!/usr/bin/env bash
# Compatibility entrypoint that forwards to scripts/install.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/install.sh" "$@"
