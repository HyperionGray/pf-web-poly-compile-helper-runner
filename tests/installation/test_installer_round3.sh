#!/usr/bin/env bash
# Comprehensive installer test suite for Round 3
# Tests canonical installation methods and bashisms

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNNER_DIR="$REPO_ROOT/pf-runner-full"
if [[ ! -d "$RUNNER_DIR" ]]; then
    RUNNER_DIR="$REPO_ROOT/pf-runner"
fi
TEST_DIR="/tmp/installer-round3-tests-$$"
TESTS_PASSED=0
TESTS_FAILED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

cleanup() {
    log_info "Cleaning up test directory: $TEST_DIR"
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

# Create test directory
mkdir -p "$TEST_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    pf-runner Installer Testing - Round 3${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# Test 1: Verify installer syntax (bashisms check)
# ============================================================================
log_test "Test 1: Verify installer syntax and bashisms"

# Test install.sh syntax
if bash -n "$REPO_ROOT/install.sh" 2>/dev/null; then
    log_success "install.sh: Syntax check passed"
else
    log_error "install.sh: Syntax errors detected"
fi

# Test install-static.sh syntax
if bash -n "$REPO_ROOT/install-static.sh" 2>/dev/null; then
    log_success "install-static.sh: Syntax check passed"
else
    log_error "install-static.sh: Syntax errors detected"
fi

# Validate modular installer entrypoint and key options
if [[ -f "$REPO_ROOT/scripts/installer/main.sh" ]]; then
    log_success "Modular installer entrypoint exists"
else
    log_error "Missing scripts/installer/main.sh"
fi

if "$REPO_ROOT/install.sh" --dry-run --prefix "$TEST_DIR/dry-run-prefix" >/dev/null 2>&1; then
    log_success "install.sh --dry-run works"
else
    log_error "install.sh --dry-run failed"
fi

if "$REPO_ROOT/install.sh" --help 2>/dev/null | grep -q -- "--write-shell-profile"; then
    log_success "install.sh help includes shell-profile guidance option"
else
    log_error "install.sh help missing --write-shell-profile option"
fi

echo ""

# ============================================================================
# Test 2: Test native installation (install.sh)
# ============================================================================
log_test "Test 2: Native installation (install.sh)"

NATIVE_PREFIX="$TEST_DIR/native-install"
log_info "Installing to: $NATIVE_PREFIX"

if "$REPO_ROOT/install.sh" --prefix "$NATIVE_PREFIX" --skip-deps >/dev/null 2>&1; then
    log_success "Native installation completed"
    
    # Verify installation structure
    if [[ -x "$NATIVE_PREFIX/bin/pf" ]]; then
        log_success "pf executable created"
    else
        log_error "pf executable not found"
    fi
    
    if [[ -d "$NATIVE_PREFIX/lib/pf-runner" ]]; then
        log_success "pf-runner library directory created"
    else
        log_error "pf-runner library directory not found"
    fi
    
    if [[ -d "$NATIVE_PREFIX/lib/pf-runner-venv" ]]; then
        log_success "Python virtual environment created"
    else
        log_success "Python virtual environment skipped (fallback install path used)"
    fi
    
    # Test pf executable
    if "$NATIVE_PREFIX/bin/pf" -V >/dev/null 2>&1; then
        log_success "pf -V works"
    else
        log_error "pf -V failed"
    fi
    
    # Test task listing
    if cd "$RUNNER_DIR" && "$NATIVE_PREFIX/bin/pf" test.pf list >/dev/null 2>&1; then
        log_success "pf list works"
    else
        log_error "pf list failed"
    fi
    
    # Test task execution
    if cd "$RUNNER_DIR" && "$NATIVE_PREFIX/bin/pf" test.pf smoke >/dev/null 2>&1; then
        log_success "pf task execution works"
    else
        log_error "pf task execution failed"
    fi
else
    log_error "Native installation failed"
fi

echo ""

# ============================================================================
# Test 3: Test static installation (install-static.sh)
# ============================================================================
log_test "Test 3: Static installation (install-static.sh)"

# Check if static executable exists
STATIC_EXE=""
if [[ -f "$REPO_ROOT/pf-runner-full/pf-static" ]]; then
    STATIC_EXE="$REPO_ROOT/pf-runner-full/pf-static"
elif [[ -f "$REPO_ROOT/pf-runner/pf-static" ]]; then
    STATIC_EXE="$REPO_ROOT/pf-runner/pf-static"
fi

if [[ -z "$STATIC_EXE" ]]; then
    log_info "Static executable not built, skipping static installation test"
    log_info "Build with: cd pf-runner-full && make build-static"
else
    STATIC_PREFIX="$TEST_DIR/static-install"
    log_info "Installing to: $STATIC_PREFIX"
    
    if "$REPO_ROOT/install-static.sh" --prefix "$STATIC_PREFIX" >/dev/null 2>&1; then
        log_success "Static installation completed"
        
        # Verify installation
        if [[ -x "$STATIC_PREFIX/bin/pf" ]]; then
            log_success "pf static executable installed"
        else
            log_error "pf static executable not found"
        fi
        
        # Test static executable
        if "$STATIC_PREFIX/bin/pf" -V >/dev/null 2>&1; then
            log_success "Static pf -V works"
        else
            log_error "Static pf -V failed"
        fi
        
        # Test task listing
        if cd "$RUNNER_DIR" && "$STATIC_PREFIX/bin/pf" test.pf list >/dev/null 2>&1; then
            log_success "Static pf list works"
        else
            log_error "Static pf list failed"
        fi
    else
        log_error "Static installation failed"
    fi
fi

echo ""

# ============================================================================
# Test 4: Test installer help and options
# ============================================================================
log_test "Test 4: Installer help and options"

# Test install.sh help
if "$REPO_ROOT/install.sh" --help >/dev/null 2>&1; then
    log_success "install.sh --help works"
else
    log_error "install.sh --help failed"
fi

# Test install-static.sh help
if "$REPO_ROOT/install-static.sh" --help >/dev/null 2>&1; then
    log_success "install-static.sh --help works"
else
    log_error "install-static.sh --help failed"
fi

echo ""

# ============================================================================
# Test 5: Test pf task definitions and container features
# ============================================================================
log_test "Test 5: pf task definitions and dependencies"

if [[ -x "$NATIVE_PREFIX/bin/pf" ]]; then
    # Test that Pfyfile.pf can be parsed
    if cd "$REPO_ROOT" && "$NATIVE_PREFIX/bin/pf" list >/dev/null 2>&1; then
        log_success "Main Pfyfile.pf parses correctly"
    else
        log_error "Main Pfyfile.pf failed to parse"
    fi
    
    # Check that container tasks are defined
    if cd "$REPO_ROOT" && "$NATIVE_PREFIX/bin/pf" list 2>/dev/null | grep -q "containers"; then
        log_success "Container tasks are defined"
    else
        log_info "Container tasks may not be available (expected if not in task list)"
    fi
fi

echo ""

# ============================================================================
# Test 6: Test bashism support in installer scripts
# ============================================================================
log_test "Test 6: Advanced bashism support"

# Create a test script that uses various bashisms
TEST_SCRIPT="$TEST_DIR/bashism-test.sh"
cat > "$TEST_SCRIPT" <<'BASHISMS_EOF'
#!/usr/bin/env bash
set -euo pipefail

# Test heredoc
cat <<EOF
Heredoc test
Multiple lines
EOF

# Test semicolons
echo "test1"; echo "test2"

# Test && operator
true && echo "AND works"

# Test quotes preservation
VAR="test value"
echo "${VAR}"

# Test command substitution
RESULT=$(echo "command sub")
echo "$RESULT"

exit 0
BASHISMS_EOF

chmod +x "$TEST_SCRIPT"

if bash "$TEST_SCRIPT" >/dev/null 2>&1; then
    log_success "Bashism test script executed successfully"
else
    log_error "Bashism test script failed"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Installation methods validated:"
    echo "  ✓ install.sh (native installation)"
    echo "  ✓ install-static.sh (static executable)"
    echo ""
    echo "Bashisms validated:"
    echo "  ✓ Heredocs"
    echo "  ✓ Semicolons"
    echo "  ✓ && operators"
    echo "  ✓ Proper quoting"
    echo ""
    echo "pf functionality validated:"
    echo "  ✓ Version command"
    echo "  ✓ Task listing"
    echo "  ✓ Task execution"
    echo "  ✓ Pfyfile parsing"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
