#!/usr/bin/env bash
set -euo pipefail

dev_setup_display_cleanup_summary() {
  log_success "Repository cleanup complete"
  printf '%s\n' ""
  printf '%s\n' "Ran cleanup tasks:"
  printf '%s\n' "  - Coverage artifacts removed (.coverage, coverage.xml, htmlcov/)"
  printf '%s\n' "  - egg-info metadata restored (when present)"
  printf '%s\n' ""
  printf '%s\n' "Tips:"
  printf '%s\n' "  - Use --deep-clean to remove known stale nested duplicate directories"
  printf '%s\n' "  - Re-run full setup with ./setup_dev_environment.sh"
}

dev_setup_display_summary() {
  log_success "Development environment setup complete"
  printf '%s\n' ""
  printf '%s\n' "Virtual environment:"
  printf '%s\n' "  - ${PF_DEV_VENV}"
  printf '%s\n' ""
  printf '%s\n' "Next steps:"
  printf '%s\n' "  - source ${PF_DEV_VENV}/bin/activate"
  printf '%s\n' "  - pf --version"
  printf '%s\n' "  - pf --help"
  printf '%s\n' "  - npm run test:unit"
  printf '%s\n' "  - python -m pytest tests/test_pf_parser.py -q"
  printf '%s\n' ""
  printf '%s\n' "Optional:"
  printf '%s\n' "  - ./setup_dev_environment.sh --cleanup-only --deep-clean"
}

