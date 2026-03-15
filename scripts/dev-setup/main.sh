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
DEV_SETUP_CLEANUP_ONLY="false"
DEV_SETUP_CLEANUP_ALL="false"
DEV_SETUP_CLEANUP_DRY_RUN="false"

dev_setup_show_help() {
  cat <<'EOF'
Usage: ./setup_dev_environment.sh [options]

Options:
  --venv <path>          Use a custom virtual environment path
  --skip-playwright      Skip Playwright browser installation
  --skip-tests           Skip initial smoke tests
  --cleanup-only         Skip setup steps and run cleanup only
  --cleanup-all          Remove additional caches/reports during cleanup
  --cleanup-dry-run      Preview cleanup targets without removing files
  --help, -h             Show this help message
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
      --skip-playwright)
        DEV_SETUP_SKIP_PLAYWRIGHT="true"
        shift
        ;;
      --skip-tests)
        DEV_SETUP_SKIP_TESTS="true"
        shift
        ;;
      --cleanup-only)
        DEV_SETUP_CLEANUP_ONLY="true"
        shift
        ;;
      --cleanup-all)
        DEV_SETUP_CLEANUP_ALL="true"
        shift
        ;;
      --cleanup-dry-run)
        DEV_SETUP_CLEANUP_DRY_RUN="true"
        shift
        ;;
      --help|-h)
        dev_setup_show_help
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

  if [[ "${DEV_SETUP_CLEANUP_ONLY}" == "true" ]]; then
    log_info "Running cleanup-only mode..."
    dev_setup_cleanup_generated_files
    log_success "Cleanup-only mode complete"
    return 0
  fi

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
  dev_setup_cleanup_generated_files
  dev_setup_display_summary
}

