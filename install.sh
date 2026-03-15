#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_MAIN="${SCRIPT_DIR}/scripts/installer/main.sh"

if [[ ! -f "${INSTALLER_MAIN}" ]]; then
  echo "[ERROR] Installer module not found: ${INSTALLER_MAIN}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${INSTALLER_MAIN}"
installer_main "$@"
