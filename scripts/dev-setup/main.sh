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
DEV_SETUP_SKIP_NODE="false"
DEV_SETUP_CHECK_ONLY="false"

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
      --skip-node)
        DEV_SETUP_SKIP_NODE="true"
        DEV_SETUP_SKIP_PLAYWRIGHT="true"
        shift
        ;;
      --skip-tests)
        DEV_SETUP_SKIP_TESTS="true"
        shift
        ;;
      --check-only)
        DEV_SETUP_CHECK_ONLY="true"
        DEV_SETUP_SKIP_TESTS="true"
        shift
        ;;
      --help|-h)
        dev_setup_print_usage
        exit 0
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

  dev_setup_check_system_requirements "${DEV_SETUP_SKIP_NODE}"
  if [[ "${DEV_SETUP_CHECK_ONLY}" == "true" ]]; then
    log_success "Preflight checks passed (--check-only). No changes were made."
    return 0
  fi

  dev_setup_install_python_dependencies
  if [[ "${DEV_SETUP_SKIP_NODE}" != "true" ]]; then
    dev_setup_install_node_dependencies
  else
    log_info "Skipping Node.js dependency installation (--skip-node)"
  fi

  if [[ "${DEV_SETUP_SKIP_PLAYWRIGHT}" != "true" ]] && [[ "${DEV_SETUP_SKIP_NODE}" != "true" ]]; then
    dev_setup_install_playwright_browsers
  elif [[ "${DEV_SETUP_SKIP_PLAYWRIGHT}" == "true" ]]; then
    log_info "Skipping Playwright browser installation (--skip-playwright)"
  fi
  dev_setup_setup_git_hooks
  dev_setup_create_dev_configs
  if [[ "${DEV_SETUP_SKIP_TESTS}" != "true" ]]; then
    dev_setup_run_initial_tests
  fi
  dev_setup_cleanup_generated_files
  dev_setup_display_summary
}

