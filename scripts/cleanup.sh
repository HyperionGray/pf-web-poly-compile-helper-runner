#!/usr/bin/env bash
set -euo pipefail

# Repo cleanup helper:
# - removes common local test/build artifacts
# - does not use environment variables for configuration (CLI flags only)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f "${SCRIPT_DIR}/lib/pf-bash-lib.sh" ]]; then
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/lib/pf-bash-lib.sh"
fi

if ! command -v log_info >/dev/null 2>&1; then
  log_info() { printf '%s\n' "[INFO] $*"; }
  log_success() { printf '%s\n' "[OK] $*"; }
  log_warning() { printf '%s\n' "[WARN] $*" >&2; }
  log_error() { printf '%s\n' "[ERROR] $*" >&2; }
fi

show_help() {
  cat <<'EOF'
Repository cleanup

Usage:
  scripts/cleanup.sh [--dry-run] [--all]

Options:
  --dry-run   Show what would be removed, but do nothing
  --all       Also remove additional caches/reports (still does NOT delete node_modules/)
  --help,-h   Show this help
EOF
}

dry_run=false
all=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) dry_run=true ;;
    --all) all=true ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      show_help
      exit 2
      ;;
  esac
  shift
done

remove_paths() {
  local label="$1"
  shift

  local removed_any=false
  local p
  for p in "$@"; do
    [[ -e "$p" ]] || continue
    removed_any=true
    if [[ "$dry_run" == true ]]; then
      printf '%s\n' "would remove: $p"
    else
      rm -rf -- "$p"
    fi
  done

  if [[ "$removed_any" == true && "$dry_run" == false ]]; then
    log_success "$label"
  fi
}

log_info "Cleaning repository artifacts (all=${all}, dry_run=${dry_run})"

remove_paths "Removed common artifacts" \
  .coverage .coverage.* coverage.xml htmlcov \
  .pytest_cache __pycache__ \
  test-results playwright-report tui-test-report.json fuzz_results.json

if [[ "$all" == true ]]; then
  remove_paths "Removed additional caches" \
    .pf \
    pf-runner/build pf-runner/dist \
    pf-runner/.pytest_cache pf-runner/__pycache__ \
    .mypy_cache .ruff_cache

  # Keep node_modules/ intact; only remove well-known caches inside it if present.
  if [[ -d node_modules ]]; then
    remove_paths "Removed node_modules caches" \
      node_modules/.cache node_modules/.vite node_modules/.turbo
  fi
fi

if [[ "$dry_run" == true ]]; then
  log_info "Dry run complete (no changes made)."
else
  log_success "Cleanup complete."
fi

