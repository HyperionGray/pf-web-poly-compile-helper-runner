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

dev_setup_cleanup_repo_hygiene() {
  log_info "Running deep repository hygiene cleanup..."

  local stale_paths=(
    "build-packages/build-packages"
    "third-party/archive/src-duplicate-20260214b"
  )
  local removed_count=0
  local target

  for target in "${stale_paths[@]}"; do
    if [[ -e "${target}" ]]; then
      rm -rf -- "${target}"
      log_info "Removed stale path: ${target}"
      removed_count=$((removed_count + 1))
    fi
  done

  if [[ "${removed_count}" -eq 0 ]]; then
    log_info "No stale nested duplicate directories were found"
  elif [[ "${removed_count}" -eq 1 ]]; then
    log_success "Removed 1 stale nested duplicate directory"
  else
    log_success "Removed ${removed_count} stale nested duplicate directories"
  fi
}
