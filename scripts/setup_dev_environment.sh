#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

# shellcheck source=dev-setup/main.sh
source "${REPO_ROOT}/scripts/dev-setup/main.sh"

dev_setup_main "$@"