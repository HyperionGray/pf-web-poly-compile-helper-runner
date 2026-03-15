#!/usr/bin/env bash
# run_installer_tests.sh - Wrapper script to run installer tests
# 
# Usage:
#   ./run_installer_tests.sh [options]
#
# Options:
#   -v, --verbose     Run with verbose output
#   -k EXPRESSION     Only run tests matching EXPRESSION
#   --install-deps    Install test dependencies first
#   --help            Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_help() {
    cat << EOF
pf-runner Installer Test Suite Runner

Usage: ./run_installer_tests.sh [options]

Options:
  -v, --verbose         Run tests with verbose output
  -k EXPRESSION         Only run tests matching EXPRESSION
  --install-deps        Install required Python dependencies first
  --direct              Run only direct execution tests
  --python              Run only Python-mode installer tests
  --static              Run only static installer tests
  --help, -h            Show this help message

Examples:
  # Run all tests
  ./run_installer_tests.sh

  # Run with verbose output
  ./run_installer_tests.sh -v

  # Run only direct execution tests
  ./run_installer_tests.sh --direct

  # Run only Python-mode installer tests
  ./run_installer_tests.sh --python

  # Run only static installer tests
  ./run_installer_tests.sh --static

  # Run tests matching "version"
  ./run_installer_tests.sh -k version

  # Install dependencies and run tests
  ./run_installer_tests.sh --install-deps -v

EOF
}

# Parse command line arguments
VERBOSE=""
FILTER=""
INSTALL_DEPS=false
TEST_CLASS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -k)
            FILTER="-k $2"
            shift 2
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --direct)
            TEST_CLASS="::TestDirectExecution"
            shift
            ;;
        --python)
            TEST_CLASS="::TestPythonModeInstall"
            shift
            ;;
        --static)
            TEST_CLASS="::TestStaticModeInstall"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

cd "$REPO_ROOT"

# Install dependencies if requested
if [[ "$INSTALL_DEPS" == true ]]; then
    log_info "Installing test dependencies..."
    python3 -m pip install -q pytest lark fabric typer json5
    log_success "Dependencies installed"
fi

# Check if pytest is available
if ! python3 -m pytest --version >/dev/null 2>&1; then
    log_warning "pytest not found. Installing..."
    python3 -m pip install -q pytest
fi

# Check if pf-runner dependencies are available
log_info "Checking pf-runner dependencies..."
MISSING_DEPS=""
for dep in lark fabric typer json5; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [[ -n "$MISSING_DEPS" ]]; then
    log_warning "Missing dependencies:$MISSING_DEPS"
    log_info "Install with: pip install$MISSING_DEPS"
    log_info "Or run with: $0 --install-deps"
fi

# Run tests
log_info "Running installer tests..."
echo ""

python3 -m pytest \
    tests/installation/test_installer_comprehensive.py${TEST_CLASS} \
    $VERBOSE \
    $FILTER \
    --tb=short

TEST_RESULT=$?

echo ""
if [[ $TEST_RESULT -eq 0 ]]; then
    log_success "All tests passed!"
else
    log_warning "Some tests failed or were skipped"
    log_info "See README at tests/installation/README_TESTS.md for details"
fi

exit $TEST_RESULT
