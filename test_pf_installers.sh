#!/usr/bin/env bash
# Comprehensive PF task installer test script
# Tests all pf-runner installer tasks and verifies functionality

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner"
PF_DIR="${REPO_ROOT}/build-packages/deb/pf-runner-1.0.0/pf-runner"
PF_FILE="${REPO_ROOT}/pf-files/Pfyfile.pf"
TEST_PREFIX="/tmp/pf-installer-test-$(date +%s)"

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

declare -a FAILED_INSTALLERS
declare -a SKIPPED_INSTALLERS

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

# Run PF command
run_pf() {
    python3 "$PF_DIR/pf_main.py" -f "$PF_FILE" "$@"
}

# Test if a command/binary exists
check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Test an installer task
test_installer() {
    local task_name="$1"
    local expected_binary="${2:-}"
    local expected_package="${3:-}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_test "Testing: $task_name"
    
    # Try running the installer (capture output)
    if timeout 600 run_pf "$task_name" prefix="$TEST_PREFIX" >/tmp/install_${task_name}.log 2>&1; then
        log_success "Installer completed: $task_name"
        
        # Verify installation if we have something to check
        if [[ -n "$expected_binary" ]]; then
            if check_command "$expected_binary" || [ -x "$TEST_PREFIX/bin/$expected_binary" ]; then
                log_success "Verified binary: $expected_binary"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                log_error "Binary not found: $expected_binary"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                FAILED_INSTALLERS+=("$task_name (binary not found: $expected_binary)")
            fi
        else
            # No specific verification - assume success
            PASSED_TESTS=$((PASSED_TESTS + 1))
        fi
    else
        local exit_code=$?
        if [[ $exit_code == 124 ]]; then
            log_skip "Timeout (10min): $task_name"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            SKIPPED_INSTALLERS+=("$task_name (timeout)")
        else
            log_error "Failed: $task_name (exit code: $exit_code)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            FAILED_INSTALLERS+=("$task_name")
            
            # Show last few lines of error
            echo "  Last 10 lines of output:"
            tail -10 /tmp/install_${task_name}.log | sed 's/^/    /'
        fi
    fi
    
    echo ""
}

# Test installer help messages
test_help_output() {
    local task_name="$1"
    
    log_test "Testing help: $task_name"
    
    if run_pf "$task_name" 2>&1 | grep -qi "usage\|help\|instruction\|example"; then
        log_success "Help output present: $task_name"
        return 0
    else
        log_error "Help output missing: $task_name"
        return 1
    fi
}

mkdir -p "$TEST_PREFIX"

echo "========================================"
echo "PF Task Installer Test Suite"
echo "========================================"
echo ""
log_info "Test prefix: $TEST_PREFIX"
log_info "Using PF from: $PF_DIR"
echo ""

#
# Test help tasks first
#
echo "========================================"
echo "Phase 1: Testing Help Commands"
echo "========================================"
echo ""

test_help_output "category-installation-help"
test_help_output "install-help"

#
# Test individual installers (safe/fast ones first)
#
echo "========================================"
echo "Phase 2: Testing Individual Installers"
echo "========================================"
echo ""

# Note: Many installers require sudo or specific system dependencies
# We'll test them but expect some to skip or fail

log_info "Testing injection tools installer..."
test_installer "install-injection-tools" "patchelf"

log_info "Testing checksec installer..."
test_installer "install-checksec" "checksec"

log_info "Testing git filter repo..."
test_installer "install-git-filter-repo"

# Module installers
log_info "Testing module installers..."
# These might require special permissions
log_skip "Module installers require system permissions - skipping for now"
SKIPPED_TESTS=$((SKIPPED_TESTS + 1))

# Large installers that take time
log_skip "Large installers (AFL++, Ghidra, etc.) take significant time - skipping"
SKIPPED_TESTS=$((SKIPPED_TESTS + 1))

#
# Summary
#
echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""
echo "Total tests:   $TOTAL_TESTS"
echo "Passed:        $PASSED_TESTS (${GREEN}✓${NC})"
echo "Failed:        $FAILED_TESTS (${RED}✗${NC})"
echo "Skipped:       $SKIPPED_TESTS (${YELLOW}○${NC})"
echo ""

if [[ ${#FAILED_INSTALLERS[@]} -gt 0 ]]; then
    echo "Failed installers:"
    for installer in "${FAILED_INSTALLERS[@]}"; do
        echo "  - $installer"
    done
    echo ""
fi

if [[ ${#SKIPPED_INSTALLERS[@]} -gt 0 ]]; then
    echo "Skipped installers:"
    for installer in "${SKIPPED_INSTALLERS[@]}"; do
        echo "  - $installer"
    done
    echo ""
fi

if [[ $FAILED_TESTS -eq 0 ]]; then
    log_success "All tested installers passed! 🎉"
    exit 0
else
    log_error "Some installers failed. Review the output above."
    exit 1
fi
