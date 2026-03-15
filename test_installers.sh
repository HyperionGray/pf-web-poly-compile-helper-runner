#!/usr/bin/env bash
# Smoke-test the current no-build installer flow against the pf-runner-full layout.

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner-full"
TEST_DIR="/tmp/installer-tests-$$"
INSTALL_PREFIX="${TEST_DIR}/static-install"
STATIC_PF="${INSTALL_PREFIX}/bin/pf"

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

cleanup() {
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

if [[ -x "${PF_RUNNER_DIR}/.venv/bin/python" ]]; then
    RUNNER_PYTHON="${PF_RUNNER_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    RUNNER_PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    RUNNER_PYTHON="$(command -v python)"
else
    log_error "Python is required to run installer smoke tests"
    exit 1
fi

test_pf_wrapper() {
    local test_name="$1"
    local pf_cmd="$2"

    log_test "Testing ${test_name}"

    if ! PF_PYTHON="$RUNNER_PYTHON" "$pf_cmd" -V >/dev/null 2>&1; then
        log_error "${test_name}: pf -V failed"
        return 1
    fi
    log_info "${test_name}: pf -V works"

    if ! (cd "$PF_RUNNER_DIR" && PF_PYTHON="$RUNNER_PYTHON" "$pf_cmd" -f test.pf list >/dev/null 2>&1); then
        log_error "${test_name}: pf list failed"
        return 1
    fi
    log_info "${test_name}: pf list works"

    if ! (cd "$PF_RUNNER_DIR" && PF_PYTHON="$RUNNER_PYTHON" "$pf_cmd" -f test.pf run smoke >/dev/null 2>&1); then
        log_error "${test_name}: pf smoke failed"
        return 1
    fi
    log_info "${test_name}: pf smoke task works"

    log_success "${test_name}: All tests passed"
}

mkdir -p "$TEST_DIR"

echo "========================================"
echo "pf-runner Installer Test Suite"
echo "========================================"
echo ""

log_test "Test 1: Repository layout checks"
[[ -d "$PF_RUNNER_DIR" ]] || { log_error "pf-runner-full directory not found"; exit 1; }
[[ -f "${REPO_ROOT}/install-static.sh" ]] || { log_error "install-static.sh not found"; exit 1; }
log_success "Installer assets found"
echo ""

log_test "Test 2: Direct pf_main.py execution"
if (cd "$PF_RUNNER_DIR" && \
    "$RUNNER_PYTHON" "${PF_RUNNER_DIR}/pf_main.py" -V >/dev/null 2>&1 && \
    "$RUNNER_PYTHON" "${PF_RUNNER_DIR}/pf_main.py" -f test.pf list >/dev/null 2>&1 && \
    "$RUNNER_PYTHON" "${PF_RUNNER_DIR}/pf_main.py" -f test.pf run smoke >/dev/null 2>&1); then
    log_success "Direct execution works"
else
    log_error "Direct execution failed"
    exit 1
fi
echo ""

log_test "Test 3: install-static.sh syntax"
if bash -n "${REPO_ROOT}/install-static.sh"; then
    log_success "install-static.sh syntax check passed"
else
    log_error "install-static.sh syntax check failed"
    exit 1
fi
echo ""

log_test "Test 4: install-static.sh no-build install"
if "${REPO_ROOT}/install-static.sh" --prefix "$INSTALL_PREFIX" >/dev/null 2>&1; then
    log_success "install-static.sh completed"
else
    log_error "install-static.sh failed"
    exit 1
fi

[[ -x "$STATIC_PF" ]] || { log_error "Installed pf wrapper not found at $STATIC_PF"; exit 1; }
[[ -f "${INSTALL_PREFIX}/lib/pf-runner/pf_main.py" ]] || { log_error "Installed pf_main.py missing"; exit 1; }
[[ -d "${INSTALL_PREFIX}/lib/pf-runner/pf-files" ]] || { log_error "Installed pf-files directory missing"; exit 1; }
log_success "Installed layout looks correct"
echo ""

test_pf_wrapper "Static install wrapper" "$STATIC_PF"
echo ""

log_test "Test 5: Optional pf-static binary"
if [[ -x "${PF_RUNNER_DIR}/pf-static" ]]; then
    if "${PF_RUNNER_DIR}/pf-static" -V >/dev/null 2>&1; then
        log_success "Optional pf-static binary works"
    else
        log_error "Optional pf-static binary failed"
        exit 1
    fi
else
    log_info "pf-static not built; skipping optional binary smoke test"
fi
echo ""

echo "========================================"
echo "Test Summary"
echo "========================================"
log_success "Installer smoke tests completed successfully"
echo ""
echo "Validated:"
echo "  ✓ Direct pf_main.py execution"
echo "  ✓ install-static.sh syntax"
echo "  ✓ install-static.sh no-build installation"
echo "  ✓ Installed pf wrapper execution via PF_PYTHON"
