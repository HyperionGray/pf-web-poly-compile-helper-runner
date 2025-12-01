#!/bin/bash
# Shared test utilities for pf test suite
# This file contains common logging functions and utilities used across all test scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters (initialize if not already set)
TOTAL_TESTS=${TOTAL_TESTS:-0}
PASSED_TESTS=${PASSED_TESTS:-0}
FAILED_TESTS=${FAILED_TESTS:-0}

# Logging functions for test output
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Print test summary
print_test_summary() {
    local test_type="${1:-Test}"
    local test_type_lower
    test_type_lower=$(echo "$test_type" | tr '[:upper:]' '[:lower:]')
    
    echo
    echo "=== ${test_type} Results ==="
    echo "Total tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}All ${test_type_lower} tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some ${test_type_lower} tests failed!${NC}"
        return 1
    fi
}

# Display last N lines of a log file on failure
display_logs_on_failure() {
    local log_file="$1"
    local lines="${2:-50}"
    
    if [ -f "$log_file" ]; then
        echo "Last $lines lines of $log_file:"
        tail -n "$lines" "$log_file"
    fi
}

# Check OS type for platform-specific tests
get_os_type() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

# Check if running on GNU/Linux (for GNU-specific tools)
is_gnu_linux() {
    [ "$(get_os_type)" = "linux" ]
}
