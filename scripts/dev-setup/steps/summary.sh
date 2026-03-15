#!/usr/bin/env bash
set -euo pipefail

dev_setup_display_summary() {
  if [[ "${DEV_SETUP_MODE:-full}" == "cleanup" ]]; then
    log_success "Repository cleanup complete"
    printf '%s\n' ""
    printf '%s\n' "Cleanup options used:"
    printf '%s\n' "  - prune caches: ${DEV_SETUP_PRUNE_CACHES:-false}"
    printf '%s\n' ""
    printf '%s\n' "Tip: run ./setup_dev_environment.sh to perform full setup."
    return 0
  fi

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
}

