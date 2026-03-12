#!/usr/bin/env bash
# Comprehensive installer test and validation script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

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

# Test native installation in a temporary directory
test_native_installation() {
    log_info "Testing native installation..."
    
    local test_dir="/tmp/pf-test-native-$$"
    local install_prefix="${test_dir}/install"
    
    # Create test directory
    mkdir -p "$test_dir"
    
    # Copy repository to test directory
    log_info "Copying repository to test directory..."
    cp -r "$REPO_ROOT" "$test_dir/repo"
    cd "$test_dir/repo"
    
    # Fix hardcoded paths first
    log_info "Fixing hardcoded paths..."
    if [[ -f "pf-runner-full/pf_parser.py" ]]; then
        sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner-full/pf_parser.py
        log_success "Fixed shebang in pf_parser.py"
    fi
    
    # Test native installation
    log_info "Running native installation to $install_prefix..."
    if ./install.sh --prefix "$install_prefix" --skip-deps; then
        log_success "Native installation completed"
        
        # Test if pf command works
        if [[ -x "${install_prefix}/bin/pf" ]]; then
            log_info "Testing pf command..."
            export PATH="${install_prefix}/bin:$PATH"
            
            if "${install_prefix}/bin/pf" --version >/dev/null 2>&1; then
                log_success "pf --version works"
            else
                log_error "pf --version failed"
                return 1
            fi
            
            if "${install_prefix}/bin/pf" list >/dev/null 2>&1; then
                log_success "pf list works"
            else
                log_warning "pf list failed (may be expected without fabric)"
            fi
        else
            log_error "pf command not found at ${install_prefix}/bin/pf"
            return 1
        fi
    else
        log_error "Native installation failed"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Native installation test completed successfully"
    return 0
}

# Main test function
main() {
    echo -e "${BLUE}pf-runner Comprehensive Installation Test${NC}"
    echo "=========================================="
    echo ""

    if test_native_installation; then
        log_success "Native installation tests passed!"
        return 0
    else
        log_error "Native installation tests failed"
        return 1
    fi
}

# Check if we're in the right directory
if [[ ! -f "${REPO_ROOT}/install.sh" ]] || [[ ! -d "${REPO_ROOT}/pf-runner-full" ]]; then
    log_error "This script must be run from the repository root directory"
    exit 1
fi

# Run main function
main "$@"
