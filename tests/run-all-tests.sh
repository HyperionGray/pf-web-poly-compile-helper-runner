#!/bin/bash
# Master Test Runner for pf Language
# Runs ALL comprehensive tests for the pf language and framework

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source shared test utilities if available
if [ -f "$SCRIPT_DIR/lib/test-utils.sh" ]; then
    source "$SCRIPT_DIR/lib/test-utils.sh"
fi

# Colors for output (define even if sourced, as this file has suite-specific logging)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test suite counters
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

log_suite() {
    echo -e "${CYAN}[SUITE]${NC} $1"
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
}

log_suite_pass() {
    echo -e "${GREEN}[SUITE PASS]${NC} $1"
    PASSED_SUITES=$((PASSED_SUITES + 1))
}

log_suite_fail() {
    echo -e "${RED}[SUITE FAIL]${NC} $1"
    FAILED_SUITES=$((FAILED_SUITES + 1))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Function to run a test suite
run_test_suite() {
    local suite_name="$1"
    local test_script="$2"
    
    log_suite "Running $suite_name"
    
    if [ ! -f "$test_script" ]; then
        log_suite_fail "$suite_name - Test script not found: $test_script"
        return 1
    fi
    
    if [ ! -x "$test_script" ]; then
        chmod +x "$test_script"
    fi
    
    if "$test_script"; then
        log_suite_pass "$suite_name"
        return 0
    else
        log_suite_fail "$suite_name"
        return 1
    fi
}

echo "=================================================================="
echo "                pf Language Comprehensive Test Suite"
echo "=================================================================="
echo "Testing ALL grammar features, APIs, compilation targets,"
echo "debugging tools, and ensuring docs align with implementation"
echo "=================================================================="
echo

# Check if we're in the right directory
if [ ! -f "$ROOT_DIR/Pfyfile.pf" ]; then
    echo -e "${RED}Error: Not in pf repository root. Expected to find Pfyfile.pf${NC}"
    exit 1
fi

# Check basic dependencies
log_info "Checking basic dependencies..."
missing_deps=()

if ! command -v python3 >/dev/null 2>&1; then
    missing_deps+=("python3")
fi

if ! command -v bash >/dev/null 2>&1; then
    missing_deps+=("bash")
fi

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo -e "${RED}Missing critical dependencies: ${missing_deps[*]}${NC}"
    echo "Please install the missing dependencies and try again."
    exit 1
fi

log_info "Basic dependencies satisfied"
echo

# Test Suite 0: Install / Container Build Smoke Test
echo "=================================================================="
echo "0. INSTALL / CONTAINER BUILD SMOKE TEST"
echo "=================================================================="
if [ -f "$SCRIPT_DIR/install/test-install-wrapper.sh" ]; then
    run_test_suite "Install Script (podman)" "$SCRIPT_DIR/install/test-install-wrapper.sh"
else
    log_info "Install smoke test not found, skipping"
fi
echo

# Test Suite 1: Grammar Testing
echo "=================================================================="
echo "1. GRAMMAR TESTING"
echo "=================================================================="
run_test_suite "Grammar Rule Validation" "$SCRIPT_DIR/grammar/test-grammar.sh"
echo

# Test Suite 2: Shell Script Feature Testing
echo "=================================================================="
echo "2. SHELL SCRIPT FEATURE TESTING"
echo "=================================================================="
run_test_suite "All DSL Features" "$SCRIPT_DIR/shell-scripts/test-all-features.sh"
run_test_suite "Polyglot Languages" "$SCRIPT_DIR/shell-scripts/test-polyglot-languages.sh"
echo

# Test Suite 3: API Testing
echo "=================================================================="
echo "3. API TESTING"
echo "=================================================================="
run_test_suite "REST API & WebSocket" "$SCRIPT_DIR/api/test-rest-api.sh"
echo

# Test Suite 4: Compilation Testing
echo "=================================================================="
echo "4. COMPILATION TESTING"
echo "=================================================================="
run_test_suite "All Compilation Targets" "$SCRIPT_DIR/compilation/test-all-targets.sh"
echo

# Test Suite 5: Debugging Workflow Testing
echo "=================================================================="
echo "5. DEBUGGING WORKFLOW TESTING"
echo "=================================================================="
run_test_suite "Debugging Tools & Workflows" "$SCRIPT_DIR/debugging/test-debugging-workflows.sh"
echo

# Test Suite 6: TUI Testing (existing)
echo "=================================================================="
echo "6. TUI TESTING"
echo "=================================================================="
if [ -f "$SCRIPT_DIR/tui/run-all-tui-tests.mjs" ]; then
    log_suite "Running TUI Tests"
    cd "$SCRIPT_DIR/tui"
    if node run-all-tui-tests.mjs; then
        log_suite_pass "TUI Tests"
    else
        log_suite_fail "TUI Tests"
    fi
    cd "$ROOT_DIR"
else
    log_info "TUI tests not found, skipping"
fi
echo

# Test Suite 7: Integration Testing
echo "=================================================================="
echo "7. INTEGRATION TESTING"
echo "=================================================================="
log_suite "Running Integration Tests"

# Test that pf command works
if command -v pf >/dev/null 2>&1; then
    if pf list >/dev/null 2>&1; then
        log_suite_pass "pf command integration"
    else
        log_suite_fail "pf command integration - pf list failed"
    fi
else
    log_suite_fail "pf command integration - pf command not found"
fi

# Test that basic tasks work
cd "$ROOT_DIR"
if pf --help >/dev/null 2>&1; then
    log_suite_pass "pf help integration"
else
    log_suite_fail "pf help integration"
fi
echo

# Test Suite 8: Performance Testing
echo "=================================================================="
echo "8. PERFORMANCE TESTING"
echo "=================================================================="
log_suite "Running Performance Tests"

# Test large Pfyfile parsing performance
start_time=$(date +%s%N)
pf list >/dev/null 2>&1
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

if [ $duration -lt 2000 ]; then # Less than 2 seconds
    log_suite_pass "Pfyfile parsing performance - ${duration}ms"
else
    log_suite_fail "Pfyfile parsing performance - ${duration}ms (>2s)"
fi
echo

# Test Suite 9: Error Handling Testing
echo "=================================================================="
echo "9. ERROR HANDLING TESTING"
echo "=================================================================="
log_suite "Running Error Handling Tests"

# Test invalid Pfyfile handling
INVALID_PF_FILE=$(mktemp)
echo "invalid syntax" > "$INVALID_PF_FILE"
if pf --file="$INVALID_PF_FILE" list 2>/dev/null; then
    log_suite_fail "Invalid Pfyfile handling - Should have failed"
else
    log_suite_pass "Invalid Pfyfile handling - Correctly rejected"
fi
rm -f "$INVALID_PF_FILE"

# Test missing task handling
if pf nonexistent-task 2>/dev/null; then
    log_suite_fail "Missing task handling - Should have failed"
else
    log_suite_pass "Missing task handling - Correctly rejected"
fi
echo

# Test Suite 10: Documentation Validation
echo "=================================================================="
echo "10. DOCUMENTATION VALIDATION"
echo "=================================================================="
log_suite "Running Documentation Validation"

# Check that documented tasks exist
documented_tasks=("web-dev" "web-build-rust" "web-build-c" "api-server" "tui" "install")
missing_tasks=()

for task in "${documented_tasks[@]}"; do
    if ! pf list | grep -q "$task"; then
        missing_tasks+=("$task")
    fi
done

if [ ${#missing_tasks[@]} -eq 0 ]; then
    log_suite_pass "Documentation validation - All documented tasks exist"
else
    log_suite_fail "Documentation validation - Missing tasks: ${missing_tasks[*]}"
fi
echo

# Final Results
echo "=================================================================="
echo "                        FINAL RESULTS"
echo "=================================================================="
echo "Total test suites: $TOTAL_SUITES"
echo "Passed suites: $PASSED_SUITES"
echo "Failed suites: $FAILED_SUITES"
echo

if [ $FAILED_SUITES -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}The pf language implementation is comprehensive and robust.${NC}"
    echo -e "${GREEN}All grammar features, APIs, compilation targets, and debugging tools are working.${NC}"
    echo -e "${GREEN}Documentation is aligned with implementation.${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED ❌${NC}"
    echo -e "${RED}$FAILED_SUITES out of $TOTAL_SUITES test suites failed.${NC}"
    echo -e "${YELLOW}Please review the failed tests and fix the issues before deployment.${NC}"
    exit 1
fi