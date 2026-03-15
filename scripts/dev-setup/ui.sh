#!/usr/bin/env bash
set -euo pipefail

dev_setup_print_header() {
  log_header "pf-web-poly-compile-helper-runner Dev Setup"
  printf '%s\n' "=================================================="
}

dev_setup_print_usage() {
  cat <<'EOF'
Usage: ./setup_dev_environment.sh [options]

Options:
  --venv <path>         Custom virtual environment path
  --skip-node           Skip npm dependencies and Playwright setup
  --skip-playwright     Skip Playwright browser installation
  --skip-tests          Skip initial smoke tests
  --check-only          Validate requirements without installing dependencies
  --help, -h            Show this help message

Examples:
  ./setup_dev_environment.sh
  ./setup_dev_environment.sh --check-only
  ./setup_dev_environment.sh --skip-node --skip-tests
EOF
}

