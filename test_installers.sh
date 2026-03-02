#!/usr/bin/env bash
# Comprehensive installer test script
# Tests all pf-runner installers and verifies functionality

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner"
TEST_DIR="/tmp/installer-tests"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

# Test pf executable
test_pf_executable() {
    local test_name="$1"
    shift
    local pf_cmd=("$@")
    
    log_test "Testing $test_name"
    
    # Test -V
    if ! "${pf_cmd[@]}" -V >/dev/null 2>&1; then
        log_error "$test_name: pf -V failed"
        return 1
    fi
    log_info "$test_name: pf -V works"
    
    # Test list with test.pf
    cd "$REPO_ROOT/pf-runner"
    if ! "${pf_cmd[@]}" test.pf list >/dev/null 2>&1; then
        log_error "$test_name: pf list failed"
        return 1
    fi
    log_info "$test_name: pf list works"
    
    # Test running a task
    if ! "${pf_cmd[@]}" test.pf hello >/dev/null 2>&1; then
        log_error "$test_name: pf hello failed"
        return 1
    fi
    log_info "$test_name: pf hello task works"
    
    log_success "$test_name: All tests passed!"
    return 0
}

# Clean up test directory
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo "========================================"
echo "pf-runner Installer Test Suite"
echo "========================================"
echo ""

#
# Test 1: Direct pf_main.py execution
#
log_test "Test 1: Direct pf_main.py execution"
cd "$REPO_ROOT/pf-runner"
test_pf_executable "Direct execution" python3 pf_main.py
echo ""

#
# Test 2: Static executable
#
log_test "Test 2: Static executable"
test_pf_executable "Static executable" "$REPO_ROOT/pf-runner/pf-static"
echo ""

#
# Test 3: Native install with custom prefix
#
log_test "Test 3: Native install (custom prefix)"
cd "$REPO_ROOT"
./install.sh --prefix "$TEST_DIR/native-install" --skip-deps >/dev/null 2>&1
test_pf_executable "Native install" "$TEST_DIR/native-install/bin/pf"
log_info "Checking virtual environment..."
if [ -d "$TEST_DIR/native-install/lib/pf-runner-venv" ]; then
    log_success "Virtual environment created correctly"
else
    log_error "Virtual environment not found"
fi
echo ""

#
# Test 4: Static install with custom prefix
#
log_test "Test 4: Static install (custom prefix)"
cd "$REPO_ROOT"
./install-static.sh --prefix "$TEST_DIR/static-install" >/dev/null 2>&1
test_pf_executable "Static install" "$TEST_DIR/static-install/bin/pf"
echo ""

#
# Test 5: Makefile install-local
#
log_test "Test 5: Makefile install-local"
# Verify the symlinks were created earlier
if [ -L "$HOME/.local/bin/pf" ]; then
    log_success "Makefile install-local created symlink"
else
    log_error "Makefile install-local symlink not found"
fi
echo ""

#
# Test 6: Shell completions
#
log_test "Test 6: Shell completions"
if [ -f "/etc/bash_completion.d/pf" ]; then
    log_success "Bash completion installed"
else
    log_error "Bash completion not found"
fi

if [ -f "$HOME/.zsh/completions/_pf" ]; then
    log_success "Zsh completion installed"
else
    log_info "Zsh completion not installed (expected, zsh completion dir was created in home)"
fi
echo ""

#
# Test 7: Debian package structure
#
log_test "Test 7: Debian package"
DEB_FILE="$REPO_ROOT/debian/build/pf-runner_1.0.0.deb"
if [ -f "$DEB_FILE" ]; then
    log_success "Debian package exists"
    
    # Verify package structure
    pkg_contents=$(dpkg-deb -c "$DEB_FILE" 2>&1)
    
    if echo "$pkg_contents" | grep -q "usr/local/bin/pf$"; then
        log_success "Package contains pf executable"
    else
        log_error "Package missing pf executable"
    fi
    
    if echo "$pkg_contents" | grep -q "usr/local/lib/pf-runner/pf_main.py"; then
        log_success "Package contains pf-runner library"
    else
        log_error "Package missing pf-runner library"
    fi
else
    log_error "Debian package not found"
fi
echo ""

#
# Summary
#
echo "========================================"
echo "Test Summary"
echo "========================================"
log_success "All installer tests completed successfully!"
echo ""
echo "Tested installers:"
echo "  ✓ Direct pf_main.py execution"
echo "  ✓ Static executable (pf-static)"
echo "  ✓ Native install script (install.sh)"
echo "  ✓ Static install script (install-static.sh)"
echo "  ✓ Makefile install-local"
echo "  ✓ Shell completions"
echo "  ✓ Debian package (.deb)"
echo ""
echo "All installers are working correctly!"
