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

  cat > "${PREFIX}/bin/pf" <<EOF
#!/usr/bin/env bash
set -euo pipefail

DEFAULT_IMAGE="${CONTAINER_IMAGE}"
DEFAULT_RUNTIME="${CONTAINER_RT}"

IMAGE="\${PF_IMAGE:-\$DEFAULT_IMAGE}"
RUNTIME="\${PF_RUNTIME:-\$DEFAULT_RUNTIME}"

if ! command -v "\$RUNTIME" >/dev/null 2>&1; then
  echo "Error: container runtime '\$RUNTIME' not found." >&2
  echo "" >&2
  echo "Available options:" >&2
  echo "  1. Install \$RUNTIME (recommended)" >&2
  echo "  2. Use a different runtime: PF_RUNTIME=podman pf ..." >&2
  echo "  3. Install the native runner: ./install.sh --native" >&2
  exit 1
fi

if [[ -z "\${PF_IMAGE:-}" ]]; then
  IMAGE_EXISTS=false
  if [[ "\$RUNTIME" = "podman" ]]; then
    if podman image exists "\$IMAGE" >/dev/null 2>&1; then
      IMAGE_EXISTS=true
    fi
  elif [[ "\$RUNTIME" = "docker" ]]; then
    if docker image inspect "\$IMAGE" >/dev/null 2>&1; then
      IMAGE_EXISTS=true
    fi
  fi

  if [[ "\$IMAGE_EXISTS" = "false" ]]; then
    echo "Error: container image '\$IMAGE' not found locally." >&2
    echo "" >&2
    echo "To fix this issue:" >&2
    echo "  1. Build the image from the repo root: ./install.sh --mode container --runtime \$RUNTIME" >&2
    echo "  2. Or install the native runner: ./install.sh --native" >&2
    echo "  3. Or specify a different image: PF_IMAGE=<your-image> pf ..." >&2
    exit 1
  fi
fi

WORKDIR="\${PWD}"
ARGS=(run --rm)
if [[ -t 0 && -t 1 ]]; then
  ARGS+=(-it)
fi

USER_FLAG=()
if command -v id >/dev/null 2>&1; then
  USER_FLAG=(--user "\$(id -u)":"\$(id -g)")
fi

ARGS+=(-v "\${WORKDIR}:\${WORKDIR}")
ARGS+=(-w "\${WORKDIR}")
if [[ -d "\${HOME}" ]]; then
  ARGS+=(-v "\${HOME}:\${HOME}")
  ARGS+=(-e "HOME=\${HOME}")
fi

if command -v podman >/dev/null 2>&1; then
  if [[ -x "/usr/bin/podman" ]]; then
    ARGS+=(-v "/usr/bin/podman:/usr/bin/podman:ro")
  fi
  [[ -d "/usr/libexec/podman" ]] && ARGS+=(-v "/usr/libexec/podman:/usr/libexec/podman:ro")
  [[ -d "/usr/lib/podman" ]] && ARGS+=(-v "/usr/lib/podman:/usr/lib/podman:ro")
  SOCK_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
  if [[ -S "\${SOCK_DIR}/podman/podman.sock" ]]; then
    ARGS+=(-v "\${SOCK_DIR}/podman:\${SOCK_DIR}/podman")
    ARGS+=(-e "XDG_RUNTIME_DIR=\${SOCK_DIR}")
    ARGS+=(-e "CONTAINER_HOST=unix://\${SOCK_DIR}/podman/podman.sock")
  fi
  [[ -d "/etc/containers" ]] && ARGS+=(-v "/etc/containers:/etc/containers:ro")
  [[ -d "/usr/share/containers" ]] && ARGS+=(-v "/usr/share/containers:/usr/share/containers:ro")
fi

if [[ -n "\${PFY_FILE:-}" ]]; then
  ARGS+=(-e "PFY_FILE=\${PFY_FILE}")
fi

exec "\$RUNTIME" "\${ARGS[@]}" "\${USER_FLAG[@]}" "\$IMAGE" pf "\$@"
EOF
  chmod +x "${PREFIX}/bin/pf"
}

installer_validate_container_installation() {
  log_info "Validating container installation..."

  [[ -x "${PREFIX}/bin/pf" ]] || return 1
  "${PREFIX}/bin/pf" --version >/dev/null 2>&1 || return 1
  "${PREFIX}/bin/pf" list >/dev/null 2>&1 || return 1

  log_success "Container installation validated successfully"
  return 0
}

