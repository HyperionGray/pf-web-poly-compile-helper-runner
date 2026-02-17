#!/usr/bin/env bash
# Smoke test for pf-web-poly-compile-helper-runner install script (native only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEST_PREFIX="/tmp/pf-install-test-$$"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail()  { echo -e "${RED}[FAIL]${NC} $*"; }

cleanup() {
  rm -rf "${TEST_PREFIX}" 2>/dev/null || true
}
trap cleanup EXIT

test_direct_install() {
  log_info "Testing direct install to ${TEST_PREFIX}..."
  
  cd "${PROJECT_ROOT}"
  
  # Run install with test prefix and skip deps (to speed up test)
  ./install.sh --prefix "${TEST_PREFIX}" --skip-deps
  
  # Verify pf executable exists
  if [[ -x "${TEST_PREFIX}/bin/pf" ]]; then
    log_pass "Direct install: pf executable created at ${TEST_PREFIX}/bin/pf"
  else
    log_fail "Direct install: pf executable not found"
    return 1
  fi
  
  # Verify library files were copied
  if [[ -f "${TEST_PREFIX}/lib/pf-runner/pf_parser.py" ]]; then
    log_pass "Direct install: library files copied correctly"
  else
    log_fail "Direct install: library files not found"
    return 1
  fi
  
  return 0
}

main() {
  log_info "pf install script smoke tests"
  log_info "=============================="
  
  local failed=0
  
  test_direct_install || failed=1
  
  if [[ ${failed} -eq 0 ]]; then
    log_pass "All install tests passed!"
    exit 0
  else
    log_fail "Some install tests failed"
    exit 1
  fi
}

main "$@"
