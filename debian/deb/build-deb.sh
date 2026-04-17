#!/usr/bin/env bash
# Compatibility wrapper: canonical Debian package build script now lives in ./deb.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/../../deb/build-deb.sh" "$@"
