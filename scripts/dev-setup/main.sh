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
DEV_SETUP_CLEAN_ONLY="false"
DEV_SETUP_DEEP_CLEAN="false"

dev_setup_usage() {
  cat <<'EOF'
Usage: ./setup_dev_environment.sh [options]

Options:
  --venv PATH         Use a custom virtual environment path
  --skip-node         Skip Node.js dependency and Playwright setup
  --skip-playwright   Skip Playwright browser installation
  --skip-tests        Skip initial smoke tests
  --cleanup-only      Run repository cleanup steps only
  --deep-clean        Remove known stale nested duplicate directories
  -h, --help          Show this help message
EOF
}

dev_setup_parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --venv)
        [[ $# -ge 2 ]] || die "--venv requires a path"
        PF_DEV_VENV="$2"
        shift 2
        ;;
      --skip-node)
        DEV_SETUP_SKIP_NODE="true"
        shift
        ;;
      --skip-playwright)
        DEV_SETUP_SKIP_PLAYWRIGHT="true"
        shift
        ;;
      --skip-tests)
        DEV_SETUP_SKIP_TESTS="true"
        shift
        ;;
      --cleanup-only)
        DEV_SETUP_CLEAN_ONLY="true"
        shift
        ;;
      --deep-clean)
        DEV_SETUP_DEEP_CLEAN="true"
        shift
        ;;
      -h|--help)
        dev_setup_usage
        exit 0
        ;;
      *)
        dev_setup_usage
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

  if [[ "${DEV_SETUP_CLEAN_ONLY}" == "true" ]]; then
    log_info "Running cleanup-only mode..."
    dev_setup_cleanup_generated_files
    if [[ "${DEV_SETUP_DEEP_CLEAN}" == "true" ]]; then
      dev_setup_cleanup_repo_hygiene
    else
      log_info "Deep repository cleanup skipped (use --deep-clean to enable)"
    fi
    dev_setup_display_cleanup_summary
    return 0
  fi

  dev_setup_check_system_requirements
  dev_setup_install_python_dependencies
  if [[ "${DEV_SETUP_SKIP_NODE}" != "true" ]]; then
    dev_setup_install_node_dependencies
    if [[ "${DEV_SETUP_SKIP_PLAYWRIGHT}" != "true" ]]; then
      dev_setup_install_playwright_browsers
    fi
  else
    log_info "Skipping Node.js dependencies and Playwright setup (--skip-node)"
  fi
  dev_setup_setup_git_hooks
  dev_setup_create_dev_configs
  if [[ "${DEV_SETUP_SKIP_TESTS}" != "true" ]]; then
    dev_setup_run_initial_tests
  fi
  dev_setup_cleanup_generated_files
  if [[ "${DEV_SETUP_DEEP_CLEAN}" == "true" ]]; then
    dev_setup_cleanup_repo_hygiene
  fi
  dev_setup_display_summary
}

