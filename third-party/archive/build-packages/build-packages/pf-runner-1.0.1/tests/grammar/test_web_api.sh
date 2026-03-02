#!/bin/bash
# test_web_api.sh - Unit tests for web/WASM builds and REST API
# Tests web-build-*, api-server, and related tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PF_RUNNER="$REPO_ROOT/pf-runner"
PF_CMD="python3 $PF_RUNNER/pf_parser.py"

echo "Testing Web/WASM builds and REST API"
echo "Repository: $REPO_ROOT"
echo ""

pass() {
    PASSED=$((PASSED + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail() {
    FAILED=$((FAILED + 1))
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo "  Reason: $2"
}

skip() {
    SKIPPED=$((SKIPPED + 1))
    echo -e "${YELLOW}○ SKIP${NC}: $1 (reason: $2)"
}

section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

# ==============================================================================
section "1. Web Build Tasks Exist"
# ==============================================================================

cd "$REPO_ROOT"
TASK_LIST=$($PF_CMD Pfyfile.pf list 2>&1)

# Test 1.1: web-build-rust exists
if echo "$TASK_LIST" | grep -q "web-build-rust"; then
    pass "web-build-rust task exists"
else
    fail "web-build-rust task exists" "Task not found"
fi

# Test 1.2: web-build-c exists
if echo "$TASK_LIST" | grep -q "web-build-c"; then
    pass "web-build-c task exists"
else
    fail "web-build-c task exists" "Task not found"
fi

# Test 1.3: web-build-fortran exists
if echo "$TASK_LIST" | grep -q "web-build-fortran"; then
    pass "web-build-fortran task exists"
else
    fail "web-build-fortran task exists" "Task not found"
fi

# Test 1.4: web-build-wat exists
if echo "$TASK_LIST" | grep -q "web-build-wat"; then
    pass "web-build-wat task exists"
else
    fail "web-build-wat task exists" "Task not found"
fi

# Test 1.5: web-build-all exists
if echo "$TASK_LIST" | grep -q "web-build-all"; then
    pass "web-build-all task exists"
else
    fail "web-build-all task exists" "Task not found"
fi

# ==============================================================================
section "2. WASM Target Tasks"
# ==============================================================================

# Test 2.1: web-build-rust-wasm exists
if echo "$TASK_LIST" | grep -q "web-build-rust-wasm"; then
    pass "web-build-rust-wasm task exists"
else
    fail "web-build-rust-wasm task exists" "Task not found"
fi

# Test 2.2: web-build-c-wasm exists
if echo "$TASK_LIST" | grep -q "web-build-c-wasm"; then
    pass "web-build-c-wasm task exists"
else
    fail "web-build-c-wasm task exists" "Task not found"
fi

# Test 2.3: web-build-fortran-wasm exists
if echo "$TASK_LIST" | grep -q "web-build-fortran-wasm"; then
    pass "web-build-fortran-wasm task exists"
else
    fail "web-build-fortran-wasm task exists" "Task not found"
fi

# Test 2.4: web-build-wat-wasm exists
if echo "$TASK_LIST" | grep -q "web-build-wat-wasm"; then
    pass "web-build-wat-wasm task exists"
else
    fail "web-build-wat-wasm task exists" "Task not found"
fi

# Test 2.5: web-build-all-wasm exists
if echo "$TASK_LIST" | grep -q "web-build-all-wasm"; then
    pass "web-build-all-wasm task exists"
else
    fail "web-build-all-wasm task exists" "Task not found"
fi

# ==============================================================================
section "3. LLVM Target Tasks"
# ==============================================================================

# Test 3.1: web-build-rust-llvm exists
if echo "$TASK_LIST" | grep -q "web-build-rust-llvm"; then
    pass "web-build-rust-llvm task exists"
else
    fail "web-build-rust-llvm task exists" "Task not found"
fi

# Test 3.2: web-build-c-llvm exists
if echo "$TASK_LIST" | grep -q "web-build-c-llvm"; then
    pass "web-build-c-llvm task exists"
else
    fail "web-build-c-llvm task exists" "Task not found"
fi

# Test 3.3: web-build-fortran-llvm exists
if echo "$TASK_LIST" | grep -q "web-build-fortran-llvm"; then
    pass "web-build-fortran-llvm task exists"
else
    fail "web-build-fortran-llvm task exists" "Task not found"
fi

# Test 3.4: web-build-all-llvm exists
if echo "$TASK_LIST" | grep -q "web-build-all-llvm"; then
    pass "web-build-all-llvm task exists"
else
    fail "web-build-all-llvm task exists" "Task not found"
fi

# Test 3.5: web-build-c-llvm-opt exists
if echo "$TASK_LIST" | grep -q "web-build-c-llvm-opt"; then
    pass "web-build-c-llvm-opt task exists"
else
    fail "web-build-c-llvm-opt task exists" "Task not found"
fi

# ==============================================================================
section "4. asm.js Target Tasks"
# ==============================================================================

# Test 4.1: web-build-c-asm exists
if echo "$TASK_LIST" | grep -q "web-build-c-asm"; then
    pass "web-build-c-asm task exists"
else
    fail "web-build-c-asm task exists" "Task not found"
fi

# Test 4.2: web-build-all-asm exists
if echo "$TASK_LIST" | grep -q "web-build-all-asm"; then
    pass "web-build-all-asm task exists"
else
    fail "web-build-all-asm task exists" "Task not found"
fi

# ==============================================================================
section "5. Development Server Tasks"
# ==============================================================================

# Test 5.1: web-dev exists
if echo "$TASK_LIST" | grep -q "web-dev"; then
    pass "web-dev task exists"
else
    fail "web-dev task exists" "Task not found"
fi

# Test 5.2: web-dev-static exists
if echo "$TASK_LIST" | grep -q "web-dev-static"; then
    pass "web-dev-static task exists"
else
    fail "web-dev-static task exists" "Task not found"
fi

# Test 5.3: api-server exists
if echo "$TASK_LIST" | grep -q "api-server"; then
    pass "api-server task exists"
else
    fail "api-server task exists" "Task not found"
fi

# ==============================================================================
section "6. Testing Tasks"
# ==============================================================================

# Test 6.1: web-test exists
if echo "$TASK_LIST" | grep -q "web-test"; then
    pass "web-test task exists"
else
    fail "web-test task exists" "Task not found"
fi

# ==============================================================================
section "7. API Server Files Exist"
# ==============================================================================

# Test 7.1: API server file exists
if [ -f "$REPO_ROOT/tools/api-server.mjs" ]; then
    pass "API server file exists (tools/api-server.mjs)"
else
    fail "API server file exists" "tools/api-server.mjs not found"
fi

# Test 7.2: Static server file exists
if [ -f "$REPO_ROOT/tools/static-server.mjs" ]; then
    pass "Static server file exists (tools/static-server.mjs)"
else
    fail "Static server file exists" "tools/static-server.mjs not found"
fi

# ==============================================================================
section "8. Web Demo Files Exist"
# ==============================================================================

# Test 8.1: Demo directory exists
if [ -d "$REPO_ROOT/demos/pf-web-polyglot-demo-plus-c" ]; then
    pass "Web demo directory exists"
else
    fail "Web demo directory exists" "Demo directory not found"
fi

# Test 8.2: Rust source exists
if [ -d "$REPO_ROOT/demos/pf-web-polyglot-demo-plus-c/rust" ]; then
    pass "Rust demo source exists"
else
    fail "Rust demo source exists" "Rust source not found"
fi

# Test 8.3: C source exists
if [ -d "$REPO_ROOT/demos/pf-web-polyglot-demo-plus-c/c" ]; then
    pass "C demo source exists"
else
    fail "C demo source exists" "C source not found"
fi

# Test 8.4: Fortran source exists
if [ -d "$REPO_ROOT/demos/pf-web-polyglot-demo-plus-c/fortran" ]; then
    pass "Fortran demo source exists"
else
    fail "Fortran demo source exists" "Fortran source not found"
fi

# Test 8.5: WAT source exists
if [ -d "$REPO_ROOT/demos/pf-web-polyglot-demo-plus-c/asm" ]; then
    pass "WAT demo source exists"
else
    fail "WAT demo source exists" "WAT source not found"
fi

# ==============================================================================
section "9. Parameter Support in Tasks"
# ==============================================================================

# Test 9.1: Check opt_level parameter in web-build-rust-llvm
TASK_DEF=$(grep -A5 "task web-build-rust-llvm" "$REPO_ROOT/Pfyfile.pf" 2>/dev/null || echo "")
if echo "$TASK_DEF" | grep -q "opt_level"; then
    pass "web-build-rust-llvm supports opt_level parameter"
else
    fail "web-build-rust-llvm supports opt_level parameter" "opt_level not found in task"
fi

# Test 9.2: Check parallel parameter in web-build-c-llvm
TASK_DEF=$(grep -A5 "task web-build-c-llvm" "$REPO_ROOT/Pfyfile.pf" 2>/dev/null || echo "")
if echo "$TASK_DEF" | grep -q "parallel"; then
    pass "web-build-c-llvm supports parallel parameter"
else
    fail "web-build-c-llvm supports parallel parameter" "parallel not found in task"
fi

# ==============================================================================
section "10. REST API Documentation"
# ==============================================================================

# Test 10.1: REST API documentation exists
if [ -f "$REPO_ROOT/docs/REST-API.md" ]; then
    pass "REST API documentation exists"
else
    fail "REST API documentation exists" "docs/REST-API.md not found"
fi

# Test 10.2: Documentation covers all endpoints
API_DOC="$REPO_ROOT/docs/REST-API.md"
if [ -f "$API_DOC" ]; then
    ENDPOINTS=0
    grep -q "/api/health" "$API_DOC" && ENDPOINTS=$((ENDPOINTS+1))
    grep -q "/api/build" "$API_DOC" && ENDPOINTS=$((ENDPOINTS+1))
    grep -q "/api/status" "$API_DOC" && ENDPOINTS=$((ENDPOINTS+1))
    grep -q "/api/projects" "$API_DOC" && ENDPOINTS=$((ENDPOINTS+1))
    
    if [ $ENDPOINTS -ge 4 ]; then
        pass "REST API documentation covers main endpoints ($ENDPOINTS found)"
    else
        fail "REST API documentation covers main endpoints" "Only $ENDPOINTS/4 endpoints documented"
    fi
else
    skip "REST API documentation covers main endpoints" "Documentation file not found"
fi

# ==============================================================================
section "11. Playwright Test Configuration"
# ==============================================================================

# Test 11.1: Playwright config exists
if [ -f "$REPO_ROOT/playwright.config.ts" ]; then
    pass "Playwright configuration exists"
else
    fail "Playwright configuration exists" "playwright.config.ts not found"
fi

# Test 11.2: E2E test files exist
E2E_TESTS=$(find "$REPO_ROOT/tests/e2e" -name "*.spec.ts" 2>/dev/null | wc -l)
if [ $E2E_TESTS -gt 0 ]; then
    pass "E2E test files exist ($E2E_TESTS tests found)"
else
    fail "E2E test files exist" "No .spec.ts files in tests/e2e"
fi

# ==============================================================================
section "12. Installation Tasks"
# ==============================================================================

# Test 12.1: install-base exists
if echo "$TASK_LIST" | grep -q "install-base"; then
    pass "install-base task exists"
else
    fail "install-base task exists" "Task not found"
fi

# Test 12.2: install-web exists
if echo "$TASK_LIST" | grep -q "install-web"; then
    pass "install-web task exists"
else
    fail "install-web task exists" "Task not found"
fi

# Test 12.3: install exists
if echo "$TASK_LIST" | grep -q "install"; then
    pass "install task exists"
else
    fail "install task exists" "Task not found"
fi

# ==============================================================================
section "13. Security Testing Tasks"
# ==============================================================================

# Test 13.1: security-scan exists
if echo "$TASK_LIST" | grep -q "security-scan"; then
    pass "security-scan task exists"
else
    fail "security-scan task exists" "Task not found"
fi

# Test 13.2: security-fuzz exists
if echo "$TASK_LIST" | grep -q "security-fuzz"; then
    pass "security-fuzz task exists"
else
    fail "security-fuzz task exists" "Task not found"
fi

# Test 13.3: checksec exists
if echo "$TASK_LIST" | grep -q "checksec"; then
    pass "checksec task exists"
else
    fail "checksec task exists" "Task not found"
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "========================================"
echo -e "${BLUE}Web/API Test Summary${NC}"
echo "========================================"
echo -e "${GREEN}Passed:${NC}  $PASSED"
echo -e "${RED}Failed:${NC}  $FAILED"
echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
echo "========================================"

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All $TOTAL tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed out of $TOTAL${NC}"
    exit 1
fi
