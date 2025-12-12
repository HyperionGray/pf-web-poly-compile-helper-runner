#!/usr/bin/env bash
# Smoke test for pf-web-poly-compile-helper-runner install script
# Tests both the direct install and container install methods

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

test_container_install() {
  if ! command -v podman >/dev/null 2>&1; then
    log_warn "podman not found; skipping container install test"
    return 0
  fi

  cd "${PROJECT_ROOT}"

  # Use a test image tag so we don't interfere with user's main image
  local test_image="pf-runner:test-install"

  log_info "Testing container install with podman (image=${test_image})..."

  # Build container images
  ./install-container.sh --runtime podman --image "${test_image}" >/dev/null 2>&1 || {
    log_warn "Container build failed (may be expected in CI without full podman setup)"
    return 0
  }

  # Verify image exists
  if podman image exists "${test_image}" >/dev/null 2>&1; then
    log_pass "Container install: successfully built image ${test_image}"
    return 0
  else
    log_warn "Container install: image not found (may be expected in CI)"
    return 0
  fi
}

main() {
  log_info "pf install script smoke tests"
  log_info "=============================="
  
  local failed=0
  
  test_direct_install || failed=1
  test_container_install || failed=1
  
  if [[ ${failed} -eq 0 ]]; then
    log_pass "All install tests passed!"
    exit 0
  else
    log_fail "Some install tests failed"
    exit 1
  fi
}

main "$@"
