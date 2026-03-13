#!/usr/bin/env bash
set -euo pipefail

dev_setup_run_initial_tests() {
  log_info "Running initial smoke tests..."

  local python_bin pf_bin
  python_bin="$(dev_setup_python_bin)"
  pf_bin="${PF_DEV_VENV}/bin/pf"

  if [[ -x "${pf_bin}" ]]; then
    "${pf_bin}" --version >/dev/null || log_warning "pf --version failed (non-critical)"
    "${pf_bin}" list >/dev/null || log_warning "pf list failed (non-critical)"
  else
    log_warning "pf CLI was not installed into ${PF_DEV_VENV}/bin"
  fi

  if [[ -f "tests/test_pf_parser.py" ]]; then
    "${python_bin}" -m pytest tests/test_pf_parser.py -q || log_warning "Python smoke tests failed (non-critical)"
  elif [[ -f "pytest.ini" ]] || [[ -d "tests" ]]; then
    "${python_bin}" -m pytest -q || log_warning "pytest failed (non-critical)"
  else
    log_info "No Python tests detected; skipping"
  fi

  if [[ -f "package.json" ]]; then
    npm run test:unit --silent || log_warning "Node.js unit tests failed (non-critical)"
  fi
}

