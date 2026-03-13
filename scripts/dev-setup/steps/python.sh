#!/usr/bin/env bash
set -euo pipefail

dev_setup_python_bin() {
  printf '%s\n' "${PF_DEV_VENV}/bin/python"
}

dev_setup_pip_install() {
  local python_bin
  python_bin="$(dev_setup_python_bin)"
  "${python_bin}" -m pip install "$@"
}

dev_setup_install_python_dependencies() {
  log_info "Preparing Python virtual environment..."

  if [[ ! -d "${PF_DEV_VENV}" ]]; then
    python3 -m venv "${PF_DEV_VENV}" || die "Failed to create virtual environment at ${PF_DEV_VENV}"
  fi

  if [[ ! -x "$(dev_setup_python_bin)" ]]; then
    die "Python virtual environment is missing its interpreter: ${PF_DEV_VENV}"
  fi

  log_info "Upgrading pip tooling in ${PF_DEV_VENV}..."
  dev_setup_pip_install --upgrade pip setuptools wheel || die "Failed to upgrade pip tooling"

  if [[ -f "requirements.txt" ]]; then
    log_info "Installing root Python requirements..."
    dev_setup_pip_install -r requirements.txt || die "Failed to install root Python requirements"
  fi

  log_info "Installing Python test dependencies..."
  dev_setup_pip_install pytest pytest-cov || die "Failed to install Python test dependencies"

  if [[ -d "pf-runner-full" ]]; then
    log_info "Installing pf-runner-full in editable mode..."
    dev_setup_pip_install -e "./pf-runner-full[api,tui]" || die "Failed to install pf-runner-full"
  else
    die "pf-runner-full/ is required for development setup"
  fi

  log_success "Python dependencies installed into ${PF_DEV_VENV}"
}

