#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_main_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_main_loaded() { :; }

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${INSTALLER_DIR}/../.." && pwd)"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner"
if [[ -d "${REPO_ROOT}/pf-runner-full" ]]; then
  PF_RUNNER_DIR="${REPO_ROOT}/pf-runner-full"
fi

source "${INSTALLER_DIR}/common.sh"
source "${INSTALLER_DIR}/config.sh"
source "${INSTALLER_DIR}/cli.sh"
source "${INSTALLER_DIR}/native.sh"
source "${INSTALLER_DIR}/container.sh"

installer_normalize_settings() {
  if [[ "$MODE" != "package" && "$MODE" != "container" && "$MODE" != "native" ]]; then
    die "Invalid --mode: $MODE (expected 'package', 'container', or 'native')"
  fi

  if [[ "$BUILD_ONLY" == true && "$SKIP_BUILD" == true ]]; then
    die "--build-only and --skip-build cannot be used together"
  fi

  if [[ "$PREFIX_SET" == false ]]; then
    if [[ "$MODE" == "container" ]]; then
      if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX_NATIVE"
      else
        PREFIX="$DEFAULT_PREFIX_CONTAINER"
      fi
    else
      if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX_NATIVE"
      else
        PREFIX="$DEFAULT_PREFIX_USER"
      fi
    fi
  fi
}

installer_run_preflight_checks() {
  log_info "Running preflight checks only (--check). No files will be installed."
  log_info "Mode: ${MODE}"
  log_info "Install prefix: ${PREFIX}"

  if [[ "$MODE" == "container" ]]; then
    installer_check_container_runtime
    log_success "Container runtime available: ${CONTAINER_RT}"
    log_info "Container image name: ${CONTAINER_IMAGE}"
    if [[ "$SKIP_BUILD" == true ]]; then
      log_info "Container image build step will be skipped (--skip-build)"
    fi
  else
    installer_check_prerequisites
    log_success "Native prerequisites available (python3, git, pip)"
    if [[ "$SKIP_DEPS" == true ]]; then
      log_info "System dependency installation will be skipped (--skip-deps)"
    else
      log_info "System dependency target OS: $(detect_os)"
    fi
  fi

  if [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
    if [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]]; then
      log_warning "Installing to ${PREFIX} will require root privileges."
      log_info "When ready, run with sudo."
    else
      log_success "Current user has root privileges for ${PREFIX}."
    fi
  fi

  printf '\n'
  log_success "Preflight checks passed."
  log_info "When ready, run:"

  local cmd="./install.sh --mode ${MODE} --prefix ${PREFIX}"
  if [[ "$MODE" == "container" ]]; then
    cmd="${cmd} --runtime ${CONTAINER_RT}"
    if [[ "$SKIP_BUILD" == true ]]; then
      cmd="${cmd} --skip-build"
    fi
  elif [[ "$SKIP_DEPS" == true ]]; then
    cmd="${cmd} --skip-deps"
  fi

  printf '%s\n' "  ${cmd}"
}

installer_main() {
  installer_parse_args "$@"

  if [[ "$SHOW_HELP" == true ]]; then
    installer_show_help
    return 0
  fi

  printf '%b\n' "${BLUE}pf-runner Installation Script${NC}"
  printf '%s\n\n' "=============================="

  if [[ ! -d "$PF_RUNNER_DIR" ]]; then
    die "pf-runner directory not found at ${PF_RUNNER_DIR}. Run from repository root."
  fi

  installer_normalize_settings

  if [[ "$CHECK_ONLY" == true ]]; then
    installer_run_preflight_checks
    return 0
  fi

  installer_check_permissions

  if [[ "$MODE" == "container" ]]; then
    installer_check_container_runtime
    log_info "Container runtime: ${CONTAINER_RT}"
    log_info "pf-runner image: ${CONTAINER_IMAGE}"

    installer_build_container_images

    if [[ "$NO_WRAPPER" != true ]]; then
      installer_install_container_wrapper
    else
      log_info "Wrapper installation skipped"
    fi

    installer_validate_container_installation || die "Container installation validation failed"
    printf '\n'
    log_success "pf-runner container installation completed successfully!"
    installer_update_path_info
    installer_print_post_install_guidance "container"
    return 0
  fi

  # "package" behaves like "native" in this repo.
  installer_check_prerequisites
  if [[ "$SKIP_DEPS" == false ]]; then
    installer_install_system_deps
  fi

  installer_setup_python_env
  installer_install_pf_runner

  installer_validate_native_installation || die "Native installation validation failed"
  printf '\n'
  log_success "pf-runner native installation completed successfully!"
  installer_update_path_info
  installer_print_post_install_guidance "native"
  return 0
}

