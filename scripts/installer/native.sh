#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_native_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_native_loaded() { :; }
INSTALLER_PYTHON_BIN="${INSTALLER_PYTHON_BIN:-}"

installer_resolve_base_python() {
  if [[ -n "${PF_PYTHON:-}" && -x "${PF_PYTHON}" ]]; then
    printf '%s\n' "${PF_PYTHON}"
    return 0
  fi

  command_exists python3 || return 1

  python3 - <<'PY'
import os
import shutil
import sys

candidates = []
for raw in (
    getattr(sys, "_base_executable", "") or "",
    sys.executable,
    shutil.which("python3") or "",
    shutil.which("python") or "",
):
    if not raw:
        continue
    resolved = os.path.realpath(raw)
    candidates.append(os.path.join(os.path.dirname(resolved), "python3"))
    candidates.append(resolved)

seen = set()
for candidate in candidates:
    if not candidate or candidate in seen:
        continue
    seen.add(candidate)
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        print(candidate)
        break
else:
    raise SystemExit(1)
PY
}

installer_copy_runner_tree() {
  local source_dir="${PF_RUNNER_DIR}"
  local dest_dir="${PREFIX}/lib/pf-runner"
  local prefix_abs=""
  local entry=""
  local entry_abs=""
  local base=""
  prefix_abs="$(pf_abs_path "${PREFIX}")"

  shopt -s nullglob dotglob
  for entry in "${source_dir}"/* "${source_dir}"/.[!.]* "${source_dir}"/..?*; do
    [[ -e "$entry" ]] || continue
    entry_abs="$(pf_abs_path "$entry")"
    if [[ "$prefix_abs" == "$entry_abs" || "$prefix_abs" == "$entry_abs/"* ]]; then
      log_warning "Skipping $(basename "$entry") because install prefix is inside that source tree"
      continue
    fi
    base="$(basename "$entry")"
    case "$base" in
      .venv|vendor|bak)
        continue
        ;;
    esac
    cp -R "$entry" "$dest_dir/"
  done
  shopt -u dotglob nullglob

  find "$dest_dir" -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
  find "$dest_dir" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
}

installer_check_prerequisites() {
  log_info "Checking prerequisites..."

  command_exists python3 || die "Python 3 is required but not installed."
  command_exists git || die "Git is required but not installed."
  INSTALLER_PYTHON_BIN="$(installer_resolve_base_python)" || die "Could not resolve a stable Python 3 interpreter."
  "${INSTALLER_PYTHON_BIN}" -m pip --version >/dev/null 2>&1 || die "pip is required but not available for ${INSTALLER_PYTHON_BIN}."

  local python_version=""
  python_version="$("${INSTALLER_PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
  if ! "${INSTALLER_PYTHON_BIN}" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
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
      run_as_root apt-get install -y python3-dev python3-pip build-essential curl git
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

installer_install_python_runtime() {
  log_info "Installing bundled Python runtime dependencies..."

  local vendor_dir="${PREFIX}/lib/pf-runner/vendor"
  local python_bin="${INSTALLER_PYTHON_BIN:-}"
  [[ -n "$python_bin" ]] || python_bin="$(installer_resolve_base_python)"

  mkdir -p "${PREFIX}/lib/pf-runner"
  rm -rf "$vendor_dir"
  mkdir -p "$vendor_dir"

  "${python_bin}" -m pip install --upgrade \
    --target "$vendor_dir" \
    "fabric>=3.2,<4" \
    "lark" \
    "typer" \
    "json5" \
    "rich"
}

installer_install_pf_runner() {
  log_info "Installing pf-runner..."
  mkdir -p "${PREFIX}/lib" "${PREFIX}/bin"
  rm -rf "${PREFIX}/lib/pf-runner" "${PREFIX}/lib/pf-runner-venv"
  mkdir -p "${PREFIX}/lib/pf-runner"
  installer_copy_runner_tree

  if [[ -d "${PF_TASKS_DIR:-}" ]]; then
    local prefix_abs=""
    local tasks_abs=""
    prefix_abs="$(pf_abs_path "${PREFIX}")"
    tasks_abs="$(pf_abs_path "${PF_TASKS_DIR}")"
    if [[ "$prefix_abs" == "$tasks_abs" || "$prefix_abs" == "$tasks_abs/"* ]]; then
      log_warning "Skipping pf-files copy because install prefix is inside that source tree"
    else
      rm -rf "${PREFIX}/lib/pf-runner/pf-files"
      mkdir -p "${PREFIX}/lib/pf-runner/pf-files"
      cp -R "${PF_TASKS_DIR}/." "${PREFIX}/lib/pf-runner/pf-files/"
    fi
  fi

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

    for dir in tools scripts demos containers web docs examples pf tests; do
      if [[ -d "${REPO_ROOT}/${dir}" ]]; then
        local prefix_abs=""
        local dir_abs=""
        prefix_abs="$(pf_abs_path "${PREFIX}")"
        dir_abs="$(pf_abs_path "${REPO_ROOT}/${dir}")"
        if [[ "$prefix_abs" == "$dir_abs" || "$prefix_abs" == "$dir_abs/"* ]]; then
          log_warning "Skipping ${dir} copy because install prefix is inside that source tree"
          continue
        fi
        if [[ "$dir" == "pf" ]]; then
          rm -rf "${PREFIX}/lib/pf-runner/pf"
        fi
        cp -R "${REPO_ROOT}/${dir}" "${PREFIX}/lib/pf-runner/"
      fi
    done
    for file in docker-compose.yml docker-compose.gpu.yml podman-compose.yml podman-compose.gpu.yml tools-capabilities.json package.json package-lock.json playwright.config.ts requirements.txt pyproject.toml install.sh quick-install.sh; do
      if [[ -f "${REPO_ROOT}/${file}" ]]; then
        cp "${REPO_ROOT}/${file}" "${PREFIX}/lib/pf-runner/"
      fi
    done
  fi
  local stable_python_quoted=""
  printf -v stable_python_quoted '%q' "${INSTALLER_PYTHON_BIN:-$(installer_resolve_base_python)}"

  cat > "${PREFIX}/bin/pf" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
LIB_DIR="$(cd "${SCRIPT_DIR}/../lib/pf-runner" && pwd -P)"
EOF
  cat >> "${PREFIX}/bin/pf" <<EOF
PF_STABLE_PYTHON=${stable_python_quoted}
source "\${LIB_DIR}/pf_runtime.sh"
pf_exec_runner "\${LIB_DIR}" "\${LIB_DIR}" "\$@"
EOF
  chmod +x "${PREFIX}/bin/pf"
}

installer_validate_native_installation() {
  log_info "Validating native installation..."

  [[ -x "${PREFIX}/bin/pf" ]] || return 1
  "${PREFIX}/bin/pf" --version >/dev/null 2>&1 || return 1
  "${PREFIX}/bin/pf" list >/dev/null 2>&1 || return 1
  "${PREFIX}/bin/pf" quickstart-hello >/dev/null 2>&1 || return 1

  local fake_venv=""
  fake_venv="$(mktemp -d 2>/dev/null || mktemp -d -t pf-fake-venv)"
  mkdir -p "${fake_venv}/bin"
  cat > "${fake_venv}/bin/python3" <<'EOF'
#!/usr/bin/env bash
echo "unexpected PATH python3" >&2
exit 97
EOF
  chmod +x "${fake_venv}/bin/python3"
  if ! VIRTUAL_ENV="${fake_venv}" PATH="${fake_venv}/bin:${PATH}" "${PREFIX}/bin/pf" list >/dev/null 2>&1; then
    rm -rf "${fake_venv}"
    return 1
  fi
  rm -rf "${fake_venv}"

  log_success "Native installation validated successfully"
  return 0
}
