#!/usr/bin/env bash
set -euo pipefail

dev_setup_cleanup_generated_files() {
  log_info "Cleaning generated development artifacts..."

  rm -f .coverage .coverage.* coverage.xml test-report.json tui-test-report.json
  rm -rf htmlcov .pytest_cache

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git restore --quiet \
      pf-runner-full/pf_runner.egg-info/PKG-INFO \
      pf-runner-full/pf_runner.egg-info/SOURCES.txt \
      pf-runner-full/pf_runner.egg-info/dependency_links.txt \
      pf-runner-full/pf_runner.egg-info/entry_points.txt \
      pf-runner-full/pf_runner.egg-info/requires.txt \
      pf-runner-full/pf_runner.egg-info/top_level.txt \
      >/dev/null 2>&1 || true
  fi

  if [[ "${DEV_SETUP_PRUNE_CACHES:-false}" == "true" ]]; then
    log_info "Pruning local caches and transient files..."

    local cache_dir=""
    for cache_dir in "__pycache__" ".pytest_cache" ".mypy_cache" ".ruff_cache"; do
      while IFS= read -r matched_dir; do
        rm -rf "${matched_dir}"
      done < <(find . -type d -name "${cache_dir}" -not -path "./.git/*" -print)
    done

    while IFS= read -r cache_file; do
      rm -f "${cache_file}"
    done < <(find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".DS_Store" \) -not -path "./.git/*" -print)

    # Only remove untracked editor metadata. Tracked entries are handled via git cleanup.
    while IFS= read -r bish_file; do
      if git ls-files --error-unmatch "${bish_file#./}" >/dev/null 2>&1; then
        continue
      fi
      rm -f "${bish_file}"
    done < <(find . -type f -name ".bish.sqlite" -not -path "./.git/*" -print)
  fi

  log_success "Cleanup complete"
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

  if [[ -f "package.json" ]]; then
    npm run test:unit --silent || log_warning "Node.js unit tests failed (non-critical)"
  fi
}

