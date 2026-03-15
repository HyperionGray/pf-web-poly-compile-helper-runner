#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_main_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_main_loaded() { :; }

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${INSTALLER_DIR}/../.." && pwd)"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner-full"
if [[ ! -d "$PF_RUNNER_DIR" && -d "${REPO_ROOT}/pf-runner" ]]; then
  PF_RUNNER_DIR="${REPO_ROOT}/pf-runner"
fi
PF_TASKS_DIR="${REPO_ROOT}/pf-files"
if [[ ! -d "$PF_TASKS_DIR" && -d "${PF_RUNNER_DIR}/pf-files" ]]; then
  PF_TASKS_DIR="${PF_RUNNER_DIR}/pf-files"
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
  if [[ "$MODE" == "container" ]]; then
    installer_check_container_runtime
    log_success "Container runtime is available: ${CONTAINER_RT}"

    if [[ "$SKIP_BUILD" == true ]]; then
      if installer_image_exists "${CONTAINER_IMAGE}"; then
        log_success "Container image is available locally: ${CONTAINER_IMAGE}"
      else
        die "--skip-build was requested, but image '${CONTAINER_IMAGE}' is missing. Build it first or remove --skip-build."
      fi
    else
      [[ -f "${REPO_ROOT}/containers/dockerfiles/Dockerfile.base" ]] || die "Missing container definition: containers/dockerfiles/Dockerfile.base"
      [[ -f "${REPO_ROOT}/containers/dockerfiles/Dockerfile.pf-runner" ]] || die "Missing container definition: containers/dockerfiles/Dockerfile.pf-runner"
      log_success "Container build definitions are present"
    fi
    return 0
  fi

  installer_check_prerequisites
  log_success "Native prerequisites are available"
  if [[ "$SKIP_DEPS" == true ]]; then
    log_info "System dependency installation check skipped (--skip-deps)"
  else
    log_info "Detected OS family: $(detect_os)"
  fi
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
    log_info "Running preflight checks only (--check-only)"
    if [[ "$MODE" != "container" ]] && [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]] && [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
      log_warning "Installing to ${PREFIX} would require root privileges"
    fi
    installer_run_preflight_checks
    log_success "Preflight checks passed. Re-run without --check-only to perform installation."
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
    return 0
  fi

  # "package" behaves like "native" in this repo.
  installer_check_prerequisites
  if [[ "$SKIP_DEPS" == false ]]; then
    installer_install_system_deps
  fi

  installer_install_pf_runner
  installer_install_python_runtime

  installer_validate_native_installation || die "Native installation validation failed"
  printf '\n'
  log_success "pf-runner native installation completed successfully!"
  installer_update_path_info
  return 0
}

