#!/usr/bin/env bash
set -euo pipefail

DEV_SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${DEV_SETUP_DIR}/../.." && pwd)"

# shellcheck source=../lib/pf-bash-lib.sh
source "${REPO_ROOT}/scripts/lib/pf-bash-lib.sh"
# shellcheck source=ui.sh
source "${DEV_SETUP_DIR}/ui.sh"
# shellcheck source=steps.sh
source "${DEV_SETUP_DIR}/steps.sh"

dev_setup_main() {
  dev_setup_print_header

  dev_setup_check_system_requirements
  dev_setup_install_python_dependencies
  dev_setup_install_node_dependencies
  dev_setup_install_playwright_browsers
  dev_setup_setup_git_hooks
  dev_setup_create_dev_configs
  dev_setup_run_initial_tests
  dev_setup_display_summary
}

