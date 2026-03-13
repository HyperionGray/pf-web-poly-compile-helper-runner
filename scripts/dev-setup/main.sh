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

DEV_SETUP_SKIP_PLAYWRIGHT="false"
DEV_SETUP_SKIP_TESTS="false"

dev_setup_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --venv)
        [[ $# -ge 2 ]] || die "--venv requires a path"
        PF_DEV_VENV="$2"
        shift 2
        ;;
      --skip-playwright)
        DEV_SETUP_SKIP_PLAYWRIGHT="true"
        shift
        ;;
      --skip-tests)
        DEV_SETUP_SKIP_TESTS="true"
        shift
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
  done
}

dev_setup_main() {
  cd "${REPO_ROOT}"
  export PF_DEV_VENV="${PF_DEV_VENV:-${REPO_ROOT}/.venv-dev}"
  dev_setup_parse_args "$@"

  dev_setup_print_header

  dev_setup_check_system_requirements
  dev_setup_install_python_dependencies
  dev_setup_install_node_dependencies
  if [[ "${DEV_SETUP_SKIP_PLAYWRIGHT}" != "true" ]]; then
    dev_setup_install_playwright_browsers
  fi
  dev_setup_setup_git_hooks
  dev_setup_create_dev_configs
  if [[ "${DEV_SETUP_SKIP_TESTS}" != "true" ]]; then
    dev_setup_run_initial_tests
  fi
  dev_setup_display_summary
}

