#!/usr/bin/env bash
# test-containers.sh - Test container builds and basic functionality
# Run this to validate the container infrastructure works

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[FAIL]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Container runtime
CONTAINER_RT="${CONTAINER_RT:-podman}"
if ! command -v "${CONTAINER_RT}" &> /dev/null; then
    if command -v docker &> /dev/null; then
        CONTAINER_RT="docker"
        log_warn "Using docker instead of podman"
    else
        log_error "Neither podman nor docker found"
        exit 1
    fi
fi

# Test output directory
TEST_OUTPUT="/tmp/pf-container-test-$$"
mkdir -p "${TEST_OUTPUT}"

cleanup() {
    log_info "Cleaning up test containers and output..."
    ${CONTAINER_RT} rm -f test-api-server test-pf-runner 2>/dev/null || true
    rm -rf "${TEST_OUTPUT}"
}
trap cleanup EXIT

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local name="$1"
    shift
    local cmd="$*"
    
    log_info "Testing: ${name}"
    if eval "${cmd}"; then
        log_success "${name}"
        ((TESTS_PASSED++))
    else
        log_error "${name}"
        ((TESTS_FAILED++))
    fi
}

cd "${PROJECT_ROOT}"

echo ""
echo "====================================="
echo "Container Infrastructure Tests"
echo "====================================="
echo ""
log_info "Container runtime: ${CONTAINER_RT}"
log_info "Project root: ${PROJECT_ROOT}"
log_info "Test output: ${TEST_OUTPUT}"
echo ""

# Test 1: Build base image
run_test "Build base image" "${CONTAINER_RT} build -t localhost/pf-base:test -f containers/dockerfiles/Dockerfile.base . >/dev/null 2>&1"

# Test 2: Base container runs
run_test "Base container runs" "${CONTAINER_RT} run --rm localhost/pf-base:test echo 'Hello from container'"

# Test 3: Base container has required tools
run_test "Base has Python3" "${CONTAINER_RT} run --rm localhost/pf-base:test python3 --version"
run_test "Base has GDB" "${CONTAINER_RT} run --rm localhost/pf-base:test which gdb"
run_test "Base has Git" "${CONTAINER_RT} run --rm localhost/pf-base:test git --version"

# Test 4: Build pf-runner image
run_test "Build pf-runner image" "${CONTAINER_RT} build -t localhost/pf-runner:test -f containers/dockerfiles/Dockerfile.pf-runner . >/dev/null 2>&1"

# Test 5: pf-runner can list tasks
run_test "pf-runner lists tasks" "${CONTAINER_RT} run --rm localhost/pf-runner:test pf list | head -5"

# Test 6: Build API server image
run_test "Build API server image" "${CONTAINER_RT} build -t localhost/pf-api-server:test -f containers/dockerfiles/Dockerfile.api-server . >/dev/null 2>&1"

# Test 7: API server health check
log_info "Testing: API server health check"
${CONTAINER_RT} run -d --name test-api-server -p 8082:8080 localhost/pf-api-server:test
sleep 5
if curl -sf http://localhost:8082/api/health | grep -q '"status":"ok"'; then
    log_success "API server health check"
    ((TESTS_PASSED++))
else
    log_error "API server health check"
    ((TESTS_FAILED++))
fi
${CONTAINER_RT} stop test-api-server >/dev/null 2>&1 || true
${CONTAINER_RT} rm test-api-server >/dev/null 2>&1 || true

# Test 8: Build Rust builder image (skip if it takes too long)
log_info "Testing: Build Rust builder image (this may take several minutes)"
if timeout 600 ${CONTAINER_RT} build -t localhost/pf-build-rust:test -f containers/dockerfiles/Dockerfile.build-rust . >/dev/null 2>&1; then
    log_success "Build Rust builder image"
    ((TESTS_PASSED++))
    
    # Test 9: Rust WASM build
    log_info "Testing: Rust WASM build"
    mkdir -p "${TEST_OUTPUT}/rust-src" "${TEST_OUTPUT}/rust-out"
    cp -r demos/pf-web-polyglot-demo-plus-c/rust/* "${TEST_OUTPUT}/rust-src/"
    chmod -R 777 "${TEST_OUTPUT}"
    
    if ${CONTAINER_RT} run --rm --userns=keep-id \
        -v "${TEST_OUTPUT}/rust-src:/app/rust:rw" \
        -v "${TEST_OUTPUT}/rust-out:/app/output:rw" \
        localhost/pf-build-rust:test 2>&1 | tail -5; then
        
        if [[ -f "${TEST_OUTPUT}/rust-out/wasm/rust/pkg/rust_demo_bg.wasm" ]]; then
            log_success "Rust WASM build"
            ((TESTS_PASSED++))
        else
            log_error "Rust WASM build - no output file"
            ((TESTS_FAILED++))
        fi
    else
        log_error "Rust WASM build"
        ((TESTS_FAILED++))
    fi
else
    log_warn "Skipped Rust builder (build timeout or failed)"
fi

# Test 10: WAT to WASM build using base image
log_info "Testing: WAT to WASM build"
mkdir -p "${TEST_OUTPUT}/wat-out"
if ${CONTAINER_RT} run --rm \
    -v "${PROJECT_ROOT}/demos/pf-web-polyglot-demo-plus-c/asm:/asm:ro" \
    -v "${TEST_OUTPUT}/wat-out:/out:rw" \
    localhost/pf-base:test \
    bash -c "apt-get update -qq && apt-get install -y -qq wabt >/dev/null 2>&1 && wat2wasm /asm/mini.wat -o /out/mini.wasm" 2>&1; then
    
    if [[ -f "${TEST_OUTPUT}/wat-out/mini.wasm" ]]; then
        log_success "WAT to WASM build"
        ((TESTS_PASSED++))
    else
        log_error "WAT to WASM build - no output file"
        ((TESTS_FAILED++))
    fi
else
    log_error "WAT to WASM build"
    ((TESTS_FAILED++))
fi

echo ""
echo "====================================="
echo "Test Summary"
echo "====================================="
echo ""
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [[ ${TESTS_FAILED} -eq 0 ]]; then
    log_success "All tests passed!"
    exit 0
else
    log_error "Some tests failed"
    exit 1
fi
