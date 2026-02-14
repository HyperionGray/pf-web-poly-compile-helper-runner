#!/usr/bin/env bash
# Master installer validation script
# Runs all tests and provides comprehensive installer validation
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
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

log_header() {
    echo -e "${BOLD}${BLUE}$1${NC}"
}

# Apply all necessary fixes
apply_fixes() {
    log_header "Applying Repository Fixes"
    echo "=========================="
    
    local fixes_applied=0
    
    # Fix 1: Hardcoded shebang in pf_parser.py
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        local current_shebang=$(head -1 pf-runner/pf_parser.py)
        if [[ "$current_shebang" != "#!/usr/bin/env python3" ]]; then
            log_info "Fixing hardcoded shebang in pf_parser.py..."
            cp pf-runner/pf_parser.py pf-runner/pf_parser.py.backup
            sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
            log_success "Fixed shebang: $current_shebang -> #!/usr/bin/env python3"
            fixes_applied=$((fixes_applied + 1))
        else
            log_success "Shebang already correct in pf_parser.py"
        fi
    else
        log_error "pf_parser.py not found"
        return 1
    fi
    
    # Fix 2: Make scripts executable
    if [[ -f "install.sh" ]]; then
        chmod +x install.sh
        log_success "Made install.sh executable"
    fi
    
    if [[ -f "pf-runner/pf_universal" ]]; then
        chmod +x pf-runner/pf_universal
        log_success "Made pf_universal executable"
    fi
    
    # Fix 3: Check for other hardcoded paths
    log_info "Checking for remaining hardcoded paths..."
    if grep -r "/home/punk" . --exclude-dir=.git --exclude="*.backup" 2>/dev/null; then
        log_warning "Found additional hardcoded paths that may need fixing"
    else
        log_success "No additional hardcoded paths found"
    fi
    
    echo ""
    log_success "Applied $fixes_applied fixes to repository"
    return 0
}

# Run native installer tests
run_native_tests() {
    log_header "Native Installer Tests"
    echo "======================"
    
    if [[ -x "./test_native_installer.sh" ]]; then
        if ./test_native_installer.sh; then
            log_success "Native installer tests passed"
            return 0
        else
            log_error "Native installer tests failed"
            return 1
        fi
    else
        log_warning "Native installer test script not found or not executable"
        return 1
    fi
}

# Run container installer tests
run_container_tests() {
    log_header "Container Installer Tests"
    echo "========================="
    
    if [[ -x "./test_container_installer.sh" ]]; then
        if ./test_container_installer.sh; then
            log_success "Container installer tests passed"
            return 0
        else
            log_error "Container installer tests failed"
            return 1
        fi
    else
        log_warning "Container installer test script not found or not executable"
        return 1
    fi
}

# Generate comprehensive report
generate_report() {
    local native_result="$1"
    local container_result="$2"
    
    echo ""
    log_header "Comprehensive Installer Validation Report"
    echo "=========================================="
    echo ""
    
    # System information
    log_info "System Information:"
    echo "  OS: $(uname -s) $(uname -r)"
    echo "  Architecture: $(uname -m)"
    if command -v lsb_release >/dev/null 2>&1; then
        echo "  Distribution: $(lsb_release -d | cut -f2)"
    fi
    echo "  Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "  Git: $(git --version 2>/dev/null || echo 'Not found')"
    echo "  Podman: $(podman --version 2>/dev/null || echo 'Not found')"
    echo "  Docker: $(docker --version 2>/dev/null || echo 'Not found')"
    echo ""
    
    # Repository status
    log_info "Repository Status:"
    echo "  Location: $(pwd)"
    echo "  install.sh: $(if [[ -x install.sh ]]; then echo 'Present and executable'; else echo 'Missing or not executable'; fi)"
    echo "  pf-runner/: $(if [[ -d pf-runner ]]; then echo 'Present'; else echo 'Missing'; fi)"
    echo "  containers/: $(if [[ -d containers ]]; then echo 'Present'; else echo 'Missing'; fi)"
    
    # Check shebang status
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        local shebang=$(head -1 pf-runner/pf_parser.py)
        echo "  pf_parser.py shebang: $shebang"
    fi
    echo ""
    
    # Test results
    log_info "Test Results:"
    if [[ "$native_result" == "0" ]]; then
        echo "  ✓ Native installer: PASSED"
    else
        echo "  ✗ Native installer: FAILED"
    fi
    
    if [[ "$container_result" == "0" ]]; then
        echo "  ✓ Container installer: PASSED"
    else
        echo "  ✗ Container installer: FAILED"
    fi
    echo ""
    
    # Container variants summary
    log_info "Container Variants:"
    local variant_count=0
    for dockerfile in ./containers/dockerfiles/Dockerfile.*; do
        if [[ -f "$dockerfile" ]]; then
            local variant=$(basename "$dockerfile" | sed 's/Dockerfile\.//')
            echo "  - $variant"
            variant_count=$((variant_count + 1))
        fi
    done
    echo "  Total: $variant_count variants"
    echo ""
    
    # Recommendations
    log_info "Recommendations:"
    
    if [[ "$native_result" == "0" ]]; then
        echo "  ✓ Native installation is ready for users"
        echo "    Command: ./install.sh --mode native"
        echo "    User install: ./install.sh --mode native --prefix ~/.local"
        echo "    System install: sudo ./install.sh --mode native"
    else
        echo "  ✗ Native installation needs fixes before user deployment"
    fi
    
    if [[ "$container_result" == "0" ]]; then
        echo "  ✓ Container installation is ready for users"
        echo "    Command: ./install.sh --mode container"
        echo "    With podman: ./install.sh --mode container --runtime podman"
        echo "    With docker: ./install.sh --mode container --runtime docker"
    else
        echo "  ✗ Container installation needs fixes before user deployment"
    fi
    
    echo ""
    
    # Overall status
    if [[ "$native_result" == "0" ]] && [[ "$container_result" == "0" ]]; then
        log_success "🎉 All installers are working correctly!"
        echo ""
        echo "Users can now:"
        echo "1. Install natively on fresh Ubuntu: ./install.sh --mode native"
        echo "2. Install with containers: ./install.sh --mode container"
        echo "3. Choose their preferred installation method"
        echo ""
        return 0
    elif [[ "$native_result" == "0" ]] || [[ "$container_result" == "0" ]]; then
        log_warning "⚠️  Some installers are working, but not all"
        echo ""
        echo "Partial success - at least one installation method works"
        echo ""
        return 1
    else
        log_error "❌ Both installers have issues that need to be resolved"
        echo ""
        echo "Both installation methods need fixes before user deployment"
        echo ""
        return 1
    fi
}

# Main function
main() {
    echo -e "${BOLD}${BLUE}pf-runner Master Installer Validation${NC}"
    echo "======================================"
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "install.sh" ]] || [[ ! -d "pf-runner" ]]; then
        log_error "This script must be run from the repository root directory"
        exit 1
    fi
    
    # Apply fixes
    if ! apply_fixes; then
        log_error "Failed to apply repository fixes"
        exit 1
    fi
    
    echo ""
    
    # Make test scripts executable
    chmod +x test_native_installer.sh 2>/dev/null || true
    chmod +x test_container_installer.sh 2>/dev/null || true
    
    # Run native tests
    local native_result=1
    if run_native_tests; then
        native_result=0
    fi
    
    echo ""
    
    # Run container tests
    local container_result=1
    if run_container_tests; then
        container_result=0
    fi
    
    # Generate comprehensive report
    generate_report "$native_result" "$container_result"
}

# Run main function
main "$@"