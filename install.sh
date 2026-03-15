#!/usr/bin/env bash
# install.sh - Repository-root wrapper for the native installer

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/install.sh" "$@"
