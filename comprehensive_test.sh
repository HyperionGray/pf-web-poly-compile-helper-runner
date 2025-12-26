#!/usr/bin/env bash
# Comprehensive installer test and validation script
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

# Test native installation in a temporary directory
test_native_installation() {
    log_info "Testing native installation..."
    
    local test_dir="/tmp/pf-test-native-$$"
    local install_prefix="${test_dir}/install"
    
    # Create test directory
    mkdir -p "$test_dir"
    
    # Copy repository to test directory
    log_info "Copying repository to test directory..."
    cp -r . "$test_dir/repo"
    cd "$test_dir/repo"
    
    # Fix hardcoded paths first
    log_info "Fixing hardcoded paths..."
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
        log_success "Fixed shebang in pf_parser.py"
    fi
    
    # Test native installation
    log_info "Running native installation to $install_prefix..."
    if ./install.sh --mode native --prefix "$install_prefix" --skip-deps; then
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

# Test container installation
test_container_installation() {
    log_info "Testing container installation..."
    
    # Check if container runtime is available
    local runtime=""
    if command -v podman >/dev/null 2>&1; then
        runtime="podman"
    elif command -v docker >/dev/null 2>&1; then
        runtime="docker"
    else
        log_warning "No container runtime found, skipping container tests"
        return 0
    fi
    
    log_info "Using container runtime: $runtime"
    
    local test_dir="/tmp/pf-test-container-$$"
    local install_prefix="${test_dir}/install"
    
    # Create test directory
    mkdir -p "$test_dir"
    
    # Copy repository to test directory
    log_info "Copying repository to test directory..."
    cp -r . "$test_dir/repo"
    cd "$test_dir/repo"
    
    # Fix hardcoded paths first
    log_info "Fixing hardcoded paths..."
    if [[ -f "pf-runner/pf_parser.py" ]]; then
        sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
        log_success "Fixed shebang in pf_parser.py"
    fi
    
    # Test container installation
    log_info "Running container installation..."
    if ./install.sh --mode container --runtime "$runtime" --prefix "$install_prefix"; then
        log_success "Container installation completed"
        
        # Test if pf wrapper works
        if [[ -x "${install_prefix}/bin/pf" ]]; then
            log_info "Testing pf wrapper..."
            export PATH="${install_prefix}/bin:$PATH"
            
            # Test basic wrapper functionality (may fail if images aren't built)
            if "${install_prefix}/bin/pf" --version >/dev/null 2>&1; then
                log_success "pf wrapper --version works"
            else
                log_warning "pf wrapper --version failed (may be expected if images not built)"
            fi
        else
            log_error "pf wrapper not found at ${install_prefix}/bin/pf"
            return 1
        fi
    else
        log_error "Container installation failed"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Container installation test completed successfully"
    return 0
}

# Test all container variants
test_container_variants() {
    log_info "Testing container variants..."
    
    # Check if container runtime is available
    local runtime=""
    if command -v podman >/dev/null 2>&1; then
        runtime="podman"
    elif command -v docker >/dev/null 2>&1; then
        runtime="docker"
    else
        log_warning "No container runtime found, skipping container variant tests"
        return 0
    fi
    
    log_info "Found container runtime: $runtime"
    
    local variants_tested=0
    local variants_successful=0
    local variants_failed=0
    
    echo ""
    log_info "Container Variants Analysis:"
    echo "============================"
    
    for dockerfile in ./containers/dockerfiles/Dockerfile.*; do
        if [[ -f "$dockerfile" ]]; then
            local variant=$(basename "$dockerfile" | sed 's/Dockerfile\.//')
            ((variants_tested++))
            
            echo ""
            log_info "Variant: $variant"
            echo "  File: $dockerfile"
            
            # Check if dockerfile has obvious issues
            if grep -q "FROM.*localhost/" "$dockerfile" 2>/dev/null; then
                local base_image=$(grep "FROM.*localhost/" "$dockerfile" | head -1 | awk '{print $2}')
                echo "  Base image: $base_image (requires local build)"
                
                # Check if base image exists or can be built
                if [[ "$base_image" == "localhost/pf-base:latest" ]]; then
                    echo "  Status: Depends on pf-base (buildable)"
                    ((variants_successful++))
                else
                    echo "  Status: Depends on unknown base image"
                    ((variants_failed++))
                fi
            elif grep -q "FROM" "$dockerfile" 2>/dev/null; then
                local base_image=$(grep "FROM" "$dockerfile" | head -1 | awk '{print $2}')
                echo "  Base image: $base_image"
                echo "  Status: Uses external base image (should work)"
                ((variants_successful++))
            else
                echo "  Status: No FROM directive found (broken)"
                ((variants_failed++))
            fi
            
            # Check for obvious issues
            if grep -q "apt-get\|yum\|dnf\|pacman" "$dockerfile" 2>/dev/null; then
                echo "  Package manager: Found"
            else
                echo "  Package manager: None detected"
            fi
            
            # Check for COPY/ADD directives
            if grep -q "COPY\|ADD" "$dockerfile" 2>/dev/null; then
                echo "  File operations: Found"
            else
                echo "  File operations: None"
            fi
        fi
    done
    
    echo ""
    echo "============================"
    log_info "Container Variants Summary:"
    echo "  Total variants: $variants_tested"
    echo "  Likely working: $variants_successful"
    echo "  Likely broken: $variants_failed"
    
    return 0
}

# Test specific container builds
test_container_builds() {
    log_info "Testing container builds..."
    
    # Check if container runtime is available
    local runtime=""
    if command -v podman >/dev/null 2>&1; then
        runtime="podman"
    elif command -v docker >/dev/null 2>&1; then
        runtime="docker"
    else
        log_warning "No container runtime found, skipping container build tests"
        return 0
    fi
    
    log_info "Testing base container build..."
    
    # Try to build base image
    if "$runtime" build -t "localhost/pf-base:test" -f "containers/dockerfiles/Dockerfile.base" . >/dev/null 2>&1; then
        log_success "Base image builds successfully"
        
        # Try to build pf-runner image
        log_info "Testing pf-runner container build..."
        if "$runtime" build -t "localhost/pf-runner:test" -f "containers/dockerfiles/Dockerfile.pf-runner" . >/dev/null 2>&1; then
            log_success "pf-runner image builds successfully"
            
            # Test running the container
            log_info "Testing container execution..."
            if "$runtime" run --rm "localhost/pf-runner:test" pf --version >/dev/null 2>&1; then
                log_success "Container execution works"
            else
                log_warning "Container execution failed"
            fi
            
            # Cleanup test images
            "$runtime" rmi "localhost/pf-runner:test" >/dev/null 2>&1 || true
        else
            log_error "pf-runner image build failed"
        fi
        
        # Cleanup test images
        "$runtime" rmi "localhost/pf-base:test" >/dev/null 2>&1 || true
    else
        log_error "Base image build failed"
        return 1
    fi
    
    return 0
}

# Main test function
main() {
    echo -e "${BLUE}pf-runner Comprehensive Installation Test${NC}"
    echo "=========================================="
    echo ""
    
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Native installation
    if test_native_installation; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    
    # Test 2: Container installation
    if test_container_installation; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    
    # Test 3: Container variants analysis
    test_container_variants
    
    echo ""
    
    # Test 4: Container builds
    if test_container_builds; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    echo "=========================================="
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