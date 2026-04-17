#!/usr/bin/env bash
# Backward-compatible wrapper to the canonical deb packaging entrypoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/../deb/build-packages.sh" "$@"
