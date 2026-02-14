#!/usr/bin/env bash
# Container installer validation script
# Tests the container installer and all container variants
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

# Detect available container runtime
detect_container_runtime() {
    if command -v podman >/dev/null 2>&1; then
        echo "podman"
    elif command -v docker >/dev/null 2>&1; then
        echo "docker"
    else
        echo ""
    fi
}

# Test container runtime availability
test_container_runtime() {
    log_info "Testing container runtime availability..."
    
    local runtime=$(detect_container_runtime)
    
    if [[ -n "$runtime" ]]; then
        log_success "Container runtime found: $runtime"
        
        # Test runtime functionality
        if "$runtime" --version >/dev/null 2>&1; then
            log_success "Container runtime is functional"
        else
            log_error "Container runtime is not functional"
            return 1
        fi
        
        # Test if we can run containers
        if "$runtime" run --rm hello-world >/dev/null 2>&1; then
            log_success "Can run containers successfully"
        else
            log_warning "Cannot run containers (may need daemon or permissions)"
        fi
        
        echo "$runtime"
        return 0
    else
        log_error "No container runtime found (podman or docker required)"
        return 1
    fi
}

# Test container installation
test_container_install() {
    local runtime="$1"
    
    log_info "Testing container installation with $runtime..."
    
    local test_dir="/tmp/pf-container-test-$$"
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
    
    # Test container installation
    log_info "Running container installation..."
    log_info "Command: ./install.sh --mode container --runtime $runtime --prefix $install_prefix"
    
    if ./install.sh --mode container --runtime "$runtime" --prefix "$install_prefix" 2>&1 | tee "${test_dir}/install.log"; then
        log_success "Container installation completed"
        
        # Verify installation
        log_info "Verifying container installation..."
        
        # Check if pf wrapper exists
        if [[ -x "${install_prefix}/bin/pf" ]]; then
            log_success "pf wrapper created at ${install_prefix}/bin/pf"
            
            # Check wrapper content
            if grep -q "PF_IMAGE" "${install_prefix}/bin/pf"; then
                log_success "pf wrapper contains image configuration"
            else
                log_error "pf wrapper missing image configuration"
                return 1
            fi
            
            if grep -q "PF_RUNTIME" "${install_prefix}/bin/pf"; then
                log_success "pf wrapper contains runtime configuration"
            else
                log_error "pf wrapper missing runtime configuration"
                return 1
            fi
            
        else
            log_error "pf wrapper not found at ${install_prefix}/bin/pf"
            return 1
        fi
        
        # Check if universal wrapper exists
        if [[ -x "${install_prefix}/lib/pf-runner/pf_universal" ]]; then
            log_success "pf_universal wrapper installed"
        else
            log_error "pf_universal wrapper not found"
            return 1
        fi
        
        # Check if images were built
        if "$runtime" image exists "localhost/pf-base:latest" >/dev/null 2>&1; then
            log_success "pf-base image exists"
        else
            log_warning "pf-base image not found (may have been skipped)"
        fi
        
        if "$runtime" image exists "localhost/pf-runner:latest" >/dev/null 2>&1; then
            log_success "pf-runner image exists"
        else
            log_warning "pf-runner image not found (may have been skipped)"
        fi
        
    else
        log_error "Container installation failed"
        cat "${test_dir}/install.log"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Container installation test completed successfully"
    return 0
}

# Test container image building
test_container_builds() {
    local runtime="$1"
    
    log_info "Testing container image builds with $runtime..."
    
    local test_dir="/tmp/pf-build-test-$$"
    
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
    fi
    
    # Test base image build
    log_info "Building base image..."
    if "$runtime" build -t "localhost/pf-base:test" -f "containers/dockerfiles/Dockerfile.base" . 2>&1 | tee "${test_dir}/base-build.log"; then
        log_success "Base image built successfully"
        
        # Test pf-runner image build
        log_info "Building pf-runner image..."
        if "$runtime" build -t "localhost/pf-runner:test" -f "containers/dockerfiles/Dockerfile.pf-runner" . 2>&1 | tee "${test_dir}/runner-build.log"; then
            log_success "pf-runner image built successfully"
            
            # Test running the container
            log_info "Testing container execution..."
            if "$runtime" run --rm "localhost/pf-runner:test" pf --version 2>&1 | tee "${test_dir}/run-test.log"; then
                log_success "Container execution works"
            else
                log_warning "Container execution failed"
                cat "${test_dir}/run-test.log"
            fi
            
            # Test pf list in container
            log_info "Testing pf list in container..."
            if "$runtime" run --rm "localhost/pf-runner:test" pf list 2>&1 | tee "${test_dir}/list-test.log"; then
                log_success "pf list works in container"
            else
                log_warning "pf list failed in container"
                cat "${test_dir}/list-test.log"
            fi
            
            # Cleanup test images
            "$runtime" rmi "localhost/pf-runner:test" >/dev/null 2>&1 || true
        else
            log_error "pf-runner image build failed"
            cat "${test_dir}/runner-build.log"
            return 1
        fi
        
        # Cleanup test images
        "$runtime" rmi "localhost/pf-base:test" >/dev/null 2>&1 || true
    else
        log_error "Base image build failed"
        cat "${test_dir}/base-build.log"
        return 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$test_dir"
    
    log_success "Container build test completed successfully"
    return 0
}

