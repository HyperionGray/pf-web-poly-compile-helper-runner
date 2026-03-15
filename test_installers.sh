#!/usr/bin/env bash
# Portable installer smoke tests.
# Verifies direct execution and install-static.sh behavior.

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner-full"
TEST_PF_FILE="${PF_RUNNER_DIR}/test.pf"
TEST_DIR="$(mktemp -d /tmp/installer-tests.XXXXXX)"

PASSED=0
FAILED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

record_result() {
    local name="$1"
    local status="$2"
    if [[ "$status" == "pass" ]]; then
        PASSED=$((PASSED + 1))
        log_success "$name"
    else
        FAILED=$((FAILED + 1))
        log_error "$name"
    fi
}

cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

run_pf_smoke() {
    local mode="$1"
    shift
    local pf_cmd=("$@")

    if ! "${pf_cmd[@]}" -V >/dev/null 2>&1; then
        log_error "${mode}: pf -V failed"
        return 1
    fi

    if ! "${pf_cmd[@]}" "$TEST_PF_FILE" list >/dev/null 2>&1; then
        log_error "${mode}: list failed"
        return 1
    fi

    if ! "${pf_cmd[@]}" "$TEST_PF_FILE" smoke >/dev/null 2>&1; then
        log_error "${mode}: smoke task failed"
        return 1
    fi

    return 0
}

echo "========================================"
echo "pf-runner Installer Smoke Suite"
echo "========================================"
echo ""

log_info "Repo root: $REPO_ROOT"
log_info "Temporary test dir: $TEST_DIR"
echo ""

if [[ ! -f "${PF_RUNNER_DIR}/pf_main.py" ]]; then
    log_error "Missing ${PF_RUNNER_DIR}/pf_main.py"
    exit 1
fi

if [[ ! -f "$TEST_PF_FILE" ]]; then
    log_error "Missing ${TEST_PF_FILE}"
    exit 1
fi

log_test "Test 1: direct pf_main.py execution"
if run_pf_smoke "Direct execution" python3 "${PF_RUNNER_DIR}/pf_main.py"; then
    record_result "Direct execution smoke test passed" "pass"
else
    record_result "Direct execution smoke test failed" "fail"
fi
echo ""

log_test "Test 2: install-static.sh with --verify"
INSTALL_PREFIX="${TEST_DIR}/static-install"
if "${REPO_ROOT}/install-static.sh" --prefix "$INSTALL_PREFIX" --verify >/dev/null 2>&1; then
    if run_pf_smoke "Static install" "${INSTALL_PREFIX}/bin/pf"; then
        record_result "Static installer smoke test passed" "pass"
    else
        record_result "Static installer smoke test failed" "fail"
    fi
else
    record_result "Static installer execution failed" "fail"
fi
echo ""

echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [[ $FAILED -eq 0 ]]; then
    log_success "All installer smoke tests passed."
    exit 0
fi

log_error "Some installer smoke tests failed."
exit 1
