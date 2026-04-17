#!/usr/bin/env bash
# Compatibility wrapper for legacy debian/ path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/../deb/build-deb.sh" "$@"