# Test all container variants
test_container_variants() {
    local runtime="$1"
    
    log_info "Testing all container variants..."
    
    echo ""
    echo "Container Variants Analysis:"
    echo "============================"
    
    local total_variants=0
    local buildable_variants=0
    local failed_variants=0
    
    for dockerfile in ./containers/dockerfiles/Dockerfile.*; do
        if [[ -f "$dockerfile" ]]; then
            local variant=$(basename "$dockerfile" | sed 's/Dockerfile\.//')
            total_variants=$((total_variants + 1))
            
            echo ""
            log_info "Analyzing variant: $variant"
            echo "  File: $dockerfile"
            
            # Check base image
            if grep -q "FROM" "$dockerfile" 2>/dev/null; then
                local base_image=$(grep "FROM" "$dockerfile" | head -1 | awk '{print $2}')
                echo "  Base image: $base_image"
                
                # Categorize variant
                if [[ "$base_image" == "localhost/pf-base:latest" ]]; then
                    echo "  Category: pf-runner variant (depends on pf-base)"
                    echo "  Status: Should be buildable after pf-base"
                    buildable_variants=$((buildable_variants + 1))
                elif [[ "$base_image" =~ ^localhost/ ]]; then
                    echo "  Category: Custom local image"
                    echo "  Status: Requires manual base image build"
                    failed_variants=$((failed_variants + 1))
                elif [[ "$base_image" =~ ^docker\.io/ ]] || [[ "$base_image" =~ ^registry\./ ]] || [[ ! "$base_image" =~ / ]]; then
                    echo "  Category: Public registry image"
                    echo "  Status: Should be buildable (external base)"
                    buildable_variants=$((buildable_variants + 1))
                else
                    echo "  Category: Unknown"
                    echo "  Status: Uncertain"
                    failed_variants=$((failed_variants + 1))
                fi
                
                # Check for package managers
                if grep -q "apt-get\|yum\|dnf\|pacman" "$dockerfile" 2>/dev/null; then
                    echo "  Package manager: Detected"
                else
                    echo "  Package manager: None"
                fi
                
                # Check for COPY/ADD operations
                if grep -q "COPY\|ADD" "$dockerfile" 2>/dev/null; then
                    echo "  File operations: Present"
                else
                    echo "  File operations: None"
                fi
                
                # Check for obvious issues
                if grep -q "RUN.*&&.*\\\\" "$dockerfile" 2>/dev/null; then
                    echo "  Multi-line RUN: Present (good practice)"
                else
                    echo "  Multi-line RUN: Not detected"
                fi
                
            else
                echo "  Status: No FROM directive (broken)"
                failed_variants=$((failed_variants + 1))
            fi
        fi
    done
    
    echo ""
    echo "============================"
    log_info "Container Variants Summary:"
    echo "  Total variants: $total_variants"
    echo "  Likely buildable: $buildable_variants"
    echo "  Likely problematic: $failed_variants"
    
    # Test building a few key variants
    echo ""
    log_info "Testing key container builds..."
    
    local test_variants=("base" "pf-runner" "api-server" "debugger")
    local successful_builds=0
    
    for variant in "${test_variants[@]}"; do
        local dockerfile="./containers/dockerfiles/Dockerfile.$variant"
        if [[ -f "$dockerfile" ]]; then
            log_info "Testing build of $variant..."
            
            if "$runtime" build -t "localhost/pf-$variant:test" -f "$dockerfile" . >/dev/null 2>&1; then
                log_success "$variant builds successfully"
                successful_builds=$((successful_builds + 1))
                
                # Cleanup
                "$runtime" rmi "localhost/pf-$variant:test" >/dev/null 2>&1 || true
            else
                log_error "$variant build failed"
            fi
        else
            log_warning "$variant dockerfile not found"
        fi
    done
    
    echo ""
    log_info "Build test results: $successful_builds/${#test_variants[@]} variants built successfully"
    
    return 0
}

# Main test function
main() {
    echo -e "${BLUE}Container Installer Validation${NC}"
    echo "=============================="
    echo ""
    
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Container runtime availability
    local runtime
    if runtime=$(test_container_runtime); then
        tests_passed=$((tests_passed + 1))
    else
        log_error "No container runtime available, skipping container tests"
        return 1
    fi
    
    echo ""
    
    # Test 2: Container installation
    if test_container_install "$runtime"; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    echo ""
    
    # Test 3: Container builds
    if test_container_builds "$runtime"; then
        tests_passed=$((tests_passed + 1))
    else
        tests_failed=$((tests_failed + 1))
    fi
    
    echo ""
    
    # Test 4: Container variants analysis
    test_container_variants "$runtime"
    
    echo ""
    echo "=============================="
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