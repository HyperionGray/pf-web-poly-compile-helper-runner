#!/usr/bin/env bash
# Installer smoke tests for current repository layout

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="/tmp/installer-tests-$$"
TESTS_PASSED=0
TESTS_FAILED=0

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

pass_test() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_success "$1"
}

fail_test() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    log_error "$1"
}

cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

mkdir -p "$TEST_DIR"

echo "========================================"
echo "pf-runner Installer Smoke Tests"
echo "========================================"
echo ""
log_info "Repository root: ${REPO_ROOT}"
log_info "Temporary test dir: ${TEST_DIR}"
echo ""

#
# Test 1: install-static help output
#
log_test "Test 1: install-static help output"
if "$REPO_ROOT/install-static.sh" --help >/dev/null 2>&1; then
    pass_test "install-static.sh --help works"
else
    fail_test "install-static.sh --help failed"
fi
echo ""

#
# Test 2: install-static dry-run mode
#
log_test "Test 2: install-static dry-run mode"
DRY_RUN_LOG="$TEST_DIR/install-static-dry-run.log"
if "$REPO_ROOT/install-static.sh" --prefix "$TEST_DIR/dry-run-prefix" --dry-run >"$DRY_RUN_LOG" 2>&1; then
    if grep -q "\[DRY-RUN\]" "$DRY_RUN_LOG"; then
        pass_test "install-static.sh dry-run emits planned actions"
    else
        fail_test "install-static.sh dry-run did not print expected markers"
    fi
else
    fail_test "install-static.sh --dry-run exited non-zero"
fi
echo ""

#
# Test 3: install-static real install + verify
#
log_test "Test 3: install-static install and verify"
STATIC_PREFIX="$TEST_DIR/static-install"
if "$REPO_ROOT/install-static.sh" --prefix "$STATIC_PREFIX" --verify >/dev/null 2>&1; then
    pass_test "install-static.sh completed with --verify"
else
    fail_test "install-static.sh failed with --verify"
fi

if [[ -x "$STATIC_PREFIX/bin/pf" ]]; then
    pass_test "Installed pf wrapper is executable"
else
    fail_test "Installed pf wrapper missing or not executable"
fi

if "$STATIC_PREFIX/bin/pf" -V >/dev/null 2>&1; then
    pass_test "Installed pf responds to -V"
else
    fail_test "Installed pf -V failed"
fi

if "$STATIC_PREFIX/bin/pf" "$STATIC_PREFIX/lib/pf-runner/test.pf" list >/dev/null 2>&1; then
    pass_test "Installed pf can parse bundled test.pf"
else
    fail_test "Installed pf failed to parse bundled test.pf"
fi
echo ""

#
# Test 4: native installer help (if present)
#
log_test "Test 4: native installer help command"
if [[ -x "$REPO_ROOT/install.sh" ]]; then
    if "$REPO_ROOT/install.sh" --help >/dev/null 2>&1; then
        pass_test "install.sh --help works"
    else
        fail_test "install.sh --help failed"
    fi
elif [[ -x "$REPO_ROOT/scripts/install.sh" ]]; then
    if "$REPO_ROOT/scripts/install.sh" --help >/dev/null 2>&1; then
        pass_test "scripts/install.sh --help works"
    else
        fail_test "scripts/install.sh --help failed"
    fi
else
    log_info "Native installer script not found; skipping help smoke test."
fi
echo ""

echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""
echo "Passed: ${TESTS_PASSED}"
echo "Failed: ${TESTS_FAILED}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    log_success "All installer smoke tests passed."
    exit 0
fi

log_error "Installer smoke tests failed."
exit 1
