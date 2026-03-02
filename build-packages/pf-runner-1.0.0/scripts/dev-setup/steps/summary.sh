#!/usr/bin/env bash
set -euo pipefail

dev_setup_display_summary() {
  log_success "Development environment setup complete"
  printf '%s\n' ""
  printf '%s\n' "Next steps:"
  printf '%s\n' "  - pf list"
  printf '%s\n' "  - pf run repo-validate"
}

