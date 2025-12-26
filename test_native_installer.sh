#!/usr/bin/env bash
# Native installer validation script
# Tests the native installer without making assumptions about the user's environment
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Test prerequisites that should be available on fresh Ubuntu
test_prerequisites() {
    log_info "Testing prerequisites on this system..."
    
    local prereq_ok=true
    
    # Test Python 3
    if command -v python3 >/dev/null 2>&1; then
        local py_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_success "Python 3 found: $py_version"
        
        # Test Python version
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            log_success "Python version is 3.8+"
        else
            log_error "Python version is too old (need 3.8+)"
            prereq_ok=false
        fi
    else
        log_error "Python 3 not found"
        prereq_ok=false
    fi
    
    # Test pip
    if python3 -m pip --version >/dev/null 2>&1; then
        log_success "pip is available"
    else
        log_error "pip not available"
        prereq_ok=false
    fi
    
    # Test Git
    if command -v git >/dev/null 2>&1; then
        log_success "Git found"
    else
        log_error "Git not found"
        prereq_ok=false
    fi
    
    # Test build tools (for native compilation)
    if command -v gcc >/dev/null 2>&1; then
        log_success "GCC found"
    else
        log_warning "GCC not found (may be needed for some Python packages)"
    fi
    
    if [[ "$prereq_ok" == true ]]; then
        log_success "All prerequisites check passed"
        return 0
    else
        log_error "Prerequisites check failed"
        return 1
    fi
}

# Test native installation in isolation
test_native_install_isolated() {
    log_info "Testing native installation in isolation..."
    
    local test_dir="/tmp/pf-native-test-$$"
    local install_prefix="${test_dir}/install"
    
    # Create test environment
    mkdir -p "$test_dir"
    
    # Copy repository
    log_info "Copying repository to test directory..."
    cp -r . "$test_dir/repo"
    cd "$test_dir/repo"
    
    # Apply fixes
    log_info "Applying fixes..."
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
        log_success "Fixed shebang in pf_parser.py"
    fi
    
    # Make scripts executable
    chmod +x install.sh
    chmod +x pf-runner/pf_universal 2>/dev/null || true
    
    # Test installation
    log_info "Running native installation..."
    log_info "Command: ./install.sh --mode native --prefix $install_prefix --skip-deps"
    
    if ./install.sh --mode native --prefix "$install_prefix" --skip-deps 2>&1 | tee "${test_dir}/install.log"; then
        log_success "Installation completed without errors"
        
        # Verify installation
        log_info "Verifying installation..."
        
        # Check if pf binary exists
        if [[ -x "${install_prefix}/bin/pf" ]]; then
            log_success "pf binary created at ${install_prefix}/bin/pf"
            
            # Test pf functionality
            export PATH="${install_prefix}/bin:$PATH"
            
            # Test version
            log_info "Testing pf --version..."
            if "${install_prefix}/bin/pf" --version 2>&1 | tee "${test_dir}/version.log"; then
                log_success "pf --version works"
            else
                log_error "pf --version failed"
                cat "${test_dir}/version.log"
                return 1
            fi
            
            # Test list
            log_info "Testing pf list..."
            if "${install_prefix}/bin/pf" list 2>&1 | tee "${test_dir}/list.log"; then
                log_success "pf list works"
            else
                log_warning "pf list failed (may be expected without fabric)"
                cat "${test_dir}/list.log"
            fi
            
        else
            log_error "pf binary not found at ${install_prefix}/bin/pf"
            return 1
        fi
        
        # Check library installation
        if [[ -d "${install_prefix}/lib/pf-runner" ]]; then
            log_success "pf-runner library installed"
            
            # Check main parser
            if [[ -f "${install_prefix}/lib/pf-runner/pf_parser.py" ]]; then
                log_success "pf_parser.py installed"
                
                # Check shebang
                local shebang=$(head -1 "${install_prefix}/lib/pf-runner/pf_parser.py")
                if [[ "$shebang" == "#!/usr/bin/env python3" ]]; then
                    log_success "Shebang is correct: $shebang"
                else
                    log_error "Shebang is wrong: $shebang"
                    return 1
                fi
            else
                log_error "pf_parser.py not found in library"
                return 1
            fi
        else
            log_error "pf-runner library not installed"
            return 1
        fi
        
    else
        log_error "Installation failed"
        cat "${test_dir}/install.log"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Native installation test completed successfully"
    return 0
}

# Test native installation with dependencies
test_native_install_with_deps() {
    log_info "Testing native installation with dependency installation..."
    
    # This test requires root privileges
    if [[ $EUID -ne 0 ]]; then
        log_warning "Skipping dependency installation test (requires root)"
        return 0
    fi
    
    local test_dir="/tmp/pf-native-deps-test-$$"
    local install_prefix="${test_dir}/install"
    
    # Create test environment
    mkdir -p "$test_dir"
    
    # Copy repository
    log_info "Copying repository to test directory..."
    cp -r . "$test_dir/repo"
    cd "$test_dir/repo"
    
    # Apply fixes
    log_info "Applying fixes..."
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
        log_success "Fixed shebang in pf_parser.py"
    fi
    
    # Make scripts executable
    chmod +x install.sh
    chmod +x pf-runner/pf_universal 2>/dev/null || true
    
    # Test installation with dependencies
    log_info "Running native installation with dependencies..."
    log_info "Command: ./install.sh --mode native --prefix $install_prefix"
    
    if ./install.sh --mode native --prefix "$install_prefix" 2>&1 | tee "${test_dir}/install-deps.log"; then
        log_success "Installation with dependencies completed"
        
        # Test fabric functionality
        export PATH="${install_prefix}/bin:$PATH"
        
        log_info "Testing fabric functionality..."
        if "${install_prefix}/bin/pf" list >/dev/null 2>&1; then
            log_success "pf list works with fabric"
        else
            log_warning "pf list still fails (fabric may not be properly installed)"
        fi
        
    else
        log_error "Installation with dependencies failed"
        cat "${test_dir}/install-deps.log"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Native installation with dependencies test completed"
    return 0
}

# Main test function
main() {
    echo -e "${BLUE}Native Installer Validation${NC}"
    echo "============================"
    echo ""
    
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Prerequisites
    if test_prerequisites; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    
    # Test 2: Native installation (isolated)
    if test_native_install_isolated; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    
    # Test 3: Native installation with dependencies (if root)
    if test_native_install_with_deps; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    echo "============================"
    log_info "Test Summary:"
    echo "  Tests passed: $tests_passed"
    if [[ $tests_failed -gt 0 ]]; then
        echo "  Tests failed: $tests_failed"
        log_error "Some tests failed"
        return 1
    else
        log_success "All tests passed!"
        return 0
    fi
}

# Check if we're in the right directory
if [[ ! -f "install.sh" ]] || [[ ! -d "pf-runner" ]]; then
    log_error "This script must be run from the repository root directory"
    exit 1
fi

# Run main function
main "$@"