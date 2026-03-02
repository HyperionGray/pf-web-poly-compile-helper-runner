#!/usr/bin/env bash
set -euo pipefail

DEV_SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=steps/system.sh
source "${DEV_SETUP_DIR}/steps/system.sh"
# shellcheck source=steps/python.sh
source "${DEV_SETUP_DIR}/steps/python.sh"
# shellcheck source=steps/node.sh
source "${DEV_SETUP_DIR}/steps/node.sh"
# shellcheck source=steps/git.sh
source "${DEV_SETUP_DIR}/steps/git.sh"
# shellcheck source=steps/configs.sh
source "${DEV_SETUP_DIR}/steps/configs.sh"
# shellcheck source=steps/tests.sh
source "${DEV_SETUP_DIR}/steps/tests.sh"
# shellcheck source=steps/summary.sh
source "${DEV_SETUP_DIR}/steps/summary.sh"

