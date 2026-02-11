#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_container_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_container_loaded() { :; }

installer_detect_container_runtime() {
  local preferred="${1:-podman}"

  if [[ -n "$preferred" ]] && command_exists "$preferred"; then
    printf '%s\n' "$preferred"
    return 0
  fi
  if command_exists podman; then
    printf '%s\n' podman
    return 0
  fi
  if command_exists docker; then
    printf '%s\n' docker
    return 0
  fi
  return 1
}

installer_check_container_runtime() {
  if [[ "$CONTAINER_RT_SET" == true ]]; then
    command_exists "${CONTAINER_RT}" || die "Container runtime '${CONTAINER_RT}' not found. Install it or use --mode native."
    return 0
  fi

  local detected=""
  detected="$(installer_detect_container_runtime "${CONTAINER_RT:-podman}")" || true
  [[ -n "$detected" ]] || die "Container runtime not found. Install podman/docker, or use --mode native."
  CONTAINER_RT="$detected"
}

installer_image_exists() {
  "${CONTAINER_RT}" image exists "$1" >/dev/null 2>&1
}

installer_build_container_images() {
  if [[ "$SKIP_BUILD" == true ]]; then
    log_info "Skipping container image build (--skip-build)"
    return 0
  fi

  log_info "Building container images..."
  "${CONTAINER_RT}" build -t "${BASE_IMAGE_DEFAULT}" -f "${REPO_ROOT}/containers/dockerfiles/Dockerfile.base" "${REPO_ROOT}"
  "${CONTAINER_RT}" build -t "${CONTAINER_IMAGE}" -f "${REPO_ROOT}/containers/dockerfiles/Dockerfile.pf-runner" "${REPO_ROOT}"
}

installer_install_container_wrapper() {
  log_info "Installing container wrapper..."

  mkdir -p "${PREFIX}/bin" "${PREFIX}/lib/pf-runner"
  cp "${PF_RUNNER_DIR}/pf_universal" "${PREFIX}/lib/pf-runner/pf_universal"
  chmod +x "${PREFIX}/lib/pf-runner/pf_universal" || true

  # Make wrapper default runtime consistent with chosen runtime.
  sed_in_place "s|^DEFAULT_RUNTIME=.*$|DEFAULT_RUNTIME=\"${CONTAINER_RT}\"|g" "${PREFIX}/lib/pf-runner/pf_universal"

  ln -sf "${PREFIX}/lib/pf-runner/pf_universal" "${PREFIX}/bin/pf"
}

installer_validate_container_installation() {
  log_info "Validating container installation..."

  [[ -x "${PREFIX}/bin/pf" ]] || return 1
  "${PREFIX}/bin/pf" --help >/dev/null 2>&1 || return 1

  log_success "Container installation validated successfully"
  return 0
}

