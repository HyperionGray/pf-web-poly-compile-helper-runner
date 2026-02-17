#!/usr/bin/env bash
# Top-level validation runner (native-only).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info() { printf '[INFO] %s\n' "$*"; }
ok()   { printf '[ OK ] %s\n' "$*"; }
fail() { printf '[ERR ] %s\n' "$*" >&2; }

apply_fixes() {
  info "Ensuring executables are marked"
  chmod +x "${SCRIPT_DIR}/install.sh" "${SCRIPT_DIR}/comprehensive_test.sh" 2>/dev/null || true
}

run_suite() {
  if "${SCRIPT_DIR}/comprehensive_test.sh"; then
    ok "Native install smoke test passed"
  else
    fail "Native install smoke test failed"
    return 1
  fi

  if python3 tools/validate-pf-tasks.py; then
    ok "Static pf task validation passed"
  else
    fail "Static pf task validation failed"
    return 1
  fi
}

main() {
  apply_fixes
  run_suite
  ok "Master validation complete"
}

main "$@"
