#!/usr/bin/env bash
set -euo pipefail

dev_setup_display_summary() {
  log_success "Development environment setup complete"
  printf '%s\n' ""
  printf '%s\n' "Virtual environment:"
  printf '%s\n' "  - ${PF_DEV_VENV}"
  printf '%s\n' ""
  printf '%s\n' "Next steps:"
  printf '%s\n' "  - source ${PF_DEV_VENV}/bin/activate"
  printf '%s\n' "  - pf --version"
  printf '%s\n' "  - pf list"
  printf '%s\n' "  - npm run test:unit"
  printf '%s\n' "  - python -m pytest tests/test_pf_parser.py -q"
}

