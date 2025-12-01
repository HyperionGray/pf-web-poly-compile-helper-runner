#!/bin/bash
# run_all_grammar_tests.sh - Main entry point for grammar unit tests
# Runs all grammar test suites and produces a summary report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     pf Grammar Unit Tests - Comprehensive Test Suite            ║"
echo "║     Testing ALL grammar features from pf.lark and docs          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Track overall results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Array to store results
declare -a SUITE_RESULTS

run_suite() {
    local name=$1
    local script=$2
    
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Running: $name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -x "$script" ]; then
        if bash "$script"; then
            PASSED_SUITES=$((PASSED_SUITES + 1))
            SUITE_RESULTS+=("${GREEN}✓${NC} $name")
        else
            FAILED_SUITES=$((FAILED_SUITES + 1))
            SUITE_RESULTS+=("${RED}✗${NC} $name")
        fi
    else
        echo -e "${YELLOW}Warning: $script not found or not executable${NC}"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        SUITE_RESULTS+=("${YELLOW}○${NC} $name (script not found)")
    fi
    
    echo ""
}

# Run all test suites
run_suite "Core Grammar Tests" "$SCRIPT_DIR/test_grammar.sh"
run_suite "Polyglot Language Tests" "$SCRIPT_DIR/test_polyglot.sh"
run_suite "Build Helper Tests" "$SCRIPT_DIR/test_build_helpers.sh"
run_suite "Web/API Tests" "$SCRIPT_DIR/test_web_api.sh"
run_suite "Debugging/RE Tests" "$SCRIPT_DIR/test_debugging.sh"

# Print overall summary
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     OVERALL TEST SUMMARY                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "Test Suite Results:"
echo "───────────────────"
for result in "${SUITE_RESULTS[@]}"; do
    echo -e "  $result"
done
echo ""

echo "───────────────────"
echo -e "Total Suites:  $TOTAL_SUITES"
echo -e "${GREEN}Passed:${NC}        $PASSED_SUITES"
echo -e "${RED}Failed:${NC}        $FAILED_SUITES"
echo "───────────────────"

echo ""
if [ $FAILED_SUITES -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ALL TEST SUITES PASSED! Grammar coverage complete.          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     SOME TEST SUITES FAILED! Please review the output above.    ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
