#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

source "${ROOT_DIR}/scripts/installer/main.sh"
installer_main "$@"
