#!/usr/bin/env bash
# Unified installer entrypoint (delegates to modular installer)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/installer/main.sh"

installer_main "$@"
