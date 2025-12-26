#!/usr/bin/env bash
# Test script for native installation
# This simulates a fresh Ubuntu installation and tests the native installer

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="${SCRIPT_DIR}/test-native-install-temp"
TEST_PREFIX="${TEST_DIR}/install-target"

log_info() {
    echo -e "${BLUE}[TEST INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[TEST SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[TEST ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[TEST WARNING]${NC} $1"
}

cleanup() {
    log_info "Cleaning up test directory..."
    if [[ -d "$TEST_DIR" ]]; then
        rm -rf "$TEST_DIR"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

test_prerequisites() {
    log_info "Testing prerequisite checks..."
    
    # Python 3 should be available
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 not found - prerequisite check should catch this"
        return 1
    fi
    
    # Git should be available
    if ! command -v git >/dev/null 2>&1; then
        log_error "Git not found - prerequisite check should catch this"
        return 1
    fi
    
    # pip should be available
    if ! python3 -m pip --version >/dev/null 2>&1; then
        log_error "pip not found - prerequisite check should catch this"
        return 1
    fi
    
    log_success "All prerequisites available"
    return 0
}

test_native_install() {
    log_info "Testing native installation to ${TEST_PREFIX}..."
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    cd "$REPO_ROOT"
    
    # Run installer with test prefix
    log_info "Running: ./install.sh --mode native --prefix ${TEST_PREFIX} --skip-deps"
    if ! ./install.sh --mode native --prefix "${TEST_PREFIX}" --skip-deps; then
        log_error "Native installation failed"
        return 1
    fi
    
    log_success "Native installation completed"
    return 0
}

test_pf_executable() {
    log_info "Testing pf executable..."
    
    local pf_cmd="${TEST_PREFIX}/bin/pf"
    
    # Check if pf exists
    if [[ ! -f "$pf_cmd" ]]; then
        log_error "pf executable not found at ${pf_cmd}"
        return 1
    fi
    
    # Check if pf is executable
    if [[ ! -x "$pf_cmd" ]]; then
        log_error "pf is not executable"
        return 1
    fi
    
    log_success "pf executable exists and is executable"
    return 0
}

test_pf_functionality() {
    log_info "Testing pf functionality..."
    
    local pf_cmd="${TEST_PREFIX}/bin/pf"
    export PATH="${TEST_PREFIX}/bin:$PATH"
    
    # Test pf --version
    log_info "Testing: ${pf_cmd} --version"
    if ! "${pf_cmd}" --version >/dev/null 2>&1; then
        log_error "pf --version failed"
        log_info "Trying with explicit python..."
        python3 "${TEST_PREFIX}/lib/pf-runner/pf_parser.py" --version || true
        return 1
    fi
    
    # Test pf list
    log_info "Testing: ${pf_cmd} list"
    if ! "${pf_cmd}" list >/dev/null 2>&1; then
        log_error "pf list failed"
        return 1
    fi
    
    log_success "pf basic functionality working"
    return 0
}

test_python_dependencies() {
    log_info "Testing Python dependencies..."
    
    local venv_python="${TEST_PREFIX}/lib/pf-runner-venv/bin/python"
    
    if [[ -f "$venv_python" ]]; then
        log_info "Virtual environment found at ${TEST_PREFIX}/lib/pf-runner-venv"
        
        # Test fabric import
        if ! "$venv_python" -c "import fabric" 2>/dev/null; then
            log_error "fabric not installed in venv"
            return 1
        fi
        
        # Test lark import
        if ! "$venv_python" -c "import lark" 2>/dev/null; then
            log_error "lark not installed in venv"
            return 1
        fi
        
        log_success "All Python dependencies available in venv"
    else
        log_info "No venv found, checking system python..."
        
        # Test fabric import
        if ! python3 -c "import fabric" 2>/dev/null; then
            log_error "fabric not installed in system python"
            return 1
        fi
        
        # Test lark import
        if ! python3 -c "import lark" 2>/dev/null; then
            log_error "lark not installed in system python"
            return 1
        fi
        
        log_success "All Python dependencies available in system python"
    fi
    
    return 0
}

test_no_hardcoded_paths() {
    log_info "Checking for hardcoded paths..."
    
    local lib_dir="${TEST_PREFIX}/lib/pf-runner"
    
    # Check pf_parser.py for hardcoded paths
    if grep -q "/home/punk" "${lib_dir}/pf_parser.py" 2>/dev/null; then
        log_error "Found hardcoded /home/punk path in pf_parser.py"
        return 1
    fi
    
    # Check for absolute paths that aren't dynamic
    if head -1 "${lib_dir}/pf_parser.py" | grep -q "/home/" | grep -v "/usr/bin/env"; then
        log_error "Found suspicious absolute path in pf_parser.py shebang"
        head -1 "${lib_dir}/pf_parser.py"
        return 1
    fi
    
    log_success "No hardcoded paths found"
    return 0
}

test_file_structure() {
    log_info "Verifying installed file structure..."
    
    local expected_files=(
        "${TEST_PREFIX}/bin/pf"
        "${TEST_PREFIX}/lib/pf-runner/pf_parser.py"
        "${TEST_PREFIX}/lib/pf-runner/Pfyfile.pf"
    )
    
    for file in "${expected_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Expected file not found: $file"
            return 1
        fi
    done
    
    log_success "All expected files present"
    return 0
}

run_all_tests() {
    local failed=0
    local passed=0
    
    echo ""
    echo "================================="
    echo "Native Installer Test Suite"
    echo "================================="
    echo ""
    
    # Run tests
    if test_prerequisites; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_native_install; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_file_structure; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_no_hardcoded_paths; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_pf_executable; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_python_dependencies; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_pf_functionality; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo ""
    echo "================================="
    echo "Test Results"
    echo "================================="
    echo -e "${GREEN}Passed: ${passed}${NC}"
    echo -e "${RED}Failed: ${failed}${NC}"
    echo ""
    
    if [[ $failed -eq 0 ]]; then
        log_success "All tests passed!"
        return 0
    else
        log_error "${failed} test(s) failed"
        return 1
    fi
}

# Main
main() {
    if run_all_tests; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
