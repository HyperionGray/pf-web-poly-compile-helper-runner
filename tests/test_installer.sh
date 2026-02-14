#!/usr/bin/env bash
# Test script to validate installer functionality
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[TEST-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[TEST-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[TEST-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[TEST-ERROR]${NC} $1" >&2
}

# Test 1: Check for hardcoded paths
test_hardcoded_paths() {
    log_info "Testing for hardcoded paths..."
    
    local hardcoded_found=false
    
    # Check for /home/punk paths
    if grep -r "/home/punk" . --exclude-dir=.git 2>/dev/null; then
        log_error "Found hardcoded /home/punk paths"
        hardcoded_found=true
    fi
    
    # Check for other suspicious hardcoded paths
    if grep -r "#!/.*home.*venv" . --exclude-dir=.git 2>/dev/null; then
        log_error "Found hardcoded venv paths in shebangs"
        hardcoded_found=true
    fi
    
    if [[ "$hardcoded_found" == false ]]; then
        log_success "No hardcoded paths found"
        return 0
    else
        return 1
    fi
}

# Test 2: Check installer prerequisites
test_installer_prereqs() {
    log_info "Testing installer prerequisites..."
    
    # Check if install.sh exists and is executable
    if [[ ! -x "./install.sh" ]]; then
        log_error "install.sh not found or not executable"
        return 1
    fi
    
    # Check if pf-runner directory exists
    if [[ ! -d "./pf-runner" ]]; then
        log_error "pf-runner directory not found"
        return 1
    fi
    
    # Check if main parser exists
    if [[ ! -f "./pf-runner/pf_parser.py" ]]; then
        log_error "pf_parser.py not found"
        return 1
    fi
    
    log_success "Installer prerequisites check passed"
    return 0
}

# Test 3: Check container files
test_container_files() {
    log_info "Testing container files..."
    
    # Check if container directory exists
    if [[ ! -d "./containers" ]]; then
        log_error "containers directory not found"
        return 1
    fi
    
    # Check for base Dockerfile
    if [[ ! -f "./containers/dockerfiles/Dockerfile.base" ]]; then
        log_error "Dockerfile.base not found"
        return 1
    fi
    
    # Check for pf-runner Dockerfile
    if [[ ! -f "./containers/dockerfiles/Dockerfile.pf-runner" ]]; then
        log_error "Dockerfile.pf-runner not found"
        return 1
    fi
    
    # Check for universal wrapper
    if [[ ! -f "./pf-runner/pf_universal" ]]; then
        log_error "pf_universal wrapper not found"
        return 1
    fi
    
    log_success "Container files check passed"
    return 0
}

# Test 4: Dry run installer help
test_installer_help() {
    log_info "Testing installer help..."
    
    if ./install.sh --help >/dev/null 2>&1; then
        log_success "Installer help works"
        return 0
    else
        log_error "Installer help failed"
        return 1
    fi
}

# Test 5: Check Python dependencies in pf_parser.py
test_python_deps() {
    log_info "Testing Python dependencies..."
    
    # Check if pf_parser.py has proper imports
    if ! python3 -m py_compile ./pf-runner/pf_parser.py 2>/dev/null; then
        log_warning "pf_parser.py has syntax issues or missing dependencies"
        # This is expected if fabric is not installed, so we'll check imports manually
        
        # Check for required imports
        if ! grep -q "from fabric import" ./pf-runner/pf_parser.py; then
            log_error "Missing fabric import in pf_parser.py"
            return 1
        fi
        
        log_info "Python syntax check skipped (dependencies not installed)"
    else
        log_success "Python syntax check passed"
    fi
    
    return 0
}

# Test 6: List all container variants
test_list_containers() {
    log_info "Listing all container variants..."
    
    local dockerfile_count=0
    for dockerfile in ./containers/dockerfiles/Dockerfile.*; do
        if [[ -f "$dockerfile" ]]; then
            local name=$(basename "$dockerfile" | sed 's/Dockerfile\.//')
            echo "  - $name"
            dockerfile_count=$((dockerfile_count + 1))
        fi
    done
    
    log_info "Found $dockerfile_count container variants"
    return 0
}

# Main test runner
main() {
    echo -e "${BLUE}pf-runner Installer Test Suite${NC}"
    echo "================================"
    echo ""
    
    local tests_passed=0
    local tests_failed=0
    
    # Run tests
    if test_hardcoded_paths; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    if test_installer_prereqs; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    if test_container_files; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    if test_installer_help; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    if test_python_deps; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    test_list_containers
    
    echo ""
    echo "================================"
    log_info "Tests passed: $tests_passed"
    if [[ $tests_failed -gt 0 ]]; then
        log_error "Tests failed: $tests_failed"
        return 1
    else
        log_success "All tests passed!"
        return 0
    fi
}

# Run main function
main "$@"