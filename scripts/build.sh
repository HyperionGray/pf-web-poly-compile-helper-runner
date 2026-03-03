#!/usr/bin/env bash
# Repository build helper (thin wrapper around scripts/lib/pf-build-lib.sh)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/pf-build-lib.sh
source "${SCRIPT_DIR}/lib/pf-build-lib.sh"

usage() {
  local script_name=""
  script_name="$(basename "${0:-build.sh}")"
  cat <<EOF
Usage: ${script_name} [options]

Options:
  --version=VERSION  Informational only
  --no-install       Do not auto-install missing system dependencies
  --install          Auto-install missing system dependencies (default)
  --cc=CC            C compiler to use (default: auto-detect)
  --help, -h         Show this help message
EOF
}

main() {
  local version=""
  local auto_install=1
  local cc=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version=*)
        version="${1#*=}"
        shift
        ;;
      --no-install)
        auto_install=0
        shift
        ;;
      --install)
        auto_install=1
        shift
        ;;
      --cc=*)
        cc="${1#*=}"
        shift
        ;;
      --cc)
        cc="${2:-}"
        shift 2
        ;;
      --help|-h)
        usage
        return 0
        ;;
      *)
        log_warning "Unknown option: $1"
        shift
        ;;
    esac
  done

  if [[ -n "$version" ]]; then
    log_info "Build version: ${version}"
  fi

  log_info "Starting build process..."
  log_info "Working directory: $(pwd)"

  if ! check_dependencies "$cc" "$auto_install"; then
    log_error "Dependency check failed"
    return 1
  fi

  if build_project; then
    log_success "Build completed successfully"
    return 0
  fi

  log_error "Build failed"
  return 1
}

main "$@"

