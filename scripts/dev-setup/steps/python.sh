#!/usr/bin/env bash
set -euo pipefail

dev_setup_pip_install() {
  local -a pip_args=()

  local in_venv="false"
  in_venv="$(python3 - <<'PY'
import sys
print("true" if getattr(sys, "base_prefix", sys.prefix) != sys.prefix else "false")
PY
)"

  if [[ "$in_venv" != "true" ]]; then
    pip_args+=(--user)
  fi

  python3 -m pip install "${pip_args[@]}" "$@"
}

dev_setup_install_python_dependencies() {
  log_info "Installing Python dependencies..."

  local core_deps=(
    "fabric>=3.2,<4"
    "rich"
    "lark"
  )

  local dev_deps=(
    "pytest"
    "pytest-cov"
    "coverage"
  )

  log_info "Upgrading pip..."
  dev_setup_pip_install --upgrade pip || log_warning "Failed to upgrade pip (continuing)"

  log_info "Installing core Python packages..."
  dev_setup_pip_install "${core_deps[@]}" || die "Failed to install core Python dependencies"

  log_info "Installing dev Python packages..."
  dev_setup_pip_install "${dev_deps[@]}" || log_warning "Failed to install some dev dependencies (non-critical)"

  log_success "Python dependencies installed"
}

