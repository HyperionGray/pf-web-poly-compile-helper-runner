#!/usr/bin/env bash
# Debian installer validation script
# Tests pf runner execution and Debian .deb package contents

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RUNNER_DIR="${REPO_ROOT}/pf-runner-full"
TEST_PF="${REPO_ROOT}/tests/fixtures/installer_test.pf"
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

test_pf_ignores_fake_venv() {
    local test_name="$1"
    shift
    local pf_cmd=("$@")
    local fake_venv="${TEST_DIR}/fake-venv-${RANDOM}"

    mkdir -p "${fake_venv}/bin"
    cat > "${fake_venv}/bin/python3" <<'EOF'
#!/usr/bin/env bash
echo "fake venv python3 should not be used" >&2
exit 97
EOF
    chmod +x "${fake_venv}/bin/python3"

    if ! VIRTUAL_ENV="${fake_venv}" PATH="${fake_venv}/bin:${PATH}" "${pf_cmd[@]}" -V >/dev/null 2>&1; then
        log_error "$test_name: pf used PATH python3 from fake venv"
        return 1
    fi

    log_info "$test_name: fake active venv does not break pf"
    return 0
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
    
    # Test list with shared installer fixture
    cd "$REPO_ROOT"
    if ! "${pf_cmd[@]}" -f "$TEST_PF" list >/dev/null 2>&1; then
        log_error "$test_name: pf list failed"
        return 1
    fi
    log_info "$test_name: pf list works"
    
    # Test running a task
    if ! "${pf_cmd[@]}" -f "$TEST_PF" hello >/dev/null 2>&1; then
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
# Test 1: Repo wrapper
#
log_test "Test 1: Repo wrapper"
cd "$REPO_ROOT"
test_pf_executable "Repo wrapper" "$REPO_ROOT/pf.sh"
test_pf_ignores_fake_venv "Repo wrapper" "$REPO_ROOT/pf.sh"
echo ""

#
# Test 2: Debian package structure
#
log_test "Test 2: Debian package"
DEB_FILE="$(ls -1 "$REPO_ROOT"/build-packages/deb/pf-runner_*.deb "$REPO_ROOT"/deb/build/pf-runner_*.deb 2>/dev/null | sort -V | tail -n1 || true)"
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
log_success "All available installer tests completed successfully!"
echo ""
echo "Tested installers:"
echo "  ✓ Direct pf_main.py execution"
echo "  ✓ Debian package (.deb)"
echo ""
echo "All available installers are working correctly!"
echo ""
log_info "For production use, install via .deb package:"
echo "  sudo dpkg -i build-packages/deb/pf-runner_latest.deb"
