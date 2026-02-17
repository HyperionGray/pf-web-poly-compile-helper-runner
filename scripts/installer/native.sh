#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_native_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_native_loaded() { :; }

installer_check_prerequisites() {
  log_info "Checking prerequisites..."

  command_exists python3 || die "Python 3 is required but not installed."
  command_exists git || die "Git is required but not installed."
  python3 -m pip --version >/dev/null 2>&1 || die "pip is required but not available."

  local python_version=""
  python_version="$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
  if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    die "Python 3.8+ is required. Found: ${python_version}"
  fi
}

installer_install_system_deps() {
  log_info "Installing system dependencies..."

  local os_type=""
  os_type="$(detect_os)"

  case "$os_type" in
    debian)
      run_as_root apt-get update
      run_as_root apt-get install -y python3-dev python3-pip python3-venv build-essential curl git
      ;;
    rhel)
      if command_exists dnf; then
        run_as_root dnf install -y python3-devel python3-pip gcc gcc-c++ make curl git
      else
        run_as_root yum install -y python3-devel python3-pip gcc gcc-c++ make curl git
      fi
      ;;
    arch)
      run_as_root pacman -Sy --noconfirm python python-pip base-devel curl git
      ;;
    macos)
      log_warning "macOS detected; please ensure Python 3 and build tools are installed"
      ;;
    *)
      log_warning "Unknown OS; skipping system dependency installation"
      ;;
  esac
}

installer_setup_python_env() {
  log_info "Setting up Python environment..."

  local venv_dir=""
  if [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
    venv_dir=""
  else
    venv_dir="${PREFIX}/lib/pf-runner-venv"
  fi

  if [[ -n "$venv_dir" ]]; then
    mkdir -p "${PREFIX}/lib"
    python3 -m venv "$venv_dir"
    # shellcheck disable=SC1091
    source "${venv_dir}/bin/activate"
    python3 -m pip install --upgrade pip
  fi

  python3 -m pip install --upgrade "fabric>=3.2,<4" "lark" "typer" "json5" "rich"
}

installer_install_pf_runner() {
  log_info "Installing pf-runner..."

  mkdir -p "${PREFIX}/lib/pf-runner" "${PREFIX}/bin"
  cp -R "${PF_RUNNER_DIR}/." "${PREFIX}/lib/pf-runner/"

  if [[ -n "${REPO_ROOT:-}" ]]; then
    if [[ -f "${REPO_ROOT}/pf.config.json5" ]]; then
      cp "${REPO_ROOT}/pf.config.json5" "${PREFIX}/lib/pf-runner/"
    fi

    shopt -s nullglob
    for pfy_file in "${REPO_ROOT}"/Pfyfile*.pf; do
      if [[ -f "$pfy_file" ]]; then
        cp "$pfy_file" "${PREFIX}/lib/pf-runner/"
      fi
    done
    shopt -u nullglob

    for dir in tools scripts demos containers web docs examples; do
      if [[ -d "${REPO_ROOT}/${dir}" ]]; then
        cp -R "${REPO_ROOT}/${dir}" "${PREFIX}/lib/pf-runner/"
      fi
    done

    for file in docker-compose.yml docker-compose.gpu.yml podman-compose.yml podman-compose.gpu.yml tools-capabilities.json; do
      if [[ -f "${REPO_ROOT}/${file}" ]]; then
        cp "${REPO_ROOT}/${file}" "${PREFIX}/lib/pf-runner/"
      fi
    done
  fi

  cat > "${PREFIX}/bin/pf" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
LIB_DIR="$(cd "${SCRIPT_DIR}/../lib/pf-runner" && pwd -P)"
VENV_PY="${SCRIPT_DIR}/../lib/pf-runner-venv/bin/python3"
DEFAULT_PFY="${LIB_DIR}/Pfyfile.pf"

if [[ -z "${PFY_FILE:-}" && -f "${DEFAULT_PFY}" ]]; then
  export PFY_FILE="${DEFAULT_PFY}"
  export PFY_ROOT="${LIB_DIR}"
fi

if [[ -x "$VENV_PY" ]]; then
  exec "$VENV_PY" "${LIB_DIR}/pf_main.py" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "${LIB_DIR}/pf_main.py" "$@"
fi

echo "python3 is required to run pf (missing in PATH)." >&2
exit 1
EOF
  chmod +x "${PREFIX}/bin/pf"
}

installer_validate_native_installation() {
  log_info "Validating native installation..."

  [[ -x "${PREFIX}/bin/pf" ]] || return 1
  "${PREFIX}/bin/pf" --help >/dev/null 2>&1 || return 1

  log_success "Native installation validated successfully"
  return 0
}
