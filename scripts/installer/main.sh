#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_main_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_main_loaded() { :; }

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${INSTALLER_DIR}/../.." && pwd)"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner"

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

installer_print_dry_run_plan() {
  log_info "Dry run mode enabled. No files or packages will be modified."
  log_info "Mode: ${MODE}"
  log_info "Prefix: ${PREFIX}"

  if [[ "$MODE" == "container" ]]; then
    if [[ "${CONTAINER_RT_SET}" == true ]]; then
      log_info "Container runtime (explicit): ${CONTAINER_RT}"
    else
      log_info "Container runtime (auto-detected at runtime): ${CONTAINER_RT}"
    fi
    log_info "Container image: ${CONTAINER_IMAGE}"
    if [[ "$SKIP_BUILD" == true ]]; then
      log_info "Would skip image build (--skip-build)"
    else
      log_info "Would build base and runner container images"
    fi

    if [[ "$NO_WRAPPER" == true ]]; then
      log_info "Would skip wrapper install (--no-wrapper)"
    else
      log_info "Would install pf wrapper to ${PREFIX}/bin/pf"
    fi
  else
    if [[ "$SKIP_DEPS" == true ]]; then
      log_info "Would skip OS dependency installation (--skip-deps)"
    else
      log_info "Would install OS dependencies (apt/dnf/yum/pacman as available)"
    fi
    log_info "Would set up Python environment and install pf-runner to ${PREFIX}/lib/pf-runner"
    log_info "Would install executable wrapper to ${PREFIX}/bin/pf"

    if [[ "$PREFIX" != "/usr/local" && "$PREFIX" != "/usr"* ]]; then
      local bin_dir="${PREFIX}/bin"
      local shell_name=""
      shell_name="$(installer_detect_shell_name)"
      local profile_path=""
      profile_path="$(installer_detect_shell_profile)"
      local export_line=""
      export_line="$(installer_path_export_line "$bin_dir" "$shell_name")"
      log_info "Suggested PATH update: ${export_line}"
      log_info "Suggested profile: ${profile_path}"
      if [[ "${WRITE_SHELL_PROFILE}" == true ]]; then
        log_info "Would append PATH update automatically (--write-shell-profile)"
      fi
    fi
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
  if [[ "$DRY_RUN" == true ]]; then
    installer_print_dry_run_plan
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

  installer_setup_python_env
  installer_install_pf_runner

  installer_validate_native_installation || die "Native installation validation failed"
  printf '\n'
  log_success "pf-runner native installation completed successfully!"
  installer_update_path_info
  return 0
}

