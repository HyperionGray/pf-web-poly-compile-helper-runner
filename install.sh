#!/usr/bin/env bash
# Thin installer entrypoint.
#
# The implementation lives in `scripts/installer/*.sh` to keep this top-level
# script short and easier to maintain.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/installer/main.sh
source "${REPO_ROOT}/scripts/installer/main.sh"

installer_main "$@"

