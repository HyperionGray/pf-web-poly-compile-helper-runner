#!/usr/bin/env bash
set -euo pipefail

dev_setup_run_initial_tests() {
  log_info "Running initial tests (best-effort)..."

  if [[ -f "pytest.ini" ]] || [[ -d "tests" ]]; then
    python3 -m pytest -q || log_warning "pytest failed (non-critical)"
  else
    log_info "No tests detected; skipping"
  fi
}

