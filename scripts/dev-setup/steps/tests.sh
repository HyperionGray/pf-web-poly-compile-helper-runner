#!/usr/bin/env bash
set -euo pipefail

dev_setup_cleanup_generated_files() {
  rm -f .coverage coverage.xml
  rm -rf htmlcov

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git restore --quiet \
      pf-runner-full/pf_runner.egg-info/PKG-INFO \
      pf-runner-full/pf_runner.egg-info/SOURCES.txt \
      pf-runner-full/pf_runner.egg-info/requires.txt \
      >/dev/null 2>&1 || true
  fi
}

dev_setup_run_initial_tests() {
  log_info "Running initial smoke tests..."

  local python_bin pf_bin
  python_bin="$(dev_setup_python_bin)"
  pf_bin="${PF_DEV_VENV}/bin/pf"

  if [[ -x "${pf_bin}" ]]; then
    "${pf_bin}" --version >/dev/null || log_warning "pf --version failed (non-critical)"
    "${pf_bin}" --help >/dev/null || log_warning "pf --help failed (non-critical)"
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

  if [[ "${DEV_SETUP_SKIP_NODE:-false}" == "true" ]]; then
    log_info "Skipping Node.js unit tests (--skip-node)"
  elif [[ -f "package.json" ]]; then
    npm run test:unit --silent || log_warning "Node.js unit tests failed (non-critical)"
  fi
}

